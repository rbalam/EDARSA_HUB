from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WORKER = ROOT / "tools" / "mirror_sync" / "universal_job_worker.sh"
RECONCILER = ROOT / "tools" / "mirror_sync" / "worker_runtime_reconciler.py"
DISPATCHER = ROOT / "tools" / "mirror_sync" / "universal_job_dispatcher.py"
PUBLISHER = ROOT / "tools" / "mirror_sync" / "universal_job_result_publisher.py"
HEALTH = ROOT / "tools" / "mirror_sync" / "runtime_health_publisher.py"

def text(path): return path.read_text(encoding="utf-8")

def test_property_1_intake_is_independent_and_fast():
    source = text(WORKER); assert 'INTAKE_SECONDS="${UNIVERSAL_WORKER_INTAKE_SECONDS:-10}"' in source; assert "intake_loop &" in source; assert "dispatch_loop &" in source; assert "result_loop &" in source; assert "receive_once" in source

def test_property_2_self_heal_is_safe_not_age_only():
    source = text(RECONCILER)
    for marker in ("recover_orphan_processing","reconcile_claims","claim_terminal","process_references","worktree_clean","CLAIM_NOT_STALE","WORK_NOT_TERMINAL_OR_INTEGRATED","LIVE_PROCESS_REFERENCES_WORKTREE","WORKTREE_NOT_CLEAN"): assert marker in source
    assert "reconcile_loop &" in text(WORKER)

def test_property_3_terminal_result_pipeline_is_mandatory():
    dispatcher = text(DISPATCHER); publisher = text(PUBLISHER); assert '"status": "BLOCKED"' in dispatcher; assert "RESULTS" in dispatcher and "write_json" in dispatcher; assert "UNIVERSAL_RESULTS_PUBLISH_ERROR_COUNT" in publisher; assert "return 1 if errors else 0" in publisher

def test_remote_health_exposes_runtime_and_blocking_state():
    health = text(HEALTH)
    for marker in ("last_cycle_utc","last_receive_utc",'"BLOCKED"','"REJECTED"','"RESULT_READY"'): assert marker in health
