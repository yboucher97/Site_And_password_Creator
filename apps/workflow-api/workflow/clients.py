from __future__ import annotations

import time
from typing import Any

import httpx

from .config import DownstreamOmadaSettings, DownstreamPdfSettings


class PdfGeneratorClient:
    def __init__(self, settings: DownstreamPdfSettings) -> None:
        self.settings = settings

    def create_job(self, payload: dict[str, Any]) -> dict[str, Any]:
        headers: dict[str, str] = {}
        if self.settings.api_key:
            headers["X-API-Key"] = self.settings.api_key

        response = httpx.post(
            f"{self.settings.base_url}/webhooks/zoho/wifi-pdfs",
            json=payload,
            headers=headers,
            timeout=30,
        )
        response.raise_for_status()
        return response.json()

    def get_job(self, job_id: str) -> dict[str, Any]:
        response = httpx.get(f"{self.settings.base_url}/jobs/{job_id}", timeout=30)
        response.raise_for_status()
        return response.json()

    def wait_for_completion(self, job_id: str) -> dict[str, Any]:
        deadline = time.monotonic() + self.settings.timeout_seconds
        while time.monotonic() < deadline:
            job = self.get_job(job_id)
            status = str(job.get("status", "")).lower()
            if status in {"completed", "failed"}:
                return job
            time.sleep(self.settings.poll_interval_seconds)
        raise TimeoutError(f"Timed out waiting for Password_PDF_Generator job {job_id}.")


class OmadaClient:
    def __init__(self, settings: DownstreamOmadaSettings) -> None:
        if not settings.webhook_token:
            raise ValueError("OMADA_SITE_CREATOR_WEBHOOK_TOKEN is required.")
        self.settings = settings

    def create_job(self, plan: dict[str, Any], file_name: str) -> dict[str, Any]:
        response = httpx.post(
            f"{self.settings.base_url}/api/webhooks/run",
            json={
                "fileName": file_name,
                "plan": plan,
            },
            headers={
                "Authorization": f"Bearer {self.settings.webhook_token}",
            },
            timeout=30,
        )
        response.raise_for_status()
        return response.json()

    def get_job(self, job_id: str) -> dict[str, Any]:
        response = httpx.get(f"{self.settings.base_url}/api/jobs/{job_id}", timeout=30)
        response.raise_for_status()
        body = response.json()
        return body["job"]

    def wait_for_completion(self, job_id: str) -> dict[str, Any]:
        deadline = time.monotonic() + self.settings.timeout_seconds
        while time.monotonic() < deadline:
            job = self.get_job(job_id)
            status = str(job.get("status", "")).lower()
            if status in {"success", "failed"}:
                return job
            time.sleep(self.settings.poll_interval_seconds)
        raise TimeoutError(f"Timed out waiting for Omada Site Creator job {job_id}.")
