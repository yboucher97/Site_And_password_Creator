from __future__ import annotations

import json
import os
from pathlib import Path

from .exceptions import ConfigurationError


def _clean_env(name: str) -> str | None:
    value = os.getenv(name)
    if value is None:
        return None
    text = value.strip()
    return text or None


def load_zoho_credentials() -> dict[str, str | None]:
    payload: dict[str, str | None] = {}

    credentials_path = _clean_env("ZOHO_WORKDRIVE_CREDENTIALS_PATH")
    if credentials_path:
        path = Path(credentials_path)
        if path.exists():
            raw_payload = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(raw_payload, dict):
                raise ConfigurationError(f"Unexpected Zoho credential file format: {path}")
            for key in ("client_id", "client_secret", "refresh_token", "access_token"):
                value = raw_payload.get(key)
                if value is not None:
                    payload[key] = str(value).strip()

    env_overrides = {
        "client_id": _clean_env("ZOHO_WORKDRIVE_CLIENT_ID"),
        "client_secret": _clean_env("ZOHO_WORKDRIVE_CLIENT_SECRET"),
        "refresh_token": _clean_env("ZOHO_WORKDRIVE_REFRESH_TOKEN"),
        "access_token": _clean_env("ZOHO_WORKDRIVE_ACCESS_TOKEN"),
    }
    for key, value in env_overrides.items():
        if value:
            payload[key] = value

    return payload
