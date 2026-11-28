/*
COA Gate 6D - DESIGN ONLY
Rollback conservador del seed canonico.
*/
SET NOCOUNT ON;
SET XACT_ABORT ON;

IF OBJECT_ID('dbo.Fiscal_DocumentosEmitidosEstatus','U') IS NULL
    THROW 51010, 'COA_GATE6D_TARGET_TABLE_MISSING', 1;

IF EXISTS (
    SELECT 1
    FROM dbo.Fiscal_DocumentosEmitidos d
    WHERE d.EstatusDocumentoFiscalEmitidoID IN (1,2,3,4,5,6)
)
    THROW 51011, 'COA_GATE6D_ROLLBACK_REFERENCED_ROWS', 1;

DELETE FROM dbo.Fiscal_DocumentosEmitidosEstatus
WHERE
    (EstatusDocumentoFiscalEmitidoID=1 AND Codigo='BORRADOR') OR
    (EstatusDocumentoFiscalEmitidoID=2 AND Codigo='PENDIENTE_TIMBRADO') OR
    (EstatusDocumentoFiscalEmitidoID=3 AND Codigo='TIMBRADO') OR
    (EstatusDocumentoFiscalEmitidoID=4 AND Codigo='ERROR_TIMBRADO') OR
    (EstatusDocumentoFiscalEmitidoID=5 AND Codigo='CANCELACION_SOLICITADA') OR
    (EstatusDocumentoFiscalEmitidoID=6 AND Codigo='CANCELADO');
