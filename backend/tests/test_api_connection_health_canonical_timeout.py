import sys
from types import SimpleNamespace

import pytest

import modules.api_connections.repository as repository
from modules.integrations_runtime.api_local_sync import DEFAULT_API_LOCAL_TIMEOUT_SECONDS


@pytest.mark.asyncio
async def test_health_reuses_canonical_api_local_timeout(monkeypatch):
    captured = {}

    monkeypatch.setattr(
        repository,
        "get_api_connection_with_decrypted_key",
        lambda api_id: {
            "id": api_id,
            "url": "http://example.invalid/query",
            "api_key_decrypted": "fixture-value",
            "activo": True,
        },
    )

    class Response:
        status_code = 200
        elapsed = SimpleNamespace(total_seconds=lambda: 0.012)

    def fake_get(url, *, headers, params, timeout):
        captured["timeout"] = timeout
        return Response()

    import requests
    monkeypatch.setattr(requests, "get", fake_get)

    monkeypatch.setitem(
        sys.modules,
        "modules.integrations_runtime.health",
        SimpleNamespace(persist_connection_health=lambda *a, **k: None),
    )

    result = await repository.test_api_connection_health(
        api_id="00000000-0000-4000-8000-000000000703"
    )

    assert result["success"] is True
    assert captured["timeout"] == DEFAULT_API_LOCAL_TIMEOUT_SECONDS
    assert DEFAULT_API_LOCAL_TIMEOUT_SECONDS == 30
