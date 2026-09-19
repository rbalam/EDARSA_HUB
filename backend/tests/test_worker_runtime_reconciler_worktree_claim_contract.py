from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TARGET = ROOT / 'tools/mirror_sync/worker_runtime_reconciler.py'


def test_reconciler_covers_state_worktree_claims():
    text = TARGET.read_text(encoding='utf-8')
    assert 'GUARD_STATE_WORKTREES' in text
    assert 'glob("*.json")' in text
    assert 'registered_at' in text


def test_reconciler_derives_job_id_without_task_id():
    text = TARGET.read_text(encoding='utf-8')
    assert 'def claim_task_id' in text
    assert 'agent/worker/' in text
    assert 'worker-' in text


def test_reconciler_keeps_surgical_safety_guards():
    text = TARGET.read_text(encoding='utf-8')
    assert 'WORK_NOT_TERMINAL_OR_INTEGRATED' in text
    assert 'LIVE_PROCESS_REFERENCES_WORKTREE' in text
    assert 'WORKTREE_NOT_CLEAN' in text
    assert 'git("branch", "-d", branch)' in text
    assert 'git("branch", "-D", branch)' not in text
