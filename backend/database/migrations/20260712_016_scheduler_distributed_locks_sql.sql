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

    IF COL_LENGTH(
        'dbo.Scheduler_DistributedLocks',
        'JobName'
    ) IS NULL
       OR COL_LENGTH(
        'dbo.Scheduler_DistributedLocks',
        'OwnerID'
    ) IS NULL
       OR COL_LENGTH(
        'dbo.Scheduler_DistributedLocks',
        'AcquiredAt'
    ) IS NULL
       OR COL_LENGTH(
        'dbo.Scheduler_DistributedLocks',
        'HeartbeatAt'
    ) IS NULL
       OR COL_LENGTH(
        'dbo.Scheduler_DistributedLocks',
        'LockUntil'
    ) IS NULL
    BEGIN
        THROW 51001,
            'Scheduler_DistributedLocks existe con contrato incompatible.',
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

    COMMIT TRANSACTION;
END TRY
BEGIN CATCH
    IF XACT_STATE() <> 0
        ROLLBACK TRANSACTION;

    THROW;
END CATCH;
