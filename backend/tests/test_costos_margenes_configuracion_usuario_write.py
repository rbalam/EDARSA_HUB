from modules.costos_margenes import configuracion_repository as repo


class FakeCursor:
    def __init__(self, existente=None):
        self.existente = existente
        self.executions = []
        self.fetchone_count = 0

    def execute(self, sql, params=()):
        self.executions.append((sql, params))

    def fetchone(self):
        self.fetchone_count += 1
        return self.existente


class FakeConnection:
    def __init__(self, existente=None):
        self.cursor_obj = FakeCursor(existente)
        self.commits = 0
        self.rollbacks = 0
        self.closed = 0

    def cursor(self, as_dict=False):
        assert as_dict is True
        return self.cursor_obj

    def commit(self):
        self.commits += 1

    def rollback(self):
        self.rollbacks += 1

    def close(self):
        self.closed += 1


def test_patch_omitido_conserva_estado_leido_en_misma_transaccion(
    monkeypatch,
):
    conn = FakeConnection(
        {
            "ConfiguracionUsuarioID": 10,
            "MargenMinimoPorcentaje": 35,
            "MultiploRedondeo": 5,
            "MetodoRedondeo": "MAS_CERCANO",
        }
    )

    monkeypatch.setattr(
        repo,
        "open_validated_writer_connection",
        lambda: (
            conn,
            type(
                "Identity",
                (),
                {
                    "database_name": "EDARSAHUB",
                    "login_name": "HRLectura",
                    "user_name": "HRLectura",
                },
            )(),
        ),
    )

    monkeypatch.setattr(
        repo,
        "_leer_config_usuario",
        lambda usuario_id: {
            "ConfiguracionUsuarioID": 10,
            "UsuarioID": usuario_id,
            "MargenMinimoPorcentaje": 35,
            "MultiploRedondeo": 10,
            "MetodoRedondeo": "MAS_CERCANO",
        },
    )

    result = repo.guardar_configuracion_usuario(
        99,
        {
            "MultiploRedondeo": 10,
        },
    )

    assert len(conn.cursor_obj.executions) == 2

    select_sql, select_params = (
        conn.cursor_obj.executions[0]
    )

    update_sql, update_params = (
        conn.cursor_obj.executions[1]
    )

    assert "UPDLOCK" in select_sql
    assert "HOLDLOCK" in select_sql
    assert select_params == (99,)

    assert "UPDATE" in update_sql
    assert update_params[0] == 35
    assert update_params[1] == 10
    assert update_params[2] == "MAS_CERCANO"

    assert conn.commits == 1
    assert conn.rollbacks == 0
    assert conn.closed == 1

    assert result["MultiploRedondeo"] == 10


def test_null_explicito_elimina_override(monkeypatch):
    conn = FakeConnection(
        {
            "ConfiguracionUsuarioID": 10,
            "MargenMinimoPorcentaje": 35,
            "MultiploRedondeo": 5,
            "MetodoRedondeo": "MAS_CERCANO",
        }
    )

    monkeypatch.setattr(
        repo,
        "open_validated_writer_connection",
        lambda: (
            conn,
            type(
                "Identity",
                (),
                {
                    "database_name": "EDARSAHUB",
                    "login_name": "HRLectura",
                    "user_name": "HRLectura",
                },
            )(),
        ),
    )

    monkeypatch.setattr(
        repo,
        "_leer_config_usuario",
        lambda usuario_id: {
            "ConfiguracionUsuarioID": 10,
            "UsuarioID": usuario_id,
            "MargenMinimoPorcentaje": None,
            "MultiploRedondeo": 5,
            "MetodoRedondeo": "MAS_CERCANO",
        },
    )

    repo.guardar_configuracion_usuario(
        99,
        {
            "MargenMinimoPorcentaje": None,
        },
    )

    _, params = conn.cursor_obj.executions[1]

    assert params[0] is None
    assert params[1] == 5
    assert params[2] == "MAS_CERCANO"


def test_insert_nuevo_usuario(monkeypatch):
    conn = FakeConnection(None)

    monkeypatch.setattr(
        repo,
        "open_validated_writer_connection",
        lambda: (
            conn,
            type(
                "Identity",
                (),
                {
                    "database_name": "EDARSAHUB",
                    "login_name": "HRLectura",
                    "user_name": "HRLectura",
                },
            )(),
        ),
    )

    monkeypatch.setattr(
        repo,
        "_leer_config_usuario",
        lambda usuario_id: {
            "ConfiguracionUsuarioID": 20,
            "UsuarioID": usuario_id,
            "MargenMinimoPorcentaje": 40,
            "MultiploRedondeo": None,
            "MetodoRedondeo": None,
        },
    )

    result = repo.guardar_configuracion_usuario(
        99,
        {
            "MargenMinimoPorcentaje": 40,
        },
    )

    assert len(conn.cursor_obj.executions) == 2

    select_sql, _ = conn.cursor_obj.executions[0]
    insert_sql, params = conn.cursor_obj.executions[1]

    assert "UPDLOCK" in select_sql
    assert "HOLDLOCK" in select_sql
    assert "INSERT INTO" in insert_sql
    assert params == (99, 40, None, None)

    assert conn.commits == 1
    assert conn.rollbacks == 0
    assert conn.closed == 1

    assert result["MargenMinimoPorcentaje"] == 40


def test_writer_rechaza_campos_no_permitidos():
    try:
        repo.guardar_configuracion_usuario(
            99,
            {"UsuarioID": 123},
        )
    except ValueError as exc:
        assert (
            "CAMPOS_CONFIGURACION_NO_PERMITIDOS"
            in str(exc)
        )
    else:
        raise AssertionError(
            "Debio rechazar UsuarioID"
        )


def test_writer_rechaza_usuario_bool():
    try:
        repo.guardar_configuracion_usuario(
            True,
            {"MargenMinimoPorcentaje": 40},
        )
    except ValueError as exc:
        assert str(exc) == "USUARIO_ID_INVALIDO"
    else:
        raise AssertionError(
            "Debio rechazar bool como UsuarioID"
        )


def test_writer_rollback_ante_error(monkeypatch):
    class ErrorCursor(FakeCursor):
        def execute(self, sql, params=()):
            if "UPDATE" in sql:
                raise RuntimeError("write failure")
            super().execute(sql, params)

    conn = FakeConnection(
        {
            "ConfiguracionUsuarioID": 10,
            "MargenMinimoPorcentaje": 35,
            "MultiploRedondeo": 5,
            "MetodoRedondeo": "MAS_CERCANO",
        }
    )

    conn.cursor_obj = ErrorCursor(
        conn.cursor_obj.existente
    )

    monkeypatch.setattr(
        repo,
        "open_validated_writer_connection",
        lambda: (
            conn,
            type(
                "Identity",
                (),
                {
                    "database_name": "EDARSAHUB",
                    "login_name": "HRLectura",
                    "user_name": "HRLectura",
                },
            )(),
        ),
    )

    try:
        repo.guardar_configuracion_usuario(
            99,
            {"MultiploRedondeo": 10},
        )
    except RuntimeError as exc:
        assert str(exc) == "write failure"
    else:
        raise AssertionError(
            "Debio propagar error de escritura"
        )

    assert conn.commits == 0
    assert conn.rollbacks == 1
    assert conn.closed == 1
