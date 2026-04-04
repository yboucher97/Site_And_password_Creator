#!/usr/bin/env bash
set -euo pipefail

APP_NAME="opticable-api-platform"
REPO_URL="${SITE_AND_PASSWORD_CREATOR_REPO_URL:-https://github.com/yboucher97/opticable-api-platform.git}"
REPO_REF="${SITE_AND_PASSWORD_CREATOR_REPO_REF:-main}"
INSTALL_DIR="${SITE_AND_PASSWORD_CREATOR_INSTALL_DIR:-/opt/opticable-api-platform}"

PUBLIC_API_HOST="${SITE_AND_PASSWORD_API_HOST:-}"
SHARED_GROUP="${SITE_AND_PASSWORD_SHARED_GROUP:-siteandpassword}"
SHARED_DATA_DIR="${SITE_AND_PASSWORD_SHARED_DATA_DIR:-/var/lib/opticable-api-platform/shared}"
ZOHO_OAUTH_CREDENTIALS_PATH="${ZOHO_OAUTH_CREDENTIALS_PATH:-${SHARED_DATA_DIR}/zoho-oauth.json}"

PDF_APP_DIR="${INSTALL_DIR}/apps/password-pdf-service"
PDF_SERVICE_NAME="${PASSWORD_PDF_SERVICE_NAME:-password-pdf-generator}"
PDF_SERVICE_USER="${PASSWORD_PDF_SERVICE_USER:-passwordpdf}"
PDF_DATA_DIR="${PASSWORD_PDF_DATA_DIR:-/var/lib/password-pdf-generator}"
PDF_CONFIG_DIR="${PASSWORD_PDF_CONFIG_DIR:-/etc/password-pdf-generator}"
PDF_CONFIG_PATH="${PDF_CONFIG_DIR}/brand_settings.json"
PDF_ENV_FILE="${PASSWORD_PDF_ENV_FILE:-/etc/password-pdf-generator.env}"
PDF_PORT="${PASSWORD_PDF_PORT:-8000}"
PDF_HOST="${PASSWORD_PDF_HOST:-}"

OMADA_APP_DIR="${INSTALL_DIR}/apps/omada-site-service"
OMADA_SERVICE_NAME="${OMADA_SITE_CREATOR_SERVICE_NAME:-omada-site-creator}"
OMADA_SERVICE_USER="${OMADA_SITE_CREATOR_USER:-omada-site-creator}"
OMADA_DATA_DIR="${OMADA_SITE_CREATOR_DATA_DIR:-/var/lib/omada-site-creator}"
OMADA_ENV_FILE="${OMADA_SITE_CREATOR_ENV_FILE:-/etc/omada-site-creator.env}"
OMADA_PORT="${OMADA_SITE_CREATOR_PORT:-3210}"
OMADA_HOST="${OMADA_SITE_CREATOR_PUBLIC_HOST:-}"

WORKFLOW_APP_DIR="${INSTALL_DIR}/apps/workflow-api"
WORKFLOW_SERVICE_NAME="${SITE_AND_PASSWORD_WORKFLOW_SERVICE_NAME:-site-and-password-workflow}"
WORKFLOW_SERVICE_USER="${SITE_AND_PASSWORD_WORKFLOW_USER:-sitepasswordworkflow}"
WORKFLOW_DATA_DIR="${SITE_AND_PASSWORD_WORKFLOW_DATA_DIR:-/var/lib/site-and-password-workflow}"
WORKFLOW_ENV_FILE="${SITE_AND_PASSWORD_WORKFLOW_ENV_FILE:-/etc/site-and-password-workflow.env}"
WORKFLOW_PORT="${SITE_AND_PASSWORD_WORKFLOW_PORT:-8100}"
WORKFLOW_HOST="${SITE_AND_PASSWORD_WORKFLOW_PUBLIC_HOST:-}"

PASSWORD_PDF_API_KEY="${PASSWORD_PDF_API_KEY:-${WIFI_PDF_API_KEY:-}}"
OMADA_SITE_CREATOR_WEBHOOK_TOKEN="${OMADA_SITE_CREATOR_WEBHOOK_TOKEN:-}"
SITE_AND_PASSWORD_WORKFLOW_API_KEY="${SITE_AND_PASSWORD_WORKFLOW_API_KEY:-${SITE_WORKFLOW_API_KEY:-}}"
PASSWORD_PDF_ENABLE_WORKDRIVE="${PASSWORD_PDF_ENABLE_WORKDRIVE:-true}"
PASSWORD_PDF_ZOHO_REGION="${PASSWORD_PDF_ZOHO_REGION:-com}"
ZOHO_OAUTH_CLIENT_ID="${ZOHO_OAUTH_CLIENT_ID:-${ZOHO_WORKDRIVE_CLIENT_ID:-}}"
ZOHO_OAUTH_CLIENT_SECRET="${ZOHO_OAUTH_CLIENT_SECRET:-${ZOHO_WORKDRIVE_CLIENT_SECRET:-}}"
ZOHO_OAUTH_ACCOUNTS_BASE_URL="${ZOHO_OAUTH_ACCOUNTS_BASE_URL:-}"
ZOHO_OAUTH_REDIRECT_URI="${ZOHO_OAUTH_REDIRECT_URI:-}"
ZOHO_OAUTH_SCOPES="${ZOHO_OAUTH_SCOPES:-WorkDrive.files.READ,WorkDrive.files.CREATE,WorkDrive.files.UPDATE}"

