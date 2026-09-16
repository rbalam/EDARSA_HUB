#!/usr/bin/env bash
set -euo pipefail

SAFETY_GUARD="/app/tools/mirror_sync/shared_app_safety_guard.sh"
test -r "$SAFETY_GUARD" || {
    echo "ABORT=SHARED_APP_SAFETY_GUARD_MISSING"
    exit 90
}
. "$SAFETY_GUARD"
edarsahub_require_sync_enabled || exit $?
# Compatibility observation only. Dirty state is not a blanket blocker;
# collision checks below are authoritative.
edarsahub_require_clean_shared_app || exit $?

MIRROR_SYNC_GUARD="/app/tools/mirror_sync/mirror_sync_guard.sh"
test -r "$MIRROR_SYNC_GUARD" || {
    echo "ABORT=MIRROR_SYNC_GUARD_MISSING"
    echo "WRITE_OPERATION_EXECUTED=NO"
    exit 90
}
. "$MIRROR_SYNC_GUARD"
mirror_sync_require_enabled || exit $?
mirror_sync_acquire_global_lock || exit $?

ROOT="/app"
DEV_BRANCH="Edarsahub_Desarrollo"
MIRROR_BRANCH="mirror/emergent-live"
cd "$ROOT"

echo "===== EDARSAHUB SAFE REMOTE UPDATE APPLY ====="
BRANCH="$(git branch --show-current)"
LOCAL_BEFORE="$(git rev-parse HEAD)"
echo "LOCAL_BRANCH=$BRANCH"
echo "LOCAL_BEFORE=$LOCAL_BEFORE"
test "$BRANCH" = "$DEV_BRANCH" || { echo "ABORT=WRONG_BRANCH"; exit 10; }

echo
echo "===== 1. FETCH ====="
git fetch origin "$DEV_BRANCH" "$MIRROR_BRANCH"
REMOTE_DEV="$(git rev-parse origin/$DEV_BRANCH)"
REMOTE_MIRROR="$(git rev-parse origin/$MIRROR_BRANCH)"
echo "REMOTE_DEV=$REMOTE_DEV"
echo "REMOTE_MIRROR=$REMOTE_MIRROR"
TARGET="$REMOTE_DEV"

if [ "$LOCAL_BEFORE" = "$TARGET" ] && [ "$REMOTE_MIRROR" = "$TARGET" ]; then
    echo "DECISION=ALREADY_SYNCHRONIZED"
    echo "WRITE_OPERATION_EXECUTED=NO"
    echo "PRODUCTION_TOUCHED=NO"
    exit 0
fi

git merge-base --is-ancestor "$LOCAL_BEFORE" "$TARGET" || {
    echo "ABORT=TARGET_NOT_FAST_FORWARD"
    echo "WRITE_OPERATION_EXECUTED=NO"
    exit 31
}

MIRROR_FAST_FORWARD_REQUIRED=NO
if [ "$REMOTE_MIRROR" != "$TARGET" ]; then
    git merge-base --is-ancestor "$REMOTE_MIRROR" "$TARGET" || {
        echo "ABORT=DEV_MIRROR_TRUE_DIVERGENCE"
        echo "WRITE_OPERATION_EXECUTED=NO"
        exit 30
    }
    MIRROR_FAST_FORWARD_REQUIRED=YES
fi
echo "MIRROR_FAST_FORWARD_REQUIRED=$MIRROR_FAST_FORWARD_REQUIRED"

