# Site And Password Creator

This repository combines the three apps needed for the WiFi + Omada workflow on one machine:

- `apps/password-pdf-generator`
- `apps/omada-site-creator`
- `apps/site-and-password-workflow`

## Install On One Linux VM

Use the top-level installer to deploy the full stack from this monorepo:

```bash
sudo SITE_AND_PASSWORD_API_HOST=api01.opticable.ca \
bash <(curl -fsSL https://raw.githubusercontent.com/yboucher97/Site_And_password_Creator/main/install.sh)
```

What it does:

- clones or updates this repo into `/opt/site-and-password-creator`
- installs Python, Node.js, Caddy, and Playwright Chromium
- creates and enables:
  - `password-pdf-generator.service`
  - `omada-site-creator.service`
  - `site-and-password-workflow.service`
- creates default runtime files:
  - `/etc/password-pdf-generator.env`
  - `/etc/password-pdf-generator/brand_settings.json`
  - `/etc/omada-site-creator.env`
  - `/etc/site-and-password-workflow.env`
- optionally writes one master Caddy site if you provide `SITE_AND_PASSWORD_API_HOST`

Important runtime paths:

- combined code: `/opt/site-and-password-creator`
- PDF data: `/var/lib/password-pdf-generator`
- Omada data: `/var/lib/omada-site-creator`
- Workflow data: `/var/lib/site-and-password-workflow`
- PDF config: `/etc/password-pdf-generator/brand_settings.json`
- PDF secrets: `/etc/password-pdf-generator.env`
- Omada secrets: `/etc/omada-site-creator.env`
- Workflow secrets: `/etc/site-and-password-workflow.env`

Optional installer variables:

- `SITE_AND_PASSWORD_API_HOST`
- `PASSWORD_PDF_API_KEY`
- `OMADA_SITE_CREATOR_WEBHOOK_TOKEN`
- `SITE_AND_PASSWORD_WORKFLOW_API_KEY`
- `PASSWORD_PDF_ENABLE_WORKDRIVE`
- `PASSWORD_PDF_ZOHO_REGION`
- `ZOHO_WORKDRIVE_CLIENT_ID`
- `ZOHO_WORKDRIVE_CLIENT_SECRET`
- `ZOHO_WORKDRIVE_REFRESH_TOKEN`
- `ZOHO_WORKDRIVE_PARENT_FOLDER_ID`
- `OMADA_SITE_CREATOR_CLOUD_EMAIL`
- `OMADA_SITE_CREATOR_CLOUD_PASSWORD`
- `OMADA_SITE_CREATOR_DEVICE_USERNAME`
- `OMADA_SITE_CREATOR_DEVICE_PASSWORD`

## Included Apps

### Password PDF Generator

Location: `apps/password-pdf-generator`

Purpose:

- generate WiFi PDFs
- generate merged PDF, ZIP, and text exports
- upload the output to Zoho WorkDrive

### Omada Site Creator

Location: `apps/omada-site-creator`

Purpose:

- receive a plan file
- authenticate to TP-Link Omada
- create sites, LANs, WLAN groups, and SSIDs

### Site And Password Workflow

Location: `apps/site-and-password-workflow`

Purpose:

- receive the Zoho webhook
- decide whether credentials are generated or predefined
- run the PDF generator first
- optionally create the Omada site after PDFs succeed

## Public Endpoint Layout

With `SITE_AND_PASSWORD_API_HOST=api01.opticable.ca`, Caddy exposes:

- `https://api01.opticable.ca/webhooks/zoho/site-and-password`
- `https://api01.opticable.ca/health`
- `https://api01.opticable.ca/pdf/health`
- `https://api01.opticable.ca/omada/api/health`
- `https://api01.opticable.ca/workflow/health`

The root host proxies to the workflow app by default, so Zoho can post directly to:

- `https://api01.opticable.ca/webhooks/zoho/site-and-password`

## Workflow Modes

Supported webhook flags:

- `credential_mode: generated | predefined`
- `workflow_mode: pdf_only | pdf_and_site`

`generated`:

- send units like `101,102,103`
- the VM generates SSIDs like `APT_101_XX`
- the VM generates passwords

`predefined`:

- send final SSIDs and passwords
- the VM uses them as-is

`pdf_only`:

- creates PDFs, merged PDF, ZIP, and text export
- uploads to WorkDrive
- skips Omada

`pdf_and_site`:

- creates PDFs first
- uploads to WorkDrive
- then creates the Omada site from the same generated batch

## Suggested Deployment Model

- expose only the workflow/webhook entrypoint publicly
- keep the PDF generator and Omada creator on localhost behind Caddy or another reverse proxy
- run each app from its own runtime environment

## Notes

- This is the main monorepo for the combined system.
- Build artifacts, runtime data, and nested Git metadata are intentionally excluded.
- The older standalone workflow repo can be retired after you finish this migration.