log() {
  printf '[%s] %s\n' "${APP_NAME}" "$*"
}

fail() {
  printf '[%s] ERROR: %s\n' "${APP_NAME}" "$*" >&2
  exit 1
}

generate_secret() {
  od -An -N32 -tx1 /dev/urandom | tr -d ' \n'
}

resolve_zoho_accounts_base() {
  case "${PASSWORD_PDF_ZOHO_REGION}" in
    com)
      printf '%s' "https://accounts.zoho.com"
      ;;
    eu)
      printf '%s' "https://accounts.zoho.eu"
      ;;
    in)
      printf '%s' "https://accounts.zoho.in"
      ;;
    com.au)
      printf '%s' "https://accounts.zoho.com.au"
      ;;
    *)
      fail "Unsupported PASSWORD_PDF_ZOHO_REGION: ${PASSWORD_PDF_ZOHO_REGION}"
      ;;
  esac
}

require_root() {
  if [[ "${EUID}" -ne 0 ]]; then
    fail "Run this installer as root. Example: sudo bash <(curl -fsSL https://raw.githubusercontent.com/yboucher97/opticable-api-platform/main/install.sh)"
  fi
}

ensure_packages() {
  export DEBIAN_FRONTEND=noninteractive
  apt-get update
  apt-get install -y git curl ca-certificates openssl python3 python3-venv python3-pip caddy ufw build-essential unzip

  if ! command -v node >/dev/null 2>&1; then
    curl -fsSL https://deb.nodesource.com/setup_22.x | bash -
    apt-get install -y nodejs
  fi
}

ensure_secrets() {
  if [[ -z "${PASSWORD_PDF_API_KEY}" ]]; then
    PASSWORD_PDF_API_KEY="$(generate_secret)"
  fi
  if [[ -z "${OMADA_SITE_CREATOR_WEBHOOK_TOKEN}" ]]; then
    OMADA_SITE_CREATOR_WEBHOOK_TOKEN="$(generate_secret)"
  fi
  if [[ -z "${SITE_AND_PASSWORD_WORKFLOW_API_KEY}" ]]; then
    SITE_AND_PASSWORD_WORKFLOW_API_KEY="$(generate_secret)"
  fi
}

ensure_users_and_dirs() {
  if ! getent group "${SHARED_GROUP}" >/dev/null 2>&1; then
    groupadd --system "${SHARED_GROUP}"
  fi

  if ! id -u "${PDF_SERVICE_USER}" >/dev/null 2>&1; then
    useradd --system --create-home --home "${PDF_DATA_DIR}" --shell /usr/sbin/nologin "${PDF_SERVICE_USER}"
  fi
  if ! id -u "${OMADA_SERVICE_USER}" >/dev/null 2>&1; then
    useradd --system --create-home --home "${OMADA_DATA_DIR}" --shell /usr/sbin/nologin "${OMADA_SERVICE_USER}"
  fi
  if ! id -u "${WORKFLOW_SERVICE_USER}" >/dev/null 2>&1; then
    useradd --system --create-home --home "${WORKFLOW_DATA_DIR}" --shell /usr/sbin/nologin "${WORKFLOW_SERVICE_USER}"
  fi

  usermod -a -G "${SHARED_GROUP}" "${PDF_SERVICE_USER}"
  usermod -a -G "${SHARED_GROUP}" "${WORKFLOW_SERVICE_USER}"

  mkdir -p "${PDF_DATA_DIR}" "${PDF_CONFIG_DIR}" "${OMADA_DATA_DIR}" "${WORKFLOW_DATA_DIR}"
  install -d -m 2770 -o root -g "${SHARED_GROUP}" "${SHARED_DATA_DIR}"
  chown -R "${PDF_SERVICE_USER}:${PDF_SERVICE_USER}" "${PDF_DATA_DIR}"
  chown -R "${OMADA_SERVICE_USER}:${OMADA_SERVICE_USER}" "${OMADA_DATA_DIR}"
  chown -R "${WORKFLOW_SERVICE_USER}:${WORKFLOW_SERVICE_USER}" "${WORKFLOW_DATA_DIR}"
}

