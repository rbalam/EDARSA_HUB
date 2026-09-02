from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

MIRROR = ROOT / "tools" / "mirror_sync" / "mirror_sync_worker.sh"
CONTROL = ROOT / "tools" / "mirror_sync" / "worker_control_plane.py"


def test_mirror_does_not_spawn_universal_worker():
    text = MIRROR.read_text(encoding="utf-8")

    assert "UNIVERSAL_JOB_WORKER_START_BY_MIRROR=FORBIDDEN" in text
    assert "UNIVERSAL_JOB_WORKER_OWNERSHIP=EXTERNAL" in text
    assert 'canonical_universal_worker_pid' in text

    forbidden = '/bin/bash "$UNIVERSAL_WORKER" & UNIVERSAL_PID=$!'
    assert forbidden not in text


def test_mirror_adopts_runtime_pid():
    text = MIRROR.read_text(encoding="utf-8")

    assert '"$UNIVERSAL_STATE/pid"' in text
    assert 'kill -0 "$pid"' in text
    assert "universal_job_worker.sh" in text


def test_control_plane_dirty_app_defers():
    text = CONTROL.read_text(encoding="utf-8")

    assert "DEFER_LOCAL_DIRTY" in text
    assert "FAST_FORWARD_DEFERRED_LOCAL_DIRTY" in text
    assert '"status", "--porcelain=v1", "--untracked-files=all"' in text


def test_control_plane_never_stashes_shared_app():
    text = CONTROL.read_text(encoding="utf-8")

    assert '["git", "stash"' not in text
    assert "stash push" not in text
