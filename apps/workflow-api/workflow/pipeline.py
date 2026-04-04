from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .clients import OmadaClient, PdfGeneratorClient
from .config import AppSettings
from .models import WorkflowBatchRequest
from .omada_plan import build_omada_plan, write_omada_plan
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
        omada_plan_path = str(omada_plan_written)

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
        if batch.workdrive_folder_id:
            self.logger.info("Workflow job %s: uploading Omada plan to WorkDrive", job_id)
            omada_plan_upload = self._get_workdrive_client().upload_file(omada_plan_written, batch.workdrive_folder_id)

        omada_job_id: str | None = None
        omada_job: dict[str, Any] | None = None

        if batch.workflow_mode in {"pdf_and_site", "site_only"}:
            self.logger.info("Workflow job %s: creating Omada Site Creator job", job_id)
            omada_accept = self._get_omada_client().create_job(omada_plan, omada_plan_written.name)
            omada_job_id = str(omada_accept["job"]["id"])
            omada_job = self._get_omada_client().wait_for_completion(omada_job_id)
            if str(omada_job.get("status", "")).lower() != "success":
                raise RuntimeError(f"Omada Site Creator job {omada_job_id} failed: {omada_job.get('error')}")

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
            "pdf_job": pdf_job,
            "omada_plan_upload": omada_plan_upload,
            "omada_job": omada_job,
        }

    def _write_json(self, path: Path, payload: dict[str, Any]) -> Path:
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        return path
