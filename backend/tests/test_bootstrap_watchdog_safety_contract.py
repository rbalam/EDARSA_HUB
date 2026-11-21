from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BOOTSTRAP = ROOT / "tools/bootstrap/edarsahub_bootstrap_watchdog.py"
INSTALLER = ROOT / "tools/bootstrap/install_bootstrap_watchdog.sh"
MIRROR_CONF = ROOT / "tools/mirror_sync/supervisor/edarsahub-mirror-sync.conf"
MIRROR_START = ROOT / "tools/mirror_sync/mirror_sync_start.sh"


def body() -> str:
    return BOOTSTRAP.read_text(encoding="utf-8")


def test_bootstrap_never_stashes_or_uses_destructive_git():
    text = body()
    assert '"stash"' not in text
    assert '"reset"' not in text
    assert '"clean"' not in text
    assert '"checkout"' not in text
    assert '"restore"' not in text
    assert '"rebase"' not in text


def test_bootstrap_dirty_shared_app_defers():
    text = body()
    assert '"status", "--porcelain=v1", "--untracked-files=all"' in text
    assert "DEFERRED_LOCAL_DIRTY" in text
    assert "FAST_FORWARD_DEFERRED" in text
    assert "LOCAL_WORK_DIRTY" in text


def test_bootstrap_only_allows_strict_fast_forward():
    text = body()
    assert '"rev-list", "--left-right", "--count"' in text
    assert "left != 0 or right <= 0" in text
    assert '"merge", "--ff-only"' in text
    assert "NON_FF" in text


def test_bootstrap_requires_explicit_persistent_authorization():
    text = body()
    assert 'MIRROR_ENABLE = MIRROR_STATE / "ENABLED"' in text
    assert 'MIRROR_STOP = MIRROR_STATE / "STOP"' in text
    assert 'SYNC_PAUSE = APP / ".git" / "EDARSAHUB_SYNC_PAUSED"' in text
    assert "EXPLICIT_ENABLE_REQUIRED" in text
    assert "PERSISTENT_KILL_SWITCH" in text
    assert "BLOCKED_PRODUCTION_ENV" in text


def test_pod_bootstrap_forces_fail_closed_state():
    text = INSTALLER.read_text(encoding="utf-8")
    assert 'rm -f "$MIRROR_ENABLE"' in text
    assert 'POD_BOOTSTRAP_FAIL_CLOSED_AT_UTC=' in text
    assert 'supervisorctl stop "$MIRROR_SERVICE"' in text
    assert "MIRROR_SYNC_STARTUP_POLICY=FAIL_CLOSED" in text


def test_mirror_supervisor_does_not_autostart():
    text = MIRROR_CONF.read_text(encoding="utf-8")
    assert "autostart=false" in text
    assert "autorestart=true" in text


def test_bootstrap_can_recover_stale_universal_worker_without_mirror_dependency():
    text = body()
    assert 'WORKER_SERVICE = os.environ.get("EDARSAHUB_UNIVERSAL_WORKER_SERVICE", "edarsahub-universal-worker")' in text
    assert "UNIVERSAL_WORKER_STALE_RECOVERY" in text
    assert "BOOTSTRAP_WATCHDOG_SUPERVISOR_FALLBACK" in text
    assert 'supervisor_restart("WORKER_HEARTBEAT_STALE", WORKER_SERVICE)' in text
    assert 'cycle_age = age_seconds(RUNTIME / "last_cycle_utc")' in text
    assert "stale = cycle_age is None or cycle_age > MAX_STALE" in text
    assert '"worker_receive_age_seconds": receive_age' in text


def test_bootstrap_may_restart_mirror_only_after_ff():
    text = body()
    assert 'SERVICE = os.environ.get("EDARSAHUB_SUPERVISOR_SERVICE", "edarsahub-mirror-sync")' in text
    assert 'supervisor_restart("FAST_FORWARD_APPLIED")' in text


def test_bootstrap_explicitly_excludes_production():
    text = body()
    assert '"production_touched": False' in text
    assert "Edarsahub_Produccion" not in text


def test_bootstrap_state_writes_are_outside_shared_worktree():
    text = body()
    assert 'STATE = Path(os.environ.get("EDARSAHUB_BOOTSTRAP_STATE", "/var/lib/edarsahub-bootstrap"))' in text
    assert "STATUS = STATE /" in text
    assert "AUDIT = STATE /" in text


