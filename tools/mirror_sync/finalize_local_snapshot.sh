#!/usr/bin/env bash
set -euo pipefail

MIRROR_SYNC_GUARD="/app/tools/mirror_sync/mirror_sync_guard.sh"

test -r "$MIRROR_SYNC_GUARD" || {
    echo "ABORT=MIRROR_SYNC_GUARD_MISSING"
    echo "WRITE_OPERATION_EXECUTED=NO"
    exit 90
}

. "$MIRROR_SYNC_GUARD"
SAFETY_GUARD="/app/tools/mirror_sync/shared_app_safety_guard.sh"
test -r "$SAFETY_GUARD" || { echo "ABORT=SHARED_APP_SAFETY_GUARD_MISSING"; exit 90; }
. "$SAFETY_GUARD"

mirror_sync_require_enabled || exit $?
mirror_sync_acquire_global_lock || exit $?
WRITER_JOB_ID="mirror-finalize-$$"
WRITER_OWNER="mirror-finalize"
WRITER_LOCK_ACQUIRED=0

ROOT="/app"
REMOTE="origin"
DEV_BRANCH="Edarsahub_Desarrollo"
MIRROR_BRANCH="mirror/emergent-live"

MAX_BYTES=5000000

SNAPSHOT="${1:-}"

if [ -z "$SNAPSHOT" ]; then
    echo "USAGE=$0 SNAPSHOT_SHA"
    echo "WRITE_OPERATION_EXECUTED=NO"
    exit 2
fi

cd "$ROOT"

echo "===== EDARSAHUB SAFE LOCAL SNAPSHOT FINALIZER ====="

BRANCH="$(git branch --show-current)"
LOCAL_HEAD="$(git rev-parse HEAD)"

echo "LOCAL_BRANCH=$BRANCH"
echo "LOCAL_HEAD=$LOCAL_HEAD"
echo "REQUESTED_SNAPSHOT=$SNAPSHOT"

test "$BRANCH" = "$DEV_BRANCH" || {
    echo "ABORT=WRONG_BRANCH"
    echo "WRITE_OPERATION_EXECUTED=NO"
    exit 10
}

echo
echo "===== 1. SNAPSHOT OBJECT GUARD ====="

git cat-file -e "$SNAPSHOT^{commit}" 2>/dev/null || {
    echo "ABORT=SNAPSHOT_COMMIT_NOT_FOUND"
    echo "WRITE_OPERATION_EXECUTED=NO"
    exit 11
}

SNAPSHOT="$(git rev-parse "$SNAPSHOT^{commit}")"

echo "SNAPSHOT=$SNAPSHOT"

PARENT_COUNT="$(
    git rev-list \
        --parents \
        -n 1 \
        "$SNAPSHOT" |
    awk '{print NF-1}'
)"

echo "SNAPSHOT_PARENT_COUNT=$PARENT_COUNT"

test "$PARENT_COUNT" -eq 1 || {
    echo "ABORT=SNAPSHOT_NOT_SINGLE_PARENT"
    echo "WRITE_OPERATION_EXECUTED=NO"
    exit 12
}

SNAPSHOT_PARENT="$(git rev-parse "$SNAPSHOT^")"

echo "SNAPSHOT_PARENT=$SNAPSHOT_PARENT"

test "$SNAPSHOT_PARENT" = "$LOCAL_HEAD" || {
    echo "ABORT=SNAPSHOT_PARENT_NOT_LOCAL_HEAD"
    echo "WRITE_OPERATION_EXECUTED=NO"
    exit 13
}

git merge-base --is-ancestor "$LOCAL_HEAD" "$SNAPSHOT" || {
    echo "ABORT=SNAPSHOT_NOT_FAST_FORWARD"
    echo "WRITE_OPERATION_EXECUTED=NO"
    exit 14
}

echo "SNAPSHOT_FAST_FORWARD=YES"

