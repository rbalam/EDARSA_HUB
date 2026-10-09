SET NOCOUNT ON;
SET XACT_ABORT ON;

BEGIN TRY
    BEGIN TRANSACTION;

    IF OBJECT_ID('dbo.Sistema_Sync_Catalogo','U') IS NULL
        THROW 51000, 'SYNC_HISTORICAL_SEED_ROLLBACK_MISSING_CATALOG', 1;

    /*
      Retira exclusivamente el seed de este gate.
      Se niega a borrar metadata si ya fue modificada por una fase posterior.
    */
    IF EXISTS (
        SELECT 1
        FROM dbo.Sistema_Sync_Catalogo
        WHERE Codigo='comercial_ventas_cerradas'
          AND (
              ISNULL(CategoriaCodigo,'') <> 'VENTAS'
              OR ISNULL(EntidadCodigo,'') <> 'VENTAS_CERRADAS_KPI'
              OR ISNULL(CampoFecha,'') <> 'fecha_operacion'
              OR ISNULL(VersionContrato,'') <> 'historical-v1'
          )
          AND (
              CategoriaCodigo IS NOT NULL
              OR EntidadCodigo IS NOT NULL
              OR CampoFecha IS NOT NULL
              OR VersionContrato IS NOT NULL
          )
    )
        THROW 51000, 'SYNC_HISTORICAL_SEED_ROLLBACK_REFUSES_DIVERGED_METADATA', 1;

    DELETE link
    FROM dbo.Sistema_Sync_Capacidades link
    JOIN dbo.Sistema_Capacidades cap
      ON cap.SistemaCapacidadID=link.SistemaCapacidadID
    JOIN dbo.Sistema_Tipos st
      ON st.SistemaTipoID=cap.SistemaTipoID
    WHERE link.CodigoSync='comercial_ventas_cerradas'
      AND cap.CodigoCapacidad='SYNC_VENTAS_HISTORICAS'
      AND st.CodigoSistema IN ('MPRO','SOFTRESTAURANT');

    UPDATE dbo.Sistema_Sync_Catalogo
       SET CategoriaCodigo=NULL,
           EntidadCodigo=NULL,
           CampoFecha=NULL,
           ClaveNegocio=NULL,
           SoportaIncremental=0,
           SoportaFullSync=0,
           SoportaResume=0,
           SoportaSafeStop=0,
           VersionContrato=NULL,
           MetadataJSON=NULL,
           FechaModificacion=SYSUTCDATETIME()
     WHERE Codigo='comercial_ventas_cerradas'
       AND CategoriaCodigo='VENTAS'
       AND EntidadCodigo='VENTAS_CERRADAS_KPI'
       AND CampoFecha='fecha_operacion'
       AND VersionContrato='historical-v1';

    COMMIT TRANSACTION;
END TRY
BEGIN CATCH
    IF XACT_STATE() <> 0 ROLLBACK TRANSACTION;
    THROW;
END CATCH;
