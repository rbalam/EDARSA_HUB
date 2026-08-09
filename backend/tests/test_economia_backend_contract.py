from pathlib import Path
import ast


ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "modules" / "economia"


def _read(name: str) -> str:
    return (MODULE / name).read_text(encoding="utf-8")


def test_economia_module_files_exist():
    expected = {
        "__init__.py",
        "repository.py",
        "service.py",
        "schemas.py",
        "routes.py",
    }

    actual = {
        p.name
        for p in MODULE.iterdir()
        if p.is_file()
    }

    assert expected <= actual


def test_economia_has_no_mongo_contract():
    text = "\n".join(
        _read(name)
        for name in (
            "__init__.py",
            "repository.py",
            "service.py",
            "schemas.py",
            "routes.py",
        )
    ).lower()

    assert "pymongo" not in text
    assert "motor.motor_asyncio" not in text
    assert "mongodb://" not in text
    assert "mongodb+srv://" not in text


def test_repository_uses_canonical_db_helper():
    text = _read("repository.py")

    assert "execute_sql_query_params" in text
    assert "pymssql.connect" not in text
    assert "pyodbc.connect" not in text


def test_repository_uses_only_economia_tables():
    text = _read("repository.py")

    assert "dbo.Economia_Series" in text
    assert "dbo.Economia_Valores" in text
    assert "dbo.Economia_ContextoOperativo" in text

    forbidden = (
        "Comercial_KPIs",
        "Sync_Sales",
        "Fact_Ventas",
        "View_Inteligencia",
    )

    for token in forbidden:
        assert token not in text


def test_routes_prefix_is_economia():
    text = _read("routes.py")
    tree = ast.parse(text)

    calls = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "APIRouter"
    ]

    assert len(calls) == 1

    prefix = None

    for keyword in calls[0].keywords:
        if keyword.arg == "prefix":
            prefix = ast.literal_eval(keyword.value)

    assert prefix == "/economia"


def test_routes_use_explicit_economia_permissions():
    text = _read("routes.py")

    assert "require_explicit_permission_dual" in text
    assert '"economia.indicadores.leer"' in text
    assert '"economia.series.leer"' in text
    assert '"economia.contexto.administrar"' in text

    assert "require_admin" not in text
    assert "ADMINISTRADOR" not in text


def test_service_does_not_access_sql_directly():
    text = _read("service.py")

    assert "execute_sql_query" not in text
    assert "pymssql" not in text
    assert "pyodbc" not in text


def test_schemas_have_no_infrastructure_dependencies():
    text = _read("schemas.py")

    assert "core.db" not in text
    assert "core.rbac" not in text
    assert "fastapi" not in text


def test_module_does_not_register_scheduler():
    text = "\n".join(
        _read(name)
        for name in (
            "__init__.py",
            "repository.py",
            "service.py",
            "schemas.py",
            "routes.py",
        )
    ).lower()

    assert "scheduler_manager" not in text
    assert "add_job(" not in text
    assert "register_job" not in text


def _economia_include_statement(server: str) -> str:
    marker = "app.include_router(economia_router)"
    start = server.find(marker)

    if start < 0:
        return ""

    end = server.find("\n", start)

    if end < 0:
        return server[start:]

    return server[start:end]


def test_server_composes_economia_router_explicitly():
    server = (ROOT / "server.py").read_text(
        encoding="utf-8",
        errors="replace",
    )

    assert (
        "from modules.economia.routes import router as economia_router"
        in server
    )
    assert "app.include_router(economia_router)" in server

    include_statement = _economia_include_statement(server)

    assert 'prefix="/api"' not in include_statement
    assert 'prefix="/api/v2"' not in include_statement


def test_package_init_has_no_eager_routes_import():
    text = _read("__init__.py")
    tree = ast.parse(text)

    for node in tree.body:
        if isinstance(node, ast.ImportFrom):
            assert node.module != "routes"

        if isinstance(node, ast.Import):
            for alias in node.names:
                assert "economia.routes" not in alias.name

    assert "economia_router" not in text


def test_package_import_does_not_require_runtime_secrets():
    """
    Contrato estático BOS:
    __init__ debe permanecer libre de RBAC/security/configuración.
    """
    text = _read("__init__.py").lower()

    forbidden = (
        "core.rbac",
        "core.security",
        "jwt_secret",
        "edarsahub_sql_",
        "load_dotenv",
        "get_edarsahub_sql_config",
    )

    for token in forbidden:
        assert token not in text


def test_repository_uses_real_installed_economia_column_names():
    text = _read("repository.py")

    required = (
        "s.SerieEconomicaID",
        "s.UnidadMedidaCodigo",
        "s.FrecuenciaCodigo",
        "v.SerieEconomicaID",
        "v.FechaPeriodo",
        "v.EsDatoPreliminar",
        "v.EsDatoEstimado",
        "c.ContextoEconomicoID",
        "c.EsPrincipal",
    )

    for token in required:
        assert token in text

    forbidden = (
        "s.ID",
        "s.UnidadMedida ",
        "s.Frecuencia ",
        "v.SerieID",
        "v.Periodo ",
        "v.Preliminar",
        "v.Estimado",
        "c.ID",
        "c.Principal ",
    )

    for token in forbidden:
        assert token not in text


def test_repository_does_not_cast_bigint_ids_as_guid_strings():
    text = _read("repository.py")

    assert (
        "CONVERT(varchar(36), s.SerieEconomicaID)"
        not in text
    )
    assert (
        "CONVERT(varchar(36), v.SerieEconomicaID)"
        not in text
    )
    assert (
        "CONVERT(varchar(36), c.ContextoEconomicoID)"
        not in text
    )


def test_repository_preserves_real_guid_only_for_unidad_negocio():
    text = _read("repository.py")

    assert (
        "CONVERT(varchar(36), c.UnidadNegocioID)"
        in text
    )
