import sys
import types

import pytest

from core.sql_first import connection_factory


def _base_config():
    return {
        "host": "example.invalid,6969",
        "port": 6969,
        "database": "db_test",
        "username": "user_test",
        "password": "password_test",
        "login_timeout": 10,
        "timeout": 30,
        "tds_version": "7.0",
        "as_dict": True,
    }


def test_external_factory_normalizes_host_and_port(
    monkeypatch,
):
    captured = {}

    class FakeConnection:
        pass

    def fake_connect(**kwargs):
        captured.update(kwargs)
        return FakeConnection()

    fake_pymssql = types.SimpleNamespace(
        connect=fake_connect,
    )

    monkeypatch.setitem(
        sys.modules,
        "pymssql",
        fake_pymssql,
    )

    conn = (
        connection_factory
        .get_external_sql_connection(
            _base_config()
        )
    )

    assert isinstance(
        conn,
        FakeConnection,
    )

    assert captured["server"] == (
        "example.invalid"
    )

    assert captured["port"] == 6969

    assert captured["database"] == "db_test"
    assert captured["user"] == "user_test"
    assert captured["password"] == "password_test"
    assert captured["tds_version"] == "7.0"
    assert captured["as_dict"] is True


def test_external_factory_keeps_plain_host(
    monkeypatch,
):
    captured = {}

    def fake_connect(**kwargs):
        captured.update(kwargs)
        return object()

    monkeypatch.setitem(
        sys.modules,
        "pymssql",
        types.SimpleNamespace(
            connect=fake_connect,
        ),
    )

    cfg = _base_config()
    cfg["host"] = "sql.example.invalid"
    cfg["port"] = 1444

    connection_factory.get_external_sql_connection(
        cfg
    )

    assert captured["server"] == (
        "sql.example.invalid"
    )

    assert captured["port"] == 1444


def test_external_factory_propagates_real_pymssql_connection_error(monkeypatch):
    class ExpectedConnectionError(RuntimeError):
        pass

    def fail_connect(**kwargs):
        raise ExpectedConnectionError("REAL_PYMSSQL_CONNECTION_ERROR")

    monkeypatch.setitem(
        sys.modules,
        "pymssql",
        types.SimpleNamespace(connect=fail_connect),
    )
    monkeypatch.setitem(
        sys.modules,
        "pyodbc",
        types.SimpleNamespace(
            connect=lambda *args, **kwargs: pytest.fail(
                "pyodbc must not mask a real pymssql connection error"
            )
        ),
    )

    with pytest.raises(ExpectedConnectionError, match="REAL_PYMSSQL_CONNECTION_ERROR"):
        connection_factory.get_external_sql_connection(_base_config())


def test_external_factory_falls_back_to_pyodbc_only_when_pymssql_import_missing(monkeypatch):
    captured = {}

    def fake_odbc_connect(connection_string, **kwargs):
        captured["connection_string"] = connection_string
        captured.update(kwargs)
        return object()

    monkeypatch.setitem(sys.modules, "pymssql", None)
    monkeypatch.setitem(
        sys.modules,
        "pyodbc",
        types.SimpleNamespace(connect=fake_odbc_connect),
    )

    connection_factory.get_external_sql_connection(_base_config())

    assert "SERVER=example.invalid,6969" in captured["connection_string"]
    assert "DATABASE=db_test" in captured["connection_string"]
    assert captured["timeout"] == 10
