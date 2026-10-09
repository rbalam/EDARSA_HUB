"""Lectura NO-LIVE del ticket de venta para Comercial."""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from .service import _query_edarsahub_tablero
from modules.comercial_v2.ticket_contract import FIELDS, fields_from, header_from, discount_comment


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


def _snapshot_line_net_amount(row: Dict[str, Any]) -> float:
    """Resuelve neto canónico y recupera snapshots MPRO legacy sin neto."""
    bruto = _money(row.get("importe_bruto"))
    descuento = _money(row.get("descuento_producto"))
    raw_neto = row.get("importe_neto_producto")

    if raw_neto is None:
        return bruto - descuento

    neto = _money(raw_neto)
    sistema = str(row.get("sistema_origen") or "").strip().upper()
    tiene_descuento = any(
        abs(_money(row.get(field))) > 0.005
        for field in (
            "descuento_producto",
            "descuento_pct",
            "tipo_descuento_valor",
        )
    )

    if (
        sistema == "MPRO"
        and abs(neto) <= 0.005
        and abs(bruto) > 0.005
        and not tiene_descuento
    ):
        return bruto

    return neto


def _snapshot_partida_sort_key(row: Dict[str, Any]):
    value = str(row.get("partida_origen_id") or "").strip()
    try:
        return (0, int(value), value)
    except (TypeError, ValueError):
        return (1, 0, value)


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
    FROM dbo.Comercial_Ventas_Dia_Abiertas_v2
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


def _snapshot_display_folio(row: Dict[str, Any]) -> str:
    """Folio visible estable: numcheque 0/NULL no identifica una cuenta."""
    folio = str(row.get("folio") or "").strip()
    folio_origen = str(row.get("folio_origen") or "").strip()
    if folio in {"", "0"}:
        return folio_origen or folio
    return folio


def _snapshot_ticket_identity(row: Dict[str, Any]) -> str:
    """Identidad atómica del ticket, independiente del folio visible."""
    sistema = str(row.get("sistema_origen") or "").strip().upper()
    origen = str(row.get("folio_origen") or "").strip()
    visible = _snapshot_display_folio(row)
    return f"{sistema}:{origen or visible}"


def _snapshot_sales_amount(row: Dict[str, Any]) -> float:
    """Venta visible bruta del ticket; incluye propina cuando el origen la incluye."""
    return _money(row.get("total_ticket"))

