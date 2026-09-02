from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PUBLISHER = ROOT / "tools/mirror_sync/universal_job_result_publisher.py"
BRIDGE = ROOT / "tools/mirror_sync/universal_job_bridge.py"


def test_result_publisher_uses_dedicated_result_branch():
    text = PUBLISHER.read_text(encoding="utf-8")

    assert 'RESULT_BRANCH = os.environ.get(' in text
    assert '"worker/results"' in text

    # Result publication must not push to request intake.
    assert 'refs/heads/{QUEUE_BRANCH}' not in text
    assert 'refs/heads/{RESULT_BRANCH}' in text


def test_request_bridge_remains_on_worker_requests():
    text = BRIDGE.read_text(encoding="utf-8")

    assert (
        'QUEUE_BRANCH = os.environ.get('
        '"EDARSAHUB_QUEUE_BRANCH", "worker/requests")'
        in text
    )
    assert '"worker_queue/inbox"' in text


def test_request_and_result_branches_are_distinct_contracts():
    publisher = PUBLISHER.read_text(encoding="utf-8")

    assert '"worker/requests"' in publisher
    assert '"worker/results"' in publisher
    assert "RESULT_BRANCH" in publisher
