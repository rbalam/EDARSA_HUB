/*
Fase 3 Comercial KPI cross-menu/source audit.

Solo lectura. Ejecutar con:
/app/.venv/bin/python backend/tools/edarsahub_sql_runner.py --mode validate --script backend/database/validation/phase3_comercial_kpi_cross_menu_source_audit.sql

Objetivo:
- Comparar KPIs visibles en Tablero Ejecutivo, Comercial e Inteligencia Comercial.
- Contrastar la vista KPI diaria v2 contra las tablas sincronizadas de detalle.
- Detectar diferencias de ventas netas/brutas, tickets, pax y semantica de promedios.
*/

SET NOCOUNT ON;
GO

SELECT
    DB_NAME() AS database_name,
    SYSDATETIME() AS fecha_ejecucion,
    'phase3_comercial_kpi_cross_menu_source_audit' AS auditoria,
    'READ_ONLY' AS modo,
    'Ultimos 30 dias cerrados segun vw_Comercial_KPIs_Diarios_v2_Runtime' AS rango_base;
GO

SELECT
    esperado.name AS objeto,
    obj.type_desc,
    obj.create_date,
    obj.modify_date,
    CASE WHEN obj.object_id IS NULL THEN 'FALTA' ELSE 'OK' END AS estado
FROM (
    VALUES
        ('vw_Comercial_KPIs_Diarios_v2_Runtime'),
        ('Comercial_KPIs_Diarios_v2'),
        ('Comercial_Ventas_Dia_Abiertas_v2'),
        ('Comercial_Inteligencia_VentasDetalleProducto'),
        ('Sync_Sales'),
        ('Sync_PAX_Detalle'),
        ('Unidades_Negocio')
) AS esperado(name)
LEFT JOIN sys.objects obj
    ON obj.object_id = OBJECT_ID('dbo.' + esperado.name)
ORDER BY esperado.name;
GO

SELECT
    'Tablero Ejecutivo' AS menu,
    '/api/v2/comercial/dashboard, /api/v2/comercial/kpis-diarios' AS endpoints_clave,
    'vw_Comercial_KPIs_Diarios_v2_Runtime' AS fuente_principal,
    'ventas_sin_propina para backend v2; algunas vistas frontend aun usan nombre ventas_total' AS ventas_kpi,
    'cheque_promedio = ventas / tickets; ticket_promedio canonico = ventas / pax' AS regla_promedios,
    'Revisar nombres heredados ticket_promedio/pax_promedio' AS riesgo
UNION ALL
SELECT
    'Comercial',
    '/api/comercial/dashboard/{server_id}',
    'Servicio comercial SQL-first; debe converger a vw_Comercial_KPIs_Diarios_v2_Runtime',
    'ventas_sin_propina preferida; legacy puede exponer ventas_periodo',
    'legacy usa ticket_promedio como ventas / tickets',
    'Nomenclatura legacy puede diferir de Inteligencia'
UNION ALL
SELECT
    'Inteligencia Comercial',
    '/api/inteligencia/dashboard, /api/reporteador-bi/*, /api/inteligencia/iscam/*',
    'KPI view + Comercial_Inteligencia_VentasDetalleProducto + Sync_Sales + Sync_PAX_Detalle',
    'dashboard usa ventas_sin_propina; ISCAM usa MontoTotal',
    'dashboard canonico: ticket = ventas / pax, cheque = ventas / tickets',
    'Mezcla vista agregada, detalle por producto y Sync_Sales';
GO

DECLARE @fecha_fin DATE = (
    SELECT MAX(fecha_operacion)
    FROM dbo.vw_Comercial_KPIs_Diarios_v2_Runtime
    WHERE ISNULL(ventas_sin_propina, 0) > 0
);
DECLARE @fecha_inicio DATE = DATEADD(DAY, -30, ISNULL(@fecha_fin, CAST(GETDATE() AS DATE)));

