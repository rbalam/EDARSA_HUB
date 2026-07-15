import pytest

from core.connections.edarsahub_readonly_repository import (
    DatabaseIdentityMismatch,
    UnitCodeRequired,
    UnitServerMappingNotFound,
    get_unit_scope_metadata_readonly,
)


VALID_IDENTITY = {
    "database_name": "EDARSAHUB",
    "login_name": "HRLectura",
    "database_user": "HRLectura",
}

VALID_METADATA = {
    "unidad_negocio_pk": "unit-pk",
    "unidad_negocio_codigo": "UNIT-A",
    "unidad_negocio_nombre": "Unit A",
    "server_id": "server-a",
    "sucursal_origen_id": None,
    "system_type": "SYSTEM-A",
    "unidad_activo": 1,
    "servidor_activo": 1,
    "empresa_id": "company-a",
    "visible_en_operaciones": 1,
    "active_units_on_server": 1,
}


class FakeCursor:
    def __init__(self, connection):
        self.connection = connection
        self.description = None

    def execute(self, sql, params=None):
        self.connection.executions.append(
            (sql, params)
        )

    def fetchone(self):
        if not self.connection.rows:
            return None

        return self.connection.rows.pop(0)


class FakeConnection:
    def __init__(self, rows):
        self.rows = list(rows)
        self.executions = []
        self.closed = False

    def cursor(self):
        return FakeCursor(self)

    def close(self):
        self.closed = True


def make_factory(rows):
    connection = FakeConnection(rows)

    def factory():
        return connection

    return connection, factory


def test_identity_is_checked_before_unit_query():
    connection, factory = make_factory(
        [
            dict(VALID_IDENTITY),
            dict(VALID_METADATA),
        ]
    )

    result = get_unit_scope_metadata_readonly(
        unidad="UNIT-A",
        connection_factory=factory,
    )

    assert len(connection.executions) == 2
    assert "DB_NAME()" in connection.executions[0][0]
    assert (
        "Unidades_Negocio"
        in connection.executions[1][0]
    )
    assert result["server_id"] == "server-a"
    assert result["active_units_on_server"] == 1
    assert connection.closed is True


def test_selector_is_parameterized_for_code_or_pk():
    connection, factory = make_factory(
        [
            dict(VALID_IDENTITY),
            dict(VALID_METADATA),
        ]
    )

    get_unit_scope_metadata_readonly(
        unidad="unit-pk",
        connection_factory=factory,
    )

    sql, params = connection.executions[1]

    assert params == ("unit-pk", "unit-pk")
    assert "unit-pk" not in sql
    assert sql.count("%s") == 2


def test_empty_selector_rejected_before_connection():
    called = False

    def factory():
        nonlocal called
        called = True
        return None

    with pytest.raises(UnitCodeRequired):
        get_unit_scope_metadata_readonly(
            unidad="",
            connection_factory=factory,
        )

    assert called is False


def test_unknown_or_ambiguous_unit_fails_closed():
    connection, factory = make_factory(
        [
            dict(VALID_IDENTITY),
            None,
        ]
    )

    with pytest.raises(UnitServerMappingNotFound):
        get_unit_scope_metadata_readonly(
            unidad="UNKNOWN",
            connection_factory=factory,
        )

    assert connection.closed is True


def test_inactive_unit_fails_closed():
    metadata = {
        **VALID_METADATA,
        "unidad_activo": 0,
    }

    connection, factory = make_factory(
        [
            dict(VALID_IDENTITY),
            metadata,
        ]
    )

    with pytest.raises(UnitServerMappingNotFound):
        get_unit_scope_metadata_readonly(
            unidad="UNIT-A",
            connection_factory=factory,
        )

    assert connection.closed is True


def test_invalid_identity_prevents_catalog_query():
    identity = {
        **VALID_IDENTITY,
        "login_name": "OTHER",
    }

    connection, factory = make_factory(
        [
            identity,
            dict(VALID_METADATA),
        ]
    )

    with pytest.raises(DatabaseIdentityMismatch):
        get_unit_scope_metadata_readonly(
            unidad="UNIT-A",
            connection_factory=factory,
        )

    assert len(connection.executions) == 1
    assert connection.closed is True


def test_result_does_not_expose_secrets():
    connection, factory = make_factory(
        [
            dict(VALID_IDENTITY),
            dict(VALID_METADATA),
        ]
    )

    result = get_unit_scope_metadata_readonly(
        unidad="UNIT-A",
        connection_factory=factory,
    )

    lowered_keys = {
        str(key).lower()
        for key in result
    }

    assert "password" not in lowered_keys
    assert "password_encrypted" not in lowered_keys
    assert "api_key" not in lowered_keys
    assert result["secrets_exposed"] is False
