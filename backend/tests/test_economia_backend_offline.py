import asyncio
import importlib
import os
import sys
from datetime import date
from decimal import Decimal
from unittest.mock import Mock

import pytest
from fastapi import HTTPException


# El runtime real carga estas variables antes de importar RBAC.
# Para esta suite offline solo se definen valores sintéticos locales;
# nunca se abre SQL ni HTTP real.
os.environ.setdefault("EDARSAHUB_SQL_HOST", "offline.invalid")
os.environ.setdefault("EDARSAHUB_SQL_PORT", "1433")
os.environ.setdefault("EDARSAHUB_SQL_DATABASE", "EDARSAHUB")
os.environ.setdefault("EDARSAHUB_SQL_USER", "offline")
os.environ.setdefault("EDARSAHUB_SQL_PASSWORD", "offline")
os.environ.setdefault(
    "JWT_SECRET",
    "offline-test-secret-offline-test-secret-123456789",
)


repository = importlib.import_module(
    "modules.economia.repository"
)
service = importlib.import_module(
    "modules.economia.service"
)
routes = importlib.import_module(
    "modules.economia.routes"
)


def run(coro):
    return asyncio.run(coro)


def test_repository_listar_series_parameter_contract(monkeypatch):
    captured = {}

    def fake_query(sql, params=()):
        captured["sql"] = sql
        captured["params"] = tuple(params)

        return [
            {
                "id": 10,
                "codigo_canonico": "INPC_MX",
                "nombre": "INPC",
                "unidad_medida": "INDICE",
                "frecuencia": "MENSUAL",
                "activo": True,
            }
        ]

    monkeypatch.setattr(
        repository,
        "_query",
        fake_query,
    )

    result = repository.EconomiaRepository.listar_series(
        activo=True,
        limite=25,
    )

    assert result[0]["id"] == 10
    assert "FROM dbo.Economia_Series s" in captured["sql"]
    assert "s.Activo = %s" in captured["sql"]
    assert "TOP (%s)" in captured["sql"]
    assert captured["params"] == (25, 1)


def test_repository_listar_series_all_statuses(monkeypatch):
    captured = {}

    def fake_query(sql, params=()):
        captured["sql"] = sql
        captured["params"] = tuple(params)
        return []

    monkeypatch.setattr(
        repository,
        "_query",
        fake_query,
    )

    result = repository.EconomiaRepository.listar_series(
        activo=None,
        limite=100,
    )

    assert result == []
    assert "s.Activo = %s" not in captured["sql"]
    assert captured["params"] == (100,)


def test_repository_obtener_serie_parameter_contract(monkeypatch):
    captured = {}

    def fake_query(sql, params=()):
        captured["sql"] = sql
        captured["params"] = tuple(params)

        return [
            {
                "id": 42,
                "codigo_canonico": "PIB_MX",
                "nombre": "PIB",
                "unidad_medida": "PORCENTAJE",
                "frecuencia": "TRIMESTRAL",
                "activo": True,
            }
        ]

    monkeypatch.setattr(
        repository,
        "_query",
        fake_query,
    )

    result = repository.EconomiaRepository.obtener_serie(
        "42"
    )

    assert result["id"] == 42
    assert "WHERE s.SerieEconomicaID = %s" in captured["sql"]
    assert captured["params"] == ("42",)


def test_repository_obtener_serie_none(monkeypatch):
    monkeypatch.setattr(
        repository,
        "_query",
        lambda sql, params=(): [],
    )

    assert (
        repository.EconomiaRepository.obtener_serie(
            "999"
        )
        is None
    )


def test_repository_listar_valores_full_range(monkeypatch):
    captured = {}

    def fake_query(sql, params=()):
        captured["sql"] = sql
        captured["params"] = tuple(params)

        return [
            {
                "serie_id": 5,
                "periodo": date(2026, 7, 1),
                "valor": 4.25,
                "version_dato": 1,
                "es_revision": False,
                "preliminar": False,
                "estimado": False,
            }
        ]

    monkeypatch.setattr(
        repository,
        "_query",
        fake_query,
    )

    desde = date(2026, 1, 1)
    hasta = date(2026, 7, 31)

    result = repository.EconomiaRepository.listar_valores(
        serie_id="5",
        desde=desde,
        hasta=hasta,
        limite=75,
    )

    assert result[0]["serie_id"] == 5

    sql = captured["sql"]

    assert "v.SerieEconomicaID = %s" in sql
    assert "v.FechaPeriodo >= %s" in sql
    assert "v.FechaPeriodo <= %s" in sql
    assert "v.Activo = 1" in sql
    assert "TOP (%s)" in sql

    assert captured["params"] == (
        "5",
        desde,
        hasta,
        75,
    )


def test_repository_listar_valores_without_optional_dates(monkeypatch):
    captured = {}

    def fake_query(sql, params=()):
        captured["sql"] = sql
        captured["params"] = tuple(params)
        return []

    monkeypatch.setattr(
        repository,
        "_query",
        fake_query,
    )

    repository.EconomiaRepository.listar_valores(
        serie_id="8",
        limite=50,
    )

    assert "v.FechaPeriodo >= %s" not in captured["sql"]
    assert "v.FechaPeriodo <= %s" not in captured["sql"]
    assert captured["params"] == ("8", 50)


def test_repository_contextos_contract(monkeypatch):
    captured = {}

    def fake_query(sql, params=()):
        captured["sql"] = sql
        captured["params"] = tuple(params)

        return [
            {
                "id": 1,
                "pais_id": None,
                "empresa_id": 2,
                "unidad_negocio_id": None,
                "moneda_id": 1,
                "principal": True,
                "activo": True,
            }
        ]

    monkeypatch.setattr(
        repository,
        "_query",
        fake_query,
    )

    result = (
        repository.EconomiaRepository
        .listar_contextos_activos()
    )

    assert result[0]["id"] == 1
    assert "dbo.Economia_ContextoOperativo" in captured["sql"]
    assert "c.Activo = 1" in captured["sql"]
    assert "c.EsPrincipal DESC" in captured["sql"]
    assert captured["params"] == ()


def test_query_uses_canonical_helper_without_real_io(monkeypatch):
    captured = {}

    def fake_execute(
        host,
        port,
        database,
        username,
        password,
        sql,
        params,
    ):
        captured.update(
            {
                "host": host,
                "port": port,
                "database": database,
                "username": username,
                "password": password,
                "sql": sql,
                "params": params,
            }
        )

        return [{"ok": 1}]

    monkeypatch.setenv(
        "EDARSAHUB_SQL_HOST",
        "canonical-host",
    )
    monkeypatch.setenv(
        "EDARSAHUB_SQL_PORT",
        "1433",
    )
    monkeypatch.setenv(
        "EDARSAHUB_SQL_DATABASE",
        "EDARSAHUB",
    )
    monkeypatch.setenv(
        "EDARSAHUB_SQL_USER",
        "HRLectura",
    )
    monkeypatch.setenv(
        "EDARSAHUB_SQL_PASSWORD",
        "synthetic-secret",
    )

    monkeypatch.setattr(
        repository,
        "execute_sql_query_params",
        fake_execute,
    )

    rows = repository._query(
        "SELECT %s AS x",
        (7,),
    )

    assert rows == [{"ok": 1}]
    assert captured["host"] == "canonical-host"
    assert captured["port"] == 1433
    assert captured["database"] == "EDARSAHUB"
    assert captured["username"] == "HRLectura"
    assert captured["sql"] == "SELECT %s AS x"
    assert captured["params"] == (7,)