WITH SourceFreshness AS (
    SELECT
        'KPI_RUNTIME' AS fuente,
        COUNT_BIG(*) AS registros,
        COUNT(DISTINCT unidad_negocio_id) AS unidades,
        COUNT(DISTINCT fecha_operacion) AS dias,
        MIN(fecha_operacion) AS fecha_minima,
        MAX(fecha_operacion) AS fecha_maxima,
        MAX(fecha_sincronizacion) AS ultima_sync,
        SUM(ISNULL(ventas_sin_propina, 0)) AS ventas_netas,
        SUM(ISNULL(ventas_total, 0)) AS ventas_brutas,
        SUM(ISNULL(tickets_total, 0)) AS tickets,
        SUM(ISNULL(pax_total, 0)) AS pax
    FROM dbo.vw_Comercial_KPIs_Diarios_v2_Runtime
    WHERE fecha_operacion BETWEEN @fecha_inicio AND @fecha_fin

    UNION ALL

    SELECT
        'INTEL_DETALLE',
        COUNT_BIG(*),
        COUNT(DISTINCT unidad_negocio_id),
        COUNT(DISTINCT fecha_operacion),
        MIN(fecha_operacion),
        MAX(fecha_operacion),
        MAX(fecha_sincronizacion),
        SUM(ISNULL(importe_neto, 0)),
        SUM(ISNULL(importe_bruto, 0)),
        COUNT(DISTINCT CONCAT(
            ISNULL(NULLIF(id_transaccion, ''), 'SIN_TX'),
            '|',
            ISNULL(NULLIF(numero_ticket, ''), 'SIN_TICKET'),
            '|',
            CONVERT(VARCHAR(10), fecha_operacion, 120)
        )),
        CAST(NULL AS DECIMAL(18, 2))
    FROM dbo.Comercial_Inteligencia_VentasDetalleProducto
    WHERE ISNULL(activo, 1) = 1
      AND fecha_operacion BETWEEN @fecha_inicio AND @fecha_fin

    UNION ALL

    SELECT
        'SYNC_SALES',
        COUNT_BIG(*),
        COUNT(DISTINCT UnidadNegocio),
        COUNT(DISTINCT CAST(FechaHora AS DATE)),
        MIN(CAST(FechaHora AS DATE)),
        MAX(CAST(FechaHora AS DATE)),
        MAX(last_modified),
        SUM(ISNULL(MontoTotal, total)),
        SUM(ISNULL(MontoTotal, total)),
        COUNT_BIG(*),
        SUM(ISNULL(Pax, 0))
    FROM dbo.Sync_Sales
    WHERE ISNULL(status, 'COMPLETED') = 'COMPLETED'
      AND CAST(FechaHora AS DATE) BETWEEN @fecha_inicio AND @fecha_fin

    UNION ALL

    SELECT
        'SYNC_PAX_DETALLE',
        COUNT_BIG(*),
        COUNT(DISTINCT SucursalNombre),
        COUNT(DISTINCT FechaOperacion),
        MIN(FechaOperacion),
        MAX(FechaOperacion),
        MAX(FechaSync),
        SUM(ISNULL(VentaCuenta, 0)),
        SUM(ISNULL(VentaCuenta, 0)),
        COUNT(DISTINCT ISNULL(CuentaID, CuentaFolio)),
        SUM(ISNULL(NumeroComensales, 0))
    FROM dbo.Sync_PAX_Detalle
    WHERE FechaOperacion BETWEEN @fecha_inicio AND @fecha_fin
)
SELECT
    @fecha_inicio AS fecha_inicio_audit,
    @fecha_fin AS fecha_fin_audit,
    fuente,
    registros,
    unidades,
    dias,
    fecha_minima,
    fecha_maxima,
    DATEDIFF(DAY, fecha_maxima, @fecha_fin) AS dias_retraso_vs_kpi,
    ultima_sync,
    ventas_netas,
    ventas_brutas,
    tickets,
    pax
FROM SourceFreshness
ORDER BY fuente;
GO

DECLARE @fecha_fin DATE = (
    SELECT MAX(fecha_operacion)
    FROM dbo.vw_Comercial_KPIs_Diarios_v2_Runtime
    WHERE ISNULL(ventas_sin_propina, 0) > 0
);
DECLARE @fecha_inicio DATE = DATEADD(DAY, -30, ISNULL(@fecha_fin, CAST(GETDATE() AS DATE)));

