from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

PUBLISHER = (
    ROOT
    / "tools"
    / "mirror_sync"
    / "universal_job_result_publisher.py"
)


def source():
    return PUBLISHER.read_text(encoding="utf-8")


def test_queue_publication_has_bounded_retry():
    text = source()

    assert "QUEUE_PUBLISH_MAX_ATTEMPTS" in text
    assert (
        "for attempt in range("
        "1, QUEUE_PUBLISH_MAX_ATTEMPTS + 1"
        in text
    )


def test_queue_branch_move_is_retryable():
    text = source()

    assert "QUEUE_BRANCH_MOVED" in text
    assert (
        "UNIVERSAL_RESULT_PUBLISH_RETRY="
        in text
    )


def test_concurrent_push_rejections_are_retryable():
    text = source()

    assert '"fetch first"' in text
    assert '"cannot lock ref"' in text
    assert '"non-fast-forward"' in text
    assert '"stale info"' in text
    assert "CONCURRENT_QUEUE_PUSH" in text


def test_retry_recreates_isolated_checkout():
    text = source()

    loop = text.index(
        "for attempt in range("
    )

    prepare = text.index(
        "prepare_queue_worktree()",
        loop,
    )

    assert prepare > loop

    assert (
        "shutil.rmtree("
        in text[prepare:]
    )


def test_retry_exhaustion_fails_closed():
    text = source()

    assert (
        "QUEUE_RESULT_PUBLISH_RETRIES_EXHAUSTED"
        in text
    )

    assert (
        "raise RuntimeError("
        in text
    )


def test_previous_temp_isolation_is_preserved():
    text = source()

    assert "tempfile.mkdtemp(" in text

    assert (
        'prefix="edarsahub-worker-result-publish-"'
        in text
    )

    assert (
        '"/tmp/edarsahub-worker-result-publish"'
        not in text
    )


def test_error_propagation_is_preserved():
    text = source()

    assert "errors += 1" in text
    assert "return 1 if errors else 0" in text


def test_certification_republication_is_preserved():
    text = source()

    assert (
        '"certification=CERTIFIED" in marker_text'
        in text
    )

    assert (
        "certification={public.get('certification')}"
        in text
    )
