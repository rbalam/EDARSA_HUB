#!/usr/bin/env bash

# EDARSAHUB shared /app safety contract.
#
# Rules:
# - Never mutate /app when dirty.
# - Never stash/reset/checkout/restore/clean /app.
# - Kill switch always wins.
# - Worker execution must happen outside /app.

EDARSAHUB_APP="${EDARSAHUB_APP:-/app}"
EDARSAHUB_SYNC_PAUSE_FILE="${EDARSAHUB_SYNC_PAUSE_FILE:-$EDARSAHUB_APP/.git/EDARSAHUB_SYNC_PAUSED}"

edarsahub_sync_is_paused() {
    [ "${EDARSAHUB_SYNC_PAUSED:-0}" = "1" ] ||
    [ -e "$EDARSAHUB_SYNC_PAUSE_FILE" ]
}

edarsahub_require_sync_enabled() {
    if edarsahub_sync_is_paused; then
        echo "DECISION=SYNC_PAUSED"
        echo "WRITE_OPERATION_EXECUTED=NO"
        return 70
    fi
}

edarsahub_shared_app_is_dirty() {
    [ -n "$(git -C "$EDARSAHUB_APP" status --porcelain=v1 --untracked-files=all)" ]
}

edarsahub_require_clean_shared_app() {
    if edarsahub_shared_app_is_dirty; then
        echo "DECISION=DEFERRED_LOCAL_DIRTY"
        echo "LOCAL_FAST_FORWARD_EXECUTED=NO"
        echo "WRITE_OPERATION_EXECUTED=NO"
        return 71
    fi
}

edarsahub_require_worker_isolation() {
    case "$(pwd -P)" in
        "$EDARSAHUB_APP")
            echo "ABORT=WORKER_SHARED_APP_MUTATION_PROHIBITED"
            return 72
            ;;
        "$EDARSAHUB_APP/.agent-worktrees/"*)
            return 0
            ;;
        /tmp/edarsahub-worker-jobs/*)
            return 0
            ;;
        *)
            echo "ABORT=WORKER_EXECUTION_LOCATION_NOT_ALLOWLISTED"
            return 73
            ;;
    esac
}
