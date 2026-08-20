#!/usr/bin/env bash
set -euo pipefail

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

test "$BRANCH" = "$DEV_BRANCH" || {
    echo "ABORT=WRONG_BRANCH"
    exit 10
}

echo
echo "===== 1. FETCH ====="

git fetch origin "$DEV_BRANCH" "$MIRROR_BRANCH"

REMOTE_DEV="$(git rev-parse origin/$DEV_BRANCH)"
REMOTE_MIRROR="$(git rev-parse origin/$MIRROR_BRANCH)"

echo "REMOTE_DEV=$REMOTE_DEV"
echo "REMOTE_MIRROR=$REMOTE_MIRROR"

echo
echo "===== 2. LOCAL MUTATION GUARDS ====="

STAGED="$(git diff --cached --name-only | wc -l)"
TRACKED="$(git diff --name-only | wc -l)"

echo "STAGED_COUNT=$STAGED"
echo "TRACKED_MODIFIED_COUNT=$TRACKED"

test "$STAGED" -eq 0 || {
    echo "ABORT=STAGED_WORK_PRESENT"
    exit 20
}

test "$TRACKED" -eq 0 || {
    echo "ABORT=LOCAL_TRACKED_CHANGES_PRESENT"
    git diff --name-status
    exit 21
}

echo
echo "===== 3. REMOTE CONSISTENCY ====="

test "$REMOTE_DEV" = "$REMOTE_MIRROR" || {
    echo "ABORT=DEV_MIRROR_DIVERGENCE"
    exit 30
}

TARGET="$REMOTE_DEV"

if [ "$LOCAL_BEFORE" = "$TARGET" ]; then
    echo "DECISION=ALREADY_SYNCHRONIZED"
    echo "WRITE_OPERATION_EXECUTED=NO"
    exit 0
fi

git merge-base --is-ancestor "$LOCAL_BEFORE" "$TARGET" || {
    echo "ABORT=TARGET_NOT_FAST_FORWARD"
    exit 31
}

echo "FAST_FORWARD_VALID=YES"

echo
echo "===== 4. INCOMING PAYLOAD ====="

git diff --name-status "$LOCAL_BEFORE" "$TARGET"

INCOMING_COUNT="$(git diff --name-only "$LOCAL_BEFORE" "$TARGET" | wc -l)"

echo "INCOMING_FILES=$INCOMING_COUNT"

echo
echo "===== 5. PROTECT UNTRACKED COLLISIONS ====="

COLLISION=0

while IFS= read -r FILE; do
    [ -n "$FILE" ] || continue

    if git ls-files --error-unmatch -- "$FILE" >/dev/null 2>&1; then
        continue
    fi

    if [ -e "$FILE" ]; then
        echo "UNTRACKED_COLLISION=$FILE"
        COLLISION=1
    fi
done < <(git diff --name-only "$LOCAL_BEFORE" "$TARGET")

test "$COLLISION" -eq 0 || {
    echo "ABORT=UNTRACKED_WOULD_BE_OVERWRITTEN"
    exit 32
}

echo "UNTRACKED_COLLISIONS=NONE"

echo
echo "===== 6. PRESERVE UNTRACKED MANIFEST ====="

TS="$(date -u +%Y%m%dT%H%M%SZ)"
STATE_DIR="/tmp/edarsahub-agents/mirror-sync/$TS"

mkdir -p "$STATE_DIR"

UNTRACKED_BEFORE="$STATE_DIR/untracked_before.txt"

git status --porcelain=v1 |
grep '^?? ' |
sed 's/^?? //' |
sort > "$UNTRACKED_BEFORE" || true

UNTRACKED_COUNT_BEFORE="$(wc -l < "$UNTRACKED_BEFORE")"

echo "UNTRACKED_COUNT_BEFORE=$UNTRACKED_COUNT_BEFORE"

echo
echo "===== 7. CREATE LOCAL RECOVERY REF ====="

BACKUP_REF="refs/backup/mirror-sync/$TS"

git update-ref "$BACKUP_REF" "$LOCAL_BEFORE"

