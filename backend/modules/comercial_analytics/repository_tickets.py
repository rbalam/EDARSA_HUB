from __future__ import annotations

from modules.comercial_v2.ticket_contract import FIELDS, fields_from, header_from, discount_comment

from datetime import date, datetime
from typing import Any, Callable, Iterable

from core.db import execute_sql_query_params
from core.server_registry import EDARSAHUB_CONFIG

from .ticket_identity import (
    TicketIdentity,
    create_ticket_pk,
)


DETAIL_TABLE = "Comercial_Inteligencia_VentasDetalleProducto"
PRODUCT_SYNC_TABLE = "Sync_Productos"
CLASSIFICATION_TABLE = "Comercial_ClasificacionesProducto"
ENRICHMENT_TABLE = "Comercial_ProductosEnriquecimiento"


QueryExecutor = Callable[[str, tuple[Any, ...]], list[dict[str, Any]]]


def _execute_readonly_query_params(
    sql: str,
    params: tuple[Any, ...],
) -> list[dict[str, Any]]:
    cfg = EDARSAHUB_CONFIG
    return list(execute_sql_query_params(
        cfg['host'],
        cfg['port'],
        cfg['database'],
        cfg['username'],
        cfg['password'],
        sql,
        params,
    ) or [])


def _date_string(value: Any, field: str) -> str:
    if isinstance(value, datetime):
        return value.date().isoformat()

    if isinstance(value, date):
        return value.isoformat()

    normalized = str(value or "").strip()[:10]

    try:
        return datetime.strptime(
            normalized,
            "%Y-%m-%d",
        ).date().isoformat()
    except ValueError as exc:
        raise ValueError(f"{field} inválida") from exc


def _required(value: Any, field: str) -> str:
    normalized = str(value or "").strip()

    if not normalized:
        raise ValueError(f"{field} es obligatorio")

    return normalized


def _normalize_allowed_units(
    allowed_unit_codes: Iterable[Any],
) -> list[str]:
    return sorted({
        str(value).strip()
        for value in allowed_unit_codes
        if str(value or "").strip()
    })


def _ensure_unit_allowed(
    unit_code: str,
    allowed_unit_codes: Iterable[Any],
) -> None:
    allowed = _normalize_allowed_units(allowed_unit_codes)

    if not allowed or unit_code not in allowed:
        raise PermissionError(
            "La unidad solicitada está fuera del alcance RBAC"
        )


def _execute(
    sql: str,
    params: tuple[Any, ...],
    *,
    query_executor: QueryExecutor | None = None,
) -> list[dict[str, Any]]:
    executor = query_executor or _execute_readonly_query_params
    return list(executor(sql, params) or [])


