import asyncio

import pytest
import requests

import modules.integrations_runtime.api_local_sync as transport


class FakeResponse:
    def __init__(self, status_code=200, payload=None, text=""):
        self.status_code = status_code
        self._payload = payload
        self.text = text

    def json(self):
        if isinstance(self._payload, Exception):
            raise self._payload
        return self._payload


def test_execute_readonly_select_contract():
    calls = []

    def fake_get(url, *, params, headers, timeout):
        calls.append((url, params, headers, timeout))
        return FakeResponse(200, {"data": [{"SucursalID": "01"}]})

    cfg = transport.ApiLocalSyncConfig(
        server_id="srv",
        server_name="Enterprise",
        api_url="http://internal/query",
        api_key="secret-value",
    )

    rows = transport.execute_api_local_readonly(
        cfg,
        "SELECT SucursalID FROM dbo.Sucursales",
        timeout_seconds=20,
        request_get=fake_get,
    )

    assert rows == [{"SucursalID": "01"}]
    assert calls == [(
        "http://internal/query",
        {"sql": "SELECT SucursalID FROM dbo.Sucursales"},
        {"X-API-Key": "secret-value"},
        20,
    )]


@pytest.mark.parametrize(
    "sql",
    [
        "UPDATE dbo.X SET a=1",
        "DELETE FROM dbo.X",
        "SELECT * INTO dbo.Y FROM dbo.X",
        "SELECT 1; SELECT 2",
    ],
)
def test_transport_rejects_non_read_only_sql_before_http(sql):
    touched = False

    def fake_get(*args, **kwargs):
        nonlocal touched
        touched = True
        raise AssertionError("HTTP must not be called")

    cfg = transport.ApiLocalSyncConfig(
        server_id="srv",
        server_name="Enterprise",
        api_url="http://internal/query",
        api_key="secret-value",
    )

    with pytest.raises(ValueError):
        transport.execute_api_local_readonly(
            cfg,
            sql,
            request_get=fake_get,
        )
    assert touched is False


def test_transport_fail_closed_on_timeout():
    def fake_get(*args, **kwargs):
        raise requests.exceptions.Timeout()

    cfg = transport.ApiLocalSyncConfig(
        server_id="srv",
        server_name="Enterprise",
        api_url="http://internal/query",
        api_key="secret-value",
    )

    with pytest.raises(transport.ApiLocalSyncError, match="API_LOCAL_TIMEOUT"):
        transport.execute_api_local_readonly(
            cfg,
            "SELECT 1",
            request_get=fake_get,
        )


def test_transport_rejects_invalid_payload():
    cfg = transport.ApiLocalSyncConfig(
        server_id="srv",
        server_name="Enterprise",
        api_url="http://internal/query",
        api_key="secret-value",
    )

    with pytest.raises(transport.ApiLocalSyncError, match="API_LOCAL_INVALID_DATA"):
        transport.execute_api_local_readonly(
            cfg,
            "SELECT 1",
            request_get=lambda *a, **k: FakeResponse(200, {"data": {"x": 1}}),
        )


def test_config_repr_does_not_expose_api_key():
    cfg = transport.ApiLocalSyncConfig(
        server_id="srv",
        server_name="Enterprise",
        api_url="http://internal/query",
        api_key="do-not-print-me",
    )
    assert "do-not-print-me" not in repr(cfg)


def test_resolver_uses_canonical_registry_and_decryption(monkeypatch):
    async def fake_get_server_by_id(*args, **kwargs):
        assert kwargs["prefer_sql"] is True
        assert kwargs["allow_mongo_fallback"] is False
        assert kwargs["mask_secrets"] is False
        return {
            "id": "srv",
            "name": "CHAPUR",
            "tipo_conexion": "API_LOCAL",
            "active": True,
            "system_type": "ENTERPRISE",
            "config_origin": "EDARSAHUB_SQL",
        }

    monkeypatch.setattr(transport, "get_server_by_id", fake_get_server_by_id)
    monkeypatch.setattr(
        transport,
        "get_decrypted_credentials",
        lambda server: {
            "api_url": "http://internal/query",
            "api_key": "secret-value",
        },
    )

    cfg = asyncio.run(transport.resolve_api_local_sync_config("srv"))

    assert cfg.server_id == "srv"
    assert cfg.system_type == "ENTERPRISE"
    assert cfg.config_origin == "EDARSAHUB_SQL"


def test_http_500_classifier_never_returns_raw_error_text():
    response = FakeResponse(
        500,
        text="Login failed for user sensitive-user on secret-host",
    )

    code = transport.classify_api_local_http_error(response)

    assert code == "API_LOCAL_HTTP_500_UPSTREAM_SQL_AUTH"
    assert "sensitive-user" not in code
    assert "secret-host" not in code


def test_http_500_classifier_distinguishes_connectivity_and_query():
    assert transport.classify_api_local_http_error(
        FakeResponse(500, text="DB-Lib error: server unavailable")
    ) == "API_LOCAL_HTTP_500_UPSTREAM_SQL_CONNECTIVITY"
    assert transport.classify_api_local_http_error(
        FakeResponse(500, text="Invalid object name dbo.Missing")
    ) == "API_LOCAL_HTTP_500_UPSTREAM_SQL_QUERY"


def test_resolver_rejects_non_api_local(monkeypatch):
    async def fake_get_server_by_id(*args, **kwargs):
        return {
            "id": "srv",
            "tipo_conexion": "DATA_SOURCE",
            "active": True,
        }

    monkeypatch.setattr(transport, "get_server_by_id", fake_get_server_by_id)

    with pytest.raises(
        transport.ApiLocalSyncError,
        match="API_LOCAL_CONNECTION_TYPE_REQUIRED",
    ):
        asyncio.run(transport.resolve_api_local_sync_config("srv"))
