#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
CONFIG_FILE="${LOCAL_CICD_CONFIG:-${SCRIPT_DIR}/local-cicd.env}"

if [ -f "${CONFIG_FILE}" ]; then
  # shellcheck disable=SC1090
  source "${CONFIG_FILE}"
fi

# Safe-by-default: this script must not deploy, export, or push unless the
# caller explicitly opts in through the environment or local-cicd.env.
ENABLE_DEPLOY="${ENABLE_DEPLOY:-0}"
ENABLE_EXPORT_ARCHIVE="${ENABLE_EXPORT_ARCHIVE:-0}"
ENABLE_MIRROR_PUSH="${ENABLE_MIRROR_PUSH:-0}"
EXPORT_URL="${EXPORT_URL:-http://127.0.0.1:9899/compliance/export}"
EXPORT_DIR="${EXPORT_DIR:-${REPO_ROOT}/.local-cicd-exports}"
EXPORT_RETENTION="${EXPORT_RETENTION:-10}"
TARGET_REMOTE_NAME="${TARGET_REMOTE_NAME:-sovereignty-ai-studio}"
TARGET_REPO_URL="${TARGET_REPO_URL:-git@github.com:Appel420/Sovereignty-AI-Studio.git}"
TARGET_BRANCH="${TARGET_BRANCH:-$(git -C "${REPO_ROOT}" rev-parse --abbrev-ref HEAD)}"
CONFIRM_MIRROR_PUSH="${CONFIRM_MIRROR_PUSH:-}"
WAIT_RETRIES="${WAIT_RETRIES:-30}"
WAIT_SECONDS="${WAIT_SECONDS:-2}"

error() {
  printf '❌ %s\n' "$*" >&2
}

info() {
  printf 'ℹ️  %s\n' "$*"
}

on_err() {
  local code=$?
  error "Local deploy/sync failed (line ${BASH_LINENO[0]}, exit ${code})"
  exit "${code}"
}
trap on_err ERR

sha256_text() {
  if command -v sha256sum >/dev/null 2>&1; then
    printf '%s' "$1" | sha256sum | awk '{print $1}'
  elif command -v shasum >/dev/null 2>&1; then
    printf '%s' "$1" | shasum -a 256 | awk '{print $1}'
  else
    error "Neither sha256sum nor shasum is installed"
    exit 1
  fi
}

wait_for_export() {
  local n=1
  while [ "${n}" -le "${WAIT_RETRIES}" ]; do
    if curl --silent --fail --max-time 5 "${EXPORT_URL}" >/dev/null; then
      return 0
    fi
    sleep "${WAIT_SECONDS}"
    n=$((n + 1))
  done
  return 1
}

run_deploy() {
  if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
    info "Deploying local stack with docker compose..."
    docker compose -f "${REPO_ROOT}/docker-compose.yml" up -d --build
  elif command -v docker-compose >/dev/null 2>&1; then
    info "Deploying local stack with docker-compose..."
    docker-compose -f "${REPO_ROOT}/docker-compose.yml" up -d --build
  else
    error "docker compose or docker-compose is required for ENABLE_DEPLOY=1"
    exit 1
  fi
}