WITH Unidades AS (
    SELECT
        codigo,
        nombre,
        system_type,
        server_id,
        activo
    FROM dbo.Unidades_Negocio
    WHERE ISNULL(activo, 1) = 1
),
KpiUnidad AS (
    SELECT
        k.unidad_negocio_id,
        MAX(k.unidad_negocio_nombre) AS unidad_negocio_nombre,
        MAX(k.sistema_origen) AS sistema_origen,
        COUNT(DISTINCT k.fecha_operacion) AS dias_kpi,
        SUM(ISNULL(k.ventas_sin_propina, 0)) AS kpi_ventas_netas,
        SUM(ISNULL(k.ventas_total, 0)) AS kpi_ventas_brutas,
        SUM(ISNULL(k.propinas_total, 0)) AS kpi_propinas,
        SUM(ISNULL(k.tickets_total, 0)) AS kpi_tickets,
        SUM(ISNULL(k.pax_total, 0)) AS kpi_pax
    FROM dbo.vw_Comercial_KPIs_Diarios_v2_Runtime k
    WHERE k.fecha_operacion BETWEEN @fecha_inicio AND @fecha_fin
    GROUP BY k.unidad_negocio_id
),
DetalleTicket AS (
    SELECT
        COALESCE(NULLIF(d.unidad_negocio_id, ''), u.codigo, d.unidad_negocio_nombre) AS unidad_negocio_id,
        MAX(COALESCE(d.unidad_negocio_nombre, u.nombre)) AS unidad_negocio_nombre,
        d.fecha_operacion,
        CONCAT(
            ISNULL(NULLIF(d.id_transaccion, ''), 'SIN_TX'),
            '|',
            ISNULL(NULLIF(d.numero_ticket, ''), 'SIN_TICKET'),
            '|',
            CONVERT(VARCHAR(10), d.fecha_operacion, 120)
        ) AS ticket_key,
        SUM(ISNULL(d.importe_neto, 0)) AS venta_ticket_neta,
        SUM(ISNULL(d.importe_bruto, 0)) AS venta_ticket_bruta,
        MAX(ISNULL(d.pax, 0)) AS pax_ticket,
        COUNT_BIG(*) AS lineas_producto
    FROM dbo.Comercial_Inteligencia_VentasDetalleProducto d
    LEFT JOIN Unidades u
        ON UPPER(LTRIM(RTRIM(d.unidad_negocio_id))) = UPPER(LTRIM(RTRIM(u.codigo)))
        OR UPPER(LTRIM(RTRIM(d.unidad_negocio_nombre))) = UPPER(LTRIM(RTRIM(u.nombre)))
    WHERE ISNULL(d.activo, 1) = 1
      AND d.fecha_operacion BETWEEN @fecha_inicio AND @fecha_fin
    GROUP BY
        COALESCE(NULLIF(d.unidad_negocio_id, ''), u.codigo, d.unidad_negocio_nombre),
        d.fecha_operacion,
        CONCAT(
            ISNULL(NULLIF(d.id_transaccion, ''), 'SIN_TX'),
            '|',
            ISNULL(NULLIF(d.numero_ticket, ''), 'SIN_TICKET'),
            '|',
            CONVERT(VARCHAR(10), d.fecha_operacion, 120)
        )
),
DetalleUnidad AS (
    SELECT
        unidad_negocio_id,
        MAX(unidad_negocio_nombre) AS unidad_negocio_nombre,
        COUNT(DISTINCT fecha_operacion) AS dias_detalle,
        COUNT_BIG(*) AS detalle_tickets,
        SUM(venta_ticket_neta) AS detalle_ventas_netas,
        SUM(venta_ticket_bruta) AS detalle_ventas_brutas,
        SUM(pax_ticket) AS detalle_pax,
        SUM(lineas_producto) AS detalle_lineas
    FROM DetalleTicket
    GROUP BY unidad_negocio_id
),
SyncSalesUnidad AS (
    SELECT
        COALESCE(u.codigo, s.UnidadNegocio) AS unidad_negocio_id,
        MAX(COALESCE(u.nombre, s.UnidadNegocio)) AS unidad_negocio_nombre,
        COUNT(DISTINCT CAST(s.FechaHora AS DATE)) AS dias_sync_sales,
        COUNT_BIG(*) AS sync_sales_tickets,
        SUM(ISNULL(s.MontoTotal, s.total)) AS sync_sales_ventas,
        SUM(ISNULL(s.Pax, 0)) AS sync_sales_pax
    FROM dbo.Sync_Sales s
    LEFT JOIN Unidades u
        ON UPPER(LTRIM(RTRIM(s.UnidadNegocio))) = UPPER(LTRIM(RTRIM(u.codigo)))
        OR UPPER(LTRIM(RTRIM(s.UnidadNegocio))) = UPPER(LTRIM(RTRIM(u.nombre)))
    WHERE ISNULL(s.status, 'COMPLETED') = 'COMPLETED'
      AND CAST(s.FechaHora AS DATE) BETWEEN @fecha_inicio AND @fecha_fin
    GROUP BY COALESCE(u.codigo, s.UnidadNegocio)
),
KeySet AS (
    SELECT unidad_negocio_id FROM KpiUnidad
    UNION
    SELECT unidad_negocio_id FROM DetalleUnidad
    UNION
    SELECT unidad_negocio_id FROM SyncSalesUnidad
)
SELECT
    @fecha_inicio AS fecha_inicio_audit,
    @fecha_fin AS fecha_fin_audit,
    keyset.unidad_negocio_id,
    COALESCE(k.unidad_negocio_nombre, d.unidad_negocio_nombre, s.unidad_negocio_nombre) AS unidad_negocio_nombre,
    COALESCE(k.sistema_origen, u.system_type) AS sistema_origen,
    k.dias_kpi,
    d.dias_detalle,
    s.dias_sync_sales,
    k.kpi_ventas_netas,
    d.detalle_ventas_netas,
    k.kpi_ventas_netas - d.detalle_ventas_netas AS diff_kpi_neto_vs_detalle,
    CASE WHEN ABS(k.kpi_ventas_netas) > 0
        THEN ((d.detalle_ventas_netas - k.kpi_ventas_netas) / NULLIF(k.kpi_ventas_netas, 0)) * 100
        ELSE NULL END AS pct_diff_detalle_neto,
    k.kpi_ventas_brutas,
    s.sync_sales_ventas,
    s.sync_sales_ventas - k.kpi_ventas_brutas AS diff_sync_sales_vs_kpi_bruto,
    CASE WHEN ABS(k.kpi_ventas_brutas) > 0
        THEN ((s.sync_sales_ventas - k.kpi_ventas_brutas) / NULLIF(k.kpi_ventas_brutas, 0)) * 100
        ELSE NULL END AS pct_diff_sync_sales_bruto,
    k.kpi_tickets,
    d.detalle_tickets,
    s.sync_sales_tickets,
    k.kpi_pax,
    d.detalle_pax,
    s.sync_sales_pax,
    CASE
        WHEN k.unidad_negocio_id IS NULL THEN 'SIN_KPI_RUNTIME'
        WHEN d.unidad_negocio_id IS NULL AND s.unidad_negocio_id IS NULL THEN 'SIN_DETALLE_Y_SYNC_SALES'
        WHEN d.unidad_negocio_id IS NULL THEN 'SIN_DETALLE_INTELIGENCIA'
        WHEN s.unidad_negocio_id IS NULL THEN 'SIN_SYNC_SALES'
        WHEN ABS(ISNULL(d.detalle_ventas_netas, 0) - ISNULL(k.kpi_ventas_netas, 0)) > 1000
             AND ABS(ISNULL(d.detalle_ventas_netas, 0) - ISNULL(k.kpi_ventas_netas, 0)) > ABS(ISNULL(k.kpi_ventas_netas, 0)) * 0.01
             THEN 'KPI_NETO_VS_DETALLE_DIFIERE'
        WHEN ABS(ISNULL(s.sync_sales_ventas, 0) - ISNULL(k.kpi_ventas_brutas, 0)) > 1000
             AND ABS(ISNULL(s.sync_sales_ventas, 0) - ISNULL(k.kpi_ventas_brutas, 0)) > ABS(ISNULL(k.kpi_ventas_brutas, 0)) * 0.01
             THEN 'KPI_BRUTO_VS_SYNC_SALES_DIFIERE'
        WHEN ABS(ISNULL(k.kpi_tickets, 0) - ISNULL(d.detalle_tickets, 0)) > 2 THEN 'TICKETS_KPI_VS_DETALLE_DIFIEREN'
        WHEN ABS(ISNULL(k.kpi_pax, 0) - ISNULL(d.detalle_pax, 0)) > 5 THEN 'PAX_KPI_VS_DETALLE_DIFIERE'
        ELSE 'OK'
    END AS hallazgo
