"""Regression tests: API_LOCAL universal tests must resolve SQL identity from authenticated email only."""
import pytest

from modules.api_connections import universal_test_routes as module


@pytest.mark.asyncio
async def test_verified_email_allows_authorized_access(monkeypatch):
    seen = []
    def resolve(user):
        seen.append(user)
        return 101
    monkeypatch.setattr(module, "resolve_sql_usuario_id", resolve)
    monkeypatch.setattr(module, "can_access_permission_sql", lambda uid, permission: uid == 101 and permission == "SERVIDORES_VER")
    monkeypatch.setattr(module, "can_access_empresa_sql", lambda uid, empresa: uid == 101 and empresa == 7)
    result = await module.get_api_connection_access_result(
        {"email": "verified@example.invalid", "usuario_id": 999, "_sql_usuario_id": 999},
        {"id": "api-1", "EmpresaID": 7},
    )
    assert result["allowed"] is True
    assert seen == [{"email": "verified@example.invalid"}]


@pytest.mark.asyncio
async def test_injected_id_without_sql_email_resolution_is_denied(monkeypatch):
    seen = []
    def resolve(user):
        seen.append(user)
        return None
    monkeypatch.setattr(module, "resolve_sql_usuario_id", resolve)
    def fail(*args, **kwargs):
        raise AssertionError("RBAC must not execute without verified identity")
    monkeypatch.setattr(module, "can_access_permission_sql", fail)
    monkeypatch.setattr(module, "can_access_empresa_sql", fail)
    result = await module.get_api_connection_access_result(
        {"email": "unknown@example.invalid", "usuario_id": 101, "UsuarioID": 101, "_sql_usuario_id": 101},
        {"id": "api-1", "EmpresaID": 7},
    )
    assert result["allowed"] is False
    assert result["reason"] == "SQL_IDENTITY_NOT_RESOLVED"
    assert seen == [{"email": "unknown@example.invalid"}]


@pytest.mark.asyncio
async def test_missing_authenticated_email_denies_without_sql_lookup(monkeypatch):
    def fail(*args, **kwargs):
        raise AssertionError("No SQL lookup or permission check without authenticated email")
    monkeypatch.setattr(module, "resolve_sql_usuario_id", fail)
    monkeypatch.setattr(module, "can_access_permission_sql", fail)
    monkeypatch.setattr(module, "can_access_empresa_sql", fail)
    result = await module.get_api_connection_access_result(
        {"usuario_id": 101},
        {"id": "api-1", "EmpresaID": 7},
    )
    assert result["allowed"] is False
    assert result["status_code"] == 403
    assert result["reason"] == "SQL_IDENTITY_NOT_RESOLVED"


@pytest.mark.asyncio
async def test_sql_identity_outage_fails_closed(monkeypatch):
    def outage(user):
        raise RuntimeError("simulated SQL outage")
    monkeypatch.setattr(module, "resolve_sql_usuario_id", outage)
    def fail(*args, **kwargs):
        raise AssertionError("No permission or empresa checks when SQL identity fails")
    monkeypatch.setattr(module, "can_access_permission_sql", fail)
    monkeypatch.setattr(module, "can_access_empresa_sql", fail)
    result = await module.get_api_connection_access_result(
        {"email": "verified@example.invalid", "usuario_id": 101},
        {"id": "api-1", "EmpresaID": 7},
    )
    assert result["allowed"] is False
    assert result["status_code"] == 403
    assert result["reason"] == "ACCESS_VALIDATION_EXCEPTION"
