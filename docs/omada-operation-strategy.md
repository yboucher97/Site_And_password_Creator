# Omada Operation Strategy

This document defines the scalable contract for Omada-triggered automation.

## Source Of Truth

Use two sources for different kinds of truth:

- WorkDrive artifacts for desired credentials and plan files
- Live Omada discovery for what currently exists on the controller

Do not treat live Omada discovery as the password source of truth. Current discovery gives you site, LAN, WLAN group, and SSID identity data, but not the current PSK in a reliable public shape.

## Recommended Public Contract

Use one Omada-focused trigger model:

- `operation`: `create | upsert | update | get`
- `source_preference`: `yaml_then_txt | yaml_only | txt_only`
- `workdrive_folder_id`
- `site_name`
- `building_name`
- optional Omada defaults:
  - `omada_region`
  - `omada_timezone`
  - `omada_scenario`

## Resolution Order

For WorkDrive-driven site application:

1. open the requested WorkDrive building folder
2. if a `Document locataire` child folder exists, read from that child
3. if YAML exists, use it first
4. if no YAML exists, fall back to the TXT credential export
5. if neither exists, fail clearly

Preferred YAML names:

- `create.yaml`
- `upsert.yaml`
- `update.yaml`
- `omada-plan.yaml`

TXT fallback:

- `Mot de passe <building>.txt`
- or any `.txt` file in that target folder when it is the only TXT export

## Endpoint Model

Current public routes:

- `POST /v1/omada/jobs`
  Raw YAML/JSON Omada plan execution
- `GET /v1/omada/jobs/{jobId}`
  Omada job tracking
- `POST /v1/omada/workdrive/jobs`
  Resolve WorkDrive folder, use YAML first, TXT second
- `GET /v1/omada/sites/{siteId}/snapshot`
  Export live Omada state as JSON or YAML

## Operation Meaning

`create`

- intended for a brand new site or a brand new batch of objects
- if the folder already contains `create.yaml`, prefer it
- if only TXT exists, generate a `create.yaml` plan from the TXT export

`upsert`

- intended for “create missing, reuse existing”
- today this maps cleanly to the current Omada ensure/create engine
- if TXT is the fallback source, generate `upsert.yaml`

`update`

- reserved for future in-place mutation of existing VLANs, WLAN groups, and SSIDs
- should preserve AP assignment by updating inside the existing WLAN group instead of deleting/recreating it
- today this should be treated as contract-only, not as live execution behavior

`get`

- export the live controller state into a stable YAML or JSON shape
- use this as a review artifact or as a starting point for later update work
- current live snapshot intentionally marks SSID passwords as unavailable

## Zoho Webhook Strategy

Use explicit fields in Zoho instead of one-off endpoint proliferation.

Recommended Zoho webhook routing rule:

- `domain = omada`
- `operation = create | upsert | update | get`
- `source_preference = yaml_then_txt | yaml_only | txt_only`

That lets one stable endpoint handle many future behaviors:

- `POST /v1/omada/workdrive/jobs`

Example:

```json
{
  "domain": "omada",
  "operation": "upsert",
  "source_preference": "yaml_then_txt",
  "workdrive_folder_id": "replace-with-workdrive-folder-id",
  "site_name": "123 Main Street",
  "building_name": "123 Main Street",
  "omada_region": "Canada",
  "omada_timezone": "America/Toronto",
  "omada_scenario": "Office"
}
```

For workflow-style PDF generation plus site creation, continue using:

- `POST /v1/workflows/site-and-password`

That route remains the right choice for multi-step automation.

## Why This Scales

- one Omada entrypoint for artifact-driven site actions
- one workflow entrypoint for multi-step business flows
- explicit operation type instead of hidden inference
- YAML files for human review and re-use
- TXT fallback keeps old jobs usable even when YAML is missing
- live snapshot gives you a stable read contract before true update mode lands