FROM KeySet keyset
LEFT JOIN KpiUnidad k
    ON k.unidad_negocio_id = keyset.unidad_negocio_id
LEFT JOIN DetalleUnidad d
    ON d.unidad_negocio_id = keyset.unidad_negocio_id
LEFT JOIN SyncSalesUnidad s
    ON s.unidad_negocio_id = keyset.unidad_negocio_id
LEFT JOIN Unidades u
    ON u.codigo = keyset.unidad_negocio_id
ORDER BY
    CASE
        WHEN k.unidad_negocio_id IS NULL THEN 0
        WHEN d.unidad_negocio_id IS NULL OR s.unidad_negocio_id IS NULL THEN 1
        ELSE 2
    END,
    ABS(ISNULL(d.detalle_ventas_netas, 0) - ISNULL(k.kpi_ventas_netas, 0)) DESC,
    keyset.unidad_negocio_id;
GO

DECLARE @fecha_fin DATE = (
    SELECT MAX(fecha_operacion)
    FROM dbo.vw_Comercial_KPIs_Diarios_v2_Runtime
    WHERE ISNULL(ventas_sin_propina, 0) > 0
);
DECLARE @fecha_inicio DATE = DATEADD(DAY, -30, ISNULL(@fecha_fin, CAST(GETDATE() AS DATE)));

