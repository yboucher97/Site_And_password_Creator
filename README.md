# Site And Password Creator

This repository combines the two existing projects needed for the WiFi + Omada workflow on one machine:

- `apps/password-pdf-generator`
- `apps/omada-site-creator`

## Install Both Apps On One Linux VM

Use the top-level installer to deploy both apps from this monorepo:

```bash
sudo PASSWORD_PDF_HOST=wifi-api.example.com \
OMADA_SITE_CREATOR_PUBLIC_HOST=omada.example.com \
bash <(curl -fsSL https://raw.githubusercontent.com/yboucher97/Site_And_password_Creator/main/install.sh)
```

What it does:

- clones or updates this repo into `/opt/site-and-password-creator`
- installs Python, Node.js, Caddy, and Playwright Chromium
- creates and enables:
  - `password-pdf-generator.service`
  - `omada-site-creator.service`
- creates default runtime files:
  - `/etc/password-pdf-generator.env`
  - `/etc/password-pdf-generator/brand_settings.json`
  - `/etc/omada-site-creator.env`
- optionally writes Caddy sites if you provide hostnames

Important runtime paths:

- combined code: `/opt/site-and-password-creator`
- PDF data: `/var/lib/password-pdf-generator`
- Omada data: `/var/lib/omada-site-creator`
- PDF config: `/etc/password-pdf-generator/brand_settings.json`
- PDF secrets: `/etc/password-pdf-generator.env`
- Omada secrets: `/etc/omada-site-creator.env`

Optional installer variables:

- `PASSWORD_PDF_HOST`
- `OMADA_SITE_CREATOR_PUBLIC_HOST`
- `PASSWORD_PDF_API_KEY`
- `OMADA_SITE_CREATOR_WEBHOOK_TOKEN`
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

## Suggested Deployment Model

- expose only the workflow/webhook entrypoint publicly
- keep the PDF generator and Omada creator on localhost behind Caddy or another reverse proxy
- run each app from its own runtime environment

## Notes

- This is a monorepo copy of the two app codebases.
- Build artifacts, runtime data, and nested Git metadata are intentionally excluded.
- The original standalone repositories can still be used independently.
- The combined installer deploys only the PDF generator and Omada site creator. `Site_Workflow_01` remains a separate repo.
