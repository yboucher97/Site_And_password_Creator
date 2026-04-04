# Workflow API

This app is the orchestration layer inside the monorepo. It sits in front of:

- `apps/password-pdf-service`
- `apps/omada-site-service`

## Flow

1. receive the inbound webhook
2. normalize the payload
3. generate SSIDs and passwords if `credential_mode=generated`
4. call the PDF generator
5. wait for PDF generation and WorkDrive upload to finish
6. if `workflow_mode=pdf_and_site`, build `omada-plan.yaml`
7. call Omada site creation

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
- skip Omada

`pdf_and_site`

- generate PDFs and exports
- upload to WorkDrive
- then create the Omada site

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
- If `credential_mode` is omitted, the workflow still infers generated vs predefined for backward compatibility
- The FastAPI Swagger docs are available at `/docs`
- The OpenAPI document is available at `/openapi.json`
