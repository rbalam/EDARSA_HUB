#!/usr/bin/env bash
set -euo pipefail

ROOT="/app"
DIR="$ROOT/tools/mirror_sync"
RUNTIME_GENERATION="20260826-canonical-python-v1"

resolve_worker_python() {
    if [ -x "$ROOT/.venv/bin/python" ]; then
        printf '%s\n' "$ROOT/.venv/bin/python"
        return 0
    fi

    command -v python3 2>/dev/null || command -v python 2>/dev/null || true
}

PYTHON_BIN="$(resolve_worker_python)"

if [ -z "$PYTHON_BIN" ] || [ ! -x "$PYTHON_BIN" ]; then
    echo "ABORT=WORKER_PYTHON_NOT_EXECUTABLE"
    exit 4
fi

CHECK="$DIR/check_remote_update.sh"
APPLY="$DIR/apply_remote_update.sh"
PUBLISH="$DIR/publish_local_snapshot.sh"
FINALIZER="$DIR/finalize_local_snapshot.sh"
STATUS="$DIR/mirror_sync_status.sh"
REPORTER="$DIR/mirror_sync_result_reporter.py"
AUDIT_EXPORTER="$DIR/mirror_sync_audit_exporter.py"
UNIVERSAL_BRIDGE="$DIR/universal_job_bridge.py"
UNIVERSAL_DISPATCHER="$DIR/universal_job_dispatcher.py"
UNIVERSAL_RESULT_PUBLISHER="$DIR/universal_job_result_publisher.py"
RUNTIME_HEALTH_PUBLISHER="$DIR/runtime_health_publisher.py"

STATE_DIR="$ROOT/.git/mirror-sync"
ENABLE_FLAG="$STATE_DIR/ENABLED"
PERSISTENT_STOP="$STATE_DIR/STOP"
TEMP_STOP="/tmp/edarsahub-mirror-sync/STOP"

LOOP_SECONDS="${MIRROR_SYNC_LOOP_SECONDS:-60}"
RUNNING=1

