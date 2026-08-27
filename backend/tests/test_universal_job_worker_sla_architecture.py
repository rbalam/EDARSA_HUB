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
