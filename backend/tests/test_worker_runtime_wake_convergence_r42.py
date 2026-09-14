from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ROUTE = ROOT / 'backend' / 'modules' / 'worker_runtime_wake' / 'routes.py'


def test_wake_convergence_uses_safe_reset_after_ancestor_and_clean_checks():
    text = ROUTE.read_text(encoding='utf-8')
    fn = text.split('def _converge_development_if_safe()', 1)[1].split('def _current_worker_code_tree', 1)[0]
    assert 'merge-base' in fn
    assert '--is-ancestor' in fn
    assert 'status' in fn and '--porcelain=v1' in fn
    assert '_runtime_git("reset", "--hard", f"origin/{DEV_BRANCH}"' in fn
    assert '_runtime_git("merge", "--ff-only"' not in fn


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
