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

echo
echo "===== 3. REMOTE CONSISTENCY ====="

MIRROR_FAST_FORWARD_REQUIRED=NO
if [ "$REMOTE_DEV" != "$REMOTE_MIRROR" ]; then
    git merge-base --is-ancestor "$REMOTE_MIRROR" "$REMOTE_DEV" || {
        echo "ABORT=DEV_MIRROR_TRUE_DIVERGENCE"
        exit 30
    }
    MIRROR_FAST_FORWARD_REQUIRED=YES
fi

echo "MIRROR_FAST_FORWARD_REQUIRED=$MIRROR_FAST_FORWARD_REQUIRED"
TARGET="$REMOTE_DEV"

if [ "$LOCAL_BEFORE" = "$TARGET" ] && [ "$REMOTE_MIRROR" = "$TARGET" ]; then
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
INCOMING_RUNTIME_CHANGED="NO"
if git diff --name-only "$LOCAL_BEFORE" "$TARGET" | grep -Eq '^tools/mirror_sync/(mirror_sync_worker\.sh|universal_job_bridge\.py|universal_job_dispatcher\.py|universal_job_result_publisher\.py|runtime_health_publisher\.py|apply_remote_update\.sh)$'; then
    INCOMING_RUNTIME_CHANGED="YES"
fi

echo "INCOMING_FILES=$INCOMING_COUNT"
echo "INCOMING_RUNTIME_CHANGED=$INCOMING_RUNTIME_CHANGED"

echo
echo "===== 5. PROTECT TRACKED LOCAL CHANGES ====="

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
done < <(git diff --name-only "$LOCAL_BEFORE" "$TARGET")

test "$TRACKED_COLLISION" -eq 0 || {
    echo "ABORT=LOCAL_TRACKED_COLLISION"
    echo "WRITE_OPERATION_EXECUTED=NO"
    exit 20
}

echo "STAGED_COLLISIONS=NONE"
echo "UNSTAGED_COLLISIONS=NONE"

echo
echo "===== 6. PROTECT UNTRACKED COLLISIONS ====="

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
echo "===== 7. PRESERVE LOCAL WORK STATE ====="

TS="$(date -u +%Y%m%dT%H%M%SZ)"
STATE_DIR="/tmp/edarsahub-agents/mirror-sync/$TS"

mkdir -p "$STATE_DIR"

STAGED_PATCH_BEFORE="$STATE_DIR/staged_before.patch"
STAGED_PATCH_AFTER="$STATE_DIR/staged_after.patch"
UNSTAGED_PATCH_BEFORE="$STATE_DIR/unstaged_before.patch"
UNSTAGED_PATCH_AFTER="$STATE_DIR/unstaged_after.patch"

git diff --cached --binary -- > "$STAGED_PATCH_BEFORE"
git diff --binary -- > "$UNSTAGED_PATCH_BEFORE"

STAGED_PATCH_SHA_BEFORE="$(sha256sum "$STAGED_PATCH_BEFORE" | awk '{print $1}')"
UNSTAGED_PATCH_SHA_BEFORE="$(sha256sum "$UNSTAGED_PATCH_BEFORE" | awk '{print $1}')"

echo "STAGED_PATCH_SHA_BEFORE=$STAGED_PATCH_SHA_BEFORE"
echo "UNSTAGED_PATCH_SHA_BEFORE=$UNSTAGED_PATCH_SHA_BEFORE"

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

test "$REMOTE_MIRROR_2" = "$REMOTE_MIRROR" || {
    echo "ABORT=MIRROR_MOVED_DURING_CHECK"
    exit 43
}

if [ "$REMOTE_MIRROR_2" != "$TARGET" ]; then
    git merge-base --is-ancestor "$REMOTE_MIRROR_2" "$TARGET" || {
        echo "ABORT=MIRROR_NO_LONGER_FAST_FORWARDABLE"
        exit 44
    }

    echo
    echo "===== 9. FAST-FORWARD REMOTE MIRROR ====="

    EDARSA_ALLOW_PUSH=1 git push origin       "$TARGET:refs/heads/$MIRROR_BRANCH" || {
        echo "ABORT=MIRROR_FAST_FORWARD_PUSH_FAILED"
        exit 45
    }

    git fetch origin "$MIRROR_BRANCH"

    MIRROR_AFTER_PUSH="$(git rev-parse origin/$MIRROR_BRANCH)"
    echo "MIRROR_AFTER_PUSH=$MIRROR_AFTER_PUSH"

    test "$MIRROR_AFTER_PUSH" = "$TARGET" || {
        echo "ABORT=MIRROR_FAST_FORWARD_VERIFY_FAILED"
        exit 46
    }
else
    echo "MIRROR_ALREADY_AT_TARGET=YES"
fi

echo
echo "===== 11. SAFE LOCAL FAST-FORWARD ====="