sync_repo() {
  if [[ -d "${INSTALL_DIR}/.git" ]]; then
    git -C "${INSTALL_DIR}" fetch --tags origin
    git -C "${INSTALL_DIR}" checkout "${REPO_REF}"
    git -C "${INSTALL_DIR}" pull --ff-only origin "${REPO_REF}"
  else
    rm -rf "${INSTALL_DIR}"
    git clone --branch "${REPO_REF}" "${REPO_URL}" "${INSTALL_DIR}"
  fi
}

configure_pdf_json() {
  local workdrive_api_base
  local workdrive_accounts_base
  local crm_api_base

  case "${PASSWORD_PDF_ZOHO_REGION}" in
    com)
      workdrive_api_base="https://www.zohoapis.com/workdrive/api/v1"
      workdrive_accounts_base="https://accounts.zoho.com/oauth/v2/token"
      crm_api_base="https://www.zohoapis.com/crm/v7"
      ;;
    eu)
      workdrive_api_base="https://www.zohoapis.eu/workdrive/api/v1"
      workdrive_accounts_base="https://accounts.zoho.eu/oauth/v2/token"
      crm_api_base="https://www.zohoapis.eu/crm/v7"
      ;;
    in)
      workdrive_api_base="https://www.zohoapis.in/workdrive/api/v1"
      workdrive_accounts_base="https://accounts.zoho.in/oauth/v2/token"
      crm_api_base="https://www.zohoapis.in/crm/v7"
      ;;
    com.au)
      workdrive_api_base="https://www.zohoapis.com.au/workdrive/api/v1"
      workdrive_accounts_base="https://accounts.zoho.com.au/oauth/v2/token"
      crm_api_base="https://www.zohoapis.com.au/crm/v7"
      ;;
    *)
      fail "Unsupported PASSWORD_PDF_ZOHO_REGION: ${PASSWORD_PDF_ZOHO_REGION}"
      ;;
  esac

  if [[ ! -f "${PDF_CONFIG_PATH}" ]]; then
    cp "${PDF_APP_DIR}/config/wifi_pdf/brand_settings.json" "${PDF_CONFIG_PATH}"
  fi

  PDF_CONFIG_PATH="${PDF_CONFIG_PATH}" \
  PDF_OUTPUT_DIR="${PDF_DATA_DIR}/output/pdf/wifi" \
  PASSWORD_PDF_ENABLE_WORKDRIVE="${PASSWORD_PDF_ENABLE_WORKDRIVE}" \
  WORKDRIVE_API_BASE="${workdrive_api_base}" \
  WORKDRIVE_ACCOUNTS_BASE="${workdrive_accounts_base}" \
  CRM_API_BASE="${crm_api_base}" \
  ZOHO_WORKDRIVE_PARENT_FOLDER_ID="${ZOHO_WORKDRIVE_PARENT_FOLDER_ID:-}" \
  python3 - <<'PY'
import json
import os
from pathlib import Path

config_path = Path(os.environ["PDF_CONFIG_PATH"])
payload = json.loads(config_path.read_text(encoding="utf-8"))
payload["output"]["root_dir"] = os.environ["PDF_OUTPUT_DIR"]
payload["workdrive"]["enabled"] = os.environ["PASSWORD_PDF_ENABLE_WORKDRIVE"].lower() == "true"
payload["workdrive"]["api_base_url"] = os.environ["WORKDRIVE_API_BASE"]
payload["workdrive"]["accounts_base_url"] = os.environ["WORKDRIVE_ACCOUNTS_BASE"]
payload.setdefault("crm", {})
payload["crm"]["api_base_url"] = os.environ["CRM_API_BASE"]

folder_id = os.environ.get("ZOHO_WORKDRIVE_PARENT_FOLDER_ID", "").strip()
if folder_id:
    payload["workdrive"]["parent_folder_id"] = folder_id

config_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
PY

  chmod 644 "${PDF_CONFIG_PATH}"
}

