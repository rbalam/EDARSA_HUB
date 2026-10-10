from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

MODULE = ROOT / "backend/modules/production_quality"
ROUTES = MODULE / "routes.py"
SERVICE = MODULE / "service.py"
REPOSITORY = MODULE / "repository.py"
SCHEMAS = MODULE / "schemas.py"
SERVER = ROOT / "backend/server.py"


def text(path):
    return path.read_text(encoding="utf-8")


def test_bounded_context_exists():
    for name in (
        "__init__.py",
        "schemas.py",
        "repository.py",
        "service.py",
        "routes.py",
    ):
        assert (MODULE / name).is_file()


def test_routes_do_not_issue_sql():
    source = text(ROUTES).upper()

    for token in (
        "SELECT ",
        "INSERT INTO ",
        "UPDATE DBO.",
        "DELETE FROM ",
        "GET_SQL_CONNECTION",
        "PYMSSQL",
    ):
        assert token not in source


def test_repository_owns_sql_and_uses_canonical_connection():
    source = text(REPOSITORY)

    assert "from core.sql_first.db import get_sql_connection" in source
    assert "get_sql_connection()" in source

    for table in (
        "dbo.Production_Item",
        "dbo.Production_QualityStandard",
        "dbo.Production_Measurement",
        "dbo.Production_Evidence",
        "dbo.Production_QualityDecision",
        "dbo.Production_QualityAction",
        "dbo.Production_Device",
        "dbo.Production_DeviceCalibration",
    ):
        assert table in source


def test_service_uses_canonical_rbac_scope():
    source = text(SERVICE)

    assert "RBACSQLService.can_access_empresa" in source
    assert "RBACSQLService.can_access_unidad" in source
    assert "EmpresaID" in source
    assert "UnidadNegocioID" in source


def test_service_uses_canonical_operational_date():
    source = text(SERVICE)

    assert "get_operational_window" in source
    assert ".fecha_operacion" in source

    forbidden = (
        "date.today(",
        "datetime.today(",
    )

    for token in forbidden:
        assert token not in source


def test_routes_use_explicit_sql_rbac():
    source = text(ROUTES)

    assert "require_explicit_permission_dual" in source

    for permission in (
        "production_quality.execution_VER",
        "production_quality.execution_GESTIONAR",
        "production_quality.evidence_CREAR",
        "production_quality.standards_VER",
        "production_quality.decisions_AUTORIZAR",
        "production_quality.rework_GESTIONAR",
        "production_quality.override_AUTORIZAR",
        "production_quality.devices_VER",
        "production_quality.devices_CONFIGURAR",
    ):
        assert permission in source


def test_idempotency_is_repository_enforced():
    source = text(REPOSITORY)

    assert source.count("IdempotencyKey") >= 8
    assert "WHERE IdempotencyKey = %s" in source


def test_no_mongo_or_live_dependency():
    source = (
        text(ROUTES)
        + text(SERVICE)
        + text(REPOSITORY)
        + text(SCHEMAS)
    ).lower()

    for token in (
        "pymongo",
        "mongodb://",
        "mongodb+srv://",
        "mongo_client",
        "query_api_mpro_local",
        "get_external_sql_connection",
    ):
        assert token not in source


def test_no_database_secrets_or_inline_connection_config():
    source = (
        text(ROUTES)
        + text(SERVICE)
        + text(REPOSITORY)
    ).lower()

    for token in (
        "edarsahub_sql_password",
        "password=",
        "server=",
        "host=",
        "user=",
    ):
        assert token not in source


def test_server_registers_router_exactly_once():
    source = text(SERVER)

    assert source.count(
        "from modules.production_quality import "
        "router as production_quality_router"
    ) == 1

    assert source.count(
        "api_router.include_router(production_quality_router)"
    ) == 1


def test_api_prefix_is_bounded_context_specific():
    source = text(ROUTES)

    assert 'prefix="/production-quality"' in source


def test_evidence_stores_metadata_not_binary_payload():
    schema = text(SCHEMAS).lower()
    repository = text(REPOSITORY).lower()

    assert "storage_path" in schema
    assert "content_hash" in schema
    assert "contentsize" not in schema

    for token in (
        "varbinary(max)",
        "base64.b64decode",
        "uploadfile",
    ):
        assert token not in repository


def test_routes_have_no_admin_role_bypass():
    source = text(ROUTES)

    for token in (
        "SUPERADMIN",
        "ADMINISTRADOR",
        "es_admin(",
        "role ==",
    ):
        assert token not in source
