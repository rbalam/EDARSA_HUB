from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

import tools.edarsahub_sql_runner as runner
from core.connections.hrlectura_connection_factory import (
    ConfiguredLoginMismatch,
)


BACKEND = Path(__file__).parents[1]
RUNNER_PATH = (
    BACKEND / "tools" / "edarsahub_sql_runner.py"
)
SQL_ENV_NAMES = (
    "EDARSAHUB_SQL_HOST",
    "EDARSAHUB_SQL_PORT",
    "EDARSAHUB_SQL_DATABASE",
    "EDARSAHUB_SQL_USER",
    "EDARSAHUB_SQL_PASSWORD",
)


def _env_without_sql_config():
    env = os.environ.copy()
    for name in SQL_ENV_NAMES:
        env.pop(name, None)
    return env


def test_runner_importa_sin_configuracion_sql():
    process = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import tools.edarsahub_sql_runner; "
                "print('runner_import_ok=1')"
            ),
        ],
        cwd=BACKEND,
        env=_env_without_sql_config(),
        capture_output=True,
        text=True,
        check=False,
    )

    assert process.returncode == 0, process.stderr
    assert "runner_import_ok=1" in process.stdout


def test_runner_help_funciona_sin_configuracion_sql():
    process = subprocess.run(
        [
            sys.executable,
            str(RUNNER_PATH),
            "--help",
        ],
        cwd=BACKEND,
        env=_env_without_sql_config(),
        capture_output=True,
        text=True,
        check=False,
    )

    assert process.returncode == 0, process.stderr
    assert "--mode" in process.stdout
    assert "--script" in process.stdout


def test_dry_run_no_abre_conexion(monkeypatch):
    def forbidden_connection(mode):
        raise AssertionError(
            f"dry-run intento abrir conexion: {mode}"
        )

    monkeypatch.setattr(
        runner,
        "get_connection",
        forbidden_connection,
    )

    result = runner.execute_sql(
        "SELECT 1;",
        "dry-run",
    )

    assert result["success"] is True
    assert result["mode"] == "dry-run"


def test_readonly_rechaza_login_antes_de_abrir(
    monkeypatch,
):
    opened = []

    class Config:
        user = "GptLectura"

    monkeypatch.setattr(
        runner,
        "get_edarsahub_sql_config",
        lambda profile="default": Config(),
    )
    monkeypatch.setattr(
        runner,
        "get_edarsahub_pymssql_connection",
        lambda **kwargs: opened.append(kwargs),
    )

    with pytest.raises(ConfiguredLoginMismatch):
        runner.get_connection("diagnostic")

    assert opened == []


def test_identidad_efectiva_se_valida_antes_del_batch(
    monkeypatch,
):
    events = []

    class FakeCursor:
        description = [("value",)]
        rowcount = 1

        def execute(self, sql):
            events.append(("execute", sql))

        def fetchall(self):
            return [{"value": 1}]

        def close(self):
            events.append(("cursor_close", None))

    class FakeConnection:
        def cursor(self, as_dict=False):
            events.append(("cursor", as_dict))
            return FakeCursor()

        def rollback(self):
            events.append(("rollback", None))

        def close(self):
            events.append(("connection_close", None))

    connection = FakeConnection()

    monkeypatch.setattr(
        runner,
        "get_connection",
        lambda mode: connection,
    )
    monkeypatch.setattr(
        runner,
        "validate_readonly_identity",
        lambda conn: events.append(("identity", conn)),
    )

    result = runner.execute_sql(
        "SELECT 1;",
        "diagnostic",
    )

    assert result["success"] is True

    identity_index = next(
        index
        for index, event in enumerate(events)
        if event[0] == "identity"
    )
    execute_index = next(
        index
        for index, event in enumerate(events)
        if event[0] == "execute"
    )

    assert identity_index < execute_index


