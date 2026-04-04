from __future__ import annotations

import json
import mimetypes
from pathlib import Path
from typing import Any

import httpx

from .config import ZohoOAuthSettings


class WorkflowWorkDriveError(RuntimeError):
    pass


class WorkflowWorkDriveClient:
    def __init__(self, oauth_settings: ZohoOAuthSettings, logger, target_folder_name: str = "Document locataire") -> None:
        self.oauth_settings = oauth_settings
        self.logger = logger
        self.target_folder_name = target_folder_name.strip()
        self._access_token: str | None = None

    def upload_file(self, path: Path, parent_folder_id: str) -> dict[str, Any]:
        timeout = httpx.Timeout(60.0, connect=20.0)
        with httpx.Client(timeout=timeout) as client:
            headers = self._get_auth_headers(client)
            folder_id = self._resolve_upload_folder_id(client, headers, parent_folder_id)
            params = {
                "parent_id": folder_id,
                "filename": path.name,
                "override-name-exist": "true",
            }

            with path.open("rb") as handle:
                content_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
                response = client.post(
                    f"{self._api_base_url()}/upload",
                    headers=headers,
                    params=params,
                    files={"content": (path.name, handle, content_type)},
                )

        if response.status_code >= 400:
            raise WorkflowWorkDriveError(
                f"WorkDrive upload failed for '{path.name}' with status {response.status_code}: {response.text}"
            )

        try:
            payload = response.json()
        except json.JSONDecodeError:
            payload = {"raw_response": response.text}

        self.logger.info("Uploaded workflow artifact '%s' to WorkDrive folder %s", path.name, folder_id)
        return {
            "filename": path.name,
            "folder_id": folder_id,
            "status_code": response.status_code,
            "response": payload,
        }

    def _resolve_upload_folder_id(self, client: httpx.Client, headers: dict[str, str], parent_folder_id: str) -> str:
        if not self.target_folder_name:
            return parent_folder_id

        child_id = self._find_child_folder_id(client, headers, parent_folder_id)
        if child_id:
            return child_id

        self.logger.info(
            "Workflow WorkDrive child folder '%s' was missing inside parent %s. Creating it now.",
            self.target_folder_name,
            parent_folder_id,
        )
        return self._create_child_folder_id(client, headers, parent_folder_id)

    def _find_child_folder_id(self, client: httpx.Client, headers: dict[str, str], parent_folder_id: str) -> str | None:
        response = client.get(
            f"{self._api_base_url()}/files/{parent_folder_id}/files",
            headers=headers,
            params={"filter[type]": "folder", "page[limit]": 200},
        )
        if response.status_code >= 400:
            raise WorkflowWorkDriveError(
                f"WorkDrive folder lookup failed for parent '{parent_folder_id}' with status {response.status_code}: {response.text}"
            )

        payload = response.json()
        for item in payload.get("data", []):
            attributes = item.get("attributes") if isinstance(item, dict) else None
            if not isinstance(attributes, dict):
                continue
            if str(attributes.get("name", "")).strip() == self.target_folder_name:
                folder_id = item.get("id")
                if folder_id:
                    return str(folder_id)
        return None

    def _create_child_folder_id(self, client: httpx.Client, headers: dict[str, str], parent_folder_id: str) -> str:
        response = client.post(
            f"{self._api_base_url()}/files",
            headers=headers,
            json={
                "data": {
                    "type": "files",
                    "attributes": {
                        "name": self.target_folder_name,
                        "parent_id": parent_folder_id,
                        "type": "folder",
                    },
                }
            },
        )
        if response.status_code >= 400:
            raise WorkflowWorkDriveError(
                f"WorkDrive child folder creation failed for parent '{parent_folder_id}' with status {response.status_code}: {response.text}"
            )

        payload = response.json()
        data = payload.get("data")
        if not isinstance(data, dict) or not data.get("id"):
            raise WorkflowWorkDriveError(
                f"WorkDrive child folder creation returned an unexpected payload: {payload}"
            )
        return str(data["id"])

    def _get_auth_headers(self, client: httpx.Client) -> dict[str, str]:
        access_token = self._get_access_token(client)
        return {
            "Authorization": f"Zoho-oauthtoken {access_token}",
            "Accept": "application/vnd.api+json",
        }

    def _get_access_token(self, client: httpx.Client) -> str:
        if self._access_token:
            return self._access_token

        credentials = self._load_credentials()
        refresh_token = credentials.get("refresh_token")
        client_id = credentials.get("client_id")
        client_secret = credentials.get("client_secret")
        if refresh_token and client_id and client_secret:
            response = client.post(
                f"{self.oauth_settings.accounts_base_url}/oauth/v2/token",
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": refresh_token,
                    "client_id": client_id,
                    "client_secret": client_secret,
                },
            )
            if response.status_code >= 400:
                raise WorkflowWorkDriveError(
                    f"Zoho OAuth refresh failed with status {response.status_code}: {response.text}"
                )
            payload = response.json()
            access_token = payload.get("access_token")
            if not access_token:
                raise WorkflowWorkDriveError(f"Zoho OAuth refresh did not return an access token: {payload}")
            self._access_token = str(access_token)
            return self._access_token

        direct_token = credentials.get("access_token")
        if direct_token:
            self._access_token = str(direct_token)
            return self._access_token

        raise WorkflowWorkDriveError(
            "Missing Zoho OAuth credentials. Complete the server-side Zoho OAuth flow and "
            "ensure ZOHO_OAUTH_CREDENTIALS_PATH points at the generated credential file."
        )

    def _load_credentials(self) -> dict[str, Any]:
        path = self.oauth_settings.credentials_path
        if not path.exists():
            raise WorkflowWorkDriveError(
                "Zoho OAuth credentials file is missing. Complete the server-side Zoho OAuth flow first."
            )

        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise WorkflowWorkDriveError(f"Unexpected Zoho credential file format at {path}")
        return payload

    def _api_base_url(self) -> str:
        credentials = self._load_credentials()
        api_domain = str(credentials.get("api_domain", "")).strip().rstrip("/")
        if api_domain:
            return f"{api_domain}/workdrive/api/v1"
        accounts_base = self.oauth_settings.accounts_base_url.rstrip("/")
        accounts_to_api = {
            "https://accounts.zoho.com": "https://www.zohoapis.com",
            "https://accounts.zoho.eu": "https://www.zohoapis.eu",
            "https://accounts.zoho.in": "https://www.zohoapis.in",
            "https://accounts.zoho.com.au": "https://www.zohoapis.com.au",
        }
        api_domain = accounts_to_api.get(accounts_base, "https://www.zohoapis.com")
        return f"{api_domain}/workdrive/api/v1"
