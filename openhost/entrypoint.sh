#!/bin/bash
# Sculptor container entrypoint for OpenHost (packaged release).
#
# 1. Fetch secrets from the OpenHost secrets service
# 2. Wire openhost data dirs to sculptor env vars
# 3. Configure the non-root user for terminal sessions
# 4. Configure Git
# 5. Seed a default user config (skip onboarding wizard)
# 6. Export secrets into the environment
# 7. Start supervisord (runs sculptor backend, seed-workspace)
set -e

# --- 1. Fetch secrets ---
echo "entrypoint: fetching secrets..."
python3 /app/setup/fetch_secrets.py
chmod 644 /run/openhost-secrets.env 2>/dev/null || true

# --- 2. Wire data directories ---
export SCULPTOR_FOLDER="${OPENHOST_APP_DATA_DIR}"
export DATABASE_URL="sqlite:///${OPENHOST_APP_DATA_DIR}/database.db"
export LOG_PATH="${OPENHOST_APP_DATA_DIR}/logs"
export TASK_SYNC_DIR="${OPENHOST_APP_TEMP_DIR}/task_sync"
export WORKSPACE_SYNC_DIR="${OPENHOST_APP_TEMP_DIR}/workspace_sync"

mkdir -p "${SCULPTOR_FOLDER}" "${LOG_PATH}" "${TASK_SYNC_DIR}" "${WORKSPACE_SYNC_DIR}"

# --- 3. Configure non-root user ---
# devuser is created at build time in the Dockerfile.
DEVUSER="devuser"
DEVUSER_HOME="${OPENHOST_APP_DATA_DIR}/home"
export SCULPTOR_RUN_USER="${DEVUSER}"

# Point devuser's home at the persistent data dir
usermod -d "${DEVUSER_HOME}" "${DEVUSER}"
mkdir -p "${DEVUSER_HOME}"

chown -R "${DEVUSER}:${DEVUSER}" "${DEVUSER_HOME}"
chown -R "${DEVUSER}:${DEVUSER}" "${OPENHOST_APP_DATA_DIR}"
chown -R "${DEVUSER}:${DEVUSER}" "${OPENHOST_APP_TEMP_DIR}"

# --- 4. Configure Git ---
echo "entrypoint: setting up git..."
su - "${DEVUSER}" -c "bash /app/setup/setup_git.sh"

# --- 5. Seed default config (first run only) ---
CONFIG_FILE="${SCULPTOR_FOLDER}/config.toml"
if [ ! -f "${CONFIG_FILE}" ]; then
    DEFAULT_EMAIL="user@openhost.local"
    cat > "${CONFIG_FILE}" <<EOF
user_email = "${DEFAULT_EMAIL}"
user_full_name = "OpenHost User"
user_id = "$(echo -n "${DEFAULT_EMAIL}" | md5sum | cut -d' ' -f1)"
organization_id = "$(echo -n "organization:${DEFAULT_EMAIL}" | md5sum | cut -d' ' -f1)"
instance_id = "$(cat /proc/sys/kernel/random/uuid 2>/dev/null || uuidgen || echo openhost-instance)"
is_privacy_policy_consented = true
EOF
    chown "${DEVUSER}:${DEVUSER}" "${CONFIG_FILE}"
    echo "entrypoint: created default config at ${CONFIG_FILE}"
fi

# --- 6. Export secrets into the environment ---
# Claude Code reads ANTHROPIC_API_KEY directly from the environment,
# so we source the secrets file here so it propagates to all child processes.
source /run/openhost-secrets.env 2>/dev/null || true

# --- 7. Start supervisord ---
echo "entrypoint: starting supervisord..."
exec supervisord -n -c /etc/supervisor/conf.d/sculptor.conf