echo
echo "===== 2. FETCH REMOTES ====="

git fetch "$REMOTE" "$DEV_BRANCH" "$MIRROR_BRANCH"

REMOTE_DEV="$(git rev-parse "$REMOTE/$DEV_BRANCH")"
REMOTE_MIRROR="$(git rev-parse "$REMOTE/$MIRROR_BRANCH")"

echo "REMOTE_DEV=$REMOTE_DEV"
echo "REMOTE_MIRROR=$REMOTE_MIRROR"

test "$REMOTE_DEV" = "$LOCAL_HEAD" || {
    echo "ABORT=REMOTE_DEV_NOT_LOCAL_BASE"
    echo "WRITE_OPERATION_EXECUTED=NO"
    exit 20
}

test "$REMOTE_MIRROR" = "$SNAPSHOT" || {
    echo "ABORT=MIRROR_NOT_REQUESTED_SNAPSHOT"
    echo "WRITE_OPERATION_EXECUTED=NO"
    exit 21
}

echo
echo "===== 3. REAL INDEX MUST BE UNSTAGED ====="

STAGED_COUNT="$(git diff --cached --name-only | wc -l)"

echo "STAGED_COUNT=$STAGED_COUNT"

test "$STAGED_COUNT" -eq 0 || {
    echo "ABORT=REAL_INDEX_HAS_STAGED_WORK"
    echo "WRITE_OPERATION_EXECUTED=NO"
    exit 30
}

echo
echo "===== 4. REBUILD CURRENT WORKTREE SNAPSHOT IN ISOLATED INDEX ====="

TMP_INDEX="$(mktemp)"

cleanup() {
    rm -f "$TMP_INDEX"
    if [ "$WRITER_LOCK_ACQUIRED" -eq 1 ]; then
        edarsahub_release_git_writer_lock "$WRITER_JOB_ID" "$WRITER_OWNER" >/dev/null || echo "GIT_WRITER_LOCK_RELEASE=FAIL"
    fi
}

trap cleanup EXIT

export GIT_INDEX_FILE="$TMP_INDEX"

git read-tree "$LOCAL_HEAD"

git add -u

for PATHNAME in \
    backend \
    frontend \
    docs \
    memory \
    tools \
    .github
do
    if [ -e "$PATHNAME" ]; then
        git add -- "$PATHNAME"
    fi
done

for PATHNAME in \
    AGENTS.md \
    ANTIGRAVITY.md \
    CLAUDE.md \
    CODEX.md \
    GEMINI.md \
    GROK.md \
    KIMI.md
do
    if [ -f "$PATHNAME" ]; then
        git add -- "$PATHNAME"
    fi
done

WORKTREE_TREE="$(git write-tree)"
SNAPSHOT_TREE="$(git rev-parse "$SNAPSHOT^{tree}")"

echo "WORKTREE_TREE=$WORKTREE_TREE"
echo "SNAPSHOT_TREE=$SNAPSHOT_TREE"

test "$WORKTREE_TREE" = "$SNAPSHOT_TREE" || {
    echo "ABORT=WORKTREE_DOES_NOT_MATCH_SNAPSHOT"
    echo
    echo "===== WORKTREE VS SNAPSHOT ====="

    git diff \
        --cached \
        --name-status \
        "$SNAPSHOT" || true

    echo "WRITE_OPERATION_EXECUTED=NO"
    exit 31
}

echo "WORKTREE_MATCHES_SNAPSHOT=YES"

unset GIT_INDEX_FILE

echo
echo "===== 5. SECRET AND SIZE REVALIDATION ====="

SENSITIVE="$(
    git diff --name-only "$LOCAL_HEAD" "$SNAPSHOT" |
    grep -Ei '(^|/)(\.env($|\.)|.*\.pem$|.*\.key$|id_rsa$|id_ed25519$|credentials?\.json$|secrets?\.json$)' \
    || true
)"

