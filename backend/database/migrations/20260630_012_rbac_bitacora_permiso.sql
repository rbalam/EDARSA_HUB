/*
EDARSAHUB - RBAC Fase 2E
Crear permiso canónico para Bitácora RBAC.

Ejecutar con:
EDARSAHUB_ALLOW_MIGRATIONS=true python backend/tools/edarsahub_sql_runner.py \
  --mode migrate \
  --script backend/database/migrations/20260630_012_rbac_bitacora_permiso.sql

Reglas:
- Idempotente.
- No crea usuarios.
- No toca MongoDB.
- Usa modelo canónico Usuario_Modulos + Usuario_Acciones + Usuario_PermisosRolModulo.
- Permiso efectivo esperado: SISTEMA_RBAC_BITACORA_VER.
*/

SET NOCOUNT ON;
SET XACT_ABORT ON;

BEGIN TRY
    BEGIN TRANSACTION;

    IF OBJECT_ID('dbo.Usuario_Roles', 'U') IS NULL
        THROW 51000, 'No existe dbo.Usuario_Roles.', 1;

    IF OBJECT_ID('dbo.Usuario_Modulos', 'U') IS NULL
        THROW 51000, 'No existe dbo.Usuario_Modulos.', 1;

    IF OBJECT_ID('dbo.Usuario_Acciones', 'U') IS NULL
        THROW 51000, 'No existe dbo.Usuario_Acciones.', 1;

    IF OBJECT_ID('dbo.Usuario_PermisosRolModulo', 'U') IS NULL
        THROW 51000, 'No existe dbo.Usuario_PermisosRolModulo.', 1;

    DECLARE @ModuloID INT;
    DECLARE @AccionID INT;
    DECLARE @PermisosInsertados INT = 0;
    DECLARE @PermisosReactivados INT = 0;

    IF NOT EXISTS (
        SELECT 1
        FROM dbo.Usuario_Modulos
        WHERE CodigoModulo = 'SISTEMA_RBAC_BITACORA'
    )
    BEGIN
        INSERT INTO dbo.Usuario_Modulos (
            ModuloPadreID,
            CodigoModulo,
            NombreModulo,
            Descripcion,
            TipoModulo,
            Ruta,
            Icono,
            OrdenMenu,
            EsVisibleMenu,
            RequiereAutorizacion,
            Activo,
            FechaAlta
        )
        VALUES (
            NULL,
            'SISTEMA_RBAC_BITACORA',
            'Bitácora RBAC',
            'Consulta de bitácora y auditoría de verificaciones RBAC.',
            'MODULO',
            '/usuarios?tab=bitacora',
            'file-text',
            98,
            0,
            0,
            1,
            SYSDATETIME()
        );
    END
    ELSE
    BEGIN
        UPDATE dbo.Usuario_Modulos
        SET
            NombreModulo = COALESCE(NULLIF(NombreModulo, ''), 'Bitácora RBAC'),
            Descripcion = COALESCE(NULLIF(Descripcion, ''), 'Consulta de bitácora y auditoría de verificaciones RBAC.'),
            Activo = 1
        WHERE CodigoModulo = 'SISTEMA_RBAC_BITACORA';
    END;

    SELECT @ModuloID = ModuloID
    FROM dbo.Usuario_Modulos
    WHERE CodigoModulo = 'SISTEMA_RBAC_BITACORA'
      AND Activo = 1;

    IF @ModuloID IS NULL
        THROW 51000, 'No se pudo resolver módulo activo SISTEMA_RBAC_BITACORA.', 1;

    SELECT @AccionID = AccionID
    FROM dbo.Usuario_Acciones
    WHERE CodigoAccion = 'VER'
      AND Activo = 1;

    IF @AccionID IS NULL
        THROW 51000, 'No existe acción activa VER en dbo.Usuario_Acciones.', 1;

    DECLARE @RolesObjetivo TABLE (
        RolID INT NOT NULL PRIMARY KEY,
        CodigoRol VARCHAR(100) NOT NULL
    );

    INSERT INTO @RolesObjetivo (RolID, CodigoRol)
    SELECT
        r.RolID,
        r.CodigoRol
    FROM dbo.Usuario_Roles r
    WHERE r.Activo = 1
      AND (
            r.CodigoRol IN ('SUPERADMIN', 'SUPERADMINISTRADOR')
            OR ISNULL(r.NivelJerarquia, 0) >= 100
      );

    IF NOT EXISTS (SELECT 1 FROM @RolesObjetivo)
        THROW 51000, 'No existe rol activo SuperAdministrador/SUPERADMIN o NivelJerarquia >= 100.', 1;

    UPDATE prm
    SET
        prm.Activo = 1,
        prm.Permitido = 1
    FROM dbo.Usuario_PermisosRolModulo prm
    INNER JOIN @RolesObjetivo ro
        ON ro.RolID = prm.RolID
    WHERE prm.ModuloID = @ModuloID
      AND prm.AccionID = @AccionID
      AND (prm.Activo = 0 OR prm.Permitido = 0);

    SET @PermisosReactivados = @@ROWCOUNT;

    INSERT INTO dbo.Usuario_PermisosRolModulo (
        RolID,
        ModuloID,
        AccionID,
        Permitido,
        RestriccionPropietario,
        RestriccionSucursal,
        RequiereAutorizacion,
        NivelAutorizacionRequerido,
        Activo,
        FechaAlta,
        CreatedBy
    )
    SELECT
        ro.RolID,
        @ModuloID,
        @AccionID,
        1,
        0,
        0,
        0,
        NULL,
        1,
        SYSDATETIME(),
        'RBAC_PHASE2E_BITACORA'
    FROM @RolesObjetivo ro
    WHERE NOT EXISTS (
        SELECT 1
        FROM dbo.Usuario_PermisosRolModulo prm
        WHERE prm.RolID = ro.RolID
          AND prm.ModuloID = @ModuloID
          AND prm.AccionID = @AccionID
    );

    SET @PermisosInsertados = @@ROWCOUNT;

    SELECT
        'RBAC_BITACORA_PERMISSION_MIGRATION' AS paso,
        @ModuloID AS modulo_id,
        @AccionID AS accion_id,
        @PermisosInsertados AS permisos_insertados,
        @PermisosReactivados AS permisos_reactivados;

    SELECT
        'RBAC_BITACORA_PERMISSION_RESULT' AS paso,
        r.CodigoRol,
        m.CodigoModulo,
        a.CodigoAccion,
        CONCAT(UPPER(m.CodigoModulo), '_', UPPER(a.CodigoAccion)) AS permiso_normalizado,
        prm.Permitido,
        prm.Activo
    FROM dbo.Usuario_PermisosRolModulo prm
    INNER JOIN dbo.Usuario_Roles r
        ON r.RolID = prm.RolID
    INNER JOIN dbo.Usuario_Modulos m
        ON m.ModuloID = prm.ModuloID
    INNER JOIN dbo.Usuario_Acciones a
        ON a.AccionID = prm.AccionID
    WHERE m.CodigoModulo = 'SISTEMA_RBAC_BITACORA'
      AND a.CodigoAccion = 'VER'
      AND r.RolID IN (SELECT RolID FROM @RolesObjetivo)
    ORDER BY r.NivelJerarquia DESC, r.CodigoRol;

    COMMIT TRANSACTION;
END TRY
BEGIN CATCH
    IF @@TRANCOUNT > 0
        ROLLBACK TRANSACTION;

    DECLARE @ErrorMessage NVARCHAR(4000) = ERROR_MESSAGE();
    THROW 51000, @ErrorMessage, 1;
END CATCH;
