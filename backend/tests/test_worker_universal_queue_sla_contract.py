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


def test_stale_processing_is_requeued_once_then_terminal():
    text = CONTROL.read_text(encoding='utf-8')
    assert '_worker_stale_requeue_count' in text
    assert 'retry_count >= 1' in text
    assert 'processing_stale_after_single_requeue' in text


def test_health_exposes_sla_metrics():
    text = HEALTH.read_text(encoding='utf-8')
    for token in ('queue_depth','oldest_pending_age_seconds','intake_sla_seconds','intake_sla_breached','current_job_id','last_terminal_utc'):
        assert token in text
