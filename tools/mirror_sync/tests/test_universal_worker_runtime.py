from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
MIRROR = ROOT / "tools/mirror_sync/mirror_sync_worker.sh"
UNIVERSAL = ROOT / "tools/mirror_sync/universal_job_worker.sh"
LAUNCHER = ROOT / "tools/mirror_sync/mirror_sync_supervisor_entrypoint.sh"


def text(path):
    return path.read_text(encoding="utf-8")


def test_universal_worker_is_dedicated_and_fast_polling():
    body = text(UNIVERSAL)
    assert 'UNIVERSAL_WORKER_INTAKE_SECONDS:-10' in body
    assert 'UNIVERSAL_WORKER_RESULT_SECONDS:-10' in body
    assert 'UNIVERSAL_WORKER_HEALTH_SECONDS:-30' in body
    assert 'UNIVERSAL_WORKER_RECONCILE_SECONDS:-30' in body
    assert 'UNIVERSAL_WORKER_DISPATCH_IDLE_SECONDS:-2' in body
    assert '"$PYTHON_BIN" "$BRIDGE" receive' in body
    assert '"$PYTHON_BIN" "$DISPATCHER"' in body
    assert '"$PYTHON_BIN" "$RESULT_PUBLISHER"' in body
    assert 'last_cycle_utc' in body
    assert 'last_receive_utc' in body


def test_mirror_cycle_no_longer_owns_receive_dispatch_publish():
    body = text(MIRROR)
    assert 'UNIVERSAL_WORKER="$DIR/universal_job_worker.sh"' in body
    assert 'start_universal_worker' in body
    assert 'ensure_universal_worker' in body
    assert 'receive_universal_jobs' not in body
    assert 'dispatch_universal_jobs' not in body
    assert 'publish_universal_results' not in body


def test_mirror_blocking_operations_are_bounded():
    body = text(MIRROR)
    assert 'MIRROR_TOOL_TIMEOUT_SECONDS' in body
    assert 'timeout --signal=TERM --kill-after=5' in body
    assert 'STATE=CHECK_TIMEOUT' in body
    assert 'STATE=PUBLISH_TIMEOUT' in body
    assert 'STATE=FINALIZER_TIMEOUT' in body


def test_launcher_has_progress_watchdog_and_bounded_health():
    body = text(LAUNCHER)
    assert 'UNIVERSAL_WORKER_STALE_SECONDS:-90' in body
    assert 'UNIVERSAL_PROGRESS_STALE=YES' in body
    assert 'LAUNCHER_RESTART_REASON=UNIVERSAL_PROGRESS_STALE' in body
    assert 'MIRROR_LAUNCHER_HEALTH_TIMEOUT_SECONDS:-60' in body
    assert 'LAUNCHER_HEALTH_TIMEOUT=YES' in body
