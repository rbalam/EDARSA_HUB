-- ======================================================================================
-- SCRIPT DE BASE DE DATOS: ACTUALIZACION_KPI_PROYECCION_COMERCIAL.sql
-- PROYECTO: EDARSA HUB ERP - SISTEMA DE ALTA DISPONIBILIDAD COMERCIAL
-- MOTOR: Microsoft SQL Server 2019+ / Azure SQL (Base de datos: EDARSAHUB)
-- DESCRIPCIÓN: Actualiza el cálculo de proyección de ventas con la fórmula lineal
--              corregida: (Ventas Reales / Días con Ventas) * Días Totales del Mes.
-- ======================================================================================

USE [EDARSAHUB];
GO

-- Iniciamos bloque transaccional para garantizar consistencia absoluta
BEGIN TRANSACTION;

BEGIN TRY

    -- 1. Declaración de Variables Auxiliares Ajustables (Parámetros)
    DECLARE @MesSeleccionado NVARCHAR(20) = N'Mayo';
    DECLARE @AnioSeleccionado INT = 2026;
    DECLARE @DiasConVentas DECIMAL(18, 4) = 30.0000; -- Días transcurridos con actividad real

    -- 2. Traducción de nombre de mes a número índice (1-12)
    DECLARE @NumeroMes INT = 
        CASE LOWER(LTRIM(RTRIM(@MesSeleccionado)))
            WHEN 'enero'      THEN 1
            WHEN 'febrero'    THEN 2
            WHEN 'marzo'      THEN 3
            WHEN 'abril'      THEN 4
            WHEN 'mayo'       THEN 5
            WHEN 'junio'      THEN 6
            WHEN 'julio'      THEN 7
            WHEN 'agosto'     THEN 8
            WHEN 'septiembre' THEN 9
            WHEN 'oktubre'    THEN 10
            WHEN 'noviembre'  THEN 11
            WHEN 'diciembre'  THEN 12
            ELSE MONTH(GETDATE()) -- fallback al mes en curso
        END;

    -- 3. Cálculo Dinámico de Días Calendario de ese Mes y Año (Soporta Años Bisiestos)
    DECLARE @DiasTotales DECIMAL(18, 4) = CAST(DAY(EOMONTH(DATEFROMPARTS(@AnioSeleccionado, @NumeroMes, 1))) AS DECIMAL(18, 4));

    -- 4. Verificación de existencia de las tablas y actualización de registros
    IF OBJECT_ID('dbo.Sync_KPI_Ventas_Unidades', 'U') IS NOT NULL
    BEGIN
        -- Actualización del KPI en la tabla directa de reporte de EDARSA HUB
        UPDATE [dbo].[Sync_KPI_Ventas_Unidades]
        SET 
            -- Aplicación formal de la fórmula lineal corregida con días dinámicos
            Proyeccion_Ventas = CAST((Ventas_Reales_M / NULLIF(@DiasConVentas, 0)) * @DiasTotales AS DECIMAL(18, 4)),
            UltimaActualizacion = GETDATE()
        WHERE 
            Mes = @MesSeleccionado AND Anio = @AnioSeleccionado;

        -- Registrar éxito en la bitácora central de auditoría de EDARSA HUB
        IF OBJECT_ID('dbo.Sync_Logs', 'U') IS NOT NULL
        BEGIN
            INSERT INTO dbo.Sync_Logs (service, type, message, timestamp)
            VALUES (
                'CORRECCION_KPI_PROYECCION', 
                'SUCCESS', 
                CONCAT('SQL Script de Corrección de KPI aplicado con éxito para ', @MesSeleccionado, ' ', CAST(@AnioSeleccionado AS VARCHAR(4)), ' (Días con ventas: ', CAST(CAST(@DiasConVentas AS INT) AS VARCHAR(2)), ', Días Totales del Mes: ', CAST(CAST(@DiasTotales AS INT) AS VARCHAR(2)), ').'), 
                GETDATE()
            );
        END

        PRINT 'Metodología corregida y guardada para dbo.Sync_KPI_Ventas_Unidades.';
    END
    ELSE
    BEGIN
        PRINT 'Advertencia: Tabla [Sync_KPI_Ventas_Unidades] no encontrada en esta instancia. Asegúrese de estar en el contexto de EDARSAHUB.';
    END

    -- Confirmación segura de la transacción si todo se ejecuta correctamente
    COMMIT TRANSACTION;
    PRINT 'Transacción confirmada exitosamente. Todos los cambios se han guardado.';

END TRY
BEGIN CATCH
    -- Deshacer cambios inmediatamente ante cualquier fallo imprevisto
    ROLLBACK TRANSACTION;
    
    DECLARE @ErrorMsg NVARCHAR(4000) = ERROR_MESSAGE();
    DECLARE @ErrorSeverity INT = ERROR_SEVERITY();
    DECLARE @ErrorState INT = ERROR_STATE();
    
    PRINT 'ERROR DETECTADO: ' + @ErrorMsg;
    
    -- Registrar fallo en la bitácora si existe la tabla
    IF OBJECT_ID('dbo.Sync_Logs', 'U') IS NOT NULL
    BEGIN
        INSERT INTO dbo.Sync_Logs (service, type, message, timestamp)
        VALUES ('CORRECCION_KPI_PROYECCION', 'ERROR', 'Fallo al aplicar corrección de KPI: ' + @ErrorMsg, GETDATE());
    END

    RAISERROR(@ErrorMsg, @ErrorSeverity, @ErrorState);
END CATCH
GO
