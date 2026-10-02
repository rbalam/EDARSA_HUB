"""Snapshot de detalle operativo de Ventas del Dia para Comercial.

Este modulo solo define consultas del sincronizador autorizado de Ventas del Dia
y serializa su resultado para persistirlo dentro del snapshot EDARSAHUB.
Los endpoints de Comercial nunca consultan el POS directamente.

Compatibilidad:
- La columna persistida conserva el nombre legacy ``detalle_abiertas_json``.
- Para MPRO el payload contiene abiertas y cerradas del dia, porque el encabezado
  tambien combina ambos grupos desde la API local. Asi el drill-down puede
  conciliar con el total del encabezado sin leer CENTRAL2020 ni otro POS.
"""

from __future__ import annotations

import json
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List


QUERY_SOFTRESTAURANT_DETALLE_ABIERTAS = """
SELECT
    COALESCE(
        NULLIF(MAX(LTRIM(RTRIM(CONVERT(varchar(64), ch.numcheque)))), ''),
        CONVERT(varchar(64), ch.folio)
    ) AS folio,
    CONVERT(varchar(64), ch.folio) AS folio_origen,
    'ABIERTA' AS estado_ticket,
    'SOFTRESTAURANT' AS sistema_origen,
    MIN(ch.fecha) AS fecha_hora,
    MAX(ISNULL(ch.nopersonas, 0)) AS pax,
    MAX(ISNULL(ch.propina, 0)) AS propina,
    MAX(CONVERT(varchar(50), ch.idmesero)) AS vendedor_id,
    MAX(NULLIF(LTRIM(RTRIM(CONVERT(varchar(100), m.nombre))), '')) AS vendedor_nombre,
    MAX(NULLIF(LTRIM(RTRIM(CONVERT(varchar(100), ch.mesa))), '')) AS mesa,
    MAX(ISNULL(ch.total, 0)) AS total_ticket,
    MAX(ISNULL(ch.descuentoimporte, 0)) AS descuento_encabezado_reportado,
    MAX(ISNULL(ch.totaldescuentos, 0)) AS descuento_total_reportado,
    COALESCE(
        NULLIF(CONVERT(varchar(100), d.idproducto), ''),
        'SIN_CODIGO'
    ) AS producto_codigo,
    COALESCE(
        MAX(CONVERT(varchar(300), p.descripcion)),
        'VENTA SIN DETALLE DE PRODUCTO'
    ) AS producto_nombre,
    SUM(CAST(ISNULL(d.cantidad, 0) AS decimal(18,4))) AS cantidad,
    CASE
        WHEN SUM(CAST(ISNULL(d.cantidad, 0) AS decimal(18,4))) <> 0
        THEN
            SUM(
                CAST(
                    ISNULL(d.cantidad, 0) * ISNULL(d.precio, 0)
                    AS decimal(18,4)
                )
            )
            / SUM(CAST(ISNULL(d.cantidad, 0) AS decimal(18,4)))
        ELSE MAX(CAST(ISNULL(d.precio, 0) AS decimal(18,4)))
    END AS precio_unitario,
    SUM(
        CAST(
            ISNULL(d.cantidad, 0) * ISNULL(d.precio, 0)
            AS decimal(18,4)
        )
    ) AS importe_bruto,
    MAX(CAST(ISNULL(d.descuento, 0) AS decimal(18,4))) AS descuento_pct,
    SUM(
        CAST(
            ISNULL(d.cantidad, 0)
            * ISNULL(d.precio, 0)
            * (ISNULL(d.descuento, 0) / 100.0)
            AS decimal(18,4)
        )
    ) AS descuento_producto,
    SUM(
        CAST(
            ISNULL(d.cantidad, 0)
            * ISNULL(d.precio, 0)
            * (1 - (ISNULL(d.descuento, 0) / 100.0))
            AS decimal(18,4)
        )
    ) AS importe_neto_producto
FROM tempcheques ch
LEFT JOIN tempcheqdet d
    ON d.foliodet = ch.folio
LEFT JOIN meseros m
    ON m.idmesero = ch.idmesero
LEFT JOIN productos p
    ON p.idproducto = d.idproducto
WHERE ISNULL(ch.cancelado, 0) = 0
  AND ISNULL(ch.total, 0) >= 0
  AND ch.fecha >= CONVERT(
        DATETIME,
        REPLACE('{fecha_operacion}', '-', ''),
        112
    )
  AND ch.fecha < DATEADD(
        DAY,
        1,
        CONVERT(
            DATETIME,
            REPLACE('{fecha_operacion}', '-', ''),
            112
        )
    )
GROUP BY
    ch.folio,
    COALESCE(
        NULLIF(CONVERT(varchar(100), d.idproducto), ''),
        'SIN_CODIGO'
    ),
    CAST(ISNULL(d.descuento, 0) AS decimal(18,4))
ORDER BY ch.folio, producto_codigo
"""