WITH KpiDia AS (
    SELECT
        unidad_negocio_id,
        MAX(unidad_negocio_nombre) AS unidad_negocio_nombre,
        fecha_operacion,
        SUM(ISNULL(ventas_sin_propina, 0)) AS ventas_sin_propina,
        SUM(ISNULL(ventas_total, 0)) AS ventas_total,
        SUM(ISNULL(propinas_total, 0)) AS propinas_total,
        SUM(ISNULL(tickets_total, 0)) AS tickets_total,
        SUM(ISNULL(pax_total, 0)) AS pax_total,
        AVG(ISNULL(ticket_promedio, 0)) AS ticket_promedio_guardado,
        AVG(ISNULL(pax_promedio, 0)) AS pax_promedio_guardado
    FROM dbo.vw_Comercial_KPIs_Diarios_v2_Runtime
    WHERE fecha_operacion BETWEEN @fecha_inicio AND @fecha_fin
    GROUP BY unidad_negocio_id, fecha_operacion
),
Semantica AS (
    SELECT
        unidad_negocio_id,
        unidad_negocio_nombre,
        fecha_operacion,
        ventas_sin_propina,
        ventas_total,
        propinas_total,
        tickets_total,
        pax_total,
        ticket_promedio_guardado,
        pax_promedio_guardado,
        CASE WHEN tickets_total > 0 THEN ventas_sin_propina / tickets_total ELSE 0 END AS cheque_promedio_neto_calc,
        CASE WHEN pax_total > 0 THEN ventas_sin_propina / pax_total ELSE 0 END AS ticket_promedio_canonico_calc,
        CASE WHEN tickets_total > 0 THEN CAST(pax_total AS DECIMAL(18, 4)) / tickets_total ELSE 0 END AS pax_por_cheque_calc
    FROM KpiDia
)
SELECT TOP 100
    unidad_negocio_id,
    unidad_negocio_nombre,
    fecha_operacion,
    ventas_sin_propina,
    ventas_total,
    propinas_total,
    tickets_total,
    pax_total,
    ticket_promedio_guardado,
    cheque_promedio_neto_calc,
    ticket_promedio_canonico_calc,
    pax_promedio_guardado,
    pax_por_cheque_calc,
    ABS(ticket_promedio_guardado - cheque_promedio_neto_calc) AS delta_ticket_vs_cheque_neto,
    ABS(ticket_promedio_guardado - ticket_promedio_canonico_calc) AS delta_ticket_vs_ticket_canonico,
    ABS(pax_promedio_guardado - ticket_promedio_canonico_calc) AS delta_paxprom_vs_ticket_canonico,
    ABS(pax_promedio_guardado - pax_por_cheque_calc) AS delta_paxprom_vs_pax_por_cheque,
    CASE
        WHEN ABS(ticket_promedio_guardado - cheque_promedio_neto_calc) <= 0.05
             AND ABS(ticket_promedio_guardado - ticket_promedio_canonico_calc) > 0.05
             THEN 'CAMPO_TICKET_PROMEDIO_ES_CHEQUE_PROMEDIO'
        WHEN ABS(ticket_promedio_guardado - ticket_promedio_canonico_calc) <= 0.05
             THEN 'CAMPO_TICKET_PROMEDIO_CANONICO'
        ELSE 'CAMPO_TICKET_PROMEDIO_NO_CUADRA'
    END AS hallazgo_ticket_promedio,
    CASE
        WHEN ABS(pax_promedio_guardado - ticket_promedio_canonico_calc) <= 0.05
             THEN 'CAMPO_PAX_PROMEDIO_ES_VENTA_POR_PAX'
        WHEN ABS(pax_promedio_guardado - pax_por_cheque_calc) <= 0.05
             THEN 'CAMPO_PAX_PROMEDIO_ES_PAX_POR_CHEQUE'
        ELSE 'CAMPO_PAX_PROMEDIO_NO_CUADRA'
    END AS hallazgo_pax_promedio
