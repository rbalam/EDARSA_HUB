import os

import pytest


def _module():
    return __import__(
        "tools.provision_inegi_token",
        fromlist=["*"],
    )


def test_no_token_hardcodeado():
    from pathlib import Path

    path = (
        Path(__file__).resolve().parents[1]
        / "tools"
        / "provision_inegi_token.py"
    )

    text = path.read_text(
        encoding="utf-8",
        errors="replace",
    )

    assert "INEGI_API_TOKEN" in text
    assert "Bearer " not in text
    assert "api_key=" not in text


def test_exige_server_secret_key(monkeypatch):
    module = _module()

    monkeypatch.delenv(
        "SERVER_SECRET_KEY",
        raising=False,
    )
    monkeypatch.setenv(
        "INEGI_API_TOKEN",
        "TEST_TOKEN",
    )

    with pytest.raises(Exception):
        module.build_encrypted_token()


def test_exige_token(monkeypatch):
    module = _module()

    monkeypatch.setenv(
        "SERVER_SECRET_KEY",
        "test-secret-key",
    )
    monkeypatch.delenv(
        "INEGI_API_TOKEN",
        raising=False,
    )

    monkeypatch.setattr(
        module,
        "require_server_secret_key",
        lambda: "ok",
    )

    with pytest.raises(
        RuntimeError,
        match="INEGI_API_TOKEN",
    ):
        module.build_encrypted_token()


def test_aborta_si_encrypt_devuelve_plano(monkeypatch):
    module = _module()

    monkeypatch.setenv(
        "INEGI_API_TOKEN",
        "TEST_TOKEN",
    )

    monkeypatch.setattr(
        module,
        "require_server_secret_key",
        lambda: "ok",
    )

    monkeypatch.setattr(
        module,
        "encrypt_secret",
        lambda value: value,
    )

    monkeypatch.setattr(
        module,
        "is_encrypted_secret",
        lambda value: False,
    )

    with pytest.raises(
        RuntimeError,
        match="no pudo cifrarse",
    ):
        module.build_encrypted_token()


def test_acepta_secreto_cifrado(monkeypatch):
    module = _module()

    monkeypatch.setenv(
        "INEGI_API_TOKEN",
        "TEST_TOKEN",
    )

    monkeypatch.setattr(
        module,
        "require_server_secret_key",
        lambda: "ok",
    )

    monkeypatch.setattr(
        module,
        "encrypt_secret",
        lambda value: "enc:v1:ABC",
    )

    monkeypatch.setattr(
        module,
        "is_encrypted_secret",
        lambda value: value.startswith("enc:v1:"),
    )

    assert (
        module.build_encrypted_token()
        == "enc:v1:ABC"
    )


def test_herramienta_no_activa_inegi():
    from pathlib import Path

    path = (
        Path(__file__).resolve().parents[1]
        / "tools"
        / "provision_inegi_token.py"
    )

    text = path.read_text(encoding="utf-8")

    assert "UPDATE dbo.Economia_Proveedores" not in text
    assert "UPDATE dbo.Economia_Series" not in text
    assert "SCHEDULER_ECONOMIA_SYNC_ENABLED" not in text


class FakeCursor:
    def __init__(
        self,
        select_rows=None,
        update_rowcount=1,
        validation_row=(False, 1),
    ):
        self.select_rows = (
            [(object(), False)]
            if select_rows is None
            else select_rows
        )
        self.update_rowcount = update_rowcount
        self.validation_row = validation_row
        self.rowcount = -1
        self.execute_count = 0
        self.executions = []

    def execute(self, sql, params=None):
        self.execute_count += 1
        self.executions.append((sql, params))

        if "UPDATE dbo.Servidores_Conexiones" in sql:
            self.rowcount = self.update_rowcount

    def fetchall(self):
        return self.select_rows

    def fetchone(self):
        return self.validation_row


class FakeConnection:
    def __init__(self, cursor):
        self._cursor = cursor
        self.committed = False
        self.rolled_back = False
        self.closed = False

    def cursor(self):
        return self._cursor

    def commit(self):
        self.committed = True

    def rollback(self):
        self.rolled_back = True

    def close(self):
        self.closed = True


def test_provision_update_es_parametrizado_y_fail_closed(
    monkeypatch,
):
    module = _module()

    monkeypatch.setattr(
        module,
        "is_encrypted_secret",
        lambda value: value.startswith("enc:v1:"),
    )

    cursor = FakeCursor()
    conn = FakeConnection(cursor)

    module.provision_encrypted_token(
        "enc:v1:ABC",
        connection_factory=lambda: conn,
    )

    assert conn.committed is True
    assert conn.rolled_back is False
    assert conn.closed is True

    update_calls = [
        item
        for item in cursor.executions
        if "UPDATE dbo.Servidores_Conexiones" in item[0]
    ]

    assert len(update_calls) == 1

    sql, params = update_calls[0]

    assert "api_key_encrypted = %s" in sql
    assert "system_type = %s" in sql
    assert "activo = 0" in sql

    assert params[0] == "enc:v1:ABC"
    assert params[2] == "INEGI"

    assert "enc:v1:ABC" not in sql