QUERY_MPRO_DETALLE_ABIERTAS = """
SELECT
    CONVERT(varchar(64), c.Co_Folio) AS folio,
    CONVERT(varchar(64), c.Co_Folio) AS folio_origen,
    'ABIERTA' AS estado_ticket,
    'MPRO' AS sistema_origen,
    MIN(c.Co_Fecha) AS fecha_hora,
    MAX(ISNULL(c.Co_Personas, 0)) AS pax,
    MAX(ISNULL(c.Co_Propina, 0)) AS propina,
    MAX(CONVERT(varchar(100), c.Vn_Cve_Vendedor)) AS vendedor_id,
    MAX(NULLIF(LTRIM(RTRIM(CONVERT(varchar(200), vnd.Vn_Descripcion))), '')) AS vendedor_nombre,
    MAX(NULLIF(LTRIM(RTRIM(CONVERT(varchar(100), c.Co_Referencia))), '')) AS mesa,
    SUM(SUM(CAST(ISNULL(d.Cd_Importe, 0) AS decimal(18,4))))
        OVER (PARTITION BY c.Co_Folio) AS total_ticket,
    COALESCE(
        NULLIF(CONVERT(varchar(100), d.Pr_Cve_Producto), ''),
        'SIN_CODIGO'
    ) AS producto_codigo,
    COALESCE(
        MAX(CONVERT(varchar(300), d.Cd_Concepto)),
        'VENTA SIN DETALLE DE PRODUCTO'
    ) AS producto_nombre,
    SUM(CAST(ISNULL(d.Cd_Cantidad, 0) AS decimal(18,4))) AS cantidad,
    CASE
        WHEN SUM(CAST(ISNULL(d.Cd_Cantidad, 0) AS decimal(18,4))) <> 0
        THEN
            SUM(CAST(ISNULL(d.Cd_Importe, 0) AS decimal(18,4)))
            / SUM(CAST(ISNULL(d.Cd_Cantidad, 0) AS decimal(18,4)))
        ELSE MAX(CAST(ISNULL(d.Cd_Precio, 0) AS decimal(18,4)))
    END AS precio_unitario,
    SUM(CAST(ISNULL(d.Cd_Importe, 0) AS decimal(18,4))) AS importe_bruto
FROM Comanda c
LEFT JOIN Comanda_Detalle d
    ON d.Co_Folio = c.Co_Folio
   AND ISNULL(d.Es_Cve_Estado, '') = 'AC'
   AND d.Fecha_Baja IS NULL
LEFT JOIN Vendedor vnd
    ON vnd.Vn_Cve_Vendedor = c.Vn_Cve_Vendedor
WHERE CAST(c.Co_Fecha AS date) = '{fecha_operacion}'
  AND c.Sc_Cve_Sucursal = '{sucursal_id}'
  AND c.Es_Cve_Estado IN ('AC', 'IM')
GROUP BY
    c.Co_Folio,
    COALESCE(
        NULLIF(CONVERT(varchar(100), d.Pr_Cve_Producto), ''),
        'SIN_CODIGO'
    )
ORDER BY c.Co_Folio, producto_codigo
"""


