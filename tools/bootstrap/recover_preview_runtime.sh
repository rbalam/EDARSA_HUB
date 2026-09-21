#!/usr/bin/env bash
set -euo pipefail

APP="${EDARSAHUB_APP:-/app}"
DEV_BRANCH="${EDARSAHUB_DEV_BRANCH:-Edarsahub_Desarrollo}"
BACKEND_SERVICE="backend"
WORKER_SERVICE="edarsahub-universal-worker"
INSTALLER="$APP/tools/bootstrap/install_bootstrap_watchdog.sh"
PREFERRED_JOB_ID="${1:-}"

log(){ printf '%s %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$*"; }

cd "$APP"

ENV_NAME="$(printf '%s' "${EDARSA_ENV:-${APP_ENV:-${ENVIRONMENT:-PREVIEW}}}" | tr '[:lower:]' '[:upper:]')"
case "$ENV_NAME" in
  *PROD*)
    echo "PREVIEW_RUNTIME_RECOVERY=BLOCKED_PRODUCTION_ENV"
    echo "PRODUCTION_TOUCHED=NO"
    exit 80
    ;;
esac

BRANCH="$(git branch --show-current)"
if [ "$BRANCH" != "$DEV_BRANCH" ]; then
  echo "PREVIEW_RUNTIME_RECOVERY=BLOCKED_WRONG_BRANCH"
  echo "EXPECTED=$DEV_BRANCH"
  echo "ACTUAL=$BRANCH"
  exit 81
fi

if [ -n "$(git status --porcelain=v1 --untracked-files=all)" ]; then
  echo "PREVIEW_RUNTIME_RECOVERY=DEFERRED_LOCAL_DIRTY"
  echo "LOCAL_WORK_PRESERVATION_REQUIRED=YES"
  echo "PRODUCTION_TOUCHED=NO"
  exit 82
fi

if [ -n "$PREFERRED_JOB_ID" ] && ! [[ "$PREFERRED_JOB_ID" =~ ^[A-Za-z0-9][A-Za-z0-9._-]{2,120}$ ]]; then
  echo "PREVIEW_RUNTIME_RECOVERY=INVALID_PREFERRED_JOB_ID"
  exit 83
fi

log "PREVIEW_RUNTIME_RECOVERY=FETCH"
git fetch --quiet origin "$DEV_BRANCH"

read -r LOCAL_AHEAD REMOTE_AHEAD <<EOF
$(git rev-list --left-right --count "HEAD...origin/$DEV_BRANCH")
EOF

if [ "$LOCAL_AHEAD" -ne 0 ]; then
  echo "PREVIEW_RUNTIME_RECOVERY=BLOCKED_LOCAL_AHEAD"
  echo "LOCAL_AHEAD=$LOCAL_AHEAD"
  echo "REMOTE_AHEAD=$REMOTE_AHEAD"
  echo "PRODUCTION_TOUCHED=NO"
  exit 84
fi

if [ "$REMOTE_AHEAD" -gt 0 ]; then
  git merge --ff-only "origin/$DEV_BRANCH"
  log "PREVIEW_RUNTIME_RECOVERY=FAST_FORWARD_APPLIED"
else
  log "PREVIEW_RUNTIME_RECOVERY=ALREADY_ALIGNED"
fi

test -x "$INSTALLER" || chmod 0755 "$INSTALLER"
"$INSTALLER"

supervisorctl restart "$BACKEND_SERVICE"
sleep 6
supervisorctl status "$BACKEND_SERVICE"
supervisorctl restart "$WORKER_SERVICE" || supervisorctl start "$WORKER_SERVICE"
sleep 4
supervisorctl status "$WORKER_SERVICE"

QUEUE_SHA="$(git ls-remote origin refs/heads/worker/requests | awk '{print $1}')"
test "${#QUEUE_SHA}" -eq 40

HEADERS=(
  -H "X-Worker-Queue-Sha: $QUEUE_SHA"
  -H "Content-Type: application/json"
)
if [ -n "$PREFERRED_JOB_ID" ]; then
  HEADERS+=( -H "X-Worker-Preferred-Job-Id: $PREFERRED_JOB_ID" )
fi

HTTP_CODE="$(curl --silent --show-error \
  --connect-timeout 3 --max-time 20 \
  --output /tmp/edarsahub-local-wake.json --write-out '%{http_code}' \
  --request POST "http://127.0.0.1:8001/api/internal/worker/wake" \
  "${HEADERS[@]}" \
  --data '{}' || true)"

cat /tmp/edarsahub-local-wake.json 2>/dev/null || true
echo
echo "LOCAL_WAKE_HTTP_CODE=$HTTP_CODE"

case "$HTTP_CODE" in
  200|202|429)
    ;;
  409)
    if ! grep -qi 'worker wake already in progress' /tmp/edarsahub-local-wake.json 2>/dev/null; then
      echo "PREVIEW_RUNTIME_RECOVERY=WAKE_CONFLICT"
      exit 85
    fi
    ;;
  *)
    echo "PREVIEW_RUNTIME_RECOVERY=LOCAL_WAKE_FAILED"
    exit 86
    ;;
esac

for _ in $(seq 1 12); do
  if [ -r "$APP/.git/universal-worker-queue/runtime/last_receive_utc" ]; then
    LAST_RECEIVE="$(cat "$APP/.git/universal-worker-queue/runtime/last_receive_utc" 2>/dev/null || true)"
    if [ -n "$LAST_RECEIVE" ]; then
      echo "WORKER_LAST_RECEIVE_UTC=$LAST_RECEIVE"
      echo "PREVIEW_RUNTIME_RECOVERY=COMPLETE"
      echo "PRODUCTION_TOUCHED=NO"
      exit 0
    fi
  fi
  sleep 5
done

echo "PREVIEW_RUNTIME_RECOVERY=WORKER_HEARTBEAT_NOT_CONFIRMED"
echo "PRODUCTION_TOUCHED=NO"
exit 87
