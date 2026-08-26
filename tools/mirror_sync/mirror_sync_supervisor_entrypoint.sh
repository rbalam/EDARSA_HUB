#!/usr/bin/env bash
set -euo pipefail

ROOT="/app"
DIR="$ROOT/tools/mirror_sync"
WORKER="$DIR/mirror_sync_worker.sh"

resolve_worker_python() {
  if [ -x "$ROOT/.venv/bin/python" ]; then
    printf '%s\n' "$ROOT/.venv/bin/python"
    return 0
  fi

  command -v python3 2>/dev/null || command -v python 2>/dev/null || true
}

PYTHON_BIN="$(resolve_worker_python)"

if [ -z "$PYTHON_BIN" ] || [ ! -x "$PYTHON_BIN" ]; then
  echo "ABORT=WORKER_PYTHON_NOT_EXECUTABLE"
  exit 4
fi
CHECK="$DIR/check_remote_update.sh"
APPLY="$DIR/apply_remote_update.sh"
STATUS="$DIR/mirror_sync_status.sh"
HEALTH="$DIR/runtime_health_publisher.py"
STATE="$ROOT/.git/mirror-sync"
LAUNCHER_STATE="$STATE/launcher"
LOOP_SECONDS="${MIRROR_LAUNCHER_LOOP_SECONDS:-15}"
WORKER_PID=""
WORKER_SHA=""
RUNNING=1

mkdir -p "$LAUNCHER_STATE"

log() { printf '%s %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$*"; }
sha_file() { sha256sum "$1" | awk '{print $1}'; }

stop_worker() {
  if [ -n "${WORKER_PID:-}" ] && kill -0 "$WORKER_PID" 2>/dev/null; then
    kill -TERM "$WORKER_PID" 2>/dev/null || true
    for _ in $(seq 1 20); do
      kill -0 "$WORKER_PID" 2>/dev/null || break
      sleep 0.25
    done
    kill -KILL "$WORKER_PID" 2>/dev/null || true
    wait "$WORKER_PID" 2>/dev/null || true
  fi
  WORKER_PID=""
}

shutdown() {
  RUNNING=0
  log "LAUNCHER_SIGNAL_RECEIVED=YES"
  stop_worker
}
trap shutdown TERM INT HUP

start_worker() {
  test -x "$WORKER" || chmod 0755 "$WORKER" 2>/dev/null || true
  test -r "$WORKER" || { log "LAUNCHER_WORKER_MISSING=YES"; return 1; }
  WORKER_SHA="$(sha_file "$WORKER")"
  log "LAUNCHER_START_WORKER_SHA=$WORKER_SHA"
  /bin/bash "$WORKER" &
  WORKER_PID=$!
  printf '%s\n' "$WORKER_PID" > "$LAUNCHER_STATE/worker.pid"
  printf '%s\n' "$WORKER_SHA" > "$LAUNCHER_STATE/worker.sha256"
}

safe_refresh() {
  local out rc
  out="$(mktemp)"
  set +e
  "$CHECK" >"$out" 2>&1
  rc=$?
  set -e
  cat "$out"
  if [ "$rc" -eq 0 ] && grep -q '^DECISION=SAFE_REMOTE_FAST_FORWARD_AVAILABLE$' "$out"; then
    log "LAUNCHER_REMOTE_UPDATE_AVAILABLE=YES"
    rm -f "$out"
    set +e
    "$APPLY"
    rc=$?
    set -e
    log "LAUNCHER_APPLY_RC=$rc"
    return "$rc"
  fi
  rm -f "$out"
  return 0
}

log "MIRROR_SUPERVISOR_LAUNCHER_STARTED=YES"
log "LAUNCHER_LOOP_SECONDS=$LOOP_SECONDS"

while [ "$RUNNING" -eq 1 ]; do
  # The launcher is the stable parent. It performs safe repository refreshes
  # independently from the worker child, eliminating self-update deadlocks.
  safe_refresh || true

  CURRENT_SHA=""
  [ -r "$WORKER" ] && CURRENT_SHA="$(sha_file "$WORKER")"

  if [ -z "$WORKER_PID" ] || ! kill -0 "$WORKER_PID" 2>/dev/null; then
    [ -z "$WORKER_PID" ] || wait "$WORKER_PID" 2>/dev/null || true
    log "LAUNCHER_WORKER_NOT_RUNNING=YES"
    start_worker || true
  elif [ -n "$CURRENT_SHA" ] && [ "$CURRENT_SHA" != "$WORKER_SHA" ]; then
    log "LAUNCHER_WORKER_CODE_CHANGED=YES"
    log "LAUNCHER_OLD_WORKER_SHA=$WORKER_SHA"
    log "LAUNCHER_NEW_WORKER_SHA=$CURRENT_SHA"
    stop_worker
    start_worker || true
  fi

  # Publish health independently as a second observability path. This keeps
  # status visible even if the child worker is temporarily unhealthy.
  if [ -f "$HEALTH" ]; then
    "$PYTHON_BIN" "$HEALTH" >/tmp/edarsahub-worker-health-launcher.log 2>&1 || true
  fi

  sleep "$LOOP_SECONDS" &
  wait $! || true
done

stop_worker
log "MIRROR_SUPERVISOR_LAUNCHER_STOPPED=YES"
