from pathlib import Path


ROOT = Path("/app")
MIGRATION = ROOT / (
    "backend/database/migrations/"
    "20260819_034_usuario_autorizaciones_contexto.sql"
)
VALIDATION = ROOT / (
    "backend/database/validation/"
    "20260819_034_usuario_autorizaciones_contexto_validation.sql"
)
ROLLBACK = ROOT / (
    "backend/database/rollback/"
    "20260819_034_usuario_autorizaciones_contexto_rollback.sql"
)


def _migration_source() -> str:
    return MIGRATION.read_text(encoding="utf-8")


def _validation_source() -> str:
    return VALIDATION.read_text(encoding="utf-8")


def _rollback_source() -> str:
    return ROLLBACK.read_text(encoding="utf-8")


def test_migration_adds_canonical_column_and_configures_aut_tes_pagos():
    source = _migration_source()

    assert "RequiereUnidadNegocio BIT NOT NULL" in source
    assert "DF_Usuario_TiposAutorizacion_RequiereUnidadNegocio DEFAULT (0)" in source
    assert "UPDATE dbo.Usuario_TiposAutorizacion" in source
    assert "SET RequiereUnidadNegocio = 1" in source
    assert "WHERE CodigoTipoAutorizacion = 'AUT_TES_PAGOS'" in source
    # Dynamic update by code, no hardcoded ID
    assert "TipoAutorizacionID = 4" not in source


def test_migration_sp_has_no_user_or_personal_hardcodes():
    source = _migration_source()

    assert "@edarsa" not in source
    assert "ricardo" not in source.lower()
    assert "carlos" not in source.lower()
    assert "UsuarioID = 1" not in source
    assert "UsuarioID = 8" not in source
    assert "INSERT INTO dbo.Usuario_RolesContexto" not in source
    assert "INSERT INTO dbo.Usuario_RolesAsignacion" not in source


def test_sp_enforces_unit_context_fail_closed_for_configured_types():
    source = _migration_source()

    assert "@UnidadNegocioID UNIQUEIDENTIFIER = NULL" in source
    assert "@RequiereUnidadNegocio = 1 AND @UnidadNegocioID IS NULL" in source
    assert "THROW 51046, 'La autorizacion requiere especificar una unidad de negocio.', 1;" in source
    assert "FROM dbo.Unidades_Negocio" in source
    assert "THROW 51045, 'Unidad de negocio inexistente o inactiva.', 1;" in source


def test_sp_resolves_contextual_approvers_with_exact_priority_over_global():
    source = _migration_source()

    assert "FROM dbo.Usuario_RolesContexto AS urc" in source
    assert "urc.RolID = MA.RolID" in source
    assert "urc.Activo = 1" in source
    assert "urc.FechaBaja IS NULL OR urc.FechaBaja > SYSDATETIME()" in source
    assert "urc.UnidadNegocioID = @UnidadNegocioID OR urc.UnidadNegocioID IS NULL" in source
    assert "CASE WHEN @UnidadNegocioID IS NOT NULL AND urc.UnidadNegocioID = @UnidadNegocioID THEN 0 ELSE 1 END" in source
    assert "urc.EsRolPrimario DESC" in source
    assert "THROW 51036, 'La matriz aplicable no tiene autorizadores activos.', 1;" in source


def test_slice_1_transactional_guarantees_strictly_preserved():
    source = _migration_source()

    assert "SET XACT_ABORT ON;" in source
    assert "BEGIN TRANSACTION;" in source
    assert "COMMIT TRANSACTION;" in source
    assert "IF @@TRANCOUNT > 0" in source
    assert "ROLLBACK TRANSACTION;" in source
    assert "EXEC dbo.sp_Usuario_LogActividad" in source


def test_validation_verifies_context_contract_and_absence_of_synthetic_users():
    val = _validation_source()

    assert "IF DB_NAME() <> N'EDARSAHUB'" in val
    assert "RequiereUnidadNegocio" in val
    assert "AUT_TES_PAGOS" in val
    assert "@UnidadNegocioID UNIQUEIDENTIFIER = NULL" in val
    assert "dbo.Usuario_RolesContexto" in val
    assert "dbo.Unidades_Negocio" in val
    assert "WHERE r.CodigoRol IN ('GERENCIA', 'DIRECCION')" in val
    assert "VALIDATION_SUCCESS" in val


def test_rollback_restores_slice_1_sp_definition_and_removes_column():
    rb = _rollback_source()

    assert "CREATE OR ALTER PROCEDURE dbo.sp_Usuario_CrearAutorizacion" in rb
    assert "@UnidadNegocioID" not in rb
    assert "FROM dbo.Usuario_RolesAsignacion AS URA" in rb
    assert "ALTER TABLE dbo.Usuario_TiposAutorizacion DROP CONSTRAINT" in rb
    assert "ALTER TABLE dbo.Usuario_TiposAutorizacion" in rb
    assert "DROP COLUMN RequiereUnidadNegocio" in rb
