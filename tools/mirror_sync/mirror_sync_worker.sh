#!/usr/bin/env bash
set -euo pipefail

SAFETY_GUARD="/app/tools/mirror_sync/shared_app_safety_guard.sh"
test -r "$SAFETY_GUARD" || {
    echo "ABORT=SHARED_APP_SAFETY_GUARD_MISSING"
    exit 90
}
. "$SAFETY_GUARD"
edarsahub_require_sync_enabled || exit $?
edarsahub_require_clean_shared_app || exit $?


ROOT="/app"
DIR="$ROOT/tools/mirror_sync"
RUNTIME_GENERATION="20260827-mirror-runtime-control-plane-v3"

resolve_worker_python() {
    if [ -x "$ROOT/.venv/bin/python" ]; then printf '%s\n' "$ROOT/.venv/bin/python"; return 0; fi
    command -v python3 2>/dev/null || command -v python 2>/dev/null || true
}

PYTHON_BIN="$(resolve_worker_python)"
[ -n "$PYTHON_BIN" ] && [ -x "$PYTHON_BIN" ] || { echo "ABORT=WORKER_PYTHON_NOT_EXECUTABLE"; exit 4; }

CHECK="$DIR/check_remote_update.sh"
APPLY="$DIR/apply_remote_update.sh"
PUBLISH="$DIR/publish_local_snapshot.sh"
FINALIZER="$DIR/finalize_local_snapshot.sh"
REPORTER="$DIR/mirror_sync_result_reporter.py"
AUDIT_EXPORTER="$DIR/mirror_sync_audit_exporter.py"
UNIVERSAL_WORKER="$DIR/universal_job_worker.sh"
CONTROL_PLANE="$DIR/worker_control_plane.py"

STATE_DIR="$ROOT/.git/mirror-sync"
ENABLE_FLAG="$STATE_DIR/ENABLED"
PERSISTENT_STOP="$STATE_DIR/STOP"
TEMP_STOP="/tmp/edarsahub-mirror-sync/STOP"
UNIVERSAL_STATE="$ROOT/.git/universal-worker-queue/runtime"
LOOP_SECONDS="${MIRROR_SYNC_LOOP_SECONDS:-60}"
MIRROR_TOOL_TIMEOUT_SECONDS="${MIRROR_TOOL_TIMEOUT_SECONDS:-120}"
MIRROR_APPLY_TIMEOUT_SECONDS="${MIRROR_APPLY_TIMEOUT_SECONDS:-180}"
MIRROR_FINALIZE_TIMEOUT_SECONDS="${MIRROR_FINALIZE_TIMEOUT_SECONDS:-180}"
REPORTING_TIMEOUT_SECONDS="${MIRROR_REPORTING_TIMEOUT_SECONDS:-90}"
RUNNING=1
UNIVERSAL_PID=""
CONTROL_PID=""

