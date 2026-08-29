from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DISPATCHER = ROOT / 'tools' / 'mirror_sync' / 'universal_job_dispatcher.py'


def test_dispatcher_releases_agent_guard_claim_before_removing_worktree():
    text = DISPATCHER.read_text(encoding='utf-8')
    assert 'def release_agent_guard_claim(job_id: str)' in text
    assert '"release", "--agent-id", agent_id' in text
    finally_pos = text.index('    finally:')
    release_pos = text.index('release_agent_guard_claim(job_id)', finally_pos)
    worktree_remove_pos = text.index('git("worktree", "remove"', finally_pos)
    branch_delete_pos = text.index('git("branch", "-D"', finally_pos)
    write_result_pos = text.index('write_json(RESULTS / path.name, result)', finally_pos)
    assert release_pos < worktree_remove_pos < branch_delete_pos < write_result_pos


def test_release_failure_is_visible_and_blocks_certification():
    text = DISPATCHER.read_text(encoding='utf-8')
    assert 'result["agent_guard_release"] = "PASS" if release_ok else "FAIL"' in text
    assert 'agent_guard_release_failed:' in text
    assert 'result["quality_gate"] = "FAIL"' in text
    assert 'result["certification"] = "NOT_CERTIFIED"' in text
