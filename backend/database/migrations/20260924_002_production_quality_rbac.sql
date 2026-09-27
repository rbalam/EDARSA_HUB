/*
EDARSAHUB
Production Quality / Foto Finish
Gate5D2 - RBAC canonical materialization.

Repository artifact only at Gate5D2.
Execution belongs to a later controlled Development gate.

Rules:
- Reuse canonical Usuario_* RBAC.
- No new roles.
- No new actions.
- No role IDs.
- No action IDs.
- No parallel RBAC.
- Hidden authorization taxonomy.
- Navigation remains under Operacion / Produccion.
*/

SET NOCOUNT ON;
SET XACT_ABORT ON;

IF DB_NAME() <> N'EDARSAHUB'
BEGIN
    THROW 51000,
        'Production Quality RBAC solo puede ejecutarse en EDARSAHUB.',
        1;
END;

BEGIN TRY
    BEGIN TRANSACTION;

    DECLARE @LockResult INT;

    EXEC @LockResult = sys.sp_getapplock
        @Resource = N'EDARSAHUB:PRODUCTION_QUALITY:RBAC',
        @LockMode = N'Exclusive',
        @LockOwner = N'Transaction',
        @LockTimeout = 15000;

    IF @LockResult < 0
        THROW 51001,
            'No fue posible adquirir el lock de Production Quality RBAC.',
            1;

    /* Canonical RBAC physical contract */

    IF OBJECT_ID(N'dbo.Usuario_Modulos', N'U') IS NULL
        THROW 51002, 'Usuario_Modulos no existe.', 1;

    IF OBJECT_ID(N'dbo.Usuario_Acciones', N'U') IS NULL
        THROW 51003, 'Usuario_Acciones no existe.', 1;

    IF OBJECT_ID(N'dbo.Usuario_Roles', N'U') IS NULL
        THROW 51004, 'Usuario_Roles no existe.', 1;

    IF OBJECT_ID(N'dbo.Usuario_PermisosRolModulo', N'U') IS NULL
        THROW 51005, 'Usuario_PermisosRolModulo no existe.', 1;

    /*
      Reuse canonical actions.
      Gate5D2 does NOT create actions.
    */

    DECLARE @RequiredActions TABLE (
        CodigoAccion VARCHAR(100) NOT NULL PRIMARY KEY
    );

    INSERT INTO @RequiredActions (CodigoAccion)
    VALUES
        ('VER'),
        ('CREAR'),
        ('GESTIONAR'),
        ('AUTORIZAR'),
        ('CONFIGURAR');

    IF EXISTS (
        SELECT 1
        FROM @RequiredActions req
        LEFT JOIN dbo.Usuario_Acciones a
            ON UPPER(a.CodigoAccion) = UPPER(req.CodigoAccion)
           AND ISNULL(a.Activo, 1) = 1
        WHERE a.AccionID IS NULL
    )
        THROW 51006,
            'Falta una accion RBAC canonica requerida.',
            1;

    /*
      Source-policy modules.
      We inherit grants instead of hardcoding roles.
    */

    IF NOT EXISTS (
        SELECT 1
        FROM dbo.Usuario_Modulos
        WHERE LOWER(CodigoModulo) = 'tablajeria'
          AND ISNULL(Activo, 1) = 1
    )
        THROW 51007,
            'Modulo fuente tablajeria no existe o no esta activo.',
            1;

    IF NOT EXISTS (
        SELECT 1
        FROM dbo.Usuario_Modulos
        WHERE LOWER(CodigoModulo) = 'tablajeria.config'
          AND ISNULL(Activo, 1) = 1
    )
        THROW 51008,
            'Modulo fuente tablajeria.config no existe o no esta activo.',
            1;

    IF NOT EXISTS (
        SELECT 1
        FROM dbo.Usuario_Modulos
        WHERE LOWER(CodigoModulo) = 'auth'
          AND ISNULL(Activo, 1) = 1
    )
        THROW 51009,
            'Modulo fuente auth no existe o no esta activo.',
            1;

    /*
      Authorization taxonomy.
      These modules are RBAC resources, not menu roots.
    */

    DECLARE @Modules TABLE (
        CodigoModulo VARCHAR(120) NOT NULL PRIMARY KEY,
        CodigoPadre VARCHAR(120) NULL,
        NombreModulo NVARCHAR(200) NOT NULL,
        Descripcion NVARCHAR(500) NOT NULL,
        OrdenMenu INT NOT NULL
    );

    INSERT INTO @Modules (
        CodigoModulo,
        CodigoPadre,
        NombreModulo,
        Descripcion,
        OrdenMenu
    )
    VALUES
        (
            'production_quality',
            NULL,
            N'Production Quality',
            N'PQ_RBAC_GATE5D2: raiz RBAC canonica Production Quality.',
            1
        ),
        (
            'production_quality.execution',
            'production_quality',
            N'Ejecucion Production Quality',
            N'PQ_RBAC_GATE5D2: ejecucion operativa.',
            2
        ),
        (
            'production_quality.standards',
            'production_quality',
            N'Estandares de Calidad',
            N'PQ_RBAC_GATE5D2: estandares y versiones.',
            3
        ),
        (
            'production_quality.evidence',
            'production_quality',
            N'Evidencias de Calidad',
            N'PQ_RBAC_GATE5D2: evidencias y Foto Finish.',
            4
        ),
        (
            'production_quality.decisions',
            'production_quality',
            N'Decisiones de Calidad',
            N'PQ_RBAC_GATE5D2: decisiones PASS WARNING FAIL.',
            5
        ),
        (
            'production_quality.rework',
            'production_quality',
            N'Retrabajo de Calidad',
            N'PQ_RBAC_GATE5D2: flujo de retrabajo.',
            6
        ),
        (
            'production_quality.override',
            'production_quality',
            N'Override de Calidad',
            N'PQ_RBAC_GATE5D2: autorizacion excepcional auditable.',
            7
        ),
        (
            'production_quality.devices',
            'production_quality',
            N'Dispositivos de Calidad',
            N'PQ_RBAC_GATE5D2: camaras basculas termometros y calibracion.',
            8
        );

    /*
      Root module.
    */

    IF NOT EXISTS (
        SELECT 1
        FROM dbo.Usuario_Modulos
        WHERE LOWER(CodigoModulo) = 'production_quality'
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
            FechaAlta,
            FechaModificacion
        )
        VALUES (
            NULL,
            'production_quality',
            N'Production Quality',
            N'PQ_RBAC_GATE5D2: raiz RBAC canonica Production Quality.',
            'MODULO',
            NULL,
            NULL,
            1,
            0,
            1,
            1,
            SYSUTCDATETIME(),
            NULL
        );
    END;

    DECLARE @RootID INT;

    SELECT @RootID = ModuloID
    FROM dbo.Usuario_Modulos
    WHERE LOWER(CodigoModulo) = 'production_quality';

    IF @RootID IS NULL
        THROW 51010,
            'No fue posible resolver production_quality.',
            1;

    IF EXISTS (
        SELECT 1
        FROM dbo.Usuario_Modulos
        WHERE ModuloID = @RootID
          AND (
                ISNULL(Activo, 1) <> 1
             OR ISNULL(EsVisibleMenu, 0) <> 0
          )
    )
        THROW 51011,
            'Collision: production_quality incompatible.',
            1;

    /*
      Child RBAC resources.
    */

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
        FechaAlta,
        FechaModificacion
    )
    SELECT
        @RootID,
        source.CodigoModulo,
        source.NombreModulo,
        source.Descripcion,
        'SUBMODULO',
        NULL,
        NULL,
        source.OrdenMenu,
        0,
        1,
        1,
        SYSUTCDATETIME(),
        NULL
    FROM @Modules source
    WHERE source.CodigoPadre = 'production_quality'
      AND NOT EXISTS (
          SELECT 1
          FROM dbo.Usuario_Modulos existing_module
          WHERE LOWER(existing_module.CodigoModulo) =
                LOWER(source.CodigoModulo)
      );

    IF EXISTS (
        SELECT 1
        FROM @Modules expected
        JOIN dbo.Usuario_Modulos actual
          ON LOWER(actual.CodigoModulo) =
             LOWER(expected.CodigoModulo)
        WHERE expected.CodigoPadre = 'production_quality'
          AND (
                ISNULL(actual.Activo, 1) <> 1
             OR actual.ModuloPadreID <> @RootID
             OR ISNULL(actual.EsVisibleMenu, 0) <> 0
          )
    )
        THROW 51012,
            'Collision: submodulo Production Quality incompatible.',
            1;

    /*
      Permission inheritance policy.

      No CodigoRol and no RolID are hardcoded.
      The source permissions determine who receives
      the new target permission.
    */

    DECLARE @Policy TABLE (
        TargetModule VARCHAR(120) NOT NULL,
        TargetAction VARCHAR(100) NOT NULL,
        SourceModule VARCHAR(120) NOT NULL,
        SourceAction VARCHAR(100) NOT NULL,
        RequiresAuthorization BIT NOT NULL,
        PRIMARY KEY (TargetModule, TargetAction)
    );

    INSERT INTO @Policy (
        TargetModule,
        TargetAction,
        SourceModule,
        SourceAction,
        RequiresAuthorization
    )
    VALUES
        ('production_quality',
         'VER',
         'tablajeria',
         'VER',
         0),

        ('production_quality.execution',
         'VER',
         'tablajeria',
         'VER',
         0),

        ('production_quality.execution',
         'GESTIONAR',
         'tablajeria',
         'CREAR',
         0),

        ('production_quality.standards',
         'VER',
         'tablajeria',
         'VER',
         0),

        ('production_quality.standards',
         'CONFIGURAR',
         'tablajeria.config',
         'CONFIGURAR',
         0),

        ('production_quality.evidence',
         'VER',
         'tablajeria',
         'VER',
         0),

        ('production_quality.evidence',
         'CREAR',
         'tablajeria',
         'CREAR',
         0),

        ('production_quality.decisions',
         'VER',
         'tablajeria',
         'VER',
         0),

        ('production_quality.decisions',
         'AUTORIZAR',
         'tablajeria',
         'AUTORIZAR',
         1),

        ('production_quality.rework',
         'VER',
         'tablajeria',
         'VER',
         0),

        ('production_quality.rework',
         'GESTIONAR',
         'tablajeria',
         'AUTORIZAR',
         1),

        ('production_quality.override',
         'VER',
         'tablajeria',
         'VER',
         0),

        ('production_quality.override',
         'AUTORIZAR',
         'auth',
         'ADMIN',
         1),

        ('production_quality.devices',
         'VER',
         'tablajeria.config',
         'VER',
         0),

        ('production_quality.devices',
         'CONFIGURAR',
         'tablajeria.config',
         'CONFIGURAR',
         1);

    /*
      Every source policy entry must have real coverage.
    */

    IF EXISTS (
        SELECT 1
        FROM @Policy p
        WHERE NOT EXISTS (
            SELECT 1
            FROM dbo.Usuario_PermisosRolModulo source_perm
            JOIN dbo.Usuario_Modulos source_module
              ON source_module.ModuloID = source_perm.ModuloID
            JOIN dbo.Usuario_Acciones source_action
              ON source_action.AccionID = source_perm.AccionID
            JOIN dbo.Usuario_Roles source_role
              ON source_role.RolID = source_perm.RolID
            WHERE LOWER(source_module.CodigoModulo) =
                  LOWER(p.SourceModule)
              AND UPPER(source_action.CodigoAccion) =
                  UPPER(p.SourceAction)
              AND ISNULL(source_perm.Activo, 1) = 1
              AND ISNULL(source_perm.Permitido, 0) = 1
              AND ISNULL(source_module.Activo, 1) = 1
              AND ISNULL(source_action.Activo, 1) = 1
              AND ISNULL(source_role.Activo, 1) = 1
        )
    )
        THROW 51013,
            'La politica fuente no tiene cobertura activa suficiente.',
            1;

    /*
      Materialize inherited grants.
      Existing explicit records are not overwritten.
    */

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
        FechaModificacion,
        CreatedBy,
        ModifiedBy
    )
    SELECT DISTINCT
        source_perm.RolID,
        target_module.ModuloID,
        target_action.AccionID,
        1,
        source_perm.RestriccionPropietario,
        source_perm.RestriccionSucursal,
        p.RequiresAuthorization,
        CASE
            WHEN p.RequiresAuthorization = 1
            THEN COALESCE(
                source_perm.NivelAutorizacionRequerido,
                source_role.NivelJerarquia
            )
            ELSE NULL
        END,
        1,
        SYSUTCDATETIME(),
        NULL,
        'PQ_RBAC_GATE5D2',
        NULL
    FROM @Policy p
    JOIN dbo.Usuario_Modulos source_module
      ON LOWER(source_module.CodigoModulo) =
         LOWER(p.SourceModule)
    JOIN dbo.Usuario_Acciones source_action
      ON UPPER(source_action.CodigoAccion) =
         UPPER(p.SourceAction)
    JOIN dbo.Usuario_PermisosRolModulo source_perm
      ON source_perm.ModuloID = source_module.ModuloID
     AND source_perm.AccionID = source_action.AccionID
    JOIN dbo.Usuario_Roles source_role
      ON source_role.RolID = source_perm.RolID
    JOIN dbo.Usuario_Modulos target_module
      ON LOWER(target_module.CodigoModulo) =
         LOWER(p.TargetModule)
    JOIN dbo.Usuario_Acciones target_action
      ON UPPER(target_action.CodigoAccion) =
         UPPER(p.TargetAction)
    WHERE ISNULL(source_perm.Activo, 1) = 1
      AND ISNULL(source_perm.Permitido, 0) = 1
      AND ISNULL(source_module.Activo, 1) = 1
      AND ISNULL(source_action.Activo, 1) = 1
      AND ISNULL(source_role.Activo, 1) = 1
      AND ISNULL(target_module.Activo, 1) = 1
      AND ISNULL(target_action.Activo, 1) = 1
      AND NOT EXISTS (
          SELECT 1
          FROM dbo.Usuario_PermisosRolModulo existing_perm
          WHERE existing_perm.RolID = source_perm.RolID
            AND existing_perm.ModuloID = target_module.ModuloID
            AND existing_perm.AccionID = target_action.AccionID
      );

    /*
      Existing explicit denies/inactive records are not
      silently reactivated. Fail closed.
    */

    IF EXISTS (
        SELECT 1
        FROM @Policy p
        JOIN dbo.Usuario_Modulos target_module
          ON LOWER(target_module.CodigoModulo) =
             LOWER(p.TargetModule)
        JOIN dbo.Usuario_Acciones target_action
          ON UPPER(target_action.CodigoAccion) =
             UPPER(p.TargetAction)
        JOIN dbo.Usuario_PermisosRolModulo target_perm
          ON target_perm.ModuloID = target_module.ModuloID
         AND target_perm.AccionID = target_action.AccionID
        WHERE (
              ISNULL(target_perm.Activo, 1) = 0
           OR ISNULL(target_perm.Permitido, 0) = 0
        )
    )
        THROW 51014,
            'Existe permiso Production Quality denegado/inactivo.',
            1;

    COMMIT TRANSACTION;
END TRY
BEGIN CATCH
    IF @@TRANCOUNT > 0
        ROLLBACK TRANSACTION;

    THROW;
END CATCH;
