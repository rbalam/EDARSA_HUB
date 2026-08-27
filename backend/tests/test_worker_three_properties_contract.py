from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WORKER = ROOT / "tools" / "mirror_sync" / "universal_job_worker.sh"
RECONCILER = ROOT / "tools" / "mirror_sync" / "worker_runtime_reconciler.py"
DISPATCHER = ROOT / "tools" / "mirror_sync" / "universal_job_dispatcher.py"
PUBLISHER = ROOT / "tools" / "mirror_sync" / "universal_job_result_publisher.py"
HEALTH = ROOT / "tools" / "mirror_sync" / "runtime_health_publisher.py"


def text(path):
    return path.read_text(encoding="utf-8")


def test_property_1_intake_is_independent_and_fast():
    source = text(WORKER)
    assert 'INTAKE_SECONDS="${UNIVERSAL_WORKER_INTAKE_SECONDS:-10}"' in source
    assert "intake_loop &" in source
    assert "dispatch_loop &" in source
    assert "result_loop &" in source
    assert "receive_once" in source


def test_property_2_self_heal_is_safe_not_age_only():
    source = text(RECONCILER)
    assert "recover_orphan_processing" in source
    assert "reconcile_claims" in source
    assert "claim_terminal" in source
    assert "process_references" in source
    assert "worktree_clean" in source
    assert "CLAIM_NOT_STALE" in source
    assert "WORK_NOT_TERMINAL_OR_INTEGRATED" in source
    assert "LIVE_PROCESS_REFERENCES_WORKTREE" in source
    assert "WORKTREE_NOT_CLEAN" in source
    worker = text(WORKER)
    assert "reconcile_loop &" in worker


def test_property_3_terminal_result_pipeline_is_mandatory():
    dispatcher = text(DISPATCHER)
    publisher = text(PUBLISHER)
    assert '"status": "BLOCKED"' in dispatcher
    assert "RESULTS" in dispatcher and "write_json" in dispatcher
    assert "UNIVERSAL_RESULTS_PUBLISH_ERROR_COUNT" in publisher
    assert "return 1 if errors else 0" in publisher


def test_remote_health_exposes_runtime_and_blocking_state():
    health = text(HEALTH)
    assert "last_cycle_utc" in health
    assert "last_receive_utc" in health
    assert '"BLOCKED"' in health
    assert '"REJECTED"' in health
    assert '"RESULT_READY"' in health
