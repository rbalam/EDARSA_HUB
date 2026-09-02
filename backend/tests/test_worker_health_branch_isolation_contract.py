from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

HEALTH = (
    ROOT
    / "tools"
    / "mirror_sync"
    / "runtime_health_publisher.py"
)

RESULT = (
    ROOT
    / "tools"
    / "mirror_sync"
    / "universal_job_result_publisher.py"
)

BRIDGE = (
    ROOT
    / "tools"
    / "mirror_sync"
    / "universal_job_bridge.py"
)


def test_health_uses_dedicated_health_branch():
    text = HEALTH.read_text(encoding="utf-8")

    assert "HEALTH_BRANCH" in text
    assert '"worker/health"' in text
    assert 'refs/heads/{HEALTH_BRANCH}' in text

    assert 'refs/heads/{BRANCH}' not in text
    assert 'git("fetch", REMOTE, BRANCH)' not in text


def test_result_publisher_uses_results_branch():
    text = RESULT.read_text(encoding="utf-8")

    assert "RESULT_BRANCH" in text
    assert '"worker/results"' in text
    assert 'refs/heads/{RESULT_BRANCH}' in text


def test_bridge_keeps_request_branch_for_intake():
    text = BRIDGE.read_text(encoding="utf-8")

    assert '"worker/requests"' in text
    assert "worker_queue/inbox" in text


def test_channels_are_separated():
    health = HEALTH.read_text(encoding="utf-8")
    result = RESULT.read_text(encoding="utf-8")

    assert '"worker/health"' in health
    assert '"worker/results"' in result
