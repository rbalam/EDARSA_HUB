SET NOCOUNT ON;
SET XACT_ABORT ON;

BEGIN TRY
    BEGIN TRANSACTION;

    IF OBJECT_ID('dbo.Sync_Control_Ejecuciones','U') IS NULL
        THROW 51000, 'SYNC_HISTORICAL_CANARY_MISSING_LEDGER', 1;

    IF OBJECT_ID('dbo.Sistema_Sync_Catalogo','U') IS NULL
        THROW 51000, 'SYNC_HISTORICAL_CANARY_MISSING_REGISTRY', 1;

    DECLARE @Fecha date = '2026-10-08';
    DECLARE @CorrelationID uniqueidentifier =
        CONVERT(uniqueidentifier, '4E7A84DE-3E62-4C95-9F53-202610090001');
    DECLARE @ParentRunID nvarchar(50) = N'HIST-CANARY-P-20261009';
    DECLARE @ParentID int;

    SELECT @ParentID = SyncControlID
    FROM dbo.Sync_Control_Ejecuciones
    WHERE SyncRunID=@ParentRunID
      AND RunKind='PARENT';

    IF @ParentID IS NULL
    BEGIN
        INSERT INTO dbo.Sync_Control_Ejecuciones (
            SyncRunID, SyncType, FechaInicio, FechaFin,
            IsDryRun, Status, StartedAtMexico,
            StartedAtUTC, IdempotencyKey,
            RunKind, CorrelationID, PlanJSON,
            AttemptCount, MaxAttempts,
            PauseRequested, CancelRequested,
            RequestedBy, Reason, UpdatedAtUTC
        )
        VALUES (
            @ParentRunID, 'HISTORICAL_PARENT', @Fecha, @Fecha,
            1, 'QUEUED', SYSDATETIME(),
            SYSUTCDATETIME(), 'historical-canary-parent:20261009',
            'PARENT', @CorrelationID,
            N'{"canary":true,"date":"2026-10-08","units":["ORIGEN","CIENFUEGOS"],"capability":"comercial_ventas_cerradas"}',
            0, 1,
            0, 0,
            'WORKER_UNIVERSAL_V1.2_CANARY',
            N'Canario DRY RUN de Sincronizacion Historica; valida MPRO y SoftRestaurant Pro sin escribir ventas.',
            SYSUTCDATETIME()
        );

        SET @ParentID = SCOPE_IDENTITY();
    END;

    ;WITH CandidateUnits AS (
        SELECT
            u.id AS UnidadNegocioID,
            UPPER(LTRIM(RTRIM(u.codigo))) AS UnidadCodigo,
            u.server_id AS ConexionID,
            u.sucursal_origen_id AS SucursalOrigenID,
            s.sistema_version_id AS SistemaVersionID,
            st.SistemaTipoID,
            cap.SistemaCapacidadID,
            suc.SucursalID,
            suc.EmpresaID,
            sc.Codigo AS CodigoSync,
            sc.CategoriaCodigo,
            sc.EntidadCodigo,
            ISNULL(sc.Orden,100) AS ExecutionOrder
        FROM dbo.Unidades_Negocio u
        JOIN dbo.Servidores_Conexiones s
          ON LOWER(CONVERT(nvarchar(100),s.id))
           = LOWER(CONVERT(nvarchar(100),u.server_id))
        JOIN dbo.Sistema_Tipos st
          ON st.CodigoSistema=s.system_type
         AND ISNULL(st.Activo,1)=1
        JOIN dbo.Sistema_Capacidades cap
          ON cap.SistemaTipoID=st.SistemaTipoID
         AND cap.CodigoCapacidad='SYNC_VENTAS_HISTORICAS'
         AND ISNULL(cap.Activo,1)=1
        JOIN dbo.Sistema_Sync_Capacidades link
          ON link.SistemaCapacidadID=cap.SistemaCapacidadID
         AND link.CodigoSync='comercial_ventas_cerradas'
         AND ISNULL(link.Activo,1)=1
        JOIN dbo.Sistema_Sync_Catalogo sc
          ON sc.Codigo=link.CodigoSync
         AND ISNULL(sc.Activo,1)=1
         AND ISNULL(sc.PermiteResync,0)=1
        JOIN dbo.Sistema_SucursalServidorMapeo map
          ON LOWER(CONVERT(nvarchar(100),map.ServidorID))
           = LOWER(CONVERT(nvarchar(100),u.server_id))
         AND ISNULL(map.Activo,0)=1
         AND (
              NULLIF(LTRIM(RTRIM(CONVERT(nvarchar(100),map.SucursalOrigenID))),'')
              =
              NULLIF(LTRIM(RTRIM(CONVERT(nvarchar(100),u.sucursal_origen_id))),'')
              OR (
                  NULLIF(LTRIM(RTRIM(CONVERT(nvarchar(100),map.SucursalOrigenID))),'') IS NULL
                  AND
                  NULLIF(LTRIM(RTRIM(CONVERT(nvarchar(100),u.sucursal_origen_id))),'') IS NULL
              )
         )
        JOIN dbo.Sistema_Sucursales suc
          ON suc.SucursalID=map.SucursalID
        WHERE ISNULL(u.activo,1)=1
          AND ISNULL(s.activo,1)=1
          AND UPPER(LTRIM(RTRIM(u.codigo))) IN ('ORIGEN','CIENFUEGOS')
    )
    INSERT INTO dbo.Sync_Control_Ejecuciones (
        SyncRunID, SyncType, ServerID, EmpresaID,
        FechaInicio, FechaFin,
        IsDryRun, Status, StartedAtMexico,
        ConexionID, UnidadNegocioID, CodigoSync,
        StartedAtUTC, IdempotencyKey,
        ParentSyncControlID, RunKind, CorrelationID,
        SistemaTipoID, SistemaCapacidadID, SistemaVersionID, SucursalID,
        SucursalOrigenID, CategoriaCodigo, EntidadCodigo, BlockOrdinal,
        ExecutionOrder, PlanJSON, AttemptCount, MaxAttempts,
        PauseRequested, CancelRequested,
        RequestedBy, Reason, UpdatedAtUTC
    )
    SELECT
        LEFT(N'HIST-CAN-' + cu.UnidadCodigo + N'-20261008',50),
        'HISTORICAL_ATOMIC',
        cu.ConexionID,
        cu.EmpresaID,
        @Fecha,
        @Fecha,
        1,
        'QUEUED',
        SYSDATETIME(),
        cu.ConexionID,
        cu.UnidadNegocioID,
        cu.CodigoSync,
        SYSUTCDATETIME(),
        LEFT(N'historical-canary:' + LOWER(cu.UnidadCodigo)
             + N':2026-10-08:comercial_ventas_cerradas',200),
        @ParentID,
        'ATOMIC',
        @CorrelationID,
        cu.SistemaTipoID,
        cu.SistemaCapacidadID,
        cu.SistemaVersionID,
        cu.SucursalID,
        cu.SucursalOrigenID,
        cu.CategoriaCodigo,
        cu.EntidadCodigo,
        1,
        cu.ExecutionOrder,
        N'{"canary":true,"metadata":{"retry_backoff_seconds":5}}',
        0,
        1,
        0,
        0,
        'WORKER_UNIVERSAL_V1.2_CANARY',
        N'Canario DRY RUN de Sincronizacion Historica; no escribe ventas.',
        SYSUTCDATETIME()
    FROM CandidateUnits cu
    WHERE NOT EXISTS (
        SELECT 1
        FROM dbo.Sync_Control_Ejecuciones existing
        WHERE existing.IdempotencyKey =
              LEFT(N'historical-canary:' + LOWER(cu.UnidadCodigo)
                   + N':2026-10-08:comercial_ventas_cerradas',200)
    );

    IF (
        SELECT COUNT(*)
        FROM dbo.Sync_Control_Ejecuciones
        WHERE ParentSyncControlID=@ParentID
          AND RunKind='ATOMIC'
          AND IsDryRun=1
    ) <> 2
        THROW 51000, 'SYNC_HISTORICAL_CANARY_EXPECTED_TWO_ATOMIC_UNITS', 1;

    COMMIT TRANSACTION;
END TRY
BEGIN CATCH
    IF XACT_STATE() <> 0 ROLLBACK TRANSACTION;
    THROW;
END CATCH;
