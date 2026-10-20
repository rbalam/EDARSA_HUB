import builtins
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

import core.sql_first.connection_factory as factory_module
import core.sql_first.db as db_module
from core.config.edarsahub_config import (
    get_edarsahub_sql_config,
)


BACKEND = Path(__file__).parents[1]


def _source(relative_path: str) -> str:
    return (
        BACKEND / relative_path
    ).read_text(
        encoding="utf-8",
        errors="replace",
    )


def test_db_es_fachada_sin_drivers_directos():
    source = _source("core/sql_first/db.py")

    assert "pyodbc.connect" not in source
    assert "pymssql.connect" not in source
    assert "get_edarsahub_connection" in source


def test_connection_factory_es_unico_adaptador_del_lote():
    source = _source(
        "core/sql_first/connection_factory.py"
    )

    assert "from core.sql_first.db" not in source
    assert "pyodbc.connect" in source
    assert "pymssql.connect" in source


def test_db_delega_en_factory(monkeypatch):
    expected = object()
    calls = []

    def fake_factory(profile="default"):
        calls.append(profile)
        return expected

    monkeypatch.setattr(
        db_module,
        "get_edarsahub_connection",
        fake_factory,
    )

    assert db_module.get_sql_connection("default") is expected
    assert calls == ["default"]

def _fake_config():
    return SimpleNamespace(
        host="sql.internal",
        port=1433,
        database="EDARSAHUB",
        user="HRLectura",
        password="test-secret",
    )


def test_fallback_a_pymssql_si_pyodbc_no_importa(
    monkeypatch,
):
    expected_connection = object()
    pymssql_calls = []

    def pymssql_connect(**kwargs):
        pymssql_calls.append(kwargs)
        return expected_connection

    monkeypatch.setattr(
        factory_module,
        "get_edarsahub_sql_config",
        lambda profile="default": _fake_config(),
    )
    monkeypatch.setitem(
        sys.modules,
        "pymssql",
        SimpleNamespace(connect=pymssql_connect),
    )

    original_import = builtins.__import__

    def controlled_import(
        name,
        globals=None,
        locals=None,
        fromlist=(),
        level=0,
    ):
        if name == "pyodbc":
            raise ImportError("pyodbc no disponible")

        return original_import(
            name,
            globals,
            locals,
            fromlist,
            level,
        )

    monkeypatch.setattr(
        builtins,
        "__import__",
        controlled_import,
    )

    result = factory_module.get_edarsahub_connection()

    assert result is expected_connection
    assert len(pymssql_calls) == 1
    assert pymssql_calls[0]["database"] == "EDARSAHUB"


def test_fallback_si_driver_odbc_17_no_existe(
    monkeypatch,
):
    expected_connection = object()
    pymssql_calls = []

    fake_pyodbc = SimpleNamespace(
        drivers=lambda: [
            "ODBC Driver 18 for SQL Server",
        ],
        connect=lambda *args, **kwargs: (
            pytest.fail(
                "pyodbc.connect no debe ejecutarse "
                "sin ODBC Driver 17"
            )
        ),
    )

    def pymssql_connect(**kwargs):
        pymssql_calls.append(kwargs)
        return expected_connection

    monkeypatch.setattr(
        factory_module,
        "get_edarsahub_sql_config",
        lambda profile="default": _fake_config(),
    )
    monkeypatch.setitem(
        sys.modules,
        "pyodbc",
        fake_pyodbc,
    )
    monkeypatch.setitem(
        sys.modules,
        "pymssql",
        SimpleNamespace(connect=pymssql_connect),
    )

    result = factory_module.get_edarsahub_connection()

    assert result is expected_connection
    assert len(pymssql_calls) == 1