write_pdf_env() {
  PDF_ENV_FILE="${PDF_ENV_FILE}" \
  PASSWORD_PDF_API_KEY="${PASSWORD_PDF_API_KEY}" \
  ZOHO_WORKDRIVE_CLIENT_ID="${ZOHO_WORKDRIVE_CLIENT_ID:-}" \
  ZOHO_WORKDRIVE_CLIENT_SECRET="${ZOHO_WORKDRIVE_CLIENT_SECRET:-}" \
  ZOHO_WORKDRIVE_REFRESH_TOKEN="${ZOHO_WORKDRIVE_REFRESH_TOKEN:-}" \
  ZOHO_WORKDRIVE_ACCESS_TOKEN="${ZOHO_WORKDRIVE_ACCESS_TOKEN:-}" \
  ZOHO_WORKDRIVE_PARENT_FOLDER_ID="${ZOHO_WORKDRIVE_PARENT_FOLDER_ID:-}" \
  ZOHO_WORKDRIVE_CREDENTIALS_PATH="${ZOHO_OAUTH_CREDENTIALS_PATH}" \
  python3 - <<'PY'
import os
from pathlib import Path

path = Path(os.environ["PDF_ENV_FILE"])
existing = {}
if path.exists():
    for line in path.read_text(encoding="utf-8").splitlines():
        if "=" not in line or line.strip().startswith("#"):
            continue
        key, value = line.split("=", 1)
        existing[key] = value

for key in [
    "PASSWORD_PDF_API_KEY",
    "ZOHO_WORKDRIVE_CLIENT_ID",
    "ZOHO_WORKDRIVE_CLIENT_SECRET",
    "ZOHO_WORKDRIVE_REFRESH_TOKEN",
    "ZOHO_WORKDRIVE_ACCESS_TOKEN",
    "ZOHO_WORKDRIVE_PARENT_FOLDER_ID",
    "ZOHO_WORKDRIVE_CREDENTIALS_PATH",
]:
    value = os.environ.get(key, "")
    if value:
        existing[key] = value

existing["WIFI_PDF_API_KEY"] = os.environ["PASSWORD_PDF_API_KEY"]

ordered = [
    "WIFI_PDF_API_KEY",
    "ZOHO_WORKDRIVE_CLIENT_ID",
    "ZOHO_WORKDRIVE_CLIENT_SECRET",
    "ZOHO_WORKDRIVE_REFRESH_TOKEN",
    "ZOHO_WORKDRIVE_ACCESS_TOKEN",
    "ZOHO_WORKDRIVE_PARENT_FOLDER_ID",
    "ZOHO_WORKDRIVE_CREDENTIALS_PATH",
]
path.write_text("\n".join(f"{key}={existing.get(key, '')}" for key in ordered) + "\n", encoding="utf-8")
PY

  chmod 600 "${PDF_ENV_FILE}"
}

install_pdf_app() {
  python3 -m venv "${PDF_APP_DIR}/.venv"
  "${PDF_APP_DIR}/.venv/bin/pip" install --upgrade pip
  "${PDF_APP_DIR}/.venv/bin/pip" install -r "${PDF_APP_DIR}/requirements.txt"
  configure_pdf_json
  write_pdf_env
}

write_pdf_service() {
  cat >"/etc/systemd/system/${PDF_SERVICE_NAME}.service" <<EOF
[Unit]
Description=Password PDF Generator API
After=network.target

[Service]
User=${PDF_SERVICE_USER}
Group=${PDF_SERVICE_USER}
WorkingDirectory=${PDF_APP_DIR}
EnvironmentFile=${PDF_ENV_FILE}
Environment=WIFI_PDF_CONFIG_PATH=${PDF_CONFIG_PATH}
Environment=PATH=${PDF_APP_DIR}/.venv/bin
ExecStart=${PDF_APP_DIR}/.venv/bin/uvicorn wifi_pdf.api:app --host 127.0.0.1 --port ${PDF_PORT}
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF
}

