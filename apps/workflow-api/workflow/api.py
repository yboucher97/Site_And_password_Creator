from __future__ import annotations

import os
import threading
from contextlib import asynccontextmanager
from typing import Any

from fastapi import Body, FastAPI, Header, HTTPException, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import BaseModel

from .config import load_settings
from .jobs import JobStore
from .logging_utils import configure_logging
from .models import parse_payload
from .pipeline import SiteWorkflowPipeline
from .utils import ensure_directory, sanitize_filename, utc_timestamp
from .zoho_oauth import ZohoOAuthManager


settings = load_settings()
logger = configure_logging(ensure_directory(settings.output.root_dir / "logs"))
job_store = JobStore(settings.output.jobs_dir, logger)
API_VERSION = "1.2.0"
PRIMARY_WEBHOOK_PATH = "/v1/site-and-password/webhooks/zoho"
PRIMARY_JOB_CREATE_PATH = "/v1/site-and-password/jobs"
PRIMARY_JOB_STATUS_PATH = "/v1/site-and-password/jobs/{job_id}"
ZOHO_OAUTH_START_PATH = "/v1/integrations/zoho/oauth/start"
ZOHO_OAUTH_CALLBACK_PATH = "/v1/integrations/zoho/oauth/callback"
ZOHO_OAUTH_STATUS_PATH = "/v1/integrations/zoho/oauth/status"
PLATFORM_DOCS_PATH = "/docs"
PLATFORM_OPENAPI_PATH = "/openapi.json"


class ServiceRoute(BaseModel):
    name: str
    path_prefix: str
    description: str


class PlatformIndexResponse(BaseModel):
    name: str
    version: str
    docs_url: str
    openapi_url: str
    primary_webhook: str
    services: list[ServiceRoute]


class HealthResponse(BaseModel):
    status: str
    app: str
    version: str
    jobs_dir: str
    pdf_base_url: str
    omada_base_url: str


class WorkflowJobAcceptedResponse(BaseModel):
    status: str
    job_id: str
    building_name: str
    record_count: int
    credential_mode: str
    workflow_mode: str
    job_status_url: str


class JobLookupResponse(BaseModel):
    job_id: str
    status: str
    created_at: str
    started_at: str | None = None
    finished_at: str | None = None
    request_summary: dict[str, Any]
    error: str | None = None
    result: dict[str, Any] | None = None


class ZohoOAuthStatusResponse(BaseModel):
    provider: str
    configured: bool
    connected: bool
    accounts_base_url: str
    redirect_uri: str | None
    authorization_start_url: str
    callback_url: str
    credentials_path: str
    connected_at: str | None = None
    scope: str | None = None
    configured_scopes: list[str]
    api_domain: str | None = None
    has_refresh_token: bool
    client_id_suffix: str | None = None


class ZohoOAuthConnectResponse(BaseModel):
    provider: str
    status: str
    authorization_url: str
    callback_url: str


class ZohoOAuthCallbackResponse(BaseModel):
    provider: str
    status: str
    connected: bool
    credentials_path: str
    scope: str | None = None
    api_domain: str | None = None


def _service_catalog() -> list[ServiceRoute]:
    return [
        ServiceRoute(
            name="workflow-api",
            path_prefix="/v1/site-and-password",
            description="Primary public API for webhook intake, job creation, and workflow job status.",
        ),
        ServiceRoute(
            name="password-pdf-service",
            path_prefix="/pdf",
            description="Raw internal PDF service proxied for health/debug access only.",
        ),
        ServiceRoute(
            name="omada-site-service",
            path_prefix="/omada",
            description="Raw internal Omada service proxied for health/debug access only.",
        ),
        ServiceRoute(
            name="workflow-raw",
            path_prefix="/workflow",
            description="Raw workflow service access for health/debug endpoints.",
        ),
        ServiceRoute(
            name="zoho-oauth",
            path_prefix="/v1/integrations/zoho",
            description="Server-side Zoho OAuth setup for WorkDrive and optional CRM integration.",
        ),
    ]


