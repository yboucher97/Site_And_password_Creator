# Architecture

## Public Entry

One public hostname fronts the platform:

- `api01.opticable.ca`

Caddy routes path prefixes to internal localhost services.

## Public Paths

- `/`
- `/docs`
- `/openapi.json`
- `/v1/system/*`
- `/v1/integrations/zoho/*`
- `/v1/site-and-password/*`
- `/pdf/*`
- `/omada/*`
- `/workflow/*`

## Internal Services

### Workflow API

- default public app behind `/`
- owns the OpenAPI surface
- receives webhook requests
- coordinates downstream services

### Password PDF Service

- internal PDF worker API
- creates PDFs and exports
- uploads artifacts to WorkDrive

### Omada Site Service

- internal Omada worker API
- creates sites and wireless/network objects

## Runtime Model

- one Linux VM
- one reverse proxy
- multiple localhost services
- one documented API surface
- shared server-managed Zoho credential file

## Deployment Model

- rebuild from GitHub onto a new VM
- restore env/config
- repoint DNS

That keeps the VM disposable and the platform reproducible.
