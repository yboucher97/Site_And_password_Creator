# Site And Password Creator

This repository combines the two existing projects needed for the WiFi + Omada workflow on one machine:

- `apps/password-pdf-generator`
- `apps/omada-site-creator`

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
