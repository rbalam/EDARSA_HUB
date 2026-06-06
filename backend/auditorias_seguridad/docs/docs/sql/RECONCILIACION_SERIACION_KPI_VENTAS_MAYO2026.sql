-- =========================================================================
-- RECONCILIACIÓN INTEGRAL DE SERIACIÓN Y KPI DE VENTAS TIEMPO REAL
-- EMERGENT PIPELINE AUDIT - MAYO 2026
-- =========================================================================

SET NOCOUNT ON;
SET TRANSACTION ISOLATION LEVEL READ UNCOMMITTED;

-- 1. Creación de una tabla temporal para unificar las consultas vivas en sitio
IF OBJECT_ID('tempdb..#BD_Fuentes_Sitio') IS NOT NULL DROP TABLE #BD_Fuentes_Sitio;
CREATE TABLE #BD_Fuentes_Sitio (
    Unidad_Id INT,
    Nombre_Sucursal VARCHAR(50),
    Serie_Ticket VARCHAR(10),
    Tickets_Contados INT,
    Venta_Acumulada_Fuente DECIMAL(18,4)
);

-- 2. Extracción directa y agresiva a los nodos transaccionales vía conexiones EDARSA HUB
-- NOTA: Se audita la seriación nativa para evitar sesgos de mapeo por texto.

-- >> EXTRACCIÓN SUCURSAL: CIENFUEGOS
INSERT INTO #BD_Fuentes_Sitio
SELECT 
    1 AS Unidad_Id,
    'CIENFUEGOS' AS Nombre_Sucursal,
    UPPER(t.serie) AS Serie_Ticket,
    COUNT(t.id_ticket) AS Tickets_Contados,
    SUM(t.total_neto) AS Venta_Acumulada_Fuente
FROM [SERVIDO_CIENFUEGOS].BD_Transaccional.dbo.Tickets t
WHERE t.fecha_operacion BETWEEN '2026-05-01 00:00:00' AND '2026-05-31 23:59:59'
GROUP BY UPPER(t.serie);

-- >> EXTRACCIÓN SUCURSAL: ORIGEN
INSERT INTO #BD_Fuentes_Sitio
SELECT 
    2 AS Unidad_Id,
    'ORIGEN' AS Nombre_Sucursal,
    UPPER(t.serie) AS Serie_Ticket,
    COUNT(t.id_ticket) AS Tickets_Contados,
    SUM(t.total_neto) AS Venta_Acumulada_Fuente
FROM [SERVIDOR_ORIGEN].BD_Transaccional.dbo.Tickets t
WHERE t.fecha_operacion BETWEEN '2026-05-01 00:00:00' AND '2026-05-31 23:59:59'
GROUP BY UPPER(t.serie);

-- >> EXTRACCIÓN SUCURSAL: 130° MÉRIDA
INSERT INTO #BD_Fuentes_Sitio
SELECT 
    3 AS Unidad_Id,
    '130° MERIDA' AS Nombre_Sucursal,
    UPPER(t.serie) AS Serie_Ticket,
    COUNT(t.id_ticket) AS Tickets_Contados,
    SUM(t.total_neto) AS Venta_Acumulada_Fuente
FROM [SERVIDOR_MERIDA].BD_Transaccional.dbo.Tickets t
WHERE t.fecha_operacion BETWEEN '2026-05-01 00:00:00' AND '2026-05-31 23:59:59'
GROUP BY UPPER(t.serie);

-- >> EXTRACCIÓN SUCURSAL: 130° QUERÉTARO
INSERT INTO #BD_Fuentes_Sitio
SELECT 
    4 AS Unidad_Id,
    '130° QUERETARO' AS Nombre_Sucursal,
    UPPER(t.serie) AS Serie_Ticket,
    COUNT(t.id_ticket) AS Tickets_Contados,
    SUM(t.total_neto) AS Venta_Acumulada_Fuente
FROM [SERVIDOR_QUERETARO].BD_Transaccional.dbo.Tickets t
WHERE t.fecha_operacion BETWEEN '2026-05-01 00:00:00' AND '2026-05-31 23:59:59'
GROUP BY UPPER(t.serie);

-- >> EXTRACCIÓN SUCURSAL: LA ESTELAR
INSERT INTO #BD_Fuentes_Sitio
SELECT 
    5 AS Unidad_Id,
    'LA ESTELAR' AS Nombre_Sucursal,
    UPPER(t.serie) AS Serie_Ticket,
    COUNT(t.id_ticket) AS Tickets_Contados,
    SUM(t.total_neto) AS Venta_Acumulada_Fuente
FROM [SERVIDOR_ESTELAR].BD_Transaccional.dbo.Tickets t
WHERE t.fecha_operacion BETWEEN '2026-05-01 00:00:00' AND '2026-05-31 23:59:59'
GROUP BY UPPER(t.serie);


-- =========================================================================
-- 3. CONCILIACIÓN FINAL CRUCIAL VS TABLAS DE EDARSAHUB SQL
-- =========================================================================
WITH Concentrado_Tablero_BI AS (
    SELECT 
        UPPER(eh.nombre_unidad) AS Nombre_Sucursal,
        UPPER(eh.serie_registro) AS Serie_Ticket, -- Mapeo por serie en el HUB
        COUNT(eh.id_factura) AS Tickets_HUB,
        SUM(eh.monto_total) AS Venta_HUB
    FROM EDARSA_HUB_SQL.dbo.Ventas_Consolidadas eh
    WHERE eh.fecha_corte BETWEEN '2026-05-01' AND '2026-05-31'
    GROUP BY UPPER(eh.nombre_unidad), UPPER(eh.serie_registro)
)
SELECT 
    COALESCE(src.Nombre_Sucursal, hub.Nombre_Sucursal) AS [Unidad de Negocio],
    ISNULL(src.Serie_Ticket, 'SIN SERIE EN FUENTE') AS [Serie Origen],
    ISNULL(src.Tickets_Contados, 0) AS [Tickets Creados en Sucursal],
    ISNULL(hub.Tickets_HUB, 0) AS [Tickets Cargados en EDARSA HUB],
    (ISNULL(src.Tickets_Contados, 0) - ISNULL(hub.Tickets_HUB, 0)) AS [Diferencia Volumen (Tickets)],
    ISNULL(src.Venta_Acumulada_Fuente, 0) AS [Venta Real (Sistemas Fuente)],
    ISNULL(hub.Venta_HUB, 0) AS [Venta KPI (EDARSA HUB SQL)],
    (ISNULL(src.Venta_Acumulada_Fuente, 0) - ISNULL(hub.Venta_HUB, 0)) AS [Monto Desfase Real ($)]
FROM #BD_Fuentes_Sitio src
FULL OUTER JOIN Concentrado_Tablero_BI hub 
    ON src.Nombre_Sucursal = hub.Nombre_Sucursal AND src.Serie_Ticket = hub.Serie_Ticket
ORDER BY ABS(ISNULL(src.Venta_Acumulada_Fuente, 0) - ISNULL(hub.Venta_HUB, 0)) DESC;

-- Limpieza de memoria
DROP TABLE #BD_Fuentes_Sitio;
