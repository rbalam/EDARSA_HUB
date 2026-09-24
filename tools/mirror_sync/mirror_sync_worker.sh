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
DEV_BRANCH="Edarsahub_Desarrollo"
RUNTIME_GENERATION="20260903-preview-backend-reload-v2"

resolve_worker_python() {
    if [ -x "/root/.venv/bin/python" ]; then
        printf '%s\n' "/root/.venv/bin/python"
        return 0
    fi
    if [ -x "$ROOT/.venv/bin/python" ]; then
        printf '%s\n' "$ROOT/.venv/bin/python"
        return 0
    fi
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

STATE_DIR="$ROOT/.git/mirror-sync"
PREVIEW_BACKEND_TREE_STATE="$STATE_DIR/preview_backend_tree_sha"
PREVIEW_BACKEND_RELOAD_ATTEMPT="$STATE_DIR/preview_backend_reload_attempt_epoch"
ENABLE_FLAG="$STATE_DIR/ENABLED"
PERSISTENT_STOP="$STATE_DIR/STOP"
TEMP_STOP="/tmp/edarsahub-mirror-sync/STOP"
UNIVERSAL_STATE="$ROOT/.git/universal-worker-queue/runtime"
LOOP_SECONDS="${MIRROR_SYNC_LOOP_SECONDS:-10}"
MIRROR_TOOL_TIMEOUT_SECONDS="${MIRROR_TOOL_TIMEOUT_SECONDS:-120}"
MIRROR_APPLY_TIMEOUT_SECONDS="${MIRROR_APPLY_TIMEOUT_SECONDS:-180}"
MIRROR_FINALIZE_TIMEOUT_SECONDS="${MIRROR_FINALIZE_TIMEOUT_SECONDS:-180}"
REPORTING_TIMEOUT_SECONDS="${MIRROR_REPORTING_TIMEOUT_SECONDS:-90}"
RUNNING=1
UNIVERSAL_PID=""

log(){ printf '%s %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$*"; }
shutdown_worker(){ RUNNING=0; log "WORKER_SIGNAL_RECEIVED=YES"; }
trap shutdown_worker TERM INT HUP
is_authorized(){ [ ! -e "$PERSISTENT_STOP" ] && [ ! -e "$TEMP_STOP" ] && [ -e "$ENABLE_FLAG" ]; }

maybe_reload_preview_backend(){
    local branch env_name backend_tree previous_tree now last_attempt status_out tmp_file

    branch="$(git -C "$ROOT" branch --show-current 2>/dev/null || true)"
    if [ "$branch" != "$DEV_BRANCH" ]; then
        log "PREVIEW_BACKEND_RELOAD=SKIP_BRANCH"
        return 0
    fi

    env_name="$(printf '%s' "${EDARSA_ENV:-${APP_ENV:-${ENVIRONMENT:-PREVIEW}}}" | tr '[:lower:]' '[:upper:]')"
    case "$env_name" in
        *PROD*)
            log "PREVIEW_BACKEND_RELOAD=BLOCKED_PRODUCTION_ENV"
            log "PRODUCTION_TOUCHED=NO"
            return 0
            ;;
    esac

    backend_tree="$(git -C "$ROOT" rev-parse HEAD:backend 2>/dev/null || true)"
    [ -n "$backend_tree" ] || { log "PREVIEW_BACKEND_RELOAD=BACKEND_TREE_UNAVAILABLE"; return 0; }

    previous_tree="$(cat "$PREVIEW_BACKEND_TREE_STATE" 2>/dev/null || true)"
    if [ "$previous_tree" = "$backend_tree" ]; then
        log "PREVIEW_BACKEND_RUNTIME=CURRENT"
        return 0
    fi

    now="$(date +%s)"
    last_attempt="$(cat "$PREVIEW_BACKEND_RELOAD_ATTEMPT" 2>/dev/null || echo 0)"
    case "$last_attempt" in ''|*[!0-9]*) last_attempt=0;; esac
    if [ $((now - last_attempt)) -lt 300 ]; then
        log "PREVIEW_BACKEND_RELOAD=COOLDOWN"
        return 0
    fi

    mkdir -p "$STATE_DIR"
    printf '%s\n' "$now" > "$PREVIEW_BACKEND_RELOAD_ATTEMPT"
    log "PREVIEW_BACKEND_RELOAD_REQUIRED=YES"
    log "PREVIEW_BACKEND_TREE=$backend_tree"

    if ! supervisorctl restart backend > /tmp/edarsahub-preview-backend-restart.log 2>&1; then
        cat /tmp/edarsahub-preview-backend-restart.log || true
        log "PREVIEW_BACKEND_RELOAD=FAILED"
        log "PRODUCTION_TOUCHED=NO"
        return 0
    fi
    cat /tmp/edarsahub-preview-backend-restart.log || true
    sleep 4

    status_out="$(supervisorctl status backend 2>&1 || true)"
    printf '%s\n' "$status_out"
    case "$status_out" in
        *RUNNING*|*STARTING*) ;;
        *)
            log "PREVIEW_BACKEND_RELOAD=STATUS_NOT_HEALTHY"
            log "PRODUCTION_TOUCHED=NO"
            return 0
            ;;
    esac

    tmp_file="$PREVIEW_BACKEND_TREE_STATE.tmp.$$"
    printf '%s\n' "$backend_tree" > "$tmp_file"
    mv -f "$tmp_file" "$PREVIEW_BACKEND_TREE_STATE"
    log "PREVIEW_BACKEND_RELOAD_COMPLETE=YES"
    log "PRODUCTION_TOUCHED=NO"
}

