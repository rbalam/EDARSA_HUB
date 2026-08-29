from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "tools/mirror_sync/apply_remote_update.sh"


def test_remote_update_never_resets_shared_app_worktree():
    text = SCRIPT.read_text(encoding="utf-8")

    forbidden = (
        "git reset ",
        "git reset\t",
        "git clean ",
        "git restore ",
        "git checkout ",
    )

    for token in forbidden:
        assert token not in text


def test_dirty_app_defers_local_fast_forward():
    text = SCRIPT.read_text(encoding="utf-8")

    assert 'DECISION=DEFER_LOCAL_DIRTY' in text
    assert 'LOCAL_FAST_FORWARD_EXECUTED=NO' in text
    assert 'LOCAL_WORK_PRESERVED=YES' in text

    assert '"$STAGED" -gt 0' in text
    assert '"$TRACKED" -gt 0' in text
    assert '"$UNTRACKED_COUNT_BEFORE" -gt 0' in text


def test_clean_app_still_allows_ff_only():
    text = SCRIPT.read_text(encoding="utf-8")

    assert 'git merge --ff-only "$TARGET"' in text
    assert 'LOCAL_FAST_FORWARD_EXECUTED=YES' in text
