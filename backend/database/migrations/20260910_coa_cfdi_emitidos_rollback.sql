/*
COA Gate 5E - ROLLBACK CFDI EMITIDOS
DESIGN ONLY - NO EJECUTAR EN ESTE GATE
Revierte exclusivamente objetos propuestos por 20260910_coa_cfdi_emitidos.sql.
*/
SET XACT_ABORT ON;

BEGIN TRY
    BEGIN TRANSACTION;

    IF OBJECT_ID('dbo.COA_ExpedienteReferencias','U') IS NULL
        THROW 51000, 'PRECONDITION: falta dbo.COA_ExpedienteReferencias', 1;

    IF OBJECT_ID('dbo.CK_COA_ExpedienteReferencias_UnSoloDestino','C') IS NOT NULL
        ALTER TABLE dbo.COA_ExpedienteReferencias DROP CONSTRAINT CK_COA_ExpedienteReferencias_UnSoloDestino;

    IF EXISTS (SELECT 1 FROM sys.indexes WHERE object_id=OBJECT_ID('dbo.COA_ExpedienteReferencias') AND name='IX_COA_ExpedienteReferencias_DocumentoFiscalEmitido')
        DROP INDEX IX_COA_ExpedienteReferencias_DocumentoFiscalEmitido ON dbo.COA_ExpedienteReferencias;

    IF EXISTS (SELECT 1 FROM sys.indexes WHERE object_id=OBJECT_ID('dbo.COA_ExpedienteReferencias') AND name='IX_COA_ExpedienteReferencias_Venta')
        DROP INDEX IX_COA_ExpedienteReferencias_Venta ON dbo.COA_ExpedienteReferencias;

    IF OBJECT_ID('dbo.FK_COA_ExpedienteReferencias_DocumentoFiscalEmitido','F') IS NOT NULL
        ALTER TABLE dbo.COA_ExpedienteReferencias DROP CONSTRAINT FK_COA_ExpedienteReferencias_DocumentoFiscalEmitido;

    IF OBJECT_ID('dbo.FK_COA_ExpedienteReferencias_Venta','F') IS NOT NULL
        ALTER TABLE dbo.COA_ExpedienteReferencias DROP CONSTRAINT FK_COA_ExpedienteReferencias_Venta;

    IF COL_LENGTH('dbo.COA_ExpedienteReferencias','DocumentoFiscalEmitidoID') IS NOT NULL
        ALTER TABLE dbo.COA_ExpedienteReferencias DROP COLUMN DocumentoFiscalEmitidoID;

    IF COL_LENGTH('dbo.COA_ExpedienteReferencias','VentaID') IS NOT NULL
        ALTER TABLE dbo.COA_ExpedienteReferencias DROP COLUMN VentaID;

    ALTER TABLE dbo.COA_ExpedienteReferencias ADD CONSTRAINT CK_COA_ExpedienteReferencias_UnSoloDestino CHECK (
        (CASE WHEN ClienteID IS NULL THEN 0 ELSE 1 END) +
        (CASE WHEN ProveedorID IS NULL THEN 0 ELSE 1 END) +
        (CASE WHEN DocumentoFiscalID IS NULL THEN 0 ELSE 1 END) +
        (CASE WHEN PagoID IS NULL THEN 0 ELSE 1 END) +
        (CASE WHEN DecisionPagoID IS NULL THEN 0 ELSE 1 END) +
        (CASE WHEN NominaID IS NULL THEN 0 ELSE 1 END) +
        (CASE WHEN DispersionNominaID IS NULL THEN 0 ELSE 1 END) +
        (CASE WHEN NominaReciboID IS NULL THEN 0 ELSE 1 END) +
        (CASE WHEN ColaboradorID IS NULL THEN 0 ELSE 1 END) +
        (CASE WHEN ContratoID IS NULL THEN 0 ELSE 1 END) = 1
    );

    IF OBJECT_ID('dbo.Fiscal_DocumentosEmitidos','U') IS NOT NULL
        DROP TABLE dbo.Fiscal_DocumentosEmitidos;

    IF OBJECT_ID('dbo.Fiscal_DocumentosEmitidosEstatus','U') IS NOT NULL
        DROP TABLE dbo.Fiscal_DocumentosEmitidosEstatus;

    COMMIT TRANSACTION;
END TRY
BEGIN CATCH
    IF XACT_STATE() <> 0 ROLLBACK TRANSACTION;
    THROW;
END CATCH;
