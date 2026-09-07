from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DISPATCHER = ROOT / "tools" / "mirror_sync" / "universal_job_dispatcher.py"


def _source() -> str:
    return DISPATCHER.read_text(encoding="utf-8")


def test_pickup_uses_scope_aware_policy_instead_of_global_sha_block():
    src = _source()
    assert "evaluate_scope_advance" in src
    assert "git_changed_paths(expected_base, current_head)" in src
    assert "BASE_SCOPE_CONFLICT" in src
    assert "BASE_SHA_MISMATCH:expected=" not in src


def test_integration_rechecks_scope_and_rebases_only_when_safe():
    src = _source()
    assert "development_scope_conflict" in src
    assert 'git("rebase", "--onto", remote_dev, candidate_base, branch' in src
    assert "MAX_SCOPE_REBASE_ATTEMPTS" in src
    assert 'result["concurrency"]["integration"] = integration_evidence' in src


def test_read_only_can_tolerate_unrelated_repository_advance():
    src = _source()
    assert 'allow_empty_scope_advance=(mode == "READ_ONLY_SQL")' in src


def test_production_remains_explicitly_untouched_in_worker_results():
    src = _source()
    assert '"production_touched": False' in src
