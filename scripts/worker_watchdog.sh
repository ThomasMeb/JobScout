#!/usr/bin/env bash
# JobScout worker watchdog — to be run from cron every 30 min on the VPS.
#
# Detects "silent worker death" — i.e. Docker giving up after `on-failure:5`,
# or a hung process. Restarts the container if the heartbeat is stale and
# pages via Telegram so the operator knows it happened.
#
# Crontab entry (edit COMPOSE_DIR + TELEGRAM_* below):
#   */30 * * * * /opt/jobscout/scripts/worker_watchdog.sh >> /var/log/jobscout-watchdog.log 2>&1

set -euo pipefail

COMPOSE_DIR="${JOBSCOUT_DIR:-/opt/jobscout}"
COMPOSE_FILE="docker-compose.prod.yml"
MAX_STALE_HOURS="${WATCHDOG_MAX_STALE_HOURS:-2}"

cd "$COMPOSE_DIR"

# Load Telegram creds (and Supabase) from .env.prod.
set -a
# shellcheck disable=SC1091
source .env.prod
set +a

notify() {
    local msg="$1"
    [ -z "${TELEGRAM_BOT_TOKEN:-}" ] && return 0
    [ -z "${WATCHDOG_TELEGRAM_CHAT_ID:-}" ] && return 0
    curl -fsS -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
        -d "chat_id=${WATCHDOG_TELEGRAM_CHAT_ID}" \
        -d "text=${msg}" \
        -d "parse_mode=HTML" > /dev/null || true
}

# 1. Is the worker container even up?
STATE=$(docker compose -f "$COMPOSE_FILE" ps --format json worker 2>/dev/null \
        | grep -o '"State":"[^"]*"' | head -1 | cut -d'"' -f4 || echo "absent")

if [ "$STATE" != "running" ]; then
    echo "[$(date -Is)] worker state=$STATE — restarting"
    notify "⚠️ <b>Watchdog</b>: worker container state=<code>${STATE}</code>, restart triggered."
    docker compose -f "$COMPOSE_FILE" up -d --no-deps worker
    exit 0
fi

# 2. Container is "running" but the worker can hang. Check the heartbeat row.
#    PostgREST endpoint: GET /rest/v1/worker_heartbeats?id=eq.main&select=updated_at
HB_JSON=$(curl -fsS \
    "${SUPABASE_URL}/rest/v1/worker_heartbeats?id=eq.main&select=updated_at,status,error_message" \
    -H "apikey: ${SUPABASE_SERVICE_ROLE_KEY}" \
    -H "Authorization: Bearer ${SUPABASE_SERVICE_ROLE_KEY}" 2>/dev/null || echo "[]")

UPDATED_AT=$(echo "$HB_JSON" | grep -o '"updated_at":"[^"]*"' | head -1 | cut -d'"' -f4)

if [ -z "$UPDATED_AT" ]; then
    echo "[$(date -Is)] no heartbeat row — worker may have never booted"
    notify "⚠️ <b>Watchdog</b>: no <code>worker_heartbeats</code> row found. Did the worker ever start?"
    exit 0
fi

# Age of heartbeat in hours (GNU date).
HB_EPOCH=$(date -d "$UPDATED_AT" +%s 2>/dev/null || echo 0)
NOW_EPOCH=$(date +%s)
AGE_HOURS=$(( (NOW_EPOCH - HB_EPOCH) / 3600 ))

if [ "$AGE_HOURS" -ge "$MAX_STALE_HOURS" ]; then
    echo "[$(date -Is)] heartbeat is ${AGE_HOURS}h stale — restarting"
    notify "⚠️ <b>Watchdog</b>: worker heartbeat is <b>${AGE_HOURS}h</b> stale. Restarting container."
    docker compose -f "$COMPOSE_FILE" restart worker
else
    echo "[$(date -Is)] worker OK (heartbeat ${AGE_HOURS}h old)"
fi
