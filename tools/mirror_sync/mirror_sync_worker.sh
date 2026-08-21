#!/usr/bin/env bash
set -euo pipefail

ROOT="/app"
DIR="$ROOT/tools/mirror_sync"

CHECK="$DIR/check_remote_update.sh"
APPLY="$DIR/apply_remote_update.sh"
PUBLISH="$DIR/publish_local_snapshot.sh"
FINALIZER="$DIR/finalize_local_snapshot.sh"
STATUS="$DIR/mirror_sync_status.sh"
REPORTER="$DIR/mirror_sync_result_reporter.py"

STATE_DIR="$ROOT/.git/mirror-sync"
ENABLE_FLAG="$STATE_DIR/ENABLED"
PERSISTENT_STOP="$STATE_DIR/STOP"
TEMP_STOP="/tmp/edarsahub-mirror-sync/STOP"

LOOP_SECONDS="${MIRROR_SYNC_LOOP_SECONDS:-60}"

RUNNING=1

log() {
    printf '%s %s\n' \
        "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
        "$*"
}

shutdown_worker() {
    RUNNING=0
    log "WORKER_SIGNAL_RECEIVED=YES"
}

trap shutdown_worker TERM INT

is_authorized() {
    if [ -e "$PERSISTENT_STOP" ]; then
        return 1
    fi

    if [ -e "$TEMP_STOP" ]; then
        return 1
    fi

    if [ ! -e "$ENABLE_FLAG" ]; then
        return 1
    fi

    return 0
}

run_tool() {
    local NAME="$1"
    shift

    local OUT
    local RC

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
    awk -F= '
        $1 == "SNAPSHOT_COMMIT" {
            value=$2
        }
        $1 == "MIRROR_HEAD" {
            value=$2
        }
        END {
            if (value != "") {
                print value
            }
        }
    '
}

