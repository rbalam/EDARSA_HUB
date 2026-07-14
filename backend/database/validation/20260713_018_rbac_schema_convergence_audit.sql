SET NOCOUNT ON;
SET XACT_ABORT ON;

BEGIN TRANSACTION;

SELECT
    DB_NAME() AS database_name,
    SUSER_SNAME() AS login_name,
    USER_NAME() AS database_user,
    @@SERVERNAME AS server_name,
    SYSUTCDATETIME() AS audit_utc;

IF DB_NAME() <> N'EDARSAHUB'
    THROW 51000, 'Base de datos inesperada. Se requiere EDARSAHUB.', 1;

IF SUSER_SNAME() <> N'HRLectura'
    THROW 51001, 'Login inesperado. Se requiere HRLectura.', 1;

IF USER_NAME() <> N'HRLectura'
    THROW 51002, 'Usuario de base inesperado. Se requiere HRLectura.', 1;

/* 1. Catálogo exacto de objetos RBAC, usuarios y menús */
SELECT
    s.name AS schema_name,
    o.name AS object_name,
    o.type,
    o.type_desc,
    o.create_date,
    o.modify_date
FROM sys.objects AS o
INNER JOIN sys.schemas AS s
    ON s.schema_id = o.schema_id
WHERE o.is_ms_shipped = 0
  AND (
        o.name LIKE N'%Usuario%'
     OR o.name LIKE N'%Rol%'
     OR o.name LIKE N'%Permiso%'
     OR o.name LIKE N'%Modulo%'
     OR o.name LIKE N'%Menu%'
     OR o.name LIKE N'%Accion%'
  )
ORDER BY
    o.type_desc,
    s.name,
    o.name;

/* 2. Columnas reales de las tablas candidatas */
SELECT
    s.name AS schema_name,
    t.name AS table_name,
    c.column_id,
    c.name AS column_name,
    ty.name AS data_type,
    c.max_length,
    c.precision,
    c.scale,
    c.is_nullable,
    c.is_identity,
    c.is_computed,
    dc.definition AS default_definition
FROM sys.tables AS t
INNER JOIN sys.schemas AS s
    ON s.schema_id = t.schema_id
INNER JOIN sys.columns AS c
    ON c.object_id = t.object_id
INNER JOIN sys.types AS ty
    ON ty.user_type_id = c.user_type_id
LEFT JOIN sys.default_constraints AS dc
    ON dc.parent_object_id = c.object_id
   AND dc.parent_column_id = c.column_id
WHERE (
        t.name LIKE N'%Usuario%'
     OR t.name LIKE N'%Rol%'
     OR t.name LIKE N'%Permiso%'
     OR t.name LIKE N'%Modulo%'
     OR t.name LIKE N'%Menu%'
     OR t.name LIKE N'%Accion%'
)
ORDER BY
    s.name,
    t.name,
    c.column_id;

/* 3. Claves primarias y restricciones únicas */
SELECT
    s.name AS schema_name,
    t.name AS table_name,
    kc.name AS constraint_name,
    kc.type_desc,
    ic.key_ordinal,
    c.name AS column_name
FROM sys.key_constraints AS kc
INNER JOIN sys.tables AS t
    ON t.object_id = kc.parent_object_id
INNER JOIN sys.schemas AS s
    ON s.schema_id = t.schema_id
INNER JOIN sys.index_columns AS ic
    ON ic.object_id = t.object_id
   AND ic.index_id = kc.unique_index_id
INNER JOIN sys.columns AS c
    ON c.object_id = ic.object_id
   AND c.column_id = ic.column_id
WHERE (
        t.name LIKE N'%Usuario%'
     OR t.name LIKE N'%Rol%'
     OR t.name LIKE N'%Permiso%'
     OR t.name LIKE N'%Modulo%'
     OR t.name LIKE N'%Menu%'
     OR t.name LIKE N'%Accion%'
)
ORDER BY
    s.name,
    t.name,
    kc.name,
    ic.key_ordinal;

/* 4. Foreign keys reales */
SELECT
    fk.name AS foreign_key_name,
    ps.name AS parent_schema,
    pt.name AS parent_table,
    pc.name AS parent_column,
    rs.name AS referenced_schema,
    rt.name AS referenced_table,
    rc.name AS referenced_column,
    fkc.constraint_column_id,
    fk.delete_referential_action_desc,
    fk.update_referential_action_desc,
    fk.is_disabled,
    fk.is_not_trusted
FROM sys.foreign_keys AS fk
INNER JOIN sys.foreign_key_columns AS fkc
    ON fkc.constraint_object_id = fk.object_id
INNER JOIN sys.tables AS pt
    ON pt.object_id = fk.parent_object_id
INNER JOIN sys.schemas AS ps
    ON ps.schema_id = pt.schema_id
INNER JOIN sys.columns AS pc
    ON pc.object_id = fkc.parent_object_id
   AND pc.column_id = fkc.parent_column_id
INNER JOIN sys.tables AS rt
    ON rt.object_id = fk.referenced_object_id
INNER JOIN sys.schemas AS rs
    ON rs.schema_id = rt.schema_id
INNER JOIN sys.columns AS rc
    ON rc.object_id = fkc.referenced_object_id
   AND rc.column_id = fkc.referenced_column_id