def _fallback_ticket_from_comercial(
    identity: TicketIdentity,
) -> dict[str, Any] | None:
    """Reusa la reconstrucción certificada de Comercial cuando el lookup
    analytics no encuentra el folio con su predicado tipado.
    """
    from core.server_registry import get_server_by_unidad_codigo
    from modules.comercial.ticket_service import build_ticket_venta

    unidad = (
        get_server_by_unidad_codigo(identity.unidad_negocio_id)
        or {}
    )
    unidad_nombre = (
        unidad.get("unidad_negocio_nombre")
        or identity.unidad_negocio_id
    )
    sucursal_id = str(
        unidad.get("sucursal_origen_id")
        or ""
    ).strip()

    payload = build_ticket_venta(
        identity.unidad_negocio_id,
        unidad_nombre,
        sucursal_id,
        identity.numero_ticket,
        identity.fecha_operacion,
    )

    source_ticket = (payload or {}).get("ticket")
    if not source_ticket:
        return None

    source_items = list(source_ticket.get("items") or [])
    lines = []

    for index, item in enumerate(source_items, start=1):
        importe = round(float(item.get("importe") or 0), 2)
        descuento_importe = round(
            float(item.get("descuento_importe") or 0),
            2,
        )
        importe_neto = round(
            float(
                item.get("importe_neto")
                if item.get("importe_neto") is not None
                else importe - descuento_importe
            ),
            2,
        )
        lines.append({
            **fields_from(item),
            "comentario_descuento": item.get("comentario_descuento"),
            "linea_pk": (
                f"{identity.numero_ticket}:fallback:{index}"
            ),
            "codigo": "",
            "producto": str(
                item.get("descripcion")
                or "VENTA SIN DETALLE DE PRODUCTO"
            ),
            "familia": "",
            "subfamilia": "",
            "clasificacion": "",
            "casa": "",
            "marca": "",
            "grado_alcohol": None,
            "es_alcoholico": False,
            "cantidad": round(
                float(item.get("cantidad") or 0),
                2,
            ),
            "precio_unitario": round(
                float(item.get("precio_unitario") or 0),
                2,
            ),
            "importe_bruto": importe,
            "importe": importe_neto,
            "descuento": descuento_importe,
            "descuento_importe": descuento_importe,
            "descuento_pct": round(
                float(item.get("descuento_pct") or 0),
                2,
            ),
            "importe_neto": importe_neto,
            "propina": 0.0,
            "pax": int(source_ticket.get("pax") or 0),
        })

    total = round(float(source_ticket.get("total") or 0), 2)
    subtotal = round(
        float(source_ticket.get("subtotal") or total),
        2,
    )
    descuento = round(
        float(source_ticket.get("descuento") or 0),
        2,
    )
    propina = round(
        float(source_ticket.get("propina") or 0),
        2,
    )

    return {
        "ticket": {
            **{key: value for key, value in source_ticket.items() if key.startswith(("cliente_", "ticket_"))},
            "mesa": source_ticket.get("mesa"),
            "unidad_negocio_id": identity.unidad_negocio_id,
            "unidad": (
                source_ticket.get("unidad")
                or unidad_nombre
            ),
            "sucursal": sucursal_id or None,
            "fecha_operacion": identity.fecha_operacion,
            "fecha": identity.fecha_operacion,
            "fecha_hora": str(
                source_ticket.get("fecha_hora")
                or identity.fecha_operacion
            ),
            "numero_ticket": str(
                source_ticket.get("folio")
                or identity.numero_ticket
            ),
            "estado": (
                source_ticket.get("estado")
                or "CERRADA"
            ),
            "pax": int(source_ticket.get("pax") or 0),
            "vendedor": source_ticket.get("vendedor"),
            "sistema_origen": source_ticket.get("sistema_origen"),
            "lineas": len(lines),
            "subtotal": subtotal,
            "descuento_productos": round(
                float(source_ticket.get("descuento_productos") or 0),
                2,
            ),
            "descuento_cuenta": round(
                float(source_ticket.get("descuento_cuenta") or 0),
                2,
            ),
            "descuento": descuento,
            "impuesto": source_ticket.get("impuesto"),
            "ventas": total,
            "total": total,
            "propina": propina,
        },
        "lines": lines,
        "lineas": lines,
        "traceability": {
            "source": (payload or {}).get("source")
            or "modules.comercial.ticket_service",
            "temporal_field": "fecha_operacion",
            "live": False,
            "identity_version": identity.version,
            "fallback": "COMERCIAL_TICKET_CERTIFIED_PATH",
        },
    }