if [ -n "$SENSITIVE" ]; then
    echo "ABORT=SENSITIVE_FILENAME_DETECTED"
    printf '%s\n' "$SENSITIVE"
    echo "WRITE_OPERATION_EXECUTED=NO"
    exit 32
fi

LARGE_FOUND=0

while IFS= read -r FILE; do
    [ -n "$FILE" ] || continue

    BLOB="$(
        git rev-parse "$SNAPSHOT:$FILE" 2>/dev/null || true
    )"

    [ -n "$BLOB" ] || continue

    SIZE="$(git cat-file -s "$BLOB")"

    if [ "$SIZE" -gt "$MAX_BYTES" ]; then
        echo "LARGE_FILE=$FILE"
        echo "BYTES=$SIZE"
        LARGE_FOUND=1
    fi
done < <(
    git diff \
        --diff-filter=AMCR \
        --name-only \
        "$LOCAL_HEAD" \
        "$SNAPSHOT"
)

test "$LARGE_FOUND" -eq 0 || {
    echo "ABORT=LARGE_FILE_IN_SNAPSHOT"
    echo "WRITE_OPERATION_EXECUTED=NO"
    exit 33
}

echo "CONTENT_GUARDS=PASS"

echo
echo "===== 6. PRESERVE UNTRACKED MANIFEST ====="

TS="$(date -u +%Y%m%dT%H%M%SZ)"
STATE_DIR="/tmp/edarsahub-agents/mirror-sync/finalize-$TS"

mkdir -p "$STATE_DIR"

UNTRACKED_BEFORE="$STATE_DIR/untracked_before.txt"
UNTRACKED_AFTER="$STATE_DIR/untracked_after.txt"

git status --porcelain=v1 |
grep '^?? ' |
sed 's/^?? //' |
sort > "$UNTRACKED_BEFORE" || true

echo "UNTRACKED_BEFORE=$(wc -l < "$UNTRACKED_BEFORE")"
echo "STATE_DIR=$STATE_DIR"

echo
echo "===== 7. CREATE LOCAL RECOVERY REF ====="

BACKUP_REF="refs/backup/mirror-sync/finalize-$TS"

git update-ref \
    "$BACKUP_REF" \
    "$LOCAL_HEAD"

BACKUP_SHA="$(git rev-parse "$BACKUP_REF")"

echo "BACKUP_REF=$BACKUP_REF"
echo "BACKUP_SHA=$BACKUP_SHA"

test "$BACKUP_SHA" = "$LOCAL_HEAD" || {
    echo "ABORT=BACKUP_REF_FAILED"
    exit 40
}

echo
echo "===== 8. CANONICAL DEVELOPMENT WRITER LOCK + FINAL CONCURRENCY RECHECK ====="

edarsahub_acquire_git_writer_lock "$WRITER_JOB_ID" "$WRITER_OWNER" >/dev/null || { echo "ABORT=GIT_LOCK_BUSY"; exit 45; }
WRITER_LOCK_ACQUIRED=1
git fetch "$REMOTE" "$DEV_BRANCH" "$MIRROR_BRANCH"

LOCAL_RECHECK="$(git rev-parse HEAD)"
DEV_RECHECK="$(git rev-parse "$REMOTE/$DEV_BRANCH")"
MIRROR_RECHECK="$(git rev-parse "$REMOTE/$MIRROR_BRANCH")"

echo "LOCAL_RECHECK=$LOCAL_RECHECK"
echo "DEV_RECHECK=$DEV_RECHECK"
echo "MIRROR_RECHECK=$MIRROR_RECHECK"

test "$LOCAL_RECHECK" = "$LOCAL_HEAD" || {
    echo "ABORT=LOCAL_MOVED_DURING_FINALIZE"
    exit 41
}

test "$DEV_RECHECK" = "$LOCAL_HEAD" || {
    echo "ABORT=DEVELOPMENT_MOVED_DURING_FINALIZE"
    exit 42
}

