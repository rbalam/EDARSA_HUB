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

echo "===== EDARSAHUB SAFE REMOTE UPDATE CHECK ====="

BRANCH="$(git branch --show-current)"
LOCAL="$(git rev-parse HEAD)"

echo "LOCAL_BRANCH=$BRANCH"
echo "LOCAL_HEAD=$LOCAL"

test "$BRANCH" = "$DEV_BRANCH" || {
    echo "DECISION=ABORT_WRONG_BRANCH"
    exit 10
}

echo
echo "===== FETCH ====="

git fetch origin "$DEV_BRANCH" "$MIRROR_BRANCH"

DEV="$(git rev-parse origin/$DEV_BRANCH)"
MIRROR="$(git rev-parse origin/$MIRROR_BRANCH)"

echo "REMOTE_DEV=$DEV"
echo "REMOTE_MIRROR=$MIRROR"

echo
echo "===== LOCAL STATE ====="

STAGED="$(git diff --cached --name-only | wc -l)"
TRACKED="$(git diff --name-only | wc -l)"
UNTRACKED="$(git status --porcelain=v1 | grep -c '^?? ' || true)"

echo "STAGED_COUNT=$STAGED"
echo "TRACKED_MODIFIED_COUNT=$TRACKED"
echo "UNTRACKED_COUNT=$UNTRACKED"

echo
echo "===== TOPOLOGY ====="

BASE_LOCAL_DEV="$(git merge-base "$LOCAL" "$DEV")"
BASE_LOCAL_MIRROR="$(git merge-base "$LOCAL" "$MIRROR")"

echo "BASE_LOCAL_DEV=$BASE_LOCAL_DEV"
echo "BASE_LOCAL_MIRROR=$BASE_LOCAL_MIRROR"

LOCAL_TO_DEV="$(git rev-list --count "$LOCAL..$DEV")"
DEV_TO_LOCAL="$(git rev-list --count "$DEV..$LOCAL")"

LOCAL_TO_MIRROR="$(git rev-list --count "$LOCAL..$MIRROR")"
MIRROR_TO_LOCAL="$(git rev-list --count "$MIRROR..$LOCAL")"

echo "DEV_AHEAD_OF_LOCAL=$LOCAL_TO_DEV"
echo "LOCAL_AHEAD_OF_DEV=$DEV_TO_LOCAL"
echo "MIRROR_AHEAD_OF_LOCAL=$LOCAL_TO_MIRROR"
echo "LOCAL_AHEAD_OF_MIRROR=$MIRROR_TO_LOCAL"

echo
echo "===== DECISION ====="

if [ "$DEV" = "$LOCAL" ] && [ "$MIRROR" = "$LOCAL" ]; then
    echo "DECISION=ALREADY_SYNCHRONIZED"
    echo "WRITE_OPERATION_EXECUTED=NO"
    exit 0
fi

if ! git merge-base --is-ancestor "$LOCAL" "$DEV"; then
    echo "DECISION=ABORT_DEV_NOT_FAST_FORWARD_FROM_LOCAL"
    echo "WRITE_OPERATION_EXECUTED=NO"
    exit 30
fi

if [ "$DEV" != "$MIRROR" ]; then
    if git merge-base --is-ancestor "$MIRROR" "$DEV"; then
        echo "DEV_MIRROR_RELATION=DEV_FAST_FORWARD_AHEAD"
        echo "MIRROR_FAST_FORWARD_REQUIRED=YES"
    else
        echo "DECISION=ABORT_DEV_MIRROR_TRUE_DIVERGENCE"
        echo "WRITE_OPERATION_EXECUTED=NO"
        exit 32
    fi
else
    echo "DEV_MIRROR_RELATION=ALIGNED"
    echo "MIRROR_FAST_FORWARD_REQUIRED=NO"
fi

echo
echo "===== INCOMING CHANGESET ====="

git diff --name-status "$LOCAL" "$DEV"

INCOMING_COUNT="$(git diff --name-only "$LOCAL" "$DEV" | wc -l)"

echo "INCOMING_FILES=$INCOMING_COUNT"

echo
echo "===== TRACKED LOCAL COLLISION GUARDS ====="

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
done < <(git diff --name-only "$LOCAL" "$DEV")

if [ "$TRACKED_COLLISION" -ne 0 ]; then
    echo "DECISION=ABORT_LOCAL_TRACKED_COLLISION"
    echo "WRITE_OPERATION_EXECUTED=NO"
    exit 20
fi

echo "STAGED_COLLISIONS=NONE"
echo "UNSTAGED_COLLISIONS=NONE"

echo
echo "===== UNTRACKED COLLISION GUARD ====="

COLLISION=0

while IFS= read -r FILE; do
    [ -n "$FILE" ] || continue

    # Si HEAD local ya conoce el archivo, no es una colision untracked.
    if git cat-file -e "$LOCAL:$FILE" 2>/dev/null; then
        continue
    fi

    # Si existe fisicamente pero HEAD local no lo conoce,
    # la actualizacion remota lo sobrescribiria.
    if [ -e "$FILE" ]; then
        echo "UNTRACKED_COLLISION=$FILE"
        COLLISION=1
    fi
done < <(git diff --name-only "$LOCAL" "$DEV")

if [ "$COLLISION" -ne 0 ]; then
    echo "DECISION=ABORT_UNTRACKED_WOULD_BE_OVERWRITTEN"
    echo "WRITE_OPERATION_EXECUTED=NO"
    exit 33
fi

echo "UNTRACKED_COLLISIONS=NONE"

echo
echo "DECISION=SAFE_REMOTE_FAST_FORWARD_AVAILABLE"
echo "TARGET_HEAD=$DEV"
echo "LOCAL_UNTRACKED_PRESERVED=$UNTRACKED"
echo "WRITE_OPERATION_EXECUTED=NO"
echo "PRODUCTION_TOUCHED=NO"