def _list_current_day_with_comercial_merge(
    *,
    operation_date: str,
    unit_code: str,
    page: int,
    page_size: int,
) -> dict[str, Any]:
    """Reusa el contrato de Ventas del Dia certificado en Tablero Comercial.

    Lee cerradas del detalle canonico y agrega abiertas exclusivamente mediante
    merge_open_snapshot_tickets(). No consulta POS live y conserva RBAC por
    unidad porque esta funcion solo se invoca despues de _ensure_unit_allowed().
    """
    from core.server_registry import get_server_by_unidad_codigo
    from modules.comercial.ticket_service import merge_open_snapshot_tickets

    rows = _execute(
        f"""
        SELECT
            d.unidad_negocio_id,
            MAX(d.unidad_negocio_nombre) AS unidad,
            MAX(d.sucursal_nombre) AS sucursal,
            d.numero_ticket,
            MIN(d.fecha_hora) AS fecha_hora,
            MAX(ISNULL(d.pax, 0)) AS pax,
            COUNT(*) AS lineas,
            SUM(ISNULL(d.importe_neto, 0)) AS ventas_sin_propina,
            MAX(ISNULL(d.propina, 0)) AS propina
        FROM {DETAIL_TABLE} AS d
        WHERE
            ISNULL(d.activo, 1) = 1
            AND ISNULL(d.es_kpi_valido, 1) = 1
            AND ISNULL(d.cancelado_origen, 0) = 0
            AND d.numero_ticket IS NOT NULL
            AND d.fecha_operacion = %s
            AND d.unidad_negocio_id = %s
        GROUP BY
            d.unidad_negocio_id,
            d.numero_ticket
        ORDER BY
            CASE WHEN TRY_CONVERT(BIGINT, d.numero_ticket) IS NULL THEN 1 ELSE 0 END,
            TRY_CONVERT(BIGINT, d.numero_ticket) ASC,
            d.numero_ticket ASC
        """,
        (operation_date, unit_code),
    )

    unit_meta = get_server_by_unidad_codigo(unit_code) or {}
    unit_name = (
        (rows[0].get("unidad") if rows else None)
        or unit_meta.get("unidad_negocio_nombre")
        or unit_code
    )
    sucursal_id = str(
        unit_meta.get("sucursal_origen_id")
        or (rows[0].get("sucursal") if rows else "")
        or ""
    ).strip()

    comercial_items = []
    for row in rows:
        comercial_items.append({
            "nivel": "detalle",
            "clave": None,
            "label": str(row.get("numero_ticket") or ""),
            "folio": str(row.get("numero_ticket") or ""),
            "fecha": str(row.get("fecha_hora") or operation_date),
            "folios": 1,
            "pax": int(row.get("pax") or 0),
            "total_venta": (
                float(row.get("ventas_sin_propina") or 0)
                + float(row.get("propina") or 0)
            ),
            "importe": (
                float(row.get("ventas_sin_propina") or 0)
                + float(row.get("propina") or 0)
            ),
            "num_productos": int(row.get("lineas") or 0),
            "expandible": False,
            "siguiente_nivel": None,
            "fuente_ticket": "CERRADA",
            "propina": float(row.get("propina") or 0),
        })

    merged = merge_open_snapshot_tickets(
        comercial_items,
        unit_code,
        sucursal_id,
        operation_date,
    )

    all_items = []
    for item in merged:
        ticket_number = _required(item.get("folio"), "numero_ticket")
        raw_datetime = item.get("fecha")
        hour = ""
        if isinstance(raw_datetime, datetime):
            hour = raw_datetime.strftime("%H:%M")
        elif raw_datetime:
            text = str(raw_datetime)
            hour = text[11:16] if len(text) >= 16 else ""

        all_items.append({
            "ticket_pk": create_ticket_pk(
                unidad_negocio_id=unit_code,
                fecha_operacion=operation_date,
                numero_ticket=ticket_number,
            ),
            "unidad_negocio_id": unit_code,
            "unidad": unit_name,
            "sucursal": sucursal_id or None,
            "fecha_operacion": operation_date,
            "fecha": operation_date,
            "hora": hour,
            "numero_ticket": ticket_number,
            "pax": int(item.get("pax") or 0),
            "lineas": int(
                item.get("num_productos")
                or item.get("lineas")
                or 0
            ),
            "ventas": round(
                float(item.get("total_venta") or item.get("importe") or 0),
                2,
            ),
            "propina": round(float(item.get("propina") or 0), 2),
            "fuente_ticket": item.get("fuente_ticket") or "CERRADA",
        })

    total = len(all_items)
    offset = (page - 1) * page_size
    page_items = all_items[offset:offset + page_size]
    returned = len(page_items)

    return {
        "items": page_items,
        "page": page,
        "page_size": page_size,
        "total": total,
        "returned": returned,
        "has_more": offset + returned < total,
        "traceability": {
            "source": (
                "Comercial_Inteligencia_VentasDetalleProducto"
                " + Comercial_Ventas_Dia_Abiertas_v2.detalle_abiertas_json"
            ),
            "contract": "TABLERO_COMERCIAL_VENTAS_DIA_CERTIFIED_PATH",
            "temporal_field": "fecha_operacion",
            "live": False,
            "paginated": True,
            "rbac": "UNIDAD_NEGOCIO",
        },
    }