def test_mirror_enable_requires_health_gate_before_clearing_kill_switch():
    text = MIRROR_START.read_text(encoding="utf-8")
    assert "BLOCKED_PRODUCTION_ENV" in text
    assert "BLOCKED_WRONG_BRANCH" in text
    assert "BLOCKED_GLOBAL_PAUSE" in text
    assert "DEFERRED_LOCAL_DIRTY" in text
    assert '"HEAD...origin/$DEV_BRANCH"' in text
    assert 'rm -f "$PERSISTENT_STOP" "$TEMP_STOP"' in text
    assert 'SAFETY_GUARD="$APP/tools/mirror_sync/shared_app_safety_guard.sh"' in text
    assert 'STATUS="$(edarsahub_effective_status)"' in text
    assert text.index('STATUS="$(edarsahub_effective_status)"') < text.index('rm -f "$PERSISTENT_STOP" "$TEMP_STOP"')
    assert "MIRROR_SYNC_HEALTH_GATE=PASS" in text


def test_bootstrap_installs_and_starts_universal_worker_independently():
    text = INSTALLER.read_text(encoding="utf-8")
    assert 'WORKER_SERVICE="edarsahub-universal-worker"' in text
    assert 'edarsahub-universal-worker.conf' in text
    assert 'supervisorctl restart "$WORKER_SERVICE" || supervisorctl start "$WORKER_SERVICE"' in text


def test_bootstrap_recovers_stale_preview_backend_out_of_band():
    text = body()
    assert 'BACKEND_SERVICE = os.environ.get("EDARSAHUB_BACKEND_SERVICE", "backend")' in text
    assert 'BACKEND_WAKE_URL = os.environ.get("EDARSAHUB_BACKEND_WAKE_URL", "http://127.0.0.1:8001/api/internal/worker/wake")' in text
    assert "def backend_wake_route_health()" in text
    assert 'code == "401"' in text
    assert 'supervisor_restart("WAKE_ROUTE_UNHEALTHY", BACKEND_SERVICE)' in text
    assert "PREVIEW_BACKEND_STALE_RECOVERY" in text
    assert "BACKEND_RECOVERY_COOLDOWN" in text


def test_all_watchdog_supervisor_restarts_are_production_guarded():
    text = body()
    assert "def is_production_environment()" in text
    assert "SUPERVISOR_RESTART_BLOCKED_PRODUCTION_ENV" in text
    fn = text.split("def supervisor_restart", 1)[1].split("def safe_fast_forward", 1)[0]
    assert "if is_production_environment():" in fn


def test_bootstrap_owns_control_plane_runtime_convergence():
    text = body()

    assert "def control_plane_runtime_convergence()" in text
    assert "CONTROL_PLANE_CODE_STALE" in text
    assert "CONTROL_PLANE_ACTIVE_MARKER" in text
    assert "CONTROL_PLANE_RUNTIME_STATE" in text
    assert "CONTROL_PLANE_MAX_RESTART_ATTEMPTS" in text
    assert "CONTROL_PLANE_RESTART_COOLDOWN_SECONDS" in text
    assert (
        'supervisor_restart(\n'
        '        "CONTROL_PLANE_CODE_STALE",\n'
        '        CONTROL_PLANE_SERVICE,'
        in text
    )


def test_control_plane_convergence_requires_clean_canonical_development():
    text = body()

    assert "def control_plane_repo_is_canonical()" in text
    assert '"branch", "--show-current"' in text
    assert '"status",' in text
    assert '"--porcelain=v1"' in text
    assert "DEVELOPMENT_NOT_CONVERGED" in text
    assert "LOCAL_WORK_DIRTY" in text


def test_control_plane_convergence_uses_dependency_identity_not_head_only():
    text = body()

    assert "CONTROL_PLANE_IDENTITY_PATHS" in text
    assert "worker_control_plane.py" in text
    assert "worker_maintenance_runtime.py" in text
    assert "worker_maintenance_controller.py" in text
    assert "worker_auditor.py" in text
    assert "worker_repair.py" in text
    assert 'f"HEAD:{rel}"' in text
    assert "hashlib.sha256" in text


def test_control_plane_convergence_requires_runtime_ack():
    text = body()

    assert "active_identity" in text
    assert "active_pid" in text
    assert "new_pid != previous_pid" in text
    assert "CONVERGED_AFTER_RESTART" in text
    assert "ACTIVATION_ACK_TIMEOUT" in text


def test_control_plane_convergence_remains_fail_closed():
    text = body()

    assert '"production_touched": False' in text
    assert "Edarsahub_Produccion" not in text
    assert "MIRROR_ENABLE.unlink" not in text
    assert "MIRROR_STOP.unlink" not in text