run_tool(){
    local NAME="$1" TIMEOUT_SECONDS="$2"; shift 2
    local OUT RC; OUT="$(mktemp)"; set +e
    if command -v timeout >/dev/null 2>&1; then timeout --signal=TERM --kill-after=5 "${TIMEOUT_SECONDS}s" "$@" >"$OUT" 2>&1; RC=$?; else "$@" >"$OUT" 2>&1; RC=$?; fi
    set -e; log "TOOL=$NAME RC=$RC"; cat "$OUT"; rm -f "$OUT"
    if [ "$RC" -eq 124 ] || [ "$RC" -eq 137 ]; then log "TOOL=$NAME TIMEOUT=YES"; fi
    return "$RC"
}

extract_snapshot(){ awk -F= '$1=="SNAPSHOT_COMMIT"{v=$2} $1=="MIRROR_HEAD"{v=$2} END{if(v!="")print v}'; }

canonical_universal_worker_pid(){
    local pid=""
    [ -r "$UNIVERSAL_STATE/pid" ] || return 1
    pid="$(cat "$UNIVERSAL_STATE/pid" 2>/dev/null || true)"
    case "$pid" in
        ''|*[!0-9]*) return 1 ;;
    esac
    kill -0 "$pid" 2>/dev/null || return 1
    ps -o args= -p "$pid" 2>/dev/null | grep -Fq 'bash /app/tools/mirror_sync/universal_job_worker.sh' || return 1
    printf '%s\n' "$pid"
}

start_universal_worker(){
    local existing=""
    existing="$(canonical_universal_worker_pid 2>/dev/null || true)"
    if [ -n "$existing" ]; then
        UNIVERSAL_PID=""
        log "UNIVERSAL_JOB_WORKER_OWNERSHIP=EXTERNAL"
        log "UNIVERSAL_JOB_WORKER_PID=$existing"
        return 0
    fi

    log "UNIVERSAL_JOB_WORKER_OWNERSHIP=ABSENT"
    log "UNIVERSAL_JOB_WORKER_START_BY_MIRROR=FORBIDDEN"
    return 1
}

stop_child(){ local PID="${1:-}"; [ -n "$PID" ] || return 0; if kill -0 "$PID" 2>/dev/null; then kill -TERM "$PID" 2>/dev/null || true; for _ in $(seq 1 20); do kill -0 "$PID" 2>/dev/null || break; sleep 0.25; done; kill -KILL "$PID" 2>/dev/null || true; wait "$PID" 2>/dev/null || true; fi; }
stop_universal_worker(){ stop_child "$UNIVERSAL_PID"; UNIVERSAL_PID=""; }

ensure_universal_worker(){
    local existing=""
    existing="$(canonical_universal_worker_pid 2>/dev/null || true)"
    if [ -n "$existing" ]; then
        log "UNIVERSAL_JOB_WORKER_OWNERSHIP=EXTERNAL"
        log "UNIVERSAL_JOB_WORKER_PID=$existing"
        return 0
    fi
    log "UNIVERSAL_JOB_WORKER_NOT_RUNNING=YES"
    log "UNIVERSAL_JOB_WORKER_START_BY_MIRROR=FORBIDDEN"
    return 0
}

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
maybe_reload_preview_backend
start_universal_worker || true
while [ "$RUNNING" -eq 1 ]; do ensure_universal_worker; run_cycle; maybe_reload_preview_backend; ensure_universal_worker; run_reporting_pipeline; [ "$RUNNING" -ne 0 ] || break; sleep "$LOOP_SECONDS" & wait $! || true; done
stop_universal_worker; log "MIRROR_WORKER_STOPPED=YES"; exit 0
