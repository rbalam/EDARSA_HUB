from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

WORKER = ROOT / "tools/mirror_sync/mirror_sync_worker.sh"
UNIVERSAL_WORKER = ROOT / "tools/mirror_sync/universal_job_worker.sh"
LAUNCHER = ROOT / "tools/mirror_sync/mirror_sync_supervisor_entrypoint.sh"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_worker_prefers_runtime_virtualenv():
    text = read(WORKER)

    assert '"/root/.venv/bin/python"' in text
    assert 'PYTHON_BIN="$(resolve_worker_python)"' in text
    assert "EDARSAHUB_WORKER_PYTHON" not in text

    assert (
        "command -v python3 2>/dev/null || "
        "command -v python 2>/dev/null || true"
    ) in text

    assert "ABORT=WORKER_PYTHON_NOT_EXECUTABLE" in text


def test_universal_worker_tools_use_canonical_python():
    mirror_text = read(WORKER)
    universal_text = read(UNIVERSAL_WORKER)

    # Universal Worker is externally owned by Supervisor.
    assert 'UNIVERSAL_WORKER="$DIR/universal_job_worker.sh"' in mirror_text
    assert "UNIVERSAL_JOB_WORKER_OWNERSHIP=EXTERNAL" in mirror_text
    assert "UNIVERSAL_JOB_WORKER_START_BY_MIRROR=FORBIDDEN" in mirror_text

    expected = (
        'run_tool "UNIVERSAL_JOB_BRIDGE" 45 '
        '"$PYTHON_BIN" "$BRIDGE" receive',
        'run_tool "UNIVERSAL_JOB_DISPATCHER" '
        '"${UNIVERSAL_DISPATCH_TIMEOUT_SECONDS:-1900}" '
        '"$PYTHON_BIN" "$DISPATCHER"',
        'run_tool "UNIVERSAL_JOB_RESULT_PUBLISHER" '
        '"${UNIVERSAL_RESULT_PUBLISH_TIMEOUT_SECONDS:-180}" '
        '"$PYTHON_BIN" "$RESULT_PUBLISHER"',
        'run_tool "RUNTIME_HEALTH_PUBLISHER" '
        '"${UNIVERSAL_HEALTH_TIMEOUT_SECONDS:-60}" '
        '"$PYTHON_BIN" "$HEALTH_PUBLISHER"',
    )

    for command in expected:
        assert command in universal_text

    assert '$ROOT/.venv/bin/python' in universal_text
    assert 'PYTHON_BIN="$(resolve_worker_python)"' in universal_text

    assert 'python3 "$BRIDGE"' not in universal_text
    assert 'python3 "$DISPATCHER"' not in universal_text
    assert 'python3 "$RESULT_PUBLISHER"' not in universal_text
    assert 'python3 "$HEALTH_PUBLISHER"' not in universal_text


def test_launcher_uses_same_runtime_python_contract():
    text = read(LAUNCHER)

    assert '"/root/.venv/bin/python"' in text
    assert 'PYTHON_BIN="$(resolve_worker_python)"' in text
    assert "EDARSAHUB_WORKER_PYTHON" not in text

    assert (
        "command -v python3 2>/dev/null || "
        "command -v python 2>/dev/null || true"
    ) in text

    assert (
        '"$PYTHON_BIN" "$HEALTH" '
        '>/tmp/edarsahub-worker-health-launcher.log'
    ) in text

    assert (
        'python3 "$HEALTH" '
        '>/tmp/edarsahub-worker-health-launcher.log'
    ) not in text


def test_runtime_scripts_do_not_hardcode_system_python():
    for text in (
        read(WORKER),
        read(UNIVERSAL_WORKER),
        read(LAUNCHER),
    ):
        assert "/usr/bin/python3" not in text
        assert "/usr/local/bin/python3" not in text
