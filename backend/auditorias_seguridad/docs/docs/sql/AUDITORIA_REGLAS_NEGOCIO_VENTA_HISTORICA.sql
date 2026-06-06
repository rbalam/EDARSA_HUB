-- =========================================================================
-- SCRIPT: AUDITORÍA DE REGLAS DE NEGOCIO (VENTA HISTÓRICA VS TICKETS AL DÍA)
-- OBJETIVO: Evaluar si el pipeline mezcla turnos vivos o corta a día vencido (D-1).
-- =========================================================================

SET TRANSACTION ISOLATION LEVEL READ UNCOMMITTED;

DECLARE @UnidadAuditar VARCHAR(50) = 'CIENFUEGOS';
DECLARE @FechaFiltro DATE = '2026-05-29'; -- Fecha visualizada en el corte de la captura

-- 1. Consultar la última estampa de tiempo de los tickets integrados en el HUB
SELECT 
    nombre_unidad AS [Unidad de Negocio],
    COUNT(id_factura) AS [Total Tickets Consolidados],
    SUM(monto_total) AS [Venta Acumulada en HUB],
    MIN(fecha_corte) AS [Primer Ticket Registrado (Mayo)],
    MAX(fecha_corte) AS [Último Ticket Registrado (Timestamp Real)],
    
    -- Diagnóstico crítico de la regla de corte
    CASE 
        WHEN CAST(MAX(fecha_corte) AS DATE) >= @FechaFiltro 
        THEN '⚠️ ALERTA DE VOLATILIDAD: El HUB está absorbiendo tickets del día en curso. El turno no ha cerrado.'
        WHEN CAST(MAX(fecha_corte) AS DATE) = DATEADD(DAY, -1, @FechaFiltro)
        THEN '✅ CORTE CORRECTO (D-1): El acumulado está cerrado de forma estricta hasta el día anterior.'
        ELSE '🚨 RETRASO CRÍTICO: El acumulado tiene un rezago de más de 48 horas.'
    END AS [Evaluación de Veracidad Contable]

FROM EDARSA_HUB_SQL.dbo.Ventas_Consolidadas
WHERE nombre_unidad = @UnidadAuditar
  AND fecha_corte BETWEEN '2026-05-01' AND '2026-05-31'
GROUP BY nombre_unidad;

-- 2. Inspección del comportamiento transaccional del día en curso en el POS Local
-- Evalúa cuántos pesos corresponden a tickets "Vivos/Abiertos" que comercial ya cuenta pero el HUB debería omitir.
SELECT 
    status_ticket AS [Estado del Folio en Caja],
    COUNT(id_ticket) AS [Volumen de Tickets (Hoy)],
    SUM(total_neto) AS [Monto en Cajas ($)],
    AVG(total_neto) AS [Ticket Promedio de la Jefatura]
FROM [SERVIDO_CIENFUEGOS].BD_Transaccional.dbo.Tickets
WHERE CAST(fecha_operacion AS DATE) = @FechaFiltro
GROUP BY status_ticket;