# MPRO: detalle de tickets cerrados desde la MISMA API local del encabezado.
#
# La selección de cuál consulta usar se hace en sync_comercial_abiertas_v2_job.py
# con el mismo closed_sales_source que decide el total del encabezado:
# - CANONICAL_VENTA_ENCABEZADO -> esta consulta.
# - PROVISIONAL_COMANDA -> QUERY_MPRO_DETALLE_CERRADAS_PROVISIONALES.
QUERY_MPRO_DETALLE_CERRADAS_CANONICAS = """
WITH h AS (
    SELECT
        ve.Vn_Folio,
        ve.Vn_Documento,
        ve.Vn_Fecha,
        ve.Sc_Cve_Sucursal,
        ve.Vn_Cve_Vendedor,
        CAST(
            ISNULL(ve.Vn_Precio_Neto_Importe, 0)
            AS decimal(18,4)
        ) AS total_header,
        ISNULL(c.Co_Personas, 0) AS pax,
        ISNULL(c.Co_Propina, 0) AS propina,
        NULLIF(
            LTRIM(RTRIM(CONVERT(varchar(100), c.Co_Referencia))),
            ''
        ) AS mesa,
        NULLIF(
            LTRIM(RTRIM(CONVERT(varchar(200), vnd.Vn_Descripcion))),
            ''
        ) AS vendedor_nombre
    FROM Venta_Encabezado ve
    LEFT JOIN Comanda c
        ON c.Co_Folio = ve.Vn_Documento
       AND c.Sc_Cve_Sucursal = ve.Sc_Cve_Sucursal
    LEFT JOIN Vendedor vnd
        ON vnd.Vn_Cve_Vendedor = ve.Vn_Cve_Vendedor
    WHERE CAST(ve.Vn_Fecha AS date) = '{fecha_operacion}'
      AND ve.Sc_Cve_Sucursal = '{sucursal_id}'
      AND ve.Es_Cve_Estado IN ('AC', 'FA')
      AND ve.Fecha_Baja IS NULL
),
t AS (
    SELECT
        Vn_Documento,
        MIN(Vn_Fecha) AS fecha_hora,
        MAX(pax) AS pax,
        MAX(propina) AS propina,
        MAX(CONVERT(varchar(100), Vn_Cve_Vendedor)) AS vendedor_id,
        MAX(vendedor_nombre) AS vendedor_nombre,
        MAX(mesa) AS mesa,
        SUM(total_header) AS total_ticket
    FROM h
    GROUP BY Vn_Documento
),
l AS (
    SELECT
        h.Vn_Documento,
        MAX(CONVERT(varchar(64), h.Vn_Folio)) AS folio_origen,
        COALESCE(
            NULLIF(CONVERT(varchar(100), d.Pr_Cve_Producto), ''),
            'SIN_CODIGO'
        ) AS producto_codigo,
        COALESCE(
            MAX(CONVERT(varchar(300), d.Vn_Concepto)),
            'VENTA SIN DETALLE DE PRODUCTO'
        ) AS producto_nombre,
        MAX(CASE WHEN d.Vn_Folio IS NULL THEN 0 ELSE 1 END) AS tiene_detalle,
        SUM(
            CAST(ISNULL(d.Vn_Cantidad_1, 0) AS decimal(18,4))
        ) AS cantidad,
        SUM(
            CAST(ISNULL(d.Vn_Precio_Lista_Importe, 0) AS decimal(18,4))
        ) AS importe_bruto,
        SUM(
            CAST(ISNULL(d.Vn_Descuento_Importe, 0) AS decimal(18,4))
        ) AS descuento_producto
    FROM h
    LEFT JOIN Venta d
        ON d.Vn_Folio = h.Vn_Folio
       AND d.Sc_Cve_Sucursal = h.Sc_Cve_Sucursal
    GROUP BY
        h.Vn_Documento,
        COALESCE(
            NULLIF(CONVERT(varchar(100), d.Pr_Cve_Producto), ''),
            'SIN_CODIGO'
        )
)
SELECT
    CONVERT(varchar(64), t.Vn_Documento) AS folio,
    l.folio_origen,
    'CERRADA' AS estado_ticket,
    'MPRO' AS sistema_origen,
    t.fecha_hora,
    t.pax,
    t.propina,
    t.vendedor_id,
    t.vendedor_nombre,
    t.mesa,
    t.total_ticket,
    l.producto_codigo,
    l.producto_nombre,
    CASE
        WHEN l.tiene_detalle = 0
        THEN CAST(1 AS decimal(18,4))
        ELSE l.cantidad
    END AS cantidad,
    CASE
        WHEN l.tiene_detalle = 0
        THEN t.total_ticket
        WHEN l.cantidad <> 0
        THEN l.importe_bruto / l.cantidad
        ELSE CAST(0 AS decimal(18,4))
    END AS precio_unitario,
    CASE
        WHEN l.tiene_detalle = 0
        THEN t.total_ticket
        ELSE l.importe_bruto
    END AS importe_bruto,
    CASE
        WHEN l.importe_bruto > 0
        THEN CAST(
            (l.descuento_producto * 100.0) / l.importe_bruto
            AS decimal(9,4)
        )
        ELSE CAST(0 AS decimal(9,4))
    END AS descuento_pct,
    CASE
        WHEN l.tiene_detalle = 0
        THEN CAST(0 AS decimal(18,4))
        ELSE l.descuento_producto
    END AS descuento_producto,
    CASE
        WHEN l.tiene_detalle = 0
        THEN t.total_ticket
        ELSE l.importe_bruto - l.descuento_producto
    END AS importe_neto_producto,
    CAST(0 AS decimal(18,4)) AS descuento_encabezado_reportado,
    CAST(0 AS decimal(18,4)) AS descuento_total_reportado
FROM t
INNER JOIN l
    ON l.Vn_Documento = t.Vn_Documento
ORDER BY t.Vn_Documento, l.producto_codigo
"""