def test_query_fails_closed_when_config_missing(monkeypatch):
    for key in (
        "EDARSAHUB_SQL_HOST",
        "EDARSAHUB_SQL_PORT",
        "EDARSAHUB_SQL_DATABASE",
        "EDARSAHUB_SQL_USER",
        "EDARSAHUB_SQL_PASSWORD",
    ):
        monkeypatch.delenv(
            key,
            raising=False,
        )

    with pytest.raises(
        RuntimeError,
        match="Configuracion SQL EDARSAHUB incompleta",
    ):
        repository._conn()


def test_service_delegates_listar_series(monkeypatch):
    expected = [{"id": 1}]

    mock = Mock(
        return_value=expected
    )

    monkeypatch.setattr(
        repository.EconomiaRepository,
        "listar_series",
        mock,
    )

    result = service.EconomiaService.listar_series(
        activo=False,
        limite=12,
    )

    assert result == expected

    mock.assert_called_once_with(
        activo=False,
        limite=12,
    )


def test_service_delegates_listar_valores(monkeypatch):
    expected = [{"serie_id": 2}]

    mock = Mock(
        return_value=expected
    )

    monkeypatch.setattr(
        repository.EconomiaRepository,
        "listar_valores",
        mock,
    )

    desde = date(2026, 1, 1)
    hasta = date(2026, 2, 1)

    result = service.EconomiaService.listar_valores(
        serie_id="2",
        desde=desde,
        hasta=hasta,
        limite=20,
    )

    assert result == expected

    mock.assert_called_once_with(
        serie_id="2",
        desde=desde,
        hasta=hasta,
        limite=20,
    )


def test_route_obtener_serie_404(monkeypatch):
    monkeypatch.setattr(
        routes.EconomiaService,
        "obtener_serie",
        Mock(return_value=None),
    )

    with pytest.raises(
        HTTPException
    ) as exc:
        run(
            routes.obtener_serie(
                serie_id="999",
                _={"user_id": "offline"},
            )
        )

    assert exc.value.status_code == 404
    assert (
        exc.value.detail
        == "Serie economica no encontrada"
    )


def test_route_obtener_serie_success(monkeypatch):
    expected = {
        "id": 10,
        "codigo_canonico": "INPC_MX",
    }

    monkeypatch.setattr(
        routes.EconomiaService,
        "obtener_serie",
        Mock(return_value=expected),
    )

    result = run(
        routes.obtener_serie(
            serie_id="10",
            _={"user_id": "offline"},
        )
    )

    assert result == expected


def test_route_listar_valores_rejects_invalid_range():
    with pytest.raises(
        HTTPException
    ) as exc:
        run(
            routes.listar_valores(
                serie_id="10",
                desde=date(2026, 8, 1),
                hasta=date(2026, 7, 1),
                limite=100,
                _={"user_id": "offline"},
            )
        )

    assert exc.value.status_code == 422
    assert (
        exc.value.detail
        == "El rango de fechas es invalido"
    )


def test_route_listar_valores_success(monkeypatch):
    expected = [
        {
            "serie_id": 10,
            "valor": 123.45,
        }
    ]

    mock = Mock(
        return_value=expected
    )

    monkeypatch.setattr(
        routes.EconomiaService,
        "listar_valores",
        mock,
    )

    desde = date(2026, 1, 1)
    hasta = date(2026, 7, 31)

    result = run(
        routes.listar_valores(
            serie_id="10",
            desde=desde,
            hasta=hasta,
            limite=300,
            _={"user_id": "offline"},
        )
    )

    assert result == expected

    mock.assert_called_once_with(
        serie_id="10",
        desde=desde,
        hasta=hasta,
        limite=300,
    )


def test_route_listar_series_success(monkeypatch):
    expected = [{"id": 1}]

    mock = Mock(
        return_value=expected
    )

    monkeypatch.setattr(
        routes.EconomiaService,
        "listar_series",
        mock,
    )

    result = run(
        routes.listar_series(
            activo=True,
            limite=80,
            _={"user_id": "offline"},
        )
    )

    assert result == expected

    mock.assert_called_once_with(
        activo=True,
        limite=80,
    )


def test_route_contextos_success(monkeypatch):
    expected = [{"id": 1}]

    mock = Mock(
        return_value=expected
    )

    monkeypatch.setattr(
        routes.EconomiaService,
        "listar_contextos_activos",
        mock,
    )

    result = run(
        routes.listar_contextos(
            _={"user_id": "offline"},
        )
    )

    assert result == expected


def test_routes_expose_exact_permission_dependencies():
    text = (
        routes.__file__
    )

    source = open(
        text,
        encoding="utf-8",
    ).read()

    expected = {
        "economia.indicadores.leer",
        "economia.series.leer",
        "economia.contexto.administrar",
    }

    for permission in expected:
        assert permission in source

    assert "require_admin" not in source


def test_no_real_io_modules_used():
    forbidden_loaded = {
        "pyodbc",
        "pymongo",
        "motor.motor_asyncio",
    }

    assert not (
        forbidden_loaded
        & set(sys.modules)
    )


def test_persistir_valor_versionado_nuevo(monkeypatch):
    repository = __import__("modules.economia.repository", fromlist=["*"])

    class Cursor:
        def __init__(self):
            self.calls = []

        def execute(self, sql, params=()):
            self.calls.append((sql, params))

        def fetchone(self):
            return None

    class Connection:
        def __init__(self):
            self.cursor_obj = Cursor()
            self.commits = 0
            self.rollbacks = 0

        def cursor(self):
            return self.cursor_obj

        def commit(self):
            self.commits += 1

        def rollback(self):
            self.rollbacks += 1

        def close(self):
            pass

    conn = Connection()

    class Context:
        def __enter__(self):
            return conn

        def __exit__(self, exc_type, exc, tb):
            conn.close()

    monkeypatch.setattr(
        repository,
        "sql_connection",
        lambda: Context(),
    )

    result = repository.EconomiaRepository.persistir_valor_versionado(
        10,
        date(2026, 7, 1),
        123.45,
        fuente_dato_id="FUENTE-1",
    )

    assert result == {
        "insertado": True,
        "version_dato": 1,
        "es_revision": False,
    }
    assert conn.commits == 1
    assert conn.rollbacks == 0
    assert len(conn.cursor_obj.calls) == 2
    assert "INSERT INTO dbo.Economia_Valores" in conn.cursor_obj.calls[1][0]


def test_persistir_valor_versionado_revision(monkeypatch):
    repository = __import__("modules.economia.repository", fromlist=["*"])

    class Cursor:
        def __init__(self):
            self.calls = []

        def execute(self, sql, params=()):
            self.calls.append((sql, params))

        def fetchone(self):
            return (1001, 120.00, 3)

    class Connection:
        def __init__(self):
            self.cursor_obj = Cursor()
            self.commits = 0
            self.rollbacks = 0

        def cursor(self):
            return self.cursor_obj

        def commit(self):
            self.commits += 1

        def rollback(self):
            self.rollbacks += 1

        def close(self):
            pass

    conn = Connection()

    class Context:
        def __enter__(self):
            return conn

        def __exit__(self, exc_type, exc, tb):
            conn.close()

    monkeypatch.setattr(
        repository,
        "sql_connection",
        lambda: Context(),
    )

    result = repository.EconomiaRepository.persistir_valor_versionado(
        10,
        date(2026, 7, 1),
        125.00,
    )

    assert result == {
        "insertado": True,
        "version_dato": 4,
        "es_revision": True,
    }
    assert conn.commits == 1
    assert conn.rollbacks == 0
    assert len(conn.cursor_obj.calls) == 3
    assert "UPDATE dbo.Economia_Valores" in conn.cursor_obj.calls[1][0]
    assert "INSERT INTO dbo.Economia_Valores" in conn.cursor_obj.calls[2][0]


