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
EDARSAHUB_PLATFORM_MANAGED_SYSTEM_DEPS_REL=".emergent/system_deps.txt"

# Emergent owns this file at runtime and currently materializes it as empty even
# though the canonical repository keeps "git" so fresh Preview images install
# the Git executable. Treat ONLY that exact unstaged drift as platform-managed.
# Any other content, staging, deletion, or path remains a hard blocker.
edarsahub_expected_platform_system_deps_drift() {
    local canonical current_path
    current_path="$EDARSAHUB_APP/$EDARSAHUB_PLATFORM_MANAGED_SYSTEM_DEPS_REL"

    [ -f "$current_path" ] || return 1
    [ ! -s "$current_path" ] || return 1

    canonical="$(git -C "$EDARSAHUB_APP" show "HEAD:$EDARSAHUB_PLATFORM_MANAGED_SYSTEM_DEPS_REL" 2>/dev/null || true)"
    [ "$canonical" = "git" ] || return 1

    git -C "$EDARSAHUB_APP" diff --cached --quiet -- "$EDARSAHUB_PLATFORM_MANAGED_SYSTEM_DEPS_REL" || return 1
    git -C "$EDARSAHUB_APP" diff --quiet -- "$EDARSAHUB_PLATFORM_MANAGED_SYSTEM_DEPS_REL" && return 1

    return 0
}

edarsahub_effective_status() {
    local raw
    raw="$(git -C "$EDARSAHUB_APP" status --porcelain=v1 --untracked-files=all)"
    if edarsahub_expected_platform_system_deps_drift; then
        printf '%s\n' "$raw" | grep -v '^ M \.emergent/system_deps\.txt
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
    [ -n "$(edarsahub_effective_status)" ]
}

edarsahub_require_clean_shared_app() {
    local staged unstaged untracked
    staged="$(git -C "$EDARSAHUB_APP" diff --cached --name-only | wc -l)"
    unstaged="$(edarsahub_effective_unstaged_names | sed '/^$/d' | wc -l)"
    untracked="$(git -C "$EDARSAHUB_APP" status --porcelain=v1 --untracked-files=all | grep '^?? ' | wc -l)"
    echo "STAGED_COUNT=$staged"; echo "UNSTAGED_COUNT=$unstaged"; echo "UNTRACKED_COUNT=$untracked"
    if edarsahub_expected_platform_system_deps_drift; then echo "PLATFORM_MANAGED_SYSTEM_DEPS_DRIFT=IGNORED_EXPECTED_EMPTY_RUNTIME"; fi
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
 || true
    else
        printf '%s\n' "$raw"
    fi
}

edarsahub_effective_unstaged_names() {
    local raw
    raw="$(git -C "$EDARSAHUB_APP" diff --name-only)"
    if edarsahub_expected_platform_system_deps_drift; then
        printf '%s\n' "$raw" | grep -v '^\.emergent/system_deps\.txt
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
 || true
    else
        printf '%s\n' "$raw"
    fi
}

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