QUERY_MPRO_DETALLE_CERRADAS_CANONICAS_COMANDA = """
SELECT
    CONVERT(varchar(64), c.Co_Folio) AS folio,
    CONVERT(varchar(64), c.Co_Folio) AS folio_origen,
    'CERRADA' AS estado_ticket,
    'MPRO' AS sistema_origen,
    MIN(c.Co_Fecha) AS fecha_hora,
    MAX(ISNULL(c.Co_Personas, 0)) AS pax,
    MAX(ISNULL(c.Co_Propina, 0)) AS propina,
    MAX(CONVERT(varchar(100), c.Vn_Cve_Vendedor)) AS vendedor_id,
    MAX(NULLIF(LTRIM(RTRIM(CONVERT(varchar(200), vnd.Vn_Descripcion))), '')) AS vendedor_nombre,
    MAX(NULLIF(LTRIM(RTRIM(CONVERT(varchar(100), c.Co_Referencia))), '')) AS mesa,
    SUM(SUM(CAST(ISNULL(d.Cd_Importe, 0) AS decimal(18,4))))
        OVER (PARTITION BY c.Co_Folio) AS total_ticket,
    COALESCE(
        NULLIF(CONVERT(varchar(100), d.Pr_Cve_Producto), ''),
        'SIN_CODIGO'
    ) AS producto_codigo,
    COALESCE(
        MAX(CONVERT(varchar(300), d.Cd_Concepto)),
        'VENTA SIN DETALLE DE PRODUCTO'
    ) AS producto_nombre,
    SUM(CAST(ISNULL(d.Cd_Cantidad, 0) AS decimal(18,4))) AS cantidad,
    CASE
        WHEN SUM(CAST(ISNULL(d.Cd_Cantidad, 0) AS decimal(18,4))) <> 0
        THEN
            SUM(CAST(ISNULL(d.Cd_Importe, 0) AS decimal(18,4)))
            / SUM(CAST(ISNULL(d.Cd_Cantidad, 0) AS decimal(18,4)))
        ELSE MAX(CAST(ISNULL(d.Cd_Precio, 0) AS decimal(18,4)))
    END AS precio_unitario,
    SUM(CAST(ISNULL(d.Cd_Importe, 0) AS decimal(18,4))) AS importe_bruto,
    CAST(0 AS decimal(9,4)) AS descuento_pct,
    CAST(0 AS decimal(18,4)) AS descuento_producto,
    SUM(CAST(ISNULL(d.Cd_Importe, 0) AS decimal(18,4))) AS importe_neto_producto,
    CAST(0 AS decimal(18,4)) AS descuento_encabezado_reportado,
    CAST(0 AS decimal(18,4)) AS descuento_total_reportado
FROM Comanda c
INNER JOIN Comanda_Detalle d
    ON d.Co_Folio = c.Co_Folio
   AND d.Es_Cve_Estado = 'AC'
   AND d.Fecha_Baja IS NULL
LEFT JOIN Vendedor vnd
    ON vnd.Vn_Cve_Vendedor = c.Vn_Cve_Vendedor
WHERE CAST(c.Co_Fecha AS date) = '{fecha_operacion}'
  AND c.Sc_Cve_Sucursal = '{sucursal_id}'
  AND EXISTS (
      SELECT 1
      FROM Venta_Encabezado ve
      WHERE ve.Vn_Documento = c.Co_Folio
        AND ve.Sc_Cve_Sucursal = c.Sc_Cve_Sucursal
        AND CAST(ve.Vn_Fecha AS date) = '{fecha_operacion}'
        AND ve.Es_Cve_Estado IN ('AC', 'FA')
        AND ve.Fecha_Baja IS NULL
  )
GROUP BY
    c.Co_Folio,
    COALESCE(
        NULLIF(CONVERT(varchar(100), d.Pr_Cve_Producto), ''),
        'SIN_CODIGO'
    )
ORDER BY c.Co_Folio, producto_codigo
"""


