-- =========================================================================
-- SCRIPT: AUDITORÍA CRUZADA DE SERIES VS EDARSA HUB
-- OBJETIVO: Identificar la serie exacta que Emergent está ignorando o duplicando.
-- =========================================================================

SET TRANSACTION ISOLATION LEVEL READ UNCOMMITTED;

-- Tabla para consolidar los cortes de caja locales detectados vía Linked Servers
IF OBJECT_ID('tempdb..#Series_Locales') IS NOT NULL DROP TABLE #Series_Locales;
CREATE TABLE #Series_Locales (
    Unidad VARCHAR(50),
    Serie_Ticket VARCHAR(20),
    Tickets_Locales INT,
    Venta_Bruta_Local DECIMAL(18,2),
    Venta_Neto_Local DECIMAL(18,2)
);

-- Inyección de datos vivos de Cienfuegos (Auditar Serie CF / A)
INSERT INTO #Series_Locales
SELECT 
    'CIENFUEGOS' AS Unidad,
    ISNULL(NULLIF(TRIM(UPPER(t.serie)), ''), 'SIN_SERIE') AS Serie_Ticket,
    COUNT(t.id_ticket) AS Tickets_Locales,
    SUM(t.subtotal) AS Venta_Bruta_Local,
    SUM(t.total_neto) AS Venta_Neto_Local
FROM [SERVIDO_CIENFUEGOS].BD_Transaccional.dbo.Tickets t
WHERE t.fecha_operacion BETWEEN '2026-05-01 00:00:00' AND '2026-05-31 23:59:59'
GROUP BY TRIM(UPPER(t.serie));

-- Inyección de datos vivos de ORIGEN (Auditar coincidencia de Series)
INSERT INTO #Series_Locales
SELECT 
    'ORIGEN' AS Unidad,
    ISNULL(NULLIF(TRIM(UPPER(t.serie)), ''), 'SIN_SERIE') AS Serie_Ticket,
    COUNT(t.id_ticket) AS Tickets_Locales,
    SUM(t.subtotal) AS Venta_Bruta_Local,
    SUM(t.total_neto) AS Venta_Neto_Local
FROM [SERVIDOR_ORIGEN].BD_Transaccional.dbo.Tickets t
WHERE t.fecha_operacion BETWEEN '2026-05-01 00:00:00' AND '2026-05-31 23:59:59'
GROUP BY TRIM(UPPER(t.serie));

-- CRUCE DE CONTROL CONTRA LAS TABLAS CONSOLIDADAS DE EDARSA HUB
SELECT 
    COALESCE(loc.Unidad, hub.nombre_unidad) AS [Unidad de Negocio],
    COALESCE(loc.Serie_Ticket, hub.serie_registro) AS [Serie Transaccional],
    ISNULL(loc.Tickets_Locales, 0) AS [Tickets en Caja Físico],
    ISNULL(hub.Total_Tickets_HUB, 0) AS [Tickets en EDARSA HUB],
    (ISNULL(loc.Tickets_Locales, 0) - ISNULL(hub.Total_Tickets_HUB, 0)) AS [Diferencia en Folios (Gaps)],
    ISNULL(loc.Venta_Neto_Local, 0) AS [Venta Real (Corte Local)],
    ISNULL(hub.Venta_HUB, 0) AS [Venta KPI (Tablero SQL)],
    (ISNULL(loc.Venta_Neto_Local, 0) - ISNULL(hub.Venta_HUB, 0)) AS [Desfase de Dinero ($)]
FROM #Series_Locales loc
FULL OUTER JOIN (
    SELECT 
        UPPER(nombre_unidad) AS nombre_unidad,
        UPPER(serie_registro) AS serie_registro,
        COUNT(id_factura) AS Total_Tickets_HUB,
        SUM(monto_total) AS Venta_HUB
    FROM EDARSA_HUB_SQL.dbo.Ventas_Consolidadas
    WHERE fecha_corte BETWEEN '2026-05-01' AND '2026-05-31'
    GROUP BY UPPER(nombre_unidad), UPPER(serie_registro)
) hub ON loc.Unidad = hub.nombre_unidad AND loc.Serie_Ticket = hub.serie_registro
ORDER BY ABS(ISNULL(loc.Venta_Neto_Local, 0) - ISNULL(hub.Venta_HUB, 0)) DESC;
