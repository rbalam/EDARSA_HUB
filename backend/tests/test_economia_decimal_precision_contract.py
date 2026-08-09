from decimal import Decimal

from modules.economia.repository import (
    _canonical_decimal_28_10,
    _persistir_valor_versionado,
)


class FakeCursor:
    def __init__(self):
        self.executions = []

    def execute(self, sql, params=()):
        self.executions.append(
            (sql, tuple(params))
        )

    def fetchone(self):
        return (
            123,
            Decimal("3.1200000000"),
            1,
        )


class FakeConnection:
    def __init__(self):
        self.cursor_instance = FakeCursor()
        self.commits = 0
        self.rollbacks = 0

    def cursor(self):
        return self.cursor_instance

    def commit(self):
        self.commits += 1

    def rollback(self):
        self.rollbacks += 1


def test_canonical_decimal_28_10_elimina_ruido_subdecimal():
    actual = Decimal("3.1200000000")
    externo = Decimal(
        "3.12000000000000010000"
    )

    assert (
        _canonical_decimal_28_10(actual)
        == _canonical_decimal_28_10(externo)
        == Decimal("3.1200000000")
    )


def test_persistencia_no_crea_revision_por_ruido_precision():
    conn = FakeConnection()

    result = _persistir_valor_versionado(
        serie_id=5,
        fecha_periodo="2026-07-01",
        valor=Decimal(
            "3.12000000000000010000"
        ),
        connection=conn,
    )

    assert result == {
        "insertado": False,
        "version_dato": 1,
        "es_revision": False,
    }

    # Solo SELECT. No UPDATE ni INSERT.
    assert len(
        conn.cursor_instance.executions
    ) == 1

    sql = (
        conn.cursor_instance
        .executions[0][0]
        .upper()
    )

    assert "SELECT TOP (1)" in sql
    assert "INSERT INTO" not in sql
    assert "UPDATE " not in sql

    # La transacción pertenece al caller.
    assert conn.commits == 0
    assert conn.rollbacks == 0


def test_diferencia_real_a_10_decimales_permanece_diferente():
    actual = Decimal("3.1200000000")
    nuevo = Decimal("3.1200000001")

    assert (
        _canonical_decimal_28_10(actual)
        != _canonical_decimal_28_10(nuevo)
    )
