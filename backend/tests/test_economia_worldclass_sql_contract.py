from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

MIGRATION = ROOT / "backend/database/migrations/20260730_001_economia_worldclass_core.sql"
ROLLBACK = ROOT / "backend/database/rollback/20260730_001_economia_worldclass_core_rollback.sql"
VALIDATION = ROOT / "backend/database/validation/20260730_001_economia_worldclass_core_validation.sql"


EXPECTED_TABLES = {
    "Economia_Paises",
    "Economia_Proveedores",
    "Economia_CategoriasIndicador",
    "Economia_Series",
    "Economia_Valores",
    "Economia_ContextoOperativo",
}


def read(path: Path) -> str:
    assert path.is_file(), path
    return path.read_text(encoding="utf-8")


def test_migration_contains_only_expected_economia_tables():
    sql = read(MIGRATION)

    for table in EXPECTED_TABLES:
        assert f"dbo.{table}" in sql


def test_migration_does_not_create_duplicate_platform_catalogs():
    sql = read(MIGRATION).lower()

    forbidden_create = [
        "create table dbo.sistema_empresas",
        "create table dbo.unidades_negocio",
        "create table dbo.proveedor_monedas",
        "create table dbo.servidores_conexiones",
        "create table dbo.sys_scheduler_jobs",
        "create table dbo.sistema_rbac_permisos",
    ]

    for fragment in forbidden_create:
        assert fragment not in sql


def test_migration_has_no_mongo_dependency():
    sql = read(MIGRATION).lower()

    assert "mongodb://" not in sql
    assert "mongodb+srv://" not in sql
    assert "pymongo" not in sql
    assert "motor." not in sql


def test_values_are_versioned():
    sql = read(MIGRATION)

    assert "VersionDato" in sql
    assert "EsRevision" in sql
    assert "ValorAnterior" in sql
    assert "FechaPublicacion" in sql


def test_future_indicator_does_not_require_schema_column():
    sql = read(MIGRATION)

    assert "CodigoCanonico" in sql
    assert "CategoriaIndicadorID" in sql
    assert "TipoValorCodigo" in sql


def test_rollback_covers_all_new_tables():
    sql = read(ROLLBACK)

    for table in EXPECTED_TABLES:
        assert f"DROP TABLE dbo.{table}" in sql


def test_validation_covers_all_new_tables():
    sql = read(VALIDATION)

    for table in EXPECTED_TABLES:
        assert table in sql


def test_platform_fk_types_match_canonical_schema():
    sql = read(MIGRATION)

    assert "EmpresaID               int NULL" in sql
    assert "UnidadNegocioID         uniqueidentifier NULL" in sql
    assert "ServerConexionID        uniqueidentifier NULL" in sql
    assert "MonedaID                smallint NULL" in sql


def test_platform_foreign_keys_are_explicit():
    sql = read(MIGRATION)

    expected = {
        "FK_Economia_Paises_Moneda":
            "REFERENCES dbo.Proveedor_Monedas(MonedaID)",
        "FK_Economia_Proveedores_ServerConexion":
            "REFERENCES dbo.Servidores_Conexiones(id)",
        "FK_Economia_Series_Moneda":
            "REFERENCES dbo.Proveedor_Monedas(MonedaID)",
        "FK_Economia_Series_MonedaBase":
            "REFERENCES dbo.Proveedor_Monedas(MonedaID)",
        "FK_Economia_Series_MonedaCotizada":
            "REFERENCES dbo.Proveedor_Monedas(MonedaID)",
        "FK_Economia_ContextoOperativo_Empresa":
            "REFERENCES dbo.Sistema_Empresas(EmpresaID)",
        "FK_Economia_ContextoOperativo_Unidad":
            "REFERENCES dbo.Unidades_Negocio(id)",
        "FK_Economia_ContextoOperativo_Moneda":
            "REFERENCES dbo.Proveedor_Monedas(MonedaID)",
    }

    for constraint, reference in expected.items():
        assert constraint in sql
        assert reference in sql


def test_contexto_empresa_does_not_use_guid():
    sql = read(MIGRATION)

    assert "EmpresaID               uniqueidentifier" not in sql
