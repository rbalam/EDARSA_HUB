SET NOCOUNT ON;

DECLARE @Errors int = 0;

DECLARE @Expected TABLE
(
    codigo nvarchar(300) NOT NULL
);

INSERT INTO @Expected(codigo)
VALUES
(N'economia.indicadores.leer'),
(N'economia.series.leer'),
(N'economia.series.administrar'),
(N'economia.proveedores.administrar'),
(N'economia.sincronizacion.ejecutar'),
(N'economia.backfill.ejecutar'),
(N'economia.contexto.administrar'),
(N'economia.exportar'),
(N'economia.configuracion.administrar');

SELECT
    e.codigo,
    CASE
        WHEN p.permiso_id IS NOT NULL
         AND p.modulo = N'ECONOMIA'
         AND p.activo = 1
        THEN 'PASS'
        ELSE 'FAIL'
    END AS Estado
FROM @Expected e
LEFT JOIN dbo.Sistema_RBAC_Permisos p
    ON p.codigo = e.codigo;

SELECT
    @Errors = @Errors + COUNT(*)
FROM @Expected e
LEFT JOIN dbo.Sistema_RBAC_Permisos p
    ON p.codigo = e.codigo
WHERE p.permiso_id IS NULL
   OR p.modulo <> N'ECONOMIA'
   OR p.activo <> 1;

IF EXISTS
(
    SELECT
        codigo
    FROM dbo.Sistema_RBAC_Permisos
    WHERE modulo = N'ECONOMIA'
    GROUP BY codigo
    HAVING COUNT(*) > 1
)
BEGIN
    SET @Errors += 1;
END;

SELECT
    r.codigo AS Rol,
    COUNT(DISTINCT p.permiso_id) AS PermisosEconomia
FROM dbo.Sistema_RBAC_Roles r
LEFT JOIN dbo.Sistema_RBAC_RolesPermisos rp
    ON rp.rol_id = r.rol_id
   AND rp.activo = 1
LEFT JOIN dbo.Sistema_RBAC_Permisos p
    ON p.permiso_id = rp.permiso_id
   AND p.modulo = N'ECONOMIA'
   AND p.activo = 1
WHERE r.codigo IN
(
    N'SUPERADMIN',
    N'ADMINISTRADOR'
)
GROUP BY r.codigo;

SELECT
    @Errors AS ValidationErrors,
    CASE
        WHEN @Errors = 0
        THEN 'PASS'
        ELSE 'FAIL'
    END AS Resultado;

IF @Errors <> 0
    THROW 51000, 'ECONOMIA_RBAC_VALIDATION_FAILED', 1;
