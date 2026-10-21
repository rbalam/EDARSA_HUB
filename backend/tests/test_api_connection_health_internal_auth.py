import sys
from types import SimpleNamespace

import pytest

import modules.api_connections.repository as repository
import modules.integrations_runtime.api_local_sync as transport


@pytest.mark.asyncio
async def test_health_uses_canonical_api_local_transport(monkeypatch):
    internal_value = "fixture-value"
    captured = {}

    async def fake_resolve(api_id):
        return transport.ApiLocalSyncConfig(
            server_id=api_id,
            server_name="API Test",
            api_url="http://example.invalid/query",
            api_key=internal_value,
            system_type="ENTERPRISE",
            config_origin="EDARSAHUB_SQL",
        )

    def fake_execute(config, sql, *, timeout_seconds):
        captured["config"] = config
        captured["sql"] = sql
        captured["timeout"] = timeout_seconds
        return [{"test": 1}]

    monkeypatch.setattr(transport, "resolve_api_local_sync_config", fake_resolve)
    monkeypatch.setattr(transport, "execute_api_local_readonly", fake_execute)

    def public_path_must_not_be_used(_api_id):
        raise AssertionError("public masked connection path used for runtime auth")

    monkeypatch.setattr(repository, "get_api_connection_sql", public_path_must_not_be_used)

    persisted = {}

    def fake_persist(connection_id, **kwargs):
        persisted["connection_id"] = connection_id
        persisted.update(kwargs)

    monkeypatch.setitem(
        sys.modules,
        "modules.integrations_runtime.health",
        SimpleNamespace(persist_connection_health=fake_persist),
    )

    result = await repository.test_api_connection_health(
        api_id="00000000-0000-4000-8000-000000000701"
    )

    assert result["success"] is True
    assert result["health_persisted"] is True
    assert captured["config"].api_key == internal_value
    assert captured["sql"] == "SELECT 1 as test"
    assert captured["timeout"] == transport.DEFAULT_API_LOCAL_TIMEOUT_SECONDS
    assert persisted["connection_id"] == "00000000-0000-4000-8000-000000000701"
    assert internal_value not in repr(result)