FROM Semantica
WHERE ABS(ticket_promedio_guardado - cheque_promedio_neto_calc) > 0.05
   OR ABS(ticket_promedio_guardado - ticket_promedio_canonico_calc) > 0.05
   OR ABS(pax_promedio_guardado - ticket_promedio_canonico_calc) > 0.05
   OR ABS(pax_promedio_guardado - pax_por_cheque_calc) > 0.05
ORDER BY fecha_operacion DESC, unidad_negocio_id;
GO

DECLARE @fecha_fin DATE = (
    SELECT MAX(fecha_operacion)
    FROM dbo.vw_Comercial_KPIs_Diarios_v2_Runtime
    WHERE ISNULL(ventas_sin_propina, 0) > 0
);
DECLARE @fecha_inicio DATE = DATEADD(DAY, -30, ISNULL(@fecha_fin, CAST(GETDATE() AS DATE)));

WITH KpiDia AS (
    SELECT
        unidad_negocio_id,
        MAX(unidad_negocio_nombre) AS unidad_negocio_nombre,
        fecha_operacion,
        SUM(ISNULL(ventas_sin_propina, 0)) AS kpi_ventas_netas,
        SUM(ISNULL(ventas_total, 0)) AS kpi_ventas_brutas,
        SUM(ISNULL(tickets_total, 0)) AS kpi_tickets,
        SUM(ISNULL(pax_total, 0)) AS kpi_pax
    FROM dbo.vw_Comercial_KPIs_Diarios_v2_Runtime
    WHERE fecha_operacion BETWEEN @fecha_inicio AND @fecha_fin
    GROUP BY unidad_negocio_id, fecha_operacion
),
DetalleTicket AS (
    SELECT
        COALESCE(NULLIF(unidad_negocio_id, ''), unidad_negocio_nombre) AS unidad_negocio_id,
        MAX(unidad_negocio_nombre) AS unidad_negocio_nombre,
        fecha_operacion,
        CONCAT(
            ISNULL(NULLIF(id_transaccion, ''), 'SIN_TX'),
            '|',
            ISNULL(NULLIF(numero_ticket, ''), 'SIN_TICKET'),
            '|',
            CONVERT(VARCHAR(10), fecha_operacion, 120)
        ) AS ticket_key,
        SUM(ISNULL(importe_neto, 0)) AS venta_ticket_neta,
        MAX(ISNULL(pax, 0)) AS pax_ticket
    FROM dbo.Comercial_Inteligencia_VentasDetalleProducto
    WHERE ISNULL(activo, 1) = 1
      AND fecha_operacion BETWEEN @fecha_inicio AND @fecha_fin
    GROUP BY
        COALESCE(NULLIF(unidad_negocio_id, ''), unidad_negocio_nombre),
        fecha_operacion,
        CONCAT(
            ISNULL(NULLIF(id_transaccion, ''), 'SIN_TX'),
            '|',
            ISNULL(NULLIF(numero_ticket, ''), 'SIN_TICKET'),
            '|',
            CONVERT(VARCHAR(10), fecha_operacion, 120)
        )
),
DetalleDia AS (
    SELECT
        unidad_negocio_id,
        MAX(unidad_negocio_nombre) AS unidad_negocio_nombre,
        fecha_operacion,
        SUM(venta_ticket_neta) AS detalle_ventas_netas,
        COUNT_BIG(*) AS detalle_tickets,
        SUM(pax_ticket) AS detalle_pax
    FROM DetalleTicket
    GROUP BY unidad_negocio_id, fecha_operacion
),
KeySet AS (
    SELECT unidad_negocio_id, fecha_operacion FROM KpiDia
    UNION
    SELECT unidad_negocio_id, fecha_operacion FROM DetalleDia
)
SELECT TOP 100
    keyset.fecha_operacion,
    keyset.unidad_negocio_id,
    COALESCE(k.unidad_negocio_nombre, d.unidad_negocio_nombre) AS unidad_negocio_nombre,
    k.kpi_ventas_netas,
    d.detalle_ventas_netas,
    d.detalle_ventas_netas - k.kpi_ventas_netas AS diff_ventas_netas,
    CASE WHEN ABS(k.kpi_ventas_netas) > 0
        THEN ((d.detalle_ventas_netas - k.kpi_ventas_netas) / NULLIF(k.kpi_ventas_netas, 0)) * 100
        ELSE NULL END AS pct_diff_ventas_netas,
    k.kpi_tickets,
    d.detalle_tickets,
    d.detalle_tickets - k.kpi_tickets AS diff_tickets,
    k.kpi_pax,
    d.detalle_pax,
    d.detalle_pax - k.kpi_pax AS diff_pax,
    CASE
        WHEN k.unidad_negocio_id IS NULL THEN 'DIA_SIN_KPI_RUNTIME'
        WHEN d.unidad_negocio_id IS NULL THEN 'DIA_SIN_DETALLE_INTELIGENCIA'
        WHEN ABS(ISNULL(d.detalle_ventas_netas, 0) - ISNULL(k.kpi_ventas_netas, 0)) > 1000
             AND ABS(ISNULL(d.detalle_ventas_netas, 0) - ISNULL(k.kpi_ventas_netas, 0)) > ABS(ISNULL(k.kpi_ventas_netas, 0)) * 0.01
             THEN 'VENTA_NETA_DIARIA_DIFIERE'
        WHEN ABS(ISNULL(d.detalle_tickets, 0) - ISNULL(k.kpi_tickets, 0)) > 2 THEN 'TICKETS_DIARIOS_DIFIEREN'
        WHEN ABS(ISNULL(d.detalle_pax, 0) - ISNULL(k.kpi_pax, 0)) > 5 THEN 'PAX_DIARIO_DIFIERE'
        ELSE 'OK'
    END AS hallazgo
