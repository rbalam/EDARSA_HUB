import sys
import types

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
