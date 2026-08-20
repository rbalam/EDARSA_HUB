#!/usr/bin/env bash
set -euo pipefail

STATE_DIR="/app/.git/mirror-sync"
ENABLE_FLAG="$STATE_DIR/ENABLED"
PERSISTENT_STOP="$STATE_DIR/STOP"

TEMP_DIR="/tmp/edarsahub-mirror-sync"
TEMP_STOP="$TEMP_DIR/STOP"

mkdir -p "$STATE_DIR"
mkdir -p "$TEMP_DIR"

rm -f "$PERSISTENT_STOP"
rm -f "$TEMP_STOP"

{
    echo "ENABLED_AT_UTC=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
    echo "HOST=$(hostname)"
    echo "PID=$$"
} > "$ENABLE_FLAG"

chmod 0600 "$ENABLE_FLAG"

echo "MIRROR_SYNC_ENABLED=YES"
echo "PERSISTENT_EMERGENCY_STOP=INACTIVE"
echo "TEMPORARY_EMERGENCY_STOP=INACTIVE"
echo "NOTE=NO_SYNC_EXECUTED"