QUERY_MPRO_DETALLE_CERRADAS_PROVISIONALES = """
SELECT
    CONVERT(varchar(64), c.Co_Folio) AS folio,
    CONVERT(varchar(64), c.Co_Folio) AS folio_origen,
    'CERRADA' AS estado_ticket,
    'MPRO' AS sistema_origen,
    MIN(c.Co_Fecha) AS fecha_hora,
    MAX(ISNULL(c.Co_Personas, 0)) AS pax,
    MAX(ISNULL(c.Co_Propina, 0)) AS propina,
    MAX(CONVERT(varchar(100), c.Vn_Cve_Vendedor)) AS vendedor_id,
    MAX(NULLIF(LTRIM(RTRIM(CONVERT(varchar(200), vnd.Vn_Descripcion))), '')) AS vendedor_nombre,
    MAX(NULLIF(LTRIM(RTRIM(CONVERT(varchar(100), c.Co_Referencia))), '')) AS mesa,
    SUM(SUM(CAST(ISNULL(d.Cd_Importe, 0) AS decimal(18,4))))
        OVER (PARTITION BY c.Co_Folio) AS total_ticket,
    COALESCE(
        NULLIF(CONVERT(varchar(100), d.Pr_Cve_Producto), ''),
        'SIN_CODIGO'
    ) AS producto_codigo,
    COALESCE(
        MAX(CONVERT(varchar(300), d.Cd_Concepto)),
        'VENTA SIN DETALLE DE PRODUCTO'
    ) AS producto_nombre,
    SUM(CAST(ISNULL(d.Cd_Cantidad, 0) AS decimal(18,4))) AS cantidad,
    CASE
        WHEN SUM(CAST(ISNULL(d.Cd_Cantidad, 0) AS decimal(18,4))) <> 0
        THEN
            SUM(CAST(ISNULL(d.Cd_Importe, 0) AS decimal(18,4)))
            / SUM(CAST(ISNULL(d.Cd_Cantidad, 0) AS decimal(18,4)))
        ELSE MAX(CAST(ISNULL(d.Cd_Precio, 0) AS decimal(18,4)))
    END AS precio_unitario,
    SUM(CAST(ISNULL(d.Cd_Importe, 0) AS decimal(18,4))) AS importe_bruto
FROM Comanda c
LEFT JOIN Comanda_Detalle d
    ON d.Co_Folio = c.Co_Folio
   AND ISNULL(d.Es_Cve_Estado, '') = 'AC'
   AND d.Fecha_Baja IS NULL
LEFT JOIN Vendedor vnd
    ON vnd.Vn_Cve_Vendedor = c.Vn_Cve_Vendedor
WHERE CAST(c.Co_Fecha AS date) = '{fecha_operacion}'
  AND c.Sc_Cve_Sucursal = '{sucursal_id}'
  AND c.Es_Cve_Estado = 'PA'
GROUP BY
    c.Co_Folio,
    COALESCE(
        NULLIF(CONVERT(varchar(100), d.Pr_Cve_Producto), ''),
        'SIN_CODIGO'
    )
ORDER BY c.Co_Folio, producto_codigo
"""