def test_persistir_valor_versionado_rollback(monkeypatch):
    repository = __import__("modules.economia.repository", fromlist=["*"])

    class Cursor:
        def execute(self, sql, params=()):
            raise RuntimeError("fallo simulado")

        def fetchone(self):
            return None

    class Connection:
        def __init__(self):
            self.commits = 0
            self.rollbacks = 0

        def cursor(self):
            return Cursor()

        def commit(self):
            self.commits += 1

        def rollback(self):
            self.rollbacks += 1

        def close(self):
            pass

    conn = Connection()

    class Context:
        def __enter__(self):
            return conn

        def __exit__(self, exc_type, exc, tb):
            conn.close()

    monkeypatch.setattr(
        repository,
        "sql_connection",
        lambda: Context(),
    )

    with pytest.raises(RuntimeError, match="fallo simulado"):
        repository.EconomiaRepository.persistir_valor_versionado(
            10,
            date(2026, 7, 1),
            123.45,
        )

    assert conn.commits == 0
    assert conn.rollbacks == 1


def test_persistir_valor_versionado_mismo_valor_no_duplica(monkeypatch):
    repository = __import__(
        "modules.economia.repository",
        fromlist=["*"],
    )

    class Cursor:
        def __init__(self):
            self.calls = []

        def execute(self, sql, params=()):
            self.calls.append((sql, params))

        def fetchone(self):
            return (1001, 123.45, 3)

    class Connection:
        def __init__(self):
            self.cursor_obj = Cursor()
            self.commits = 0
            self.rollbacks = 0

        def cursor(self):
            return self.cursor_obj

        def commit(self):
            self.commits += 1

        def rollback(self):
            self.rollbacks += 1

        def close(self):
            pass

    conn = Connection()

    class Context:
        def __enter__(self):
            return conn

        def __exit__(self, exc_type, exc, tb):
            conn.close()

    monkeypatch.setattr(
        repository,
        "sql_connection",
        lambda: Context(),
    )

    result = repository.EconomiaRepository.persistir_valor_versionado(
        10,
        date(2026, 7, 1),
        123.45,
    )

    assert result == {
        "insertado": False,
        "version_dato": 3,
        "es_revision": False,
    }

    assert conn.commits == 1
    assert conn.rollbacks == 0

    # Solo debe existir el SELECT inicial.
    assert len(conn.cursor_obj.calls) == 1

    sql = conn.cursor_obj.calls[0][0]

    assert "SELECT TOP (1)" in sql
    assert "UPDLOCK" in sql
    assert "HOLDLOCK" in sql

    all_sql = "\n".join(
        call[0]
        for call in conn.cursor_obj.calls
    )

    assert "UPDATE dbo.Economia_Valores" not in all_sql
    assert "INSERT INTO dbo.Economia_Valores" not in all_sql


def test_resolver_proveedor_serie_usa_cadena_canonica(monkeypatch):
    repository = __import__(
        "modules.economia.repository",
        fromlist=["*"],
    )

    captured = {}

    def fake_query(sql, params=()):
        captured["sql"] = sql
        captured["params"] = params
        return [{
            "serie_id": 10,
            "codigo_canonico": "MX.INPC",
            "codigo_proveedor": "SP1",
            "proveedor_id": 1,
            "proveedor_codigo": "PROVEEDOR",
            "server_conexion_id": "abc",
            "conexion_id": "abc",
            "conexion_activa": True,
        }]

    monkeypatch.setattr(
        repository,
        "_query",
        fake_query,
    )

    result = (
        repository.EconomiaRepository
        .resolver_proveedor_serie(10)
    )

    assert result["serie_id"] == 10
    assert captured["params"] == (10,)

    sql = captured["sql"]

    assert "dbo.Economia_Series" in sql
    assert "dbo.Economia_Proveedores" in sql
    assert "dbo.Servidores_Conexiones" in sql

    assert (
        "p.ProveedorEconomicoID = "
        "s.ProveedorEconomicoID"
    ) in sql

    assert (
        "sc.id = p.ServerConexionID"
    ) in sql

    assert "sc.api_key_encrypted AS api_key_encrypted" in sql
    assert "password_encrypted" not in sql


def test_resolver_proveedor_serie_none(monkeypatch):
    repository = __import__(
        "modules.economia.repository",
        fromlist=["*"],
    )

    monkeypatch.setattr(
        repository,
        "_query",
        lambda sql, params=(): [],
    )

    result = (
        repository.EconomiaRepository
        .resolver_proveedor_serie(999)
    )

    assert result is None


@pytest.mark.asyncio
async def test_service_resuelve_conexion_api_canonica(monkeypatch):
    service = __import__(
        "modules.economia.service",
        fromlist=["*"],
    )

    monkeypatch.setattr(
        service.EconomiaRepository,
        "resolver_proveedor_serie",
        lambda serie_id: {
            "serie_id": serie_id,
            "server_conexion_id": "conn-123",
            "conexion_id": "conn-123",
            "conexion_url": "https://api.invalid",
            "tipo_conexion": "API_LOCAL",
            "system_type": "ECONOMIA",
            "conexion_activa": True,
            "api_key_encrypted": "",
        },
    )

    result = await (
        service.EconomiaService
        .resolver_conexion_proveedor(10)
    )

    assert result["proveedor"]["serie_id"] == 10
    assert result["conexion"]["id"] == "conn-123"
    assert result["conexion"]["api_url"] == "https://api.invalid"
    assert result["api_key"] == ""



@pytest.mark.asyncio
async def test_service_resuelve_proveedor_sin_conexion(monkeypatch):
    service = __import__(
        "modules.economia.service",
        fromlist=["*"],
    )

    monkeypatch.setattr(
        service.EconomiaRepository,
        "resolver_proveedor_serie",
        lambda serie_id: {
            "serie_id": serie_id,
            "server_conexion_id": None,
        },
    )

    result = await (
        service.EconomiaService
        .resolver_conexion_proveedor(10)
    )

    assert result["conexion"] is None
    assert result["api_key"] == ""


@pytest.mark.asyncio
async def test_service_resuelve_serie_inexistente(monkeypatch):
    service = __import__(
        "modules.economia.service",
        fromlist=["*"],
    )

    monkeypatch.setattr(
        service.EconomiaRepository,
        "resolver_proveedor_serie",
        lambda serie_id: None,
    )

    result = await (
        service.EconomiaService
        .resolver_conexion_proveedor(999)
    )

    assert result is None


@pytest.mark.asyncio
async def test_contrato_http_proveedor_es_configurable(monkeypatch):
    service = __import__(
        "modules.economia.service",
        fromlist=["*"],
    )

    async def fake_resolver(serie_id):
        return {
            "proveedor": {
                "serie_id": serie_id,
                "codigo_canonico": "MX.TEST",
                "codigo_proveedor": "SERIE-EXT",
                "proveedor_codigo": "PROVEEDOR-X",
                "proveedor_tipo": "API_PUBLICA",
                "url_publica": "https://public.invalid",
                "requiere_autenticacion": True,
                "permite_backfill": True,
                "metadata_json": (
                    '{"endpoint":"/series/{codigo}",'
                    '"formato":"json"}'
                ),
            },
            "conexion": {
                "api_url": "https://api.invalid",
            },
            "api_key": "secret-test",
        }

    monkeypatch.setattr(
        service.EconomiaService,
        "resolver_conexion_proveedor",
        fake_resolver,
    )

    result = await (
        service.EconomiaService
        .resolver_contrato_http_proveedor(10)
    )

    assert result["base_url"] == "https://api.invalid"
    assert result["codigo_proveedor"] == "SERIE-EXT"
    assert result["proveedor_codigo"] == "PROVEEDOR-X"
    assert result["requiere_autenticacion"] is True
    assert result["permite_backfill"] is True
    assert result["api_key"] == "secret-test"
    assert result["metadata"] == {
        "endpoint": "/series/{codigo}",
        "formato": "json",
    }


