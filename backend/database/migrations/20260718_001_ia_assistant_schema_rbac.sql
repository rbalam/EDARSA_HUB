/*
EDARSAHUB V1.0
Asistente IA: esquema, integridad, RBAC y menú SQL canónico.

Características:
- SQL Server / base EDARSAHUB únicamente.
- Idempotente.
- Transaccional.
- Serializada mediante sp_getapplock.
- Compatible con las tablas legacy creadas originalmente por runtime.
- No elimina datos.
- No concede IA a roles operativos.
- Alcance inicial: SUPERADMIN y ADMINISTRADOR, con sus alias activos.
*/

SET NOCOUNT ON;
SET XACT_ABORT ON;

IF DB_NAME() <> N'EDARSAHUB'
BEGIN
    THROW 51000,
        'La migración IA solo puede ejecutarse en EDARSAHUB.',
        1;
END;

BEGIN TRY
    BEGIN TRANSACTION;

    DECLARE @LockResult INT;

    EXEC @LockResult = sys.sp_getapplock
        @Resource = N'EDARSAHUB:IA_ASSISTANT:SCHEMA_RBAC',
        @LockMode = N'Exclusive',
        @LockOwner = N'Transaction',
        @LockTimeout = 15000;

    IF @LockResult < 0
    BEGIN
        THROW 51001,
            'No fue posible adquirir el lock de migración IA.',
            1;
    END;

    /* =========================================================
       TABLA: IA_Assistant_Sesiones
       ========================================================= */

    IF OBJECT_ID(
        N'dbo.IA_Assistant_Sesiones',
        N'U'
    ) IS NULL
    BEGIN
        CREATE TABLE dbo.IA_Assistant_Sesiones (
            SesionID UNIQUEIDENTIFIER NOT NULL
                CONSTRAINT PK_IA_Assistant_Sesiones
                PRIMARY KEY
                CONSTRAINT DF_IA_Assistant_Sesiones_ID
                DEFAULT NEWID(),

            UsuarioEmail NVARCHAR(320) NOT NULL,

            Titulo NVARCHAR(300) NOT NULL
                CONSTRAINT DF_IA_Assistant_Sesiones_Titulo
                DEFAULT N'Nueva conversación',

            Modelo VARCHAR(50) NOT NULL,

            Activo BIT NOT NULL
                CONSTRAINT DF_IA_Assistant_Sesiones_Activo
                DEFAULT 1,

            FechaCreacion DATETIME2 NOT NULL
                CONSTRAINT DF_IA_Assistant_Sesiones_Creacion
                DEFAULT SYSUTCDATETIME(),

            FechaActualizacion DATETIME2 NOT NULL
                CONSTRAINT DF_IA_Assistant_Sesiones_Actualizacion
                DEFAULT SYSUTCDATETIME()
        );
    END;

    IF COL_LENGTH(
        N'dbo.IA_Assistant_Sesiones',
        N'SesionID'
    ) IS NULL
    OR COL_LENGTH(
        N'dbo.IA_Assistant_Sesiones',
        N'UsuarioEmail'
    ) IS NULL
    OR COL_LENGTH(
        N'dbo.IA_Assistant_Sesiones',
        N'Titulo'
    ) IS NULL
    OR COL_LENGTH(
        N'dbo.IA_Assistant_Sesiones',
        N'Modelo'
    ) IS NULL
    OR COL_LENGTH(
        N'dbo.IA_Assistant_Sesiones',
        N'Activo'
    ) IS NULL
    OR COL_LENGTH(
        N'dbo.IA_Assistant_Sesiones',
        N'FechaCreacion'
    ) IS NULL
    OR COL_LENGTH(
        N'dbo.IA_Assistant_Sesiones',
        N'FechaActualizacion'
    ) IS NULL
    BEGIN
        THROW 51002,
            'IA_Assistant_Sesiones tiene un contrato incompatible.',
            1;
    END;

    IF EXISTS (
        SELECT 1
        FROM sys.columns c
        INNER JOIN sys.types t
            ON t.user_type_id = c.user_type_id
        WHERE c.object_id =
            OBJECT_ID(N'dbo.IA_Assistant_Sesiones')
          AND c.name = N'SesionID'
          AND (
                t.name <> N'uniqueidentifier'
             OR c.is_nullable = 1
          )
    )
    BEGIN
        THROW 51003,
            'SesionID tiene un tipo o nulabilidad incompatible.',
            1;
    END;

    IF EXISTS (
        SELECT 1
        FROM sys.columns c
        INNER JOIN sys.types t
            ON t.user_type_id = c.user_type_id
        WHERE c.object_id =
            OBJECT_ID(N'dbo.IA_Assistant_Sesiones')
          AND c.name = N'UsuarioEmail'
          AND (
                t.name <> N'nvarchar'
             OR c.is_nullable = 1
          )
    )
    BEGIN
        THROW 51004,
            'UsuarioEmail tiene un tipo o nulabilidad incompatible.',
            1;
    END;

    IF EXISTS (
        SELECT 1
        FROM sys.columns c
        INNER JOIN sys.types t
            ON t.user_type_id = c.user_type_id
        WHERE c.object_id =
            OBJECT_ID(N'dbo.IA_Assistant_Sesiones')
          AND c.name = N'UsuarioEmail'
          AND t.name = N'nvarchar'
          AND c.max_length <> -1
          AND c.max_length < 640
    )
    BEGIN
        ALTER TABLE dbo.IA_Assistant_Sesiones
        ALTER COLUMN UsuarioEmail NVARCHAR(320) NOT NULL;
    END;

    /* Defaults requeridos por el repository. */

    IF NOT EXISTS (
        SELECT 1
        FROM sys.columns
        WHERE object_id =
            OBJECT_ID(N'dbo.IA_Assistant_Sesiones')
          AND name = N'Titulo'
          AND default_object_id <> 0
    )
    BEGIN
        ALTER TABLE dbo.IA_Assistant_Sesiones
        ADD CONSTRAINT DF_IA_Assistant_Sesiones_Titulo
            DEFAULT N'Nueva conversación'
            FOR Titulo;
    END;

    IF NOT EXISTS (
        SELECT 1
        FROM sys.columns
        WHERE object_id =
            OBJECT_ID(N'dbo.IA_Assistant_Sesiones')
          AND name = N'Activo'
          AND default_object_id <> 0
    )
    BEGIN
        ALTER TABLE dbo.IA_Assistant_Sesiones
        ADD CONSTRAINT DF_IA_Assistant_Sesiones_Activo
            DEFAULT 1
            FOR Activo;
    END;

    IF NOT EXISTS (
        SELECT 1
        FROM sys.columns
        WHERE object_id =
            OBJECT_ID(N'dbo.IA_Assistant_Sesiones')
          AND name = N'FechaCreacion'
          AND default_object_id <> 0
    )
    BEGIN
        ALTER TABLE dbo.IA_Assistant_Sesiones
        ADD CONSTRAINT DF_IA_Assistant_Sesiones_Creacion
            DEFAULT SYSUTCDATETIME()
            FOR FechaCreacion;
    END;

    IF NOT EXISTS (
        SELECT 1
        FROM sys.columns
        WHERE object_id =
            OBJECT_ID(N'dbo.IA_Assistant_Sesiones')
          AND name = N'FechaActualizacion'
          AND default_object_id <> 0
    )
    BEGIN
        ALTER TABLE dbo.IA_Assistant_Sesiones
        ADD CONSTRAINT DF_IA_Assistant_Sesiones_Actualizacion
            DEFAULT SYSUTCDATETIME()
            FOR FechaActualizacion;
    END;

    /* =========================================================
       TABLA: IA_Assistant_Mensajes
       ========================================================= */

    IF OBJECT_ID(
        N'dbo.IA_Assistant_Mensajes',
        N'U'
    ) IS NULL
    BEGIN
        CREATE TABLE dbo.IA_Assistant_Mensajes (
            MensajeID UNIQUEIDENTIFIER NOT NULL
                CONSTRAINT PK_IA_Assistant_Mensajes
                PRIMARY KEY
                CONSTRAINT DF_IA_Assistant_Mensajes_ID
                DEFAULT NEWID(),

            SesionID UNIQUEIDENTIFIER NOT NULL,

            Rol VARCHAR(20) NOT NULL,

            Contenido NVARCHAR(MAX) NOT NULL,

            FechaCreacion DATETIME2 NOT NULL
                CONSTRAINT DF_IA_Assistant_Mensajes_Creacion
                DEFAULT SYSUTCDATETIME()
        );
    END;

    IF COL_LENGTH(
        N'dbo.IA_Assistant_Mensajes',
        N'MensajeID'
    ) IS NULL
    OR COL_LENGTH(
        N'dbo.IA_Assistant_Mensajes',
        N'SesionID'
    ) IS NULL
    OR COL_LENGTH(
        N'dbo.IA_Assistant_Mensajes',
        N'Rol'
    ) IS NULL
    OR COL_LENGTH(
        N'dbo.IA_Assistant_Mensajes',
        N'Contenido'
    ) IS NULL
    OR COL_LENGTH(
        N'dbo.IA_Assistant_Mensajes',
        N'FechaCreacion'
    ) IS NULL
    BEGIN
        THROW 51005,
            'IA_Assistant_Mensajes tiene un contrato incompatible.',
            1;
    END;

    IF EXISTS (
        SELECT 1
        FROM sys.columns c
        INNER JOIN sys.types t
            ON t.user_type_id = c.user_type_id
        WHERE c.object_id =
            OBJECT_ID(N'dbo.IA_Assistant_Mensajes')
          AND c.name IN (
                N'MensajeID',
                N'SesionID'
          )
          AND (
                t.name <> N'uniqueidentifier'
             OR c.is_nullable = 1
          )
    )
    BEGIN
        THROW 51006,
            'Los identificadores de mensajes tienen contrato incompatible.',
            1;
    END;

    IF EXISTS (
        SELECT 1
        FROM sys.columns c
        INNER JOIN sys.types t
            ON t.user_type_id = c.user_type_id
        WHERE c.object_id =
            OBJECT_ID(N'dbo.IA_Assistant_Mensajes')
          AND c.name = N'Contenido'
          AND (
                t.name <> N'nvarchar'
             OR c.max_length <> -1
             OR c.is_nullable = 1
          )
    )
    BEGIN
        THROW 51007,
            'Contenido debe ser NVARCHAR(MAX) NOT NULL.',
            1;
    END;

    IF NOT EXISTS (
        SELECT 1
        FROM sys.columns
        WHERE object_id =
            OBJECT_ID(N'dbo.IA_Assistant_Mensajes')
          AND name = N'FechaCreacion'
          AND default_object_id <> 0
    )
    BEGIN
        ALTER TABLE dbo.IA_Assistant_Mensajes
        ADD CONSTRAINT DF_IA_Assistant_Mensajes_Creacion
            DEFAULT SYSUTCDATETIME()
            FOR FechaCreacion;
    END;

    /* =========================================================
       INTEGRIDAD REFERENCIAL
       ========================================================= */

    IF EXISTS (
        SELECT 1
        FROM dbo.IA_Assistant_Mensajes m
        LEFT JOIN dbo.IA_Assistant_Sesiones s
            ON s.SesionID = m.SesionID
        WHERE s.SesionID IS NULL
    )
    BEGIN
        THROW 51008,
            'Existen mensajes IA huérfanos; no puede agregarse la FK.',
            1;
    END;

    IF NOT EXISTS (
        SELECT 1
        FROM sys.foreign_key_columns fkc
        WHERE fkc.parent_object_id =
            OBJECT_ID(N'dbo.IA_Assistant_Mensajes')
          AND fkc.referenced_object_id =
            OBJECT_ID(N'dbo.IA_Assistant_Sesiones')
          AND COL_NAME(
                fkc.parent_object_id,
                fkc.parent_column_id
              ) = N'SesionID'
          AND COL_NAME(
                fkc.referenced_object_id,
                fkc.referenced_column_id
              ) = N'SesionID'
    )
    BEGIN
        ALTER TABLE dbo.IA_Assistant_Mensajes
        WITH CHECK
        ADD CONSTRAINT FK_IA_Assistant_Mensajes_Sesion
        FOREIGN KEY (SesionID)
        REFERENCES dbo.IA_Assistant_Sesiones (SesionID);
    END;

    /* =========================================================
       ÍNDICES
       ========================================================= */

    IF NOT EXISTS (
        SELECT 1
        FROM sys.indexes
        WHERE object_id =
            OBJECT_ID(N'dbo.IA_Assistant_Sesiones')
          AND name =
            N'IX_IA_Assistant_Sesiones_Usuario_Activo'
    )
    BEGIN
        CREATE INDEX
            IX_IA_Assistant_Sesiones_Usuario_Activo
        ON dbo.IA_Assistant_Sesiones (
            UsuarioEmail,
            Activo,
            FechaActualizacion DESC
        );
    END;

    IF NOT EXISTS (
        SELECT 1
        FROM sys.indexes
        WHERE object_id =
            OBJECT_ID(N'dbo.IA_Assistant_Mensajes')
          AND name IN (
              N'IX_IA_Mensajes_Sesion',
              N'IX_IA_Assistant_Mensajes_Sesion_Fecha'
          )
    )
    BEGIN
        CREATE INDEX
            IX_IA_Assistant_Mensajes_Sesion_Fecha
        ON dbo.IA_Assistant_Mensajes (
            SesionID,
            FechaCreacion
        );
    END;

    /* =========================================================
       RBAC CANÓNICO: Usuario_Modulos
       ========================================================= */

    IF OBJECT_ID(
        N'dbo.Usuario_Modulos',
        N'U'
    ) IS NULL
    OR OBJECT_ID(
        N'dbo.Usuario_Acciones',
        N'U'
    ) IS NULL
    OR OBJECT_ID(
        N'dbo.Usuario_Roles',
        N'U'
    ) IS NULL
    OR OBJECT_ID(
        N'dbo.Usuario_PermisosRolModulo',
        N'U'
    ) IS NULL
    BEGIN
        THROW 51009,
            'Faltan tablas canónicas de RBAC.',
            1;
    END;

    IF NOT EXISTS (
        SELECT 1
        FROM dbo.Usuario_Modulos
        WHERE CodigoModulo = N'IA_ASSISTANT'
    )
    BEGIN
        INSERT INTO dbo.Usuario_Modulos (
            CodigoModulo,
            NombreModulo,
            Descripcion,
            Icono,
            Ruta,
            Activo
        )
        VALUES (
            N'IA_ASSISTANT',
            N'Asistente IA',
            N'Asistente conversacional corporativo SQL-first',
            N'Sparkles',
            N'/ia',
            1
        );
    END
    ELSE
    BEGIN
        UPDATE dbo.Usuario_Modulos
        SET
            NombreModulo = N'Asistente IA',
            Descripcion =
                N'Asistente conversacional corporativo SQL-first',
            Icono = N'Sparkles',
            Ruta = N'/ia',
            Activo = 1
        WHERE CodigoModulo = N'IA_ASSISTANT';
    END;

    DECLARE @UsuarioModuloID INT;
    DECLARE @AccionVerID INT;

    SELECT @UsuarioModuloID = ModuloID
    FROM dbo.Usuario_Modulos
    WHERE CodigoModulo = N'IA_ASSISTANT'
      AND Activo = 1;

    SELECT TOP (1)
        @AccionVerID = AccionID
    FROM dbo.Usuario_Acciones
    WHERE CodigoAccion = N'VER'
      AND Activo = 1
    ORDER BY AccionID;

    IF @UsuarioModuloID IS NULL
    BEGIN
        THROW 51010,
            'No fue posible resolver IA_ASSISTANT en Usuario_Modulos.',
            1;
    END;

    IF @AccionVerID IS NULL
    BEGIN
        THROW 51011,
            'No existe la acción VER activa.',
            1;
    END;

    DECLARE @RolesObjetivo TABLE (
        CodigoRol VARCHAR(100) NOT NULL
            PRIMARY KEY
    );

    INSERT INTO @RolesObjetivo (
        CodigoRol
    )
    VALUES
        ('SUPERADMIN'),
        ('SUPERADMINISTRADOR'),
        ('ADMIN'),
        ('ADMINISTRADOR');

    IF NOT EXISTS (
        SELECT 1
        FROM dbo.Usuario_Roles r
        WHERE r.Activo = 1
          AND r.CodigoRol IN (
              'SUPERADMIN',
              'SUPERADMINISTRADOR'
          )
    )
    BEGIN
        THROW 51012,
            'No existe un rol SUPERADMIN activo.',
            1;
    END;

    IF NOT EXISTS (
        SELECT 1
        FROM dbo.Usuario_Roles r
        WHERE r.Activo = 1
          AND r.CodigoRol IN (
              'ADMIN',
              'ADMINISTRADOR'
          )
    )
    BEGIN
        THROW 51013,
            'No existe un rol ADMINISTRADOR activo.',
            1;
    END;

    UPDATE prm
    SET
        prm.Permitido = 1,
        prm.Activo = 1
    FROM dbo.Usuario_PermisosRolModulo prm
    INNER JOIN dbo.Usuario_Roles r
        ON r.RolID = prm.RolID
    INNER JOIN @RolesObjetivo o
        ON o.CodigoRol = r.CodigoRol
    WHERE prm.ModuloID = @UsuarioModuloID
      AND prm.AccionID = @AccionVerID
      AND r.Activo = 1;

    INSERT INTO dbo.Usuario_PermisosRolModulo (
        RolID,
        ModuloID,
        AccionID,
        Permitido,
        RestriccionPropietario,
        RestriccionSucursal,
        RequiereAutorizacion,
        Activo,
        FechaAlta,
        CreatedBy
    )
    SELECT
        r.RolID,
        @UsuarioModuloID,
        @AccionVerID,
        1,
        0,
        0,
        0,
        1,
        SYSDATETIME(),
        N'IA_ASSISTANT_V1'
    FROM dbo.Usuario_Roles r
    INNER JOIN @RolesObjetivo o
        ON o.CodigoRol = r.CodigoRol
    WHERE r.Activo = 1
      AND NOT EXISTS (
          SELECT 1
          FROM dbo.Usuario_PermisosRolModulo prm
          WHERE prm.RolID = r.RolID
            AND prm.ModuloID = @UsuarioModuloID
            AND prm.AccionID = @AccionVerID
      );

    /* =========================================================
       MENÚ SQL CANÓNICO
       ========================================================= */

    IF OBJECT_ID(
        N'dbo.Sistema_Modulos',
        N'U'
    ) IS NULL
    OR OBJECT_ID(
        N'dbo.Sistema_ModulosMenus',
        N'U'
    ) IS NULL
    BEGIN
        THROW 51014,
            'Faltan tablas canónicas del menú SQL.',
            1;
    END;

    DECLARE @SistemaModuloID INT;
    DECLARE @SistemaMenuID INT;
    DECLARE @ModuloEsIdentity BIT;
    DECLARE @MenuEsIdentity BIT;

    /*
       PRESERVE_EXISTING_IA_SYSTEM_MODULE

       Si dbo.Sistema_Modulos.Codigo = 'IA' ya existe:
       - conservar Nombre;
       - conservar Descripcion;
       - conservar Icono;
       - conservar Orden;
       - conservar EsPrincipal/EsSatelite/EsPortal;
       - conservar URLExterna.

       El menú /ia se administra en Sistema_ModulosMenus.
    */

    IF (
        SELECT COUNT(*)
        FROM dbo.Sistema_Modulos
        WHERE Codigo = N'IA'
    ) > 1
    BEGIN
        THROW 51020,
            'Existen múltiples módulos Sistema_Modulos con Codigo IA.',
            1;
    END;

    SELECT TOP (1)
        @SistemaModuloID = ModuloID
    FROM dbo.Sistema_Modulos
    WHERE Codigo = N'IA'
    ORDER BY ModuloID;

    SET @ModuloEsIdentity =
        CONVERT(
            BIT,
            COLUMNPROPERTY(
                OBJECT_ID(N'dbo.Sistema_Modulos'),
                N'ModuloID',
                'IsIdentity'
            )
        );

    IF @SistemaModuloID IS NULL
    BEGIN
        DECLARE @NuevoOrdenIA INT;

        SELECT
            @NuevoOrdenIA =
                ISNULL(MAX(Orden), 0) + 1
        FROM dbo.Sistema_Modulos
            WITH (UPDLOCK, HOLDLOCK);

        IF @ModuloEsIdentity = 1
        BEGIN
            INSERT INTO dbo.Sistema_Modulos (
                Codigo,
                Nombre,
                Descripcion,
                Icono,
                Orden,
                EsPrincipal,
                EsSatelite,
                EsPortal,
                URLExterna,
                Activo,
                FechaCreacion
            )
            VALUES (
                N'IA',
                N'Inteligencia Artificial',
                N'Asistentes, análisis, automatización',
                N'Brain',
                @NuevoOrdenIA,
                1,
                0,
                0,
                NULL,
                1,
                GETDATE()
            );

            SET @SistemaModuloID =
                CONVERT(INT, SCOPE_IDENTITY());
        END
        ELSE
        BEGIN
            SELECT
                @SistemaModuloID =
                    ISNULL(MAX(ModuloID), 0) + 1
            FROM dbo.Sistema_Modulos
                WITH (UPDLOCK, HOLDLOCK);

            INSERT INTO dbo.Sistema_Modulos (
                ModuloID,
                Codigo,
                Nombre,
                Descripcion,
                Icono,
                Orden,
                EsPrincipal,
                EsSatelite,
                EsPortal,
                URLExterna,
                Activo,
                FechaCreacion
            )
            VALUES (
                @SistemaModuloID,
                N'IA',
                N'Inteligencia Artificial',
                N'Asistentes, análisis, automatización',
                N'Brain',
                @NuevoOrdenIA,
                1,
                0,
                0,
                NULL,
                1,
                GETDATE()
            );
        END;
    END;

    IF NOT EXISTS (
        SELECT 1
        FROM dbo.Sistema_Modulos
        WHERE ModuloID = @SistemaModuloID
          AND ISNULL(Activo, 1) = 1
    )
    BEGIN
        THROW 51021,
            'El módulo IA existe pero no está activo.',
            1;
    END;

    IF (
        SELECT COUNT(*)
        FROM dbo.Sistema_ModulosMenus
        WHERE Codigo = N'ia.assistant'
           OR Ruta = N'/ia'
    ) > 1
    BEGIN
        THROW 51015,
            'Existen múltiples registros de menú IA.',
            1;
    END;

    SELECT TOP (1)
        @SistemaMenuID = MenuID
    FROM dbo.Sistema_ModulosMenus
    WHERE Codigo = N'ia.assistant'
       OR Ruta = N'/ia'
    ORDER BY MenuID;

    SET @MenuEsIdentity =
        CONVERT(
            BIT,
            COLUMNPROPERTY(
                OBJECT_ID(N'dbo.Sistema_ModulosMenus'),
                N'MenuID',
                'IsIdentity'
            )
        );

    IF @SistemaMenuID IS NULL
    BEGIN
        IF @MenuEsIdentity = 1
        BEGIN
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
            SELECT
                @SistemaModuloID,
                NULL,
                N'ia.assistant',
                N'Asistente IA',
                N'Asistente conversacional corporativo',
                N'Sparkles',
                N'/ia',
                ISNULL(MAX(Orden), 0) + 1,
                N'IA_ASSISTANT',
                1,
                GETDATE()
            FROM dbo.Sistema_ModulosMenus
            WHERE ModuloID = @SistemaModuloID;

            SET @SistemaMenuID =
                CONVERT(INT, SCOPE_IDENTITY());
        END
        ELSE
        BEGIN
            SELECT
                @SistemaMenuID =
                    ISNULL(MAX(MenuID), 0) + 1
            FROM dbo.Sistema_ModulosMenus
                WITH (UPDLOCK, HOLDLOCK);

            INSERT INTO dbo.Sistema_ModulosMenus (
                MenuID,
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
            SELECT
                @SistemaMenuID,
                @SistemaModuloID,
                NULL,
                N'ia.assistant',
                N'Asistente IA',
                N'Asistente conversacional corporativo',
                N'Sparkles',
                N'/ia',
                ISNULL(MAX(Orden), 0) + 1,
                N'IA_ASSISTANT',
                1,
                GETDATE()
            FROM dbo.Sistema_ModulosMenus
            WHERE ModuloID = @SistemaModuloID;
        END;
    END
    ELSE
    BEGIN
        UPDATE dbo.Sistema_ModulosMenus
        SET
            ModuloID = @SistemaModuloID,
            MenuPadreID = NULL,
            Codigo = N'ia.assistant',
            Nombre = N'Asistente IA',
            Descripcion =
                N'Asistente conversacional corporativo',
            Icono = N'Sparkles',
            Ruta = N'/ia',
            RequierePermiso = N'IA_ASSISTANT',
            Activo = 1
        WHERE MenuID = @SistemaMenuID;
    END;

    COMMIT TRANSACTION;

    SELECT
        N'IA_ASSISTANT_MIGRATION_READY' AS resultado,
        @UsuarioModuloID AS usuario_modulo_id,
        @AccionVerID AS accion_ver_id,
        @SistemaModuloID AS sistema_modulo_id,
        @SistemaMenuID AS sistema_menu_id;
END TRY
BEGIN CATCH
    IF @@TRANCOUNT > 0
    BEGIN
        ROLLBACK TRANSACTION;
    END;

    THROW;
END CATCH;
