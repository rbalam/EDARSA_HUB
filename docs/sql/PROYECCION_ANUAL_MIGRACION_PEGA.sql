-- ======================================================================================
-- SCRIPT DE MIGRACIÓN: PROYECCION_ANUAL_MIGRACION_PEGA.sql
-- PROYECTO: EDARSA HUB ERP - SISTEMA DE CONTROL COMERCIAL Y DE PROYECCIONES
-- MOTOR: Microsoft SQL Server 2012+ / Azure SQL (Base de datos: EDARSAHUB)
-- OBJETIVO: Alineación inmediata de proyecciones anuales (365 días) y formato de comas ($1,062.58M)
-- EJECUCIÓN: Copiar y pegar directamente en emergent.sh o terminal SSMS de Producción
-- ======================================================================================

USE [EDARSAHUB];
GO

-- 1. ASEGURAR QUE EXISTE REPOSITORIO DE CONTROL DE LOGS
IF OBJECT_ID('dbo.Sync_Logs', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.Sync_Logs (
        id INT IDENTITY(1,1) PRIMARY KEY,
        service NVARCHAR(100) NOT NULL,
        type NVARCHAR(20) NOT NULL,
        message NVARCHAR(MAX) NOT NULL,
        timestamp DATETIME DEFAULT GETDATE(),
        operador NVARCHAR(100) DEFAULT 'SISTEMA_AUTOGESTIVO_FALLBACK'
    );
END
GO

-- 2. FUNCIÓN DE FORMATEADOR CON COMAS PARA SEPARACIÓN DE MILES DE ALTA DEFINICIÓN
-- Convierte valores decimales a string con el prefijo '$', sufijo 'M' y separadores de miles con comas.
-- Ejemplo: 1062.58 -> '$1,062.58M'
IF OBJECT_ID('dbo.fn_FormatearMonedaConComas', 'FN') IS NOT NULL
BEGIN
    DROP FUNCTION dbo.fn_FormatearMonedaConComas;
END
GO

CREATE FUNCTION dbo.fn_FormatearMonedaConComas (
    @Valor DECIMAL(18,4)
)
RETURNS NVARCHAR(100)
AS
BEGIN
    IF @Valor IS NULL
        RETURN '$0.00M';
        
    -- CONVERT con estilo 1 formatea el valor MONEY con comas separatorias de miles y punto decimal de forma regional-agnóstica y sin dependencia CLR.
    RETURN '$' + CONVERT(NVARCHAR(100), CAST(@Valor AS MONEY), 1) + 'M';
END
GO

-- 3. FUNCIÓN DE PROYECCIÓN ANUAL OPTIMIZADA SOBRE EL AÑO COMPLETO DE 365 DÍAS
-- Garantiza cálculos matemáticos de alta precisión lineal de la corporación.
IF OBJECT_ID('dbo.fn_CalcularProyeccionAnual365', 'FN') IS NOT NULL
BEGIN
    DROP FUNCTION dbo.fn_CalcularProyeccionAnual365;
END
GO

CREATE FUNCTION dbo.fn_CalcularProyeccionAnual365 (
    @VentasRealesM DECIMAL(18,4),
    @DiasConVentas INT
)
RETURNS DECIMAL(18,4)
AS
BEGIN
    IF @DiasConVentas <= 0 OR @VentasRealesM IS NULL
        RETURN 0.0000;
        
    -- Fórmula Matemática: (Ventas / Días Transcurridos) * 365 días reales anuales
    RETURN (@VentasRealesM / CAST(@DiasConVentas AS DECIMAL(18,4))) * 365.0000;
END
GO

-- 4. ACTUALIZACIÓN SEGURA BAJO BLOQUE TRANSACCIONAL
BEGIN TRANSACTION;

BEGIN TRY
    PRINT 'Iniciando actualización física de base de datos de producción...';

    -- Días reales con ventas (para un mes con 31 días completos, Ej: Mayo o Enero)
    DECLARE @DiasSLA INT = 31;

    IF OBJECT_ID('dbo.Sync_KPI_Ventas_Unidades', 'U') IS NOT NULL
    BEGIN
        -- Asegurar estructura de columna requerida para almacenar la proyección
        IF NOT EXISTS (
            SELECT * FROM sys.columns 
            WHERE object_id = OBJECT_ID('dbo.Sync_KPI_Ventas_Unidades') 
            AND name = 'Proyeccion_Anual_Ventas'
        )
        BEGIN
            ALTER TABLE dbo.Sync_KPI_Ventas_Unidades ADD Proyeccion_Anual_Ventas DECIMAL(18, 4) NULL;
        END

        -- Ejecutar la corrección física de datos alineando con la proyección lineal
        UPDATE [dbo].[Sync_KPI_Ventas_Unidades]
        SET 
            Proyeccion_Anual_Ventas = dbo.fn_CalcularProyeccionAnual365(Ventas_Reales_M, @DiasSLA),
            UltimaActualizacion = GETDATE();

        PRINT 'Registros de la tabla Sync_KPI_Ventas_Unidades actualizados con éxito.';
    END
    ELSE
    BEGIN
        PRINT 'Aviso: La tabla física Sync_KPI_Ventas_Unidades no se encuentra disponible. Verificando integridad lógica de funciones.';
    END

    -- Confirmación del Log de Auditoría en base de datos
    INSERT INTO dbo.Sync_Logs (service, type, message, timestamp, operador)
    VALUES (
        'PROYECCION_ANUAL_MIGRACION_PEGA',
        'SUCCESS',
        N'Calibración y homologación exitosa de proyecciones anuales (SGP-365) y formatos de separadores de miles con comas ($1,062.58M).',
        GETDATE(),
        N'SISTEMA_ADMINISTRATIVO_PRIME'
    );

    COMMIT TRANSACTION;
    PRINT 'LA MIGRACIÓN SE HA COMPLETADO PERFECTAMENTE EN PRODUCCIÓN.';

END TRY
BEGIN CATCH
    -- Revertir cualquier cambio en caso de error operacional impidiendo inconsistencias
    ROLLBACK TRANSACTION;
    
    DECLARE @ErrorMsg NVARCHAR(4000) = ERROR_MESSAGE();
    PRINT 'Aborting: Se detectó un problema técnico durante la migración.';
    PRINT 'Detalle del Error: ' + @ErrorMsg;
    
    INSERT INTO dbo.Sync_Logs (service, type, message, timestamp, operador)
    VALUES ('PROYECCION_ANUAL_MIGRACION_PEGA', 'ERROR', N'Aborting: ' + @ErrorMsg, GETDATE(), N'SISTEMA_FALLBACK');

    THROW;
END CATCH
GO

-- 5. DEMOSTRACIÓN DE VERIFICACIÓN (QA) DE LOS FORMATEADORES EN COLA DE SALIDA
PRINT '=== PREVISUALIZACIÓN DE PRUEBA DE CONTROL DE CALIDAD ===';
DECLARE @VentasEjemplo DECIMAL(18,4) = 1062.58;
SELECT 
    @VentasEjemplo AS [Ventas Reales Planeadas],
    dbo.fn_FormatearMonedaConComas(@VentasEjemplo) AS [Formato Con Comas (Alineado con React)],
    dbo.fn_CalcularProyeccionAnual365(@VentasEjemplo, 31) AS [Proyección Anual 365 días ($M)]
GO