@pytest.mark.asyncio
async def test_contrato_http_usa_url_publica_sin_conexion(monkeypatch):
    service = __import__(
        "modules.economia.service",
        fromlist=["*"],
    )

    async def fake_resolver(serie_id):
        return {
            "proveedor": {
                "serie_id": serie_id,
                "codigo_canonico": "TEST",
                "codigo_proveedor": "EXT",
                "proveedor_codigo": "PUBLICO",
                "proveedor_tipo": "API_PUBLICA",
                "url_publica": "https://public.invalid",
                "requiere_autenticacion": False,
                "permite_backfill": True,
                "metadata_json": None,
            },
            "conexion": None,
            "api_key": "",
        }

    monkeypatch.setattr(
        service.EconomiaService,
        "resolver_conexion_proveedor",
        fake_resolver,
    )

    result = await (
        service.EconomiaService
        .resolver_contrato_http_proveedor(20)
    )

    assert result["base_url"] == "https://public.invalid"
    assert result["api_key"] == ""
    assert result["metadata"] == {}


@pytest.mark.asyncio
async def test_contrato_http_rechaza_metadata_invalida(monkeypatch):
    service = __import__(
        "modules.economia.service",
        fromlist=["*"],
    )

    async def fake_resolver(serie_id):
        return {
            "proveedor": {
                "serie_id": serie_id,
                "metadata_json": "{invalido",
            },
            "conexion": None,
            "api_key": "",
        }

    monkeypatch.setattr(
        service.EconomiaService,
        "resolver_conexion_proveedor",
        fake_resolver,
    )

    with pytest.raises(
        ValueError,
        match="MetadataJSON",
    ):
        await (
            service.EconomiaService
            .resolver_contrato_http_proveedor(30)
        )


@pytest.mark.asyncio
async def test_cliente_http_generico_offline(monkeypatch):
    service = __import__(
        "modules.economia.service",
        fromlist=["*"],
    )

    async def fake_contract(serie_id):
        return {
            "serie_id": serie_id,
            "codigo_proveedor": "ABC123",
            "base_url": "https://example.invalid",
            "requiere_autenticacion": True,
            "api_key": "secret-test",
            "metadata": {
                "endpoint": "/series/{codigo}",
                "params": {"format": "json"},
                "auth": {
                    "header": "X-Test-Key",
                    "prefix": "Token ",
                },
                "timeout_seconds": 15,
            },
        }

    monkeypatch.setattr(
        service.EconomiaService,
        "resolver_contrato_http_proveedor",
        fake_contract,
    )

    captured = {}

    class Response:
        status_code = 200

        def raise_for_status(self):
            pass

        def json(self):
            return {"ok": True}

    class Client:
        def __init__(self, timeout):
            captured["timeout"] = timeout

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

        async def get(self, url, params=None, headers=None):
            captured["url"] = url
            captured["params"] = params
            captured["headers"] = headers
            return Response()

    monkeypatch.setattr(
        service.httpx,
        "AsyncClient",
        Client,
    )

    result = await (
        service.EconomiaService
        .consultar_proveedor_http(10)
    )

    assert captured["url"] == (
        "https://example.invalid/series/ABC123"
    )
    assert captured["params"] == {"format": "json"}
    assert captured["headers"]["X-Test-Key"] == (
        "Token secret-test"
    )
    assert captured["timeout"] == 15.0
    assert result["status_code"] == 200
    assert result["data"] == {"ok": True}


@pytest.mark.asyncio
async def test_cliente_http_rechaza_endpoint_ausente(monkeypatch):
    service = __import__(
        "modules.economia.service",
        fromlist=["*"],
    )

    async def fake_contract(serie_id):
        return {
            "base_url": "https://example.invalid",
            "requiere_autenticacion": False,
            "api_key": "",
            "metadata": {},
        }

    monkeypatch.setattr(
        service.EconomiaService,
        "resolver_contrato_http_proveedor",
        fake_contract,
    )

    with pytest.raises(
        ValueError,
        match="endpoint",
    ):
        await (
            service.EconomiaService
            .consultar_proveedor_http(10)
        )


@pytest.mark.asyncio
async def test_cliente_http_no_ejecuta_auth_hardcodeada(monkeypatch):
    service = __import__(
        "modules.economia.service",
        fromlist=["*"],
    )

    async def fake_contract(serie_id):
        return {
            "codigo_proveedor": "ABC",
            "base_url": "https://example.invalid",
            "requiere_autenticacion": False,
            "api_key": "",
            "metadata": {
                "endpoint": "/data/{codigo}",
                "headers": {
                    "Accept": "application/json",
                },
            },
        }

    monkeypatch.setattr(
        service.EconomiaService,
        "resolver_contrato_http_proveedor",
        fake_contract,
    )

    captured = {}

    class Response:
        status_code = 200

        def raise_for_status(self):
            pass

        def json(self):
            return {}

    class Client:
        def __init__(self, timeout):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

        async def get(self, url, params=None, headers=None):
            captured["headers"] = headers
            return Response()

    monkeypatch.setattr(
        service.httpx,
        "AsyncClient",
        Client,
    )

    await (
        service.EconomiaService
        .consultar_proveedor_http(10)
    )

    assert captured["headers"] == {
        "Accept": "application/json",
    }
    assert "x-api-key" not in captured["headers"]
    assert "Authorization" not in captured["headers"]


def test_normalizar_observaciones_generico():
    service = __import__(
        "modules.economia.service",
        fromlist=["*"],
    )

    data = {
        "response": {
            "items": [
                {
                    "fecha": "2026-07-01",
                    "valor": "123.4500",
                    "id": "OBS-1",
                    "preliminar": True,
                },
                {
                    "fecha": "2026-08-01",
                    "valor": 124.75,
                    "id": "OBS-2",
                    "preliminar": False,
                },
            ]
        }
    }

    metadata = {
        "normalizacion": {
            "items_path": "response.items",
            "fecha_field": "fecha",
            "valor_field": "valor",
            "fuente_id_field": "id",
            "preliminar_field": "preliminar",
        }
    }

    result = (
        service.EconomiaService
        .normalizar_observaciones(
            10,
            data,
            metadata,
        )
    )

    assert len(result) == 2

    assert result[0]["serie_id"] == 10
    assert str(result[0]["fecha_periodo"]) == "2026-07-01"
    assert str(result[0]["valor"]) == "123.4500"
    assert result[0]["fuente_dato_id"] == "OBS-1"
    assert result[0]["preliminar"] is True


def test_normalizar_observaciones_rechaza_mapping_incompleto():
    service = __import__(
        "modules.economia.service",
        fromlist=["*"],
    )

    with pytest.raises(
        ValueError,
        match="normalización incompleta",
    ):
        service.EconomiaService.normalizar_observaciones(
            10,
            [],
            {"normalizacion": {}},
        )