def test_reporte_no_exige_configuracion_sql(
    monkeypatch,
    tmp_path,
):
    monkeypatch.setattr(runner, "REPORT_DIR", tmp_path)

    def missing_config():
        raise RuntimeError("config ausente")

    monkeypatch.setattr(
        runner,
        "get_edarsahub_sql_config",
        missing_config,
    )

    script = tmp_path / "diagnostic.sql"
    script.write_text("SELECT 1;", encoding="utf-8")

    report = runner.write_report(
        script,
        "dry-run",
        "SELECT 1;",
        {
            "batches": 1,
            "message": "Dry-run",
            "results": [],
        },
        None,
    )

    content = report.read_text(encoding="utf-8")
    assert "NO_DEFINIDO" in content


def test_validate_ignora_tokens_peligrosos_en_comentarios():
    runner.validate_sql_safety(
        """
        -- DROP TABLE dbo.NoDebeContar;
        /*
        UPDATE dbo.NoDebeContar
        SET valor = 1;
        */
        SELECT 1;
        """,
        "validate",
    )


@pytest.mark.parametrize(
    "sql",
    [
        "DROP TABLE dbo.DebeBloquearse;",
        (
            "UPDATE dbo.DebeBloquearse "
            "SET valor = 1;"
        ),
        (
            "DELETE FROM dbo.DebeBloquearse "
            "WHERE id = 1;"
        ),
    ],
)
def test_validate_sigue_bloqueando_sql_ejecutable(sql):
    with pytest.raises(RuntimeError):
        runner.validate_sql_safety(
            sql,
            "validate",
        )


def test_migrate_hace_driver_commit_y_no_rollback(monkeypatch):
    events = []

    class FakeCursor:
        description = None
        rowcount = 1

        def execute(self, sql):
            events.append(("execute", sql))

        def close(self):
            events.append(("cursor_close", None))

    class FakeConnection:
        def cursor(self, as_dict=False):
            events.append(("cursor", as_dict))
            return FakeCursor()

        def commit(self):
            events.append(("commit", None))

        def rollback(self):
            events.append(("rollback", None))

        def close(self):
            events.append(("connection_close", None))

    connection = FakeConnection()

    monkeypatch.setattr(
        runner,
        "get_connection",
        lambda mode: connection,
    )

    result = runner.execute_sql(
        "UPDATE dbo.Tabla SET Activo = 0 WHERE Id = 1;",
        "migrate",
    )

    assert result["success"] is True
    assert result["mode"] == "migrate"

    names = [event[0] for event in events]

    assert "execute" in names
    assert "commit" in names
    assert "rollback" not in names
    assert names.index("execute") < names.index("commit")
    assert names.index("commit") < names.index("connection_close")


def test_migrate_hace_rollback_si_falla_batch(monkeypatch):
    events = []

    class FakeCursor:
        description = None
        rowcount = 0

        def execute(self, sql):
            events.append(("execute", sql))
            raise RuntimeError("fallo controlado")

        def close(self):
            events.append(("cursor_close", None))

    class FakeConnection:
        def cursor(self, as_dict=False):
            events.append(("cursor", as_dict))
            return FakeCursor()

        def commit(self):
            events.append(("commit", None))

        def rollback(self):
            events.append(("rollback", None))

        def close(self):
            events.append(("connection_close", None))

    connection = FakeConnection()

    monkeypatch.setattr(
        runner,
        "get_connection",
        lambda mode: connection,
    )

    with pytest.raises(RuntimeError):
        runner.execute_sql(
            "UPDATE dbo.Tabla SET Activo = 0 WHERE Id = 1;",
            "migrate",
        )

    names = [event[0] for event in events]

    assert "execute" in names
    assert "rollback" in names
    assert "commit" not in names
    assert names.index("execute") < names.index("rollback")
    assert names.index("rollback") < names.index("connection_close")


def test_get_connection_migrate_usa_autocommit_false(monkeypatch):
    calls = []

    monkeypatch.setattr(
        runner,
        "get_int_env",
        lambda name, default: default,
    )

    monkeypatch.setattr(
        runner,
        "get_edarsahub_pymssql_connection",
        lambda **kwargs: calls.append(kwargs) or object(),
    )

    connection = runner.get_connection("migrate")

    assert connection is not None
    assert len(calls) == 1
    assert calls[0]["autocommit"] is False