FROM KeySet keyset
LEFT JOIN KpiDia k
    ON k.unidad_negocio_id = keyset.unidad_negocio_id
   AND k.fecha_operacion = keyset.fecha_operacion
LEFT JOIN DetalleDia d
    ON d.unidad_negocio_id = keyset.unidad_negocio_id
   AND d.fecha_operacion = keyset.fecha_operacion
WHERE k.unidad_negocio_id IS NULL
   OR d.unidad_negocio_id IS NULL
   OR ABS(ISNULL(d.detalle_ventas_netas, 0) - ISNULL(k.kpi_ventas_netas, 0)) > 1000
   OR ABS(ISNULL(d.detalle_tickets, 0) - ISNULL(k.kpi_tickets, 0)) > 2
   OR ABS(ISNULL(d.detalle_pax, 0) - ISNULL(k.kpi_pax, 0)) > 5
ORDER BY
    CASE
        WHEN k.unidad_negocio_id IS NULL OR d.unidad_negocio_id IS NULL THEN 0
        ELSE 1
    END,
    ABS(ISNULL(d.detalle_ventas_netas, 0) - ISNULL(k.kpi_ventas_netas, 0)) DESC,
    keyset.fecha_operacion DESC,
    keyset.unidad_negocio_id;
GO

DECLARE @fecha_fin DATE = (
    SELECT MAX(fecha_operacion)
    FROM dbo.vw_Comercial_KPIs_Diarios_v2_Runtime
    WHERE ISNULL(ventas_sin_propina, 0) > 0
);
DECLARE @fecha_inicio DATE = DATEADD(DAY, -30, ISNULL(@fecha_fin, CAST(GETDATE() AS DATE)));

