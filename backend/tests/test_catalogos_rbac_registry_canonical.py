from pathlib import Path
import re

ROOT = Path("/app")

MIG = ROOT / "backend/database/migrations/20260819_035_catalogos_rbac_registry_canonico.sql"
VAL = ROOT / "backend/database/validation/20260819_035_catalogos_rbac_registry_canonico_validation.sql"
RB = ROOT / "backend/database/rollback/20260819_035_catalogos_rbac_registry_canonico_rollback.sql"
ROUTES = ROOT / "backend/modules/admin_sql/routes.py"


def text(path):
    return path.read_text(encoding="utf-8")


def target_codes(sql):
    marker_start = "INSERT INTO @Target"
    marker_end = "IF (SELECT COUNT(*) FROM @Target)"

    block = sql.split(marker_start, 1)[1].split(marker_end, 1)[0]

    return re.findall(
        r"\(\s*N'([^']+)'\s*,\s*N'[^']*'\s*,\s*N'",
        block,
        flags=re.I,
    )


def test_migration_has_exactly_52_unique_physical_codes():
    sql = text(MIG)
    codes = target_codes(sql)

    assert len(codes) == 52
    assert len({x.upper() for x in codes}) == 52


def test_global_cat_bancos_only_once_and_nonphysical_excluded():
    sql = text(MIG)
    codes = [x.upper() for x in target_codes(sql)]

    assert codes.count("GLOBAL_CAT_BANCOS") == 1

    assert "GLOBAL_CAT_CENTROSCOSTO" not in codes
    assert "GLOBAL_CAT_EMPRESAS" not in codes
    assert "GLOBAL_CAT_UNIDADESMEDIDA" not in codes


def test_migration_is_fail_closed_and_does_not_touch_permission_or_module_tables():
    sql = text(MIG)
    upper = sql.upper()

    assert "SET XACT_ABORT ON" in upper
    assert "BEGIN TRY" in upper
    assert "BEGIN TRANSACTION" in upper
    assert "ROLLBACK TRANSACTION" in upper

    assert "THROW 51354" in upper
    assert "THROW 51355" in upper

    assert "INSERT INTO DBO.SISTEMA_CATALOGOSPERMISOS" not in upper
    assert "UPDATE DBO.SISTEMA_CATALOGOSPERMISOS" not in upper
    assert "DELETE FROM DBO.SISTEMA_CATALOGOSPERMISOS" not in upper

    assert "INSERT INTO DBO.USUARIO_MODULOS" not in upper
    assert "UPDATE DBO.USUARIO_MODULOS" not in upper
    assert "DELETE FROM DBO.USUARIO_MODULOS" not in upper

    assert "MONGO" not in upper.replace("LEGACYMONGOID", "")


def test_workflow_is_preserved_and_no_general_delete_exists():
    sql = text(MIG).upper()

    assert "CATALOGO_WORKFLOW" not in sql
    assert "DELETE FROM DBO.SISTEMA_CATALOGOSCONFIG" not in sql


def test_validation_requires_52_and_100_percent():
    sql = text(VAL).upper()

    assert "DECLARE @PHYSICALTARGET INT = 52" in sql
    assert "PHYSICAL_REGISTERED_ACTIVE" in sql
    assert "PHYSICAL_COVERAGE_PERCENT" in sql
    assert "WORKFLOW_PRESERVED" in sql
    assert "DUPLICATE_PHYSICAL_CODES" in sql
    assert "NONEXISTENT_TABLES_REGISTERED_AS_PHYSICAL" in sql
    assert "GLOBAL_CAT_BANCOS_REGISTRY_ROWS" in sql
    assert "CATALOG_RBAC_REGISTRY_VALID" in sql


def test_rollback_is_slice_scoped():
    sql = text(RB).upper()

    assert "MIGRATION_20260819_035" in sql
    assert "DELETE FROM DBO.SISTEMA_CATALOGOSCONFIG" in sql

    assert "DELETE FROM DBO.SISTEMA_CATALOGOSPERMISOS" not in sql
    assert "DELETE FROM DBO.USUARIO_MODULOS" not in sql


def test_runtime_routes_keep_canonical_permission_table():
    sql = text(ROUTES)

    assert "Sistema_CatalogosConfig" in sql
    assert "Sistema_CatalogosPermisos" in sql
    assert '@router.get("/catalogos-disponibles")' in sql


def test_no_hardcoded_user_or_role_ids():
    combined = "\n".join([
        text(MIG),
        text(VAL),
        text(RB),
    ])

    assert "UsuarioID =" not in combined
    assert "RolID =" not in combined