@pytest.mark.asyncio
async def test_consultar_observaciones_proveedor_offline(monkeypatch):
    service = __import__(
        "modules.economia.service",
        fromlist=["*"],
    )

    async def fake_contract(serie_id):
        return {
            "metadata": {
                "normalizacion": {
                    "items_path": "items",
                    "fecha_field": "date",
                    "valor_field": "value",
                }
            }
        }

    async def fake_http(serie_id):
        return {
            "data": {
                "items": [
                    {
                        "date": "2026-07-01",
                        "value": "10.25",
                    }
                ]
            }
        }

    monkeypatch.setattr(
        service.EconomiaService,
        "resolver_contrato_http_proveedor",
        fake_contract,
    )

    monkeypatch.setattr(
        service.EconomiaService,
        "consultar_proveedor_http",
        fake_http,
    )

    result = await (
        service.EconomiaService
        .consultar_observaciones_proveedor(10)
    )

    assert len(result) == 1
    assert result[0]["serie_id"] == 10
    assert str(result[0]["valor"]) == "10.25"


@pytest.mark.asyncio
async def test_sincronizar_serie_integra_normalizacion_y_versionado(
    monkeypatch,
):
    service = __import__(
        "modules.economia.service",
        fromlist=["*"],
    )

    async def fake_observaciones(serie_id):
        return [
            {
                "serie_id": serie_id,
                "fecha_periodo": date(2026, 7, 1),
                "valor": Decimal("10.25"),
                "periodo_codigo": "2026-07",
                "fuente_dato_id": "A",
                "preliminar": False,
                "estimado": False,
            },
            {
                "serie_id": serie_id,
                "fecha_periodo": date(2026, 8, 1),
                "valor": Decimal("11.00"),
                "periodo_codigo": "2026-08",
                "fuente_dato_id": "B",
                "preliminar": True,
                "estimado": False,
            },
        ]

    monkeypatch.setattr(
        service.EconomiaService,
        "consultar_observaciones_proveedor",
        fake_observaciones,
    )

    calls = []

    def fake_persist(**kwargs):
        calls.append(kwargs)

        if kwargs["fuente_dato_id"] == "A":
            return {
                "insertado": False,
                "version_dato": 1,
                "es_revision": False,
            }

        return {
            "insertado": True,
            "version_dato": 2,
            "es_revision": True,
        }

    monkeypatch.setattr(
        service.EconomiaRepository,
        "persistir_valor_versionado",
        fake_persist,
    )

    legacy_conn = _EconomiaBatchFakeConnection()

    monkeypatch.setattr(
        service,
        "sql_connection",
        lambda: _EconomiaBatchFakeContext(
            legacy_conn
        ),
    )

    result = await (
        service.EconomiaService
        .sincronizar_serie(
            10,
            sync_run_id="run-1",
        )
    )

    assert len(calls) == 2
    assert calls[0]["sync_run_id"] == "run-1"
    assert calls[1]["preliminar"] is True

    assert result == {
        "serie_id": 10,
        "observaciones": 2,
        "insertados": 1,
        "sin_cambio": 1,
        "revisiones": 1,
        "resultados": [
            {
                "insertado": False,
                "version_dato": 1,
                "es_revision": False,
            },
            {
                "insertado": True,
                "version_dato": 2,
                "es_revision": True,
            },
        ],
    }


@pytest.mark.asyncio
async def test_sincronizar_serie_vacia(monkeypatch):
    service = __import__(
        "modules.economia.service",
        fromlist=["*"],
    )

    async def fake_observaciones(serie_id):
        return []

    monkeypatch.setattr(
        service.EconomiaService,
        "consultar_observaciones_proveedor",
        fake_observaciones,
    )

    def forbidden_sql_connection():
        raise AssertionError(
            "No debe abrir SQL para lote vacío"
        )

    monkeypatch.setattr(
        service,
        "sql_connection",
        forbidden_sql_connection,
    )

    result = await (
        service.EconomiaService
        .sincronizar_serie(10)
    )

    assert result["observaciones"] == 0
    assert result["insertados"] == 0
    assert result["sin_cambio"] == 0
    assert result["revisiones"] == 0
    assert result["resultados"] == []


@pytest.mark.asyncio
async def test_backfill_serie_configurable_offline(monkeypatch):
    service = __import__(
        "modules.economia.service",
        fromlist=["*"],
    )

    async def fake_contract(serie_id):
        return {
            "permite_backfill": True,
            "metadata": {
                "backfill": {
                    "desde_param": "start",
                    "hasta_param": "end",
                    "date_format": "%Y-%m-%d",
                    "max_days": 365,
                },
                "normalizacion": {
                    "items_path": "items",
                    "fecha_field": "date",
                    "valor_field": "value",
                },
            },
        }

    captured = {}

    async def fake_http(serie_id, *, params_extra=None):
        captured["params"] = params_extra
        return {
            "data": {
                "items": [
                    {
                        "date": "2026-01-01",
                        "value": "10.5",
                    }
                ]
            }
        }

    monkeypatch.setattr(
        service.EconomiaService,
        "resolver_contrato_http_proveedor",
        fake_contract,
    )

    monkeypatch.setattr(
        service.EconomiaService,
        "consultar_proveedor_http",
        fake_http,
    )

    monkeypatch.setattr(
        service.EconomiaRepository,
        "persistir_valor_versionado",
        lambda **kwargs: {
            "insertado": True,
            "version_dato": 1,
            "es_revision": False,
        },
    )

    legacy_conn = _EconomiaBatchFakeConnection()

    monkeypatch.setattr(
        service,
        "sql_connection",
        lambda: _EconomiaBatchFakeContext(
            legacy_conn
        ),
    )

    result = await (
        service.EconomiaService.backfill_serie(
            10,
            date(2026, 1, 1),
            date(2026, 1, 31),
        )
    )

    assert captured["params"] == {
        "start": "2026-01-01",
        "end": "2026-01-31",
    }

    assert result["observaciones"] == 1
    assert result["insertados"] == 1
    assert result["revisiones"] == 0


@pytest.mark.asyncio
async def test_backfill_rechaza_proveedor_no_autorizado(monkeypatch):
    service = __import__(
        "modules.economia.service",
        fromlist=["*"],
    )

    async def fake_contract(serie_id):
        return {
            "permite_backfill": False,
            "metadata": {},
        }

    monkeypatch.setattr(
        service.EconomiaService,
        "resolver_contrato_http_proveedor",
        fake_contract,
    )

    with pytest.raises(
        ValueError,
        match="no permite backfill",
    ):
        await service.EconomiaService.backfill_serie(
            10,
            date(2026, 1, 1),
            date(2026, 1, 31),
        )


@pytest.mark.asyncio
async def test_backfill_rechaza_rango_superior_configurado(monkeypatch):
    service = __import__(
        "modules.economia.service",
        fromlist=["*"],
    )

    async def fake_contract(serie_id):
        return {
            "permite_backfill": True,
            "metadata": {
                "backfill": {
                    "desde_param": "from",
                    "hasta_param": "to",
                    "date_format": "%Y%m%d",
                    "max_days": 30,
                }
            },
        }

    monkeypatch.setattr(
        service.EconomiaService,
        "resolver_contrato_http_proveedor",
        fake_contract,
    )

    with pytest.raises(
        ValueError,
        match="excede máximo",
    ):
        await service.EconomiaService.backfill_serie(
            10,
            date(2026, 1, 1),
            date(2026, 3, 1),
        )


