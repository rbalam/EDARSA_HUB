from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

WORKER = ROOT / "tools/mirror_sync/mirror_sync_worker.sh"
LAUNCHER = ROOT / "tools/mirror_sync/mirror_sync_supervisor_entrypoint.sh"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_worker_prefers_repository_virtualenv():
    text = read(WORKER)

    assert '$ROOT/.venv/bin/python' in text
    assert 'PYTHON_BIN="$(resolve_worker_python)"' in text
    assert "EDARSAHUB_WORKER_PYTHON" not in text

    assert (
        "command -v python3 2>/dev/null || "
        "command -v python 2>/dev/null || true"
    ) in text

    assert "ABORT=WORKER_PYTHON_NOT_EXECUTABLE" in text


def test_universal_worker_tools_use_canonical_python():
    text = read(WORKER)

    expected = (
        'run_tool "UNIVERSAL_JOB_BRIDGE" '
        '"$PYTHON_BIN" "$UNIVERSAL_BRIDGE" receive',
        'run_tool "UNIVERSAL_JOB_DISPATCHER" '
        '"$PYTHON_BIN" "$UNIVERSAL_DISPATCHER"',
        'run_tool "UNIVERSAL_JOB_RESULT_PUBLISHER" '
        '"$PYTHON_BIN" "$UNIVERSAL_RESULT_PUBLISHER"',
        'run_tool "RUNTIME_HEALTH_PUBLISHER" '
        '"$PYTHON_BIN" "$RUNTIME_HEALTH_PUBLISHER"',
    )

    for command in expected:
        assert command in text

    assert 'run_tool "UNIVERSAL_JOB_BRIDGE" python3' not in text
    assert 'run_tool "UNIVERSAL_JOB_DISPATCHER" python3' not in text
    assert 'run_tool "UNIVERSAL_JOB_RESULT_PUBLISHER" python3' not in text
    assert 'run_tool "RUNTIME_HEALTH_PUBLISHER" python3' not in text


def test_launcher_uses_same_canonical_python_contract():
    text = read(LAUNCHER)

    assert '$ROOT/.venv/bin/python' in text
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
    for text in (read(WORKER), read(LAUNCHER)):
        assert "/usr/bin/python3" not in text
        assert "/usr/local/bin/python3" not in text