archive_export() {
  command -v jq >/dev/null 2>&1 || {
    error "jq is required for ENABLE_EXPORT_ARCHIVE=1"
    exit 1
  }

  mkdir -p "${EXPORT_DIR}"

  info "Waiting for compliance endpoint: ${EXPORT_URL}"
  if ! wait_for_export; then
    error "Timed out waiting for ${EXPORT_URL}"
    exit 1
  fi

  local ts export_file merkle_file merkle_root digest
  ts="$(date +%Y%m%d_%H%M%S)"
  export_file="${EXPORT_DIR}/compliance_export_${ts}.json"
  merkle_file="${EXPORT_DIR}/merkle_digest_${ts}.txt"

  curl --silent --show-error --fail "${EXPORT_URL}" >"${export_file}"
  merkle_root="$(jq -r '.summary.merkleRoot // empty' "${export_file}")"

  if [ -z "${merkle_root}" ] || [ "${merkle_root}" = "null" ]; then
    error "Missing summary.merkleRoot in ${export_file}"
    exit 1
  fi

  digest="$(sha256_text "${merkle_root}")"
  {
    printf 'Merkle Root: %s\n' "${merkle_root}"
    printf 'SHA-256 Digest: %s\n' "${digest}"
  } >"${merkle_file}"

  info "Compliance export archived: ${export_file}"
  info "Merkle digest archived: ${merkle_file}"

  local stamps=() idx stamp
  while IFS= read -r stamp; do
    [ -n "${stamp}" ] && stamps+=("${stamp}")
  done < <(ls -1 "${EXPORT_DIR}"/compliance_export_*.json 2>/dev/null \
    | sed -E 's|.*/compliance_export_(.*)\.json$|\1|' \
    | sort -r)
  if [ "${#stamps[@]}" -gt "${EXPORT_RETENTION}" ]; then
    info "Pruning exports older than latest ${EXPORT_RETENTION} snapshots..."
    for ((idx = EXPORT_RETENTION; idx < ${#stamps[@]}; idx++)); do
      stamp="${stamps[idx]}"
      rm -f "${EXPORT_DIR}/compliance_export_${stamp}.json" "${EXPORT_DIR}/merkle_digest_${stamp}.txt"
    done
  fi
}

run_mirror_push() {
  if [ "${CONFIRM_MIRROR_PUSH}" != "YES" ]; then
    error "Mirror push blocked. Set CONFIRM_MIRROR_PUSH=YES explicitly."
    exit 1
  fi
  if [ -z "${TARGET_BRANCH}" ] || [ "${TARGET_BRANCH}" = "HEAD" ]; then
    error "Unable to detect a checked-out branch. Set TARGET_BRANCH before ENABLE_MIRROR_PUSH=1 when running from detached HEAD."
    exit 1
  fi
  if [ "${TARGET_BRANCH}" = "main" ]; then
    error "Mirror push to main is blocked. Use a dedicated branch and pull request."
    exit 1
  fi

  local existing_url=""
  if ! existing_url="$(git -C "${REPO_ROOT}" remote get-url "${TARGET_REMOTE_NAME}" 2>/dev/null)"; then
    info "Adding mirror remote '${TARGET_REMOTE_NAME}' => ${TARGET_REPO_URL}"
    git -C "${REPO_ROOT}" remote add "${TARGET_REMOTE_NAME}" "${TARGET_REPO_URL}"
  elif [ "${existing_url}" != "${TARGET_REPO_URL}" ]; then
    info "Updating mirror remote '${TARGET_REMOTE_NAME}' to ${TARGET_REPO_URL}"
    git -C "${REPO_ROOT}" remote set-url "${TARGET_REMOTE_NAME}" "${TARGET_REPO_URL}"
  fi

  info "Pushing branch '${TARGET_BRANCH}' to ${TARGET_REMOTE_NAME}..."
  git -C "${REPO_ROOT}" push "${TARGET_REMOTE_NAME}" "HEAD:${TARGET_BRANCH}"
  info "Mirror push complete"
}

main() {
  info "Local CI/CD starting from ${REPO_ROOT}"

  if [ "${ENABLE_DEPLOY}" = "1" ]; then
    run_deploy
  else
    info "Skipping deploy (ENABLE_DEPLOY=${ENABLE_DEPLOY})"
  fi

  if [ "${ENABLE_EXPORT_ARCHIVE}" = "1" ]; then
    archive_export
  else
    info "Skipping export archive (ENABLE_EXPORT_ARCHIVE=${ENABLE_EXPORT_ARCHIVE})"
  fi

  if [ "${ENABLE_MIRROR_PUSH}" = "1" ]; then
    run_mirror_push
  else
    info "Skipping mirror push (ENABLE_MIRROR_PUSH=${ENABLE_MIRROR_PUSH})"
  fi

  info "Local CI/CD completed successfully"
}

main "$@"
