# Site And Password Workflow

This app is the orchestration layer inside the monorepo. It sits in front of:

- `apps/password-pdf-generator`
- `apps/omada-site-creator`

## Flow

1. receive the inbound webhook
2. normalize the payload
3. generate SSIDs and passwords if `credential_mode=generated`
4. call the PDF generator
5. wait for PDF generation and WorkDrive upload to finish
6. if `workflow_mode=pdf_and_site`, build `omada-plan.yaml`
7. call Omada site creation

## Endpoints

- `GET /health`
- `GET /jobs/{job_id}`
- `POST /webhooks/zoho/site-and-password`
- `POST /webhooks/zoho/site-workflow`

The `site-workflow` path remains as a compatibility alias.

## Credential Modes

`generated`

- send unit numbers or identifiers
- default SSID format is `APT_<unit>_<XX>`
- passwords are generated automatically

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