log(){ printf '%s %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$*"; }
shutdown_worker(){ RUNNING=0; log "WORKER_SIGNAL_RECEIVED=YES"; }
trap shutdown_worker TERM INT HUP
is_authorized(){ [ ! -e "$PERSISTENT_STOP" ] && [ ! -e "$TEMP_STOP" ] && [ -e "$ENABLE_FLAG" ]; }

run_tool(){
    local NAME="$1" TIMEOUT_SECONDS="$2"; shift 2
    local OUT RC; OUT="$(mktemp)"; set +e
    if command -v timeout >/dev/null 2>&1; then timeout --signal=TERM --kill-after=5 "${TIMEOUT_SECONDS}s" "$@" >"$OUT" 2>&1; RC=$?; else "$@" >"$OUT" 2>&1; RC=$?; fi
    set -e; log "TOOL=$NAME RC=$RC"; cat "$OUT"; rm -f "$OUT"
    if [ "$RC" -eq 124 ] || [ "$RC" -eq 137 ]; then log "TOOL=$NAME TIMEOUT=YES"; fi
    return "$RC"
}

extract_snapshot(){ awk -F= '$1=="SNAPSHOT_COMMIT"{v=$2} $1=="MIRROR_HEAD"{v=$2} END{if(v!="")print v}'; }

start_universal_worker(){
    [ -r "$UNIVERSAL_WORKER" ] || { log "UNIVERSAL_JOB_WORKER_AVAILABLE=NO"; return 1; }
    /bin/bash "$UNIVERSAL_WORKER" & UNIVERSAL_PID=$!
    mkdir -p "$UNIVERSAL_STATE"; printf '%s\n' "$UNIVERSAL_PID" > "$UNIVERSAL_STATE/parent_child_pid"
    log "UNIVERSAL_JOB_WORKER_STARTED_BY_MIRROR=YES"; log "UNIVERSAL_JOB_WORKER_PID=$UNIVERSAL_PID"
}

start_control_plane(){
    [ -r "$CONTROL_PLANE" ] || { log "CONTROL_PLANE_AVAILABLE=NO"; return 1; }
    "$PYTHON_BIN" "$CONTROL_PLANE" & CONTROL_PID=$!
    mkdir -p "$UNIVERSAL_STATE"; printf '%s\n' "$CONTROL_PID" > "$UNIVERSAL_STATE/control_plane_pid"
    log "CONTROL_PLANE_STARTED=YES"; log "CONTROL_PLANE_PID=$CONTROL_PID"
}

stop_child(){ local PID="${1:-}"; [ -n "$PID" ] || return 0; if kill -0 "$PID" 2>/dev/null; then kill -TERM "$PID" 2>/dev/null || true; for _ in $(seq 1 20); do kill -0 "$PID" 2>/dev/null || break; sleep 0.25; done; kill -KILL "$PID" 2>/dev/null || true; wait "$PID" 2>/dev/null || true; fi; }
stop_universal_worker(){ stop_child "$UNIVERSAL_PID"; UNIVERSAL_PID=""; }
stop_control_plane(){ stop_child "$CONTROL_PID"; CONTROL_PID=""; }

ensure_universal_worker(){ if [ -z "${UNIVERSAL_PID:-}" ] || ! kill -0 "$UNIVERSAL_PID" 2>/dev/null; then [ -z "${UNIVERSAL_PID:-}" ] || wait "$UNIVERSAL_PID" 2>/dev/null || true; log "UNIVERSAL_JOB_WORKER_NOT_RUNNING=YES"; start_universal_worker || true; fi; }
ensure_control_plane(){ if [ -z "${CONTROL_PID:-}" ] || ! kill -0 "$CONTROL_PID" 2>/dev/null; then [ -z "${CONTROL_PID:-}" ] || wait "$CONTROL_PID" 2>/dev/null || true; log "CONTROL_PLANE_NOT_RUNNING=YES"; start_control_plane || true; fi; }

run_cycle(){
    local CHECK_OUT CHECK_RC PUBLISH_OUT PUBLISH_RC SNAPSHOT FINALIZE_RC
    if ! is_authorized; then log "STATE=DISABLED"; return 0; fi
    log "STATE=AUTHORIZED"; CHECK_OUT="$(mktemp)"; set +e
    if command -v timeout >/dev/null 2>&1; then timeout --signal=TERM --kill-after=5 "${MIRROR_TOOL_TIMEOUT_SECONDS}s" "$CHECK" >"$CHECK_OUT" 2>&1; CHECK_RC=$?; else "$CHECK" >"$CHECK_OUT" 2>&1; CHECK_RC=$?; fi
    set -e; log "CHECK_RC=$CHECK_RC"; cat "$CHECK_OUT"
    if [ "$CHECK_RC" -eq 124 ] || [ "$CHECK_RC" -eq 137 ]; then rm -f "$CHECK_OUT"; log "STATE=CHECK_TIMEOUT"; return 0; fi
    if [ "$CHECK_RC" -eq 90 ]; then rm -f "$CHECK_OUT"; log "STATE=DISABLED_DURING_CHECK"; return 0; fi
    if [ "$CHECK_RC" -eq 91 ] || [ "$CHECK_RC" -eq 92 ]; then rm -f "$CHECK_OUT"; log "STATE=LOCK_UNAVAILABLE"; return 0; fi
    if [ "$CHECK_RC" -ne 0 ]; then rm -f "$CHECK_OUT"; log "STATE=CHECK_ERROR"; return 0; fi
    if grep -q '^DECISION=SAFE_REMOTE_FAST_FORWARD_AVAILABLE$' "$CHECK_OUT"; then rm -f "$CHECK_OUT"; log "STATE=REMOTE_FAST_FORWARD_AVAILABLE"; if run_tool "APPLY_REMOTE_UPDATE" "$MIRROR_APPLY_TIMEOUT_SECONDS" "$APPLY"; then log "STATE=REMOTE_APPLY_COMPLETE"; else log "STATE=REMOTE_APPLY_FAILED"; fi; return 0; fi
    if ! grep -q '^DECISION=ALREADY_SYNCHRONIZED$' "$CHECK_OUT"; then rm -f "$CHECK_OUT"; log "STATE=UNKNOWN_CHECK_DECISION"; return 0; fi
    rm -f "$CHECK_OUT"; log "STATE=REMOTE_CONVERGED"
    if ! is_authorized; then log "STATE=DISABLED_BEFORE_LOCAL_PUBLISH"; return 0; fi
    PUBLISH_OUT="$(mktemp)"; set +e
    if command -v timeout >/dev/null 2>&1; then timeout --signal=TERM --kill-after=5 "${MIRROR_TOOL_TIMEOUT_SECONDS}s" "$PUBLISH" --publish >"$PUBLISH_OUT" 2>&1; PUBLISH_RC=$?; else "$PUBLISH" --publish >"$PUBLISH_OUT" 2>&1; PUBLISH_RC=$?; fi
    set -e; log "PUBLISH_RC=$PUBLISH_RC"; cat "$PUBLISH_OUT"
    if [ "$PUBLISH_RC" -eq 124 ] || [ "$PUBLISH_RC" -eq 137 ]; then rm -f "$PUBLISH_OUT"; log "STATE=PUBLISH_TIMEOUT"; return 0; fi
    if [ "$PUBLISH_RC" -eq 90 ]; then rm -f "$PUBLISH_OUT"; log "STATE=DISABLED_DURING_PUBLISH"; return 0; fi
    if [ "$PUBLISH_RC" -eq 91 ] || [ "$PUBLISH_RC" -eq 92 ]; then rm -f "$PUBLISH_OUT"; log "STATE=LOCK_UNAVAILABLE"; return 0; fi
    if [ "$PUBLISH_RC" -ne 0 ]; then rm -f "$PUBLISH_OUT"; log "STATE=PUBLISH_ERROR"; return 0; fi
    if grep -q '^DECISION=NO_CHANGES_TO_PUBLISH$' "$PUBLISH_OUT"; then rm -f "$PUBLISH_OUT"; log "STATE=CONVERGED_NO_LOCAL_CHANGES"; return 0; fi
    SNAPSHOT="$(extract_snapshot < "$PUBLISH_OUT")"; rm -f "$PUBLISH_OUT"; [ -n "$SNAPSHOT" ] || { log "STATE=SNAPSHOT_NOT_RESOLVED"; return 0; }
    case "$SNAPSHOT" in *[!0-9a-fA-F]*) log "STATE=INVALID_SNAPSHOT_FORMAT"; return 0;; esac
    [ "${#SNAPSHOT}" -eq 40 ] || { log "STATE=INVALID_SNAPSHOT_LENGTH"; return 0; }
    log "STATE=MIRROR_SNAPSHOT_PUBLISHED"; log "SNAPSHOT=$SNAPSHOT"; is_authorized || { log "STATE=DISABLED_BEFORE_FINALIZE"; return 0; }
    set +e; if command -v timeout >/dev/null 2>&1; then timeout --signal=TERM --kill-after=5 "${MIRROR_FINALIZE_TIMEOUT_SECONDS}s" "$FINALIZER" "$SNAPSHOT"; FINALIZE_RC=$?; else "$FINALIZER" "$SNAPSHOT"; FINALIZE_RC=$?; fi; set -e
    log "FINALIZER_RC=$FINALIZE_RC"; [ "$FINALIZE_RC" -eq 0 ] && { log "STATE=LOCAL_REMOTE_MIRROR_CONVERGED"; return 0; }; log "STATE=FINALIZER_ERROR"
}

