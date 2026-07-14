# EDARSAHUB SQL Runner Report

- Fecha: 2026-07-13T18:49:16.951214
- Modo: `diagnostic`
- Servidor: `NO_DEFINIDO`
- Base de datos: `NO_DEFINIDO`
- Script: `/tmp/20260712_016_scheduler_distributed_locks_preflight.sql`

## Resultado
ERROR

## Detalle
```text
Error ejecutando SQL. Se hizo rollback. Detalle: Variable obligatoria no configurada: EDARSAHUB_SQL_HOST
```

## SQL ejecutado / revisado
```sql
SET NOCOUNT ON;

DECLARE
    @DatabaseName SYSNAME = DB_NAME(),
    @LoginName SYSNAME = SUSER_SNAME(),
    @DatabaseUser SYSNAME = USER_NAME(),
    @ObjectID INT = OBJECT_ID(
        N'dbo.Scheduler_DistributedLocks',
        N'U'
    );

SELECT
    @DatabaseName AS DatabaseName,
    @LoginName AS LoginName,
    @DatabaseUser AS DatabaseUser,
    @ObjectID AS SchedulerLockObjectID,
    CASE
        WHEN CONVERT(VARBINARY(256), @DatabaseName)
             = CONVERT(VARBINARY(256), N'EDARSAHUB')
        THEN 1
        ELSE 0
    END AS DatabaseIdentityExact,
    CASE
        WHEN CONVERT(VARBINARY(256), @LoginName)
             = CONVERT(VARBINARY(256), N'HRLectura')
        THEN 1
        ELSE 0
    END AS LoginIdentityExact,
    CASE
        WHEN CONVERT(VARBINARY(256), @DatabaseUser)
             = CONVERT(VARBINARY(256), N'HRLectura')
        THEN 1
        ELSE 0
    END AS DatabaseUserIdentityExact;

IF @DatabaseName IS NULL
   OR CONVERT(VARBINARY(256), @DatabaseName)
      <> CONVERT(VARBINARY(256), N'EDARSAHUB')
BEGIN
    ;THROW 52000,
        N'Preflight abortado: DB_NAME() debe ser EDARSAHUB.',
        1;
END;

IF @LoginName IS NULL
   OR CONVERT(VARBINARY(256), @LoginName)
      <> CONVERT(VARBINARY(256), N'HRLectura')
BEGIN
    ;THROW 52001,
        N'Preflight abortado: SUSER_SNAME() debe ser HRLectura.',
        1;
END;

IF @DatabaseUser IS NULL
   OR CONVERT(VARBINARY(256), @DatabaseUser)
      <> CONVERT(VARBINARY(256), N'HRLectura')
BEGIN
    ;THROW 52002,
        N'Preflight abortado: USER_NAME() debe ser HRLectura.',
        1;
END;

SELECT
    s.name AS SchemaName,
    t.name AS TableName
FROM sys.tables AS t
INNER JOIN sys.schemas AS s
    ON s.schema_id = t.schema_id
WHERE LOWER(t.name) LIKE N'%migr%'
   OR LOWER(t.name) LIKE N'%schema%'
   OR LOWER(t.name) LIKE N'%version%'
   OR LOWER(t.name) LIKE N'%deploy%'
ORDER BY
    s.name,
    t.name;

SELECT
    CASE
        WHEN @ObjectID IS NULL
        THEN N'ABSENT'
        ELSE N'PRESENT'
    END AS SchedulerLockTableStatus,
    @ObjectID AS ObjectID;

IF @ObjectID IS NOT NULL
BEGIN
    SELECT
        c.column_id AS ColumnID,
        c.name AS ColumnName,
        ty.name AS DataType,
        c.max_length AS MaxLength,
        c.precision AS NumericPrecision,
        c.scale AS NumericScale,
        c.is_nullable AS IsNullable,
        c.is_identity AS IsIdentity,
        dc.name AS DefaultConstraintName,
        dc.definition AS DefaultDefinition
    FROM sys.columns AS c
    INNER JOIN sys.types AS ty
        ON ty.user_type_id = c.user_type_id
    LEFT JOIN sys.default_constraints AS dc
        ON dc.parent_object_id = c.object_id
       AND dc.parent_column_id = c.column_id
    WHERE c.object_id = @ObjectID
    ORDER BY
        c.column_id;

    SELECT
        kc.name AS ConstraintName,
        kc.type_desc AS ConstraintType,
        kc.unique_index_id AS UniqueIndexID
    FROM sys.key_constraints AS kc
    WHERE kc.parent_object_id = @ObjectID
    ORDER BY
        kc.name;

    SELECT
        cc.name AS ConstraintName,
        cc.definition AS ConstraintDefinition,
        cc.is_disabled AS IsDisabled,
        cc.is_not_trusted AS IsNotTrusted
    FROM sys.check_constraints AS cc
    WHERE cc.parent_object_id = @ObjectID
    ORDER BY
        cc.name;

    SELECT
        i.name AS IndexName,
        i.type_desc AS IndexType,
        i.is_primary_key AS IsPrimaryKey,
        i.is_unique AS IsUnique,
        i.is_disabled AS IsDisabled,
        i.is_hypothetical AS IsHypothetical,
        i.has_filter AS HasFilter,
        ic.key_ordinal AS KeyOrdinal,
        ic.is_included_column AS IsIncludedColumn,
        ic.is_descending_key AS IsDescendingKey,
        c.name AS ColumnName
    FROM sys.indexes AS i
    LEFT JOIN sys.index_columns AS ic
        ON ic.object_id = i.object_id
       AND ic.index_id = i.index_id
    LEFT JOIN sys.columns AS c
        ON c.object_id = ic.object_id
       AND c.column_id = ic.column_id
    WHERE i.object_id = @ObjectID
      AND i.index_id > 0
    ORDER BY
        i.name,
        ic.is_included_column,
        ic.key_ordinal,
        c.column_id;

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
END;

```