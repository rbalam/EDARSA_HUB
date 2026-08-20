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

if [ "$STAGED" -ne 0 ]; then
    echo "DECISION=ABORT_STAGED_WORK_PRESENT"
    echo "WRITE_OPERATION_EXECUTED=NO"
    exit 20
fi

if [ "$TRACKED" -ne 0 ]; then
    echo "DECISION=ABORT_LOCAL_TRACKED_CHANGES_PRESENT"
    echo
    echo "LOCAL_CHANGED_FILES:"
    git diff --name-status
    echo "WRITE_OPERATION_EXECUTED=NO"
    exit 21
fi

if ! git merge-base --is-ancestor "$LOCAL" "$DEV"; then
    echo "DECISION=ABORT_DEV_NOT_FAST_FORWARD_FROM_LOCAL"
    echo "WRITE_OPERATION_EXECUTED=NO"
    exit 30
fi

if ! git merge-base --is-ancestor "$LOCAL" "$MIRROR"; then
    echo "DECISION=ABORT_MIRROR_NOT_FAST_FORWARD_FROM_LOCAL"
    echo "WRITE_OPERATION_EXECUTED=NO"
    exit 31
fi

if [ "$DEV" != "$MIRROR" ]; then
    echo "DECISION=ABORT_DEV_MIRROR_DIVERGENCE"
    echo "WRITE_OPERATION_EXECUTED=NO"
    exit 32
fi

echo
echo "===== INCOMING CHANGESET ====="

git diff --name-status "$LOCAL" "$DEV"

INCOMING_COUNT="$(git diff --name-only "$LOCAL" "$DEV" | wc -l)"

echo "INCOMING_FILES=$INCOMING_COUNT"

echo
echo "DECISION=SAFE_REMOTE_FAST_FORWARD_AVAILABLE"
echo "TARGET_HEAD=$DEV"
echo "LOCAL_UNTRACKED_PRESERVED=$UNTRACKED"
echo "WRITE_OPERATION_EXECUTED=NO"
echo "PRODUCTION_TOUCHED=NO"
