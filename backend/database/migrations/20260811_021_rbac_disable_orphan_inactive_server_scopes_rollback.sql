/*
Rollback exacto:
20260811_021_rbac_disable_orphan_inactive_server_scopes.sql

Restaura exclusivamente la preimagen auditada.
*/

SET NOCOUNT ON;
SET XACT_ABORT ON;

BEGIN TRY
    BEGIN TRANSACTION;

    ------------------------------------------------------------
    -- Restaurar scopes de servidor.
    ------------------------------------------------------------

    UPDATE dbo.Usuario_ServidoresAsignacion
    SET
        Activo = 1,
        FechaModificacion = NULL,
        ModificadoPor = NULL,
        Observaciones =
            N'RBAC-SCOPE-E-HARDENED: Escritura SQL productiva'
    WHERE AsignacionID = 243
      AND UsuarioID = 3
      AND ServidorID =
          'd8425038-5e57-42d9-8f3a-62e287888874';

    IF @@ROWCOUNT <> 1
    BEGIN
        THROW 51100,
            'Rollback abort: server assignment 243 cardinality mismatch.',
            1;
    END;

    UPDATE dbo.Usuario_ServidoresAsignacion
    SET
        Activo = 1,
        FechaModificacion = NULL,
        ModificadoPor = NULL,
        Observaciones =
            N'RBAC-SCOPE-E-HARDENED: Escritura SQL productiva'
    WHERE AsignacionID = 250
      AND UsuarioID = 3
      AND ServidorID =
          'b5175237-5e57-41f3-ab6d-b5ae2f5e780b';

    IF @@ROWCOUNT <> 1
    BEGIN
        THROW 51101,
            'Rollback abort: server assignment 250 cardinality mismatch.',
            1;
    END;

    ------------------------------------------------------------
    -- Restaurar scopes de sucursal.
    ------------------------------------------------------------

    UPDATE dbo.Usuario_SucursalesAsignacion
    SET
        Activo = 1,
        FechaModificacion = NULL,
        ModificadoPor = NULL,
        Observaciones =
            N'RBAC-SCOPE-E-HARDENED: Escritura SQL productiva'
    WHERE AsignacionID = 245
      AND UsuarioID = 3
      AND ServidorID =
          'b5175237-5e57-41f3-ab6d-b5ae2f5e780b'
      AND SucursalCodigo = 'default';

    IF @@ROWCOUNT <> 1
    BEGIN
        THROW 51102,
            'Rollback abort: branch assignment 245 cardinality mismatch.',
            1;
    END;

    UPDATE dbo.Usuario_SucursalesAsignacion
    SET
        Activo = 1,
        FechaModificacion = NULL,
        ModificadoPor = NULL,
        Observaciones =
            N'RBAC-SCOPE-E-HARDENED: Escritura SQL productiva'
    WHERE AsignacionID = 249
      AND UsuarioID = 3
      AND ServidorID =
          'd8425038-5e57-42d9-8f3a-62e287888874'
      AND SucursalCodigo = 'default';

    IF @@ROWCOUNT <> 1
    BEGIN
        THROW 51103,
            'Rollback abort: branch assignment 249 cardinality mismatch.',
            1;
    END;

    COMMIT TRANSACTION;

    SELECT
        CAST(1 AS bit) AS Success,
        2 AS ServerScopesRestored,
        2 AS BranchScopesRestored,
        'ROLLBACK_PASS' AS Resultado;

END TRY
BEGIN CATCH

    IF @@TRANCOUNT > 0
        ROLLBACK TRANSACTION;

    THROW;

END CATCH;