WORKFLOW_PAYLOAD_EXAMPLES = {
    "generated_pdf_and_site": {
        "summary": "Generated credentials, then PDFs and site creation",
        "value": {
            "building_name": "123 Main Street",
            "credential_mode": "generated",
            "workflow_mode": "pdf_and_site",
            "template_name": "legacy_template",
            "workdrive_folder_id": "replace-with-workdrive-folder-id",
            "site_name": "123 Main Street",
            "units": ["101", "102", "103"],
        },
    },
    "generated_pdf_only": {
        "summary": "Generated credentials, PDFs only",
        "value": {
            "building_name": "456 Example Avenue",
            "credential_mode": "generated",
            "workflow_mode": "pdf_only",
            "template_name": "legacy_template",
            "units": ["201", "202"],
        },
    },
    "predefined_pdf_only": {
        "summary": "Predefined credentials, PDFs only",
        "value": {
            "building_name": "789 Sample Road",
            "credential_mode": "predefined",
            "workflow_mode": "pdf_only",
            "template_name": "modern_template",
            "ssids": ["APT_301_AA", "APT_302_BB"],
            "passwords": ["1234ab5678!@", "5678cd1234#$"],
        },
    },
}


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Site workflow API starting")
    yield
    logger.info("Site workflow API shutting down")


app = FastAPI(
    title="Site And Password Creator API Platform",
    version=API_VERSION,
    description=(
        "Master API platform for Opticable workflow automation. "
        "This service accepts webhook payloads, generates or validates WiFi credentials, "
        "runs PDF generation and WorkDrive upload, and optionally creates Omada sites."
    ),
    lifespan=lifespan,
    openapi_tags=[
        {"name": "platform", "description": "Platform index, catalog, and shared health endpoints."},
        {"name": "site-and-password", "description": "Primary workflow endpoints for webhook intake and job tracking."},
        {"name": "integrations", "description": "External integration setup and status endpoints."},
        {"name": "compatibility", "description": "Legacy endpoints preserved for older webhook clients."},
    ],
)


def _validate_api_key(provided_api_key: str | None) -> None:
    expected_api_key = os.getenv(settings.api.api_key_env)
    if expected_api_key and provided_api_key != expected_api_key:
        raise HTTPException(status_code=401, detail="Invalid X-API-Key")


def _validate_browser_or_header_api_key(
    header_api_key: str | None,
    query_api_key: str | None = None,
) -> None:
    _validate_api_key(query_api_key or header_api_key)


def _zoho_oauth_manager() -> ZohoOAuthManager:
    return ZohoOAuthManager(settings.zoho_oauth)


def _zoho_status_payload() -> ZohoOAuthStatusResponse:
    status = _zoho_oauth_manager().status()
    return ZohoOAuthStatusResponse(
        provider="zoho",
        configured=status.configured,
        connected=status.connected,
        accounts_base_url=status.accounts_base_url,
        redirect_uri=status.redirect_uri,
        authorization_start_url=ZOHO_OAUTH_START_PATH,
        callback_url=ZOHO_OAUTH_CALLBACK_PATH,
        credentials_path=str(status.credentials_path),
        connected_at=status.connected_at,
        scope=status.scope,
        configured_scopes=list(status.scopes),
        api_domain=status.api_domain,
        has_refresh_token=status.has_refresh_token,
        client_id_suffix=status.client_id_suffix,
    )


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


def _health_payload() -> HealthResponse:
    return HealthResponse(
        status="ok",
        app="workflow-api",
        version=API_VERSION,
        jobs_dir=str(settings.output.jobs_dir),
        pdf_base_url=settings.pdf.base_url,
        omada_base_url=settings.omada.base_url,
    )


@app.get("/", response_model=PlatformIndexResponse, tags=["platform"])
@app.get("/api", response_model=PlatformIndexResponse, tags=["platform"])
async def platform_index() -> PlatformIndexResponse:
    return PlatformIndexResponse(
        name="Site And Password Creator API Platform",
        version=API_VERSION,
        docs_url=PLATFORM_DOCS_PATH,
        openapi_url=PLATFORM_OPENAPI_PATH,
        primary_webhook=PRIMARY_WEBHOOK_PATH,
        services=_service_catalog(),
    )


@app.get("/health", response_model=HealthResponse, tags=["compatibility"])
@app.get("/v1/system/health", response_model=HealthResponse, tags=["platform"])
async def health() -> HealthResponse:
    return _health_payload()


@app.get("/v1/system/catalog", response_model=PlatformIndexResponse, tags=["platform"])
async def platform_catalog() -> PlatformIndexResponse:
    return await platform_index()


@app.get("/v1/site-and-password/health", response_model=HealthResponse, tags=["site-and-password"])
async def workflow_health() -> HealthResponse:
    return _health_payload()