test "$MIRROR_RECHECK" = "$SNAPSHOT" || {
    echo "ABORT=MIRROR_MOVED_DURING_FINALIZE"
    exit 43
}

echo
echo "===== 9. PRE-PROMOTION INDEX LOCK GUARD ====="

LOCK="$ROOT/.git/index.lock"

if [ -e "$LOCK" ]; then
    echo "ABORT=INDEX_LOCK_PRESENT_BEFORE_REMOTE_PROMOTION"
    echo "LOCK=$LOCK"
    echo "REMOTE_PROMOTION_EXECUTED=NO"
    echo "LOCAL_ALIGNMENT_EXECUTED=NO"
    exit 44
fi

echo "INDEX_LOCK_BEFORE_PROMOTION=ABSENT"

echo
echo "===== 10. PROMOTE SNAPSHOT TO DEVELOPMENT ====="

EDARSA_ALLOW_PUSH=1 EDARSA_PUSH_JOB_ID="$WRITER_JOB_ID" EDARSA_PUSH_OWNER="$WRITER_OWNER" git push "$REMOTE" "$SNAPSHOT:refs/heads/$DEV_BRANCH"

git fetch "$REMOTE" "$DEV_BRANCH" "$MIRROR_BRANCH"

DEV_AFTER_PUSH="$(git rev-parse "$REMOTE/$DEV_BRANCH")"
MIRROR_AFTER_PUSH="$(git rev-parse "$REMOTE/$MIRROR_BRANCH")"

echo "DEV_AFTER_PUSH=$DEV_AFTER_PUSH"
echo "MIRROR_AFTER_PUSH=$MIRROR_AFTER_PUSH"

test "$DEV_AFTER_PUSH" = "$SNAPSHOT" || {
    echo "ABORT=DEVELOPMENT_PROMOTION_FAILED"
    exit 50
}

test "$MIRROR_AFTER_PUSH" = "$SNAPSHOT" || {
    echo "ABORT=MIRROR_CHANGED_AFTER_PROMOTION"
    exit 51
}

echo
echo "===== 11. POST-PROMOTION INDEX LOCK RECHECK ====="

if [ -e "$LOCK" ]; then
    echo "ABORT=INDEX_LOCK_APPEARED_AFTER_REMOTE_PROMOTION"
    echo "LOCK=$LOCK"
    echo "REMOTE_PROMOTION_EXECUTED=YES"
    echo "LOCAL_ALIGNMENT_EXECUTED=NO"
    echo "RECOVERY_REF=$BACKUP_REF"
    exit 52
fi

echo "INDEX_LOCK_AFTER_PROMOTION=ABSENT"

echo
echo "===== 12. ADVANCE LOCAL REF ONLY ====="

git update-ref \
    "refs/heads/$DEV_BRANCH" \
    "$SNAPSHOT" \
    "$LOCAL_HEAD"

LOCAL_AFTER_REF="$(git rev-parse HEAD)"

echo "LOCAL_AFTER_REF=$LOCAL_AFTER_REF"

test "$LOCAL_AFTER_REF" = "$SNAPSHOT" || {
    echo "ABORT=LOCAL_REF_ADVANCE_FAILED"
    exit 53
}

echo
echo "===== 13. ALIGN REAL INDEX ONLY ====="

git read-tree "$SNAPSHOT"

echo "INDEX_ALIGNMENT=COMPLETE"

echo
echo "===== 14. VERIFY TRACKED STATE ====="

TRACKED_AFTER="$(git diff --name-only | wc -l)"
STAGED_AFTER="$(git diff --cached --name-only | wc -l)"

echo "TRACKED_AFTER=$TRACKED_AFTER"
echo "STAGED_AFTER=$STAGED_AFTER"

test "$TRACKED_AFTER" -eq 0 || {
    echo "ABORT=TRACKED_DIFF_AFTER_FINALIZE"
    git diff --name-status
    exit 54
}

