from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .clients import OmadaClient, PdfGeneratorClient
from .config import AppSettings
from .models import WorkflowBatchRequest
from .omada_plan import build_omada_plan, operation_plan_filename, write_omada_plan
from .utils import ensure_directory
from .workdrive import WorkflowWorkDriveClient


class SiteWorkflowPipeline:
    def __init__(self, settings: AppSettings, logger) -> None:
        self.settings = settings
        self.logger = logger
        self.pdf_client = PdfGeneratorClient(settings.pdf)
        self.omada_client: OmadaClient | None = None
        self.workdrive_client: WorkflowWorkDriveClient | None = None

    def _get_omada_client(self) -> OmadaClient:
        if self.omada_client is None:
            self.omada_client = OmadaClient(self.settings.omada)
        return self.omada_client

    def _get_workdrive_client(self) -> WorkflowWorkDriveClient:
        if self.workdrive_client is None:
            self.workdrive_client = WorkflowWorkDriveClient(self.settings.zoho_oauth, self.logger)
        return self.workdrive_client

    def process(self, job_id: str, raw_payload: dict[str, Any], batch: WorkflowBatchRequest) -> dict[str, Any]:
        job_dir = ensure_directory(self.settings.output.jobs_dir / job_id)
        raw_payload_path = self._write_json(job_dir / "incoming-payload.json", raw_payload)
        normalized_payload_path = self._write_json(job_dir / "normalized-workflow.json", batch.model_dump(mode="json"))
        omada_plan = build_omada_plan(batch, self.settings)
        omada_plan_written = write_omada_plan(job_dir / "omada-plan.yaml", omada_plan)
        operation_plan_written = write_omada_plan(job_dir / operation_plan_filename(batch.omada_operation), omada_plan)
        omada_plan_path = str(omada_plan_written)
        operation_plan_path = str(operation_plan_written)

        if batch.workdrive_folder_id and batch.workflow_mode == "site_only":
            self.logger.info("Workflow job %s: archiving existing WorkDrive batch folder before site-only uploads", job_id)
            self._get_workdrive_client().prepare_upload_folder(batch.workdrive_folder_id)

        pdf_payload_path: str | None = None
        pdf_job_id: str | None = None
        pdf_job: dict[str, Any] | None = None

        if batch.workflow_mode in {"pdf_only", "pdf_and_site"}:
            pdf_payload = batch.to_pdf_payload()
            pdf_payload_path = str(self._write_json(job_dir / "generated-pdf-payload.json", pdf_payload))

            self.logger.info("Workflow job %s: creating Password_PDF_Generator job", job_id)
            pdf_accept = self.pdf_client.create_job(pdf_payload)
            pdf_job_id = str(pdf_accept["job_id"])
            pdf_job = self.pdf_client.wait_for_completion(pdf_job_id)
            if str(pdf_job.get("status", "")).lower() != "completed":
                raise RuntimeError(f"Password_PDF_Generator job {pdf_job_id} failed: {pdf_job.get('error')}")

        omada_plan_upload: dict[str, Any] | None = None
        operation_plan_upload: dict[str, Any] | None = None
        if batch.workdrive_folder_id:
            self.logger.info("Workflow job %s: uploading Omada plan to WorkDrive", job_id)
            omada_plan_upload = self._get_workdrive_client().upload_file(omada_plan_written, batch.workdrive_folder_id)
            if operation_plan_written.name != omada_plan_written.name:
                self.logger.info("Workflow job %s: uploading %s to WorkDrive", job_id, operation_plan_written.name)
                operation_plan_upload = self._get_workdrive_client().upload_file(operation_plan_written, batch.workdrive_folder_id)

        omada_job_id: str | None = None
        omada_job: dict[str, Any] | None = None
        omada_live_site_uploads: list[dict[str, Any]] = []

        if batch.workflow_mode in {"pdf_and_site", "site_only"}:
            self.logger.info("Workflow job %s: creating Omada Site Creator job", job_id)
            omada_accept = self._get_omada_client().create_job(omada_plan, omada_plan_written.name)
            omada_job_id = str(omada_accept["job"]["id"])
            omada_job = self._get_omada_client().wait_for_completion(omada_job_id)
            if str(omada_job.get("status", "")).lower() != "success":
                raise RuntimeError(f"Omada Site Creator job {omada_job_id} failed: {omada_job.get('error')}")
            if batch.workdrive_folder_id:
                omada_live_site_uploads = self._upload_omada_live_site_artifacts(omada_job, batch.workdrive_folder_id)

        return {
            "building_name": batch.building_name,
            "record_count": len(batch.records),
            "credential_mode": batch.credential_mode,
            "workflow_mode": batch.workflow_mode,
            "omada_operation": batch.omada_operation,
            "pdf_job_id": pdf_job_id,
            "omada_job_id": omada_job_id,
            "raw_payload_path": str(raw_payload_path),
            "normalized_payload_path": str(normalized_payload_path),
            "pdf_payload_path": pdf_payload_path,
            "omada_plan_path": omada_plan_path,
            "operation_plan_path": operation_plan_path,
            "pdf_job": pdf_job,
            "omada_plan_upload": omada_plan_upload,
            "operation_plan_upload": operation_plan_upload,
            "omada_job": omada_job,
            "omada_live_site_uploads": omada_live_site_uploads or None,
        }

    def _write_json(self, path: Path, payload: dict[str, Any]) -> Path:
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        return path

    def _upload_omada_live_site_artifacts(self, omada_job: dict[str, Any], parent_folder_id: str) -> list[dict[str, Any]]:
        report = omada_job.get("report")
        if not isinstance(report, dict):
            return []

        artifacts = report.get("artifacts")
        if not isinstance(artifacts, list):
            return []

        uploads: list[dict[str, Any]] = []
        workdrive_client = self._get_workdrive_client()

        for artifact in artifacts:
            if not isinstance(artifact, dict):
                continue
            if str(artifact.get("type", "")).strip() != "live-site-yaml":
                continue

            artifact_name = str(artifact.get("name", "")).strip() or "live-site.yaml"
            artifact_content = artifact.get("content")
            if isinstance(artifact_content, str):
                encoding = str(artifact.get("contentEncoding", "utf-8") or "utf-8")
                upload_result = workdrive_client.upload_bytes(
                    artifact_content.encode(encoding),
                    artifact_name,
                    parent_folder_id,
                    content_type="application/x-yaml",
                )
            else:
                artifact_path = Path(str(artifact.get("path", "")).strip())
                if not artifact_path.exists():
                    self.logger.warning("Omada live-site artifact path is missing: %s", artifact_path)
                    continue
                upload_result = workdrive_client.upload_file(artifact_path, parent_folder_id)
            upload_result["artifact_type"] = "live-site-yaml"
            uploads.append(upload_result)

        return uploads