def test_routes_backfill_usa_permiso_explicito():
    from pathlib import Path

    routes = (
        Path(__file__).resolve().parents[1]
        / "modules"
        / "economia"
        / "routes.py"
    ).read_text(
        encoding="utf-8",
        errors="replace",
    )

    assert (
        'require_explicit_permission_dual(\n'
        '            "economia.backfill.ejecutar"'
        in routes
    )

    assert '@router.post("/series/{serie_id}/backfill")' in routes
    assert "require_economia_backfill_ejecutar" in routes


def test_routes_backfill_no_contiene_proveedor_hardcodeado():
    from pathlib import Path

    routes = (
        Path(__file__).resolve().parents[1]
        / "modules"
        / "economia"
        / "routes.py"
    ).read_text(
        encoding="utf-8",
        errors="replace",
    )

    assert "BANXICO" not in routes.upper()
    assert "INEGI" not in routes.upper()
    assert "FRED" not in routes.upper()


@pytest.mark.asyncio
async def test_route_backfill_delega_service(monkeypatch):
    routes = __import__(
        "modules.economia.routes",
        fromlist=["*"],
    )

    captured = {}

    async def fake_backfill(
        serie_id,
        desde,
        hasta,
        **kwargs,
    ):
        captured["serie_id"] = serie_id
        captured["desde"] = desde
        captured["hasta"] = hasta

        return {
            "serie_id": serie_id,
            "observaciones": 1,
            "insertados": 1,
        }

    monkeypatch.setattr(
        routes.EconomiaService,
        "backfill_serie",
        fake_backfill,
    )

    result = await routes.ejecutar_backfill(
        serie_id=10,
        desde=date(2026, 1, 1),
        hasta=date(2026, 1, 31),
        _={"user_id": "offline"},
    )

    assert captured == {
        "serie_id": 10,
        "desde": date(2026, 1, 1),
        "hasta": date(2026, 1, 31),
    }

    assert result["insertados"] == 1


@pytest.mark.asyncio
async def test_cliente_http_auth_path_no_expone_secreto(monkeypatch):
    service = __import__(
        "modules.economia.service",
        fromlist=["*"],
    )

    async def fake_contract(serie_id):
        return {
            "codigo_proveedor": "910406",
            "base_url": "https://example.invalid",
            "requiere_autenticacion": True,
            "api_key": "TOKEN-SECRETO",
            "metadata": {
                "endpoint": (
                    "/indicator/{codigo}/"
                    "{token}"
                ),
                "auth": {
                    "placement": "path",
                    "placeholder": "token",
                },
                "timeout_seconds": 10,
            },
        }

    monkeypatch.setattr(
        service.EconomiaService,
        "resolver_contrato_http_proveedor",
        fake_contract,
    )

    captured = {}

    class Response:
        status_code = 200

        def raise_for_status(self):
            pass

        def json(self):
            return {"ok": True}

    class Client:
        def __init__(self, timeout):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

        async def get(self, url, params=None, headers=None):
            captured["url"] = url
            return Response()

    monkeypatch.setattr(
        service.httpx,
        "AsyncClient",
        Client,
    )

    result = await (
        service.EconomiaService
        .consultar_proveedor_http(10)
    )

    assert captured["url"].endswith(
        "/indicator/910406/TOKEN-SECRETO"
    )

    assert "url" not in result

    serialized = repr(result)
    assert "TOKEN-SECRETO" not in serialized


@pytest.mark.asyncio
async def test_cliente_http_auth_query_configurable(monkeypatch):
    service = __import__(
        "modules.economia.service",
        fromlist=["*"],
    )

    async def fake_contract(serie_id):
        return {
            "codigo_proveedor": "ABC",
            "base_url": "https://example.invalid",
            "requiere_autenticacion": True,
            "api_key": "SECRET",
            "metadata": {
                "endpoint": "/data/{codigo}",
                "auth": {
                    "placement": "query",
                    "name": "token",
                },
            },
        }

    monkeypatch.setattr(
        service.EconomiaService,
        "resolver_contrato_http_proveedor",
        fake_contract,
    )

    captured = {}

    class Response:
        status_code = 200

        def raise_for_status(self):
            pass

        def json(self):
            return {}

    class Client:
        def __init__(self, timeout):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

        async def get(self, url, params=None, headers=None):
            captured["params"] = params
            return Response()

    monkeypatch.setattr(
        service.httpx,
        "AsyncClient",
        Client,
    )

    await service.EconomiaService.consultar_proveedor_http(10)

    assert captured["params"]["token"] == "SECRET"


@pytest.mark.asyncio
async def test_cliente_http_auth_tipo_desconocido_fail_closed(
    monkeypatch,
):
    service = __import__(
        "modules.economia.service",
        fromlist=["*"],
    )

    async def fake_contract(serie_id):
        return {
            "codigo_proveedor": "ABC",
            "base_url": "https://example.invalid",
            "requiere_autenticacion": True,
            "api_key": "SECRET",
            "metadata": {
                "endpoint": "/data/{codigo}",
                "auth": {
                    "placement": "inventado",
                },
            },
        }

    monkeypatch.setattr(
        service.EconomiaService,
        "resolver_contrato_http_proveedor",
        fake_contract,
    )

    with pytest.raises(
        ValueError,
        match="no soportado",
    ):
        await (
            service.EconomiaService
            .consultar_proveedor_http(10)
        )


def test_normalizacion_soporta_lista_anidada_estilo_api():
    service = __import__(
        "modules.economia.service",
        fromlist=["*"],
    )

    data = {
        "Series": [
            {
                "OBSERVATIONS": [
                    {
                        "TIME_PERIOD": "2026/05",
                        "OBS_VALUE": "3.94",
                    }
                ]
            }
        ]
    }

    metadata = {
        "normalizacion": {
            "items_path": "Series.0.OBSERVATIONS",
            "fecha_field": "TIME_PERIOD",
            "valor_field": "OBS_VALUE",
            "fecha_format": "%Y/%m",
        }
    }

    result = (
        service.EconomiaService
        .normalizar_observaciones(
            10,
            data,
            metadata,
        )
    )

    assert len(result) == 1
    assert str(result[0]["fecha_periodo"]) == "2026-05-01"
    assert str(result[0]["valor"]) == "3.94"


def test_normalizacion_rechaza_indice_lista_fuera_rango():
    service = __import__(
        "modules.economia.service",
        fromlist=["*"],
    )

    with pytest.raises(
        ValueError,
        match="fuera de rango",
    ):
        service.EconomiaService.normalizar_observaciones(
            10,
            {"Series": []},
            {
                "normalizacion": {
                    "items_path": "Series.0.OBSERVATIONS",
                    "fecha_field": "TIME_PERIOD",
                    "valor_field": "OBS_VALUE",
                }
            },
        )


@pytest.mark.asyncio
async def test_cliente_http_response_format_json_default(monkeypatch):
    service = __import__(
        "modules.economia.service",
        fromlist=["*"],
    )

    async def fake_contract(serie_id):
        return {
            "serie_id": serie_id,
            "codigo_proveedor": "ABC",
            "base_url": "https://example.invalid",
            "requiere_autenticacion": False,
            "api_key": "",
            "metadata": {
                "endpoint": "/data/{codigo}",
            },
        }

    monkeypatch.setattr(
        service.EconomiaService,
        "resolver_contrato_http_proveedor",
        fake_contract,
    )

    captured = {}

    def fake_decoder(response, response_format):
        captured["format"] = response_format
        return {"ok": True}

    monkeypatch.setattr(
        service,
        "decode_http_response",
        fake_decoder,
    )

    class Response:
        status_code = 200
        text = "{}"

        def raise_for_status(self):
            pass

    class Client:
        def __init__(self, timeout):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

        async def get(self, url, params=None, headers=None):
            return Response()

    monkeypatch.setattr(
        service.httpx,
        "AsyncClient",
        Client,
    )

    result = await (
        service.EconomiaService
        .consultar_proveedor_http(10)
    )

    assert captured["format"] == "json"
    assert result["data"] == {"ok": True}


