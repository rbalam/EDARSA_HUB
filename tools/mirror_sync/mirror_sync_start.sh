#!/usr/bin/env bash
set -euo pipefail

APP="${EDARSAHUB_APP:-/app}"
DEV_BRANCH="${EDARSAHUB_DEV_BRANCH:-Edarsahub_Desarrollo}"
SERVICE="${EDARSAHUB_SUPERVISOR_SERVICE:-edarsahub-mirror-sync}"
STATE_DIR="$APP/.git/mirror-sync"
ENABLE_FLAG="$STATE_DIR/ENABLED"
PERSISTENT_STOP="$STATE_DIR/STOP"
SYNC_PAUSE="$APP/.git/EDARSAHUB_SYNC_PAUSED"

TEMP_DIR="/tmp/edarsahub-mirror-sync"
TEMP_STOP="$TEMP_DIR/STOP"

cd "$APP"
mkdir -p "$STATE_DIR" "$TEMP_DIR"

ENV_NAME="$(printf '%s' "${EDARSA_ENV:-${APP_ENV:-${ENVIRONMENT:-PREVIEW}}}" | tr '[:lower:]' '[:upper:]')"
case "$ENV_NAME" in
  *PROD*)
    echo "MIRROR_SYNC_ENABLE=BLOCKED_PRODUCTION_ENV"
    echo "PRODUCTION_TOUCHED=NO"
    exit 80
    ;;
esac

BRANCH="$(git branch --show-current)"
if [ "$BRANCH" != "$DEV_BRANCH" ]; then
  echo "MIRROR_SYNC_ENABLE=BLOCKED_WRONG_BRANCH"
  echo "EXPECTED=$DEV_BRANCH"
  echo "ACTUAL=$BRANCH"
  exit 81
fi

if [ -e "$SYNC_PAUSE" ]; then
  echo "MIRROR_SYNC_ENABLE=BLOCKED_GLOBAL_PAUSE"
  exit 82
fi

STATUS="$(git status --porcelain=v1 --untracked-files=all)"
if [ -n "$STATUS" ]; then
  echo "MIRROR_SYNC_ENABLE=DEFERRED_LOCAL_DIRTY"
  printf '%s\n' "$STATUS"
  echo "LOCAL_WORK_PRESERVATION_REQUIRED=YES"
  exit 83
fi

git fetch --quiet origin "$DEV_BRANCH" || {
  echo "MIRROR_SYNC_ENABLE=FETCH_FAILED"
  exit 84
}

read -r LOCAL_AHEAD REMOTE_AHEAD <<EOF
$(git rev-list --left-right --count "HEAD...origin/$DEV_BRANCH")
EOF

if [ "$LOCAL_AHEAD" -ne 0 ]; then
  echo "MIRROR_SYNC_ENABLE=BLOCKED_LOCAL_AHEAD"
  echo "LOCAL_AHEAD=$LOCAL_AHEAD"
  echo "REMOTE_AHEAD=$REMOTE_AHEAD"
  exit 85
fi

# Authorization is granted only after all health gates pass. If remote is ahead,
# the watchdog may perform the already-certified --ff-only convergence.
rm -f "$PERSISTENT_STOP" "$TEMP_STOP"
{
  echo "ENABLED_AT_UTC=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "HOST=$(hostname)"
  echo "PID=$$"
  echo "BRANCH=$BRANCH"
  echo "LOCAL_HEAD=$(git rev-parse HEAD)"
  echo "REMOTE_HEAD=$(git rev-parse origin/$DEV_BRANCH)"
  echo "LOCAL_AHEAD=$LOCAL_AHEAD"
  echo "REMOTE_AHEAD=$REMOTE_AHEAD"
} > "$ENABLE_FLAG"
chmod 0600 "$ENABLE_FLAG"

supervisorctl start "$SERVICE" >/dev/null 2>&1 || supervisorctl restart "$SERVICE"

echo "MIRROR_SYNC_HEALTH_GATE=PASS"
echo "MIRROR_SYNC_ENABLED=YES"
echo "PERSISTENT_EMERGENCY_STOP=INACTIVE"
echo "TEMPORARY_EMERGENCY_STOP=INACTIVE"
echo "PRODUCTION_TOUCHED=NO"
