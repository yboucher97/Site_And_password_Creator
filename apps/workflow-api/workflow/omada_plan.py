from __future__ import annotations

from pathlib import Path

import yaml

from .config import AppSettings
from .models import WorkflowBatchRequest


def build_omada_plan(batch: WorkflowBatchRequest, settings: AppSettings) -> dict:
    controller: dict[str, object] = {
        "organizationName": settings.omada.organization_name,
        "baseUrl": settings.omada.cloud_base_url,
        "browserChannel": settings.omada.browser_channel,
        "headless": settings.omada.headless,
    }

    if settings.omada.device_username and settings.omada.device_password:
        controller["deviceAccount"] = {
            "username": settings.omada.device_username,
            "password": settings.omada.device_password,
        }

    lans: list[dict[str, int | str]] = []
    seen_vlans: set[int] = set()
    for record in batch.records:
        assert record.vlan_id is not None
        if record.vlan_id in seen_vlans:
            continue
        seen_vlans.add(record.vlan_id)
        lans.append(
            {
                "name": str(record.vlan_id),
                "vlanId": record.vlan_id,
            }
        )

    wlan_groups = [
        {
            "name": record.ssid,
            "ssids": [
                {
                    "name": record.ssid,
                    "security": "wpa2_psk",
                    "password": record.password,
                    "hideSsid": record.hidden,
                    "vlanId": record.vlan_id,
                }
            ],
        }
        for record in batch.records
    ]

    site: dict[str, object] = {
        "name": batch.site_name or batch.building_name,
        "region": batch.omada_region or settings.omada.region,
        "timezone": batch.omada_timezone or settings.omada.timezone,
        "scenario": batch.omada_scenario or settings.omada.scenario,
        "lans": lans,
        "wlanGroups": wlan_groups,
    }

    return {
        "version": 1,
        "controller": controller,
        "execution": {
            "stopOnError": True,
            "screenshots": True,
            "dryRun": False,
        },
        "sites": [site],
    }


def write_omada_plan(path: Path, plan: dict) -> Path:
    path.write_text(yaml.safe_dump(plan, sort_keys=False, allow_unicode=False), encoding="utf-8")
    return path