@pytest.mark.asyncio
async def test_cliente_http_response_format_xml_configurable(monkeypatch):
    service = __import__(
        "modules.economia.service",
        fromlist=["*"],
    )

    async def fake_contract(serie_id):
        return {
            "serie_id": serie_id,
            "codigo_proveedor": "ABC",
            "base_url": "https://example.invalid",
            "requiere_autenticacion": False,
            "api_key": "",
            "metadata": {
                "endpoint": "/feed/{codigo}",
                "response_format": "xml",
            },
        }

    monkeypatch.setattr(
        service.EconomiaService,
        "resolver_contrato_http_proveedor",
        fake_contract,
    )

    captured = {}

    def fake_decoder(response, response_format):
        captured["format"] = response_format
        captured["text"] = response.text
        return {
            "feed": {
                "item": [
                    {
                        "fecha": "2026-07-01",
                        "valor": "3.9",
                    }
                ]
            }
        }

    monkeypatch.setattr(
        service,
        "decode_http_response",
        fake_decoder,
    )

    class Response:
        status_code = 200
        text = "<feed/>"

        def raise_for_status(self):
            pass

    class Client:
        def __init__(self, timeout):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

        async def get(self, url, params=None, headers=None):
            return Response()

    monkeypatch.setattr(
        service.httpx,
        "AsyncClient",
        Client,
    )

    result = await (
        service.EconomiaService
        .consultar_proveedor_http(10)
    )

    assert captured["format"] == "xml"
    assert captured["text"] == "<feed/>"
    assert result["data"]["feed"]["item"][0]["valor"] == "3.9"


@pytest.mark.asyncio
async def test_cliente_http_no_contiene_logica_especifica_inegi():
    from pathlib import Path

    path = Path(
        "modules/economia/service.py"
    )

    text = path.read_text(
        encoding="utf-8"
    ).lower()

    assert "910406" not in text
    assert "inpa_m_o_h" not in text
    assert "www.inegi.org.mx" not in text


@pytest.mark.asyncio
async def test_cliente_http_metadata_puede_desactivar_auth_del_proveedor(
    monkeypatch,
):
    service = __import__(
        "modules.economia.service",
        fromlist=["*"],
    )

    async def fake_contract(serie_id):
        return {
            "serie_id": serie_id,
            "codigo_proveedor": "SERIE-PUBLICA",
            "base_url": "https://example.invalid",
            "requiere_autenticacion": True,
            "api_key": "NO-DEBE-USARSE",
            "metadata": {
                "endpoint": "/feed.xml",
                "requires_auth": False,
                "response_format": "xml",
            },
        }

    monkeypatch.setattr(
        service.EconomiaService,
        "resolver_contrato_http_proveedor",
        fake_contract,
    )

    captured = {}

    class Response:
        status_code = 200
        content = b"<DATASET/>"

        def raise_for_status(self):
            pass

    class Client:
        def __init__(self, timeout):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

        async def get(self, url, params=None, headers=None):
            captured["url"] = url
            captured["params"] = params
            captured["headers"] = headers
            return Response()

    monkeypatch.setattr(
        service.httpx,
        "AsyncClient",
        Client,
    )

    result = await (
        service.EconomiaService
        .consultar_proveedor_http(10)
    )

    assert captured["url"] == (
        "https://example.invalid/feed.xml"
    )
    assert captured["params"] == {}
    assert captured["headers"] == {}
    assert result["status_code"] == 200


@pytest.mark.asyncio
async def test_cliente_http_metadata_requires_auth_true_mantiene_auth(
    monkeypatch,
):
    service = __import__(
        "modules.economia.service",
        fromlist=["*"],
    )

    async def fake_contract(serie_id):
        return {
            "serie_id": serie_id,
            "codigo_proveedor": "SERIE-PRIVADA",
            "base_url": "https://example.invalid",
            "requiere_autenticacion": False,
            "api_key": "TOKEN-TEST",
            "metadata": {
                "endpoint": "/data",
                "requires_auth": True,
                "auth": {
                    "placement": "header",
                    "name": "X-Api-Key",
                },
            },
        }

    monkeypatch.setattr(
        service.EconomiaService,
        "resolver_contrato_http_proveedor",
        fake_contract,
    )

    captured = {}

    class Response:
        status_code = 200

        def raise_for_status(self):
            pass

        def json(self):
            return {"ok": True}

    class Client:
        def __init__(self, timeout):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

        async def get(self, url, params=None, headers=None):
            captured["headers"] = headers
            return Response()

    monkeypatch.setattr(
        service.httpx,
        "AsyncClient",
        Client,
    )

    await (
        service.EconomiaService
        .consultar_proveedor_http(10)
    )

    assert captured["headers"]["X-Api-Key"] == (
        "TOKEN-TEST"
    )


@pytest.mark.asyncio
async def test_cliente_http_sin_override_conserva_auth_proveedor(
    monkeypatch,
):
    service = __import__(
        "modules.economia.service",
        fromlist=["*"],
    )

    async def fake_contract(serie_id):
        return {
            "serie_id": serie_id,
            "codigo_proveedor": "SERIE-LEGACY",
            "base_url": "https://example.invalid",
            "requiere_autenticacion": True,
            "api_key": "",
            "metadata": {
                "endpoint": "/data",
            },
        }

    monkeypatch.setattr(
        service.EconomiaService,
        "resolver_contrato_http_proveedor",
        fake_contract,
    )

    with pytest.raises(
        ValueError,
        match="sin credencial",
    ):
        await (
            service.EconomiaService
            .consultar_proveedor_http(10)
        )


@pytest.mark.asyncio
async def test_contrato_http_base_url_metadata_prevalece_sobre_conexion(
    monkeypatch,
):
    service = __import__(
        "modules.economia.service",
        fromlist=["*"],
    )

    async def fake_resolved(serie_id):
        return {
            "proveedor": {
                "serie_id": serie_id,
                "codigo_canonico": "SERIE.TEST",
                "codigo_proveedor": "ABC",
                "proveedor_codigo": "PROVEEDOR",
                "proveedor_tipo": "API",
                "requiere_autenticacion": True,
                "permite_backfill": True,
                "url_publica": "https://public.example.invalid",
                "metadata_json": {
                    "base_url": "https://feed.example.invalid",
                    "requires_auth": False,
                    "endpoint": "/feed.xml",
                    "response_format": "xml",
                },
            },
            "conexion": {
                "api_url": "https://api.example.invalid",
                "url": "https://api.example.invalid",
            },
            "api_key": "TOKEN-NO-DEBE-USARSE",
        }

    monkeypatch.setattr(
        service.EconomiaService,
        "resolver_conexion_proveedor",
        fake_resolved,
    )

    result = await (
        service.EconomiaService
        .resolver_contrato_http_proveedor(10)
    )

    assert result["base_url"] == (
        "https://feed.example.invalid"
    )
    assert result["metadata"]["requires_auth"] is False


