from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ROUTE = ROOT / 'backend' / 'modules' / 'worker_runtime_wake' / 'routes.py'


def test_wake_convergence_uses_canonical_fast_forward_after_ancestor_and_clean_checks():
    text = ROUTE.read_text(encoding='utf-8')
    fn = text.split('def _converge_development_if_safe()', 1)[1].split('def _current_worker_code_tree', 1)[0]
    assert '_runtime_git("fetch", "--quiet", "origin", DEV_BRANCH' in fn
    assert '_runtime_git("branch", "--show-current")' in fn
    assert '_runtime_git("rev-parse", "HEAD")' in fn
    assert '_runtime_git("rev-parse", f"origin/{DEV_BRANCH}")' in fn
    assert '_runtime_git("merge-base", "--is-ancestor", local, remote)' in fn
    assert '_runtime_git("status", "--porcelain=v1", "--untracked-files=all")' in fn
    assert 'GIT_GUARD_PATH.is_file()' in fn
    assert '"refresh"' in fn
    assert '"--expected-remote"' in fn
    assert 'new_head = _runtime_git("rev-parse", "HEAD")' in fn
    assert 'if new_head != remote:' in fn
    assert '_runtime_git("reset"' not in fn
    assert '_runtime_git("merge"' not in fn
    assert '_runtime_git("stash"' not in fn
    assert '"--force"' not in fn


def test_wake_contract_still_forbids_production_touch():
    text = ROUTE.read_text(encoding='utf-8')
    assert 'production_touched' in text
    assert 'Production is never touched' in text


def test_wake_preserves_active_job_before_runtime_convergence():
    text = ROUTE.read_text(encoding='utf-8')
    fn = text.split('def wake_worker(', 1)[1]
    active_pos = fn.index('active_job_id = _active_job_id()')
    converge_pos = fn.index('convergence = _converge_development_if_safe()')
    assert active_pos < converge_pos
    assert '"action": "active_job_preserved"' in fn
    assert '"state": "DEFERRED_ACTIVE_JOB"' in fn


def test_wake_git_calls_preserve_process_environment():
    text = ROUTE.read_text(encoding='utf-8')
    assert 'import os' in text
    assert text.count('env={**os.environ, "GIT_TERMINAL_PROMPT": "0"}') >= 3
