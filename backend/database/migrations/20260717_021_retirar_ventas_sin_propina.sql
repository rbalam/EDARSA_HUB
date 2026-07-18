/*
EDARSAHUB V1.0
Retiro físico de ventas_sin_propina.

PRECONDICIÓN: ejecutar y validar primero 20260717_020.
Este archivo se prepara para el runner autorizado; no se ejecuta automáticamente.
*/

SET NOCOUNT ON;
SET XACT_ABORT ON;

IF DB_NAME() <> N'EDARSAHUB'
BEGIN
    THROW 51200, 'Base no autorizada. Se esperaba EDARSAHUB.', 1;
END;

THROW 51210,
    'Migración 021 diferida: requiere inventario completo y ventana DDL autorizada.',
    1;

/* BLOQUE DIFERIDO: referencia de diseño, no ejecutable.
IF COL_LENGTH(
    N'dbo.Comercial_KPIs_Diarios_v2',
    N'ventas_sin_propina'
) IS NULL
BEGIN
    THROW 51201, 'La columna diaria ya no existe.', 1;
END;

IF COL_LENGTH(
    N'dbo.Comercial_KPIs_Mensuales_v2',
    N'ventas_sin_propina'
) IS NULL
BEGIN
    THROW 51202, 'La columna mensual ya no existe.', 1;
END;

CREATE TABLE #DependentViews (
    object_id int NOT NULL PRIMARY KEY,
    schema_name sysname NOT NULL,
    view_name sysname NOT NULL,
    depth int NOT NULL
);

;WITH ViewGraph AS (
    SELECT
        dependency.referencing_id AS object_id,
        0 AS depth
    FROM sys.sql_expression_dependencies dependency
    INNER JOIN sys.views view_object
      ON view_object.object_id = dependency.referencing_id
    WHERE dependency.referenced_id IN (
        OBJECT_ID(N'dbo.Comercial_KPIs_Diarios_v2'),
        OBJECT_ID(N'dbo.Comercial_KPIs_Mensuales_v2')
    )

    UNION ALL

    SELECT
        dependency.referencing_id,
        graph.depth + 1
    FROM ViewGraph graph
    INNER JOIN sys.sql_expression_dependencies dependency
      ON dependency.referenced_id = graph.object_id
    INNER JOIN sys.views view_object
      ON view_object.object_id = dependency.referencing_id
    WHERE graph.depth < 16
)
INSERT INTO #DependentViews (
    object_id,
    schema_name,
    view_name,
    depth
)
SELECT
    graph.object_id,
    OBJECT_SCHEMA_NAME(graph.object_id),
    OBJECT_NAME(graph.object_id),
    MIN(graph.depth)
FROM ViewGraph graph
GROUP BY graph.object_id
OPTION (MAXRECURSION 32);

IF (SELECT COUNT(*) FROM #DependentViews) <> 5
BEGIN
    THROW 51203,
        'Dependencias inesperadas: se esperaban exactamente cinco vistas.',
        1;
END;

IF EXISTS (
    SELECT 1
    FROM #DependentViews dependency
    WHERE OBJECT_DEFINITION(dependency.object_id) IS NULL
)
BEGIN
    THROW 51204, 'No se pudo leer la definición de una vista.', 1;
END;

BEGIN TRANSACTION;

DECLARE
    @schema_name sysname,
    @view_name sysname,
    @definition nvarchar(max),
    @sql nvarchar(max);

DECLARE view_rewrite CURSOR LOCAL FAST_FORWARD FOR
SELECT
    schema_name,
    view_name,
    OBJECT_DEFINITION(object_id)
FROM #DependentViews
ORDER BY depth, schema_name, view_name;

OPEN view_rewrite;
FETCH NEXT FROM view_rewrite
INTO @schema_name, @view_name, @definition;

WHILE @@FETCH_STATUS = 0
BEGIN
    SET @definition = REPLACE(
        @definition,
        N'ventas_sin_propina',
        N'ventas_total'
    );
    SET @definition = REPLACE(
        @definition,
        N'VENTAS_SIN_PROPINA',
        N'ventas_total'
    );
    SET @definition = REPLACE(
        @definition,
        N'CREATE VIEW',
        N'CREATE OR ALTER VIEW'
    );
    SET @definition = REPLACE(
        @definition,
        N'create view',
        N'CREATE OR ALTER VIEW'
    );

    EXEC sys.sp_executesql @definition;

    FETCH NEXT FROM view_rewrite
    INTO @schema_name, @view_name, @definition;
END;

CLOSE view_rewrite;
DEALLOCATE view_rewrite;

IF EXISTS (
    SELECT 1
    FROM #DependentViews dependency
    WHERE LOWER(OBJECT_DEFINITION(dependency.object_id))
          LIKE N'%ventas_sin_propina%'
)
BEGIN
    THROW 51205, 'Una vista conserva la referencia legacy.', 1;
END;

DECLARE constraint_drop CURSOR LOCAL FAST_FORWARD FOR
SELECT
    N'ALTER TABLE '
    + QUOTENAME(OBJECT_SCHEMA_NAME(column_object.object_id))
    + N'.' + QUOTENAME(OBJECT_NAME(column_object.object_id))
    + N' DROP CONSTRAINT ' + QUOTENAME(default_object.name) + N';'
FROM sys.default_constraints default_object
INNER JOIN sys.columns column_object
  ON column_object.object_id = default_object.parent_object_id
 AND column_object.column_id = default_object.parent_column_id
WHERE column_object.object_id IN (
        OBJECT_ID(N'dbo.Comercial_KPIs_Diarios_v2'),
        OBJECT_ID(N'dbo.Comercial_KPIs_Mensuales_v2')
    )
  AND column_object.name = N'ventas_sin_propina';

OPEN constraint_drop;
FETCH NEXT FROM constraint_drop INTO @sql;

WHILE @@FETCH_STATUS = 0
BEGIN
    EXEC sys.sp_executesql @sql;
    FETCH NEXT FROM constraint_drop INTO @sql;
END;

CLOSE constraint_drop;
DEALLOCATE constraint_drop;

ALTER TABLE dbo.Comercial_KPIs_Diarios_v2
DROP COLUMN ventas_sin_propina;

ALTER TABLE dbo.Comercial_KPIs_Mensuales_v2
DROP COLUMN ventas_sin_propina;

COMMIT TRANSACTION;

SELECT
    schema_name,
    view_name,
    depth
FROM #DependentViews
ORDER BY depth, schema_name, view_name;
*/
