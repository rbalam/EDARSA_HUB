from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONTROL = ROOT / "tools" / "mirror_sync" / "worker_control_plane.py"
MIRROR = ROOT / "tools" / "mirror_sync" / "mirror_sync_worker.sh"


def test_control_plane_is_independent_and_supervised():
    control = CONTROL.read_text(encoding="utf-8")
    mirror = MIRROR.read_text(encoding="utf-8")

    assert "edarsahub.worker-control-plane.v1" in control

    # Supervisor owns the control-plane lifecycle independently.
    assert "start_control_plane" not in mirror
    assert "ensure_control_plane" not in mirror
    assert "stop_control_plane" not in mirror
    assert "CONTROL_PLANE_STARTED=YES" not in mirror


def test_orphan_claims_are_quarantined_not_deleted():
    text = CONTROL.read_text(encoding="utf-8")
    assert "AGENT_GUARD_ORPHAN_QUARANTINED" in text
    assert "shutil.move" in text
    assert "pid_alive" in text
    assert "CLAIM_GRACE" in text
    assert "unlink(" not in text


def test_runtime_self_heal_detects_generation_heartbeat_and_pid():
    text = CONTROL.read_text(encoding="utf-8")
    assert "GENERATION_STALE" in text
    assert "HEARTBEAT_STALE" in text
    assert "PID_DEAD" in text
    assert "request_universal_restart" in text
    assert "last_receive_utc" in text


def test_worktree_recovery_is_preserving_and_fast_forward_only():
    text = CONTROL.read_text(encoding="utf-8")

    # El contrato FF autoritativo usa rev-list para comprobar
    # que local no tenga commits exclusivos y que remoto esté adelante.
    assert '"rev-list", "--left-right", "--count"' in text
    assert "local_ahead != 0 or remote_ahead <= 0" in text

    assert "DEFER_LOCAL_DIRTY" in text
    assert "FAST_FORWARD_DEFERRED_LOCAL_DIRTY" in text

    assert '"stash", "push", "--include-untracked"' not in text
    assert '"reset"' not in text
    assert '"clean"' not in text
    assert '"rebase"' not in text

    assert "FAST_FORWARD_APPLIED" in text
    assert "SKIP_NON_FF" in text


def test_stale_processing_is_idempotently_requeued():
    text = CONTROL.read_text(encoding="utf-8")
    assert "STALE_PROCESSING_REQUEUED" in text
    assert "if target.exists()" in text
    assert "os.replace(path, target)" in text


def test_production_is_explicitly_out_of_scope():
    text = CONTROL.read_text(encoding="utf-8")
    assert '"production_touched": False' in text
    assert "Edarsahub_Produccion" not in text
