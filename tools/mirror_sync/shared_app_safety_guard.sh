#!/usr/bin/env bash

# EDARSAHUB shared /app safety contract.
#
# Rules:
# - Never discard, stash, reset, restore, checkout or clean local /app work.
# - A dirty /app is a hard blocker for automated synchronization/publication.
#   No staged, unstaged or untracked state may be discarded or auto-stashed.
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
    local staged unstaged untracked
    staged="$(git -C "$EDARSAHUB_APP" diff --cached --name-only | wc -l)"
    unstaged="$(git -C "$EDARSAHUB_APP" diff --name-only | wc -l)"
    untracked="$(git -C "$EDARSAHUB_APP" status --porcelain=v1 --untracked-files=all | grep '^?? ' | wc -l)"
    echo "STAGED_COUNT=$staged"; echo "UNSTAGED_COUNT=$unstaged"; echo "UNTRACKED_COUNT=$untracked"
    if [ "$staged" -ne 0 ] || [ "$unstaged" -ne 0 ] || [ "$untracked" -ne 0 ]; then echo "DECISION=GIT_WORKTREE_NOT_CLEAN"; echo "LOCAL_WORK_PRESERVATION_REQUIRED=YES"; echo "WRITE_OPERATION_EXECUTED=NO"; return 74; fi
    echo "DECISION=LOCAL_APP_CLEAN"; return 0
}

edarsahub_git_guard_python() {
    if [ -x /root/.venv/bin/python ]; then printf '%s\n' /root/.venv/bin/python; elif [ -x "$EDARSAHUB_APP/.venv/bin/python" ]; then printf '%s\n' "$EDARSAHUB_APP/.venv/bin/python"; else command -v python3; fi
}
edarsahub_acquire_git_writer_lock() { local job_id="$1" owner="$2" py; py="$(edarsahub_git_guard_python)" || return 75; "$py" "$EDARSAHUB_APP/tools/mirror_sync/git_divergence_guard.py" acquire-lock --repo "$EDARSAHUB_APP" --job-id "$job_id" --owner "$owner" --owner-pid "$$"; }
edarsahub_release_git_writer_lock() { local job_id="$1" owner="$2" py; py="$(edarsahub_git_guard_python)" || return 75; "$py" "$EDARSAHUB_APP/tools/mirror_sync/git_divergence_guard.py" release-lock --repo "$EDARSAHUB_APP" --job-id "$job_id" --owner "$owner"; }

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
