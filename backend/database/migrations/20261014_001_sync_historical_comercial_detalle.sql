SET NOCOUNT ON;
SET XACT_ABORT ON;

BEGIN TRY
    BEGIN TRANSACTION;

    IF OBJECT_ID('dbo.Sistema_Sync_Catalogo','U') IS NULL
        THROW 51000, 'SYNC_HISTORICAL_DETAIL_MISSING_CATALOG', 1;
    IF OBJECT_ID('dbo.Sistema_Sync_Capacidades','U') IS NULL
        THROW 51000, 'SYNC_HISTORICAL_DETAIL_MISSING_BINDINGS', 1;

    /*
      Capability historica de detalle de ventas.
      Aditiva: no modifica ni reutiliza los sincronizadores protegidos de
      Ventas del Dia / Ventas Cerradas. El runtime atomico usa el backfill
      historico de dbo.Sync_Sales.
    */
    UPDATE dbo.Sistema_Sync_Catalogo
       SET CategoriaCodigo='VENTAS',
           EntidadCodigo='VENTA_DETALLE',
           CampoFecha='FechaHora',
           ClaveNegocio=N'["UnidadNegocio","NumeroTicket","FechaHora"]',
           Handler='backfill_sync_sales',
           HandlerImplementado=1,
           SoportaIncremental=1,
           SoportaFullSync=1,
           SoportaResume=1,
           SoportaSafeStop=1,
           VersionContrato='historical-detail-v1',
           MetadataJSON=N'{"chunk_unit":"day","max_attempts":3,"retry_backoff_seconds":15,"atomic_boundary":"unit-capability-day"}'
     WHERE Codigo='comercial_ventas_detalle'
       AND ISNULL(Activo,1)=1
       AND ISNULL(PermiteResync,0)=1;

    IF @@ROWCOUNT <> 1
        THROW 51000, 'SYNC_HISTORICAL_DETAIL_CATALOG_ROW_MISSING', 1;

    INSERT INTO dbo.Sistema_Sync_Capacidades
        (CodigoSync, SistemaCapacidadID, Obligatoria, Activo)
    SELECT
        'comercial_ventas_detalle',
        cap.SistemaCapacidadID,
        1,
        1
    FROM dbo.Sistema_Capacidades cap
    JOIN dbo.Sistema_Tipos st
      ON st.SistemaTipoID=cap.SistemaTipoID
    WHERE cap.CodigoCapacidad='SYNC_VENTAS_HISTORICAS'
      AND ISNULL(cap.Activo,1)=1
      AND ISNULL(st.Activo,1)=1
      AND st.CodigoSistema IN ('MPRO','SOFTRESTAURANT_PRO')
      AND NOT EXISTS (
          SELECT 1
          FROM dbo.Sistema_Sync_Capacidades link
          WHERE link.CodigoSync='comercial_ventas_detalle'
            AND link.SistemaCapacidadID=cap.SistemaCapacidadID
      );

    IF (
        SELECT COUNT(DISTINCT st.CodigoSistema)
        FROM dbo.Sistema_Sync_Capacidades link
        JOIN dbo.Sistema_Capacidades cap
          ON cap.SistemaCapacidadID=link.SistemaCapacidadID
        JOIN dbo.Sistema_Tipos st
          ON st.SistemaTipoID=cap.SistemaTipoID
        WHERE link.CodigoSync='comercial_ventas_detalle'
          AND ISNULL(link.Activo,1)=1
          AND cap.CodigoCapacidad='SYNC_VENTAS_HISTORICAS'
          AND ISNULL(cap.Activo,1)=1
          AND ISNULL(st.Activo,1)=1
          AND st.CodigoSistema IN ('MPRO','SOFTRESTAURANT_PRO')
    ) <> 2
        THROW 51000, 'SYNC_HISTORICAL_DETAIL_BINDINGS_INCOMPLETE', 1;

    COMMIT TRANSACTION;
END TRY
BEGIN CATCH
    IF XACT_STATE() <> 0 ROLLBACK TRANSACTION;
    THROW;
END CATCH;
