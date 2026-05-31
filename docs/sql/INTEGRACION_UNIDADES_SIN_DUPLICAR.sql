-- ======================================================================================
-- SCRIPT DE BASE DE DATOS: INTEGRACION_UNIDADES_SIN_DUPLICAR.sql
-- PROYECTO: EDARSA HUB ERP - EVITAR DUPLICIDAD DE CATÁLOGOS
-- MOTOR: SQL Server 2012+ (Base de datos: EDARSAHUB)
-- ======================================================================================

USE [EDARSAHUB];
GO

BEGIN TRANSACTION;
BEGIN TRY

    -- 1. Si la tabla de unidades ya existe, solo nos aseguramos de que tenga los campos de KPIs
    --    comerciales necesarios para el cálculo de proyecciones lineales del ERP.
    IF EXISTS (SELECT * FROM sys.tables WHERE name = 'Sync_KPI_Ventas_Unidades')
    BEGIN
        PRINT 'La tabla base de unidades ya existe. Verificando/añadiendo columnas faltantes...';
        
        IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('dbo.Sync_KPI_Ventas_Unidades') AND name = 'Ventas_Reales_M')
            ALTER TABLE dbo.Sync_KPI_Ventas_Unidades ADD Ventas_Reales_M DECIMAL(18,4) NULL;

        IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('dbo.Sync_KPI_Ventas_Unidades') AND name = 'Dias_Con_Ventas')
            ALTER TABLE dbo.Sync_KPI_Ventas_Unidades ADD Dias_Con_Ventas DECIMAL(5,2) NULL;

        IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('dbo.Sync_KPI_Ventas_Unidades') AND name = 'Proyeccion_Ventas')
            ALTER TABLE dbo.Sync_KPI_Ventas_Unidades ADD Proyeccion_Ventas DECIMAL(18,4) NULL;
            
        PRINT 'Estructuras de columnas sincronizadas con éxito.';
    END
    ELSE
    BEGIN
        PRINT 'No se detectó la tabla de sincronización. Creando bajo especificación segura...';
        -- Solo se ejecuta si es un entorno limpio; en producción usará tu tabla existente
        CREATE TABLE dbo.Sync_KPI_Ventas_Unidades (
            Unidad_Id VARCHAR(50) PRIMARY KEY,
            Nombre_Unidad VARCHAR(100) NOT NULL,
            Ventas_Reales_M DECIMAL(18,4) DEFAULT 0.0000,
            Dias_Con_Ventas DECIMAL(5,2) DEFAULT 0.0,
            Proyeccion_Ventas DECIMAL(18,4) DEFAULT 0.0000,
            Mes VARCHAR(20) DEFAULT 'Mayo',
            Anio INT DEFAULT 2026,
            UltimaActualizacion DATETIME DEFAULT GETDATE()
        );
    END

    COMMIT TRANSACTION;
    PRINT 'Transacción de alineación de base de datos confirmada de forma segura.';

END TRY
BEGIN CATCH
    ROLLBACK TRANSACTION;
    DECLARE @ErrorMsg NVARCHAR(4000) = ERROR_MESSAGE();
    PRINT 'Error al alinear las unidades de negocio comerciales: ' + @ErrorMsg;
    RAISERROR(@ErrorMsg, 16, 1);
END CATCH;
GO
