"""Deterministic safety checks for the existing commercial clock recovery gate."""
import datetime as dt
import importlib.util
from pathlib import Path

PATH = Path(__file__).resolve().parents[1] / "tools" / "commercial_clock_recovery.py"
spec = importlib.util.spec_from_file_location("commercial_clock_recovery", PATH)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
NOW = dt.datetime(2026, 11, 11, 20, 30, tzinfo=dt.timezone.utc)


def run_record(age: int, *, status="completed", conclusion="success", event="workflow_dispatch"):
    created = NOW - dt.timedelta(seconds=age)
    return {
        "event": event, "status": status, "conclusion": conclusion,
        "created_at": created.isoformat().replace("+00:00", "Z"),
    }


def test_normal_dispatch_preserved():
    assert module.decision("workflow_dispatch", [], NOW, 420) == (True, "NORMAL_DISPATCH")


def test_recent_cycle_skips_backup():
    assert module.decision("schedule", [run_record(301)], NOW, 420) == (False, "DISPATCH_RECENT")


def test_stale_cycle_recovers():
    assert module.decision("schedule", [run_record(421)], NOW, 420) == (True, "DISPATCH_STALE")


def test_startup_failure_recovers_without_waiting_for_staleness():
    assert module.decision("schedule", [run_record(12, conclusion="startup_failure")], NOW, 420) == (True, "PREVIOUS_STARTUP_FAILURE")


def test_any_running_owner_blocks_recovery():
    assert module.decision("schedule", [run_record(900), run_record(20, status="in_progress", conclusion=None)], NOW, 420) == (False, "OWNER_RUN_ACTIVE")


def test_no_dispatch_is_not_healthy():
    assert module.decision("schedule", [run_record(3600, event="schedule")], NOW, 420) == (True, "NO_PREVIOUS_DISPATCH")


def test_clock_skew_blocks_recovery():
    assert module.decision("schedule", [run_record(-60)], NOW, 420) == (False, "CLOCK_SKEW")


def test_recovery_never_reads_untrusted_workflow_identity():
    import pytest
    with pytest.raises(ValueError, match="UNAUTHORIZED"):
        module.load_runs("someone/other", "commercial-open-sales-clock.yml", "token")
    with pytest.raises(ValueError, match="UNAUTHORIZED"):
        module.load_runs(module.EXPECTED_REPO, "unknown.yml", "token")