def _load_watchdog_for_test(tmp_path: Path, monkeypatch):
    import importlib.util

    state_dir = tmp_path / "bootstrap_state"
    monkeypatch.setenv("EDARSAHUB_BOOTSTRAP_STATE", str(state_dir))
    monkeypatch.setenv("EDARSA_ENV", "PREVIEW")
    monkeypatch.delenv("EDARSAHUB_BACKEND_UNHEALTHY_THRESHOLD", raising=False)
    monkeypatch.delenv("EDARSAHUB_SUPERVISOR_RESTART_TIMEOUT", raising=False)
    monkeypatch.delenv("EDARSAHUB_BACKEND_RECOVERY_COOLDOWN", raising=False)

    spec = importlib.util.spec_from_file_location(
        f"edarsahub_bootstrap_watchdog_test_{id(tmp_path)}",
        BOOTSTRAP,
    )
    module = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_transient_probe_timeout_does_not_restart_running_backend(tmp_path, monkeypatch):
    import subprocess

    watchdog = _load_watchdog_for_test(tmp_path, monkeypatch)
    calls: list[list[str]] = []

    def fake_run(args, cwd=None, timeout=60):
        calls.append(list(args))
        if args[0] == "curl":
            return subprocess.CompletedProcess(args, 28, stdout="000")
        if args[:2] == ["supervisorctl", "status"]:
            return subprocess.CompletedProcess(
                args, 0, stdout="backend RUNNING pid 1001, uptime 0:05:00\n"
            )
        raise AssertionError(f"unexpected command: {args}")

    monkeypatch.setattr(watchdog, "run", fake_run)
    outcome = watchdog.maybe_recover_backend()

    assert outcome["state"] == "TRANSIENT_UNHEALTHY"
    assert outcome["restarted"] is False
    assert outcome["consecutive_failures"] == 1
    assert outcome["probe"]["failure_kind"] == "PROBE_TIMEOUT"
    assert not watchdog.BACKEND_RECOVERY_STAMP.exists()
    assert not any(cmd[:2] == ["supervisorctl", "restart"] for cmd in calls)


def test_consecutive_failures_require_threshold_before_restart(tmp_path, monkeypatch):
    import subprocess

    watchdog = _load_watchdog_for_test(tmp_path, monkeypatch)
    restart_calls = 0
    restarted_ok = False

    def fake_run(args, cwd=None, timeout=60):
        nonlocal restart_calls, restarted_ok
        if args[0] == "curl":
            if restarted_ok:
                return subprocess.CompletedProcess(args, 0, stdout="401")
            return subprocess.CompletedProcess(args, 28, stdout="000")
        if args[:2] == ["supervisorctl", "status"]:
            return subprocess.CompletedProcess(
                args, 0, stdout="backend RUNNING pid 1002, uptime 0:05:00\n"
            )
        if args[:2] == ["supervisorctl", "restart"]:
            restart_calls += 1
            restarted_ok = True
            return subprocess.CompletedProcess(args, 0, stdout="backend: started\n")
        raise AssertionError(f"unexpected command: {args}")

    monkeypatch.setattr(watchdog, "run", fake_run)

    first = watchdog.maybe_recover_backend()
    second = watchdog.maybe_recover_backend()
    assert first["state"] == "TRANSIENT_UNHEALTHY"
    assert first["consecutive_failures"] == 1
    assert second["state"] == "TRANSIENT_UNHEALTHY"
    assert second["consecutive_failures"] == 2
    assert restart_calls == 0
    assert not watchdog.BACKEND_RECOVERY_STAMP.exists()

    third = watchdog.maybe_recover_backend()
    assert third["state"] == "RESTART_REQUESTED"
    assert third["restarted"] is True
    assert third["restart_confirmed"] is True
    assert third["consecutive_failures"] == 0
    assert restart_calls == 1
    assert watchdog.BACKEND_RECOVERY_STAMP.exists()