def merge_open_snapshot_tickets(
    items: List[Dict[str, Any]],
    unidad_codigo: str,
    sucursal_id: str,
    fecha_operacion: str,
) -> List[Dict[str, Any]]:
    """Agrega folios del snapshot del día sin duplicar detalle canónico.

    El nombre se conserva por compatibilidad. Para MPRO el snapshot puede
    contener tanto ABIERTA como CERRADA porque ambos grupos provienen de la
    misma API local que alimenta el encabezado de Ventas del Día.
    """
    result = list(items or [])
    snapshot_rows = load_open_snapshot_lines(
        unidad_codigo,
        sucursal_id,
        fecha_operacion,
    )

    # SoftRestaurant durante la operacion activa: tempcheques/tempcheqdet
    # es el conjunto autoritativo del turno. No se mezcla con el historico
    # cerrado del mismo dia porque puede representar las mismas cuentas y
    # duplicar folios/importe. Si el snapshot temporal ya no existe tras el
    # corte, result conserva naturalmente el detalle canonico cerrado.
    snapshot_softrestaurant = any(
        str(row.get("sistema_origen") or "").strip().upper() == "SOFTRESTAURANT"
        for row in snapshot_rows
    )
    if snapshot_softrestaurant:
        result = []

    # Para MPRO del dia, el snapshot API_LOCAL es la misma fuente que el
    # encabezado. Sus tickets cerrados deben REEMPLAZAR cualquier fila
    # canonica/historica ya presente (por ejemplo, una carga Central2020).
    preferidos_api_local_mpro = {
        _snapshot_display_folio(row)
        for row in snapshot_rows
        if _snapshot_display_folio(row)
        and str(row.get("estado_ticket") or "").strip().upper() == "CERRADA"
        and str(row.get("sistema_origen") or "").strip().upper() == "MPRO"
    }
    if preferidos_api_local_mpro:
        result = [
            item
            for item in result
            if str(item.get("folio") or "").strip()
            not in preferidos_api_local_mpro
        ]

    existentes = {str(item.get("folio") or "").strip() for item in result}
    grouped: Dict[str, Dict[str, Any]] = {}

    for row in snapshot_rows:
        folio = _snapshot_display_folio(row)
        identity = _snapshot_ticket_identity(row)
        if not folio or folio in existentes:
            continue
        ticket = grouped.setdefault(
            identity,
            {
                "folio": folio,
                "folio_origen": str(row.get("folio_origen") or "").strip() or None,
                "fecha": row.get("fecha_hora"),
                "pax": _integer(row.get("pax")),
                "total_venta": _snapshot_sales_amount(row),
                "num_productos": 0,
                "descuento_productos": 0.0,
                "descuento_encabezado_reportado": 0.0,
                "descuento_total_reportado": 0.0,
                "descuento_pct_max": 0.0,
                "vendedor": None,
                "estado_ticket": str(
                    row.get("estado_ticket") or "ABIERTA"
                ).strip().upper(),
                "sistema_origen": row.get("sistema_origen"),
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
        ticket["pax"] = max(ticket["pax"], _integer(row.get("pax")))
        ticket["total_venta"] = max(
            ticket["total_venta"],
            _snapshot_sales_amount(row),
        )
        if not ticket.get("fecha") and row.get("fecha_hora"):
            ticket["fecha"] = row.get("fecha_hora")
        if str(row.get("estado_ticket") or "").strip().upper() == "CERRADA":
            ticket["estado_ticket"] = "CERRADA"
        if not ticket.get("sistema_origen") and row.get("sistema_origen"):
            ticket["sistema_origen"] = row.get("sistema_origen")

    for _identity, ticket in grouped.items():
        folio = ticket["folio"]
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
            "fuente_ticket": (
                "CERRADA_API_LOCAL"
                if ticket.get("estado_ticket") == "CERRADA"
                else "ABIERTA"
            ),
            "sistema_origen": ticket.get("sistema_origen"),
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
    """Reconstruye ticket canónico; si no existe, usa snapshot del día."""
    unidad = _safe_sql(unidad_codigo)
    ticket = _safe_sql(folio)
    fecha = _safe_sql(fecha_operacion)

    snapshot_rows = [
        row
        for row in load_open_snapshot_lines(
            unidad_codigo,
            sucursal_id,
            fecha_operacion,
        )
        if _snapshot_display_folio(row) == str(folio)
    ]
    snapshot_rows.sort(key=_snapshot_partida_sort_key)
    preferir_snapshot_mpro = any(
        str(row.get("estado_ticket") or "").strip().upper() == "CERRADA"
        and str(row.get("sistema_origen") or "").strip().upper() == "MPRO"
        for row in snapshot_rows
    )

    # Si existe ticket MPRO cerrado en el snapshot del dia, NO consultar ni
    # priorizar la tabla historica/canonica: el snapshot proviene de la API
    # local real y es la misma fuente usada por el encabezado de Ventas del Dia.
    closed_rows = [] if preferir_snapshot_mpro else _query_edarsahub_tablero(
        f"""
        SELECT
            {", ".join(FIELDS)},
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
        FROM dbo.Comercial_Inteligencia_VentasDetalleProducto
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
                **fields_from(row),
                "comentario_descuento": discount_comment(row),
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
                **header_from(closed_rows),
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

    if not snapshot_rows:
        return None

    estado_snapshot = (
        "CERRADA"
        if any(
            str(row.get("estado_ticket") or "").strip().upper() == "CERRADA"
            for row in snapshot_rows
        )
        else "ABIERTA"
    )
    sistema_snapshot = next(
        (
            str(row.get("sistema_origen") or "").strip()
            for row in snapshot_rows
            if str(row.get("sistema_origen") or "").strip()
        ),
        None,
    )

    subtotal = sum(_money(row.get("importe_bruto")) for row in snapshot_rows)
    descuento_productos = sum(
        max(0.0, _money(row.get("descuento_producto")))
        for row in snapshot_rows
    )
    neto_productos = sum(
        _snapshot_line_net_amount(row)
        for row in snapshot_rows
    )
    total = max(
        (_snapshot_sales_amount(row) for row in snapshot_rows),
        default=0,
    )
    propina = max(
        (_money(row.get("propina")) for row in snapshot_rows),
        default=0,
    )
    pax = max(
        (_integer(row.get("pax")) for row in snapshot_rows),
        default=0,
    )

    # El encabezado final es autoritativo. Cualquier reducción adicional
    # después de aplicar descuentos de producto se presenta como descuento
    # de cuenta/encabezado para que el ticket concilie exactamente.
    descuento_cuenta = max(0.0, neto_productos - total)
    descuento = descuento_productos + descuento_cuenta
    vendedor = next(
        (
            str(row.get("vendedor_nombre") or "").strip()
            for row in snapshot_rows
            if str(row.get("vendedor_nombre") or "").strip()
        ),
        None,
    )
    mesa = next(
        (
            str(row.get("mesa") or "").strip()
            for row in snapshot_rows
            if str(row.get("mesa") or "").strip()
        ),
        None,
    )
    return {
        "source_status": "SUCCESS",
        "source": "Comercial_Ventas_Dia_Abiertas_v2.detalle_abiertas_json:API_LOCAL_DIA",
        "ticket": {
            **header_from(snapshot_rows),
            "unidad": unidad_nombre,
            "sistema_origen": sistema_snapshot,
            "folio": folio,
            "fecha_hora": str(snapshot_rows[0].get("fecha_hora") or ""),
            "pax": pax,
            "vendedor": vendedor,
            "mesa": mesa,
            "estado": estado_snapshot,
            "items": [
                {
                    **fields_from(row),
                    "comentario_descuento": discount_comment(row),
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
                    "importe_neto": _snapshot_line_net_amount(row),
                }
                for row in snapshot_rows
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
