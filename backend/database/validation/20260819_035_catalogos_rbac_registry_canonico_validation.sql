SET NOCOUNT ON;

DECLARE @PhysicalTarget INT = 52;

DECLARE @PhysicalRegistered INT = (
    SELECT COUNT(DISTINCT UPPER(LTRIM(RTRIM(CodigoCatalogo))))
    FROM dbo.Sistema_CatalogosConfig
    WHERE Activo = 1
      AND UPPER(LTRIM(RTRIM(TipoConfiguracion))) = N'CATALOGO_FISICO'
);

DECLARE @WorkflowPreserved INT = (
    SELECT COUNT(DISTINCT UPPER(LTRIM(RTRIM(CodigoCatalogo))))
    FROM dbo.Sistema_CatalogosConfig
    WHERE Activo = 1
      AND UPPER(LTRIM(RTRIM(TipoConfiguracion))) = N'CATALOGO_WORKFLOW'
      AND UPPER(LTRIM(RTRIM(CodigoCatalogo))) IN (
          N'CLIENTES',
          N'COMPETIDORES',
          N'CONSULTAS_SQL',
          N'EMPLEADOS',
          N'IMPUESTOS',
          N'PRODUCTOS',
          N'PROVEEDORES',
          N'SISTEMAS'
      )
);

DECLARE @DuplicatePhysical INT = (
    SELECT COUNT(*)
    FROM (
        SELECT UPPER(LTRIM(RTRIM(CodigoCatalogo))) AS Codigo
        FROM dbo.Sistema_CatalogosConfig
        WHERE UPPER(LTRIM(RTRIM(TipoConfiguracion))) = N'CATALOGO_FISICO'
        GROUP BY UPPER(LTRIM(RTRIM(CodigoCatalogo)))
        HAVING COUNT(*) > 1
    ) d
);

DECLARE @NonexistentPhysical INT = (
    SELECT COUNT(*)
    FROM dbo.Sistema_CatalogosConfig c
    WHERE c.Activo = 1
      AND UPPER(LTRIM(RTRIM(c.TipoConfiguracion))) = N'CATALOGO_FISICO'
      AND OBJECT_ID(N'dbo.' + QUOTENAME(c.CodigoCatalogo), N'U') IS NULL
);

DECLARE @BancosRows INT = (
    SELECT COUNT(*)
    FROM dbo.Sistema_CatalogosConfig
    WHERE UPPER(LTRIM(RTRIM(CodigoCatalogo))) = N'GLOBAL_CAT_BANCOS'
      AND UPPER(LTRIM(RTRIM(TipoConfiguracion))) = N'CATALOGO_FISICO'
);

DECLARE @TotalAvailable INT = (
    SELECT COUNT(DISTINCT UPPER(LTRIM(RTRIM(CodigoCatalogo))))
    FROM dbo.Sistema_CatalogosConfig
    WHERE Activo = 1
);

SELECT 'PHYSICAL_DEFINED_TARGET' AS Metric, CAST(@PhysicalTarget AS NVARCHAR(100)) AS Value
UNION ALL
SELECT 'PHYSICAL_REGISTERED_ACTIVE', CAST(@PhysicalRegistered AS NVARCHAR(100))
UNION ALL
SELECT 'PHYSICAL_COVERAGE_PERCENT',
       CAST(CASE WHEN @PhysicalTarget = 0 THEN 0
                 ELSE (@PhysicalRegistered * 100) / @PhysicalTarget END AS NVARCHAR(100))
UNION ALL
SELECT 'WORKFLOW_EXPECTED', '8'
UNION ALL
SELECT 'WORKFLOW_PRESERVED', CAST(@WorkflowPreserved AS NVARCHAR(100))
UNION ALL
SELECT 'DUPLICATE_PHYSICAL_CODES', CAST(@DuplicatePhysical AS NVARCHAR(100))
UNION ALL
SELECT 'NONEXISTENT_TABLES_REGISTERED_AS_PHYSICAL', CAST(@NonexistentPhysical AS NVARCHAR(100))
UNION ALL
SELECT 'GLOBAL_CAT_BANCOS_REGISTRY_ROWS', CAST(@BancosRows AS NVARCHAR(100))
UNION ALL
SELECT 'CATALOG_PERMISSION_TABLE_EXISTS',
       CASE WHEN OBJECT_ID(N'dbo.Sistema_CatalogosPermisos', N'U') IS NOT NULL THEN 'YES' ELSE 'NO' END
UNION ALL
SELECT 'TARGET_TOTAL_AVAILABLE_UNIQUE', CAST(@TotalAvailable AS NVARCHAR(100))
UNION ALL
SELECT 'CATALOG_RBAC_REGISTRY_VALID',
       CASE
         WHEN @PhysicalRegistered = 52
          AND @WorkflowPreserved = 8
          AND @DuplicatePhysical = 0
          AND @NonexistentPhysical = 0
          AND @BancosRows = 1
          AND OBJECT_ID(N'dbo.Sistema_CatalogosPermisos', N'U') IS NOT NULL
         THEN 'YES'
         ELSE 'NO'
       END;
