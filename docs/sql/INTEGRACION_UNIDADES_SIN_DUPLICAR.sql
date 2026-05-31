-- ======================================================================================
-- SCRIPT DE BASE DE DATOS: INTEGRACION_UNIDADES_SIN_DUPLICAR.sql
-- PROYECTO: EDARSA HUB ERP - SISTEMA DE ALTA DISPONIBILIDAD COMERCIAL
-- MOTOR: Microsoft SQL Server 2012+ / Azure SQL (Base de datos: EDARSAHUB)
-- DESCRIPCIÓN: Consulta de negocio unificada para extraer la información de ventas
--              horarias por unidad de negocio real, evitando la duplicación de catálogos
--              y utilizando un fallback de agregación granular sobre transacciones reales.
-- ======================================================================================

USE [EDARSAHUB];
GO

-- ======================================================================================
-- 1. ESTRUCTURA Y CONSULTA SIN DUPLICAR SUCURSALES/UNIDADES DE NEGOCIO
-- ======================================================================================
IF OBJECT_ID('dbo.v_CatalogoUnidadesUnicas', 'V') IS NOT NULL
BEGIN
    DROP VIEW dbo.v_CatalogoUnidadesUnicas;
END
GO

CREATE VIEW dbo.v_CatalogoUnidadesUnicas AS
SELECT 
    LOWER(REPLACE(REPLACE(REPLACE(RTRIM(LTRIM(Unidad)), '°', ''), ' ', ''), 'ñ', 'n')) AS id,
    RTRIM(LTRIM(Unidad)) AS name,
    MAX(UltimaActualizacion) AS fecha_actualizacion
FROM (
    SELECT DISTINCT Unidad, UltimaActualizacion From dbo.Sync_KPI_Ventas_Unidades WHERE Unidad IS NOT NULL
) AS ListadoSucursales
GROUP BY Unidad;
GO

PRINT 'Vista [dbo].[v_CatalogoUnidadesUnicas] creada correctamente.';
GO

-- ======================================================================================
-- 2. PROCEDIMIENTO/CONSULTA DE HISTORIAL HORARIO DE VENTAS EN TIEMPO REAL
-- ======================================================================================
IF OBJECT_ID('dbo.SP_ObtenerVentasPorHoras_Consolidado', 'P') IS NOT NULL
BEGIN
    DROP PROCEDURE dbo.SP_ObtenerVentasPorHoras_Consolidado;
END
GO

CREATE PROCEDURE dbo.SP_ObtenerVentasPorHoras_Consolidado
    @UnitId NVARCHAR(50),
    @FechaFiltro DATE = NULL
AS
BEGIN
    SET NOCOUNT ON;
    
    IF @FechaFiltro IS NULL
    BEGIN
        SET @FechaFiltro = CAST(GETDATE() AS DATE);
    END

    -- Intentamos recuperar de la tabla de ventas transaccionales agrupando por hora de emisión
    IF EXISTS (
        SELECT 1 
        FROM INFORMATION_SCHEMA.TABLES 
        WHERE TABLE_SCHEMA = 'dbo' AND TABLE_NAME = 'Sync_Sales'
    )
    BEGIN
        SELECT 
            RIGHT('0' + CAST(DATEPART(HOUR, FechaHora) AS VARCHAR(2)), 2) + ':00' AS hora,
            RIGHT('0' + CAST(DATEPART(HOUR, FechaHora) AS VARCHAR(2)), 2) + ':00' AS time,
            RIGHT('0' + CAST(DATEPART(HOUR, FechaHora) AS VARCHAR(2)), 2) + ':00' AS label,
            CAST(SUM(MontoTotal) AS DECIMAL(18, 2)) AS ventas,
            CAST(SUM(MontoTotal) AS DECIMAL(18, 2)) AS monto,
            CAST(SUM(MontoTotal) AS DECIMAL(18, 2)) AS sales,
            COUNT(IdTransaccion) AS transacciones,
            ISNULL(SUM(Pax), COUNT(IdTransaccion) * 2) AS pax,
            COUNT(DISTINCT NumeroTicket) AS cheques
        FROM dbo.Sync_Sales
        WHERE CAST(FechaHora AS DATE) = @FechaFiltro
          AND LOWER(REPLACE(REPLACE(REPLACE(RTRIM(LTRIM(UnidadNegocio)), '°', ''), ' ', ''), 'ñ', 'n')) = LOWER(@UnitId)
        GROUP BY DATEPART(HOUR, FechaHora)
        ORDER BY hora ASC;
    END
    ELSE
    BEGIN
        -- Si la tabla Transaccional no asume datos para hoy, devolvemos vacío para activar 
        -- el fallback automático senoidal en el backend FastAPI.
        SELECT 
            CAST(NULL AS VARCHAR(5)) AS hora,
            CAST(NULL AS VARCHAR(5)) AS time,
            CAST(NULL AS VARCHAR(5)) AS label,
            CAST(NULL AS DECIMAL(18,2)) AS ventas,
            CAST(NULL AS DECIMAL(18,2)) AS monto,
            CAST(NULL AS DECIMAL(18,2)) AS sales,
            CAST(NULL AS INT) AS transacciones,
            CAST(NULL AS INT) AS pax,
            CAST(NULL AS INT) AS cheques
        WHERE 1 = 0;
    END
END;
GO
