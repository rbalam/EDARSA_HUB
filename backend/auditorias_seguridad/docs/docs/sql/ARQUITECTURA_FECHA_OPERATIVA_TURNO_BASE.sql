-- =========================================================================
-- SCRIPT: ARQUITECTURA DE FECHA OPERATIVA Y CLASIFICACIÓN POR APERTURA DE TURNO
-- ENTIDAD: EDARSA HUB MULTI-UNIDAD (MOTOR: SQL SERVER)
-- REGLA DE NEGOCIO: SOBERANÍA DEL TURNO BASE (IGNORA FECHA CALENDARIO Y CIERRE)
-- =========================================================================

SET NOCOUNT ON;
SET TRANSACTION ISOLATION LEVEL READ UNCOMMITTED;

DECLARE @FechaHoy DATE = CAST(GETDATE() AS DATE);
DECLARE @InicioMes DATE = DATEADD(MONTH, DATEDIFF(MONTH, 0, GETDATE()), 0); -- 2026-05-01
DECLARE @Ayer DATE = DATEADD(DAY, -1, @FechaHoy);                          -- 2026-05-28

-- 🔍 PASO 1: AGREGACIÓN DE SEGMENTOS OPERATIVOS Y CATALOGACIÓN DE EMPRESA
-- Separamos los giros comerciales porque EDARSA HUB no solo consolida restaurantes.
WITH Cat_Unidades_Negocio AS (
    SELECT 'CIENFUEGOS' AS Unidad, 'RESTAURANTE' AS Tipo_Giro UNION ALL
    SELECT 'ORIGEN', 'RESTAURANTE' UNION ALL
    SELECT '130° MERIDA', 'RESTAURANTE' UNION ALL
    SELECT '130° QUERETARO', 'RESTAURANTE' UNION ALL
    SELECT 'LA ESTELAR', 'RESTAURANTE'
),

-- 🔍 PASO 2: EXTRACCIÓN Y NORMALIZACIÓN DE TRANSACCIONES VIVAS Y RECIENTES
-- Aplicamos las sub-reglas de horarios asignando el dinero por la Apertura del Turno.
Pipeline_Master_Normalizado AS (
    SELECT 
        t.id_ticket,
        cat.Tipo_Giro,
        UPPER(TRIM(t.nombre_unidad)) AS Unidad,
        
        -- CRÍTICO: La fecha real contable es el día en que se abrió el TURNO de la caja,
        -- NO la fecha de la computadora al cerrar la cuenta, ni la fecha del corte físico.
        CAST(t.fecha_apertura_turno AS DATE) AS Fecha_Operativa_Real,
        
        -- Mapeo estricto del bloque de servicio según la hora de inicio de la transacción
        CASE 
            WHEN CAST(t.hora_apertura_cuenta AS TIME) BETWEEN '07:00:00' AND '13:00:00' THEN 'DESAYUNO'
            WHEN CAST(t.hora_apertura_cuenta AS TIME) BETWEEN '13:00:01' AND '19:00:00' THEN 'COMIDA'
            ELSE 'CENA / CIERRE NOCTURNO'
        END AS Bloque_Servicio,
        
        t.total_neto,
        t.pax_cuenta,
        t.status_ticket -- 'CERRADO', 'ABIERTO', 'CANCELADO'
    FROM EDARSA_HUB_SQL.dbo.STG_Tickets_Transaccionales t
    INNER JOIN Cat_Unidades_Negocio cat ON UPPER(TRIM(t.nombre_unidad)) = cat.Unidad
    WHERE CAST(t.fecha_apertura_turno AS DATE) BETWEEN @InicioMes AND @FechaHoy
),

