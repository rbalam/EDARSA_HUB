#!/usr/bin/env bash

MIRROR_SYNC_STATE_DIR="/app/.git/mirror-sync"
MIRROR_SYNC_ENABLE_FLAG="$MIRROR_SYNC_STATE_DIR/ENABLED"
MIRROR_SYNC_TEMP_STOP="/tmp/edarsahub-mirror-sync/STOP"

mirror_sync_require_enabled() {
    if [ -e "$MIRROR_SYNC_TEMP_STOP" ]; then
        echo "MIRROR_SYNC_ENABLED=NO"
        echo "MIRROR_SYNC_STOP_REASON=EMERGENCY_STOP_ACTIVE"
        echo "WRITE_OPERATION_EXECUTED=NO"
        return 90
    fi

    if [ ! -e "$MIRROR_SYNC_ENABLE_FLAG" ]; then
        echo "MIRROR_SYNC_ENABLED=NO"
        echo "MIRROR_SYNC_STOP_REASON=PERSISTENT_ENABLE_ABSENT"
        echo "WRITE_OPERATION_EXECUTED=NO"
        return 90
    fi

    echo "MIRROR_SYNC_ENABLED=YES"
    return 0
}
