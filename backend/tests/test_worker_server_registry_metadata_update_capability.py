from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BRIDGE = ROOT / "tools" / "mirror_sync" / "universal_job_bridge.py"
DISPATCHER = ROOT / "tools" / "mirror_sync" / "universal_job_dispatcher.py"
GUARD = ROOT / "tools" / "mirror_sync" / "git_divergence_guard.py"
SCRIPT = ROOT / "backend" / "scripts" / "update_server_registry_metadata.py"


def test_mode_is_closed_and_forbids_secrets_and_inline_sql():
    bridge = BRIDGE.read_text(encoding="utf-8")
    dispatcher = DISPATCHER.read_text(encoding="utf-8")
    assert 'SERVER_REGISTRY_METADATA_UPDATE_MODE = "SERVER_REGISTRY_METADATA_UPDATE"' in bridge
    assert 'SERVER_REGISTRY_METADATA_UPDATE_MODE = "SERVER_REGISTRY_METADATA_UPDATE"' in dispatcher
    for forbidden in ('"sql"', '"command"', '"shell"', '"script"', '"path"', '"password"', '"secret"', '"username"'):
        assert forbidden in bridge
        assert forbidden in dispatcher
    assert "confirm_server_registry_metadata_update" in bridge
    assert "confirm_server_registry_metadata_update" in dispatcher


def test_mode_requires_readonly_preflight_and_post_audit():
    bridge = BRIDGE.read_text(encoding="utf-8")
    dispatcher = DISPATCHER.read_text(encoding="utf-8")
    assert "SERVER_REGISTRY_METADATA_UPDATE_PREFLIGHT_REQUIRED" in bridge
    assert "SERVER_REGISTRY_METADATA_UPDATE_POST_AUDIT_REQUIRED" in bridge
    block = dispatcher.split("if mode == SERVER_REGISTRY_METADATA_UPDATE_MODE:", 1)[1].split("if mode == SQL_MIGRATION_DEVELOPMENT_MODE:", 1)[0]
    assert "sql_readonly_audit" in block
    assert "preflight_checks" in block
    assert 'result["checks"]' in block
    assert "CERTIFIED_OPERATIONAL" in block
    assert "canonical_sql_mutation" in block


def test_runtime_uses_canonical_server_registry_helper_and_preserves_active():
    text = SCRIPT.read_text(encoding="utf-8")
    assert 'update_server(server_id, {"database_name": database_name})' in text
    assert "_get_server_by_id_from_sql(server_id, include_inactive=True)" in text
    assert "ACTIVE_STATE_CHANGED" in text
    assert "password" not in text.lower()
    assert "pymssql" not in text.lower()


def test_operational_mode_does_not_require_git_writer_lock():
    text = GUARD.read_text(encoding="utf-8")
    assert '"SERVER_REGISTRY_METADATA_UPDATE"' in text
