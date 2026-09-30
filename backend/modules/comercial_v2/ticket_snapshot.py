"""Snapshot de detalle de ventas abiertas para Comercial.

Este modulo solo define consultas del sincronizador autorizado de Ventas del Dia
y serializa su resultado para persistirlo dentro del snapshot EDARSAHUB.
Los endpoints de Comercial nunca consultan el POS directamente.
"""

from __future__ import annotations

import json
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List


QUERY_SOFTRESTAURANT_DETALLE_ABIERTAS = """
SELECT
    CONVERT(varchar(64), ch.folio) AS folio,
    MIN(ch.fecha) AS fecha_hora,
    MAX(ISNULL(ch.nopersonas, 0)) AS pax,
    MAX(ISNULL(ch.propina, 0)) AS propina,
    MAX(
        CASE
            WHEN ISNULL(ch.total, 0) >= ISNULL(ch.propina, 0)
            THEN ISNULL(ch.total, 0) - ISNULL(ch.propina, 0)
            ELSE ISNULL(ch.total, 0)
        END
    ) AS total_ticket,
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
    ) AS importe_bruto
FROM tempcheques ch
LEFT JOIN tempcheqdet d
    ON d.foliodet = ch.folio
LEFT JOIN productos p
    ON p.idproducto = d.idproducto
WHERE ISNULL(ch.cancelado, 0) = 0
  AND ISNULL(ch.total, 0) > 0
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
    )
ORDER BY ch.folio, producto_codigo
"""


QUERY_MPRO_DETALLE_ABIERTAS = """
SELECT
    CONVERT(varchar(64), c.Co_Folio) AS folio,
    MIN(c.Co_Fecha) AS fecha_hora,
    MAX(ISNULL(c.Co_Personas, 0)) AS pax,
    MAX(ISNULL(c.Co_Propina, 0)) AS propina,
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
            "fecha_hora": row.get("fecha_hora"),
            "pax": int(_number(row.get("pax"))),
            "propina": _number(row.get("propina")),
            "total_ticket": _number(row.get("total_ticket")),
            "producto_codigo": str(row.get("producto_codigo") or "SIN_CODIGO"),
            "producto_nombre": str(
                row.get("producto_nombre") or "VENTA SIN DETALLE DE PRODUCTO"
            )[:300],
            "cantidad": _number(row.get("cantidad")),
            "precio_unitario": _number(row.get("precio_unitario")),
            "importe_bruto": _number(row.get("importe_bruto")),
        })
    return json.dumps(
        normalized,
        ensure_ascii=False,
        separators=(",", ":"),
        default=_json_default,
    )