def test_healthy_probe_resets_consecutive_failure_counter(tmp_path, monkeypatch):
    import subprocess

    watchdog = _load_watchdog_for_test(tmp_path, monkeypatch)
    probe_healthy = False
    restart_calls = 0

    def fake_run(args, cwd=None, timeout=60):
        nonlocal restart_calls
        if args[0] == "curl":
            if probe_healthy:
                return subprocess.CompletedProcess(args, 0, stdout="401")
            return subprocess.CompletedProcess(args, 28, stdout="000")
        if args[:2] == ["supervisorctl", "status"]:
            return subprocess.CompletedProcess(
                args, 0, stdout="backend RUNNING pid 1003, uptime 0:05:00\n"
            )
        if args[:2] == ["supervisorctl", "restart"]:
            restart_calls += 1
            return subprocess.CompletedProcess(args, 0, stdout="ok\n")
        raise AssertionError(f"unexpected command: {args}")

    monkeypatch.setattr(watchdog, "run", fake_run)

    assert watchdog.maybe_recover_backend()["consecutive_failures"] == 1
    assert watchdog.maybe_recover_backend()["consecutive_failures"] == 2

    probe_healthy = True
    healthy = watchdog.maybe_recover_backend()
    assert healthy["state"] == "HEALTHY"
    assert healthy["consecutive_failures"] == 0

    probe_healthy = False
    after_healthy = watchdog.maybe_recover_backend()
    assert after_healthy["state"] == "TRANSIENT_UNHEALTHY"
    assert after_healthy["consecutive_failures"] == 1
    assert restart_calls == 0


def test_persistent_unhealthy_route_recovers_after_threshold(tmp_path, monkeypatch):
    import subprocess

    watchdog = _load_watchdog_for_test(tmp_path, monkeypatch)
    restarted = False

    def fake_run(args, cwd=None, timeout=60):
        nonlocal restarted
        if args[0] == "curl":
            code = "401" if restarted else "404"
            return subprocess.CompletedProcess(args, 0, stdout=code)
        if args[:2] == ["supervisorctl", "status"]:
            return subprocess.CompletedProcess(
                args, 0, stdout="backend RUNNING pid 1004, uptime 0:02:00\n"
            )
        if args[:2] == ["supervisorctl", "restart"]:
            restarted = True
            return subprocess.CompletedProcess(args, 0, stdout="backend: started\n")
        raise AssertionError(f"unexpected command: {args}")

    monkeypatch.setattr(watchdog, "run", fake_run)

    assert watchdog.maybe_recover_backend()["restarted"] is False
    assert watchdog.maybe_recover_backend()["restarted"] is False
    third = watchdog.maybe_recover_backend()
    assert third["state"] == "RESTART_REQUESTED"
    assert third["restarted"] is True
    assert third["probe"]["failure_kind"] == "ROUTE_NOT_MOUNTED"


def test_confirmed_stopped_fatal_or_exited_backend_recovers_immediately(tmp_path, monkeypatch):
    import subprocess

    for dead_state in ("STOPPED", "FATAL", "EXITED"):
        sub = tmp_path / dead_state.lower()
        sub.mkdir()
        watchdog = _load_watchdog_for_test(sub, monkeypatch)
        process_up = False
        restart_calls = 0

        def fake_run(args, cwd=None, timeout=60):
            nonlocal process_up, restart_calls
            if args[0] == "curl":
                if process_up:
                    return subprocess.CompletedProcess(args, 0, stdout="401")
                return subprocess.CompletedProcess(args, 7, stdout="000")
            if args[:2] == ["supervisorctl", "status"]:
                if process_up:
                    return subprocess.CompletedProcess(
                        args, 0, stdout="backend RUNNING pid 2001, uptime 0:00:02\n"
                    )
                return subprocess.CompletedProcess(
                    args, 3, stdout=f"backend {dead_state} Nov 17 04:49 AM\n"
                )
            if args[:2] == ["supervisorctl", "restart"]:
                restart_calls += 1
                process_up = True
                return subprocess.CompletedProcess(args, 0, stdout="backend: started\n")
            raise AssertionError(f"unexpected command: {args}")

        monkeypatch.setattr(watchdog, "run", fake_run)
        result = watchdog.maybe_recover_backend()
        assert result["restarted"] is True
        assert result["restart_confirmed"] is True
        assert result["supervisor_state"] == dead_state
        assert restart_calls == 1