write_omada_env() {
  OMADA_ENV_FILE="${OMADA_ENV_FILE}" \
  OMADA_PORT="${OMADA_PORT}" \
  OMADA_DATA_DIR="${OMADA_DATA_DIR}" \
  OMADA_SITE_CREATOR_WEBHOOK_TOKEN="${OMADA_SITE_CREATOR_WEBHOOK_TOKEN}" \
  OMADA_SITE_CREATOR_CLOUD_EMAIL="${OMADA_SITE_CREATOR_CLOUD_EMAIL:-}" \
  OMADA_SITE_CREATOR_CLOUD_PASSWORD="${OMADA_SITE_CREATOR_CLOUD_PASSWORD:-}" \
  OMADA_SITE_CREATOR_DEVICE_USERNAME="${OMADA_SITE_CREATOR_DEVICE_USERNAME:-}" \
  OMADA_SITE_CREATOR_DEVICE_PASSWORD="${OMADA_SITE_CREATOR_DEVICE_PASSWORD:-}" \
  python3 - <<'PY'
import os
from pathlib import Path

path = Path(os.environ["OMADA_ENV_FILE"])
existing = {}
if path.exists():
    for line in path.read_text(encoding="utf-8").splitlines():
        if "=" not in line or line.strip().startswith("#"):
            continue
        key, value = line.split("=", 1)
        existing[key] = value

defaults = {
    "NODE_ENV": "production",
    "OMADA_SITE_CREATOR_HOST": "127.0.0.1",
    "OMADA_SITE_CREATOR_PORT": os.environ["OMADA_PORT"],
    "OMADA_SITE_CREATOR_DATA_DIR": f"{os.environ['OMADA_DATA_DIR']}/data",
    "OMADA_SITE_CREATOR_WEBHOOK_TOKEN": os.environ["OMADA_SITE_CREATOR_WEBHOOK_TOKEN"],
    "OMADA_SITE_CREATOR_HEADLESS": "true",
    "OMADA_SITE_CREATOR_BROWSER_CHANNEL": "chromium",
}

for key, value in defaults.items():
    existing.setdefault(key, value)

for key in [
    "OMADA_SITE_CREATOR_WEBHOOK_TOKEN",
    "OMADA_SITE_CREATOR_CLOUD_EMAIL",
    "OMADA_SITE_CREATOR_CLOUD_PASSWORD",
    "OMADA_SITE_CREATOR_DEVICE_USERNAME",
    "OMADA_SITE_CREATOR_DEVICE_PASSWORD",
]:
    value = os.environ.get(key, "").strip()
    if value:
        existing[key] = value

ordered = [
    "NODE_ENV",
    "OMADA_SITE_CREATOR_HOST",
    "OMADA_SITE_CREATOR_PORT",
    "OMADA_SITE_CREATOR_DATA_DIR",
    "OMADA_SITE_CREATOR_WEBHOOK_TOKEN",
    "OMADA_SITE_CREATOR_HEADLESS",
    "OMADA_SITE_CREATOR_BROWSER_CHANNEL",
    "OMADA_SITE_CREATOR_CLOUD_EMAIL",
    "OMADA_SITE_CREATOR_CLOUD_PASSWORD",
    "OMADA_SITE_CREATOR_DEVICE_USERNAME",
    "OMADA_SITE_CREATOR_DEVICE_PASSWORD",
]

lines = []
for key in ordered:
    if key in existing:
        lines.append(f"{key}={existing[key]}")

path.write_text("\n".join(lines) + "\n", encoding="utf-8")
PY

  chmod 600 "${OMADA_ENV_FILE}"
}

install_omada_app() {
  pushd "${OMADA_APP_DIR}" >/dev/null
  npm ci
  npm run build
  npm prune --omit=dev
  npx playwright install chromium --with-deps
  popd >/dev/null
  write_omada_env
}

write_omada_service() {
  cat >"/etc/systemd/system/${OMADA_SERVICE_NAME}.service" <<EOF
[Unit]
Description=Omada Site Creator
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=${OMADA_SERVICE_USER}
Group=${OMADA_SERVICE_USER}
WorkingDirectory=${OMADA_APP_DIR}
EnvironmentFile=${OMADA_ENV_FILE}
Environment=HOME=${OMADA_DATA_DIR}
ExecStart=/usr/bin/npm run serve:dist
Restart=always
RestartSec=5
TimeoutStopSec=20

[Install]
WantedBy=multi-user.target
EOF
}

