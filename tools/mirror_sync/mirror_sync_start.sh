#!/usr/bin/env bash
set -euo pipefail

APP="${EDARSAHUB_APP:-/app}"
DEV_BRANCH="${EDARSAHUB_DEV_BRANCH:-Edarsahub_Desarrollo}"
SERVICE="${EDARSAHUB_SUPERVISOR_SERVICE:-edarsahub-mirror-sync}"
STATE_DIR="$APP/.git/mirror-sync"
ENABLE_FLAG="$STATE_DIR/ENABLED"
PERSISTENT_STOP="$STATE_DIR/STOP"
SYNC_PAUSE="$APP/.git/EDARSAHUB_SYNC_PAUSED"
SAFETY_GUARD="$APP/tools/mirror_sync/shared_app_safety_guard.sh"

TEMP_DIR="${EDARSAHUB_MIRROR_TEMP_DIR:-/tmp/edarsahub-mirror-sync}"
TEMP_STOP="$TEMP_DIR/STOP"

RECOVERY_MODE=0
case "${1:-}" in
  "")
    ;;
  --recover-authorized)
    RECOVERY_MODE=1
    ;;
  *)
    echo "MIRROR_SYNC_ENABLE=BLOCKED_INVALID_ARG"
    echo "PRODUCTION_TOUCHED=NO"
    exit 2
    ;;
esac

cd "$APP"
mkdir -p "$STATE_DIR" "$TEMP_DIR"

test -r "$SAFETY_GUARD" || {
  echo "MIRROR_SYNC_ENABLE=BLOCKED_SAFETY_GUARD_MISSING"
  exit 79
}
. "$SAFETY_GUARD"

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

if [ "$RECOVERY_MODE" -eq 1 ]; then
  if [ -e "$PERSISTENT_STOP" ] || [ -e "$TEMP_STOP" ]; then
    echo "MIRROR_SYNC_RECOVERY=BLOCKED_EMERGENCY_STOP"
    echo "PRODUCTION_TOUCHED=NO"
    exit 86
  fi
  if [ ! -e "$ENABLE_FLAG" ]; then
    echo "MIRROR_SYNC_RECOVERY=BLOCKED_EXPLICIT_ENABLE_REQUIRED"
    echo "PRODUCTION_TOUCHED=NO"
    exit 87
  fi
  CURRENT_SUP_STATUS="$(supervisorctl status "$SERVICE" 2>&1 || true)"
  case "$CURRENT_SUP_STATUS" in
    *" RUNNING "*|*" STARTING "*)
      echo "MIRROR_SYNC_ALREADY_RUNNING=YES"
      echo "MIRROR_SYNC_RECOVERY=ALREADY_RUNNING"
      echo "PRODUCTION_TOUCHED=NO"
      exit 0
      ;;
    *" STOPPED "*)
      case "$CURRENT_SUP_STATUS" in
        *"Not started"*|*"NOT STARTED"*)
          ;;
        *)
          echo "MIRROR_SYNC_RECOVERY=BLOCKED_ADMINISTRATIVE_STOP"
          echo "PRODUCTION_TOUCHED=NO"
          exit 88
          ;;
      esac
      ;;
    *)
      echo "MIRROR_SYNC_RECOVERY=DEFERRED_SUPERVISOR_STATE"
      echo "PRODUCTION_TOUCHED=NO"
      exit 89
      ;;
  esac
fi

STATUS="$(edarsahub_effective_status)"
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

if [ "$RECOVERY_MODE" -eq 1 ]; then
  supervisorctl start "$SERVICE" >/dev/null 2>&1
  POST_SUP_STATUS="$(supervisorctl status "$SERVICE" 2>&1 || true)"
  case "$POST_SUP_STATUS" in
    *" RUNNING "*|*" STARTING "*)
      echo "MIRROR_SYNC_HEALTH_GATE=PASS"
      echo "MIRROR_SYNC_ENABLED=YES"
      echo "MIRROR_SYNC_RECOVERY=STARTED"
      echo "PRODUCTION_TOUCHED=NO"
      exit 0
      ;;
    *)
      echo "MIRROR_SYNC_RECOVERY=START_UNCONFIRMED"
      echo "PRODUCTION_TOUCHED=NO"
      exit 90
      ;;
  esac
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

CURRENT_SUP_STATUS="$(supervisorctl status "$SERVICE" 2>&1 || true)"
case "$CURRENT_SUP_STATUS" in
  *" RUNNING "*|*" STARTING "*)
    echo "MIRROR_SYNC_ALREADY_RUNNING=YES"
    ;;
  *)
    supervisorctl start "$SERVICE" >/dev/null 2>&1 || supervisorctl restart "$SERVICE"
    ;;
esac

echo "MIRROR_SYNC_HEALTH_GATE=PASS"
echo "MIRROR_SYNC_ENABLED=YES"
echo "PERSISTENT_EMERGENCY_STOP=INACTIVE"
echo "TEMPORARY_EMERGENCY_STOP=INACTIVE"
echo "PRODUCTION_TOUCHED=NO"
