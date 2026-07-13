from pathlib import Path

import pytest

from core.connections.edarsahub_readonly_repository import (
    DatabaseIdentityMismatch,
    InvalidConnectionFactory,
    UnitCodeRequired,
    UnitServerMappingNotFound,
    get_unit_server_metadata_readonly,
)


VALID_IDENTITY = {
    "database_name": "EDARSAHUB",
    "login_name": "HRLectura",
    "database_user": "HRLectura",
}

VALID_METADATA = {
    "unidad_negocio_codigo": "130MID",
    "unidad_negocio_nombre": "130 Merida",
    "unidad_negocio_pk": "unidad-1",
    "server_id": "server-1",
    "sucursal_origen_id": None,
    "unidad_system_type": "SoftRestaurant",
    "unidad_activo": True,
    "servidor_nombre": "POS Merida",
    "host": "pos.internal",
    "port": 1433,
    "database_name": "SoftRestaurant",
    "username": "readonly",
    "servidor_system_type": "SoftRestaurant",
    "servidor_activo": True,
    "visible_en_operaciones": True,
    "empresa_id": "empresa-1",
}


class FakeCursor:
    def __init__(self, connection):
        self.connection = connection
        self.description = None

    def execute(self, sql, params=None):
        self.connection.executions.append((sql, params))

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


def test_valida_identidad_antes_de_consultar_tablas():
    connection, factory = make_factory(
        [dict(VALID_IDENTITY), dict(VALID_METADATA)]
    )

    result = get_unit_server_metadata_readonly(
        unidad_codigo="130MID",
        connection_factory=factory,
    )

    assert len(connection.executions) == 2
    assert "DB_NAME()" in connection.executions[0][0]
    assert "Unidades_Negocio" in connection.executions[1][0]
    assert result["server_id"] == "server-1"
    assert connection.closed is True


def test_aborta_antes_de_tablas_si_login_no_es_hrlectura():
    invalid_identity = {
        **VALID_IDENTITY,
        "login_name": "OtroLogin",
    }
    connection, factory = make_factory(
        [invalid_identity, dict(VALID_METADATA)]
    )

    with pytest.raises(DatabaseIdentityMismatch):
        get_unit_server_metadata_readonly(
            unidad_codigo="130MID",
            connection_factory=factory,
        )

    assert len(connection.executions) == 1
    assert "DB_NAME()" in connection.executions[0][0]
    assert connection.closed is True


def test_aborta_si_database_user_no_es_hrlectura():
    invalid_identity = {
        **VALID_IDENTITY,
        "database_user": "dbo",
    }
    connection, factory = make_factory(
        [invalid_identity, dict(VALID_METADATA)]
    )

    with pytest.raises(DatabaseIdentityMismatch):
        get_unit_server_metadata_readonly(
            unidad_codigo="130MID",
            connection_factory=factory,
        )

    assert len(connection.executions) == 1
    assert connection.closed is True


def test_aborta_si_database_no_es_edarsahub():
    invalid_identity = {
        **VALID_IDENTITY,
        "database_name": "master",
    }
    connection, factory = make_factory(
        [invalid_identity, dict(VALID_METADATA)]
    )

    with pytest.raises(DatabaseIdentityMismatch):
        get_unit_server_metadata_readonly(
            unidad_codigo="130MID",
            connection_factory=factory,
        )

    assert len(connection.executions) == 1


def test_consulta_unidad_con_parametro_no_interpolado():
    connection, factory = make_factory(
        [dict(VALID_IDENTITY), dict(VALID_METADATA)]
    )

    get_unit_server_metadata_readonly(
        unidad_codigo="130mid",
        connection_factory=factory,
    )

    sql, params = connection.executions[1]

    assert params == ("130MID",)
    assert "'130MID'" not in sql
    assert "%s" in sql


def test_no_consulta_columnas_de_secretos():
    connection, factory = make_factory(
        [dict(VALID_IDENTITY), dict(VALID_METADATA)]
    )

    result = get_unit_server_metadata_readonly(
        unidad_codigo="130MID",
        connection_factory=factory,
    )

    metadata_sql = connection.executions[1][0].lower()

    assert "password" not in metadata_sql
    assert "api_key" not in metadata_sql
    assert "secret" not in metadata_sql
    assert "password" not in result
    assert "password_encrypted" not in result
    assert result["secrets_exposed"] is False


def test_aborta_si_unidad_no_existe():
    connection, factory = make_factory(
        [dict(VALID_IDENTITY), None]
    )

    with pytest.raises(UnitServerMappingNotFound):
        get_unit_server_metadata_readonly(
            unidad_codigo="NOEXISTE",
            connection_factory=factory,
        )

    assert connection.closed is True


def test_exige_codigo_y_fabrica():
    with pytest.raises(UnitCodeRequired):
        get_unit_server_metadata_readonly(
            unidad_codigo="",
            connection_factory=lambda: None,
        )

    with pytest.raises(InvalidConnectionFactory):
        get_unit_server_metadata_readonly(
            unidad_codigo="130MID",
            connection_factory=None,
        )


def test_modulo_no_abre_conexiones_ni_descifra_secretos():
    module_path = (
        Path(__file__).parents[1]
        / "core"
        / "connections"
        / "edarsahub_readonly_repository.py"
    )
    source = module_path.read_text(
        encoding="utf-8",
        errors="replace",
    ).lower()

    forbidden_terms = (
        "pymssql",
        "pyodbc",
        "get_sql_connection",
        "execute_sql_query",
        "get_external_sql_connection",
        "decrypt_secret",
        "password_encrypted",
        "api_key_encrypted",
        "mongo",
    )

    for term in forbidden_terms:
        assert term not in source

@pytest.mark.parametrize(
    "field,value",
    [
        ("database_name", "edarsahub"),
        ("login_name", "hrlectura"),
        ("login_name", "HRLECTURA"),
        ("database_user", "HrLectura"),
    ],
)
def test_rechaza_identidad_con_casing_incorrecto(
    field,
    value,
):
    invalid_identity = {
        **VALID_IDENTITY,
        field: value,
    }
    connection, factory = make_factory(
        [invalid_identity, dict(VALID_METADATA)]
    )

    with pytest.raises(DatabaseIdentityMismatch):
        get_unit_server_metadata_readonly(
            unidad_codigo="130MID",
            connection_factory=factory,
        )

    assert len(connection.executions) == 1
    assert connection.closed is True
