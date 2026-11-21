from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TARGET = ROOT / 'tools/mirror_sync/worker_runtime_reconciler.py'


def test_reconciler_uses_active_claim_authority_only():
    text = TARGET.read_text(encoding='utf-8')
    assert 'state" / "claims"' in text
    assert 'status") or "").strip().upper() != "ACTIVE"' in text
    guard_start = text.index("def guard_claims()")
    guard_end = text.index("\ndef parse_iso", guard_start)
    guard_block = text[guard_start:guard_end]
    assert 'GUARD_STATE_WORKTREES.glob' not in guard_block
    assert '"claims"]' not in guard_block


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


def test_reconciler_fetches_development_once_per_cycle_and_caches_branch_checks():
    text = TARGET.read_text(encoding="utf-8")

    assert "def prepare_integration_snapshot() -> bool:" in text
    assert "_CYCLE_REMOTE_HEAD" in text
    assert "_BRANCH_INTEGRATION_CACHE" in text
    assert '_BRANCH_INTEGRATION_CACHE.get(branch)' in text

    prepare_start = text.index("def prepare_integration_snapshot() -> bool:")
    prepare_end = text.index("\ndef branch_is_integrated", prepare_start)
    prepare_block = text[prepare_start:prepare_end]

    assert prepare_block.count('git("fetch", REMOTE, DEV_BRANCH)') == 1

    branch_start = text.index("def branch_is_integrated(branch: str) -> bool:")
    branch_end = text.index("\ndef worktree_clean", branch_start)
    branch_block = text[branch_start:branch_end]

    assert 'git("fetch"' not in branch_block
    assert '"merge-base",' in branch_block
    assert '"--is-ancestor",' in branch_block


def test_reconciler_integration_snapshot_fails_closed():
    text = TARGET.read_text(encoding="utf-8")

    assert "integration_snapshot_ready = prepare_integration_snapshot()" in text
    assert 'if not _CYCLE_REMOTE_HEAD:' in text
    assert '_BRANCH_INTEGRATION_CACHE[branch] = False' in text
    assert '"integration_snapshot_ready": integration_snapshot_ready' in text