echo
echo "===== 2. INCOMING PAYLOAD ====="
INCOMING_FILE_LIST="$(mktemp)"
trap 'rm -f "$INCOMING_FILE_LIST"' EXIT
git diff --name-only "$LOCAL_BEFORE" "$TARGET" | sort -u > "$INCOMING_FILE_LIST"
git diff --name-status "$LOCAL_BEFORE" "$TARGET"
INCOMING_COUNT="$(wc -l < "$INCOMING_FILE_LIST")"
INCOMING_RUNTIME_CHANGED="NO"
if grep -Eq '^tools/mirror_sync/(mirror_sync_worker\.sh|mirror_sync_supervisor_entrypoint\.sh|shared_app_safety_guard\.sh|universal_job_bridge\.py|universal_job_dispatcher\.py|universal_job_result_publisher\.py|runtime_health_publisher\.py|apply_remote_update\.sh)$' "$INCOMING_FILE_LIST"; then
    INCOMING_RUNTIME_CHANGED="YES"
fi
echo "INCOMING_FILES=$INCOMING_COUNT"
echo "INCOMING_RUNTIME_CHANGED=$INCOMING_RUNTIME_CHANGED"

echo
echo "===== 3. LOCAL STATE SNAPSHOT ====="
TS="$(date -u +%Y%m%dT%H%M%SZ)"
STATE_DIR="/tmp/edarsahub-agents/mirror-sync/$TS"
mkdir -p "$STATE_DIR"
STAGED_PATCH_BEFORE="$STATE_DIR/staged_before.patch"
STAGED_PATCH_AFTER="$STATE_DIR/staged_after.patch"
UNSTAGED_PATCH_BEFORE="$STATE_DIR/unstaged_before.patch"
UNSTAGED_PATCH_AFTER="$STATE_DIR/unstaged_after.patch"
UNTRACKED_BEFORE="$STATE_DIR/untracked_before.txt"
UNTRACKED_AFTER="$STATE_DIR/untracked_after.txt"

git diff --cached --binary -- > "$STAGED_PATCH_BEFORE"
git diff --binary -- > "$UNSTAGED_PATCH_BEFORE"
git status --porcelain=v1 --untracked-files=all | grep '^?? ' | sed 's/^?? //' | sort > "$UNTRACKED_BEFORE" || true
STAGED="$(git diff --cached --name-only | wc -l)"
TRACKED="$(git diff --name-only | wc -l)"
UNTRACKED="$(wc -l < "$UNTRACKED_BEFORE")"
echo "STAGED_COUNT=$STAGED"
echo "TRACKED_MODIFIED_COUNT=$TRACKED"
echo "UNTRACKED_COUNT=$UNTRACKED"

echo
echo "===== 4. COLLISION AUDIT ====="
TRACKED_COLLISION=0
while IFS= read -r FILE; do
    [ -n "$FILE" ] || continue
    if git diff --cached --name-only -- | grep -Fxq -- "$FILE"; then
        echo "STAGED_COLLISION=$FILE"
        TRACKED_COLLISION=1
    fi
    if git diff --name-only -- | grep -Fxq -- "$FILE"; then
        echo "UNSTAGED_COLLISION=$FILE"
        TRACKED_COLLISION=1
    fi
done < "$INCOMING_FILE_LIST"
if [ "$TRACKED_COLLISION" -ne 0 ]; then
    echo "ABORT=LOCAL_TRACKED_COLLISION"
    echo "WRITE_OPERATION_EXECUTED=NO"
    exit 20
fi
echo "STAGED_COLLISIONS=NONE"
echo "UNSTAGED_COLLISIONS=NONE"

UNTRACKED_COLLISION=0
while IFS= read -r FILE; do
    [ -n "$FILE" ] || continue
    if git cat-file -e "$LOCAL_BEFORE:$FILE" 2>/dev/null; then
        continue
    fi
    if [ -e "$FILE" ]; then
        echo "UNTRACKED_COLLISION=$FILE"
        UNTRACKED_COLLISION=1
    fi
done < "$INCOMING_FILE_LIST"
if [ "$UNTRACKED_COLLISION" -ne 0 ]; then
    echo "ABORT=UNTRACKED_WOULD_BE_OVERWRITTEN"
    echo "WRITE_OPERATION_EXECUTED=NO"
    exit 32
