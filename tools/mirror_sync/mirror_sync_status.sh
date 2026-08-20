#!/usr/bin/env bash
set -euo pipefail

ENABLE_FLAG="/app/.git/mirror-sync/ENABLED"
STOP_FLAG="/tmp/edarsahub-mirror-sync/STOP"

echo "===== EDARSAHUB MIRROR SYNC STATUS ====="

if [ -e "$STOP_FLAG" ]; then
    echo "MIRROR_SYNC_ENABLED=NO"
    echo "EMERGENCY_STOP=ACTIVE"
    echo "REASON=TEMPORARY_STOP_FLAG"
elif [ ! -e "$ENABLE_FLAG" ]; then
    echo "MIRROR_SYNC_ENABLED=NO"
    echo "EMERGENCY_STOP=INACTIVE"
    echo "REASON=PERSISTENT_ENABLE_ABSENT"
else
    echo "MIRROR_SYNC_ENABLED=YES"
    echo "EMERGENCY_STOP=INACTIVE"
    echo "REASON=AUTHORIZED"
fi

echo
echo "ENABLE_FLAG=$ENABLE_FLAG"
echo "STOP_FLAG=$STOP_FLAG"