run_cycle() {
    local CHECK_OUT
    local CHECK_RC
    local PUBLISH_OUT
    local PUBLISH_RC
    local SNAPSHOT
    local FINALIZE_RC

    if ! is_authorized; then
        log "STATE=DISABLED"
        return 0
    fi

    log "STATE=AUTHORIZED"

    CHECK_OUT="$(mktemp)"

    set +e
    "$CHECK" >"$CHECK_OUT" 2>&1
    CHECK_RC=$?
    set -e

    log "CHECK_RC=$CHECK_RC"
    cat "$CHECK_OUT"

    if [ "$CHECK_RC" -eq 90 ]; then
        rm -f "$CHECK_OUT"
        log "STATE=DISABLED_DURING_CHECK"
        return 0
    fi

    if [ "$CHECK_RC" -eq 91 ] || [ "$CHECK_RC" -eq 92 ]; then
        rm -f "$CHECK_OUT"
        log "STATE=LOCK_UNAVAILABLE"
        return 0
    fi

    if [ "$CHECK_RC" -ne 0 ]; then
        rm -f "$CHECK_OUT"
        log "STATE=CHECK_ERROR"
        return 0
    fi

    if grep -q '^DECISION=SAFE_REMOTE_FAST_FORWARD_AVAILABLE$' "$CHECK_OUT"; then
        rm -f "$CHECK_OUT"

        log "STATE=REMOTE_FAST_FORWARD_AVAILABLE"

        if run_tool "APPLY_REMOTE_UPDATE" "$APPLY"; then
            log "STATE=REMOTE_APPLY_COMPLETE"
        else
            log "STATE=REMOTE_APPLY_FAILED"
        fi

        return 0
    fi

    if ! grep -q '^DECISION=ALREADY_SYNCHRONIZED$' "$CHECK_OUT"; then
        rm -f "$CHECK_OUT"
        log "STATE=UNKNOWN_CHECK_DECISION"
        return 0
    fi

    rm -f "$CHECK_OUT"

    log "STATE=REMOTE_CONVERGED"

    if ! is_authorized; then
        log "STATE=DISABLED_BEFORE_LOCAL_PUBLISH"
        return 0
    fi

    PUBLISH_OUT="$(mktemp)"

    set +e
    "$PUBLISH" --publish >"$PUBLISH_OUT" 2>&1
    PUBLISH_RC=$?
    set -e

    log "PUBLISH_RC=$PUBLISH_RC"
    cat "$PUBLISH_OUT"

    if [ "$PUBLISH_RC" -eq 90 ]; then
        rm -f "$PUBLISH_OUT"
        log "STATE=DISABLED_DURING_PUBLISH"
        return 0
    fi

    if [ "$PUBLISH_RC" -eq 91 ] || [ "$PUBLISH_RC" -eq 92 ]; then
        rm -f "$PUBLISH_OUT"
        log "STATE=LOCK_UNAVAILABLE"
        return 0
    fi

    if [ "$PUBLISH_RC" -ne 0 ]; then
        rm -f "$PUBLISH_OUT"
        log "STATE=PUBLISH_ERROR"
        return 0
    fi

    if grep -q '^DECISION=NO_CHANGES_TO_PUBLISH$' "$PUBLISH_OUT"; then
        rm -f "$PUBLISH_OUT"
        log "STATE=CONVERGED_NO_LOCAL_CHANGES"
        return 0
    fi

    SNAPSHOT="$(
        extract_snapshot < "$PUBLISH_OUT"
    )"

    rm -f "$PUBLISH_OUT"

    if [ -z "$SNAPSHOT" ]; then
        log "STATE=SNAPSHOT_NOT_RESOLVED"
        return 0
    fi

    case "$SNAPSHOT" in
        *[!0-9a-fA-F]*)
            log "STATE=INVALID_SNAPSHOT_FORMAT"
            return 0
            ;;
    esac

    if [ "${#SNAPSHOT}" -ne 40 ]; then
        log "STATE=INVALID_SNAPSHOT_LENGTH"
        return 0
    fi

    log "STATE=MIRROR_SNAPSHOT_PUBLISHED"
    log "SNAPSHOT=$SNAPSHOT"

    if ! is_authorized; then
        log "STATE=DISABLED_BEFORE_FINALIZE"
        return 0
    fi

    set +e
    "$FINALIZER" "$SNAPSHOT"
    FINALIZE_RC=$?
    set -e

    log "FINALIZER_RC=$FINALIZE_RC"

    if [ "$FINALIZE_RC" -eq 0 ]; then
        log "STATE=LOCAL_REMOTE_MIRROR_CONVERGED"
        return 0
    fi

    if [ "$FINALIZE_RC" -eq 90 ]; then
        log "STATE=DISABLED_DURING_FINALIZE"
        return 0
    fi

    if [ "$FINALIZE_RC" -eq 91 ] || [ "$FINALIZE_RC" -eq 92 ]; then
        log "STATE=LOCK_UNAVAILABLE"
        return 0
    fi

    log "STATE=FINALIZER_ERROR"
    return 0
}

case "$LOOP_SECONDS" in
    ''|*[!0-9]*)
        echo "ABORT=INVALID_LOOP_SECONDS"
        exit 2
        ;;
esac

if [ "$LOOP_SECONDS" -lt 10 ]; then
    echo "ABORT=LOOP_SECONDS_TOO_LOW"
    exit 3
fi

log "MIRROR_WORKER_STARTED=YES"
log "LOOP_SECONDS=$LOOP_SECONDS"

while [ "$RUNNING" -eq 1 ]; do
    run_cycle

    if [ -x "$REPORTER" ]; then
        set +e
        REPORT_OUT="$("$REPORTER" 2>&1)"
        REPORT_RC=$?
        set -e

        if [ "$REPORT_RC" -eq 0 ]; then
            if [ -n "$REPORT_OUT" ]; then
                printf '%s\n' "$REPORT_OUT"
            fi
        else
            log "RESULT_REPORTER_ERROR=YES"
            log "RESULT_REPORTER_RC=$REPORT_RC"
            if [ -n "$REPORT_OUT" ]; then
                printf '%s\n' "$REPORT_OUT"
            fi
        fi
    else
        log "RESULT_REPORTER_AVAILABLE=NO"
    fi

    if [ "$RUNNING" -eq 0 ]; then
        break
    fi

    sleep "$LOOP_SECONDS" &
    wait $! || true
done

log "MIRROR_WORKER_STOPPED=YES"
exit 0