fi
echo "UNTRACKED_COLLISIONS=NONE"

echo
echo "===== 5. RECOVERY REF ====="
BACKUP_REF="refs/backup/mirror-sync/$TS"
git update-ref "$BACKUP_REF" "$LOCAL_BEFORE"
BACKUP_SHA="$(git rev-parse "$BACKUP_REF")"
test "$BACKUP_SHA" = "$LOCAL_BEFORE" || { echo "ABORT=BACKUP_REF_FAILED"; exit 40; }
echo "RECOVERY_REF=$BACKUP_REF"
echo "RECOVERY_SHA=$BACKUP_SHA"

echo
echo "===== 6. CONCURRENCY RECHECK ====="
git fetch origin "$DEV_BRANCH" "$MIRROR_BRANCH"
REMOTE_DEV_2="$(git rev-parse origin/$DEV_BRANCH)"
REMOTE_MIRROR_2="$(git rev-parse origin/$MIRROR_BRANCH)"
LOCAL_2="$(git rev-parse HEAD)"
test "$LOCAL_2" = "$LOCAL_BEFORE" || { echo "ABORT=LOCAL_MOVED_DURING_CHECK"; exit 41; }
test "$REMOTE_DEV_2" = "$TARGET" || { echo "ABORT=REMOTE_DEV_MOVED_DURING_CHECK"; exit 42; }
test "$REMOTE_MIRROR_2" = "$REMOTE_MIRROR" || { echo "ABORT=MIRROR_MOVED_DURING_CHECK"; exit 43; }

if [ "$REMOTE_MIRROR_2" != "$TARGET" ]; then
    git merge-base --is-ancestor "$REMOTE_MIRROR_2" "$TARGET" || { echo "ABORT=MIRROR_NO_LONGER_FAST_FORWARDABLE"; exit 44; }
    EDARSA_ALLOW_PUSH=1 git push origin "$TARGET:refs/heads/$MIRROR_BRANCH" || { echo "ABORT=MIRROR_FAST_FORWARD_PUSH_FAILED"; exit 45; }
    git fetch origin "$MIRROR_BRANCH"
    test "$(git rev-parse origin/$MIRROR_BRANCH)" = "$TARGET" || { echo "ABORT=MIRROR_FAST_FORWARD_VERIFY_FAILED"; exit 46; }
    echo "MIRROR_FAST_FORWARD_EXECUTED=YES"
else
    echo "MIRROR_ALREADY_AT_TARGET=YES"
fi

echo
echo "===== 7. SAFE LOCAL FAST-FORWARD ====="
# Canonical refresh uses writer lock, ref CAS and read-tree plumbing; no destructive sync command is executed.
if [ "$LOCAL_BEFORE" != "$TARGET" ]; then
    PY="$(edarsahub_git_guard_python)" || { echo "ABORT=GIT_GUARD_PYTHON_NOT_FOUND"; exit 50; }
    "$PY" "$ROOT/tools/mirror_sync/git_divergence_guard.py" refresh --repo "$ROOT" --expected-remote "$TARGET" --job-id "mirror-sync-refresh-$$" --owner "mirror-sync-refresh" --owner-pid "$$" || { echo "ABORT=LOCAL_FAST_FORWARD_REFRESH_FAILED"; exit 50; }
fi
LOCAL_AFTER="$(git rev-parse HEAD)"
test "$LOCAL_AFTER" = "$TARGET" || { echo "ABORT=LOCAL_FAST_FORWARD_VERIFY_FAILED"; exit 50; }
echo "LOCAL_AFTER=$LOCAL_AFTER"
echo "LOCAL_FAST_FORWARD_EXECUTED=YES"

echo
echo "===== 8. VERIFY LOCAL WORK PRESERVATION ====="
git diff --cached --binary -- > "$STAGED_PATCH_AFTER"
git diff --binary -- > "$UNSTAGED_PATCH_AFTER"
git status --porcelain=v1 --untracked-files=all | grep '^?? ' | sed 's/^?? //' | sort > "$UNTRACKED_AFTER" || true