def test_no_oculta_error_real_de_pyodbc(
    monkeypatch,
):
    pymssql_calls = []

    def failing_pyodbc_connect(*args, **kwargs):
        raise RuntimeError("authentication failed")

    fake_pyodbc = SimpleNamespace(
        drivers=lambda: [
            factory_module.ODBC_DRIVER_NAME,
        ],
        connect=failing_pyodbc_connect,
    )

    def pymssql_connect(**kwargs):
        pymssql_calls.append(kwargs)
        return object()

    monkeypatch.setattr(
        factory_module,
        "get_edarsahub_sql_config",
        lambda profile="default": _fake_config(),
    )
    monkeypatch.setitem(
        sys.modules,
        "pyodbc",
        fake_pyodbc,
    )
    monkeypatch.setitem(
        sys.modules,
        "pymssql",
        SimpleNamespace(connect=pymssql_connect),
    )

    with pytest.raises(
        RuntimeError,
        match="authentication failed",
    ):
        factory_module.get_edarsahub_connection()

    assert pymssql_calls == []


def test_no_oculta_error_al_enumerar_drivers(
    monkeypatch,
):
    pymssql_calls = []

    def failing_drivers():
        raise RuntimeError("driver registry unavailable")

    fake_pyodbc = SimpleNamespace(
        drivers=failing_drivers,
        connect=lambda *args, **kwargs: object(),
    )

    def pymssql_connect(**kwargs):
        pymssql_calls.append(kwargs)
        return object()

    monkeypatch.setattr(
        factory_module,
        "get_edarsahub_sql_config",
        lambda profile="default": _fake_config(),
    )
    monkeypatch.setitem(
        sys.modules,
        "pyodbc",
        fake_pyodbc,
    )
    monkeypatch.setitem(
        sys.modules,
        "pymssql",
        SimpleNamespace(connect=pymssql_connect),
    )

    with pytest.raises(
        RuntimeError,
        match="driver registry unavailable",
    ):
        factory_module.get_edarsahub_connection()

    assert pymssql_calls == []

@pytest.mark.parametrize(
    "profile",
    [
        "gptread",
        "gptwrite",
        "GptLectura",
        "GptEscritura",
    ],
)
def test_rechaza_perfiles_sql_alternativos(profile):
    with pytest.raises(
        ValueError,
        match="Perfil EDARSAHUB SQL no soportado",
    ):
        get_edarsahub_sql_config(profile)


def test_writer_profile_reuses_default_transport_and_dedicated_credentials(
    monkeypatch,
):
    values = {
        "EDARSAHUB_SQL_HOST": "canonical-host",
        "EDARSAHUB_SQL_PORT": "1444",
        "EDARSAHUB_SQL_DATABASE": "EDARSAHUB",
        "EDARSAHUB_SQL_USER": "HRLectura",
        "EDARSAHUB_SQL_PASSWORD": "readonly-secret",
        "EDARSAHUB_SQL_WRITER_USER": "GptEscritura",
        "EDARSAHUB_SQL_WRITER_PASSWORD": "writer-secret",
    }

    for name, value in values.items():
        monkeypatch.setenv(name, value)

    cfg = get_edarsahub_sql_config("writer")

    assert cfg.profile == "writer"
    assert cfg.host == "canonical-host"
    assert cfg.port == 1444
    assert cfg.database == "EDARSAHUB"
    assert cfg.user == "GptEscritura"
    assert cfg.password == "writer-secret"


def test_writer_profile_fails_closed_when_dedicated_credentials_missing(
    monkeypatch,
):
    values = {
        "EDARSAHUB_SQL_HOST": "canonical-host",
        "EDARSAHUB_SQL_DATABASE": "EDARSAHUB",
        "EDARSAHUB_SQL_USER": "HRLectura",
        "EDARSAHUB_SQL_PASSWORD": "readonly-secret",
    }

    for name, value in values.items():
        monkeypatch.setenv(name, value)

    monkeypatch.delenv("EDARSAHUB_SQL_WRITER_USER", raising=False)
    monkeypatch.delenv("EDARSAHUB_SQL_WRITER_PASSWORD", raising=False)

    with pytest.raises(
        RuntimeError,
        match="EDARSAHUB_SQL_WRITER_USER",
    ):
        get_edarsahub_sql_config("writer")