def summarize_current_day_tickets(
    *,
    operation_date: str,
    unit_code: str,
) -> dict[str, Any]:
    """Resume exactamente el mismo conjunto atomico que usa Detalle de Ventas.

    Esta funcion NO crea una segunda logica de KPI: consume
    _list_current_day_with_comercial_merge(), que es la ruta certificada usada
    por /v2/comercial/analytics/tickets para una sola fecha/unidad.
    """
    payload = _list_current_day_with_comercial_merge(
        operation_date=_date_string(operation_date, "operation_date"),
        unit_code=_required(unit_code, "unit_code"),
        page=1,
        page_size=1_000_000,
    )
    items = list(payload.get("items") or [])
    ventas = round(sum(float(item.get("ventas") or 0) for item in items), 2)
    pax = sum(int(item.get("pax") or 0) for item in items)
    cheques = len(items)

    return {
        "ventas": ventas,
        "pax": pax,
        "cheques": cheques,
        "ticket_promedio": round(ventas / cheques, 2) if cheques > 0 else 0.0,
        "pax_promedio": round(ventas / pax, 2) if pax > 0 else 0.0,
        "items": items,
        "traceability": {
            **dict(payload.get("traceability") or {}),
            "contract": "DETALLE_VENTAS_CANONICO_ATOMICO_TRANSVERSAL",
            "aggregation": "SUM(items.ventas), SUM(items.pax), COUNT(items)",
        },
    }

def list_tickets(
    *,
    fecha_inicio: Any,
    fecha_fin: Any,
    allowed_unit_codes: Iterable[Any],
    unidad_negocio_id: str | None = None,
    page: int = 1,
    page_size: int = 100,
    query_executor: QueryExecutor | None = None,
) -> dict[str, Any]:
    """Lista paginada de encabezados reconstruidos desde detalle canónico."""

    start = _date_string(fecha_inicio, "fecha_inicio")
    end = _date_string(fecha_fin, "fecha_fin")

    if start > end:
        raise ValueError(
            "fecha_inicio no puede ser posterior a fecha_fin"
        )

    page = int(page)
    page_size = int(page_size)

    if page < 1:
        raise ValueError("page debe ser mayor o igual a 1")

    if page_size < 1 or page_size > 200:
        raise ValueError("page_size debe estar entre 1 y 200")

    allowed = _normalize_allowed_units(allowed_unit_codes)

    if not allowed:
        raise PermissionError(
            "El usuario no tiene unidades permitidas"
        )

    requested_unit = (
        _required(unidad_negocio_id, "unidad_negocio_id")
        if unidad_negocio_id is not None
        else None
    )

    if requested_unit:
        _ensure_unit_allowed(requested_unit, allowed)
        effective_units = [requested_unit]
    else:
        effective_units = allowed

    if (
        requested_unit
        and start == end
        and query_executor is None
    ):
        return _list_current_day_with_comercial_merge(
            operation_date=start,
            unit_code=requested_unit,
            page=page,
            page_size=page_size,
        )

    placeholders = ", ".join(["%s"] * len(effective_units))

    where_sql = f"""
        ISNULL(d.activo, 1) = 1
        AND ISNULL(d.es_kpi_valido, 1) = 1
        AND ISNULL(d.cancelado_origen, 0) = 0
        AND d.numero_ticket IS NOT NULL
        AND d.fecha_operacion BETWEEN %s AND %s
        AND d.unidad_negocio_id IN ({placeholders})
    """

    base_params: tuple[Any, ...] = (
        start,
        end,
        *effective_units,
    )

    count_sql = f"""
        SELECT COUNT(*) AS total
        FROM (
            SELECT
                d.unidad_negocio_id,
                d.fecha_operacion,
                d.numero_ticket
            FROM {DETAIL_TABLE} AS d
            WHERE {where_sql}
            GROUP BY
                d.unidad_negocio_id,
                d.fecha_operacion,
                d.numero_ticket
        ) AS tickets
    """

    count_rows = _execute(
        count_sql,
        base_params,
        query_executor=query_executor,
    )

    total = int(
        count_rows[0].get("total") or 0
    ) if count_rows else 0

    offset = (page - 1) * page_size

    data_sql = f"""
        SELECT
            d.unidad_negocio_id,
            MAX(d.unidad_negocio_nombre) AS unidad,
            MAX(d.sucursal_nombre) AS sucursal,
            d.fecha_operacion,
            d.numero_ticket,
            MIN(d.fecha_hora) AS fecha_hora,
            MAX(ISNULL(d.pax, 0)) AS pax,
            COUNT(*) AS lineas,
            SUM(ISNULL(d.importe_neto, 0)) AS ventas,
            SUM(ISNULL(d.propina, 0)) AS propina
        FROM {DETAIL_TABLE} AS d
        WHERE {where_sql}
        GROUP BY
            d.unidad_negocio_id,
            d.fecha_operacion,
            d.numero_ticket
        ORDER BY
            MIN(d.fecha_hora) DESC,
            d.unidad_negocio_id,
            d.numero_ticket
        OFFSET %s ROWS
        FETCH NEXT %s ROWS ONLY
    """

    rows = _execute(
        data_sql,
        (
            *base_params,
            offset,
            page_size,
        ),
        query_executor=query_executor,
    )

    items = []

    for row in rows:
        unit_code = _required(
            row.get("unidad_negocio_id"),
            "unidad_negocio_id",
        )
        operation_date = _date_string(
            row.get("fecha_operacion"),
            "fecha_operacion",
        )
        ticket_number = _required(
            row.get("numero_ticket"),
            "numero_ticket",
        )

        raw_datetime = row.get("fecha_hora")
        hour = ""

        if isinstance(raw_datetime, datetime):
            hour = raw_datetime.strftime("%H:%M")
        elif raw_datetime:
            text = str(raw_datetime)
            hour = text[11:16] if len(text) >= 16 else ""

        items.append({
            "ticket_pk": create_ticket_pk(
                unidad_negocio_id=unit_code,
                fecha_operacion=operation_date,
                numero_ticket=ticket_number,
            ),
            "unidad_negocio_id": unit_code,
            "unidad": row.get("unidad") or unit_code,
            "sucursal": row.get("sucursal"),
            "fecha_operacion": operation_date,
            "fecha": operation_date,
            "hora": hour,
            "numero_ticket": ticket_number,
            "pax": int(row.get("pax") or 0),
            "lineas": int(row.get("lineas") or 0),
            "ventas": round(float(row.get("ventas") or 0), 2),
            "propina": round(float(row.get("propina") or 0), 2),
        })

    returned = len(items)

    return {
        "items": items,
        "page": page,
        "page_size": page_size,
        "total": total,
        "returned": returned,
        "has_more": offset + returned < total,
        "traceability": {
            "source": DETAIL_TABLE,
            "temporal_field": "fecha_operacion",
            "live": False,
            "paginated": True,
        },
    }


