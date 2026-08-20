#!/usr/bin/env bash

MIRROR_SYNC_STATE_DIR="/app/.git/mirror-sync"

MIRROR_SYNC_ENABLE_FLAG="$MIRROR_SYNC_STATE_DIR/ENABLED"
MIRROR_SYNC_PERSISTENT_STOP="$MIRROR_SYNC_STATE_DIR/STOP"

MIRROR_SYNC_TEMP_DIR="/tmp/edarsahub-mirror-sync"
MIRROR_SYNC_TEMP_STOP="$MIRROR_SYNC_TEMP_DIR/STOP"

MIRROR_SYNC_LOCK_FILE="$MIRROR_SYNC_STATE_DIR/runtime.lock"

mirror_sync_require_enabled() {
    if [ -e "$MIRROR_SYNC_PERSISTENT_STOP" ]; then
        echo "MIRROR_SYNC_ENABLED=NO"
        echo "MIRROR_SYNC_STOP_REASON=PERSISTENT_EMERGENCY_STOP_ACTIVE"
        echo "WRITE_OPERATION_EXECUTED=NO"
        return 90
    fi

    if [ -e "$MIRROR_SYNC_TEMP_STOP" ]; then
        echo "MIRROR_SYNC_ENABLED=NO"
        echo "MIRROR_SYNC_STOP_REASON=TEMPORARY_EMERGENCY_STOP_ACTIVE"
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

mirror_sync_acquire_global_lock() {
    mkdir -p "$MIRROR_SYNC_STATE_DIR"

    command -v flock >/dev/null 2>&1 || {
        echo "MIRROR_SYNC_LOCK_ACQUIRED=NO"
        echo "MIRROR_SYNC_LOCK_REASON=FLOCK_NOT_AVAILABLE"
        echo "WRITE_OPERATION_EXECUTED=NO"
        return 91
    }

    exec 9>"$MIRROR_SYNC_LOCK_FILE"

    if ! flock -n 9; then
        echo "MIRROR_SYNC_LOCK_ACQUIRED=NO"
        echo "MIRROR_SYNC_LOCK_REASON=ANOTHER_SYNC_PROCESS_ACTIVE"
        echo "MIRROR_SYNC_LOCK_FILE=$MIRROR_SYNC_LOCK_FILE"
        echo "WRITE_OPERATION_EXECUTED=NO"
        return 92
    fi

    echo "MIRROR_SYNC_LOCK_ACQUIRED=YES"
    echo "MIRROR_SYNC_LOCK_FILE=$MIRROR_SYNC_LOCK_FILE"
    return 0
}