def test_cooldown_blocks_running_unhealthy_but_not_confirmed_stopped(tmp_path, monkeypatch):
    import subprocess
    import time

    watchdog = _load_watchdog_for_test(tmp_path, monkeypatch)
    watchdog.STATE.mkdir(parents=True, exist_ok=True)
    watchdog.BACKEND_RECOVERY_STAMP.write_text(
        f"{int(time.time()) - 10}\n", encoding="utf-8"
    )

    sup_state = "RUNNING"
    restarted = False
    restart_calls = 0

    def fake_run(args, cwd=None, timeout=60):
        nonlocal sup_state, restarted, restart_calls
        if args[0] == "curl":
            if restarted:
                return subprocess.CompletedProcess(args, 0, stdout="401")
            return subprocess.CompletedProcess(args, 28, stdout="000")
        if args[:2] == ["supervisorctl", "status"]:
            rc = 0 if sup_state == "RUNNING" else 3
            return subprocess.CompletedProcess(
                args, rc, stdout=f"backend {sup_state} detail\n"
            )
        if args[:2] == ["supervisorctl", "restart"]:
            restart_calls += 1
            restarted = True
            sup_state = "RUNNING"
            return subprocess.CompletedProcess(args, 0, stdout="backend: started\n")
        raise AssertionError(f"unexpected command: {args}")

    monkeypatch.setattr(watchdog, "run", fake_run)

    assert watchdog.maybe_recover_backend()["state"] == "TRANSIENT_UNHEALTHY"
    assert watchdog.maybe_recover_backend()["state"] == "TRANSIENT_UNHEALTHY"
    blocked = watchdog.maybe_recover_backend()
    assert blocked["state"] == "COOLDOWN"
    assert blocked["restarted"] is False
    assert restart_calls == 0

    sup_state = "STOPPED"
    recovered = watchdog.maybe_recover_backend()
    assert recovered["state"] == "RESTART_REQUESTED"
    assert recovered["cooldown_bypassed"] is True
    assert recovered["restarted"] is True
    assert restart_calls == 1


def test_supervisor_restart_timeout_exceeds_stopwaitsecs_and_handles_timeout_expired(
    tmp_path, monkeypatch
):
    import subprocess

    watchdog = _load_watchdog_for_test(tmp_path, monkeypatch)
    assert watchdog.BACKEND_STOPWAITSECS == 30
    assert watchdog.SUPERVISOR_RESTART_TIMEOUT == 65
    assert watchdog.SUPERVISOR_RESTART_TIMEOUT > watchdog.BACKEND_STOPWAITSECS

    sup_conf = Path("/etc/supervisor/conf.d/supervisord.conf")
    if sup_conf.is_file():
        backend_block = sup_conf.read_text(encoding="utf-8").split(
            "[program:backend]", 1
        )[1].split("[program:", 1)[0]
        assert "stopwaitsecs=30" in backend_block
        assert watchdog.SUPERVISOR_RESTART_TIMEOUT > 30

    observed_timeouts: list[int] = []

    def timeout_run(args, cwd=None, timeout=60):
        if args[:2] == ["supervisorctl", "restart"]:
            observed_timeouts.append(timeout)
            raise subprocess.TimeoutExpired(cmd=args, timeout=timeout)
        raise AssertionError(f"unexpected command: {args}")

    monkeypatch.setattr(watchdog, "run", timeout_run)
    assert watchdog.supervisor_restart("WAKE_ROUTE_UNHEALTHY", "backend") is False
    assert observed_timeouts == [65]


def test_regression_unconfirmed_restart_never_poisons_cooldown_stamp(
    tmp_path, monkeypatch
):
    import subprocess

    watchdog = _load_watchdog_for_test(tmp_path, monkeypatch)
    attempt = 0
    sup_state = "RUNNING"
    healthy_after = False

    def fake_run(args, cwd=None, timeout=60):
        nonlocal attempt, sup_state, healthy_after
        if args[0] == "curl":
            if healthy_after:
                return subprocess.CompletedProcess(args, 0, stdout="401")
            return subprocess.CompletedProcess(args, 28, stdout="000")
        if args[:2] == ["supervisorctl", "status"]:
            rc = 0 if sup_state == "RUNNING" else 3
            return subprocess.CompletedProcess(
                args, rc, stdout=f"backend {sup_state} info\n"
            )
        if args[:2] == ["supervisorctl", "restart"]:
            attempt += 1
            if attempt == 1:
                sup_state = "STOPPED"
                raise subprocess.TimeoutExpired(cmd=args, timeout=timeout)
            sup_state = "RUNNING"
            healthy_after = True
            return subprocess.CompletedProcess(args, 0, stdout="backend: started\n")
        raise AssertionError(f"unexpected command: {args}")

    monkeypatch.setattr(watchdog, "run", fake_run)

    assert watchdog.maybe_recover_backend()["restarted"] is False
    assert watchdog.maybe_recover_backend()["restarted"] is False
    failed = watchdog.maybe_recover_backend()
    assert failed["state"] == "RESTART_FAILED"
    assert failed["restarted"] is False
    assert failed["restart_confirmed"] is False
    assert not watchdog.BACKEND_RECOVERY_STAMP.exists()

    recovered = watchdog.maybe_recover_backend()
    assert recovered["state"] == "RESTART_REQUESTED"
    assert recovered["restarted"] is True
    assert recovered["restart_confirmed"] is True
    assert watchdog.BACKEND_RECOVERY_STAMP.exists()