# Fallbacks resumidos MPRO.
#
# Se usan cuando la consulta de detalle por producto no puede materializar
# todos los folios que ya fueron contados por el encabezado del mismo ciclo.
# Mantienen exactamente la identidad, total, PAX y vendedor del ticket y
# evitan conservar un detalle viejo mientras el encabezado avanza.
QUERY_MPRO_DETALLE_ABIERTAS_RESUMEN = """
SELECT
    CONVERT(varchar(64), c.Co_Folio) AS folio,
    CONVERT(varchar(64), c.Co_Folio) AS folio_origen,
    'ABIERTA' AS estado_ticket,
    'MPRO' AS sistema_origen,
    MIN(c.Co_Fecha) AS fecha_hora,
    MAX(ISNULL(c.Co_Personas, 0)) AS pax,
    MAX(ISNULL(c.Co_Propina, 0)) AS propina,
    MAX(CONVERT(varchar(100), c.Vn_Cve_Vendedor)) AS vendedor_id,
    MAX(NULLIF(LTRIM(RTRIM(CONVERT(varchar(200), vnd.Vn_Descripcion))), '')) AS vendedor_nombre,
    MAX(NULLIF(LTRIM(RTRIM(CONVERT(varchar(100), c.Co_Referencia))), '')) AS mesa,
    SUM(CAST(ISNULL(d.Cd_Importe, 0) AS decimal(18,4))) AS total_ticket,
    'SIN_CODIGO' AS producto_codigo,
    'CUENTA ABIERTA MPRO - DETALLE RESUMIDO' AS producto_nombre,
    CAST(1 AS decimal(18,4)) AS cantidad,
    SUM(CAST(ISNULL(d.Cd_Importe, 0) AS decimal(18,4))) AS precio_unitario,
    SUM(CAST(ISNULL(d.Cd_Importe, 0) AS decimal(18,4))) AS importe_bruto,
    CAST(0 AS decimal(9,4)) AS descuento_pct,
    CAST(0 AS decimal(18,4)) AS descuento_producto,
    SUM(CAST(ISNULL(d.Cd_Importe, 0) AS decimal(18,4))) AS importe_neto_producto,
    CAST(0 AS decimal(18,4)) AS descuento_encabezado_reportado,
    CAST(0 AS decimal(18,4)) AS descuento_total_reportado
FROM Comanda c
INNER JOIN Comanda_Detalle d
    ON d.Co_Folio = c.Co_Folio
   AND d.Es_Cve_Estado = 'AC'
   AND d.Fecha_Baja IS NULL
LEFT JOIN Vendedor vnd
    ON vnd.Vn_Cve_Vendedor = c.Vn_Cve_Vendedor
WHERE CAST(c.Co_Fecha AS date) = '{fecha_operacion}'
  AND c.Sc_Cve_Sucursal = '{sucursal_id}'
  AND c.Es_Cve_Estado IN ('AC', 'IM')
GROUP BY c.Co_Folio
ORDER BY c.Co_Folio
"""