@app.get(ZOHO_OAUTH_STATUS_PATH, response_model=ZohoOAuthStatusResponse, tags=["integrations"])
async def zoho_oauth_status(
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
    api_key: str | None = Query(default=None),
) -> ZohoOAuthStatusResponse:
    _validate_browser_or_header_api_key(x_api_key, api_key)
    return _zoho_status_payload()


@app.get(ZOHO_OAUTH_START_PATH, response_model=ZohoOAuthConnectResponse, tags=["integrations"])
async def zoho_oauth_start(
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
    api_key: str | None = Query(default=None),
    response_mode: str = Query(default="redirect", pattern="^(redirect|json)$"),
):
    _validate_browser_or_header_api_key(x_api_key, api_key)

    manager = _zoho_oauth_manager()
    try:
        authorization_url = manager.build_authorization_redirect()
    except ValueError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    if response_mode == "json":
        return ZohoOAuthConnectResponse(
            provider="zoho",
            status="ready",
            authorization_url=authorization_url,
            callback_url=ZOHO_OAUTH_CALLBACK_PATH,
        )

    return RedirectResponse(authorization_url, status_code=307)


@app.get(ZOHO_OAUTH_CALLBACK_PATH, tags=["integrations"])
async def zoho_oauth_callback(
    code: str | None = Query(default=None),
    state: str | None = Query(default=None),
    error: str | None = Query(default=None),
    error_description: str | None = Query(default=None),
    response_mode: str = Query(default="html", pattern="^(html|json)$"),
):
    manager = _zoho_oauth_manager()
    if error:
        detail = error_description or error
        raise HTTPException(status_code=400, detail=f"Zoho authorization failed: {detail}")
    if not code or not state:
        raise HTTPException(status_code=400, detail="Zoho callback is missing the authorization code or state.")

    try:
        manager.validate_state(state)
        token_payload = manager.exchange_code(code)
        credentials_path = manager.save_credentials(token_payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    status_payload = ZohoOAuthCallbackResponse(
        provider="zoho",
        status="connected",
        connected=True,
        credentials_path=str(credentials_path),
        scope=str(token_payload.get("scope")) if token_payload.get("scope") else None,
        api_domain=str(token_payload.get("api_domain")) if token_payload.get("api_domain") else None,
    )

    if response_mode == "json":
        return status_payload.model_dump()

    html = f"""
<html>
  <head><title>Zoho Connected</title></head>
  <body style="font-family: sans-serif; padding: 2rem; line-height: 1.5;">
    <h1>Zoho Connected</h1>
    <p>The server stored the Zoho refresh token successfully.</p>
    <p>Credentials path: <code>{status_payload.credentials_path}</code></p>
    <p>Next check: <code>{ZOHO_OAUTH_STATUS_PATH}</code></p>
  </body>
</html>
"""
    return HTMLResponse(content=html, status_code=200)


@app.get("/jobs/{job_id}", response_model=JobLookupResponse, tags=["compatibility"])
@app.get(PRIMARY_JOB_STATUS_PATH, response_model=JobLookupResponse, tags=["site-and-password"])
async def get_job(job_id: str) -> dict:
    job = job_store.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


def _create_job_from_payload(payload: dict[str, Any]) -> WorkflowJobAcceptedResponse:
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

    return WorkflowJobAcceptedResponse(
        status="accepted",
        job_id=job_id,
        building_name=batch.building_name,
        record_count=len(batch.records),
        credential_mode=batch.credential_mode,
        workflow_mode=batch.workflow_mode,
        job_status_url=PRIMARY_JOB_STATUS_PATH.replace("{job_id}", job_id),
    )


@app.post(PRIMARY_JOB_CREATE_PATH, response_model=WorkflowJobAcceptedResponse, tags=["site-and-password"])
@app.post("/webhooks/zoho/site-and-password", response_model=WorkflowJobAcceptedResponse, tags=["compatibility"])
@app.post("/webhooks/zoho/site-workflow", response_model=WorkflowJobAcceptedResponse, tags=["compatibility"])
@app.post("/v1/site-and-password/webhooks/zoho", response_model=WorkflowJobAcceptedResponse, tags=["site-and-password"])
async def create_site_workflow_job(
    payload: dict[str, Any] = Body(..., openapi_examples=WORKFLOW_PAYLOAD_EXAMPLES),
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
) -> WorkflowJobAcceptedResponse:
    _validate_api_key(x_api_key)

    if not isinstance(payload, dict):
        raise HTTPException(status_code=422, detail="Payload must be a JSON object.")

    return _create_job_from_payload(payload)
