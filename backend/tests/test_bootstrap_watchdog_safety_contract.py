from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BOOTSTRAP = ROOT / "tools/bootstrap/edarsahub_bootstrap_watchdog.py"


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


def test_bootstrap_does_not_own_universal_worker_restart():
    text = body()

    assert "DEFER_TO_CANONICAL_WORKER_OWNER" in text
    assert "EXTERNAL_CANONICAL_OWNER" in text
    assert 'supervisor_restart("WORKER_HEARTBEAT_STALE")' not in text


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
