#!/usr/bin/env bash
set -euo pipefail

if [[ "${EUID}" -ne 0 ]]; then
  echo "Run this installer with sudo or as root." >&2
  exit 1
fi

SERVICE_USER="${OMADA_SITE_CREATOR_USER:-omada-site-creator}"
INSTALL_DIR="${OMADA_SITE_CREATOR_INSTALL_DIR:-/opt/omada-site-creator}"
DATA_DIR="${OMADA_SITE_CREATOR_DATA_DIR:-/var/lib/omada-site-creator}"
ENV_FILE="${OMADA_SITE_CREATOR_ENV_FILE:-/etc/omada-site-creator.env}"
SERVICE_FILE="/etc/systemd/system/omada-site-creator.service"
CADDY_FILE="/etc/caddy/conf.d/omada-site-creator.caddy"
PUBLIC_HOST="${OMADA_SITE_CREATOR_PUBLIC_HOST:-}"
REPO_URL="${OMADA_SITE_CREATOR_REPO_URL:-https://github.com/yboucher97/Omada_Site_Creator.git}"
REPO_REF="${OMADA_SITE_CREATOR_REPO_REF:-main}"

apt-get update
apt-get install -y ca-certificates curl git caddy

if ! command -v node >/dev/null 2>&1; then
  curl -fsSL https://deb.nodesource.com/setup_22.x | bash -
  apt-get install -y nodejs
fi

if ! id -u "${SERVICE_USER}" >/dev/null 2>&1; then
  useradd --system --create-home --home-dir "${DATA_DIR}" --shell /usr/sbin/nologin "${SERVICE_USER}"
fi

mkdir -p "${INSTALL_DIR}"
mkdir -p "${DATA_DIR}"
chown -R "${SERVICE_USER}:${SERVICE_USER}" "${DATA_DIR}"

if [[ ! -d "${INSTALL_DIR}/.git" ]]; then
  git clone "${REPO_URL}" "${INSTALL_DIR}"
fi

git -C "${INSTALL_DIR}" fetch --tags origin
git -C "${INSTALL_DIR}" checkout "${REPO_REF}"
git -C "${INSTALL_DIR}" pull --ff-only origin "${REPO_REF}"

pushd "${INSTALL_DIR}" >/dev/null
npm ci
npm run build
npx playwright install chromium --with-deps
popd >/dev/null

if [[ ! -f "${ENV_FILE}" ]]; then
  install -m 600 "${INSTALL_DIR}/deploy/linux/omada-site-creator.env.example" "${ENV_FILE}"
fi

if ! grep -q "^OMADA_SITE_CREATOR_DATA_DIR=" "${ENV_FILE}"; then
  printf "\nOMADA_SITE_CREATOR_DATA_DIR=%s/data\n" "${DATA_DIR}" >> "${ENV_FILE}"
fi

install -m 644 "${INSTALL_DIR}/deploy/linux/omada-site-creator.service" "${SERVICE_FILE}"

mkdir -p /etc/caddy/conf.d
if [[ -n "${PUBLIC_HOST}" ]]; then
  sed "s/omada.example.com/${PUBLIC_HOST}/g" "${INSTALL_DIR}/deploy/linux/omada-site-creator.caddy" > "${CADDY_FILE}"
  systemctl reload caddy
fi

systemctl daemon-reload
systemctl enable --now omada-site-creator.service

echo
echo "Omada Site Creator installed."
echo "Code: ${INSTALL_DIR}"
echo "Env:  ${ENV_FILE}"
echo "Svc:  ${SERVICE_FILE}"
if [[ -n "${PUBLIC_HOST}" ]]; then
  echo "Host: https://${PUBLIC_HOST}"
fi
echo
echo "Edit ${ENV_FILE} and set your webhook token and TP-Link cloud credentials."