def test_provision_rechaza_token_plano(monkeypatch):
    module = _module()

    monkeypatch.setattr(
        module,
        "is_encrypted_secret",
        lambda value: False,
    )

    with pytest.raises(
        RuntimeError,
        match="no cifrado",
    ):
        module.provision_encrypted_token(
            "TOKEN_PLANO",
            connection_factory=lambda: None,
        )


def test_provision_aborta_si_no_hay_exactamente_una_conexion(
    monkeypatch,
):
    module = _module()

    monkeypatch.setattr(
        module,
        "is_encrypted_secret",
        lambda value: True,
    )

    cursor = FakeCursor(select_rows=[])
    conn = FakeConnection(cursor)

    with pytest.raises(
        RuntimeError,
        match="exactamente una",
    ):
        module.provision_encrypted_token(
            "enc:v1:ABC",
            connection_factory=lambda: conn,
        )

    assert conn.committed is False
    assert conn.rolled_back is True
    assert conn.closed is True


def test_provision_aborta_si_inegi_esta_activo(
    monkeypatch,
):
    module = _module()

    monkeypatch.setattr(
        module,
        "is_encrypted_secret",
        lambda value: True,
    )

    cursor = FakeCursor(
        select_rows=[(object(), True)]
    )
    conn = FakeConnection(cursor)

    with pytest.raises(
        RuntimeError,
        match="permanecer inactiva",
    ):
        module.provision_encrypted_token(
            "enc:v1:ABC",
            connection_factory=lambda: conn,
        )

    assert conn.committed is False
    assert conn.rolled_back is True


def test_provision_aborta_si_update_no_es_unitario(
    monkeypatch,
):
    module = _module()

    monkeypatch.setattr(
        module,
        "is_encrypted_secret",
        lambda value: True,
    )

    cursor = FakeCursor(update_rowcount=0)
    conn = FakeConnection(cursor)

    with pytest.raises(
        RuntimeError,
        match="exactamente una fila",
    ):
        module.provision_encrypted_token(
            "enc:v1:ABC",
            connection_factory=lambda: conn,
        )

    assert conn.committed is False
    assert conn.rolled_back is True


def test_provision_aborta_si_estado_final_activo(
    monkeypatch,
):
    module = _module()

    monkeypatch.setattr(
        module,
        "is_encrypted_secret",
        lambda value: True,
    )

    cursor = FakeCursor(
        validation_row=(True, 1)
    )
    conn = FakeConnection(cursor)

    with pytest.raises(
        RuntimeError,
        match="activado inesperadamente",
    ):
        module.provision_encrypted_token(
            "enc:v1:ABC",
            connection_factory=lambda: conn,
        )

    assert conn.committed is False
    assert conn.rolled_back is True


def test_provision_aborta_si_token_no_queda_persistido(
    monkeypatch,
):
    module = _module()

    monkeypatch.setattr(
        module,
        "is_encrypted_secret",
        lambda value: True,
    )

    cursor = FakeCursor(
        validation_row=(False, 0)
    )
    conn = FakeConnection(cursor)

    with pytest.raises(
        RuntimeError,
        match="no quedó persistido",
    ):
        module.provision_encrypted_token(
            "enc:v1:ABC",
            connection_factory=lambda: conn,
        )

    assert conn.committed is False
    assert conn.rolled_back is True


def test_provisioner_usa_writer_canonico():
    from pathlib import Path

    source = (
        Path(__file__)
        .resolve()
        .parents[1]
        / "tools"
        / "provision_inegi_token.py"
    ).read_text(encoding="utf-8")

    assert (
        "from core.connections.edarsahub_writer_connection import ("
        in source
    )
    assert "open_validated_writer_connection" in source
    assert (
        "connection_factory=open_validated_writer_connection"
        in source
    )
    assert (
        "connection_factory=get_sql_connection"
        not in source
    )


def test_provisioner_admite_writer_tuple_y_factory_test():
    from pathlib import Path

    source = (
        Path(__file__)
        .resolve()
        .parents[1]
        / "tools"
        / "provision_inegi_token.py"
    ).read_text(encoding="utf-8")

    assert "opened = connection_factory()" in source
    assert "conn, _identity = opened" in source
    assert "conn = opened" in source