@pytest.mark.asyncio
async def test_contrato_http_sin_base_url_metadata_conserva_conexion(
    monkeypatch,
):
    service = __import__(
        "modules.economia.service",
        fromlist=["*"],
    )

    async def fake_resolved(serie_id):
        return {
            "proveedor": {
                "serie_id": serie_id,
                "codigo_canonico": "SERIE.TEST",
                "codigo_proveedor": "ABC",
                "proveedor_codigo": "PROVEEDOR",
                "proveedor_tipo": "API",
                "requiere_autenticacion": False,
                "permite_backfill": True,
                "url_publica": "https://public.example.invalid",
                "metadata_json": {
                    "endpoint": "/data",
                },
            },
            "conexion": {
                "api_url": "https://api.example.invalid",
                "url": "https://api.example.invalid",
            },
            "api_key": "",
        }

    monkeypatch.setattr(
        service.EconomiaService,
        "resolver_conexion_proveedor",
        fake_resolved,
    )

    result = await (
        service.EconomiaService
        .resolver_contrato_http_proveedor(10)
    )

    assert result["base_url"] == (
        "https://api.example.invalid"
    )


@pytest.mark.asyncio
async def test_cliente_http_rechaza_requires_auth_no_booleano(
    monkeypatch,
):
    service = __import__(
        "modules.economia.service",
        fromlist=["*"],
    )

    async def fake_contract(serie_id):
        return {
            "serie_id": serie_id,
            "codigo_proveedor": "ABC",
            "base_url": "https://example.invalid",
            "requiere_autenticacion": True,
            "api_key": "TOKEN",
            "metadata": {
                "endpoint": "/data",
                "requires_auth": "false",
            },
        }

    monkeypatch.setattr(
        service.EconomiaService,
        "resolver_contrato_http_proveedor",
        fake_contract,
    )

    with pytest.raises(
        ValueError,
        match="requires_auth debe ser booleano",
    ):
        await (
            service.EconomiaService
            .consultar_proveedor_http(10)
        )


class _EconomiaBatchFakeConnection:
    def __init__(self):
        self.commits = 0
        self.rollbacks = 0

    def commit(self):
        self.commits += 1

    def rollback(self):
        self.rollbacks += 1


class _EconomiaBatchFakeContext:
    def __init__(self, connection):
        self.connection = connection

    def __enter__(self):
        return self.connection

    def __exit__(self, exc_type, exc, tb):
        return False


@pytest.mark.asyncio
async def test_sincronizar_serie_transaccion_unica_por_lote(
    monkeypatch,
):
    service = __import__(
        "modules.economia.service",
        fromlist=["*"],
    )

    conn = _EconomiaBatchFakeConnection()

    observaciones = [
        {
            "serie_id": 10,
            "fecha_periodo": date(2026, 1, 1),
            "valor": 10.0,
            "fuente_dato_id": "A",
        },
        {
            "serie_id": 10,
            "fecha_periodo": date(2026, 2, 1),
            "valor": 11.0,
            "fuente_dato_id": "B",
        },
    ]

    async def fake_observaciones(serie_id):
        assert serie_id == 10
        return observaciones

    conexiones_recibidas = []

    def fake_persist(**kwargs):
        conexiones_recibidas.append(kwargs.get("connection"))

        return {
            "insertado": True,
            "version_dato": 1,
            "es_revision": False,
        }

    monkeypatch.setattr(
        service,
        "sql_connection",
        lambda: _EconomiaBatchFakeContext(conn),
    )

    monkeypatch.setattr(
        service.EconomiaService,
        "consultar_observaciones_proveedor",
        fake_observaciones,
    )

    monkeypatch.setattr(
        service.EconomiaRepository,
        "persistir_valor_versionado",
        fake_persist,
    )

    result = await service.EconomiaService.sincronizar_serie(
        10,
        sync_run_id="run-atomic-success",
    )

    assert result["observaciones"] == 2
    assert result["insertados"] == 2

    assert conexiones_recibidas == [
        conn,
        conn,
    ]

    assert conn.commits == 1
    assert conn.rollbacks == 0


@pytest.mark.asyncio
async def test_sincronizar_serie_rollback_si_falla_observacion_intermedia(
    monkeypatch,
):
    service = __import__(
        "modules.economia.service",
        fromlist=["*"],
    )

    conn = _EconomiaBatchFakeConnection()

    observaciones = [
        {
            "serie_id": 10,
            "fecha_periodo": date(2026, 1, 1),
            "valor": 10.0,
        },
        {
            "serie_id": 10,
            "fecha_periodo": date(2026, 2, 1),
            "valor": 11.0,
        },
        {
            "serie_id": 10,
            "fecha_periodo": date(2026, 3, 1),
            "valor": 12.0,
        },
    ]

    async def fake_observaciones(serie_id):
        return observaciones

    llamadas = []

    def fake_persist(**kwargs):
        llamadas.append(kwargs)

        if len(llamadas) == 2:
            raise RuntimeError(
                "fallo intermedio simulado"
            )

        return {
            "insertado": True,
            "version_dato": 1,
            "es_revision": False,
        }

    monkeypatch.setattr(
        service,
        "sql_connection",
        lambda: _EconomiaBatchFakeContext(conn),
    )

    monkeypatch.setattr(
        service.EconomiaService,
        "consultar_observaciones_proveedor",
        fake_observaciones,
    )

    monkeypatch.setattr(
        service.EconomiaRepository,
        "persistir_valor_versionado",
        fake_persist,
    )

    with pytest.raises(
        RuntimeError,
        match="fallo intermedio simulado",
    ):
        await service.EconomiaService.sincronizar_serie(
            10,
            sync_run_id="run-atomic-failure",
        )

    assert len(llamadas) == 2

    assert all(
        llamada["connection"] is conn
        for llamada in llamadas
    )

    assert conn.commits == 0
    assert conn.rollbacks == 1


@pytest.mark.asyncio
async def test_backfill_serie_transaccion_unica_por_lote(
    monkeypatch,
):
    service = __import__(
        "modules.economia.service",
        fromlist=["*"],
    )

    conn = _EconomiaBatchFakeConnection()

    async def fake_contract(serie_id):
        return {
            "permite_backfill": True,
            "metadata": {
                "backfill": {
                    "desde_param": "start",
                    "hasta_param": "end",
                    "date_format": "%Y-%m-%d",
                    "max_days": 365,
                },
                "normalizacion": {
                    "items_path": "items",
                    "fecha_field": "date",
                    "valor_field": "value",
                },
            },
        }

    async def fake_http(
        serie_id,
        *,
        params_extra=None,
    ):
        return {
            "data": {
                "items": [
                    {
                        "date": "2026-01-01",
                        "value": "10.5",
                    },
                    {
                        "date": "2026-02-01",
                        "value": "11.5",
                    },
                ]
            }
        }

    conexiones_recibidas = []

    def fake_persist(**kwargs):
        conexiones_recibidas.append(
            kwargs.get("connection")
        )

        return {
            "insertado": True,
            "version_dato": 1,
            "es_revision": False,
        }

    monkeypatch.setattr(
        service,
        "sql_connection",
        lambda: _EconomiaBatchFakeContext(conn),
    )

    monkeypatch.setattr(
        service.EconomiaService,
        "resolver_contrato_http_proveedor",
        fake_contract,
    )

    monkeypatch.setattr(
        service.EconomiaService,
        "consultar_proveedor_http",
        fake_http,
    )

    monkeypatch.setattr(
        service.EconomiaRepository,
        "persistir_valor_versionado",
        fake_persist,
    )

    result = await service.EconomiaService.backfill_serie(
        10,
        date(2026, 1, 1),
        date(2026, 2, 28),
        sync_run_id="backfill-atomic-success",
    )

    assert result["observaciones"] == 2
    assert result["insertados"] == 2

    assert conexiones_recibidas == [
        conn,
        conn,
    ]

    assert conn.commits == 1
    assert conn.rollbacks == 0
