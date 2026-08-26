#!/usr/bin/env bash
set -euo pipefail

ROOT="/app"
DIR="$ROOT/tools/mirror_sync"
WORKER="$DIR/mirror_sync_worker.sh"

resolve_worker_python() {
  if [ -x "$ROOT/.venv/bin/python" ]; then printf '%s\n' "$ROOT/.venv/bin/python"; return 0; fi
  command -v python3 2>/dev/null || command -v python 2>/dev/null || true
}
PYTHON_BIN="$(resolve_worker_python)"
if [ -z "$PYTHON_BIN" ] || [ ! -x "$PYTHON_BIN" ]; then echo "ABORT=WORKER_PYTHON_NOT_EXECUTABLE"; exit 4; fi

CHECK="$DIR/check_remote_update.sh"
APPLY="$DIR/apply_remote_update.sh"
HEALTH="$DIR/runtime_health_publisher.py"
STATE="$ROOT/.git/mirror-sync"
LAUNCHER_STATE="$STATE/launcher"
UNIVERSAL_RUNTIME="$ROOT/.git/universal-worker-queue/runtime"
LOOP_SECONDS="${MIRROR_LAUNCHER_LOOP_SECONDS:-15}"
REFRESH_TIMEOUT="${MIRROR_LAUNCHER_REFRESH_TIMEOUT_SECONDS:-120}"
HEALTH_TIMEOUT="${MIRROR_LAUNCHER_HEALTH_TIMEOUT_SECONDS:-60}"
UNIVERSAL_STALE_SECONDS="${UNIVERSAL_WORKER_STALE_SECONDS:-90}"
WORKER_PID=""
WORKER_SHA=""
RUNNING=1
mkdir -p "$LAUNCHER_STATE"

log() { printf '%s %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$*"; }
sha_file() { sha256sum "$1" | awk '{print $1}'; }

run_timeout() {
  local seconds="$1"; shift
  if command -v timeout >/dev/null 2>&1; then timeout --signal=TERM --kill-after=5 "${seconds}s" "$@"; else "$@"; fi
}

stop_worker() {
  if [ -n "${WORKER_PID:-}" ] && kill -0 "$WORKER_PID" 2>/dev/null; then
    kill -TERM "$WORKER_PID" 2>/dev/null || true
    for _ in $(seq 1 20); do kill -0 "$WORKER_PID" 2>/dev/null || break; sleep 0.25; done
    kill -KILL "$WORKER_PID" 2>/dev/null || true
    wait "$WORKER_PID" 2>/dev/null || true
  fi
  WORKER_PID=""
}
shutdown() { RUNNING=0; log "LAUNCHER_SIGNAL_RECEIVED=YES"; stop_worker; }
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
  printf '%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" > "$LAUNCHER_STATE/worker_started_utc"
}

safe_refresh() {
  local out rc
  out="$(mktemp)"
  set +e; run_timeout "$REFRESH_TIMEOUT" "$CHECK" >"$out" 2>&1; rc=$?; set -e
  cat "$out"
  if [ "$rc" -eq 124 ] || [ "$rc" -eq 137 ]; then log "LAUNCHER_REFRESH_TIMEOUT=YES"; rm -f "$out"; return 0; fi
  if [ "$rc" -eq 0 ] && grep -q '^DECISION=SAFE_REMOTE_FAST_FORWARD_AVAILABLE$' "$out"; then
    log "LAUNCHER_REMOTE_UPDATE_AVAILABLE=YES"; rm -f "$out"
    set +e; run_timeout "$REFRESH_TIMEOUT" "$APPLY"; rc=$?; set -e
    log "LAUNCHER_APPLY_RC=$rc"; return 0
  fi
  rm -f "$out"; return 0
}

universal_progress_stale() {
  local stamp="$UNIVERSAL_RUNTIME/last_cycle_utc" now epoch age
  [ -r "$stamp" ] || return 1
  epoch="$(date -u -d "$(cat "$stamp")" +%s 2>/dev/null || echo 0)"
  now="$(date -u +%s)"
  [ "$epoch" -gt 0 ] || return 1
  age=$((now - epoch))
  if [ "$age" -gt "$UNIVERSAL_STALE_SECONDS" ]; then
    log "UNIVERSAL_PROGRESS_STALE=YES"
    log "UNIVERSAL_PROGRESS_AGE_SECONDS=$age"
    return 0
  fi
  return 1
}

log "MIRROR_SUPERVISOR_LAUNCHER_STARTED=YES"
log "LAUNCHER_LOOP_SECONDS=$LOOP_SECONDS"
while [ "$RUNNING" -eq 1 ]; do
  safe_refresh || true
  CURRENT_SHA=""; [ -r "$WORKER" ] && CURRENT_SHA="$(sha_file "$WORKER")"
  if [ -z "$WORKER_PID" ] || ! kill -0 "$WORKER_PID" 2>/dev/null; then
    [ -z "$WORKER_PID" ] || wait "$WORKER_PID" 2>/dev/null || true
    log "LAUNCHER_WORKER_NOT_RUNNING=YES"; start_worker || true
  elif [ -n "$CURRENT_SHA" ] && [ "$CURRENT_SHA" != "$WORKER_SHA" ]; then
    log "LAUNCHER_WORKER_CODE_CHANGED=YES"; stop_worker; start_worker || true
  elif universal_progress_stale; then
    log "LAUNCHER_RESTART_REASON=UNIVERSAL_PROGRESS_STALE"; stop_worker; start_worker || true
  fi

  if [ -f "$HEALTH" ]; then
    set +e; run_timeout "$HEALTH_TIMEOUT" "$PYTHON_BIN" "$HEALTH" >/tmp/edarsahub-worker-health-launcher.log 2>&1; HEALTH_RC=$?; set -e
    if [ "$HEALTH_RC" -eq 124 ] || [ "$HEALTH_RC" -eq 137 ]; then log "LAUNCHER_HEALTH_TIMEOUT=YES"; fi
  fi
  sleep "$LOOP_SECONDS" & wait $! || true
done
stop_worker
log "MIRROR_SUPERVISOR_LAUNCHER_STOPPED=YES"
