#!/usr/bin/env bash
set -euo pipefail

STATE_DIR="/app/.git/mirror-sync"
ENABLE_FLAG="$STATE_DIR/ENABLED"

TEMP_DIR="/tmp/edarsahub-mirror-sync"
STOP_FLAG="$TEMP_DIR/STOP"

mkdir -p "$STATE_DIR"
mkdir -p "$TEMP_DIR"

rm -f "$STOP_FLAG"

{
    echo "ENABLED_AT_UTC=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
    echo "HOST=$(hostname)"
    echo "PID=$$"
} > "$ENABLE_FLAG"

chmod 0600 "$ENABLE_FLAG"

echo "MIRROR_SYNC_ENABLED=YES"
echo "EMERGENCY_STOP=INACTIVE"
echo "NOTE=NO_SYNC_EXECUTED"
