#!/usr/bin/env bash
set -euo pipefail

STATE_DIR="/app/.git/mirror-sync"
ENABLE_FLAG="$STATE_DIR/ENABLED"

TEMP_DIR="/tmp/edarsahub-mirror-sync"
STOP_FLAG="$TEMP_DIR/STOP"

mkdir -p "$STATE_DIR"
mkdir -p "$TEMP_DIR"

rm -f "$ENABLE_FLAG"

{
    echo "STOPPED_AT_UTC=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
    echo "HOST=$(hostname)"
    echo "PID=$$"
} > "$STOP_FLAG"

chmod 0600 "$STOP_FLAG"

echo "MIRROR_SYNC_ENABLED=NO"
echo "EMERGENCY_STOP=ACTIVE"
echo "WRITE_OPERATION_EXECUTED=NO"
