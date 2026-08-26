#!/usr/bin/env bash
set -euo pipefail

ROOT="/app"
DIR="$ROOT/tools/mirror_sync"
RUNTIME_GENERATION="20260826-universal-job-worker-v1"

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

BRIDGE="$DIR/universal_job_bridge.py"
DISPATCHER="$DIR/universal_job_dispatcher.py"
RESULT_PUBLISHER="$DIR/universal_job_result_publisher.py"
HEALTH_PUBLISHER="$DIR/runtime_health_publisher.py"

STATE="$ROOT/.git/universal-worker-queue"
RUNTIME_STATE="$STATE/runtime"
PERSISTENT_STOP="$STATE/STOP"
TEMP_STOP="/tmp/edarsahub-universal-worker/STOP"
LOOP_SECONDS="${UNIVERSAL_WORKER_LOOP_SECONDS:-10}"
RUNNING=1

mkdir -p "$RUNTIME_STATE"

log() { printf '%s %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$*"; }
now_utc() { date -u +%Y-%m-%dT%H:%M:%SZ; }
shutdown_worker() { RUNNING=0; log "UNIVERSAL_WORKER_SIGNAL_RECEIVED=YES"; }
trap shutdown_worker TERM INT HUP

is_authorized() {
    [ ! -e "$PERSISTENT_STOP" ] && [ ! -e "$TEMP_STOP" ]
}

run_tool() {
    local NAME="$1" TIMEOUT_SECONDS="$2"; shift 2
    local OUT RC
    OUT="$(mktemp)"
    set +e
    if command -v timeout >/dev/null 2>&1; then
        timeout --signal=TERM --kill-after=5 "${TIMEOUT_SECONDS}s" "$@" >"$OUT" 2>&1
        RC=$?
    else
        "$@" >"$OUT" 2>&1
        RC=$?
    fi
    set -e
    log "TOOL=$NAME RC=$RC"
    cat "$OUT"
    rm -f "$OUT"
    if [ "$RC" -eq 124 ] || [ "$RC" -eq 137 ]; then
        log "TOOL=$NAME TIMEOUT=YES"
    fi
    return "$RC"
}

write_runtime_state() {
    printf '%s\n' "$$" > "$RUNTIME_STATE/pid"
    printf '%s\n' "$RUNTIME_GENERATION" > "$RUNTIME_STATE/generation"
    printf '%s\n' "$(now_utc)" > "$RUNTIME_STATE/last_cycle_utc"
}

receive_jobs() {
    [ -f "$BRIDGE" ] || { log "UNIVERSAL_JOB_BRIDGE_AVAILABLE=NO"; return 0; }
    if run_tool "UNIVERSAL_JOB_BRIDGE" 45 "$PYTHON_BIN" "$BRIDGE" receive; then
        printf '%s\n' "$(now_utc)" > "$RUNTIME_STATE/last_receive_utc"
        log "UNIVERSAL_JOB_BRIDGE_STATE=READY"
    else
        log "UNIVERSAL_JOB_BRIDGE_STATE=ERROR"
    fi
}

dispatch_jobs() {
    [ -f "$DISPATCHER" ] || { log "UNIVERSAL_JOB_DISPATCHER_AVAILABLE=NO"; return 0; }
    if run_tool "UNIVERSAL_JOB_DISPATCHER" "${UNIVERSAL_DISPATCH_TIMEOUT_SECONDS:-1900}" "$PYTHON_BIN" "$DISPATCHER"; then
        log "UNIVERSAL_JOB_DISPATCHER_STATE=READY"
    else
        log "UNIVERSAL_JOB_DISPATCHER_STATE=ERROR"
    fi
}

publish_results() {
    [ -f "$RESULT_PUBLISHER" ] || { log "UNIVERSAL_JOB_RESULT_PUBLISHER_AVAILABLE=NO"; return 0; }
    if run_tool "UNIVERSAL_JOB_RESULT_PUBLISHER" "${UNIVERSAL_RESULT_PUBLISH_TIMEOUT_SECONDS:-180}" "$PYTHON_BIN" "$RESULT_PUBLISHER"; then
        log "UNIVERSAL_JOB_RESULT_PUBLISHER_STATE=READY"
    else
        log "UNIVERSAL_JOB_RESULT_PUBLISHER_STATE=ERROR"
    fi
}

publish_health() {
    [ -f "$HEALTH_PUBLISHER" ] || { log "RUNTIME_HEALTH_PUBLISHER_AVAILABLE=NO"; return 0; }
    if run_tool "RUNTIME_HEALTH_PUBLISHER" "${UNIVERSAL_HEALTH_TIMEOUT_SECONDS:-60}" "$PYTHON_BIN" "$HEALTH_PUBLISHER"; then
        log "RUNTIME_HEALTH_PUBLISHER_STATE=READY"
    else
        log "RUNTIME_HEALTH_PUBLISHER_STATE=ERROR"
    fi
}

case "$LOOP_SECONDS" in ''|*[!0-9]*) echo "ABORT=INVALID_UNIVERSAL_LOOP_SECONDS"; exit 2;; esac
if [ "$LOOP_SECONDS" -lt 5 ]; then echo "ABORT=UNIVERSAL_LOOP_SECONDS_TOO_LOW"; exit 3; fi

log "UNIVERSAL_JOB_WORKER_STARTED=YES"
log "RUNTIME_GENERATION=$RUNTIME_GENERATION"
log "LOOP_SECONDS=$LOOP_SECONDS"

while [ "$RUNNING" -eq 1 ]; do
    write_runtime_state
    if is_authorized; then
        receive_jobs
        publish_results
        dispatch_jobs
        publish_results
        publish_health
    else
        log "STATE=DISABLED"
    fi
    [ "$RUNNING" -ne 0 ] || break
    sleep "$LOOP_SECONDS" &
    wait $! || true
done

log "UNIVERSAL_JOB_WORKER_STOPPED=YES"
exit 0