QUERY_MPRO_DETALLE_CERRADAS_CANONICAS_RESUMEN = """
SELECT
    CONVERT(varchar(64), ve.Vn_Documento) AS folio,
    MAX(CONVERT(varchar(64), ve.Vn_Folio)) AS folio_origen,
    'CERRADA' AS estado_ticket,
    'MPRO' AS sistema_origen,
    MIN(ve.Vn_Fecha) AS fecha_hora,
    MAX(ISNULL(c.Co_Personas, 0)) AS pax,
    MAX(ISNULL(c.Co_Propina, 0)) AS propina,
    MAX(CONVERT(varchar(100), ve.Vn_Cve_Vendedor)) AS vendedor_id,
    MAX(NULLIF(LTRIM(RTRIM(CONVERT(varchar(200), vnd.Vn_Descripcion))), '')) AS vendedor_nombre,
    MAX(NULLIF(LTRIM(RTRIM(CONVERT(varchar(100), c.Co_Referencia))), '')) AS mesa,
    SUM(CAST(ISNULL(ve.Vn_Precio_Neto_Importe, 0) AS decimal(18,4))) AS total_ticket,
    'SIN_CODIGO' AS producto_codigo,
    'VENTA CERRADA MPRO - DETALLE RESUMIDO' AS producto_nombre,
    CAST(1 AS decimal(18,4)) AS cantidad,
    SUM(CAST(ISNULL(ve.Vn_Precio_Neto_Importe, 0) AS decimal(18,4))) AS precio_unitario,
    SUM(CAST(ISNULL(ve.Vn_Precio_Neto_Importe, 0) AS decimal(18,4))) AS importe_bruto,
    CAST(0 AS decimal(9,4)) AS descuento_pct,
    CAST(0 AS decimal(18,4)) AS descuento_producto,
    SUM(CAST(ISNULL(ve.Vn_Precio_Neto_Importe, 0) AS decimal(18,4))) AS importe_neto_producto,
    CAST(0 AS decimal(18,4)) AS descuento_encabezado_reportado,
    CAST(0 AS decimal(18,4)) AS descuento_total_reportado
FROM Venta_Encabezado ve
LEFT JOIN Comanda c
    ON c.Co_Folio = ve.Vn_Documento
   AND c.Sc_Cve_Sucursal = ve.Sc_Cve_Sucursal
LEFT JOIN Vendedor vnd
    ON vnd.Vn_Cve_Vendedor = ve.Vn_Cve_Vendedor
WHERE CAST(ve.Vn_Fecha AS date) = '{fecha_operacion}'
  AND ve.Sc_Cve_Sucursal = '{sucursal_id}'
  AND ve.Es_Cve_Estado IN ('AC', 'FA')
  AND ve.Fecha_Baja IS NULL
GROUP BY ve.Vn_Documento
ORDER BY ve.Vn_Documento
"""


