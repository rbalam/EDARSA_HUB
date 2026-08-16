/*
EDARSAHUB
RBAC explicito para CRUD del modulo Servidores.

Objetivo:
- conservar SERVIDORES_VER existente;
- conceder CREAR, EDITAR y ELIMINAR exclusivamente mediante
  Usuario_PermisosRolModulo;
- preservar el comportamiento funcional actual de los roles
  ADMIN y SUPERADMIN;
- preparar la eliminacion posterior del bypass por nombre de rol
  existente en backend/server.py.

Reglas:
- SQL canónico;
- no MongoDB;
- no hardcodes de IDs;
- resolución por códigos canónicos;
- idempotente;
- fail-closed;
- no modifica permisos ajenos al modulo servidores.
*/

SET NOCOUNT ON;
SET XACT_ABORT ON;

BEGIN TRY
    BEGIN TRANSACTION;

    DECLARE @ModuloID INT;

    SELECT @ModuloID = ModuloID
    FROM dbo.Usuario_Modulos
    WHERE LOWER(CodigoModulo) = 'servidores'
      AND Activo = 1;

    IF @ModuloID IS NULL
        THROW 51000,
            'RBAC servidores abort: modulo servidores activo no encontrado.',
            1;

    IF (
        SELECT COUNT(*)
        FROM dbo.Usuario_Modulos
        WHERE LOWER(CodigoModulo) = 'servidores'
          AND Activo = 1
    ) <> 1
        THROW 51001,
            'RBAC servidores abort: cardinalidad inesperada del modulo servidores.',
            1;

    DECLARE @Roles TABLE (
        RolID INT NOT NULL PRIMARY KEY,
        CodigoRol NVARCHAR(255) NOT NULL
    );

    INSERT INTO @Roles (
        RolID,
        CodigoRol
    )
    SELECT
        RolID,
        CodigoRol
    FROM dbo.Usuario_Roles
    WHERE UPPER(CodigoRol) IN (
        'ADMIN',
        'SUPERADMIN'
    )
      AND Activo = 1;

    IF (
        SELECT COUNT(*)
        FROM @Roles
    ) <> 2
        THROW 51002,
            'RBAC servidores abort: ADMIN/SUPERADMIN activos no resueltos exactamente.',
            1;

    DECLARE @Acciones TABLE (
        AccionID INT NOT NULL PRIMARY KEY,
        CodigoAccion NVARCHAR(255) NOT NULL
    );

    INSERT INTO @Acciones (
        AccionID,
        CodigoAccion
    )
    SELECT
        AccionID,
        CodigoAccion
    FROM dbo.Usuario_Acciones
    WHERE UPPER(CodigoAccion) IN (
        'CREAR',
        'EDITAR',
        'ELIMINAR'
    )
      AND Activo = 1;

    IF (
        SELECT COUNT(*)
        FROM @Acciones
    ) <> 3
        THROW 51003,
            'RBAC servidores abort: acciones CRUD activas incompletas.',
            1;

    /*
    Deben existir exactamente 6 combinaciones objetivo:
      ADMIN       x CREAR/EDITAR/ELIMINAR
      SUPERADMIN  x CREAR/EDITAR/ELIMINAR
    */

    DECLARE @Objetivo TABLE (
        RolID INT NOT NULL,
        ModuloID INT NOT NULL,
        AccionID INT NOT NULL,
        PRIMARY KEY (
            RolID,
            ModuloID,
            AccionID
        )
    );

    INSERT INTO @Objetivo (
        RolID,
        ModuloID,
        AccionID
    )
    SELECT
        r.RolID,
        @ModuloID,
        a.AccionID
    FROM @Roles r
    CROSS JOIN @Acciones a;

    IF (
        SELECT COUNT(*)
        FROM @Objetivo
    ) <> 6
        THROW 51004,
            'RBAC servidores abort: matriz objetivo distinta de 6.',
            1;

    /*
    Si existe una fila previa para alguna combinación objetivo,
    no asumimos que pueda sobrescribirse silenciosamente.

    Solo aceptamos:
    - ausencia de fila; o
    - fila ya activa y permitida.

    Cualquier fila existente denegada/inactiva requiere auditoría
    específica y aborta esta migración.
    */

    IF EXISTS (
        SELECT 1
        FROM @Objetivo o
        INNER JOIN dbo.Usuario_PermisosRolModulo p
            ON p.RolID = o.RolID
           AND p.ModuloID = o.ModuloID
           AND p.AccionID = o.AccionID
        WHERE ISNULL(p.Permitido, 0) <> 1
           OR ISNULL(p.Activo, 0) <> 1
    )
        THROW 51005,
            'RBAC servidores abort: existe permiso CRUD previo denegado/inactivo; requiere auditoria.',
            1;

    /*
    No crear duplicados si la combinación ya existe activa.
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
        Activo
    )
    SELECT
        o.RolID,
        o.ModuloID,
        o.AccionID,
        1,
        0,
        0,
        0,
        NULL,
        1
    FROM @Objetivo o
    WHERE NOT EXISTS (
        SELECT 1
        FROM dbo.Usuario_PermisosRolModulo p
        WHERE p.RolID = o.RolID
          AND p.ModuloID = o.ModuloID
          AND p.AccionID = o.AccionID
    );

    /*
    Postcondición exacta.
    */

    IF (
        SELECT COUNT(*)
        FROM @Objetivo o
        INNER JOIN dbo.Usuario_PermisosRolModulo p
            ON p.RolID = o.RolID
           AND p.ModuloID = o.ModuloID
           AND p.AccionID = o.AccionID
        WHERE p.Permitido = 1
          AND p.Activo = 1
    ) <> 6
        THROW 51006,
            'RBAC servidores abort: postcondicion CRUD incompleta.',
            1;

    /*
    SERVIDORES_VER no debe ser modificado por esta migración.
    Solo verificamos que continúe disponible para los dos roles.
    */

    DECLARE @VerAccionID INT;

    SELECT @VerAccionID = AccionID
    FROM dbo.Usuario_Acciones
    WHERE UPPER(CodigoAccion) = 'VER'
      AND Activo = 1;

    IF @VerAccionID IS NULL
        THROW 51007,
            'RBAC servidores abort: accion VER no encontrada.',
            1;

    IF (
        SELECT COUNT(*)
        FROM @Roles r
        INNER JOIN dbo.Usuario_PermisosRolModulo p
            ON p.RolID = r.RolID
           AND p.ModuloID = @ModuloID
           AND p.AccionID = @VerAccionID
        WHERE p.Permitido = 1
          AND p.Activo = 1
    ) <> 2
        THROW 51008,
            'RBAC servidores abort: SERVIDORES_VER no esta activo para ambos roles.',
            1;

    SELECT
        r.CodigoRol,
        a.CodigoAccion,
        p.Permitido,
        p.RestriccionPropietario,
        p.RestriccionSucursal,
        p.RequiereAutorizacion,
        p.NivelAutorizacionRequerido,
        p.Activo
    FROM dbo.Usuario_PermisosRolModulo p
    INNER JOIN dbo.Usuario_Roles r
        ON r.RolID = p.RolID
    INNER JOIN dbo.Usuario_Acciones a
        ON a.AccionID = p.AccionID
    WHERE p.ModuloID = @ModuloID
      AND UPPER(r.CodigoRol) IN (
          'ADMIN',
          'SUPERADMIN'
      )
      AND UPPER(a.CodigoAccion) IN (
          'VER',
          'CREAR',
          'EDITAR',
          'ELIMINAR'
      )
    ORDER BY
        r.CodigoRol,
        a.CodigoAccion;

    COMMIT TRANSACTION;

END TRY
BEGIN CATCH

    IF @@TRANCOUNT > 0
        ROLLBACK TRANSACTION;

    THROW;

END CATCH;
