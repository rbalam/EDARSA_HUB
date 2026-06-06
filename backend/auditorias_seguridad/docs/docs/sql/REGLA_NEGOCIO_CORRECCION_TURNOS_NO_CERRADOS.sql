-- =========================================================================
-- SCRIPT: REGLA DE NEGOCIO DEFINITIVA - CORRECCIÓN DE TURNOS NO CERRADOS
-- ENTIDAD: EDARSA HUB CENTRAL (PIPELINE DE VERACIDAD TRANSACCIONAL)
-- CRITERIO: Fecha de registro individual con ventana de arrastre nocturno (00h-07h)
-- =========================================================================

SET NOCOUNT ON;
SET TRANSACTION ISOLATION LEVEL READ UNCOMMITTED;

DECLARE @InicioMes DATE = DATEADD(MONTH, DATEDIFF(MONTH, 0, GETDATE()), 0); -- 2026-05-01
DECLARE @FechaHoy DATE = CAST(GETDATE() AS DATE);
DECLARE @Ayer DATE = DATEADD(DAY, -1, @FechaHoy);

WITH Cat_Unidades_Negocio AS (
    SELECT 'CIENFUEGOS' AS Unidad, 'RESTAURANTE' AS Tipo_Giro UNION ALL
    SELECT 'ORIGEN', 'RESTAURANTE' UNION ALL
    SELECT '130° MERIDA', 'RESTAURANTE' UNION ALL
    SELECT '130° QUERETARO', 'RESTAURANTE' UNION ALL
    SELECT 'LA ESTELAR', 'RESTAURANTE'
),

-- 🔍 PASO 1: FISCALIZACIÓN Y REUBICACIÓN CRÍTICA DE TICKETS
-- Desembrollamos los turnos eternos usando la estampa de tiempo real de cada transacción.
Tickets_Fecha_Operativa_Calculada AS (
    SELECT 
        t.id_ticket,
        UPPER(TRIM(t.nombre_unidad)) AS Unidad,
        t.total_neto,
        t.pax_cuenta,
        t.status_ticket,
        t.fecha_registro_ticket, -- Timestamp real de la impresión/creación del ticket
        CAST(t.fecha_registro_ticket AS TIME) AS Hora_Registro,
        
        -- REGLA MAESTRA AN TI-NEGLIGENCIA:
        -- Si el ticket se emitió entre las 00:00 AM y las 06:59 AM, pertenece a la "cena" del día anterior.
        -- Si se emitió después de las 07:00 AM, pertenece al día calendario en curso.
        CASE 
            WHEN CAST(t.fecha_registro_ticket AS TIME) BETWEEN '00:00:00' AND '06:59:59'
            THEN CAST(DATEADD(DAY, -1, t.fecha_registro_ticket) AS DATE)
            ELSE CAST(t.fecha_registro_ticket AS DATE)
        END AS Fecha_Operativa_Real,
        
        -- Segmentación exacta por horario de consumo real
        CASE 
            WHEN CAST(t.fecha_registro_ticket AS TIME) BETWEEN '07:00:00' AND '13:00:00' THEN 'DESAYUNO'
            WHEN CAST(t.fecha_registro_ticket AS TIME) BETWEEN '13:00:01' AND '19:00:00' THEN 'COMIDA'
            ELSE 'CENA / TRASNOCHADO'
        END AS Bloque_Servicio
    FROM EDARSA_HUB_SQL.dbo.STG_Tickets_Transaccionales t
    INNER JOIN Cat_Unidades_Negocio cat ON UPPER(TRIM(t.nombre_unidad)) = cat.Unidad
    WHERE t.fecha_registro_ticket BETWEEN @InicioMes AND GETDATE()
),

-- 🔍 PASO 2: CONSOLIDACIÓN ACUMULADA HISTÓRICA (D-1)
Kpi_Historico_Blindado AS (
    SELECT 
        Unidad,
        SUM(total_neto) AS Venta_Historica_Acumulada,
        SUM(pax_cuenta) AS PAX_Historico,
        COUNT(id_ticket) AS Cheques_Historicos
    FROM Tickets_Fecha_Operativa_Calculada
    WHERE Fecha_Operativa_Real BETWEEN @InicioMes AND @Ayer
      AND status_ticket = 'CERRADO'
    GROUP BY Unidad
),

-- 🔍 PASO 3: FLUJO DEL TURNO ACTIVO DE HOY
Kpi_Jornada_Actual AS (
    SELECT 
        Unidad,
        SUM(CASE WHEN status_ticket = 'CERRADO' THEN total_neto ELSE 0 END) AS Venta_Hoy_Cerrada,
        SUM(CASE WHEN status_ticket = 'ABIERTO' THEN total_neto ELSE 0 END) AS Venta_Hoy_Mesas_Vivas,
        
        -- Desglose para vigilar el comportamiento del día
        SUM(CASE WHEN Bloque_Servicio = 'DESAYUNO' THEN total_neto ELSE 0 END) AS Flujo_Desayuno,
        SUM(CASE WHEN Bloque_Servicio = 'COMIDA' THEN total_neto ELSE 0 END) AS Flujo_Comida,
        SUM(CASE WHEN Bloque_Servicio = 'CENA / TRASNOCHADO' THEN total_neto ELSE 0 END) AS Flujo_Cena
    FROM Tickets_Fecha_Operativa_Calculada
    WHERE Fecha_Operativa_Real = @FechaHoy
    GROUP BY Unidad
)

-- 📊 REPORTE DE SOBERANÍA MATRICIAL (TABLERO EJECUTIVO V3)
SELECT 
    h.Unidad AS [Unidad de Negocio],
    
    -- DATOS AUDITADOS CON VENTANA DE TIEMPO AJUSTADA (D-1)
    ISNULL(h.Venta_Historica_Acumulada, 0) AS [1. Venta Histórica Real (1 al Día Anterior)],
    ISNULL(h.PAX_Historico, 0) AS [PAX Hist. Acum],
    ISNULL(h.Cheques_Historicos, 0) AS [Cheques Hist. Acum],
    
    -- OPERACIÓN DEL DÍA EN CURSO (VIVO)
    ISNULL(v.Venta_Hoy_Cerrada, 0) AS [2. Venta Cerrada Hoy],
    ISNULL(v.Venta_Hoy_Mesas_Vivas, 0) AS [3. Cuentas Abiertas en Mesa],
    
    -- INDICADORES OPERATIVOS REUBICADOS
    ISNULL(v.Flujo_Desayuno, 0) AS [Desayunos (07-13h)],
    ISNULL(v.Flujo_Comida, 0) AS [Comidas (13-19h)],
    ISNULL(v.Flujo_Cena, 0) AS [Cenas / Trasnochados (19h-07h)],
    
    -- TOTALIZADOR GRUPO EDARSA
    (ISNULL(h.Venta_Historica_Acumulada, 0) + ISNULL(v.Venta_Hoy_Cerrada, 0)) AS [KPI CONTABLE TOTAL MES]
FROM Kpi_Historico_Blindado h
LEFT JOIN Kpi_Jornada_Actual v ON h.Unidad = v.Unidad;
