from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

CONF = ROOT / "tools/mirror_sync/edarsahub-universal-worker.conf"
MIRROR = ROOT / "tools/mirror_sync/mirror_sync_worker.sh"
BOOTSTRAP = ROOT / "tools/bootstrap/edarsahub_bootstrap_watchdog.py"


def text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_external_owner_is_supervisor_managed():
    body = text(CONF)

    assert "[program:edarsahub-universal-worker]" in body
    assert (
        "command=/bin/bash "
        "/app/tools/mirror_sync/universal_job_worker.sh"
        in body
    )
    assert "autostart=true" in body
    assert "autorestart=true" in body
    assert "startsecs=3" in body
    assert "stopsignal=TERM" in body
    assert "stopwaitsecs=20" in body


def test_external_owner_has_canonical_runtime_intervals():
    body = text(CONF)

    assert 'UNIVERSAL_WORKER_INTAKE_SECONDS="5"' in body
    assert 'UNIVERSAL_WORKER_RESULT_SECONDS="5"' in body
    assert 'UNIVERSAL_WORKER_HEALTH_SECONDS="30"' in body
    assert 'UNIVERSAL_WORKER_RECONCILE_SECONDS="30"' in body
    assert 'UNIVERSAL_WORKER_DISPATCH_IDLE_SECONDS="2"' in body


def test_mirror_does_not_spawn_universal_worker():
    body = text(MIRROR)

    assert "UNIVERSAL_JOB_WORKER_START_BY_MIRROR=FORBIDDEN" in body
    assert "UNIVERSAL_JOB_WORKER_OWNERSHIP=EXTERNAL" in body
    assert "canonical_universal_worker_pid" in body

    forbidden = '/bin/bash "$UNIVERSAL_WORKER" & UNIVERSAL_PID=$!'
    assert forbidden not in body


def test_bootstrap_is_independent_stale_worker_recovery_fallback():
    body = text(BOOTSTRAP)

    assert "WORKER_HEARTBEAT_STALE" in body
    assert "BOOTSTRAP_WATCHDOG_SUPERVISOR_FALLBACK" in body
    assert "UNIVERSAL_WORKER_STALE_RECOVERY" in body
    assert 'supervisor_restart("WORKER_HEARTBEAT_STALE", WORKER_SERVICE)' in body
