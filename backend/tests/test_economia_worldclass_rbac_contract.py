from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

SEED = (
    ROOT
    / "backend/database/seeds/20260730_001_economia_worldclass_rbac.sql"
)

VALIDATION = (
    ROOT
    / "backend/database/validation/20260730_001_economia_worldclass_rbac_validation.sql"
)


EXPECTED_PERMISSIONS = {
    "economia.indicadores.leer",
    "economia.series.leer",
    "economia.series.administrar",
    "economia.proveedores.administrar",
    "economia.sincronizacion.ejecutar",
    "economia.backfill.ejecutar",
    "economia.contexto.administrar",
    "economia.exportar",
    "economia.configuracion.administrar",
}


def read(path: Path) -> str:
    assert path.is_file(), path
    return path.read_text(encoding="utf-8")


def test_all_economia_permissions_are_declared():
    sql = read(SEED)

    for code in EXPECTED_PERMISSIONS:
        assert code in sql


def test_seed_resolves_permissions_by_code_not_fixed_guid():
    sql = read(SEED).lower()

    assert "where existing.codigo = p.codigo" in sql
    assert "newid()" in sql

    forbidden_fixed_guid = [
        "00000000-0000-0000-0000-000000000000",
    ]

    for value in forbidden_fixed_guid:
        assert value not in sql


def test_seed_is_idempotent():
    sql = read(SEED).lower()

    assert "where not exists" in sql
    assert "update existing" in sql
    assert "update rp" in sql


def test_seed_uses_canonical_rbac_tables():
    sql = read(SEED)

    assert "dbo.Sistema_RBAC_Permisos" in sql
    assert "dbo.Sistema_RBAC_Roles" in sql
    assert "dbo.Sistema_RBAC_RolesPermisos" in sql


def test_module_is_explicit_economia():
    sql = read(SEED)

    assert "N'ECONOMIA'" in sql


def test_roles_resolved_by_real_canonical_codes():
    sql = read(SEED)

    expected_roles = {
        "SUPERADMIN",
        "ADMIN_COMERCIAL",
        "CONFIGURADOR_COMERCIAL",
        "ANALISTA_COMERCIAL",
        "GERENTE_UNIDAD",
        "VISOR_COMERCIAL",
    }

    for role in expected_roles:
        assert f"N'{role}'" in sql

    assert "N'ADMINISTRADOR'" not in sql
    assert "r.codigo = m.rol_codigo" in sql


def test_validation_checks_duplicates_and_expected_permissions():
    sql = read(VALIDATION)

    for code in EXPECTED_PERMISSIONS:
        assert code in sql

    assert "HAVING COUNT(*) > 1" in sql
