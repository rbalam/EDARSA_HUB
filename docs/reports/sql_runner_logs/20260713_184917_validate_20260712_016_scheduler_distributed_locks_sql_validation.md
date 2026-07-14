# EDARSAHUB SQL Runner Report

- Fecha: 2026-07-13T18:49:17.136396
- Modo: `validate`
- Servidor: `NO_DEFINIDO`
- Base de datos: `NO_DEFINIDO`
- Script: `/app/backend/database/validation/20260712_016_scheduler_distributed_locks_sql_validation.sql`

## Resultado
ERROR

## Detalle
```text
El modo validate no permite cambios de estructura o datos. Patrón detectado: \bDROP\b
```

## SQL ejecutado / revisado
```sql
/*
Validacion posterior:
dbo.Scheduler_DistributedLocks

Archivo de solo lectura:
- SELECT para evidencia.
- IF/THROW para validacion fail-closed.
- Sin INSERT, UPDATE, DELETE, MERGE, CREATE, ALTER ni DROP.

Debe ejecutarse exclusivamente con:
- DB_NAME() = EDARSAHUB
- SUSER_SNAME() = HRLectura
- USER_NAME() = HRLectura
*/

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
    @ObjectID AS ObjectID;

IF @DatabaseName IS NULL
   OR CONVERT(VARBINARY(256), @DatabaseName)
      <> CONVERT(VARBINARY(256), N'EDARSAHUB')
BEGIN
    ;THROW 51000,
        N'Validacion abortada: DB_NAME() debe ser EDARSAHUB.',
        1;
END;

IF @LoginName IS NULL
   OR CONVERT(VARBINARY(256), @LoginName)
      <> CONVERT(VARBINARY(256), N'HRLectura')
BEGIN
    ;THROW 51001,
        N'Validacion abortada: SUSER_SNAME() debe ser HRLectura.',
        1;
END;

IF @DatabaseUser IS NULL
   OR CONVERT(VARBINARY(256), @DatabaseUser)
      <> CONVERT(VARBINARY(256), N'HRLectura')
BEGIN
    ;THROW 51002,
        N'Validacion abortada: USER_NAME() debe ser HRLectura.',
        1;
END;

IF @ObjectID IS NULL
BEGIN
    ;THROW 51003,
        N'Validacion abortada: no existe dbo.Scheduler_DistributedLocks.',
        1;
END;

IF EXISTS (
    SELECT 1
    FROM (
        VALUES
            (
                N'JobName',
                N'varchar',
                CONVERT(SMALLINT, 100),
                CONVERT(TINYINT, 0),
                CONVERT(BIT, 0)
            ),
            (
                N'OwnerID',
                N'varchar',
                CONVERT(SMALLINT, 200),
                CONVERT(TINYINT, 0),
                CONVERT(BIT, 0)
            ),
            (
                N'AcquiredAt',
                N'datetime2',
                CONVERT(SMALLINT, NULL),
                CONVERT(TINYINT, 3),
                CONVERT(BIT, 0)
            ),
            (
                N'HeartbeatAt',
                N'datetime2',
                CONVERT(SMALLINT, NULL),
                CONVERT(TINYINT, 3),
                CONVERT(BIT, 0)
            ),
            (
                N'LockUntil',
                N'datetime2',
                CONVERT(SMALLINT, NULL),
                CONVERT(TINYINT, 3),
                CONVERT(BIT, 0)
            )
    ) AS expected (
        ColumnName,
        DataType,
        MaxLength,
        NumericScale,
        IsNullable
    )
    LEFT JOIN sys.columns AS c
        ON c.object_id = @ObjectID
       AND c.name = expected.ColumnName
    LEFT JOIN sys.types AS ty
        ON ty.user_type_id = c.user_type_id
    WHERE c.column_id IS NULL
       OR ty.name <> expected.DataType
       OR (
            expected.MaxLength IS NOT NULL
            AND c.max_length <> expected.MaxLength
       )
       OR c.scale <> expected.NumericScale
       OR c.is_nullable <> expected.IsNullable
       OR c.is_identity <> 0
)
OR EXISTS (
    SELECT 1
    FROM sys.columns AS c
    WHERE c.object_id = @ObjectID
      AND c.name NOT IN (
          N'JobName',
          N'OwnerID',
          N'AcquiredAt',
          N'HeartbeatAt',
          N'LockUntil'
      )
)
BEGIN
    ;THROW 51004,
        N'Validacion abortada: contrato de columnas incompatible.',
        1;
END;

IF (
    SELECT COUNT_BIG(*)
    FROM sys.default_constraints AS dc
    WHERE dc.parent_object_id = @ObjectID
) <> 2
OR NOT EXISTS (
    SELECT 1
    FROM sys.default_constraints AS dc
    INNER JOIN sys.columns AS c
        ON c.object_id = dc.parent_object_id
       AND c.column_id = dc.parent_column_id
    WHERE dc.parent_object_id = @ObjectID
      AND dc.name =
          N'DF_Scheduler_DistributedLocks_AcquiredAt'
      AND c.name = N'AcquiredAt'
      AND LOWER(
          REPLACE(
              REPLACE(
                  REPLACE(
                      REPLACE(
                          REPLACE(
                              dc.definition,
                              N'[', N''
                          ),
                          N']', N''
                      ),
                      N'(', N''
                  ),
                  N')', N''
              ),
              N' ', N''
          )
      ) = N'sysutcdatetime'
)
OR NOT EXISTS (
    SELECT 1
    FROM sys.default_constraints AS dc
    INNER JOIN sys.columns AS c
        ON c.object_id = dc.parent_object_id
       AND c.column_id = dc.parent_column_id
    WHERE dc.parent_object_id = @ObjectID
      AND dc.name =
          N'DF_Scheduler_DistributedLocks_HeartbeatAt'
      AND c.name = N'HeartbeatAt'
      AND LOWER(
          REPLACE(
              REPLACE(
                  REPLACE(
                      REPLACE(
                          REPLACE(
                              dc.definition,
                              N'[', N''
                          ),
                          N']', N''
                      ),
                      N'(', N''
                  ),
                  N')', N''
              ),
              N' ', N''
          )
      ) = N'sysutcdatetime'
)
BEGIN
    ;THROW 51005,
        N'Validacion abortada: defaults UTC incompatibles.',
        1;
END;

IF NOT EXISTS (
    SELECT 1
    FROM sys.indexes AS i
    WHERE i.object_id = @ObjectID
      AND i.name = N'PK_Scheduler_DistributedLocks'
      AND i.is_primary_key = 1
      AND i.is_unique = 1
      AND i.type = 1
      AND i.is_disabled = 0
      AND i.is_hypothetical = 0
      AND i.has_filter = 0
      AND (
          SELECT COUNT_BIG(*)
          FROM sys.index_columns AS ic
          WHERE ic.object_id = i.object_id
            AND ic.index_id = i.index_id
            AND ic.key_ordinal > 0
            AND ic.is_included_column = 0
      ) = 1
      AND EXISTS (
          SELECT 1
          FROM sys.index_columns AS ic
          INNER JOIN sys.columns AS c
              ON c.object_id = ic.object_id
             AND c.column_id = ic.column_id
          WHERE ic.object_id = i.object_id
            AND ic.index_id = i.index_id
            AND ic.key_ordinal = 1
            AND ic.is_included_column = 0
            AND ic.is_descending_key = 0
            AND c.name = N'JobName'
      )
)
BEGIN
    ;THROW 51006,
        N'Validacion abortada: primary key incompatible.',
        1;
END;

IF (
    SELECT COUNT_BIG(*)
    FROM sys.check_constraints AS cc
    WHERE cc.parent_object_id = @ObjectID
) <> 1
OR NOT EXISTS (
    SELECT 1
    FROM sys.check_constraints AS cc
    WHERE cc.parent_object_id = @ObjectID
      AND cc.name =
          N'CK_Scheduler_DistributedLocks_Expiration'
      AND cc.is_disabled = 0
      AND cc.is_not_trusted = 0
      AND LOWER(
          REPLACE(
              REPLACE(
                  REPLACE(
                      REPLACE(
                          REPLACE(
                              cc.definition,
                              N'[', N''
                          ),
                          N']', N''
                      ),
                      N'(', N''
                  ),
                  N')', N''
              ),
              N' ', N''
          )
      ) = N'lockuntil>=heartbeatat'
)
BEGIN
    ;THROW 51007,
        N'Validacion abortada: check de expiracion incompatible.',
        1;
END;

IF NOT EXISTS (
    SELECT 1
    FROM sys.indexes AS i
    WHERE i.object_id = @ObjectID
      AND i.name =
          N'IX_Scheduler_DistributedLocks_LockUntil'
      AND i.type = 2
      AND i.is_unique = 0
      AND i.is_disabled = 0
      AND i.is_hypothetical = 0
      AND i.has_filter = 0
      AND (
          SELECT COUNT_BIG(*)
          FROM sys.index_columns AS ic
          WHERE ic.object_id = i.object_id
            AND ic.index_id = i.index_id
            AND ic.key_ordinal > 0
            AND ic.is_included_column = 0
      ) = 1
      AND (
          SELECT COUNT_BIG(*)
          FROM sys.index_columns AS ic
          WHERE ic.object_id = i.object_id
            AND ic.index_id = i.index_id
            AND ic.is_included_column = 1
      ) = 2
      AND EXISTS (
          SELECT 1
          FROM sys.index_columns AS ic
          INNER JOIN sys.columns AS c
              ON c.object_id = ic.object_id
             AND c.column_id = ic.column_id
          WHERE ic.object_id = i.object_id
            AND ic.index_id = i.index_id
            AND ic.key_ordinal = 1
            AND ic.is_included_column = 0
            AND ic.is_descending_key = 0
            AND c.name = N'LockUntil'
      )
      AND EXISTS (
          SELECT 1
          FROM sys.index_columns AS ic
          INNER JOIN sys.columns AS c
              ON c.object_id = ic.object_id
             AND c.column_id = ic.column_id
          WHERE ic.object_id = i.object_id
            AND ic.index_id = i.index_id
            AND ic.is_included_column = 1
            AND c.name = N'OwnerID'
      )
      AND EXISTS (
          SELECT 1
          FROM sys.index_columns AS ic
          INNER JOIN sys.columns AS c
              ON c.object_id = ic.object_id
             AND c.column_id = ic.column_id
          WHERE ic.object_id = i.object_id
            AND ic.index_id = i.index_id
            AND ic.is_included_column = 1
            AND c.name = N'HeartbeatAt'
      )
)
BEGIN
    ;THROW 51008,
        N'Validacion abortada: indice LockUntil incompatible.',
        1;
END;

IF NOT EXISTS (
    SELECT 1
    FROM sys.indexes AS i
    WHERE i.object_id = @ObjectID
      AND i.name =
          N'IX_Scheduler_DistributedLocks_OwnerID'
      AND i.type = 2
      AND i.is_unique = 0
      AND i.is_disabled = 0
      AND i.is_hypothetical = 0
      AND i.has_filter = 0
      AND (
          SELECT COUNT_BIG(*)
          FROM sys.index_columns AS ic
          WHERE ic.object_id = i.object_id
            AND ic.index_id = i.index_id
            AND ic.key_ordinal > 0
            AND ic.is_included_column = 0
      ) = 1
      AND (
          SELECT COUNT_BIG(*)
          FROM sys.index_columns AS ic
          WHERE ic.object_id = i.object_id
            AND ic.index_id = i.index_id
            AND ic.is_included_column = 1
      ) = 0
      AND EXISTS (
          SELECT 1
          FROM sys.index_columns AS ic
          INNER JOIN sys.columns AS c
              ON c.object_id = ic.object_id
             AND c.column_id = ic.column_id
          WHERE ic.object_id = i.object_id
            AND ic.index_id = i.index_id
            AND ic.key_ordinal = 1
            AND ic.is_included_column = 0
            AND ic.is_descending_key = 0
            AND c.name = N'OwnerID'
      )
)
BEGIN
    ;THROW 51009,
        N'Validacion abortada: indice OwnerID incompatible.',
        1;
END;

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
WHERE c.object_id = @ObjectID
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
WHERE i.object_id = @ObjectID
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
WHERE cc.parent_object_id = @ObjectID
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

```