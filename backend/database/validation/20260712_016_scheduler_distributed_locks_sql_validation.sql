/*
Validacion posterior:
dbo.Scheduler_DistributedLocks

Este archivo contiene exclusivamente SELECT.
Debe ejecutarse con HRLectura.
*/

SET NOCOUNT ON;

SELECT
    DB_NAME() AS DatabaseName,
    SUSER_SNAME() AS LoginName,
    USER_NAME() AS DatabaseUser,
    OBJECT_ID(
        'dbo.Scheduler_DistributedLocks',
        'U'
    ) AS ObjectID;

SELECT
    c.column_id AS ColumnID,
    c.name AS ColumnName,
    ty.name AS DataType,
    c.max_length AS MaxLength,
    c.precision AS NumericPrecision,
    c.scale AS NumericScale,
    c.is_nullable AS IsNullable,
    c.is_identity AS IsIdentity
FROM sys.columns AS c
INNER JOIN sys.types AS ty
    ON ty.user_type_id = c.user_type_id
WHERE c.object_id = OBJECT_ID(
    'dbo.Scheduler_DistributedLocks',
    'U'
)
ORDER BY
    c.column_id;

SELECT
    i.name AS IndexName,
    i.is_unique AS IsUnique,
    i.is_primary_key AS IsPrimaryKey,
    i.type_desc AS IndexType,
    ic.key_ordinal AS KeyOrdinal,
    c.name AS ColumnName,
    ic.is_included_column AS IsIncludedColumn
FROM sys.indexes AS i
LEFT JOIN sys.index_columns AS ic
    ON ic.object_id = i.object_id
   AND ic.index_id = i.index_id
LEFT JOIN sys.columns AS c
    ON c.object_id = ic.object_id
   AND c.column_id = ic.column_id
WHERE i.object_id = OBJECT_ID(
    'dbo.Scheduler_DistributedLocks',
    'U'
)
  AND i.index_id > 0
ORDER BY
    i.name,
    ic.is_included_column,
    ic.key_ordinal,
    c.column_id;

SELECT
    cc.name AS ConstraintName,
    cc.definition AS ConstraintDefinition,
    cc.is_disabled AS IsDisabled,
    cc.is_not_trusted AS IsNotTrusted
FROM sys.check_constraints AS cc
WHERE cc.parent_object_id = OBJECT_ID(
    'dbo.Scheduler_DistributedLocks',
    'U'
)
ORDER BY
    cc.name;

SELECT
    COUNT_BIG(*) AS TotalLocks,
    COALESCE(
        SUM(
            CASE
                WHEN LockUntil > SYSUTCDATETIME()
                THEN 1
                ELSE 0
            END
        ),
        0
    ) AS ActiveLocks,
    COALESCE(
        SUM(
            CASE
                WHEN LockUntil <= SYSUTCDATETIME()
                THEN 1
                ELSE 0
            END
        ),
        0
    ) AS ExpiredLocks
FROM dbo.Scheduler_DistributedLocks;
