from pathlib import Path
import re


ROOT = Path("/app")
MIGRATION = ROOT / (
    "backend/database/migrations/"
    "20260819_033_tes_pagos_rbac_matriz.sql"
)
VALIDATION = ROOT / (
    "backend/database/validation/"
    "20260819_033_tes_pagos_rbac_matriz_validation.sql"
)
ROLLBACK = ROOT / (
    "backend/database/rollback/"
    "20260819_033_tes_pagos_rbac_matriz_rollback.sql"
)


def _migration_source() -> str:
    return MIGRATION.read_text(encoding="utf-8")


def _validation_source() -> str:
    return VALIDATION.read_text(encoding="utf-8")


def _rollback_source() -> str:
    return ROLLBACK.read_text(encoding="utf-8")


def test_migration_is_pure_dml_without_schema_mutations():
    source = _migration_source()

    assert "CREATE TABLE" in source  # only #TargetPermisos temp table
    assert "#TargetPermisos" in source
    # Check no real table creation or schema alteration
    assert "CREATE TABLE dbo." not in source
    assert "ALTER TABLE" not in source
    assert "DROP TABLE dbo." not in source
    assert "CREATE ROLE" not in source
    assert "GRANT " not in source


def test_migration_has_no_hardcoded_numeric_ids_or_users():
    source = _migration_source()

    # Dynamic lookups by code
    assert "WHERE CodigoModulo = 'TES_PAGOS'" in source
    assert "WHERE CodigoTipoAutorizacion = 'AUT_TES_PAGOS'" in source
    assert "WHERE CodigoAccion = 'AUTORIZAR'" in source
    assert "WHERE CodigoAccion = 'RECHAZAR'" in source
    assert "WHERE CodigoAccion = 'EJECUTAR'" in source
    assert "WHERE CodigoRol = 'GERENCIA'" in source
    assert "WHERE CodigoRol = 'DIRECCION'" in source
    assert "WHERE CodigoRol = 'TESORERIA'" in source
    assert "WHERE CodigoRol = 'ADMIN'" in source
    assert "WHERE CodigoRol = 'SUPERADMIN'" in source

    # No hardcoded emails or personal data
    assert "@edarsa" not in source
    assert "ricardo" not in source.lower()
    assert "UsuarioID = 1" not in source
    assert "UsuarioID = 8" not in source


def test_migration_defines_exact_11_permissions_and_2_matrix_rows():
    source = _migration_source()

    # 11 target permission tuples
    assert "(@RolGerenciaID, @ModuloID, @AccionAutorizarID)" in source
    assert "(@RolGerenciaID, @ModuloID, @AccionRechazarID)" in source
    assert "(@RolDireccionID, @ModuloID, @AccionAutorizarID)" in source
    assert "(@RolDireccionID, @ModuloID, @AccionRechazarID)" in source
    assert "(@RolTesoreriaID, @ModuloID, @AccionEjecutarID)" in source
    assert "(@RolAdminID, @ModuloID, @AccionAutorizarID)" in source
    assert "(@RolAdminID, @ModuloID, @AccionRechazarID)" in source
    assert "(@RolAdminID, @ModuloID, @AccionEjecutarID)" in source
    assert "(@RolSuperAdminID, @ModuloID, @AccionAutorizarID)" in source
    assert "(@RolSuperAdminID, @ModuloID, @AccionRechazarID)" in source
    assert "(@RolSuperAdminID, @ModuloID, @AccionEjecutarID)" in source

    # TESORERIA must NOT have AUTORIZAR or RECHAZAR
    assert "(@RolTesoreriaID, @ModuloID, @AccionAutorizarID)" not in source
    assert "(@RolTesoreriaID, @ModuloID, @AccionRechazarID)" not in source

    # Matrix: exactly 2 rows (Nivel 1 Gerencia 0-50000, Nivel 2 Direccion 50000.01-NULL)
    assert "NivelAutorizacion = 1" in source
    assert "@RolGerenciaID" in source
    assert "50000.00" in source
    assert "NivelAutorizacion = 2" in source
    assert "@RolDireccionID" in source
    assert "50000.01" in source

    # Post-check assertion in transaction
    assert "@ActivePermCount <> 11" in source
    assert "@ActiveMatrixCount <> 2" in source


def test_admin_superadmin_excluded_from_operational_matrix():
    source = _migration_source()

    assert "RolID IN (@RolAdminID, @RolSuperAdminID)" in source
    assert "Violacion: ADMIN o SUPERADMIN no deben pertenecer a la matriz operativa AUT_TES_PAGOS" in source


def test_transactional_integrity_and_fail_closed_guards():
    source = _migration_source()

    assert "SET XACT_ABORT ON;" in source
    assert "BEGIN TRY" in source
    assert "BEGIN TRANSACTION;" in source
    assert "COMMIT TRANSACTION;" in source
    assert "IF @@TRANCOUNT > 0" in source
    assert "ROLLBACK TRANSACTION;" in source
    assert "THROW 51060" in source


def test_validation_strictly_verifies_contract():
    val = _validation_source()

    assert "IF DB_NAME() <> N'EDARSAHUB'" in val
    assert "Falta permiso activo GERENCIA / TES_PAGOS / AUTORIZAR" in val
    assert "Falta permiso activo GERENCIA / TES_PAGOS / RECHAZAR" in val
    assert "Falta permiso activo DIRECCION / TES_PAGOS / AUTORIZAR" in val
    assert "Falta permiso activo DIRECCION / TES_PAGOS / RECHAZAR" in val
    assert "Falta permiso activo TESORERIA / TES_PAGOS / EJECUTAR" in val
    assert "Violacion de segregacion: TESORERIA no debe tener permiso de autorizar o rechazar" in val
    assert "Falta permiso activo ADMIN / TES_PAGOS / AUTORIZAR" in val
    assert "Falta permiso activo SUPERADMIN / TES_PAGOS / AUTORIZAR" in val
    assert "@TotalTargetPerms <> 11" in val
    assert "@TotalMatrixRows <> 2" in val
    assert "Violacion: ADMIN o SUPERADMIN detectados en la matriz operativa" in val


def test_rollback_is_surgical_and_transactional():
    rb = _rollback_source()

    assert "SET XACT_ABORT ON;" in rb
    assert "BEGIN TRANSACTION;" in rb
    assert "DELETE FROM dbo.Usuario_MatrizAutorizacion" in rb
    assert "DELETE FROM dbo.Usuario_PermisosRolModulo" in rb
    assert "WHERE TipoAutorizacionID = @TipoAutorizacionID" in rb
    assert "WHERE ModuloID = @ModuloID" in rb
    assert "DROP TABLE" not in rb
    assert "DROP PROCEDURE" not in rb
    assert "COMMIT TRANSACTION;" in rb
    assert "ROLLBACK TRANSACTION;" in rb
