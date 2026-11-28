SET NOCOUNT ON;
SET XACT_ABORT ON;

BEGIN TRY
    BEGIN TRANSACTION;

    IF OBJECT_ID('dbo.Sistema_Sync_Catalogo','U') IS NULL
        THROW 51000, 'SYNC_HISTORICAL_SEED_MISSING_CATALOG', 1;
    IF OBJECT_ID('dbo.Sistema_Sync_Capacidades','U') IS NULL
        THROW 51000, 'SYNC_HISTORICAL_SEED_MISSING_BINDING_TABLE', 1;

    /*
      Primera capability certificada.
      Evidencia en codigo: el handler oficial de Ventas Cerradas resuelve
      SoftRestaurant y ManagementPro usando el mismo contrato canonico.
    */
    UPDATE dbo.Sistema_Sync_Catalogo
       SET CategoriaCodigo='VENTAS',
           EntidadCodigo='VENTAS_CERRADAS_KPI',
           CampoFecha='fecha_operacion',
           ClaveNegocio=N'["unidad_negocio_id","sucursal_id","fecha_operacion"]',
           SoportaIncremental=0,
           SoportaFullSync=0,
           SoportaResume=1,
           SoportaSafeStop=1,
           VersionContrato='historical-v1',
           MetadataJSON=N'{"chunk_unit":"day","max_attempts":3,"retry_backoff_seconds":15,"atomic_boundary":"unit-capability-day"}'
     WHERE Codigo='comercial_ventas_cerradas'
       AND ISNULL(Activo,1)=1
       AND ISNULL(PermiteResync,0)=1
       AND ISNULL(HandlerImplementado,0)=1;

    /*
      No se inventan IDs. Solo se vinculan capacidades que YA existen
      en Sistema_Capacidades para sistemas canonicamente soportados.
    */
    INSERT INTO dbo.Sistema_Sync_Capacidades
        (CodigoSync, SistemaCapacidadID, Obligatoria, Activo)
    SELECT
        'comercial_ventas_cerradas',
        sc.SistemaCapacidadID,
        1,
        1
    FROM dbo.Sistema_Capacidades sc
    JOIN dbo.Sistema_Tipos st
      ON st.SistemaTipoID=sc.SistemaTipoID
    WHERE sc.CodigoCapacidad='SYNC_VENTAS_HISTORICAS'
      AND ISNULL(sc.Activo,1)=1
      AND ISNULL(st.Activo,1)=1
      AND st.CodigoSistema IN ('MPRO','SOFTRESTAURANT_PRO')
      AND NOT EXISTS (
          SELECT 1
          FROM dbo.Sistema_Sync_Capacidades x
          WHERE x.CodigoSync='comercial_ventas_cerradas'
            AND x.SistemaCapacidadID=sc.SistemaCapacidadID
      );

    COMMIT TRANSACTION;
END TRY
BEGIN CATCH
    IF XACT_STATE() <> 0 ROLLBACK TRANSACTION;
    THROW;
END CATCH;
