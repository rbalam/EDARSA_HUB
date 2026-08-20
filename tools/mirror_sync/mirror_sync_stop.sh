#!/usr/bin/env bash
set -euo pipefail

STATE_DIR="/app/.git/mirror-sync"
ENABLE_FLAG="$STATE_DIR/ENABLED"
PERSISTENT_STOP="$STATE_DIR/STOP"

TEMP_DIR="/tmp/edarsahub-mirror-sync"
TEMP_STOP="$TEMP_DIR/STOP"

mkdir -p "$STATE_DIR"
mkdir -p "$TEMP_DIR"

rm -f "$ENABLE_FLAG"

{
    echo "STOPPED_AT_UTC=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
    echo "HOST=$(hostname)"
    echo "PID=$$"
} > "$PERSISTENT_STOP"

{
    echo "STOPPED_AT_UTC=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
    echo "HOST=$(hostname)"
    echo "PID=$$"
} > "$TEMP_STOP"

chmod 0600 "$PERSISTENT_STOP"
chmod 0600 "$TEMP_STOP"

echo "MIRROR_SYNC_ENABLED=NO"
echo "PERSISTENT_EMERGENCY_STOP=ACTIVE"
echo "TEMPORARY_EMERGENCY_STOP=ACTIVE"
echo "WRITE_OPERATION_EXECUTED=NO"