BACKUP_SHA="$(git rev-parse "$BACKUP_REF")"

echo "BACKUP_REF=$BACKUP_REF"
echo "BACKUP_SHA=$BACKUP_SHA"

test "$BACKUP_SHA" = "$LOCAL_BEFORE" || {
    echo "ABORT=BACKUP_REF_FAILED"
    exit 40
}

echo
echo "===== 8. RECHECK CONCURRENCY ====="

git fetch origin "$DEV_BRANCH" "$MIRROR_BRANCH"

REMOTE_DEV_2="$(git rev-parse origin/$DEV_BRANCH)"
REMOTE_MIRROR_2="$(git rev-parse origin/$MIRROR_BRANCH)"
LOCAL_2="$(git rev-parse HEAD)"

echo "LOCAL_RECHECK=$LOCAL_2"
echo "REMOTE_DEV_RECHECK=$REMOTE_DEV_2"
echo "REMOTE_MIRROR_RECHECK=$REMOTE_MIRROR_2"

test "$LOCAL_2" = "$LOCAL_BEFORE" || {
    echo "ABORT=LOCAL_MOVED_DURING_CHECK"
    exit 41
}

test "$REMOTE_DEV_2" = "$TARGET" || {
    echo "ABORT=REMOTE_DEV_MOVED_DURING_CHECK"
    exit 42
}

test "$REMOTE_MIRROR_2" = "$TARGET" || {
    echo "ABORT=MIRROR_MOVED_DURING_CHECK"
    exit 43
}

echo
echo "===== 9. FAST-FORWARD LOCAL ONLY ====="

git merge --ff-only "$TARGET"

LOCAL_AFTER="$(git rev-parse HEAD)"

echo "LOCAL_AFTER=$LOCAL_AFTER"

test "$LOCAL_AFTER" = "$TARGET" || {
    echo "ABORT=LOCAL_FAST_FORWARD_FAILED"
    exit 50
}

echo
echo "===== 10. VERIFY TRACKED STATE ====="

TRACKED_AFTER="$(git diff --name-only | wc -l)"
STAGED_AFTER="$(git diff --cached --name-only | wc -l)"

echo "TRACKED_AFTER=$TRACKED_AFTER"
echo "STAGED_AFTER=$STAGED_AFTER"

test "$TRACKED_AFTER" -eq 0 || {
    echo "ABORT=TRACKED_DIFF_AFTER_APPLY"
    git diff --name-status
    exit 51
}

test "$STAGED_AFTER" -eq 0 || {
    echo "ABORT=STAGED_DIFF_AFTER_APPLY"
    git diff --cached --name-status
    exit 52
}

echo
echo "===== 11. VERIFY UNTRACKED ====="

UNTRACKED_AFTER="$STATE_DIR/untracked_after.txt"

git status --porcelain=v1 |
grep '^?? ' |
sed 's/^?? //' |
sort > "$UNTRACKED_AFTER" || true

UNTRACKED_COUNT_AFTER="$(wc -l < "$UNTRACKED_AFTER")"

echo "UNTRACKED_COUNT_AFTER=$UNTRACKED_COUNT_AFTER"

if ! cmp -s "$UNTRACKED_BEFORE" "$UNTRACKED_AFTER"; then
    echo "ABORT=UNTRACKED_SET_CHANGED"
    diff -u "$UNTRACKED_BEFORE" "$UNTRACKED_AFTER" || true
    exit 53
fi

echo "UNTRACKED_PRESERVED=YES"

echo
echo "===== 12. FINAL CONSISTENCY ====="

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

echo
echo "REMOTE_UPDATE_APPLIED=YES"
echo "FAST_FORWARD_ONLY=YES"
echo "LOCAL_REMOTE_MIRROR_MATCH=YES"
echo "TRACKED_WORKTREE_CLEAN=YES"
echo "STAGED_WORK=NONE"
echo "UNTRACKED_PRESERVED=YES"
echo "RECOVERY_REF=$BACKUP_REF"
echo "PRODUCTION_TOUCHED=NO"
