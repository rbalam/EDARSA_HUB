from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DISPATCHER = ROOT / "tools" / "mirror_sync" / "universal_job_dispatcher.py"


def test_candidate_commit_is_created_before_long_checks_but_push_stays_after_checks():
    text = DISPATCHER.read_text(encoding="utf-8")
    mutation_start = text.index('result["files_changed"] = changed_files')
    candidate_pos = text.index('head = create_commit(', mutation_start)
    checks_pos = text.index('for check in checks:', mutation_start)
    integrate_pos = text.index('ok, detail, final_head', mutation_start)
    assert candidate_pos < checks_pos < integrate_pos


def test_git_diff_check_validates_committed_candidate_against_base():
    text = DISPATCHER.read_text(encoding="utf-8")
    assert 'base_sha: str | None = None' in text
    assert '["git", "diff", "--check", base_sha, "HEAD"]' in text
    assert 'base_sha=execution_base_sha' in text


def test_failed_checks_still_block_integration():
    text = DISPATCHER.read_text(encoding="utf-8")
    mutation_start = text.index('result["files_changed"] = changed_files')
    check_fail_pos = text.index('result["status"] = "GIT_TESTS_FAILED"', mutation_start)
    blockers_pos = text.index('if result["blockers"]:', check_fail_pos)
    integrate_pos = text.index('ok, detail, final_head', blockers_pos)
    assert check_fail_pos < blockers_pos < integrate_pos
