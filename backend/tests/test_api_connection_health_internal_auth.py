import sys
from types import SimpleNamespace

import pytest

import modules.api_connections.repository as repository


@pytest.mark.asyncio
async def test_health_uses_internal_auth_value_not_public_mask(monkeypatch):
    captured = {}
    internal_value = "fixture-value"

    monkeypatch.setattr(
        repository,
        "get_api_connection_with_decrypted_key",
        lambda api_id: {
            "id": api_id,
            "url": "http://example.invalid/query",
            "api_key_decrypted": internal_value,
            "activo": True,
        },
    )

    def public_path_must_not_be_used(_api_id):
        raise AssertionError("public masked connection path used for runtime auth")

    monkeypatch.setattr(
        repository,
        "get_api_connection_sql",
        public_path_must_not_be_used,
    )

    class Response:
        status_code = 200
        elapsed = SimpleNamespace(total_seconds=lambda: 0.012)

    def fake_get(url, *, headers, params, timeout):
        captured.update(url=url, headers=headers, params=params, timeout=timeout)
        return Response()

    import requests
    monkeypatch.setattr(requests, "get", fake_get)

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
    assert captured["headers"] == {"x-api-key": internal_value}
    assert captured["params"] == {"sql": "SELECT 1 as test"}
    assert persisted["connection_id"] == "00000000-0000-4000-8000-000000000701"
    assert internal_value not in repr(result)
