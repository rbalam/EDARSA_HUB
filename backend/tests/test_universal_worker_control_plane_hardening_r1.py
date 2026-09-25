from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github" / "workflows" / "worker-runtime-recovery-probe.yml"
DISPATCHER = ROOT / "tools" / "mirror_sync" / "universal_job_dispatcher.py"
PUBLISHER = ROOT / "tools" / "mirror_sync" / "universal_job_result_publisher.py"
PROTOCOL = ROOT / "docs" / "operacion" / "WORKER_JOB_EXECUTION_PROTOCOL.md"


def test_recovery_probe_no_longer_uses_development_push_trigger():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "schedule:" in text
    assert "workflow_dispatch:" in text
    assert "preferred_job_id:" in text
    assert "branches:\n      - Edarsahub_Desarrollo" not in text
    assert "worker_queue/triggers/runtime-recovery/**" not in text


def test_dispatcher_safe_replays_remote_move_after_cas():
    text = DISPATCHER.read_text(encoding="utf-8")
    process = text.split("def process_one(", 1)[1].split("def dispatch(", 1)[0]
    assert 'terminal in {"REMOTE_MOVED_RETRY_REQUIRED", "GIT_PUSH_FAILED"}' in process
    assert "git_changed_paths(execution_base_sha, remote_now)" in process
    assert "evaluate_scope_advance(" in process
    assert 'replay_policy.get("decision") == "SAFE_REPLAY"' in process
    assert "execution_base_sha = remote_now" in process
    assert 'result["status"] = "CONCURRENT_SCOPE_CONFLICT"' in process


def test_dispatcher_integration_still_forbids_history_rewriting():
    text = DISPATCHER.read_text(encoding="utf-8")
    integrate = text.split("def integrate(", 1)[1].split("def release_agent_guard_claim", 1)[0]
    for forbidden in ('git("merge"', 'git("rebase"', 'git("cherry-pick"', "force-with-lease"):
        assert forbidden not in integrate


def test_result_publisher_exposes_bridge_rejections():
    text = PUBLISHER.read_text(encoding="utf-8")
    assert 'REJECTED = STATE / "rejected"' in text
    assert "def publishable_paths()" in text
    assert 'REJECTED.glob("*.json")' in text
    assert 'RESULTS.glob("*.json")' in text
    assert '"reasons"' in text
    assert '"received_at_utc"' in text


def test_protocol_forbids_wake_commits_on_development():
    text = PROTOCOL.read_text(encoding="utf-8")
    assert "No crear commits de wake en `Edarsahub_Desarrollo`" in text
    assert "Worker Requests Wake" in text