WITH SyncPax AS (
    SELECT
        p.SucursalNombre,
        u.codigo AS unidad_negocio_id,
        u.nombre AS unidad_negocio_nombre,
        COUNT_BIG(*) AS registros_pax,
        COUNT(DISTINCT p.FechaOperacion) AS dias_pax,
        MIN(p.FechaOperacion) AS fecha_minima,
        MAX(p.FechaOperacion) AS fecha_maxima,
        SUM(ISNULL(p.NumeroComensales, 0)) AS pax_sync_pax,
        SUM(ISNULL(p.VentaCuenta, 0)) AS venta_sync_pax
    FROM dbo.Sync_PAX_Detalle p
    LEFT JOIN dbo.Unidades_Negocio u
        ON UPPER(LTRIM(RTRIM(p.SucursalNombre))) = UPPER(LTRIM(RTRIM(u.nombre)))
        OR UPPER(LTRIM(RTRIM(p.SucursalID))) = UPPER(LTRIM(RTRIM(u.sucursal_origen_id)))
        OR UPPER(LTRIM(RTRIM(p.ServerID))) = UPPER(LTRIM(RTRIM(u.server_id)))
    WHERE p.FechaOperacion BETWEEN @fecha_inicio AND @fecha_fin
    GROUP BY p.SucursalNombre, u.codigo, u.nombre
),
Kpi AS (
    SELECT
        unidad_negocio_id,
        MAX(unidad_negocio_nombre) AS unidad_negocio_nombre,
        SUM(ISNULL(pax_total, 0)) AS pax_kpi,
        SUM(ISNULL(ventas_sin_propina, 0)) AS ventas_kpi_netas,
        COUNT(DISTINCT fecha_operacion) AS dias_kpi
    FROM dbo.vw_Comercial_KPIs_Diarios_v2_Runtime
    WHERE fecha_operacion BETWEEN @fecha_inicio AND @fecha_fin
    GROUP BY unidad_negocio_id
)
SELECT
    @fecha_inicio AS fecha_inicio_audit,
    @fecha_fin AS fecha_fin_audit,
    COALESCE(p.unidad_negocio_id, k.unidad_negocio_id) AS unidad_negocio_id,
    COALESCE(p.unidad_negocio_nombre, k.unidad_negocio_nombre, p.SucursalNombre) AS unidad_negocio_nombre,
    p.SucursalNombre,
    k.dias_kpi,
    p.dias_pax,
    k.pax_kpi,
    p.pax_sync_pax,
    p.pax_sync_pax - k.pax_kpi AS diff_pax,
    k.ventas_kpi_netas,
    p.venta_sync_pax,
    p.fecha_minima AS pax_fecha_minima,
    p.fecha_maxima AS pax_fecha_maxima,
    CASE
        WHEN p.SucursalNombre IS NULL THEN 'SIN_SYNC_PAX_DETALLE'
        WHEN k.unidad_negocio_id IS NULL THEN 'SYNC_PAX_SIN_KPI_RUNTIME'
        WHEN ABS(ISNULL(p.pax_sync_pax, 0) - ISNULL(k.pax_kpi, 0)) > 5 THEN 'PAX_SYNC_PAX_VS_KPI_DIFIERE'
        ELSE 'OK'
    END AS hallazgo
FROM Kpi k
FULL OUTER JOIN SyncPax p
    ON p.unidad_negocio_id = k.unidad_negocio_id
ORDER BY
    CASE
        WHEN p.SucursalNombre IS NULL OR k.unidad_negocio_id IS NULL THEN 0
        WHEN ABS(ISNULL(p.pax_sync_pax, 0) - ISNULL(k.pax_kpi, 0)) > 5 THEN 1
        ELSE 2
    END,
    COALESCE(p.unidad_negocio_id, k.unidad_negocio_id);
GO
