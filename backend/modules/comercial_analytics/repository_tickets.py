from __future__ import annotations

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

    placeholders = ", ".join(["%s"] * len(effective_units))

    where_sql = f"""
        ISNULL(d.activo, 1) = 1
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

    sql = f"""
        SELECT
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
            d.importe_neto AS importe,
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
            AND d.unidad_negocio_id = %s
            AND d.fecha_operacion = %s
            AND d.numero_ticket = %s
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
        raise LookupError("Ticket no encontrado")

    lines = []

    for index, row in enumerate(rows, start=1):
        lines.append({
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
            "importe": round(
                float(row.get("importe") or 0),
                2,
            ),
            "propina": round(
                float(row.get("propina") or 0),
                2,
            ),
            "pax": int(row.get("pax") or 0),
        })

    first = rows[0]
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
            "unidad_negocio_id": identity.unidad_negocio_id,
            "unidad": (
                first.get("unidad")
                or identity.unidad_negocio_id
            ),
            "sucursal": first.get("sucursal"),
            "fecha_operacion": identity.fecha_operacion,
            "fecha": identity.fecha_operacion,
            "numero_ticket": identity.numero_ticket,
            "pax": pax,
            "lineas": len(lines),
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
