from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

CHECK = ROOT / "tools/mirror_sync/check_remote_update.sh"
APPLY = ROOT / "tools/mirror_sync/apply_remote_update.sh"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_check_does_not_reject_all_staged_or_unstaged_work():
    text = read(CHECK)

    assert "DECISION=ABORT_STAGED_WORK_PRESENT" not in text
    assert "DECISION=ABORT_LOCAL_TRACKED_CHANGES_PRESENT" not in text

    assert "STAGED_COLLISION=" in text
    assert "UNSTAGED_COLLISION=" in text
    assert "DECISION=ABORT_LOCAL_TRACKED_COLLISION" in text

    assert "STAGED_COLLISIONS=NONE" in text
    assert "UNSTAGED_COLLISIONS=NONE" in text


def test_apply_rejects_only_tracked_collisions():
    text = read(APPLY)

    assert "ABORT=STAGED_WORK_PRESENT" not in text
    assert "ABORT=LOCAL_TRACKED_CHANGES_PRESENT" not in text

    assert "STAGED_COLLISION=" in text
    assert "UNSTAGED_COLLISION=" in text
    assert "ABORT=LOCAL_TRACKED_COLLISION" in text


def test_apply_snapshots_staged_and_unstaged_state():
    text = read(APPLY)

    assert 'git diff --cached --binary -- > "$STAGED_PATCH_BEFORE"' in text
    assert 'git diff --binary -- > "$UNSTAGED_PATCH_BEFORE"' in text

    assert 'git diff --cached --binary -- > "$STAGED_PATCH_AFTER"' in text
    assert 'git diff --binary -- > "$UNSTAGED_PATCH_AFTER"' in text

    assert 'cmp -s "$STAGED_PATCH_BEFORE" "$STAGED_PATCH_AFTER"' in text
    assert 'cmp -s "$UNSTAGED_PATCH_BEFORE" "$UNSTAGED_PATCH_AFTER"' in text


def test_apply_temporarily_unstages_then_restores_index():
    text = read(APPLY)

    assert 'git reset --mixed "$LOCAL_BEFORE"' in text
    assert 'git apply --cached --binary "$STAGED_PATCH_BEFORE"' in text

    assert "INDEX_RESTORE_REQUIRED=YES" in text
    assert "restore_staged_index()" in text
    assert "restore_on_exit()" in text


def test_apply_preserves_untracked_guard():
    text = read(APPLY)

    assert "UNTRACKED_COLLISION=" in text
    assert "ABORT=UNTRACKED_WOULD_BE_OVERWRITTEN" in text
    assert 'cmp -s "$UNTRACKED_BEFORE" "$UNTRACKED_AFTER"' in text
    assert "UNTRACKED_PRESERVED=YES" in text


def test_apply_requires_exact_staged_and_unstaged_preservation():
    text = read(APPLY)

    assert "ABORT=STAGED_STATE_CHANGED" in text
    assert "ABORT=UNSTAGED_STATE_CHANGED" in text
    assert "ABORT=STAGED_COUNT_CHANGED" in text
    assert "ABORT=UNSTAGED_COUNT_CHANGED" in text

    assert "STAGED_WORK_PRESERVED=YES" in text
    assert "UNSTAGED_WORK_PRESERVED=YES" in text


def test_no_destructive_cleanup_is_introduced():
    combined = read(CHECK) + "\n" + read(APPLY)

    assert "git reset --hard" not in combined
    assert "git clean " not in combined
    assert "rm -rf /app" not in combined