WHERE (
        pt.name LIKE N'%Usuario%'
     OR pt.name LIKE N'%Rol%'
     OR pt.name LIKE N'%Permiso%'
     OR pt.name LIKE N'%Modulo%'
     OR pt.name LIKE N'%Menu%'
     OR pt.name LIKE N'%Accion%'
     OR rt.name LIKE N'%Usuario%'
     OR rt.name LIKE N'%Rol%'
     OR rt.name LIKE N'%Permiso%'
     OR rt.name LIKE N'%Modulo%'
     OR rt.name LIKE N'%Menu%'
     OR rt.name LIKE N'%Accion%'
)
ORDER BY
    ps.name,
    pt.name,
    fk.name,
    fkc.constraint_column_id;

/* 5. Índices, incluidos los únicos y filtrados */
SELECT
    s.name AS schema_name,
    t.name AS table_name,
    i.name AS index_name,
    i.type_desc,
    i.is_unique,
    i.is_primary_key,
    i.is_unique_constraint,
    i.has_filter,
    i.filter_definition,
    ic.key_ordinal,
    ic.is_included_column,
    c.name AS column_name
FROM sys.indexes AS i
INNER JOIN sys.tables AS t
    ON t.object_id = i.object_id
INNER JOIN sys.schemas AS s
    ON s.schema_id = t.schema_id
INNER JOIN sys.index_columns AS ic
    ON ic.object_id = i.object_id
   AND ic.index_id = i.index_id
INNER JOIN sys.columns AS c
    ON c.object_id = ic.object_id
   AND c.column_id = ic.column_id
WHERE i.index_id > 0
  AND (
        t.name LIKE N'%Usuario%'
     OR t.name LIKE N'%Rol%'
     OR t.name LIKE N'%Permiso%'
     OR t.name LIKE N'%Modulo%'
     OR t.name LIKE N'%Menu%'
     OR t.name LIKE N'%Accion%'
  )
ORDER BY
    s.name,
    t.name,
    i.name,
    ic.key_ordinal,
    ic.index_column_id;

/* 6. Triggers que pueden introducir escrituras indirectas */
SELECT
    s.name AS schema_name,
    t.name AS table_name,
    tr.name AS trigger_name,
    tr.is_disabled,
    tr.is_instead_of_trigger,
    OBJECT_DEFINITION(tr.object_id) AS trigger_definition
FROM sys.triggers AS tr
INNER JOIN sys.tables AS t
    ON t.object_id = tr.parent_id
INNER JOIN sys.schemas AS s
    ON s.schema_id = t.schema_id
WHERE (
        t.name LIKE N'%Usuario%'
     OR t.name LIKE N'%Rol%'
     OR t.name LIKE N'%Permiso%'
     OR t.name LIKE N'%Modulo%'
     OR t.name LIKE N'%Menu%'
     OR t.name LIKE N'%Accion%'
)
ORDER BY
    s.name,
    t.name,
    tr.name;

/* 7. Dependencias SQL declaradas entre objetos */
SELECT DISTINCT
    OBJECT_SCHEMA_NAME(d.referencing_id) AS referencing_schema,
    OBJECT_NAME(d.referencing_id) AS referencing_object,
    ro.type_desc AS referencing_type,
    d.referenced_schema_name,
    d.referenced_entity_name,
    CASE
        WHEN d.referenced_id IS NOT NULL
         AND ISNULL(d.referenced_minor_id, 0) > 0
        THEN COL_NAME(
            d.referenced_id,
            d.referenced_minor_id
        )
        ELSE NULL
    END AS referenced_minor_name,
    d.is_schema_bound_reference
FROM sys.sql_expression_dependencies AS d
LEFT JOIN sys.objects AS ro
    ON ro.object_id = d.referencing_id
WHERE
       d.referenced_entity_name LIKE N'%Usuario%'
    OR d.referenced_entity_name LIKE N'%Rol%'
    OR d.referenced_entity_name LIKE N'%Permiso%'
    OR d.referenced_entity_name LIKE N'%Modulo%'
    OR d.referenced_entity_name LIKE N'%Menu%'
    OR d.referenced_entity_name LIKE N'%Accion%'
ORDER BY
    d.referenced_schema_name,
    d.referenced_entity_name,
    referencing_schema,
    referencing_object;

/* 8. Tamaño lógico, sin leer datos de negocio */
SELECT
    s.name AS schema_name,
    t.name AS table_name,
    SUM(CASE WHEN p.index_id IN (0, 1) THEN p.rows ELSE 0 END) AS approximate_rows
FROM sys.tables AS t
INNER JOIN sys.schemas AS s
    ON s.schema_id = t.schema_id
LEFT JOIN sys.partitions AS p
    ON p.object_id = t.object_id
WHERE (
        t.name LIKE N'%Usuario%'
     OR t.name LIKE N'%Rol%'
     OR t.name LIKE N'%Permiso%'
     OR t.name LIKE N'%Modulo%'
     OR t.name LIKE N'%Menu%'
     OR t.name LIKE N'%Accion%'
)
GROUP BY
    s.name,
    t.name
ORDER BY
    s.name,
    t.name;

ROLLBACK TRANSACTION;
