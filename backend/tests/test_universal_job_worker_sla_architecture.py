from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WORKER = ROOT / "tools" / "mirror_sync" / "universal_job_worker.sh"


def source() -> str:
    return WORKER.read_text(encoding="utf-8")


def test_intake_is_decoupled_from_dispatch():
    text = source()
    assert "intake_loop &" in text
    assert "dispatch_loop &" in text
    assert "result_loop &" in text
    assert "health_loop &" in text


def test_long_dispatch_timeout_cannot_define_intake_frequency():
    text = source()
    assert 'INTAKE_SECONDS="${UNIVERSAL_WORKER_INTAKE_SECONDS:-10}"' in text
    assert 'UNIVERSAL_DISPATCH_TIMEOUT_SECONDS:-1900' in text
    assert "sleep \"$INTAKE_SECONDS\"" in text


def test_default_intake_sla_is_below_thirty_seconds():
    text = source()
    assert 'UNIVERSAL_WORKER_INTAKE_SECONDS:-10' in text


def test_health_and_results_are_independent_of_dispatch():
    text = source()
    assert 'UNIVERSAL_WORKER_RESULT_SECONDS:-10' in text
    assert 'UNIVERSAL_WORKER_HEALTH_SECONDS:-30' in text


def test_worker_tools_are_isolated_and_terminated_by_process_group():
    text = source()
    assert 'SETSID_BIN="$(command -v setsid' in text
    assert '"$SETSID_BIN" --wait timeout' in text
    assert 'ACTIVE_TOOL_PGID="$TOOL_PID"' in text
    assert 'kill -TERM -- "-$ACTIVE_TOOL_PGID"' in text
    assert "trap shutdown_child_loop TERM INT HUP" in text