if ! cmp -s "$STAGED_PATCH_BEFORE" "$STAGED_PATCH_AFTER"; then
    echo "ABORT=STAGED_STATE_CHANGED"
    exit 51
fi
if ! cmp -s "$UNSTAGED_PATCH_BEFORE" "$UNSTAGED_PATCH_AFTER"; then
    echo "ABORT=UNSTAGED_STATE_CHANGED"
    exit 52
fi
if ! cmp -s "$UNTRACKED_BEFORE" "$UNTRACKED_AFTER"; then
    echo "ABORT=UNTRACKED_SET_CHANGED"
    exit 53
fi

TRACKED_AFTER="$(git diff --name-only | wc -l)"
STAGED_AFTER="$(git diff --cached --name-only | wc -l)"
UNTRACKED_COUNT_AFTER="$(wc -l < "$UNTRACKED_AFTER")"
test "$TRACKED_AFTER" -eq "$TRACKED" || { echo "ABORT=UNSTAGED_COUNT_CHANGED"; exit 54; }
test "$STAGED_AFTER" -eq "$STAGED" || { echo "ABORT=STAGED_COUNT_CHANGED"; exit 55; }
test "$UNTRACKED_COUNT_AFTER" -eq "$UNTRACKED" || { echo "ABORT=UNTRACKED_COUNT_CHANGED"; exit 56; }
echo "STAGED_WORK_PRESERVED=YES"
echo "UNSTAGED_WORK_PRESERVED=YES"
echo "UNTRACKED_PRESERVED=YES"
echo "LOCAL_WORK_PRESERVED=YES"

echo
echo "===== 9. FINAL CONSISTENCY ====="
git fetch origin "$DEV_BRANCH" "$MIRROR_BRANCH"
FINAL_LOCAL="$(git rev-parse HEAD)"
FINAL_DEV="$(git rev-parse origin/$DEV_BRANCH)"
FINAL_MIRROR="$(git rev-parse origin/$MIRROR_BRANCH)"
echo "FINAL_LOCAL=$FINAL_LOCAL"
echo "FINAL_DEV=$FINAL_DEV"
echo "FINAL_MIRROR=$FINAL_MIRROR"
test "$FINAL_LOCAL" = "$TARGET"
test "$FINAL_DEV" = "$TARGET"
test "$FINAL_MIRROR" = "$TARGET"
echo "REMOTE_UPDATE_APPLIED=YES"
echo "FAST_FORWARD_ONLY=YES"
echo "LOCAL_REMOTE_MIRROR_MATCH=YES"
echo "PRODUCTION_TOUCHED=NO"

echo
echo "===== 10. RUNTIME RELOAD ====="
if [ "$INCOMING_RUNTIME_CHANGED" = "YES" ]; then
    PARENT_CMD="$(tr '\000' ' ' < "/proc/$PPID/cmdline" 2>/dev/null || true)"
    if printf '%s' "$PARENT_CMD" | grep -q '/app/tools/mirror_sync/mirror_sync_worker.sh'; then
        echo "WORKER_RUNTIME_RELOAD_REQUIRED=YES"
        kill -HUP "$PPID" 2>/dev/null || { echo "WORKER_RUNTIME_RELOAD_SIGNAL_FAILED=YES"; exit 60; }
        echo "WORKER_RUNTIME_RELOAD_SIGNAL_SENT=YES"
    else
        echo "WORKER_RUNTIME_RELOAD_REQUIRED=NO"
        echo "REASON=APPLY_NOT_LAUNCHED_BY_MIRROR_WORKER"
    fi
else
    echo "WORKER_RUNTIME_RELOAD_REQUIRED=NO"
    echo "REASON=NO_WORKER_RUNTIME_FILES_CHANGED"
fi