test "$STAGED_AFTER" -eq 0 || {
    echo "ABORT=STAGED_DIFF_AFTER_FINALIZE"
    git diff --cached --name-status
    exit 55
}

echo
echo "===== 15. VERIFY UNTRACKED TRANSITION ====="

git status --porcelain=v1 |
grep '^?? ' |
sed 's/^?? //' |
sort > "$UNTRACKED_AFTER" || true

echo "UNTRACKED_AFTER=$(wc -l < "$UNTRACKED_AFTER")"

VALIDATION_ERRORS=0

while IFS= read -r ENTRY; do
    [ -n "$ENTRY" ] || continue

    if grep -Fxq "$ENTRY" "$UNTRACKED_AFTER"; then
        continue
    fi

    CLEAN_ENTRY="${ENTRY%/}"

    if git ls-tree -r \
        --name-only \
        "$SNAPSHOT" \
        -- "$CLEAN_ENTRY" |
        grep -q .
    then
        echo "FORMER_UNTRACKED_NOW_TRACKED_OK=$ENTRY"
    else
        echo "UNTRACKED_LOSS=$ENTRY"
        VALIDATION_ERRORS=$((VALIDATION_ERRORS + 1))
    fi
done < "$UNTRACKED_BEFORE"

echo "UNTRACKED_VALIDATION_ERRORS=$VALIDATION_ERRORS"

test "$VALIDATION_ERRORS" -eq 0 || {
    echo "ABORT=UNTRACKED_PRESERVATION_FAILED"
    exit 56
}

NEW_UNTRACKED="$STATE_DIR/untracked_new.txt"

comm -13     "$UNTRACKED_BEFORE"     "$UNTRACKED_AFTER"     > "$NEW_UNTRACKED"

NEW_UNTRACKED_COUNT="$(wc -l < "$NEW_UNTRACKED")"

echo "NEW_UNTRACKED_COUNT=$NEW_UNTRACKED_COUNT"

if [ "$NEW_UNTRACKED_COUNT" -ne 0 ]; then
    echo "ABORT=NEW_UNTRACKED_APPEARED_DURING_FINALIZE"
    cat "$NEW_UNTRACKED"
    exit 57
fi

echo "UNTRACKED_PRESERVATION_VALID=YES"
echo "NEW_UNTRACKED_APPEARED=NO"

echo
echo "===== 16. FINAL CONSISTENCY ====="

git fetch "$REMOTE" "$DEV_BRANCH" "$MIRROR_BRANCH"

FINAL_LOCAL="$(git rev-parse HEAD)"
FINAL_DEV="$(git rev-parse "$REMOTE/$DEV_BRANCH")"
FINAL_MIRROR="$(git rev-parse "$REMOTE/$MIRROR_BRANCH")"

echo "FINAL_LOCAL=$FINAL_LOCAL"
echo "FINAL_DEV=$FINAL_DEV"
echo "FINAL_MIRROR=$FINAL_MIRROR"

test "$FINAL_LOCAL" = "$SNAPSHOT"
test "$FINAL_DEV" = "$SNAPSHOT"
test "$FINAL_MIRROR" = "$SNAPSHOT"

echo
echo "LOCAL_SNAPSHOT_FINALIZED=YES"
echo "MIRROR_PROMOTED_TO_DEVELOPMENT=YES"
echo "LOCAL_REMOTE_MIRROR_MATCH=YES"
echo "FAST_FORWARD_ONLY=YES"
echo "WORKTREE_MATCH_VERIFIED=YES"
echo "TRACKED_WORKTREE_CLEAN=YES"
echo "STAGED_WORK=NONE"
echo "UNTRACKED_PRESERVED=YES"
echo "RECOVERY_REF=$BACKUP_REF"
echo "PRODUCTION_TOUCHED=NO"
