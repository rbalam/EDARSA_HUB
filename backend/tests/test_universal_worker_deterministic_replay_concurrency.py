from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DISPATCHER = ROOT / 'tools' / 'mirror_sync' / 'universal_job_dispatcher.py'
POLICY = ROOT / 'tools' / 'mirror_sync' / 'worker_concurrency.py'


def source(path):
    return path.read_text(encoding='utf-8')


def test_no_rebase_merge_or_cherry_pick_in_integration():
    text = source(DISPATCHER)
    block = text.split('def integrate(', 1)[1].split('def release_agent_guard_claim(', 1)[0]
    assert 'git("rebase"' not in block
    assert 'git("merge"' not in block
    assert 'git("cherry-pick"' not in block
    assert '--onto' not in block


def test_safe_head_advance_requests_replay_and_scope_overlap_blocks():
    dispatcher = source(DISPATCHER)
    policy = source(POLICY)
    assert 'SAFE_REPLAY' in policy
    assert 'SAFE_REPLAY' in policy
    assert 'CONCURRENT_SCOPE_CONFLICT' in dispatcher


def test_process_loop_performs_fresh_worktree_replay_and_reruns_checks():
    text = source(DISPATCHER)
    process = text.split('def process_one(', 1)[1].split('def dispatch(', 1)[0]
    assert 'for replay_attempt in range(1, MAX_CONCURRENCY_REPLAY_ATTEMPTS + 1)' in process
    assert 'release_agent_guard_claim(job_id)' in process
    assert 'git("worktree", "remove", "--force"' in process
    assert 'prepare_worktree(job_id, execution_base_sha, requested_paths)' in process
    assert 'for action in job.get("actions") or []' in process
    assert 'for check in checks:' in process
    assert 'execution_base_sha = base_sha' in process
    assert 'accumulated_integration' in process


def test_concurrency_evidence_contract_is_explicit():
    text = source(DISPATCHER)
    for key in ('initial_base_sha','execution_base_sha','integration_attempts','concurrency_replays','concurrent_head_changes'):
        assert key in text
