"""Lectura NO-LIVE del ticket de venta para Comercial."""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from .service import _query_edarsahub_tablero


def _safe_sql(value: Any) -> str:
    return str(value or "").replace("'", "''")


def _money(value: Any) -> float:
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


def _integer(value: Any) -> int:
    try:
        return int(float(value or 0))
    except (TypeError, ValueError):
        return 0


def _folio_sort_key(value: Any):
    text = str(value or "")
    try:
        return (0, int(text), text)
    except (TypeError, ValueError):
        return (1, 0, text)


def _open_detail_column_available() -> bool:
    rows = _query_edarsahub_tablero(
        """
        SELECT CASE
            WHEN COL_LENGTH(
                'dbo.Comercial_Ventas_Dia_Abiertas_v2',
                'detalle_abiertas_json'
            ) IS NULL THEN 0 ELSE 1
        END AS disponible
        """
    )
    return bool(rows and _integer(rows[0].get("disponible")) == 1)


def load_open_snapshot_lines(
    unidad_codigo: str,
    sucursal_id: str,
    fecha_operacion: str,
) -> List[Dict[str, Any]]:
    """Carga el detalle abierto por unidad canonica y fecha operativa.

    La unidad_negocio_id es la llave estable entre motores. No se filtra por
    sucursal_id porque ese valor no es homologado entre la UI y el snapshot:
    SoftRestaurant persiste DEFAULT y MPRO usa claves como 0021/0023. El
    filtro adicional provocaba falsos vacios aun cuando el JSON existia.
    """
    if not _open_detail_column_available():
        return []

    unidad = _safe_sql(unidad_codigo)
    fecha = _safe_sql(fecha_operacion)
    _ = sucursal_id  # compatibilidad de firma; la unidad canonica delimita el snapshot.

    sql = f"""
    SELECT TOP 1 detalle_abiertas_json
    FROM dbo.Comercial_Ventas_Dia_Abiertas_v2 WITH (NOLOCK)
    WHERE UPPER(LTRIM(RTRIM(unidad_negocio_id))) =
          UPPER(LTRIM(RTRIM('{unidad}')))
      AND fecha_operacion = '{fecha}'
    ORDER BY snapshot_timestamp DESC
    """

    rows = _query_edarsahub_tablero(sql)
    if not rows:
        return []

    raw = rows[0].get("detalle_abiertas_json")
    if not raw:
        return []

    try:
        parsed = json.loads(raw)
    except (TypeError, ValueError):
        return []
    return parsed if isinstance(parsed, list) else []


def merge_open_snapshot_tickets(
    items: List[Dict[str, Any]],
    unidad_codigo: str,
    sucursal_id: str,
    fecha_operacion: str,
) -> List[Dict[str, Any]]:
    """Agrega folios abiertos del snapshot sin duplicar tickets ya cerrados."""
    result = list(items or [])
    existentes = {str(item.get("folio") or "") for item in result}
    grouped: Dict[str, Dict[str, Any]] = {}

    for row in load_open_snapshot_lines(
        unidad_codigo,
        sucursal_id,
        fecha_operacion,
    ):
        folio = str(row.get("folio") or "").strip()
        if not folio or folio in existentes:
            continue
        ticket = grouped.setdefault(
            folio,
            {
                "folio": folio,
                "fecha": row.get("fecha_hora"),
                "pax": _integer(row.get("pax")),
                "total_venta": _money(row.get("total_ticket")),
                "num_productos": 0,
                "descuento_productos": 0.0,
                "descuento_encabezado_reportado": 0.0,
                "descuento_total_reportado": 0.0,
                "descuento_pct_max": 0.0,
                "vendedor": None,
            },
        )
        ticket["num_productos"] += 1
        ticket["descuento_productos"] += max(
            0.0,
            _money(row.get("descuento_producto")),
        )
        ticket["descuento_encabezado_reportado"] = max(
            ticket["descuento_encabezado_reportado"],
            max(0.0, _money(row.get("descuento_encabezado_reportado"))),
        )
        ticket["descuento_total_reportado"] = max(
            ticket["descuento_total_reportado"],
            max(0.0, _money(row.get("descuento_total_reportado"))),
        )
        ticket["descuento_pct_max"] = max(
            ticket["descuento_pct_max"],
            max(0.0, _money(row.get("descuento_pct"))),
        )
        if not ticket.get("vendedor"):
            vendedor = str(row.get("vendedor_nombre") or "").strip()
            if vendedor:
                ticket["vendedor"] = vendedor
        if not ticket.get("fecha") and row.get("fecha_hora"):
            ticket["fecha"] = row.get("fecha_hora")

    for folio, ticket in grouped.items():
        descuento_total = max(
            ticket["descuento_productos"],
            ticket["descuento_total_reportado"],
            ticket["descuento_encabezado_reportado"],
        )
        tiene_descuento = descuento_total > 0.005 or ticket["descuento_pct_max"] > 0.005
        total_cero_por_descuento = (
            abs(_money(ticket["total_venta"])) <= 0.005
            and tiene_descuento
        )
        result.append({
            "nivel": "detalle",
            "clave": None,
            "label": folio,
            "folio": folio,
            "fecha": str(ticket.get("fecha") or ""),
            "folios": 1,
            "pax": ticket["pax"],
            "total_venta": ticket["total_venta"],
            "importe": ticket["total_venta"],
            "num_productos": ticket["num_productos"],
            "tiene_descuento": tiene_descuento,
            "total_cero_por_descuento": total_cero_por_descuento,
            "descuento_total": descuento_total,
            "descuento_pct_max": ticket["descuento_pct_max"],
            "vendedor": ticket["vendedor"],
            "expandible": False,
            "siguiente_nivel": None,
            "fuente_ticket": "ABIERTA",
        })

    result.sort(key=lambda item: _folio_sort_key(item.get("folio")))
    return result


