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


def test_result_publisher_uses_unique_temporary_checkout():
    text = source()

    assert "tempfile.mkdtemp(" in text
    assert (
        'prefix="edarsahub-worker-result-publish-"'
        in text
    )
    assert "worktree_root = Path(" in text


def test_result_publisher_no_longer_uses_fixed_checkout():
    text = source()

    assert (
        '"/tmp/edarsahub-worker-result-publish"'
        not in text
    )

    assert "WORKTREE_PARENT" in text
    assert "return worktree_root, base" in text

    assert "return WORKTREE_ROOT, base" not in text


def test_clone_result_is_validated():
    text = source()

    assert "clone = run(" in text
    assert "clone.returncode != 0" in text

    assert (
        "RESULT_WORKTREE_NOT_CREATED:"
        in text
    )


def test_each_publication_cleans_its_own_checkout():
    text = source()

    assert (
        "shutil.rmtree(worktree, ignore_errors=True)"
        in text
    )


def test_publisher_propagates_partial_failures():
    text = source()

    assert "errors = 0" in text
    assert "errors += 1" in text

    assert (
        'UNIVERSAL_RESULTS_PUBLISH_ERROR_COUNT='
        in text
    )

    assert "return 1 if errors else 0" in text


def test_certification_republication_contract_is_preserved():
    text = source()

    assert 'desired = public.get("certification")' in text

    assert (
        '"certification=CERTIFIED" in marker_text'
        in text
    )

    assert (
        "certification={public.get('certification')}"
        in text
    )
