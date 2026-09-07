from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CHECK = ROOT / "tools/mirror_sync/check_remote_update.sh"
APPLY = ROOT / "tools/mirror_sync/apply_remote_update.sh"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_check_rejects_only_colliding_local_work():
    text = read(CHECK)
    assert "STAGED_COLLISION=" in text
    assert "UNSTAGED_COLLISION=" in text
    assert "DECISION=ABORT_LOCAL_TRACKED_COLLISION" in text
    assert "UNTRACKED_COLLISION=" in text
    assert "DECISION=ABORT_UNTRACKED_WOULD_BE_OVERWRITTEN" in text
    assert "DECISION=SAFE_REMOTE_FAST_FORWARD_AVAILABLE" in text


def test_apply_snapshots_staged_unstaged_and_untracked_state():
    text = read(APPLY)
    assert 'git diff --cached --binary -- > "$STAGED_PATCH_BEFORE"' in text
    assert 'git diff --binary -- > "$UNSTAGED_PATCH_BEFORE"' in text
    assert 'git diff --cached --binary -- > "$STAGED_PATCH_AFTER"' in text
    assert 'git diff --binary -- > "$UNSTAGED_PATCH_AFTER"' in text
    assert 'cmp -s "$STAGED_PATCH_BEFORE" "$STAGED_PATCH_AFTER"' in text
    assert 'cmp -s "$UNSTAGED_PATCH_BEFORE" "$UNSTAGED_PATCH_AFTER"' in text
    assert 'cmp -s "$UNTRACKED_BEFORE" "$UNTRACKED_AFTER"' in text


def test_apply_fast_forwards_without_stash_reset_or_clean():
    text = read(APPLY)
    assert 'git merge --ff-only "$TARGET"' in text
    forbidden = (
        "git reset ",
        "git stash ",
        "git clean ",
        "git checkout .",
        "git restore ",
    )
    for token in forbidden:
        assert token not in text


def test_apply_has_collision_and_concurrency_guards():
    text = read(APPLY)
    assert "ABORT=LOCAL_TRACKED_COLLISION" in text
    assert "ABORT=UNTRACKED_WOULD_BE_OVERWRITTEN" in text
    assert "ABORT=REMOTE_DEV_MOVED_DURING_CHECK" in text
    assert "ABORT=MIRROR_MOVED_DURING_CHECK" in text
    assert "ABORT=LOCAL_MOVED_DURING_CHECK" in text


def test_apply_requires_exact_local_work_preservation():
    text = read(APPLY)
    assert "ABORT=STAGED_STATE_CHANGED" in text
    assert "ABORT=UNSTAGED_STATE_CHANGED" in text
    assert "ABORT=UNTRACKED_SET_CHANGED" in text
    assert "ABORT=STAGED_COUNT_CHANGED" in text
    assert "ABORT=UNSTAGED_COUNT_CHANGED" in text
    assert "ABORT=UNTRACKED_COUNT_CHANGED" in text
    assert "STAGED_WORK_PRESERVED=YES" in text
    assert "UNSTAGED_WORK_PRESERVED=YES" in text
    assert "UNTRACKED_PRESERVED=YES" in text
    assert "LOCAL_WORK_PRESERVED=YES" in text


def test_production_is_explicitly_untouched():
    text = read(APPLY)
    assert "PRODUCTION_TOUCHED=NO" in text
