import sys
from types import SimpleNamespace

import pytest

import modules.api_connections.repository as repository
import modules.integrations_runtime.api_local_sync as transport


@pytest.mark.asyncio
async def test_health_reuses_canonical_api_local_timeout(monkeypatch):
    captured = {}

    async def fake_resolve(api_id):
        return transport.ApiLocalSyncConfig(
            server_id=api_id,
            server_name="API Test",
            api_url="http://example.invalid/query",
            api_key="fixture-value",
        )

    def fake_execute(config, sql, *, timeout_seconds):
        captured["timeout"] = timeout_seconds
        return [{"test": 1}]

    monkeypatch.setattr(transport, "resolve_api_local_sync_config", fake_resolve)
    monkeypatch.setattr(transport, "execute_api_local_readonly", fake_execute)
    monkeypatch.setitem(
        sys.modules,
        "modules.integrations_runtime.health",
        SimpleNamespace(persist_connection_health=lambda *a, **k: None),
    )

    result = await repository.test_api_connection_health(
        api_id="00000000-0000-4000-8000-000000000703"
    )

    assert result["success"] is True
    assert captured["timeout"] == transport.DEFAULT_API_LOCAL_TIMEOUT_SECONDS
    assert transport.DEFAULT_API_LOCAL_TIMEOUT_SECONDS == 30
