from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BRIDGE = ROOT / 'tools/mirror_sync/universal_job_bridge.py'
DISPATCHER = ROOT / 'tools/mirror_sync/universal_job_dispatcher.py'
CONTROL = ROOT / 'tools/mirror_sync/worker_control_plane.py'
HEALTH = ROOT / 'tools/mirror_sync/runtime_health_publisher.py'


def test_inbox_is_history_and_results_deduplicate_jobs():
    text = BRIDGE.read_text(encoding='utf-8')
    assert 'for folder in (PENDING, PROCESSING, DONE, RESULTS)' in text
    assert 'worker_queue/inbox is immutable audit history' in text
    assert 'REJECTED is evaluated' in text


def test_dispatcher_tracks_runtime_and_only_releases_created_claims():
    text = DISPATCHER.read_text(encoding='utf-8')
    assert 'agent_guard_claim_created = False' in text
    assert 'agent_guard_claim_created = True' in text
    assert 'if agent_guard_claim_created:' in text
    assert 'agent_guard_release"] = "NOT_REQUIRED"' in text
    assert 'current_job_id' in text
    assert 'last_terminal_utc' in text


def test_dispatcher_uses_serial_slot_runtime_without_parallel_execution():
    text = DISPATCHER.read_text(encoding='utf-8')
    assert 'from worker_slot_runtime import create_slot, release_slot, update_slot_state' in text
    assert 'slot_id = "readonly-1" if slot_class == "READ_ONLY" else "mutation-1"' in text
    assert 'create_slot(' in text
    assert 'update_slot_state(slot_id, "RUNNING"' in text
    assert 'update_slot_state(slot_id, "TERMINALIZING"' in text
    assert 'release_slot(slot_id)' in text
    assert 'result["parallel_execution_enabled"] = False' in text


def test_dispatcher_claim_is_atomic_and_execution_is_outside_lock():
    text = DISPATCHER.read_text(encoding='utf-8')
    assert 'def claim_one() -> Path | None:' in text
    assert 'with LOCK_FILE.open("a+") as lock:' in text
    assert 'os.replace(selected, processing)' in text
    assert 'return process_one(claimed, already_claimed=True)' in text
    claim_start = text.index('def claim_one() -> Path | None:')
    dispatch_start = text.index('def dispatch() -> int:')
    claim_block = text[claim_start:dispatch_start]
    assert 'process_one(' not in claim_block


def test_preferred_job_is_boost_not_global_freeze():
    text = DISPATCHER.read_text(encoding='utf-8')
    assert 'PREFERRED_JOB_STALE_IGNORED' in text
    assert 'WAITING_PREFERRED_JOB' not in text
    assert 'return jobs[0], False' in text


def test_stale_processing_is_requeued_once_then_terminal():
    text = CONTROL.read_text(encoding='utf-8')
    assert '_worker_stale_requeue_count' in text
    assert 'retry_count >= 1' in text
    assert 'processing_stale_after_single_requeue' in text


def test_health_exposes_sla_metrics():
    text = HEALTH.read_text(encoding='utf-8')
    for token in ('queue_depth','oldest_pending_age_seconds','intake_sla_seconds','intake_sla_breached','current_job_id','last_terminal_utc'):
        assert token in text
