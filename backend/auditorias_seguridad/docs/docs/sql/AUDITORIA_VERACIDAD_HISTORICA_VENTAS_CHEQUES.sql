-- =========================================================================
-- SCRIPT: AUDITORÍA DE VERACIDAD HISTÓRICA DE VENTAS Y Métrica de CHEQUES
-- ENTIDAD: EDARSA HUB CENTRAL VS SISTEMAS SOFTWARE REMOTOS (D-1)
-- RANGE: Mayo 2026 (Excluyendo el día en curso)
-- =========================================================================

SET NOCOUNT ON;
SET TRANSACTION ISOLATION LEVEL READ UNCOMMITTED; -- Protege históricos de bloqueos

DECLARE @InicioMes DATE = '2026-05-01';
DECLARE @Ayer DATE = DATEADD(DAY, -1, CAST(GETDATE() AS DATE)); -- 2026-05-28

-- 1. Estructura temporal para unificar los metadatos de los sistemas de software fuente
IF OBJECT_ID('tempdb..#Sistemas_Software_Fuente') IS NOT NULL 
    DROP TABLE #Sistemas_Software_Fuente;

CREATE TABLE #Sistemas_Software_Fuente (
    Unidad VARCHAR(50),
    Cheques_Emitidos_Fuente INT,
    Venta_Neta_Fuente DECIMAL(18,2)
);

-- >> EXTRACCIÓN DE SOFTWARE: CIENFUEGOS
INSERT INTO #Sistemas_Software_Fuente
SELECT 
    'CIENFUEGOS',
    COUNT(DISTINCT s.id_ticket) AS Cheques_Emitidos_Fuente,
    SUM(s.total_neto) AS Venta_Neta_Fuente
FROM [SERVIDO_CIENFUEGOS].BD_Transaccional.dbo.Tickets s
WHERE s.fecha_registro_ticket BETWEEN @InicioMes AND DATEADD(SECOND, -1, CAST(CAST(GETDATE() AS DATE) AS DATETIME))
  AND s.status_ticket = 'CERRADO'
GROUP BY s.nombre_unidad;

-- >> EXTRACCIÓN DE SOFTWARE: ORIGEN
INSERT INTO #Sistemas_Software_Fuente
SELECT 
    'ORIGEN',
    COUNT(DISTINCT s.id_ticket) AS Cheques_Emitidos_Fuente,
    SUM(s.total_neto) AS Venta_Neta_Fuente
FROM [SERVIDOR_ORIGEN].BD_Transaccional.dbo.Tickets s
WHERE s.fecha_registro_ticket BETWEEN @InicioMes AND DATEADD(SECOND, -1, CAST(CAST(GETDATE() AS DATE) AS DATETIME))
  AND s.status_ticket = 'CERRADO'
GROUP BY s.nombre_unidad;

-- >> EXTRACCIÓN DE SOFTWARE: 130° MÉRIDA
INSERT INTO #Sistemas_Software_Fuente
SELECT 
    '130° MERIDA',
    COUNT(DISTINCT s.id_ticket) AS Cheques_Emitidos_Fuente,
    SUM(s.total_neto) AS Venta_Neta_Fuente
FROM [SERVIDOR_MERIDA].BD_Transaccional.dbo.Tickets s
WHERE s.fecha_registro_ticket BETWEEN @InicioMes AND DATEADD(SECOND, -1, CAST(CAST(GETDATE() AS DATE) AS DATETIME))
  AND s.status_ticket = 'CERRADO'
GROUP BY s.nombre_unidad;

-- >> EXTRACCIÓN DE SOFTWARE: 130° QUERÉTARO
INSERT INTO #Sistemas_Software_Fuente
SELECT 
    '130° QUERETARO',
    COUNT(DISTINCT s.id_ticket) AS Cheques_Emitidos_Fuente,
    SUM(s.total_neto) AS Venta_Neta_Fuente
