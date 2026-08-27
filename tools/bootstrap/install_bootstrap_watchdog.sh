#!/usr/bin/env bash
set -euo pipefail

APP="${EDARSAHUB_APP:-/app}"
INSTALL_DIR="${EDARSAHUB_BOOTSTRAP_INSTALL_DIR:-/opt/edarsahub-bootstrap}"
SUPERVISOR_DIR="${EDARSAHUB_SUPERVISOR_DIR:-/etc/supervisor/conf.d}"
SERVICE="edarsahub-bootstrap-watchdog"

[ -d "$APP/.git" ] || { echo "ERROR: $APP is not a git checkout" >&2; exit 2; }
command -v supervisorctl >/dev/null || { echo "ERROR: supervisorctl not found" >&2; exit 3; }

install -d -m 0755 "$INSTALL_DIR" /var/lib/edarsahub-bootstrap
install -m 0755 "$APP/tools/bootstrap/edarsahub_bootstrap_watchdog.py" "$INSTALL_DIR/edarsahub_bootstrap_watchdog.py"
install -m 0644 "$APP/tools/bootstrap/edarsahub-bootstrap-watchdog.conf" "$SUPERVISOR_DIR/edarsahub-bootstrap-watchdog.conf"

/usr/bin/python3 -m py_compile "$INSTALL_DIR/edarsahub_bootstrap_watchdog.py"
/usr/bin/python3 "$INSTALL_DIR/edarsahub_bootstrap_watchdog.py" --once

supervisorctl reread
supervisorctl update
supervisorctl restart "$SERVICE" || supervisorctl start "$SERVICE"
sleep 3
supervisorctl status "$SERVICE"

echo "BOOTSTRAP_WATCHDOG_INSTALLED=1"
echo "STATUS=/var/lib/edarsahub-bootstrap/status.json"
