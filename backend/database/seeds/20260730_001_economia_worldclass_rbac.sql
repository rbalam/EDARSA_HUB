/*
EDARSAHUB V1.0
Economia WorldClass - RBAC canonico.

REGLAS:
- No IDs hardcodeados.
- No bypass por ADMIN/SUPERADMIN.
- Permisos resueltos por codigo.
- Roles existentes se reutilizan.
- Idempotente.
*/

SET NOCOUNT ON;
SET XACT_ABORT ON;

BEGIN TRY
    BEGIN TRANSACTION;

    DECLARE @Permisos TABLE
    (
        codigo      nvarchar(300) NOT NULL,
        nombre      nvarchar(400) NOT NULL,
        modulo      nvarchar(200) NOT NULL,
        descripcion nvarchar(1000) NULL
    );

    INSERT INTO @Permisos
    (
        codigo,
        nombre,
        modulo,
        descripcion
    )
    VALUES
    (
        N'economia.indicadores.leer',
        N'Consultar indicadores económicos',
        N'ECONOMIA',
        N'Permite consultar indicadores y valores económicos.'
    ),
    (
        N'economia.series.leer',
        N'Consultar series económicas',
        N'ECONOMIA',
        N'Permite consultar definición y metadatos de series económicas.'
    ),
    (
        N'economia.series.administrar',
        N'Administrar series económicas',
        N'ECONOMIA',
        N'Permite crear, editar, activar o desactivar series económicas.'
    ),
    (
        N'economia.proveedores.administrar',
        N'Administrar proveedores económicos',
        N'ECONOMIA',
        N'Permite administrar proveedores y fuentes de información económica.'
    ),
    (
        N'economia.sincronizacion.ejecutar',
        N'Ejecutar sincronización económica',
        N'ECONOMIA',
        N'Permite ejecutar sincronizaciones de series económicas.'
    ),
    (
        N'economia.backfill.ejecutar',
        N'Ejecutar backfill económico',
        N'ECONOMIA',
        N'Permite recuperar histórico de series económicas.'
    ),
    (
        N'economia.contexto.administrar',
        N'Administrar contexto económico',
        N'ECONOMIA',
        N'Permite configurar país y moneda aplicables a empresa o unidad.'
    ),
    (
        N'economia.exportar',
        N'Exportar información económica',
        N'ECONOMIA',
        N'Permite exportar series e indicadores económicos.'
    ),
    (
        N'economia.configuracion.administrar',
        N'Administrar configuración económica',
        N'ECONOMIA',
        N'Permite administrar configuración general del módulo Economía.'
    );

    INSERT INTO dbo.Sistema_RBAC_Permisos
    (
        permiso_id,
        codigo,
        nombre,
        modulo,
        descripcion,
        activo,
        fecha_alta,
        fecha_ultima_actualizacion
    )
    SELECT
        NEWID(),
        p.codigo,
        p.nombre,
        p.modulo,
        p.descripcion,
        1,
        SYSDATETIME(),
        SYSDATETIME()
    FROM @Permisos p
    WHERE NOT EXISTS
    (
        SELECT 1
        FROM dbo.Sistema_RBAC_Permisos existing
        WHERE existing.codigo = p.codigo
    );

    UPDATE existing
    SET
        existing.nombre = p.nombre,
        existing.modulo = p.modulo,
        existing.descripcion = p.descripcion,
        existing.activo = 1,
        existing.fecha_ultima_actualizacion = SYSDATETIME()
    FROM dbo.Sistema_RBAC_Permisos existing
    INNER JOIN @Permisos p
        ON p.codigo = existing.codigo;

    /*
    Asignación a roles:
    únicamente a roles canónicos ya existentes.

    SUPERADMIN debe mantener al menos las capacidades efectivas
    del rol administrador cuando dichos roles existan.
    La resolución es por codigo y jamás por GUID fijo.
    */

    DECLARE @RolePermissionMap TABLE
    (
        rol_codigo      nvarchar(200) NOT NULL,
        permiso_codigo  nvarchar(300) NOT NULL
    );

    INSERT INTO @RolePermissionMap
    (
        rol_codigo,
        permiso_codigo
    )
    VALUES

    /* SUPERADMIN: acceso total Economia */
    (N'SUPERADMIN', N'economia.indicadores.leer'),
    (N'SUPERADMIN', N'economia.series.leer'),
    (N'SUPERADMIN', N'economia.series.administrar'),
    (N'SUPERADMIN', N'economia.proveedores.administrar'),
    (N'SUPERADMIN', N'economia.sincronizacion.ejecutar'),
    (N'SUPERADMIN', N'economia.backfill.ejecutar'),
    (N'SUPERADMIN', N'economia.contexto.administrar'),
    (N'SUPERADMIN', N'economia.exportar'),
    (N'SUPERADMIN', N'economia.configuracion.administrar'),

    /* ADMIN_COMERCIAL: acceso total Economia */
    (N'ADMIN_COMERCIAL', N'economia.indicadores.leer'),
    (N'ADMIN_COMERCIAL', N'economia.series.leer'),
    (N'ADMIN_COMERCIAL', N'economia.series.administrar'),
    (N'ADMIN_COMERCIAL', N'economia.proveedores.administrar'),
    (N'ADMIN_COMERCIAL', N'economia.sincronizacion.ejecutar'),
    (N'ADMIN_COMERCIAL', N'economia.backfill.ejecutar'),
    (N'ADMIN_COMERCIAL', N'economia.contexto.administrar'),
    (N'ADMIN_COMERCIAL', N'economia.exportar'),
    (N'ADMIN_COMERCIAL', N'economia.configuracion.administrar'),

    /* CONFIGURADOR_COMERCIAL */
    (N'CONFIGURADOR_COMERCIAL', N'economia.indicadores.leer'),
    (N'CONFIGURADOR_COMERCIAL', N'economia.series.leer'),
    (N'CONFIGURADOR_COMERCIAL', N'economia.series.administrar'),
    (N'CONFIGURADOR_COMERCIAL', N'economia.proveedores.administrar'),
    (N'CONFIGURADOR_COMERCIAL', N'economia.sincronizacion.ejecutar'),
    (N'CONFIGURADOR_COMERCIAL', N'economia.backfill.ejecutar'),
    (N'CONFIGURADOR_COMERCIAL', N'economia.contexto.administrar'),
    (N'CONFIGURADOR_COMERCIAL', N'economia.configuracion.administrar'),

    /* ANALISTA_COMERCIAL */
    (N'ANALISTA_COMERCIAL', N'economia.indicadores.leer'),
    (N'ANALISTA_COMERCIAL', N'economia.series.leer'),
    (N'ANALISTA_COMERCIAL', N'economia.exportar'),

    /* GERENTE_UNIDAD */
    (N'GERENTE_UNIDAD', N'economia.indicadores.leer'),
    (N'GERENTE_UNIDAD', N'economia.series.leer'),
    (N'GERENTE_UNIDAD', N'economia.exportar'),

    /* VISOR_COMERCIAL */
    (N'VISOR_COMERCIAL', N'economia.indicadores.leer'),
    (N'VISOR_COMERCIAL', N'economia.series.leer');

    INSERT INTO dbo.Sistema_RBAC_RolesPermisos
    (
        rol_permiso_id,
        rol_id,
        permiso_id,
        activo,
        fecha_alta
    )
    SELECT
        NEWID(),
        r.rol_id,
        p.permiso_id,
        1,
        SYSDATETIME()
    FROM @RolePermissionMap m
    INNER JOIN dbo.Sistema_RBAC_Roles r
        ON r.codigo = m.rol_codigo
       AND r.activo = 1
    INNER JOIN dbo.Sistema_RBAC_Permisos p
        ON p.codigo = m.permiso_codigo
       AND p.activo = 1
    WHERE NOT EXISTS
    (
        SELECT 1
        FROM dbo.Sistema_RBAC_RolesPermisos rp
        WHERE rp.rol_id = r.rol_id
          AND rp.permiso_id = p.permiso_id
    );

    UPDATE rp
    SET rp.activo = 1
    FROM dbo.Sistema_RBAC_RolesPermisos rp
    INNER JOIN dbo.Sistema_RBAC_Roles r
        ON r.rol_id = rp.rol_id
    INNER JOIN dbo.Sistema_RBAC_Permisos p
        ON p.permiso_id = rp.permiso_id
    INNER JOIN @RolePermissionMap m
        ON m.rol_codigo = r.codigo
       AND m.permiso_codigo = p.codigo;

    COMMIT TRANSACTION;
END TRY
BEGIN CATCH
    IF @@TRANCOUNT > 0
        ROLLBACK TRANSACTION;

    THROW;
END CATCH;
