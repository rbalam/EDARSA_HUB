/*
EDARSAHUB V1.0
Migracion: Scheduler_DistributedLocks
Fecha: 2026-07-12

Objetivo:
- Sustituir scheduler_locks de MongoDB.
- Proporcionar exclusion mutua entre procesos y workers.
- Soportar expiracion, heartbeat, liberacion por propietario
  y liberacion administrativa.
- No modificar las tablas existentes del scheduler.

Esta migracion no migra datos porque el lock Mongo actual
se encuentra neutralizado mediante NullLock.
*/

SET NOCOUNT ON;
SET XACT_ABORT ON;

BEGIN TRY
    BEGIN TRANSACTION;

    IF OBJECT_ID(
        'dbo.Scheduler_DistributedLocks',
        'U'
    ) IS NULL
    BEGIN
        CREATE TABLE dbo.Scheduler_DistributedLocks
        (
            JobName VARCHAR(100) NOT NULL,
            OwnerID VARCHAR(200) NOT NULL,

            AcquiredAt DATETIME2(3) NOT NULL
                CONSTRAINT DF_Scheduler_DistributedLocks_AcquiredAt
                DEFAULT SYSUTCDATETIME(),

            HeartbeatAt DATETIME2(3) NOT NULL
                CONSTRAINT DF_Scheduler_DistributedLocks_HeartbeatAt
                DEFAULT SYSUTCDATETIME(),

            LockUntil DATETIME2(3) NOT NULL,

            CONSTRAINT PK_Scheduler_DistributedLocks
                PRIMARY KEY CLUSTERED (JobName),

            CONSTRAINT CK_Scheduler_DistributedLocks_Expiration
                CHECK (LockUntil >= HeartbeatAt)
        );
    END;

    DECLARE @ObjectID INT = OBJECT_ID(
        N'dbo.Scheduler_DistributedLocks',
        N'U'
    );

    IF @ObjectID IS NULL
    BEGIN
        ;THROW 51003,
            N'Migracion abortada: no existe dbo.Scheduler_DistributedLocks.',
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

    IF NOT EXISTS
    (
        SELECT 1
        FROM sys.indexes
        WHERE object_id = OBJECT_ID(
            'dbo.Scheduler_DistributedLocks',
            'U'
        )
          AND name =
            'IX_Scheduler_DistributedLocks_LockUntil'
    )
    BEGIN
        CREATE NONCLUSTERED INDEX
            IX_Scheduler_DistributedLocks_LockUntil
        ON dbo.Scheduler_DistributedLocks
            (LockUntil)
        INCLUDE
            (OwnerID, HeartbeatAt);
    END;

    IF NOT EXISTS
    (
        SELECT 1
        FROM sys.indexes
        WHERE object_id = OBJECT_ID(
            'dbo.Scheduler_DistributedLocks',
            'U'
        )
          AND name =
            'IX_Scheduler_DistributedLocks_OwnerID'
    )
    BEGIN
        CREATE NONCLUSTERED INDEX
            IX_Scheduler_DistributedLocks_OwnerID
        ON dbo.Scheduler_DistributedLocks
            (OwnerID);
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

    COMMIT TRANSACTION;
END TRY
BEGIN CATCH
    IF XACT_STATE() <> 0
        ROLLBACK TRANSACTION;

    THROW;
END CATCH;