log() { printf '%s %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$*"; }
shutdown_worker() { RUNNING=0; log "WORKER_SIGNAL_RECEIVED=YES"; }
trap shutdown_worker TERM INT

is_authorized() {
    [ ! -e "$PERSISTENT_STOP" ] && [ ! -e "$TEMP_STOP" ] && [ -e "$ENABLE_FLAG" ]
}

run_tool() {
    local NAME="$1"; shift
    local OUT RC
    OUT="$(mktemp)"
    set +e
    "$@" >"$OUT" 2>&1
    RC=$?
    set -e
    log "TOOL=$NAME RC=$RC"
    cat "$OUT"
    rm -f "$OUT"
    return "$RC"
}

extract_snapshot() {
    awk -F= '$1=="SNAPSHOT_COMMIT"{v=$2} $1=="MIRROR_HEAD"{v=$2} END{if(v!="")print v}'
}

receive_universal_jobs() {
    if ! is_authorized; then return 0; fi
    if [ -f "$UNIVERSAL_BRIDGE" ]; then
        if run_tool "UNIVERSAL_JOB_BRIDGE" "$PYTHON_BIN" "$UNIVERSAL_BRIDGE" receive; then
            log "UNIVERSAL_JOB_BRIDGE_STATE=READY"
        else
            log "UNIVERSAL_JOB_BRIDGE_STATE=ERROR"
        fi
    else
        log "UNIVERSAL_JOB_BRIDGE_AVAILABLE=NO"
    fi
}

dispatch_universal_jobs() {
    if ! is_authorized; then return 0; fi
    if [ -f "$UNIVERSAL_DISPATCHER" ]; then
        if run_tool "UNIVERSAL_JOB_DISPATCHER" "$PYTHON_BIN" "$UNIVERSAL_DISPATCHER"; then
            log "UNIVERSAL_JOB_DISPATCHER_STATE=READY"
        else
            log "UNIVERSAL_JOB_DISPATCHER_STATE=ERROR"
        fi
    else
        log "UNIVERSAL_JOB_DISPATCHER_AVAILABLE=NO"
    fi
}

publish_universal_results() {
    if ! is_authorized; then return 0; fi
    if [ -f "$UNIVERSAL_RESULT_PUBLISHER" ]; then
        if run_tool "UNIVERSAL_JOB_RESULT_PUBLISHER" "$PYTHON_BIN" "$UNIVERSAL_RESULT_PUBLISHER"; then
            log "UNIVERSAL_JOB_RESULT_PUBLISHER_STATE=READY"
        else
            log "UNIVERSAL_JOB_RESULT_PUBLISHER_STATE=ERROR"
        fi
    else
        log "UNIVERSAL_JOB_RESULT_PUBLISHER_AVAILABLE=NO"
    fi
}

publish_runtime_health() {
    if ! is_authorized; then return 0; fi
    if [ -f "$RUNTIME_HEALTH_PUBLISHER" ]; then
        if run_tool "RUNTIME_HEALTH_PUBLISHER" "$PYTHON_BIN" "$RUNTIME_HEALTH_PUBLISHER"; then
            log "RUNTIME_HEALTH_PUBLISHER_STATE=READY"
        else
            log "RUNTIME_HEALTH_PUBLISHER_STATE=ERROR"
        fi
    else
        log "RUNTIME_HEALTH_PUBLISHER_AVAILABLE=NO"
    fi
}

run_cycle() {
    local CHECK_OUT CHECK_RC PUBLISH_OUT PUBLISH_RC SNAPSHOT FINALIZE_RC
    if ! is_authorized; then log "STATE=DISABLED"; return 0; fi
    log "STATE=AUTHORIZED"
    CHECK_OUT="$(mktemp)"
    set +e; "$CHECK" >"$CHECK_OUT" 2>&1; CHECK_RC=$?; set -e
    log "CHECK_RC=$CHECK_RC"; cat "$CHECK_OUT"
    if [ "$CHECK_RC" -eq 90 ]; then rm -f "$CHECK_OUT"; log "STATE=DISABLED_DURING_CHECK"; return 0; fi
    if [ "$CHECK_RC" -eq 91 ] || [ "$CHECK_RC" -eq 92 ]; then rm -f "$CHECK_OUT"; log "STATE=LOCK_UNAVAILABLE"; return 0; fi
    if [ "$CHECK_RC" -ne 0 ]; then rm -f "$CHECK_OUT"; log "STATE=CHECK_ERROR"; return 0; fi
    if grep -q '^DECISION=SAFE_REMOTE_FAST_FORWARD_AVAILABLE$' "$CHECK_OUT"; then
        rm -f "$CHECK_OUT"; log "STATE=REMOTE_FAST_FORWARD_AVAILABLE"
        if run_tool "APPLY_REMOTE_UPDATE" "$APPLY"; then log "STATE=REMOTE_APPLY_COMPLETE"; else log "STATE=REMOTE_APPLY_FAILED"; fi
        return 0
    fi
    if ! grep -q '^DECISION=ALREADY_SYNCHRONIZED$' "$CHECK_OUT"; then rm -f "$CHECK_OUT"; log "STATE=UNKNOWN_CHECK_DECISION"; return 0; fi
    rm -f "$CHECK_OUT"; log "STATE=REMOTE_CONVERGED"
    if ! is_authorized; then log "STATE=DISABLED_BEFORE_LOCAL_PUBLISH"; return 0; fi
    PUBLISH_OUT="$(mktemp)"
    set +e; "$PUBLISH" --publish >"$PUBLISH_OUT" 2>&1; PUBLISH_RC=$?; set -e
    log "PUBLISH_RC=$PUBLISH_RC"; cat "$PUBLISH_OUT"
    if [ "$PUBLISH_RC" -eq 90 ]; then rm -f "$PUBLISH_OUT"; log "STATE=DISABLED_DURING_PUBLISH"; return 0; fi
    if [ "$PUBLISH_RC" -eq 91 ] || [ "$PUBLISH_RC" -eq 92 ]; then rm -f "$PUBLISH_OUT"; log "STATE=LOCK_UNAVAILABLE"; return 0; fi
    if [ "$PUBLISH_RC" -ne 0 ]; then rm -f "$PUBLISH_OUT"; log "STATE=PUBLISH_ERROR"; return 0; fi
    if grep -q '^DECISION=NO_CHANGES_TO_PUBLISH$' "$PUBLISH_OUT"; then rm -f "$PUBLISH_OUT"; log "STATE=CONVERGED_NO_LOCAL_CHANGES"; return 0; fi
    SNAPSHOT="$(extract_snapshot < "$PUBLISH_OUT")"; rm -f "$PUBLISH_OUT"
    if [ -z "$SNAPSHOT" ]; then log "STATE=SNAPSHOT_NOT_RESOLVED"; return 0; fi
    case "$SNAPSHOT" in *[!0-9a-fA-F]*) log "STATE=INVALID_SNAPSHOT_FORMAT"; return 0;; esac
    if [ "${#SNAPSHOT}" -ne 40 ]; then log "STATE=INVALID_SNAPSHOT_LENGTH"; return 0; fi
    log "STATE=MIRROR_SNAPSHOT_PUBLISHED"; log "SNAPSHOT=$SNAPSHOT"
    if ! is_authorized; then log "STATE=DISABLED_BEFORE_FINALIZE"; return 0; fi
    set +e; "$FINALIZER" "$SNAPSHOT"; FINALIZE_RC=$?; set -e
    log "FINALIZER_RC=$FINALIZE_RC"
    if [ "$FINALIZER_RC" -eq 0 ]; then log "STATE=LOCAL_REMOTE_MIRROR_CONVERGED"; return 0; fi
    if [ "$FINALIZER_RC" -eq 90 ]; then log "STATE=DISABLED_DURING_FINALIZE"; return 0; fi
    if [ "$FINALIZER_RC" -eq 91 ] || [ "$FINALIZER_RC" -eq 92 ]; then log "STATE=LOCK_UNAVAILABLE"; return 0; fi
    log "STATE=FINALIZER_ERROR"
}

