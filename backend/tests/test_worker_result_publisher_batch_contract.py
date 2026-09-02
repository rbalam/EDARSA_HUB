from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

PUB = (
    ROOT
    / "tools"
    / "mirror_sync"
    / "universal_job_result_publisher.py"
)


def test_batch_size_is_configurable_and_bounded():
    text = PUB.read_text(encoding="utf-8")

    assert "RESULT_BATCH_SIZE" in text
    assert "EDARSAHUB_RESULT_BATCH_SIZE" in text
    assert "attempted >= RESULT_BATCH_SIZE" in text


def test_direct_push_has_timeout():
    text = PUB.read_text(encoding="utf-8")

    assert "QUEUE_RESULT_PUSH_TIMEOUT:" in text
    assert "timeout=GIT_TIMEOUT_SECONDS" in text


def test_batch_metrics_are_emitted():
    text = PUB.read_text(encoding="utf-8")

    assert "UNIVERSAL_RESULTS_ATTEMPTED_COUNT=" in text
    assert "UNIVERSAL_RESULTS_BATCH_SIZE=" in text


def test_certified_markers_are_skipped_before_attempt_budget():
    text = PUB.read_text(encoding="utf-8")

    assert 'marker = PUBLISHED / path.name' in text
    assert '"certification=CERTIFIED"' in text