-- 🔍 PASO 3: CONSOLIDACIÓN DE KPI HISTÓRICO HARD DATA (D-1 HASTA EL INICIO DE MES)
-- Datos congelados y protegidos de manipulaciones operativas posteriores.
Kpi_Historico_D1 AS (
    SELECT 
        Unidad,
        Tipo_Giro,
        SUM(total_neto) AS Venta_Historica_Acumulada,
        SUM(pax_cuenta) AS PAX_Historico,
        COUNT(id_ticket) AS Cheques_Historicos
    FROM Pipeline_Master_Normalizado
    WHERE Fecha_Operativa_Real BETWEEN @InicioMes AND @Ayer
      AND status_ticket = 'CERRADO' -- Solo lo contablemente respaldado entra al histórico
    GROUP BY Unidad, Tipo_Giro
),

-- 🔍 PASO 4: FLUJO DE LA JORNADA VIVA (TURNO EN CURSO)
-- Muestra el comportamiento del día actual basándose estrictamente en las aperturas de hoy.
-- Si hay un arrastre de días sin corte, se clasificarán automáticamente en su día origen en el bloque histórico.
Kpi_Turno_Vivo AS (
    SELECT 
        Unidad,
        SUM(CASE WHEN status_ticket = 'CERRADO' THEN total_neto ELSE 0 END) AS Venta_Dia_Cerrada,
        SUM(CASE WHEN status_ticket = 'ABIERTO' THEN total_neto ELSE 0 END) AS Venta_Dia_Volatil, -- Cuentas en mesa (Modificables)
        SUM(pax_cuenta) AS PAX_Dia,
        COUNT(id_ticket) AS Cheques_Dia,
        
        -- Métricas específicas por sub-regla de horario para la toma de decisiones comerciales
        SUM(CASE WHEN Bloque_Servicio = 'DESAYUNO' THEN total_neto ELSE 0 END) AS Venta_Desayuno,
        SUM(CASE WHEN Bloque_Servicio = 'COMIDA' THEN total_neto ELSE 0 END) AS Venta_Comida,
        SUM(CASE WHEN Bloque_Servicio = 'CENA / CIERRE NOCTURNO' THEN total_neto ELSE 0 END) AS Venta_Cena
    FROM Pipeline_Master_Normalizado
    WHERE Fecha_Operativa_Real = @FechaHoy
    GROUP BY Unidad
)

-- 📊 MATRIZ EJECUTIVA REESTRUCTURADA: SOBERANÍA OPERATIVA REGASTRO
-- Presentación final de la información separando las capas de riesgo contable.
SELECT 
    h.Unidad AS [Unidad de Negocio],
    h.Tipo_Giro AS [Clasificación de Giro],
    
    -- BLOQUE 1: HISTÓRICO HARD DATA (Corte D-1 Basado en Apertura de Turnos)
    ISNULL(h.Venta_Historica_Acumulada, 0) AS [1. Venta Histórica (Acumulada Cerrada)],
    ISNULL(h.PAX_Historico, 0) AS [PAX Hist.],
    ISNULL(h.Cheques_Historicos, 0) AS [Cheques Hist.],
    
    -- BLOQUE 2: MONITOREO DE LA JORNADA EN CURSO (DÍA VIVO)
    ISNULL(v.Venta_Dia_Cerrada, 0) AS [2. Venta Hoy (Turno Cerrado)],
    ISNULL(v.Venta_Dia_Volatil, 0) AS [3. Venta Hoy (Cuentas Vivas en Mesa)],
    ISNULL(v.PAX_Dia, 0) AS [PAX Hoy],
    
    -- BLOQUE 3: DESGLOSE TÁCTICO DE HORARIOS RECONOCIDOS
    ISNULL(v.Venta_Desayuno, 0) AS [Monto Desayunos (07-13h)],
    ISNULL(v.Venta_Comida, 0) AS [Monto Comidas (13-19h)],
    ISNULL(v.Venta_Cena, 0) AS [Monto Cenas / Cierre Nocturno (19h+)],
    
    -- CONSOLIDADO GENERAL (MÓVIL)
    (ISNULL(h.Venta_Historica_Acumulada, 0) + ISNULL(v.Venta_Dia_Cerrada, 0)) AS [KPI CONTABLE TOTAL MES]
FROM Kpi_Historico_D1 h
LEFT JOIN Kpi_Turno_Vivo v ON h.Unidad = v.Unidad;
