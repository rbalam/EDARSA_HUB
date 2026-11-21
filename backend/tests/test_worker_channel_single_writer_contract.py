from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

TOOLS = ROOT / "tools" / "mirror_sync"

REQUEST_WRITER = TOOLS / "gate_chain_publisher.py"
RESULT_WRITER = TOOLS / "universal_job_result_publisher.py"
HEALTH_WRITER = TOOLS / "runtime_health_publisher.py"

CANONICAL_WRITERS = {
    "worker/requests": REQUEST_WRITER,
    "worker/results": RESULT_WRITER,
    "worker/health": HEALTH_WRITER,
}


def source(path: Path) -> str:
    return path.read_text(
        encoding="utf-8",
        errors="replace",
    )


def test_request_writer_contract_is_canonical():
    text = source(REQUEST_WRITER)

    assert "worker/requests" in text
    assert "authorized_push(" in text
    assert "worktree-create" in text
    assert "worker_queue_publication" in text

    assert "--no-verify" not in text
    assert "--force" not in text
    assert "force-with-lease" not in text


def test_result_writer_contract_is_canonical():
    text = source(RESULT_WRITER)

    assert "worker/results" in text
    assert "publish_one" in text

    assert "--no-verify" not in text
    assert "--force" not in text
    assert "force-with-lease" not in text


def test_health_writer_contract_is_canonical():
    text = source(HEALTH_WRITER)

    assert "worker/health" in text
    assert "production_touched" in text

    assert "--no-verify" not in text
    assert "--force" not in text
    assert "force-with-lease" not in text


def test_request_publication_has_exact_scope_and_agent_guard():
    text = source(REQUEST_WRITER)

    assert 'f"worker_queue/inbox/{job_id}.json"' in text
    assert "validate_commit_scope(" in text
    assert '"worktree-create"' in text
    assert '"release"' in text


def test_request_publication_has_optimistic_concurrency():
    text = source(REQUEST_WRITER)

    assert "_queue_remote_head(" in text
    assert "REMOTE_MOVED_RETRY_REQUIRED" in text
    assert "QUEUE_PUBLISHER_LINEAGE_INVALID" in text


def test_request_publisher_is_idempotent():
    text = source(REQUEST_WRITER)

    assert "REMOTE_JOB=EXISTS" in text
    assert '"cat-file",' in text


def test_channel_roles_remain_distinct():
    request = source(REQUEST_WRITER)
    result = source(RESULT_WRITER)
    health = source(HEALTH_WRITER)

    # These assertions define ownership behavior,
    # not mere knowledge of another branch.
    assert "worker_queue_publication" in request
    assert "publish_one" in result
    assert "production_touched" in health

    # Request publisher must not publish result/health payloads.
    assert "publish_one(" not in request
    assert "runtime_summary(" not in request


def test_no_parallel_workerctl_control_plane():
    workerctl = TOOLS / "workerctl.py"

    assert not workerctl.exists()


def test_existing_control_plane_remains_canonical():
    control = TOOLS / "worker_control_plane.py"
    text = source(control)

    assert control.is_file()
    assert "production_touched" in text
