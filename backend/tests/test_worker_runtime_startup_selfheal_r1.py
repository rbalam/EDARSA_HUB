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


def test_preview_startup_ensures_recovery_supervisor_services():
    assert 'WATCHDOG_SERVICE = "edarsahub-bootstrap-watchdog"' in ROUTE
    assert 'SUPERVISOR_CONF_DIR = Path("/etc/supervisor/conf.d")' in ROUTE
    assert "def _ensure_recovery_supervisor_services()" in ROUTE
    assert 'SUPERVISOR_CONF_DIR / "edarsahub-bootstrap-watchdog.conf"' in ROUTE
    assert 'SUPERVISOR_CONF_DIR / "edarsahub-universal-worker.conf"' in ROUTE
    assert '["supervisorctl", "reread"]' in ROUTE
    assert '["supervisorctl", "update"]' in ROUTE
    assert '["supervisorctl", "start", service]' in ROUTE
    assert "RECOVERY_SERVICES_READY" in ROUTE


def test_preview_startup_recovery_services_are_production_blocked():
    assert '_is_production_environment()' in ROUTE
    block = ROUTE.split("def _ensure_recovery_supervisor_services()", 1)[1].split("def ensure_worker_runtime_on_preview_startup()", 1)[0]
    assert "SKIPPED_PRODUCTION_ENV" in block
    assert '"production_touched": False' in block
def test_preview_startup_detects_running_but_stale_watchdog():
    assert "def _converge_running_watchdog_if_stale()" in ROUTE
    assert "WATCHDOG_SOURCE" in ROUTE
    assert "WATCHDOG_RUNTIME_CURRENT" in ROUTE
    assert "WATCHDOG_RUNTIME_RESTARTED" in ROUTE
    assert "WATCHDOG_CODE_STALE" in ROUTE
    assert "_watchdog_process_start_epoch(" in ROUTE
    assert "_supervisor_running_pid(" in ROUTE


def test_watchdog_convergence_requires_canonical_development():
    block = ROUTE.split(
        "def _watchdog_repo_is_canonical()",
        1,
    )[1].split(
        "def _converge_running_watchdog_if_stale()",
        1,
    )[0]

    assert '"branch",' in block
    assert '"--show-current",' in block
    assert '"status",' in block
    assert '"--porcelain=v1"' in block
    assert '"rev-parse",' in block
    assert 'f"origin/{DEV_BRANCH}"' in block
    assert "DEVELOPMENT_NOT_CONVERGED" in block
    assert "WORKTREE_DIRTY" in block


def test_running_current_watchdog_is_noop():
    block = ROUTE.split(
        "def _converge_running_watchdog_if_stale()",
        1,
    )[1].split(
        "def _ensure_recovery_supervisor_services()",
        1,
    )[0]

    assert "source_mtime <= process_start" in block
    assert '"state": "WATCHDOG_RUNTIME_CURRENT"' in block


def test_watchdog_stale_restart_is_bounded_and_locked():
    block = ROUTE.split(
        "def _converge_running_watchdog_if_stale()",
        1,
    )[1].split(
        "def _ensure_recovery_supervisor_services()",
        1,
    )[0]

    assert "WATCHDOG_RUNTIME_LOCK_PATH" in block
    assert "fcntl.LOCK_EX | fcntl.LOCK_NB" in block
    assert "WATCHDOG_RUNTIME_COOLDOWN_SECONDS" in block
    assert "WATCHDOG_CONVERGENCE_COOLDOWN" in block
    assert (
        '"supervisorctl",\n'
        '                "restart",\n'
        "                WATCHDOG_SERVICE,"
        in block
    )


def test_watchdog_restart_requires_new_running_pid():
    block = ROUTE.split(
        "def _converge_running_watchdog_if_stale()",
        1,
    )[1].split(
        "def _ensure_recovery_supervisor_services()",
        1,
    )[0]

    assert "pid_after != pid_before" in block
    assert "WATCHDOG_RESTART_NOT_PROVEN" in block
    assert "WATCHDOG_RUNTIME_RESTARTED" in block


def test_watchdog_runtime_convergence_is_production_fail_closed():
    block = ROUTE.split(
        "def _converge_running_watchdog_if_stale()",
        1,
    )[1].split(
        "def _ensure_recovery_supervisor_services()",
        1,
    )[0]

    assert "_is_production_environment()" in block
    assert "SKIPPED_PRODUCTION_ENV" in block
    assert '"production_touched": False' in block


def test_watchdog_convergence_does_not_touch_incidents_or_mirror():
    block = ROUTE.split(
        "def _converge_running_watchdog_if_stale()",
        1,
    )[1].split(
        "def _ensure_recovery_supervisor_services()",
        1,
    )[0]

    assert "maintenance/incidents" not in block
    assert "mirror-sync" not in block
    assert "MIRROR" not in block
    assert "ENABLED" not in block
    assert "STOP" not in block