run_reporting_pipeline() {
    local REPORT_OUT="" REPORT_RC=0 EXPORT_OUT="" EXPORT_RC=0
    if [ -x "$REPORTER" ]; then
        set +e; REPORT_OUT="$("$REPORTER" 2>&1)"; REPORT_RC=$?; set -e
        if [ "$REPORT_RC" -eq 0 ]; then [ -z "$REPORT_OUT" ] || printf '%s\n' "$REPORT_OUT"; else log "RESULT_REPORTER_ERROR=YES"; log "RESULT_REPORTER_RC=$REPORT_RC"; [ -z "$REPORT_OUT" ] || printf '%s\n' "$REPORT_OUT"; return 0; fi
    else log "RESULT_REPORTER_AVAILABLE=NO"; return 0; fi
    if [ -x "$AUDIT_EXPORTER" ]; then
        set +e; EXPORT_OUT="$("$AUDIT_EXPORTER" 2>&1)"; EXPORT_RC=$?; set -e
        if [ "$EXPORT_RC" -eq 0 ]; then [ -z "$EXPORT_OUT" ] || printf '%s\n' "$EXPORT_OUT"; else log "AUDIT_EXPORTER_ERROR=YES"; log "AUDIT_EXPORTER_RC=$EXPORT_RC"; [ -z "$EXPORT_OUT" ] || printf '%s\n' "$EXPORT_OUT"; fi
    else log "AUDIT_EXPORTER_AVAILABLE=NO"; fi
}

case "$LOOP_SECONDS" in ''|*[!0-9]*) echo "ABORT=INVALID_LOOP_SECONDS"; exit 2;; esac
if [ "$LOOP_SECONDS" -lt 10 ]; then echo "ABORT=LOOP_SECONDS_TOO_LOW"; exit 3; fi
log "MIRROR_WORKER_STARTED=YES"; log "RUNTIME_GENERATION=$RUNTIME_GENERATION"; log "LOOP_SECONDS=$LOOP_SECONDS"
while [ "$RUNNING" -eq 1 ]; do
    run_cycle
    receive_universal_jobs
    dispatch_universal_jobs
    publish_universal_results
    publish_runtime_health
    run_reporting_pipeline
    [ "$RUNNING" -ne 0 ] || break
    sleep "$LOOP_SECONDS" & wait $! || true
done
log "MIRROR_WORKER_STOPPED=YES"
exit 0
