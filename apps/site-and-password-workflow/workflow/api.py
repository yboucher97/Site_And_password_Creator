from __future__ import annotations

import os
import threading
from contextlib import asynccontextmanager

from fastapi import FastAPI, Header, HTTPException, Request

from .config import load_settings
from .jobs import JobStore
from .logging_utils import configure_logging
from .models import parse_payload
from .pipeline import SiteWorkflowPipeline
from .utils import ensure_directory, sanitize_filename, utc_timestamp


settings = load_settings()
logger = configure_logging(ensure_directory(settings.output.root_dir / "logs"))
job_store = JobStore(settings.output.jobs_dir, logger)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Site workflow API starting")
    yield
    logger.info("Site workflow API shutting down")


app = FastAPI(title="Site And Password Workflow", version="1.1.0", lifespan=lifespan)


def _validate_api_key(provided_api_key: str | None) -> None:
    expected_api_key = os.getenv(settings.api.api_key_env)
    if expected_api_key and provided_api_key != expected_api_key:
        raise HTTPException(status_code=401, detail="Invalid X-API-Key")


def _build_job_id(building_name: str) -> str:
    return f"{utc_timestamp()}-{sanitize_filename(building_name, default='site-and-password')}"


def _run_job(job_id: str, raw_payload: dict, batch) -> None:
    try:
        job_store.mark_running(job_id)
        pipeline = SiteWorkflowPipeline(settings, logger)
        result = pipeline.process(job_id, raw_payload, batch)
    except Exception as exc:  # pragma: no cover - runtime failure depends on downstream services
        logger.exception("Workflow job %s failed", job_id)
        job_store.mark_failed(job_id, str(exc))
    else:
        job_store.mark_succeeded(job_id, result)
        logger.info("Workflow job %s completed", job_id)


@app.get("/health")
async def health() -> dict[str, str]:
    return {
        "status": "ok",
        "app": "site-and-password-workflow",
        "jobs_dir": str(settings.output.jobs_dir),
        "pdf_base_url": settings.pdf.base_url,
        "omada_base_url": settings.omada.base_url,
    }


@app.get("/jobs/{job_id}")
async def get_job(job_id: str) -> dict:
    job = job_store.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@app.post("/webhooks/zoho/site-workflow")
@app.post("/webhooks/zoho/site-and-password")
async def create_site_workflow_job(
    request: Request,
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
) -> dict:
    _validate_api_key(x_api_key)

    try:
        payload = await request.json()
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Invalid JSON body: {exc}") from exc

    if not isinstance(payload, dict):
        raise HTTPException(status_code=422, detail="Payload must be a JSON object.")

    try:
        batch = parse_payload(payload, settings)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    job_id = _build_job_id(batch.building_name)
    job_store.create(
        job_id,
        {
            "building_name": batch.building_name,
            "record_count": len(batch.records),
            "credential_mode": batch.credential_mode,
            "workflow_mode": batch.workflow_mode,
            "template_name": batch.template_name,
            "site_name": batch.site_name or batch.building_name,
        },
    )

    worker = threading.Thread(target=_run_job, args=(job_id, payload, batch), daemon=True)
    worker.start()

    return {
        "status": "accepted",
        "job_id": job_id,
        "building_name": batch.building_name,
        "record_count": len(batch.records),
        "credential_mode": batch.credential_mode,
        "workflow_mode": batch.workflow_mode,
        "job_status_url": f"/jobs/{job_id}",
    }
