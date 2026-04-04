# Workflow API

This app is the orchestration layer inside the monorepo. It sits in front of:

- `apps/password-pdf-service`
- `apps/omada-site-service`

## Flow

1. receive the inbound webhook
2. normalize the payload
3. generate SSIDs and passwords if `credential_mode=generated`
4. always build `omada-plan.yaml`
5. if the workflow includes PDFs, call the PDF generator
6. if the workflow includes PDFs, wait for PDF generation and WorkDrive upload to finish
7. if `workdrive_folder_id` is present, upload `omada-plan.yaml` to WorkDrive
8. if the workflow includes Omada, call Omada site creation

## Endpoints

- `GET /`
- `GET /api`
- `GET /docs`
- `GET /openapi.json`
- `GET /v1/system/health`
- `GET /v1/system/catalog`
- `GET /v1/integrations/zoho/oauth/start`
- `GET /v1/integrations/zoho/oauth/callback`
- `GET /v1/integrations/zoho/oauth/status`
- `GET /v1/omada/sites`
- `GET /v1/omada/sites/{site_id}`
- `GET /v1/omada/sites/{site_id}/lans`
- `GET /v1/omada/sites/{site_id}/wlan-groups`
- `GET /v1/omada/sites/{site_id}/wlan-groups/{wlan_id}/ssids`
- `POST /v1/omada/jobs`
- `GET /v1/omada/jobs/{job_id}`
- `POST /v1/workflows/site-and-password`
- `GET /v1/workflows/site-and-password/jobs/{job_id}`
- `GET /v1/site-and-password/health`
- `GET /v1/site-and-password/jobs/{job_id}`
- `POST /v1/site-and-password/jobs`
- `POST /v1/site-and-password/webhooks/zoho`
- `GET /health`
- `GET /jobs/{job_id}`
- `POST /webhooks/zoho/site-and-password`
- `POST /webhooks/zoho/site-workflow`

The unversioned paths and the older `/v1/site-and-password/*` paths remain as compatibility aliases.

## Direct Omada Plan Webhook

Use `POST /v1/omada/jobs` when you already have an Omada YAML or JSON plan and want the master API host to forward it directly to the Omada service.

- send raw YAML, raw JSON, or a JSON plan body
- include `X-Plan-File-Name` if you want to control the saved file name
- poll `GET /v1/omada/jobs/{job_id}` for completion

This is the clean standalone path for site-template style jobs that should not go through password/PDF generation.

## Credential Modes

`generated`

- send unit numbers or identifiers
- default SSID format is `APT_<unit>_<XX>`
- passwords are generated automatically and exclude ambiguous letters like `i` and `l`

`predefined`

- send explicit SSIDs and passwords
- the workflow uses them unchanged

## Workflow Modes

`pdf_only`

- generate PDFs and exports
- upload to WorkDrive
- also generate and upload `omada-plan.yaml`
- skip Omada

`pdf_and_site`

- generate PDFs and exports
- upload to WorkDrive
- also generate and upload `omada-plan.yaml`
- then create the Omada site

`site_only`

- skip PDFs and password documents
- still generate `omada-plan.yaml`
- upload `omada-plan.yaml` to WorkDrive when `workdrive_folder_id` is provided
- create the Omada site directly

## Current Omada Mutation Behavior

Today the Omada service is still `ensure/create-only`:

- if a site does not exist, it is created
- if a LAN does not exist, it is created
- if a WLAN group does not exist, it is created
- if an SSID does not exist, it is created
- if an item already exists, it is left unchanged

That means true in-place update behavior for existing VLANs, WLAN groups, and SSIDs is not implemented yet.

For AP assignment safety:

- creating or updating inside the same existing WLAN group is the correct future approach
- deleting and recreating WLAN groups would risk changing AP assignment behavior
- the next safe increment is an explicit update policy per object, not implicit overwrite

## Zoho OAuth

Recommended Zoho client type:

- `Server-based Application`

Important env vars:

- `ZOHO_OAUTH_CLIENT_ID`
- `ZOHO_OAUTH_CLIENT_SECRET`
- `ZOHO_OAUTH_ACCOUNTS_BASE_URL`
- `ZOHO_OAUTH_REDIRECT_URI`
- `ZOHO_OAUTH_SCOPES`
- `ZOHO_OAUTH_CREDENTIALS_PATH`

Typical callback path:

- `/v1/integrations/zoho/oauth/callback`

The workflow stores the approved Zoho OAuth credentials in the shared credential file, and the PDF service reads that file automatically on future jobs.

## Example Payload

See [example_payload.json](./input/example_payload.json).

## Local Run

```bash
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
export SITE_WORKFLOW_API_KEY=replace-with-a-long-random-secret
uvicorn workflow.api:app --host 127.0.0.1 --port 8100
```

## Notes

- Default SSID prefix: `APT_`
- Default suffix length: `2`
- Default suffix casing: uppercase
- Default `workflow_mode`: `pdf_and_site`
- `omada-plan.yaml` is generated for every workflow job
- If `credential_mode` is omitted, the workflow still infers generated vs predefined for backward compatibility
- The FastAPI Swagger docs are available at `/docs`
- The OpenAPI document is available at `/openapi.json`
