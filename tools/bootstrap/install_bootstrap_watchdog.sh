#!/usr/bin/env bash
set -euo pipefail

APP="${EDARSAHUB_APP:-/app}"
SUPERVISOR_DIR="${EDARSAHUB_SUPERVISOR_DIR:-/etc/supervisor/conf.d}"
SERVICE="edarsahub-bootstrap-watchdog"
MIRROR_SERVICE="edarsahub-mirror-sync"
WORKER_SERVICE="edarsahub-universal-worker"
CONTROL_PLANE_SERVICE="edarsahub-worker-control-plane"
MIRROR_STATE="$APP/.git/mirror-sync"
MIRROR_ENABLE="$MIRROR_STATE/ENABLED"
MIRROR_STOP="$MIRROR_STATE/STOP"

[ -d "$APP/.git" ] || { echo "ERROR: $APP is not a git checkout" >&2; exit 2; }
command -v supervisorctl >/dev/null || { echo "ERROR: supervisorctl not found" >&2; exit 3; }

# Persistent blindage: every pod/bootstrap starts fail-closed.
# A human/canonical recovery action must explicitly re-enable mirror-sync via
# tools/mirror_sync/mirror_sync_start.sh after repository health is verified.
install -d -m 0700 "$MIRROR_STATE"
rm -f "$MIRROR_ENABLE"
printf 'POD_BOOTSTRAP_FAIL_CLOSED_AT_UTC=%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" > "$MIRROR_STOP"
chmod 0600 "$MIRROR_STOP"

install -d -m 0755 /var/lib/edarsahub-bootstrap
install -m 0644 "$APP/tools/bootstrap/edarsahub-bootstrap-watchdog.conf" "$SUPERVISOR_DIR/edarsahub-bootstrap-watchdog.conf"
install -m 0644 "$APP/tools/mirror_sync/supervisor/edarsahub-mirror-sync.conf" "$SUPERVISOR_DIR/edarsahub-mirror-sync.conf"
install -m 0644 "$APP/tools/mirror_sync/edarsahub-universal-worker.conf" "$SUPERVISOR_DIR/edarsahub-universal-worker.conf"
install -m 0644 "$APP/tools/mirror_sync/edarsahub-worker-control-plane.conf" "$SUPERVISOR_DIR/edarsahub-worker-control-plane.conf"

/usr/bin/python3 -m py_compile "$APP/tools/bootstrap/edarsahub_bootstrap_watchdog.py"
/usr/bin/python3 "$APP/tools/bootstrap/edarsahub_bootstrap_watchdog.py" --once

supervisorctl reread
supervisorctl update
supervisorctl stop "$MIRROR_SERVICE" >/dev/null 2>&1 || true
supervisorctl restart "$SERVICE" || supervisorctl start "$SERVICE"
supervisorctl restart "$WORKER_SERVICE" || supervisorctl start "$WORKER_SERVICE"
supervisorctl restart "$CONTROL_PLANE_SERVICE" || supervisorctl start "$CONTROL_PLANE_SERVICE"
sleep 3
supervisorctl status "$SERVICE"
supervisorctl status "$WORKER_SERVICE"
supervisorctl status "$CONTROL_PLANE_SERVICE"
supervisorctl status "$MIRROR_SERVICE" || true

echo "BOOTSTRAP_WATCHDOG_INSTALLED=1"
echo "MIRROR_SYNC_STARTUP_POLICY=FAIL_CLOSED"
echo "MIRROR_SYNC_AUTHORIZED=NO"
echo "PRODUCTION_TOUCHED=NO"
echo "STATUS=/var/lib/edarsahub-bootstrap/status.json"
