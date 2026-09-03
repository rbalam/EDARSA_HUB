from pathlib import Path


SCRIPT = (
    Path(__file__).resolve().parents[2]
    / 'tools'
    / 'mirror_sync'
    / 'mirror_sync_worker.sh'
).read_text(encoding='utf-8')


def test_reload_is_development_and_production_guarded():
    assert 'DEV_BRANCH="Edarsahub_Desarrollo"' in SCRIPT
    assert 'if [ "$branch" != "$DEV_BRANCH" ]' in SCRIPT
    assert 'PREVIEW_BACKEND_RELOAD=BLOCKED_PRODUCTION_ENV' in SCRIPT
    assert 'PRODUCTION_TOUCHED=NO' in SCRIPT


def test_reload_is_idempotent_by_backend_tree():
    assert 'git -C "$ROOT" rev-parse HEAD:backend' in SCRIPT
    assert 'PREVIEW_BACKEND_TREE_STATE="$STATE_DIR/preview_backend_tree_sha"' in SCRIPT
    assert 'PREVIEW_BACKEND_RUNTIME=CURRENT' in SCRIPT
    assert 'PREVIEW_BACKEND_RELOAD_COMPLETE=YES' in SCRIPT


def test_reload_uses_only_fixed_backend_service_and_cooldown():
    assert SCRIPT.count('supervisorctl restart backend') == 1
    assert 'supervisorctl status backend' in SCRIPT
    assert 'PREVIEW_BACKEND_RELOAD=COOLDOWN' in SCRIPT
    assert 'maybe_reload_preview_backend' in SCRIPT