def _real_product_row(row: Dict[str, Any]) -> bool:
    code = str(row.get("producto_codigo_fuente") or "")
    return not code.upper().startswith("__ISCAM_AJUSTE_")


def build_ticket_venta(
    unidad_codigo: str,
    unidad_nombre: str,
    sucursal_id: str,
    folio: str,
    fecha_operacion: str,
) -> Optional[Dict[str, Any]]:
    """Reconstruye ticket cerrado; si no existe, busca snapshot abierto."""
    unidad = _safe_sql(unidad_codigo)
    ticket = _safe_sql(folio)
    fecha = _safe_sql(fecha_operacion)

    closed_rows = _query_edarsahub_tablero(
        f"""
        SELECT
            sistema_origen,
            fecha_hora,
            numero_ticket,
            producto_codigo_fuente,
            producto_nombre,
            cantidad,
            precio_unitario,
            importe_bruto,
            importe_neto,
            descuento,
            descuento_pct,
            vendedor_nombre,
            mesa,
            propina,
            pax
        FROM dbo.Comercial_Inteligencia_VentasDetalleProducto WITH (NOLOCK)
        WHERE unidad_negocio_id = '{unidad}'
          AND fecha_operacion = '{fecha}'
          AND CONVERT(varchar(128), numero_ticket) = '{ticket}'
          AND ISNULL(activo,1) = 1
          AND ISNULL(es_kpi_valido,1) = 1
          AND ISNULL(cancelado_origen,0) = 0
        ORDER BY producto_nombre, producto_codigo_fuente
        """
    )

    if closed_rows:
        total = sum(_money(row.get("importe_neto")) for row in closed_rows)
        subtotal = sum(
            _money(row.get("importe_bruto"))
            for row in closed_rows
            if _real_product_row(row)
        )
        descuento = sum(_money(row.get("descuento")) for row in closed_rows)
        propina = sum(_money(row.get("propina")) for row in closed_rows)
        pax = max((_integer(row.get("pax")) for row in closed_rows), default=0)
        items = []
        descuento_productos = 0.0
        for row in closed_rows:
            if not _real_product_row(row):
                continue
            bruto = _money(row.get("importe_bruto"))
            neto = _money(row.get("importe_neto"))
            descuento_linea = max(0.0, _money(row.get("descuento")))
            descuento_productos += descuento_linea
            descuento_pct_origen = row.get("descuento_pct")
            descuento_pct = (
                _money(descuento_pct_origen)
                if descuento_pct_origen is not None
                else (
                    (descuento_linea / bruto) * 100.0
                    if bruto > 0 and descuento_linea > 0
                    else 0.0
                )
            )
            items.append({
                "cantidad": _money(row.get("cantidad")),
                "descripcion": str(
                    row.get("producto_nombre") or "VENTA SIN DETALLE DE PRODUCTO"
                ),
                "precio_unitario": _money(row.get("precio_unitario")),
                "importe": bruto,
                "descuento_pct": descuento_pct,
                "descuento_importe": descuento_linea,
                "importe_neto": neto,
            })
        if not items:
            items = [{
                "cantidad": 1,
                "descripcion": "VENTA SIN DETALLE DE PRODUCTO",
                "precio_unitario": total,
                "importe": total,
                "descuento_pct": 0.0,
                "descuento_importe": 0.0,
                "importe_neto": total,
            }]
        descuento_cuenta = max(0.0, descuento - descuento_productos)
        vendedor = next(
            (
                str(row.get("vendedor_nombre") or "").strip()
                for row in closed_rows
                if str(row.get("vendedor_nombre") or "").strip()
            ),
            None,
        )
        mesa = next(
            (
                str(row.get("mesa") or "").strip()
                for row in closed_rows
                if str(row.get("mesa") or "").strip()
            ),
            None,
        )
        return {
            "source_status": "SUCCESS",
            "source": "Comercial_Inteligencia_VentasDetalleProducto",
            "ticket": {
                "unidad": unidad_nombre,
                "sistema_origen": closed_rows[0].get("sistema_origen"),
                "folio": folio,
                "fecha_hora": str(closed_rows[0].get("fecha_hora") or ""),
                "pax": pax,
                "vendedor": vendedor,
                "mesa": mesa,
                "estado": "CERRADA",
                "items": items,
                "subtotal": subtotal,
                "descuento_productos": descuento_productos,
                "descuento_cuenta": descuento_cuenta,
                "descuento": descuento,
                "impuesto": None,
                "total": total,
                "propina": propina,
            },
        }

    open_rows = [
        row
        for row in load_open_snapshot_lines(
            unidad_codigo,
            sucursal_id,
            fecha_operacion,
        )
        if str(row.get("folio") or "") == str(folio)
    ]
    if not open_rows:
        return None

    subtotal = sum(_money(row.get("importe_bruto")) for row in open_rows)
    descuento_productos = sum(
        max(0.0, _money(row.get("descuento_producto")))
        for row in open_rows
    )
    neto_productos = sum(
        _money(
            row.get("importe_neto_producto")
            if row.get("importe_neto_producto") is not None
            else (
                _money(row.get("importe_bruto"))
                - _money(row.get("descuento_producto"))
            )
        )
        for row in open_rows
    )
    total = max((_money(row.get("total_ticket")) for row in open_rows), default=0)
    propina = max((_money(row.get("propina")) for row in open_rows), default=0)
    pax = max((_integer(row.get("pax")) for row in open_rows), default=0)

    # El encabezado final es autoritativo. Cualquier reducción adicional
    # después de aplicar descuentos de producto se presenta como descuento
    # de cuenta/encabezado para que el ticket concilie exactamente.
    descuento_cuenta = max(0.0, neto_productos - total)
    descuento = descuento_productos + descuento_cuenta
    vendedor = next(
        (
            str(row.get("vendedor_nombre") or "").strip()
            for row in open_rows
            if str(row.get("vendedor_nombre") or "").strip()
        ),
        None,
    )
    mesa = next(
        (
            str(row.get("mesa") or "").strip()
            for row in open_rows
            if str(row.get("mesa") or "").strip()
        ),
        None,
    )
    return {
        "source_status": "SUCCESS",
        "source": "Comercial_Ventas_Dia_Abiertas_v2.detalle_abiertas_json",
        "ticket": {
            "unidad": unidad_nombre,
            "sistema_origen": None,
            "folio": folio,
            "fecha_hora": str(open_rows[0].get("fecha_hora") or ""),
            "pax": pax,
            "vendedor": vendedor,
            "mesa": mesa,
            "estado": "ABIERTA",
            "items": [
                {
                    "cantidad": _money(row.get("cantidad")),
                    "descripcion": str(
                        row.get("producto_nombre")
                        or "VENTA SIN DETALLE DE PRODUCTO"
                    ),
                    "precio_unitario": _money(row.get("precio_unitario")),
                    "importe": _money(row.get("importe_bruto")),
                    "descuento_pct": _money(row.get("descuento_pct")),
                    "descuento_importe": max(
                        0.0,
                        _money(row.get("descuento_producto")),
                    ),
                    "importe_neto": _money(
                        row.get("importe_neto_producto")
                        if row.get("importe_neto_producto") is not None
                        else (
                            _money(row.get("importe_bruto"))
                            - _money(row.get("descuento_producto"))
                        )
                    ),
                }
                for row in open_rows
            ],
            "subtotal": subtotal,
            "descuento_productos": descuento_productos,
            "descuento_cuenta": descuento_cuenta,
            "descuento": descuento,
            "impuesto": None,
            "total": total,
            "propina": propina,
        },
    }