# /app is a shared developer workspace. Never mutate HEAD/index/worktree
# while any local work exists. The Worker uses isolated worktrees; local
# convergence is deferred until /app is completely clean.
if [ "$LOCAL_BEFORE" != "$TARGET" ]; then
    if [ "$STAGED" -gt 0 ] || [ "$TRACKED" -gt 0 ] || [ "$UNTRACKED_COUNT_BEFORE" -gt 0 ]; then
        echo "DECISION=DEFER_LOCAL_DIRTY"
        echo "LOCAL_FAST_FORWARD_EXECUTED=NO"
        echo "LOCAL_WORK_PRESERVED=YES"
        LOCAL_AFTER="$LOCAL_BEFORE"
    else
        git merge --ff-only "$TARGET"

        LOCAL_AFTER="$(git rev-parse HEAD)"

        echo "LOCAL_AFTER=$LOCAL_AFTER"

        test "$LOCAL_AFTER" = "$TARGET" || {
            echo "ABORT=LOCAL_FAST_FORWARD_FAILED"
            exit 50
        }

        echo "LOCAL_FAST_FORWARD_EXECUTED=YES"
    fi
else
    LOCAL_AFTER="$LOCAL_BEFORE"
    echo "LOCAL_ALREADY_AT_TARGET=YES"
fi

echo
echo "===== 12. VERIFY LOCAL WORK PRESERVATION ====="

git diff --cached --binary -- > "$STAGED_PATCH_AFTER"
git diff --binary -- > "$UNSTAGED_PATCH_AFTER"

STAGED_PATCH_SHA_AFTER="$(sha256sum "$STAGED_PATCH_AFTER" | awk '{print $1}')"
UNSTAGED_PATCH_SHA_AFTER="$(sha256sum "$UNSTAGED_PATCH_AFTER" | awk '{print $1}')"

echo "STAGED_PATCH_SHA_AFTER=$STAGED_PATCH_SHA_AFTER"
echo "UNSTAGED_PATCH_SHA_AFTER=$UNSTAGED_PATCH_SHA_AFTER"

if ! cmp -s "$STAGED_PATCH_BEFORE" "$STAGED_PATCH_AFTER"; then
    echo "ABORT=STAGED_STATE_CHANGED"
    diff -u "$STAGED_PATCH_BEFORE" "$STAGED_PATCH_AFTER" || true
    exit 51
fi

if ! cmp -s "$UNSTAGED_PATCH_BEFORE" "$UNSTAGED_PATCH_AFTER"; then
    echo "ABORT=UNSTAGED_STATE_CHANGED"
    diff -u "$UNSTAGED_PATCH_BEFORE" "$UNSTAGED_PATCH_AFTER" || true
    exit 52
fi

TRACKED_AFTER="$(git diff --name-only | wc -l)"
STAGED_AFTER="$(git diff --cached --name-only | wc -l)"

echo "TRACKED_AFTER=$TRACKED_AFTER"
echo "STAGED_AFTER=$STAGED_AFTER"

test "$TRACKED_AFTER" -eq "$TRACKED" || {
    echo "ABORT=UNSTAGED_COUNT_CHANGED"
    exit 54
}

test "$STAGED_AFTER" -eq "$STAGED" || {
    echo "ABORT=STAGED_COUNT_CHANGED"
    exit 55
}

echo "STAGED_WORK_PRESERVED=YES"
echo "UNSTAGED_WORK_PRESERVED=YES"

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
echo "LOCAL_WORK_PRESERVED=YES"
echo "STAGED_WORK_PRESERVED=YES"
echo "UNSTAGED_WORK_PRESERVED=YES"
echo "UNTRACKED_PRESERVED=YES"
echo "RECOVERY_REF=$BACKUP_REF"
echo "PRODUCTION_TOUCHED=NO"

# Bootstrap/self-heal: a long-running bash process keeps the old function bodies
# in memory even after its file is fast-forwarded on disk. If this apply was
# launched by the mirror worker and the incoming update changed worker runtime
# files, terminate only that worker process. Supervisor's autorestart then starts
# the freshly updated script from disk. Manual invocations are never signalled.
echo
echo "===== 13. WORKER RUNTIME RELOAD ====="
if [ "$INCOMING_RUNTIME_CHANGED" = "YES" ]; then
    PARENT_CMD="$(tr '\000' ' ' < "/proc/$PPID/cmdline" 2>/dev/null || true)"
    if printf '%s' "$PARENT_CMD" | grep -q '/app/tools/mirror_sync/mirror_sync_worker.sh'; then
        echo "WORKER_RUNTIME_RELOAD_REQUIRED=YES"
        echo "WORKER_RUNTIME_PARENT_PID=$PPID"
        echo "WORKER_RUNTIME_RELOAD_SIGNAL=HUP"
        kill -HUP "$PPID" 2>/dev/null || {
            echo "WORKER_RUNTIME_RELOAD_SIGNAL_FAILED=YES"
            exit 60
        }
        echo "WORKER_RUNTIME_RELOAD_SIGNAL_SENT=YES"
    else
        echo "WORKER_RUNTIME_RELOAD_REQUIRED=NO"
        echo "REASON=APPLY_NOT_LAUNCHED_BY_MIRROR_WORKER"
    fi
else
    echo "WORKER_RUNTIME_RELOAD_REQUIRED=NO"
    echo "REASON=NO_WORKER_RUNTIME_FILES_CHANGED"
fi
