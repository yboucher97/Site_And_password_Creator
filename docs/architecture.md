# Architecture

## Public Entry

One public hostname fronts the platform:

- `api01.opticable.ca`

Caddy routes path prefixes to internal localhost services.

## Public Paths

Current public paths are a mix of platform routes and compatibility routes.

Long-term, the public API should converge on:

- `/v1/system/*`
- `/v1/integrations/*`
- `/v1/workflows/*`
- `/v1/omada/*`
- `/v1/zoho/*`

See [API Blueprint](./api-blueprint.md).

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
- should remain the orchestrator for multi-step flows

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

## Current Workflow Fan-Out

For the site-and-password automation, one inbound webhook currently triggers:

1. workflow normalization
2. password and SSID generation when needed
3. PDF generation
4. WorkDrive upload
5. optional Omada site creation

That is one public workflow request fanning out into multiple internal service calls.

## Deployment Model

- rebuild from GitHub onto a new VM
- restore env/config
- repoint DNS

That keeps the VM disposable and the platform reproducible.
