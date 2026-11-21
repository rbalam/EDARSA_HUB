from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

MIG = ROOT / (
    "backend/database/migrations/"
    "20260924_002_production_quality_rbac.sql"
)

ROLLBACK = ROOT / (
    "backend/database/migrations/"
    "20260924_002_production_quality_rbac_rollback.sql"
)


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_rbac_artifacts_exist():
    assert MIG.is_file()
    assert ROLLBACK.is_file()


def test_uses_only_canonical_rbac_tables():
    sql = read(MIG)

    for table in (
        "dbo.Usuario_Roles",
        "dbo.Usuario_Modulos",
        "dbo.Usuario_Acciones",
        "dbo.Usuario_PermisosRolModulo",
    ):
        assert table in sql


def test_does_not_create_parallel_rbac_tables():
    sql = read(MIG).upper()

    assert "CREATE TABLE" not in sql
    assert "CREATE ROLE" not in sql


def test_does_not_create_roles_or_actions():
    sql = read(MIG).upper()

    assert "INSERT INTO DBO.USUARIO_ROLES" not in sql
    assert "INSERT INTO DBO.USUARIO_ACCIONES" not in sql


def test_production_quality_taxonomy_exists():
    sql = read(MIG)

    for module in (
        "production_quality",
        "production_quality.execution",
        "production_quality.standards",
        "production_quality.evidence",
        "production_quality.decisions",
        "production_quality.rework",
        "production_quality.override",
        "production_quality.devices",
    ):
        assert module in sql


def test_modules_are_hidden_from_menu():
    sql = read(MIG)

    assert "EsVisibleMenu" in sql
    assert "production_quality" in sql


def test_reuses_generic_actions():
    sql = read(MIG)

    for action in (
        "'VER'",
        "'CREAR'",
        "'GESTIONAR'",
        "'AUTORIZAR'",
        "'CONFIGURAR'",
    ):
        assert action in sql


def test_no_role_ids_are_hardcoded():
    sql = read(MIG).lower()

    for token in (
        "rolid = 1",
        "rolid = 2",
        "rolid = 6",
        "rolid = 7",
        "rolid = 11",
        "rolid = 12",
        "rolid = 13",
    ):
        assert token not in sql


def test_no_action_ids_are_hardcoded():
    sql = read(MIG).lower()

    for token in (
        "accionid = 1",
        "accionid = 2",
        "accionid = 3",
        "accionid = 7",
        "accionid = 13",
    ):
        assert token not in sql


def test_grants_are_inherited_from_existing_permissions():
    sql = read(MIG)

    assert "source_perm.RolID" in sql
    assert "source_role.RolID = source_perm.RolID" in sql


def test_no_role_code_seed_is_used():
    sql = read(MIG)

    for code in (
        "'SUPERADMIN'",
        "'ADMINISTRADOR'",
        "'GERENTE_OPS'",
        "'SUPERVISOR'",
        "'OPERADOR'",
        "'AUDITOR'",
    ):
        assert code not in sql


def test_override_uses_existing_admin_permission():
    sql = read(MIG)

    assert "'production_quality.override'" in sql
    assert "'auth'" in sql
    assert "'ADMIN'" in sql


def test_tablajeria_is_reused_as_source_policy():
    sql = read(MIG)

    assert "'tablajeria'" in sql
    assert "'tablajeria.config'" in sql


def test_sensitive_capabilities_require_authorization():
    sql = read(MIG)

    assert "'production_quality.decisions'" in sql
    assert "'production_quality.override'" in sql
    assert "'production_quality.devices'" in sql
    assert "RequiresAuthorization" in sql


def test_transaction_and_application_lock():
    sql = read(MIG).upper()

    assert "SET XACT_ABORT ON" in sql
    assert "BEGIN TRANSACTION" in sql
    assert "COMMIT TRANSACTION" in sql
    assert "ROLLBACK TRANSACTION" in sql
    assert "SP_GETAPPLOCK" in sql


def test_migration_is_idempotent():
    sql = read(MIG).upper()

    assert "NOT EXISTS" in sql
    assert "LOWER(CODIGOMODULO)" in sql


def test_explicit_denies_fail_closed():
    sql = read(MIG)

    assert "51014" in sql
    assert "denegado/inactivo" in sql


def test_rollback_is_gate_scoped():
    sql = read(ROLLBACK)

    assert "PQ_RBAC_GATE5D2" in sql
    assert "DELETE FROM dbo.Usuario_Roles" not in sql
    assert "DELETE FROM dbo.Usuario_Acciones" not in sql


def test_no_runtime_database_connection():
    artifacts = (
        read(MIG)
        + "\n"
        + read(ROLLBACK)
    ).lower()

    for token in (
        "pymssql.connect",
        "pyodbc.connect",
        "sqlalchemy.create_engine",
        "mongodb://",
        "mongodb+srv://",
    ):
        assert token not in artifacts