run_reporting_pipeline(){ if [ -x "$REPORTER" ]; then run_tool "RESULT_REPORTER" "$REPORTING_TIMEOUT_SECONDS" "$REPORTER" || true; else log "RESULT_REPORTER_AVAILABLE=NO"; return 0; fi; if [ -x "$AUDIT_EXPORTER" ]; then run_tool "AUDIT_EXPORTER" "$REPORTING_TIMEOUT_SECONDS" "$AUDIT_EXPORTER" || true; else log "AUDIT_EXPORTER_AVAILABLE=NO"; fi; }

case "$LOOP_SECONDS" in ''|*[!0-9]*) echo "ABORT=INVALID_LOOP_SECONDS"; exit 2;; esac
[ "$LOOP_SECONDS" -ge 10 ] || { echo "ABORT=LOOP_SECONDS_TOO_LOW"; exit 3; }

log "MIRROR_WORKER_STARTED=YES"; log "RUNTIME_GENERATION=$RUNTIME_GENERATION"; log "LOOP_SECONDS=$LOOP_SECONDS"
start_control_plane || true
start_universal_worker || true
while [ "$RUNNING" -eq 1 ]; do ensure_control_plane; ensure_universal_worker; run_cycle; ensure_control_plane; ensure_universal_worker; run_reporting_pipeline; [ "$RUNNING" -ne 0 ] || break; sleep "$LOOP_SECONDS" & wait $! || true; done
stop_universal_worker; stop_control_plane; log "MIRROR_WORKER_STOPPED=YES"; exit 0
