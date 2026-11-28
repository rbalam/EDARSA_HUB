from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BRIDGE = ROOT / 'tools' / 'mirror_sync' / 'universal_job_bridge.py'
DISPATCHER = ROOT / 'tools' / 'mirror_sync' / 'universal_job_dispatcher.py'
GUARD = ROOT / 'tools' / 'mirror_sync' / 'git_divergence_guard.py'


def _read(path: Path) -> str:
    return path.read_text(encoding='utf-8')


def test_bridge_accepts_frontend_build_certification_without_actions_required_branch():
    text = _read(BRIDGE)
    assert 'FRONTEND_BUILD_CERTIFICATION_MODE = "FRONTEND_BUILD_CERTIFICATION"' in text
    start = text.index('elif mode == FRONTEND_BUILD_CERTIFICATION_MODE:')
    end = text.index('elif mode == MPRO_FULL_HISTORY_MODE:', start)
    block = text[start:end]
    assert 'FRONTEND_BUILD_CERTIFICATION_ACTIONS_FORBIDDEN' in block
    assert 'ACTIONS_REQUIRED' not in block


def test_bridge_restricts_frontend_build_certification_checks():
    text = _read(BRIDGE)
    assert 'FRONTEND_BUILD_CERTIFICATION_FRONTEND_BUILD_REQUIRED' in text
    assert 'FRONTEND_BUILD_CERTIFICATION_ONLY_ALLOWED_CHECKS' in text
    assert '{"frontend_build", "git_diff_check", "repository_contract_audit"}' in text


def test_dispatcher_runs_frontend_build_certification_without_product_actions():
    text = _read(DISPATCHER)
    assert 'FRONTEND_BUILD_CERTIFICATION_MODE = "FRONTEND_BUILD_CERTIFICATION"' in text
    assert 'if mode == FRONTEND_BUILD_CERTIFICATION_MODE:' in text
    assert 'FRONTEND_BUILD_CERTIFICATION_ACTIONS_FORBIDDEN' in text
    assert 'FRONTEND_BUILD_CERTIFIED' in text
    assert 'CERTIFIED_FRONTEND_BUILD' in text
    assert 'frontend_build_certification_repo_mutation_detected' in text
    assert 'result["files_changed"] = []' in text


def test_git_guard_does_not_require_writer_lock_for_frontend_build_certification():
    text = _read(GUARD)
    assert 'FRONTEND_BUILD_CERTIFICATION' in text
    assert 'requires_writer_lock' in text