write_workflow_env() {
  local zoho_accounts_base="${ZOHO_OAUTH_ACCOUNTS_BASE_URL:-$(resolve_zoho_accounts_base)}"
  local zoho_redirect_uri="${ZOHO_OAUTH_REDIRECT_URI:-}"
  if [[ -z "${zoho_redirect_uri}" && -n "${PUBLIC_API_HOST}" ]]; then
    zoho_redirect_uri="https://${PUBLIC_API_HOST}/v1/integrations/zoho/oauth/callback"
  fi

  WORKFLOW_ENV_FILE="${WORKFLOW_ENV_FILE}" \
  WORKFLOW_PORT="${WORKFLOW_PORT}" \
  WORKFLOW_DATA_DIR="${WORKFLOW_DATA_DIR}" \
  SITE_AND_PASSWORD_WORKFLOW_API_KEY="${SITE_AND_PASSWORD_WORKFLOW_API_KEY}" \
  PASSWORD_PDF_API_KEY="${PASSWORD_PDF_API_KEY}" \
  OMADA_SITE_CREATOR_WEBHOOK_TOKEN="${OMADA_SITE_CREATOR_WEBHOOK_TOKEN}" \
  OMADA_SITE_CREATOR_CLOUD_EMAIL="${OMADA_SITE_CREATOR_CLOUD_EMAIL:-}" \
  OMADA_SITE_CREATOR_CLOUD_PASSWORD="${OMADA_SITE_CREATOR_CLOUD_PASSWORD:-}" \
  OMADA_SITE_CREATOR_DEVICE_USERNAME="${OMADA_SITE_CREATOR_DEVICE_USERNAME:-}" \
  OMADA_SITE_CREATOR_DEVICE_PASSWORD="${OMADA_SITE_CREATOR_DEVICE_PASSWORD:-}" \
  ZOHO_OAUTH_CLIENT_ID="${ZOHO_OAUTH_CLIENT_ID:-}" \
  ZOHO_OAUTH_CLIENT_SECRET="${ZOHO_OAUTH_CLIENT_SECRET:-}" \
  ZOHO_OAUTH_SCOPES="${ZOHO_OAUTH_SCOPES}" \
  ZOHO_OAUTH_ACCOUNTS_BASE_URL="${zoho_accounts_base}" \
  ZOHO_OAUTH_REDIRECT_URI="${zoho_redirect_uri}" \
  ZOHO_OAUTH_CREDENTIALS_PATH="${ZOHO_OAUTH_CREDENTIALS_PATH}" \
  python3 - <<'PY'
import os
from pathlib import Path

path = Path(os.environ["WORKFLOW_ENV_FILE"])
existing = {}
if path.exists():
    for line in path.read_text(encoding="utf-8").splitlines():
        if "=" not in line or line.strip().startswith("#"):
            continue
        key, value = line.split("=", 1)
        existing[key] = value

defaults = {
    "SITE_WORKFLOW_API_KEY": os.environ["SITE_AND_PASSWORD_WORKFLOW_API_KEY"],
    "SITE_WORKFLOW_HOST": "127.0.0.1",
    "SITE_WORKFLOW_PORT": os.environ["WORKFLOW_PORT"],
    "SITE_WORKFLOW_OUTPUT_ROOT": f"{os.environ['WORKFLOW_DATA_DIR']}/output",
    "SITE_WORKFLOW_SSID_PREFIX": "APT_",
    "SITE_WORKFLOW_SSID_TEMPLATE": "{prefix}{identifier}_{suffix}",
    "SITE_WORKFLOW_SSID_SUFFIX_LENGTH": "2",
    "SITE_WORKFLOW_PASSWORD_SPECIALS": "*!$@#",
    "PASSWORD_PDF_BASE_URL": "http://127.0.0.1:8000",
    "PASSWORD_PDF_API_KEY": os.environ["PASSWORD_PDF_API_KEY"],
    "PASSWORD_PDF_TIMEOUT_SECONDS": "600",
    "OMADA_SITE_CREATOR_BASE_URL": "http://127.0.0.1:3210",
    "OMADA_SITE_CREATOR_WEBHOOK_TOKEN": os.environ["OMADA_SITE_CREATOR_WEBHOOK_TOKEN"],
    "OMADA_SITE_CREATOR_TIMEOUT_SECONDS": "900",
    "OMADA_ORGANIZATION_NAME": "Opti-plex",
    "OMADA_CLOUD_BASE_URL": "https://use1-omada-cloud.tplinkcloud.com/",
    "OMADA_BROWSER_CHANNEL": "chromium",
    "OMADA_HEADLESS": "true",
    "OMADA_DEFAULT_REGION": "Canada",
    "OMADA_DEFAULT_TIMEZONE": "America/Toronto",
    "OMADA_DEFAULT_SCENARIO": "Office",
    "ZOHO_OAUTH_ACCOUNTS_BASE_URL": os.environ["ZOHO_OAUTH_ACCOUNTS_BASE_URL"],
    "ZOHO_OAUTH_REDIRECT_URI": os.environ["ZOHO_OAUTH_REDIRECT_URI"],
    "ZOHO_OAUTH_SCOPES": os.environ["ZOHO_OAUTH_SCOPES"],
    "ZOHO_OAUTH_CREDENTIALS_PATH": os.environ["ZOHO_OAUTH_CREDENTIALS_PATH"],
}

for key, value in defaults.items():
    existing.setdefault(key, value)

for key in [
    "SITE_WORKFLOW_API_KEY",
    "PASSWORD_PDF_API_KEY",
    "OMADA_SITE_CREATOR_WEBHOOK_TOKEN",
    "OMADA_SITE_CREATOR_CLOUD_EMAIL",
    "OMADA_SITE_CREATOR_CLOUD_PASSWORD",
    "OMADA_SITE_CREATOR_DEVICE_USERNAME",
    "OMADA_SITE_CREATOR_DEVICE_PASSWORD",
    "ZOHO_OAUTH_CLIENT_ID",
    "ZOHO_OAUTH_CLIENT_SECRET",
]:
    value = os.environ.get(key, "").strip()
    if value:
        existing[key] = value

ordered = [
    "SITE_WORKFLOW_API_KEY",
    "SITE_WORKFLOW_HOST",
    "SITE_WORKFLOW_PORT",
    "SITE_WORKFLOW_OUTPUT_ROOT",
    "SITE_WORKFLOW_SSID_PREFIX",
    "SITE_WORKFLOW_SSID_TEMPLATE",
    "SITE_WORKFLOW_SSID_SUFFIX_LENGTH",
    "SITE_WORKFLOW_PASSWORD_SPECIALS",
    "PASSWORD_PDF_BASE_URL",
    "PASSWORD_PDF_API_KEY",
    "PASSWORD_PDF_TIMEOUT_SECONDS",
    "OMADA_SITE_CREATOR_BASE_URL",
    "OMADA_SITE_CREATOR_WEBHOOK_TOKEN",
    "OMADA_SITE_CREATOR_TIMEOUT_SECONDS",
    "OMADA_ORGANIZATION_NAME",
    "OMADA_CLOUD_BASE_URL",
    "OMADA_BROWSER_CHANNEL",
    "OMADA_HEADLESS",
    "OMADA_DEFAULT_REGION",
    "OMADA_DEFAULT_TIMEZONE",
    "OMADA_DEFAULT_SCENARIO",
    "ZOHO_OAUTH_CLIENT_ID",
    "ZOHO_OAUTH_CLIENT_SECRET",
    "ZOHO_OAUTH_ACCOUNTS_BASE_URL",
    "ZOHO_OAUTH_REDIRECT_URI",
    "ZOHO_OAUTH_SCOPES",
    "ZOHO_OAUTH_CREDENTIALS_PATH",
    "OMADA_SITE_CREATOR_CLOUD_EMAIL",
    "OMADA_SITE_CREATOR_CLOUD_PASSWORD",
    "OMADA_SITE_CREATOR_DEVICE_USERNAME",
    "OMADA_SITE_CREATOR_DEVICE_PASSWORD",
]
path.write_text("\n".join(f"{key}={existing.get(key, '')}" for key in ordered) + "\n", encoding="utf-8")
PY

  chmod 600 "${WORKFLOW_ENV_FILE}"
}

