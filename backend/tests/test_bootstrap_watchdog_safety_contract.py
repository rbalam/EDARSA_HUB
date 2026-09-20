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
    assert text.index('git status --porcelain=v1 --untracked-files=all') < text.index('rm -f "$PERSISTENT_STOP" "$TEMP_STOP"')
    assert "MIRROR_SYNC_HEALTH_GATE=PASS" in text