QUERY_MPRO_DETALLE_CERRADAS_PROVISIONALES_RESUMEN = """
SELECT
    CONVERT(varchar(64), c.Co_Folio) AS folio,
    CONVERT(varchar(64), c.Co_Folio) AS folio_origen,
    'CERRADA' AS estado_ticket,
    'MPRO' AS sistema_origen,
    MIN(c.Co_Fecha) AS fecha_hora,
    MAX(ISNULL(c.Co_Personas, 0)) AS pax,
    MAX(ISNULL(c.Co_Propina, 0)) AS propina,
    MAX(CONVERT(varchar(100), c.Vn_Cve_Vendedor)) AS vendedor_id,
    MAX(NULLIF(LTRIM(RTRIM(CONVERT(varchar(200), vnd.Vn_Descripcion))), '')) AS vendedor_nombre,
    MAX(NULLIF(LTRIM(RTRIM(CONVERT(varchar(100), c.Co_Referencia))), '')) AS mesa,
    SUM(CAST(ISNULL(d.Cd_Importe, 0) AS decimal(18,4))) AS total_ticket,
    'SIN_CODIGO' AS producto_codigo,
    'VENTA CERRADA MPRO - DETALLE RESUMIDO' AS producto_nombre,
    CAST(1 AS decimal(18,4)) AS cantidad,
    SUM(CAST(ISNULL(d.Cd_Importe, 0) AS decimal(18,4))) AS precio_unitario,
    SUM(CAST(ISNULL(d.Cd_Importe, 0) AS decimal(18,4))) AS importe_bruto,
    CAST(0 AS decimal(9,4)) AS descuento_pct,
    CAST(0 AS decimal(18,4)) AS descuento_producto,
    SUM(CAST(ISNULL(d.Cd_Importe, 0) AS decimal(18,4))) AS importe_neto_producto,
    CAST(0 AS decimal(18,4)) AS descuento_encabezado_reportado,
    CAST(0 AS decimal(18,4)) AS descuento_total_reportado
FROM Comanda c
INNER JOIN Comanda_Detalle d
    ON d.Co_Folio = c.Co_Folio
   AND d.Es_Cve_Estado = 'AC'
   AND d.Fecha_Baja IS NULL
LEFT JOIN Vendedor vnd
    ON vnd.Vn_Cve_Vendedor = c.Vn_Cve_Vendedor
WHERE CAST(c.Co_Fecha AS date) = '{fecha_operacion}'
  AND c.Sc_Cve_Sucursal = '{sucursal_id}'
  AND c.Es_Cve_Estado = 'PA'
GROUP BY c.Co_Folio
ORDER BY c.Co_Folio
"""


def _number(value: Any) -> float:
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


def _json_default(value: Any):
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    return str(value)


def serialize_open_detail_rows(rows: List[Dict[str, Any]]) -> str:
    """Normaliza las lineas abiertas a un contrato JSON pequeno y estable."""
    normalized = []
    for row in rows or []:
        folio = str(row.get("folio") or "").strip()
        if not folio:
            continue
        normalized.append({
            "folio": folio,
            "folio_origen": str(row.get("folio_origen") or "").strip() or None,
            "estado_ticket": str(row.get("estado_ticket") or "ABIERTA").strip().upper(),
            "sistema_origen": str(row.get("sistema_origen") or "").strip() or None,
            "fecha_hora": row.get("fecha_hora"),
            "pax": int(_number(row.get("pax"))),
            "propina": _number(row.get("propina")),
            "vendedor_id": str(row.get("vendedor_id") or "").strip() or None,
            "vendedor_nombre": str(row.get("vendedor_nombre") or "").strip() or None,
            "mesa": str(row.get("mesa") or "").strip() or None,
            "total_ticket": _number(row.get("total_ticket")),
            "producto_codigo": str(row.get("producto_codigo") or "SIN_CODIGO"),
            "producto_nombre": str(
                row.get("producto_nombre") or "VENTA SIN DETALLE DE PRODUCTO"
            )[:300],
            "cantidad": _number(row.get("cantidad")),
            "precio_unitario": _number(row.get("precio_unitario")),
            "importe_bruto": _number(row.get("importe_bruto")),
            "descuento_pct": _number(row.get("descuento_pct")),
            "descuento_producto": _number(row.get("descuento_producto")),
            "importe_neto_producto": _number(row.get("importe_neto_producto")),
            "descuento_encabezado_reportado": _number(
                row.get("descuento_encabezado_reportado")
            ),
            "descuento_total_reportado": _number(
                row.get("descuento_total_reportado")
            ),
        })
    return json.dumps(
        normalized,
        ensure_ascii=False,
        separators=(",", ":"),
        default=_json_default,
    )
