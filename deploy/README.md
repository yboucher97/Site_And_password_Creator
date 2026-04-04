# Deploy

Deployment assets for the monorepo can live here when they apply to the whole platform.

Current note:

- the root `install.sh` remains the canonical Linux bootstrap entrypoint because it is convenient to fetch directly with `curl`

Service-specific deployment files stay inside each service folder under `apps/*/deploy/`.