def get_ticket_detail(
    *,
    identity: TicketIdentity,
    allowed_unit_codes: Iterable[Any],
    query_executor: QueryExecutor | None = None,
) -> dict[str, Any]:
    """Reconstruye un ticket exclusivamente desde su identidad validada."""

    _ensure_unit_allowed(
        identity.unidad_negocio_id,
        allowed_unit_codes,
    )

    if query_executor is None:
        comercial_ticket = _fallback_ticket_from_comercial(identity)
        if comercial_ticket:
            comercial_ticket.setdefault(
                "traceability",
                {},
            )["contract"] = (
                "TABLERO_COMERCIAL_TICKET_CERTIFIED_PATH"
            )
            return comercial_ticket

    sql = f"""
        SELECT
            {", ".join("d." + field for field in FIELDS)},
            d.unidad_negocio_id,
            d.unidad_negocio_nombre AS unidad,
            d.sucursal_nombre AS sucursal,
            d.fecha_operacion,
            d.numero_ticket,
            MIN(d.fecha_hora) OVER () AS primera_fecha_hora,
            d.producto_codigo_fuente AS codigo,
            d.producto_nombre AS producto,
            d.familia_nombre AS familia,
            d.subfamilia_nombre AS subfamilia,
            ISNULL(
                cc.Codigo,
                'PENDIENTE_CLASIFICACION'
            ) AS clasificacion,
            e.grupo_comercial AS casa,
            e.marca,
            e.grado_alcohol,
            e.es_alcoholico,
            d.cantidad,
            d.precio_unitario,
            d.importe_bruto AS importe_bruto,
            d.importe_neto AS importe,
            d.descuento AS descuento,
            d.propina,
            d.pax
        FROM {DETAIL_TABLE} AS d
        LEFT JOIN {PRODUCT_SYNC_TABLE} AS p
            ON p.ProductoID = d.producto_id
        LEFT JOIN {CLASSIFICATION_TABLE} AS cc
            ON cc.ClasificacionProductoID =
               p.ClasificacionProductoID
        LEFT JOIN {ENRICHMENT_TABLE} AS e
            ON e.producto_id = d.producto_id
        WHERE
            ISNULL(d.activo, 1) = 1
            AND ISNULL(d.es_kpi_valido, 1) = 1
            AND ISNULL(d.cancelado_origen, 0) = 0
            AND d.unidad_negocio_id = %s
            AND d.fecha_operacion = %s
            AND CONVERT(varchar(128), d.numero_ticket) = %s
        ORDER BY
            d.importe_neto DESC,
            d.producto_nombre
    """

    rows = _execute(
        sql,
        (
            identity.unidad_negocio_id,
            identity.fecha_operacion,
            identity.numero_ticket,
        ),
        query_executor=query_executor,
    )

    if not rows:
        if query_executor is None:
            fallback = _fallback_ticket_from_comercial(identity)
            if fallback:
                return fallback
        raise LookupError("Ticket no encontrado")

    lines = []

    for index, row in enumerate(rows, start=1):
        lines.append({
            **fields_from(row),
            "comentario_descuento": discount_comment(row),
            "linea_pk": (
                f"{identity.numero_ticket}:"
                f"{index}:"
                f"{row.get('codigo') or ''}"
            ),
            "codigo": row.get("codigo") or "",
            "producto": row.get("producto") or "",
            "familia": str(
                row.get("familia") or ""
            ).strip(),
            "subfamilia": str(
                row.get("subfamilia") or ""
            ).strip(),
            "clasificacion": str(
                row.get("clasificacion") or ""
            ).strip(),
            "casa": str(row.get("casa") or "").strip(),
            "marca": str(row.get("marca") or "").strip(),
            "grado_alcohol": (
                round(float(row["grado_alcohol"]), 1)
                if row.get("grado_alcohol") is not None
                else None
            ),
            "es_alcoholico": bool(
                row.get("es_alcoholico")
            ),
            "cantidad": round(
                float(row.get("cantidad") or 0),
                2,
            ),
            "precio_unitario": round(
                float(row.get("precio_unitario") or 0),
                2,
            ),
            "importe_bruto": round(
                float(
                    row.get("importe_bruto")
                    if row.get("importe_bruto") is not None
                    else row.get("importe")
                    or 0
                ),
                2,
            ),
            "importe": round(
                float(row.get("importe") or 0),
                2,
            ),
            "descuento": round(
                float(row.get("descuento") or 0),
                2,
            ),
            "propina": round(
                float(row.get("propina") or 0),
                2,
            ),
            "pax": int(row.get("pax") or 0),
        })

    first = rows[0]
    subtotal = round(
        sum(line["importe_bruto"] for line in lines),
        2,
    )
    descuento = round(
        sum(line["descuento"] for line in lines),
        2,
    )
    total = round(
        sum(line["importe"] for line in lines),
        2,
    )
    propina = round(
        sum(line["propina"] for line in lines),
        2,
    )
    pax = max(
        [line["pax"] for line in lines],
        default=0,
    )

    return {
        "ticket": {
            **header_from(rows),
            "unidad_negocio_id": identity.unidad_negocio_id,
            "unidad": (
                first.get("unidad")
                or identity.unidad_negocio_id
            ),
            "sucursal": first.get("sucursal"),
            "fecha_operacion": identity.fecha_operacion,
            "fecha": identity.fecha_operacion,
            "fecha_hora": str(
                first.get("primera_fecha_hora")
                or identity.fecha_operacion
            ),
            "numero_ticket": identity.numero_ticket,
            "estado": "CERRADA",
            "pax": pax,
            "lineas": len(lines),
            "subtotal": subtotal,
            "descuento": descuento,
            "impuesto": None,
            "ventas": total,
            "total": total,
            "propina": propina,
        },
        "lines": lines,
        "lineas": lines,
        "traceability": {
            "source": DETAIL_TABLE,
            "temporal_field": "fecha_operacion",
            "live": False,
            "identity_version": identity.version,
        },
    }