install_workflow_app() {
  python3 -m venv "${WORKFLOW_APP_DIR}/.venv"
  "${WORKFLOW_APP_DIR}/.venv/bin/pip" install --upgrade pip
  "${WORKFLOW_APP_DIR}/.venv/bin/pip" install -r "${WORKFLOW_APP_DIR}/requirements.txt"
  write_workflow_env
}

write_workflow_service() {
  cat >"/etc/systemd/system/${WORKFLOW_SERVICE_NAME}.service" <<EOF
[Unit]
Description=Site And Password Workflow
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=${WORKFLOW_SERVICE_USER}
Group=${WORKFLOW_SERVICE_USER}
WorkingDirectory=${WORKFLOW_APP_DIR}
EnvironmentFile=${WORKFLOW_ENV_FILE}
Environment=PATH=${WORKFLOW_APP_DIR}/.venv/bin
ExecStart=${WORKFLOW_APP_DIR}/.venv/bin/uvicorn workflow.api:app --host 127.0.0.1 --port ${WORKFLOW_PORT}
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF
}

configure_caddy() {
  if [[ -z "${PUBLIC_API_HOST}" && -z "${PDF_HOST}" && -z "${OMADA_HOST}" && -z "${WORKFLOW_HOST}" ]]; then
    return
  fi

  mkdir -p /etc/caddy/conf.d
  if [[ ! -f /etc/caddy/Caddyfile ]] || grep -Fq '/usr/share/caddy' /etc/caddy/Caddyfile; then
    cat >/etc/caddy/Caddyfile <<'EOF'
import /etc/caddy/conf.d/*.caddy
EOF
  elif ! grep -Fq 'import /etc/caddy/conf.d/*.caddy' /etc/caddy/Caddyfile; then
    printf '\nimport /etc/caddy/conf.d/*.caddy\n' >> /etc/caddy/Caddyfile
  fi

  if [[ -n "${PUBLIC_API_HOST}" ]]; then
    cat >"/etc/caddy/conf.d/${APP_NAME}.caddy" <<EOF
${PUBLIC_API_HOST} {
    @pdfRoot path /pdf
    redir @pdfRoot /pdf/ 308
    @omadaRoot path /omada
    redir @omadaRoot /omada/ 308
    @workflowRoot path /workflow
    redir @workflowRoot /workflow/ 308

    handle_path /pdf/* {
        reverse_proxy 127.0.0.1:${PDF_PORT}
    }

    handle_path /omada/* {
        reverse_proxy 127.0.0.1:${OMADA_PORT}
    }

    handle_path /workflow/* {
        reverse_proxy 127.0.0.1:${WORKFLOW_PORT}
    }

    reverse_proxy 127.0.0.1:${WORKFLOW_PORT}
}
EOF
    caddy fmt --overwrite "/etc/caddy/conf.d/${APP_NAME}.caddy" >/dev/null
  else
    if [[ -n "${PDF_HOST}" ]]; then
      cat >"/etc/caddy/conf.d/${PDF_SERVICE_NAME}.caddy" <<EOF
${PDF_HOST} {
    reverse_proxy 127.0.0.1:${PDF_PORT}
}
EOF
      caddy fmt --overwrite "/etc/caddy/conf.d/${PDF_SERVICE_NAME}.caddy" >/dev/null
    fi

    if [[ -n "${OMADA_HOST}" ]]; then
      cat >"/etc/caddy/conf.d/${OMADA_SERVICE_NAME}.caddy" <<EOF
${OMADA_HOST} {
    reverse_proxy 127.0.0.1:${OMADA_PORT}
}
EOF
      caddy fmt --overwrite "/etc/caddy/conf.d/${OMADA_SERVICE_NAME}.caddy" >/dev/null
    fi

    if [[ -n "${WORKFLOW_HOST}" ]]; then
      cat >"/etc/caddy/conf.d/${WORKFLOW_SERVICE_NAME}.caddy" <<EOF
${WORKFLOW_HOST} {
    reverse_proxy 127.0.0.1:${WORKFLOW_PORT}
}
EOF
      caddy fmt --overwrite "/etc/caddy/conf.d/${WORKFLOW_SERVICE_NAME}.caddy" >/dev/null
    fi
  fi

  caddy fmt --overwrite /etc/caddy/Caddyfile >/dev/null
  caddy validate --config /etc/caddy/Caddyfile
  systemctl enable --now caddy
  systemctl reload caddy
}

configure_ufw() {
  ufw allow OpenSSH >/dev/null 2>&1 || true
  if [[ -n "${PUBLIC_API_HOST}" || -n "${PDF_HOST}" || -n "${OMADA_HOST}" || -n "${WORKFLOW_HOST}" ]]; then
    ufw allow 80/tcp >/dev/null 2>&1 || true
    ufw allow 443/tcp >/dev/null 2>&1 || true
  fi
  ufw --force enable >/dev/null 2>&1 || true
}

start_services() {
  systemctl daemon-reload
  systemctl enable --now "${PDF_SERVICE_NAME}"
  systemctl enable --now "${OMADA_SERVICE_NAME}"
  systemctl enable --now "${WORKFLOW_SERVICE_NAME}"
}

print_summary() {
  echo
  echo "Combined install complete."
  echo "Code directory:  ${INSTALL_DIR}"
  echo "PDF config:      ${PDF_CONFIG_PATH}"
  echo "PDF env:         ${PDF_ENV_FILE}"
  echo "Omada env:       ${OMADA_ENV_FILE}"
  echo "Workflow env:    ${WORKFLOW_ENV_FILE}"
  echo "Zoho OAuth file: ${ZOHO_OAUTH_CREDENTIALS_PATH}"
  echo "Services:"
  echo "  - ${PDF_SERVICE_NAME}"
  echo "  - ${OMADA_SERVICE_NAME}"
  echo "  - ${WORKFLOW_SERVICE_NAME}"
  echo
  echo "Local checks:"
  echo "  - curl http://127.0.0.1:${PDF_PORT}/health"
  echo "  - curl http://127.0.0.1:${OMADA_PORT}/api/health"
  echo "  - curl http://127.0.0.1:${WORKFLOW_PORT}/health"
  if [[ -n "${PUBLIC_API_HOST}" ]]; then
    echo
    echo "Public base URL: https://${PUBLIC_API_HOST}"
    echo "Docs:            https://${PUBLIC_API_HOST}/docs"
    echo "OpenAPI JSON:    https://${PUBLIC_API_HOST}/openapi.json"
    echo "Catalog:         https://${PUBLIC_API_HOST}/v1/system/catalog"
    echo "Workflow webhook: https://${PUBLIC_API_HOST}/v1/site-and-password/webhooks/zoho"
    echo "Workflow jobs:    https://${PUBLIC_API_HOST}/v1/site-and-password/jobs"
    echo "Workflow health:  https://${PUBLIC_API_HOST}/v1/system/health"
    echo "Zoho OAuth start: https://${PUBLIC_API_HOST}/v1/integrations/zoho/oauth/start"
    echo "Zoho OAuth status: https://${PUBLIC_API_HOST}/v1/integrations/zoho/oauth/status"
    echo "PDF health:       https://${PUBLIC_API_HOST}/pdf/health"
    echo "Omada health:     https://${PUBLIC_API_HOST}/omada/api/health"
  fi
}

main() {
  require_root
  ensure_packages
  ensure_secrets
  ensure_users_and_dirs
  sync_repo
  install_pdf_app
  write_pdf_service
  install_omada_app
  write_omada_service
  install_workflow_app
  write_workflow_service
  configure_caddy
  configure_ufw
  start_services
  print_summary
}

main "$@"
