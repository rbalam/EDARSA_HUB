-- ======================================================================================
-- SCRIPT DE BASE DE DATOS: CORRECCION_PROYECCION_Y_MONEDA_FINAL.sql
-- PROYECTO: EDARSA HUB ERP - SISTEMA DE ALTA DISPONIBILIDAD COMERCIAL
-- MOTOR: Microsoft SQL Server 2012+ / Azure SQL (Base de datos: EDARSAHUB)
-- OBJETIVO: Alineación final de formato de moneda con comas ($1,062.58M) y cálculo anual (365 días)
-- EJECUCIÓN: Copiar y pegar en Consola de emergent.sh o SSMS de Producción
-- FECHA: 31 de Mayo, 2026
-- ======================================================================================

USE [EDARSAHUB];
GO

-- 1. CREACIÓN O CORRECCIÓN DE LA FUNCIÓN DE MONEDA DE ALTA FIDELIDAD CON COMAS
-- Esta función emula el formateador implementado en el frontend de React:
-- Reemplaza formatos planos (1062.58) con separadores estandarizados de miles (1,062.58)
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
        
    -- FORMAT con la máscara '#,##0.00' y la cultura 'en-US' garantiza la inserción de comas para los miles
    -- y el punto decimal correcto de alta definición, ej: 1062.58 -> $1,062.58M
    RETURN '$' + FORMAT(@Valor, '#,##0.00', 'en-US') + 'M';
END
GO


-- 2. CALIBRACIÓN DE LA FUNCIÓN DE PROYECCIÓN ANUAL (365 DÍAS)
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
        
    -- Proyección lineal matemática calibrada para el año completo (365 días corporativos)
    RETURN (@VentasRealesM / CAST(@DiasConVentas AS DECIMAL(18,4))) * 365.0000;
END
GO


-- 3. PROCESAMIENTO SEGURO TRANSACCIONAL PARA LA CORRECCIÓN EN PRODUCCIÓN
BEGIN TRANSACTION;

BEGIN TRY
    PRINT 'Iniciando corrección y normalización de KPIs en base de datos...';

    -- Parámetros del periodo actual de reporte (Enero / Mayo 2026)
    DECLARE @DiasSLA INT = 31;
    
    -- Si la tabla de KPIs ya existe en producción, se procede a indexar y actualizar
    IF OBJECT_ID('dbo.Sync_KPI_Ventas_Unidades', 'U') IS NOT NULL
    BEGIN
        -- Actualizar la columna correspondiente con la fórmula de 365 días reales
        UPDATE [dbo].[Sync_KPI_Ventas_Unidades]
        SET 
            -- Aplicación física de la proyección corregida
            Proyeccion_Anual_Ventas = dbo.fn_CalcularProyeccionAnual365(Ventas_Reales_M, @DiasSLA),
            UltimaActualizacion = GETDATE();
            
        PRINT 'Unidades de negocio actualizadas de forma matemática con éxito.';
    END
    ELSE
    BEGIN
        PRINT 'Aviso: Tabla de producción física Sync_KPI_Ventas_Unidades no configurada aún en este servidor local. Se valida la compilación lógica.';
    END

    -- 4. Registrar suceso en la bitácora histórica de auditoría (Sync_Logs)
    IF OBJECT_ID('dbo.Sync_Logs', 'U') IS NOT NULL
    BEGIN
        INSERT INTO dbo.Sync_Logs (service, type, message, timestamp, operador)
        VALUES (
            'CORRECCION_PROYECCION_Y_MONEDA_FINAL', 
            'SUCCESS', 
            N'Implementación de formateador monetario de alta fidelidad con comas ($1,062.58M) y calibración del KPI de proyección anual (365 días) en base de datos de producción.', 
            GETDATE(),
            N'SISTEMA_ADMINISTRATIVO_PRIME'
        );
    END

    -- Confirmar todos los cambios en producción de forma definitiva
    COMMIT TRANSACTION;
    PRINT 'TRANSACCIÓN CONFIRMADA: Base de datos alineada al 100% con los formatos de comas y cálculos de React.';

END TRY
BEGIN CATCH
    -- En caso de error, abortar para mantener la integridad operativa del sistema
    ROLLBACK TRANSACTION;
    
    DECLARE @ErrorMsg NVARCHAR(4000) = ERROR_MESSAGE();
    PRINT 'Fallo crítico durante la ejecución de correcciones en caliente.';
    PRINT 'Mensaje Técnico: ' + @ErrorMsg;
    
    IF OBJECT_ID('dbo.Sync_Logs', 'U') IS NOT NULL
    BEGIN
        INSERT INTO dbo.Sync_Logs (service, type, message, timestamp, operador)
        VALUES ('CORRECCION_PROYECCION_Y_MONEDA_FINAL', 'ERROR', N'Aborting: ' + @ErrorMsg, GETDATE(), N'SISTEMA_FALLBACK');
    END

    -- Relanzar el error para control del operador
    THROW;
END CATCH
GO

-- 5. DEMO DE CONTROL DE CALIDAD (QA) EN COLA DE SALIDA
-- Ejecuta esta consulta para validar que el formateador con comas aplique correctamente
DECLARE @DemoValor DECIMAL(18,4) = 1062.58;
SELECT 
    @DemoValor AS [Valor Plano],
    dbo.fn_FormatearMonedaConComas(@DemoValor) AS [Formateado Con Comas (EDARSA Standard)],
    dbo.fn_CalcularProyeccionAnual365(@DemoValor, 31) AS [Proyección 365 días ($M)];
GO
