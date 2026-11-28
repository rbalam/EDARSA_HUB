-- GATE-M2 R3: Registro canonico de /worker-console (sistema.worker_console) en dbo.Sistema_ModulosMenus
-- Idempotente, transaccional, reversible y exclusivo de EDARSAHUB Desarrollo (production_allowed=false).
SET NOCOUNT ON;
SET XACT_ABORT ON;

BEGIN TRY
    IF DB_NAME() <> N'EDARSAHUB'
        THROW 51000, 'UNEXPECTED_DATABASE_FORBIDDEN', 1;

    BEGIN TRANSACTION;

    DECLARE @ModuloID INT;
    DECLARE @Orden INT;

    SELECT @ModuloID = ModuloID
    FROM dbo.Sistema_Modulos WITH (UPDLOCK, HOLDLOCK)
    WHERE Codigo = N'SISTEMA'
      AND ISNULL(Activo, 1) = 1;

    IF @ModuloID IS NULL
        THROW 51001, 'SISTEMA_MODULE_NOT_FOUND', 1;

    IF EXISTS (
        SELECT 1
        FROM dbo.Sistema_ModulosMenus
        WHERE Codigo = N'sistema.worker_console'
          AND (
              ModuloID <> @ModuloID
              OR ISNULL(Ruta, N'') <> N'/worker-console'
          )
    )
        THROW 51002, 'WORKER_CONSOLE_MENU_CODE_COLLISION', 1;

    IF EXISTS (
        SELECT 1
        FROM dbo.Sistema_ModulosMenus
        WHERE Ruta = N'/worker-console'
          AND Codigo <> N'sistema.worker_console'
    )
        THROW 51003, 'WORKER_CONSOLE_MENU_ROUTE_COLLISION', 1;

    IF NOT EXISTS (
        SELECT 1
        FROM dbo.Sistema_ModulosMenus WITH (UPDLOCK, HOLDLOCK)
        WHERE Codigo = N'sistema.worker_console'
    )
    BEGIN
        SELECT @Orden = ISNULL(MAX(Orden), 0) + 1
        FROM dbo.Sistema_ModulosMenus
        WHERE ModuloID = @ModuloID;

        INSERT INTO dbo.Sistema_ModulosMenus (
            ModuloID,
            MenuPadreID,
            Codigo,
            Nombre,
            Descripcion,
            Icono,
            Ruta,
            Orden,
            RequierePermiso,
            Activo,
            FechaCreacion
        )
        VALUES (
            @ModuloID,
            NULL,
            N'sistema.worker_console',
            N'Universal Worker Console',
            N'Consola operativa de Universal Worker V4, auditoria y estado SQL canonico',
            N'ShieldCheck',
            N'/worker-console',
            @Orden,
            N'RBAC_ADMIN',
            1,
            GETDATE()
        );
    END
    ELSE
    BEGIN
        UPDATE dbo.Sistema_ModulosMenus
        SET Nombre = N'Universal Worker Console',
            Descripcion = N'Consola operativa de Universal Worker V4, auditoria y estado SQL canonico',
            Icono = N'ShieldCheck',
            RequierePermiso = N'RBAC_ADMIN',
            Activo = 1
        WHERE Codigo = N'sistema.worker_console'
          AND ModuloID = @ModuloID
          AND Ruta = N'/worker-console';
    END;

    COMMIT TRANSACTION;
END TRY
BEGIN CATCH
    IF @@TRANCOUNT > 0 ROLLBACK TRANSACTION;
    THROW;
END CATCH;
