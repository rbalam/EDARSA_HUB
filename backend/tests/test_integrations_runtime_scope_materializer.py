from unittest.mock import patch

from backend.modules.integrations_runtime.scope_materializer import (
    MaterializedSucursalScope,
    materialize_external_sucursal_scope_atomic,
)


SERVER_ID = "11111111-1111-1111-1111-111111111111"


class FakeCursor:
    def __init__(self):
        self.closed = False

    def close(self):
        self.closed = True


class FakeConnection:
    def __init__(self):
        self.cursor_value = FakeCursor()
        self.commits = 0
        self.rollbacks = 0

    def cursor(self):
        return self.cursor_value

    def commit(self):
        self.commits += 1

    def rollback(self):
        self.rollbacks += 1


def call_subject(connection):
    return materialize_external_sucursal_scope_atomic(
        connection,
        sistema_tipo_id=2,
        tipo_identificador="SUCURSAL_ORIGEN",
        valor_externo="NORTE",
        servidor_id=SERVER_ID,
        sucursal_id=7,
        sucursal_origen_id="NORTE",
        unidad_negocio_id="22222222-2222-2222-2222-222222222222",
        sistema_version_id="33333333-3333-3333-3333-333333333333",
        created_by="worker",
    )


def test_commits_once_after_both_writers_succeed():
    connection = FakeConnection()

    with patch(
        "backend.modules.integrations_runtime.scope_materializer.ensure_external_identifier",
        return_value=41,
    ) as external_writer, patch(
        "backend.modules.integrations_runtime.scope_materializer.ensure_sucursal_server_mapping",
        return_value=52,
    ) as mapping_writer:
        result = call_subject(connection)

    assert result == MaterializedSucursalScope(
        external_identifier_id=41,
        mapping_id=52,
    )
    assert connection.commits == 1
    assert connection.rollbacks == 0
    assert connection.cursor_value.closed is True
    assert external_writer.call_args.kwargs["conexion_id"] == SERVER_ID
    assert mapping_writer.call_args.kwargs["servidor_id"] == SERVER_ID


def test_rolls_back_when_external_identifier_fails():
    connection = FakeConnection()

    with patch(
        "backend.modules.integrations_runtime.scope_materializer.ensure_external_identifier",
        side_effect=ValueError("conflict"),
    ), patch(
        "backend.modules.integrations_runtime.scope_materializer.ensure_sucursal_server_mapping",
    ) as mapping_writer:
        try:
            call_subject(connection)
        except ValueError:
            pass
        else:
            raise AssertionError("expected ValueError")

    assert connection.commits == 0
    assert connection.rollbacks == 1
    assert connection.cursor_value.closed is True
    mapping_writer.assert_not_called()


def test_rolls_back_when_mapping_fails_after_external_writer():
    connection = FakeConnection()

    with patch(
        "backend.modules.integrations_runtime.scope_materializer.ensure_external_identifier",
        return_value=41,
    ), patch(
        "backend.modules.integrations_runtime.scope_materializer.ensure_sucursal_server_mapping",
        side_effect=ValueError("mapping conflict"),
    ):
        try:
            call_subject(connection)
        except ValueError:
            pass
        else:
            raise AssertionError("expected ValueError")

    assert connection.commits == 0
    assert connection.rollbacks == 1
    assert connection.cursor_value.closed is True


def test_connection_is_required():
    try:
        call_subject(None)
    except ValueError as exc:
        assert "Conexion EDARSAHUB requerida" in str(exc)
    else:
        raise AssertionError("expected ValueError")
