from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ROUTE = (ROOT / "backend/modules/worker_runtime_wake/routes.py").read_text(encoding="utf-8")
SERVER = (ROOT / "backend/server.py").read_text(encoding="utf-8")
RECOVERY = (ROOT / "tools/bootstrap/recover_preview_runtime.sh").read_text(encoding="utf-8")


def test_worker_router_is_mounted_exactly_once():
    assert SERVER.count('app.include_router(worker_runtime_wake_router, prefix="/api")') == 1


def test_preview_backend_startup_recovers_stale_worker_out_of_band():
    assert "def ensure_worker_runtime_on_preview_startup()" in ROUTE
    assert "WORKER_RESTART_REQUESTED" in ROUTE
    assert "SKIPPED_PRODUCTION_ENV" in ROUTE
    assert "ensure_worker_runtime_on_preview_startup()" in SERVER


def test_worker_restart_is_fixed_service_only():
    assert 'WORKER_SERVICE = "edarsahub-universal-worker"' in ROUTE
    assert '["supervisorctl", action, WORKER_SERVICE]' in ROUTE
    assert '_run_supervisor_worker_action("restart")' in ROUTE
    assert '_run_supervisor_worker_action("start")' in ROUTE


def test_preview_recovery_script_is_fail_closed_and_fast_forward_only():
    assert "BLOCKED_PRODUCTION_ENV" in RECOVERY
    assert "DEFERRED_LOCAL_DIRTY" in RECOVERY
    assert 'git merge --ff-only "origin/$DEV_BRANCH"' in RECOVERY
    assert "git reset" not in RECOVERY
    assert "git clean" not in RECOVERY
    assert "git stash" not in RECOVERY
    assert "PRODUCTION_TOUCHED=NO" in RECOVERY


def test_preview_recovery_uses_local_wake_after_backend_restart():
    assert 'supervisorctl restart "$BACKEND_SERVICE"' in RECOVERY
    assert 'supervisorctl restart "$WORKER_SERVICE" || supervisorctl start "$WORKER_SERVICE"' in RECOVERY
    assert "http://127.0.0.1:8001/api/internal/worker/wake" in RECOVERY


def test_preview_recovery_waits_for_backend_http_readiness_before_local_wake():
    restart_pos = RECOVERY.index('supervisorctl restart "$BACKEND_SERVICE"')
    ready_loop_pos = RECOVERY.index('for attempt in $(seq 1 18)')
    wake_pos = RECOVERY.index('http://127.0.0.1:8001/api/internal/worker/wake')
    assert restart_pos < ready_loop_pos < wake_pos
    assert 'BACKEND_READY_HTTP_CODE=' in RECOVERY
    assert 'PREVIEW_RUNTIME_RECOVERY=BACKEND_NOT_READY' in RECOVERY
    assert 'PREVIEW_BACKEND_READY=YES' in RECOVERY


def test_preview_recovery_requires_fresh_worker_heartbeat():
    assert 'RECOVERY_STARTED_EPOCH="$(date +%s)"' in RECOVERY
    assert 'LAST_RECEIVE_EPOCH="$(date -d "$LAST_RECEIVE" +%s 2>/dev/null || echo 0)"' in RECOVERY
    assert 'WORKER_HEARTBEAT_FRESH=YES' in RECOVERY
    assert '"$LAST_RECEIVE_EPOCH" -ge "$RECOVERY_STARTED_EPOCH"' in RECOVERY