FROM [SERVIDOR_QUERETARO].BD_Transaccional.dbo.Tickets s
WHERE s.fecha_registro_ticket BETWEEN @InicioMes AND DATEADD(SECOND, -1, CAST(CAST(GETDATE() AS DATE) AS DATETIME))
  AND s.status_ticket = 'CERRADO'
GROUP BY s.nombre_unidad;

-- >> EXTRACCIÓN DE SOFTWARE: LA ESTELAR
INSERT INTO #Sistemas_Software_Fuente
SELECT 
    'LA ESTELAR',
    COUNT(DISTINCT s.id_ticket) AS Cheques_Emitidos_Fuente,
    SUM(s.total_neto) AS Venta_Neta_Fuente
FROM [SERVIDOR_ESTELAR].BD_Transaccional.dbo.Tickets s
WHERE s.fecha_registro_ticket BETWEEN @InicioMes AND DATEADD(SECOND, -1, CAST(CAST(GETDATE() AS DATE) AS DATETIME))
  AND s.status_ticket = 'CERRADO'
GROUP BY s.nombre_unidad;


-- =========================================================================
-- 2. CRUCE ATÓMICO VS CONSOLIDADOR EDARSA HUB SQL
-- =========================================================================
SELECT 
    COALESCE(src.Unidad, hub.nombre_unidad) AS [Unidad de Negocio],
    
    -- COMPARATIVA DE VENTAS HISTÓRICAS ($)
    ISNULL(src.Venta_Neta_Fuente, 0) AS [Venta Real (Sistemas Software)],
    ISNULL(hub.Venta_HUB, 0) AS [Venta Grabada (EDARSA HUB SQL)],
    (ISNULL(src.Venta_Neta_Fuente, 0) - ISNULL(hub.Venta_HUB, 0)) AS [Desfase Ventas ($)],
    
    -- COMPARATIVA DE VOLUMEN DE CHEQUES
    ISNULL(src.Cheques_Emitidos_Fuente, 0) AS [Cheques Reales (Software)],
    ISNULL(hub.Cheques_HUB, 0) AS [Cheques Grabados (EDARSA HUB SQL)],
    (ISNULL(src.Cheques_Emitidos_Fuente, 0) - ISNULL(hub.Cheques_HUB, 0)) AS [Diferencia en Cheques (Gaps)],
    
    -- AUDITORÍA CRÍTICA DE CHEQUE PROMEDIO REAL VS TABLERO
    CASE 
        WHEN ISNULL(src.Cheques_Emitidos_Fuente, 0) > 0 
        THEN CAST((ISNULL(src.Venta_Neta_Fuente, 0) / ISNULL(src.Cheques_Emitidos_Fuente, 0)) AS DECIMAL(18,2))
        ELSE 0 
    END AS [Cheque Promedio Real (Software)],
    
    CASE 
        WHEN ISNULL(hub.Cheques_HUB, 0) > 0 
        THEN CAST((ISNULL(hub.Venta_HUB, 0) / ISNULL(hub.Cheques_HUB, 0)) AS DECIMAL(18,2))
        ELSE 0 
    END AS [Cheque Promedio Visualizado (HUB)]

FROM #Sistemas_Software_Fuente src
FULL OUTER JOIN (
    SELECT 
        UPPER(TRIM(eh.nombre_unidad)) AS nombre_unidad,
        SUM(eh.monto_total) AS Venta_HUB,
        SUM(eh.cheques_visual) AS Cheques_HUB
    FROM EDARSA_HUB_SQL.dbo.Ventas_Consolidadas eh
    WHERE eh.fecha_corte BETWEEN @InicioMes AND @Ayer
    GROUP BY UPPER(TRIM(eh.nombre_unidad))
) hub ON src.Unidad = hub.nombre_unidad
ORDER BY ABS(ISNULL(src.Venta_Neta_Fuente, 0) - ISNULL(hub.Venta_HUB, 0)) DESC;

-- Limpieza de tablas de auditoría
DROP TABLE #Sistemas_Software_Fuente;
