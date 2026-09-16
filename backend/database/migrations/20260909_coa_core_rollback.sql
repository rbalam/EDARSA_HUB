SET XACT_ABORT ON;

BEGIN TRY
    BEGIN TRANSACTION;

    IF EXISTS (SELECT 1 FROM dbo.COA_ComisionAplicada) OR
       EXISTS (SELECT 1 FROM dbo.COA_ExcepcionesRegla) OR
       EXISTS (SELECT 1 FROM dbo.COA_ReglasComisionCondiciones) OR
       EXISTS (SELECT 1 FROM dbo.COA_ReglasComision) OR
       EXISTS (SELECT 1 FROM dbo.COA_ExpedienteReferencias) OR
       EXISTS (SELECT 1 FROM dbo.COA_ExpedienteEventos) OR
       EXISTS (SELECT 1 FROM dbo.COA_Expedientes)
        THROW 51001, 'COA_ROLLBACK_REFUSED_NONEMPTY_TABLES', 1;

    IF OBJECT_ID('dbo.COA_ComisionAplicada','U') IS NOT NULL DROP TABLE dbo.COA_ComisionAplicada;
    IF OBJECT_ID('dbo.COA_ExcepcionesRegla','U') IS NOT NULL DROP TABLE dbo.COA_ExcepcionesRegla;
    IF OBJECT_ID('dbo.COA_ReglasComisionCondiciones','U') IS NOT NULL DROP TABLE dbo.COA_ReglasComisionCondiciones;
    IF OBJECT_ID('dbo.COA_ReglasComision','U') IS NOT NULL DROP TABLE dbo.COA_ReglasComision;
    IF OBJECT_ID('dbo.COA_ExpedienteReferencias','U') IS NOT NULL DROP TABLE dbo.COA_ExpedienteReferencias;
    IF OBJECT_ID('dbo.COA_ExpedienteEventos','U') IS NOT NULL DROP TABLE dbo.COA_ExpedienteEventos;
    IF OBJECT_ID('dbo.COA_Expedientes','U') IS NOT NULL DROP TABLE dbo.COA_Expedientes;

    COMMIT TRANSACTION;
END TRY
BEGIN CATCH
    IF @@TRANCOUNT > 0 ROLLBACK TRANSACTION;
    THROW;
END CATCH;
