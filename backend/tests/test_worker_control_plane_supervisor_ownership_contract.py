from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

CONTROL = ROOT / "tools/mirror_sync/worker_control_plane.py"
CONTROL_CONF = ROOT / "tools/mirror_sync/edarsahub-worker-control-plane.conf"
MIRROR = ROOT / "tools/mirror_sync/mirror_sync_worker.sh"
INSTALLER = ROOT / "tools/bootstrap/install_bootstrap_watchdog.sh"


def test_control_plane_has_dedicated_supervisor_owner():
    conf = CONTROL_CONF.read_text(encoding="utf-8")

    assert "[program:edarsahub-worker-control-plane]" in conf
    assert (
        "command=/root/.venv/bin/python "
        "/app/tools/mirror_sync/worker_control_plane.py"
    ) in conf
    assert "autostart=true" in conf
    assert "autorestart=true" in conf
    assert 'EDARSAHUB_CONTROL_PLANE_INTERVAL="15"' in conf


def test_mirror_no_longer_owns_control_plane_lifecycle():
    mirror = MIRROR.read_text(encoding="utf-8")

    forbidden = (
        'CONTROL_PLANE="$DIR/worker_control_plane.py"',
        'CONTROL_PID=""',
        "start_control_plane(){",
        "ensure_control_plane(){",
        "stop_control_plane(){",
        "CONTROL_PLANE_STARTED=YES",
    )

    for token in forbidden:
        assert token not in mirror


def test_bootstrap_installs_and_owns_control_plane_service():
    installer = INSTALLER.read_text(encoding="utf-8")

    assert (
        'CONTROL_PLANE_SERVICE="edarsahub-worker-control-plane"'
        in installer
    )
    assert (
        'edarsahub-worker-control-plane.conf'
        in installer
    )
    assert (
        'supervisorctl restart "$CONTROL_PLANE_SERVICE" '
        '|| supervisorctl start "$CONTROL_PLANE_SERVICE"'
        in installer
    )
    assert 'supervisorctl status "$CONTROL_PLANE_SERVICE"' in installer


def test_mirror_fail_closed_contract_is_preserved():
    mirror = MIRROR.read_text(encoding="utf-8")

    assert 'PERSISTENT_STOP="$STATE_DIR/STOP"' in mirror
    assert 'ENABLE_FLAG="$STATE_DIR/ENABLED"' in mirror
    assert "is_authorized()" in mirror

    # Mirror may observe Universal Worker ownership but never start it.
    assert "UNIVERSAL_JOB_WORKER_OWNERSHIP=EXTERNAL" in mirror
    assert "UNIVERSAL_JOB_WORKER_START_BY_MIRROR=FORBIDDEN" in mirror


def test_control_plane_remains_production_fail_closed():
    control = CONTROL.read_text(encoding="utf-8")

    assert '"production_touched": False' in control
    assert "Edarsahub_Produccion" not in control
