#!/usr/bin/env bash
set -euo pipefail

ROOT="/app"
DIR="$ROOT/tools/mirror_sync"
RUNTIME_GENERATION="20260827-universal-job-worker-sla-v2"

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
INTAKE_SECONDS="${UNIVERSAL_WORKER_INTAKE_SECONDS:-10}"
RESULT_SECONDS="${UNIVERSAL_WORKER_RESULT_SECONDS:-10}"
HEALTH_SECONDS="${UNIVERSAL_WORKER_HEALTH_SECONDS:-30}"
DISPATCH_IDLE_SECONDS="${UNIVERSAL_WORKER_DISPATCH_IDLE_SECONDS:-2}"
RUNNING=1
CHILD_PIDS=()

mkdir -p "$RUNTIME_STATE"

log() { printf '%s %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$*"; }
now_utc() { date -u +%Y-%m-%dT%H:%M:%SZ; }

shutdown_worker() {
    RUNNING=0
    log "UNIVERSAL_WORKER_SIGNAL_RECEIVED=YES"
    local pid
    for pid in "${CHILD_PIDS[@]:-}"; do
        [ -n "$pid" ] || continue
        kill "$pid" 2>/dev/null || true
    done
}
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

write_runtime_identity() {
    printf '%s\n' "$$" > "$RUNTIME_STATE/pid"
    printf '%s\n' "$RUNTIME_GENERATION" > "$RUNTIME_STATE/generation"
}

receive_once() {
    [ -f "$BRIDGE" ] || { log "UNIVERSAL_JOB_BRIDGE_AVAILABLE=NO"; return 0; }
    if run_tool "UNIVERSAL_JOB_BRIDGE" 45 "$PYTHON_BIN" "$BRIDGE" receive; then
        printf '%s\n' "$(now_utc)" > "$RUNTIME_STATE/last_receive_utc"
        log "UNIVERSAL_JOB_BRIDGE_STATE=READY"
    else
        log "UNIVERSAL_JOB_BRIDGE_STATE=ERROR"
    fi
}

dispatch_once() {
    [ -f "$DISPATCHER" ] || { log "UNIVERSAL_JOB_DISPATCHER_AVAILABLE=NO"; return 0; }
    if run_tool "UNIVERSAL_JOB_DISPATCHER" "${UNIVERSAL_DISPATCH_TIMEOUT_SECONDS:-1900}" "$PYTHON_BIN" "$DISPATCHER"; then
        log "UNIVERSAL_JOB_DISPATCHER_STATE=READY"
    else
        log "UNIVERSAL_JOB_DISPATCHER_STATE=ERROR"
    fi
}

publish_results_once() {
    [ -f "$RESULT_PUBLISHER" ] || { log "UNIVERSAL_JOB_RESULT_PUBLISHER_AVAILABLE=NO"; return 0; }
    if run_tool "UNIVERSAL_JOB_RESULT_PUBLISHER" "${UNIVERSAL_RESULT_PUBLISH_TIMEOUT_SECONDS:-180}" "$PYTHON_BIN" "$RESULT_PUBLISHER"; then
        log "UNIVERSAL_JOB_RESULT_PUBLISHER_STATE=READY"
    else
        log "UNIVERSAL_JOB_RESULT_PUBLISHER_STATE=ERROR"
    fi
}

publish_health_once() {
    [ -f "$HEALTH_PUBLISHER" ] || { log "RUNTIME_HEALTH_PUBLISHER_AVAILABLE=NO"; return 0; }
    if run_tool "RUNTIME_HEALTH_PUBLISHER" "${UNIVERSAL_HEALTH_TIMEOUT_SECONDS:-60}" "$PYTHON_BIN" "$HEALTH_PUBLISHER"; then
        log "RUNTIME_HEALTH_PUBLISHER_STATE=READY"
    else
        log "RUNTIME_HEALTH_PUBLISHER_STATE=ERROR"
    fi
}

validate_interval() {
    local name="$1" value="$2" minimum="$3"
    case "$value" in ''|*[!0-9]*) echo "ABORT=INVALID_${name}"; exit 2;; esac
    if [ "$value" -lt "$minimum" ]; then echo "ABORT=${name}_TOO_LOW"; exit 3; fi
}

intake_loop() {
    while [ "$RUNNING" -eq 1 ]; do
        printf '%s\n' "$(now_utc)" > "$RUNTIME_STATE/last_cycle_utc"
        if is_authorized; then receive_once; else log "INTAKE_STATE=DISABLED"; fi
        sleep "$INTAKE_SECONDS" || true
    done
}

result_loop() {
    while [ "$RUNNING" -eq 1 ]; do
        if is_authorized; then publish_results_once; else log "RESULT_STATE=DISABLED"; fi
        sleep "$RESULT_SECONDS" || true
    done
}

health_loop() {
    while [ "$RUNNING" -eq 1 ]; do
        if is_authorized; then publish_health_once; else log "HEALTH_STATE=DISABLED"; fi
        sleep "$HEALTH_SECONDS" || true
    done
}

dispatch_loop() {
    while [ "$RUNNING" -eq 1 ]; do
        if is_authorized; then dispatch_once; else log "DISPATCH_STATE=DISABLED"; fi
        sleep "$DISPATCH_IDLE_SECONDS" || true
    done
}

validate_interval "UNIVERSAL_WORKER_INTAKE_SECONDS" "$INTAKE_SECONDS" 5
validate_interval "UNIVERSAL_WORKER_RESULT_SECONDS" "$RESULT_SECONDS" 5
validate_interval "UNIVERSAL_WORKER_HEALTH_SECONDS" "$HEALTH_SECONDS" 10
validate_interval "UNIVERSAL_WORKER_DISPATCH_IDLE_SECONDS" "$DISPATCH_IDLE_SECONDS" 1

write_runtime_identity
log "UNIVERSAL_JOB_WORKER_STARTED=YES"
log "RUNTIME_GENERATION=$RUNTIME_GENERATION"
log "INTAKE_SECONDS=$INTAKE_SECONDS RESULT_SECONDS=$RESULT_SECONDS HEALTH_SECONDS=$HEALTH_SECONDS"

intake_loop & CHILD_PIDS+=("$!")
result_loop & CHILD_PIDS+=("$!")
health_loop & CHILD_PIDS+=("$!")
dispatch_loop & CHILD_PIDS+=("$!")

set +e
while [ "$RUNNING" -eq 1 ]; do
    sleep 1
    for pid in "${CHILD_PIDS[@]}"; do
        if ! kill -0 "$pid" 2>/dev/null; then
            log "CHILD_LOOP_EXITED_UNEXPECTEDLY=$pid"
            RUNNING=0
            break
        fi
    done
done
set -e
shutdown_worker
wait "${CHILD_PIDS[@]}" 2>/dev/null || true
log "UNIVERSAL_JOB_WORKER_STOPPED=YES"
exit 0
