from __future__ import annotations

from datetime import date, datetime
from typing import Any, Callable, Iterable

from core.utils.operational_window import get_fecha_operacion_now, get_operational_window
from modules.comercial_v2.repository_readonly import (
    get_ventas_dia_abiertas,
)

from .operational_service import build_operational_snapshot


OperationalDateResolver = Callable[[str], date]
OperationalContextResolver = Callable[[str], dict[str, Any]]
OpenSalesReader = Callable[[date, list[str]], list[dict[str, Any]]]


class OperationalDateResolutionError(RuntimeError):
    """No fue posible resolver la fecha operativa de una unidad."""


def _required(value: Any, field: str) -> str:
    normalized = str(value or "").strip()

    if not normalized:
        raise ValueError(f"{field} es obligatorio")

    return normalized


def _normalize_date(value: Any) -> date:
    if isinstance(value, datetime):
        return value.date()

    if isinstance(value, date):
        return value

    try:
        return date.fromisoformat(str(value or "").strip()[:10])
    except ValueError as exc:
        raise OperationalDateResolutionError(
            "El motor devolvió una fecha_operacion inválida"
        ) from exc


def resolve_current_operational_context(unit_code: str) -> dict[str, Any]:
    """Resuelve fecha + estado de ventana para la operación en curso.

    La fecha operativa por sí sola no alcanza para decidir qué debe mostrarse
    en Ventas del Día. También se necesita saber si estamos realmente dentro
    de un turno que cruza medianoche o solamente antes del primer turno.
    """
    code = _required(unit_code, "unidad_negocio_id")

    try:
        window = get_operational_window(code)
    except Exception as exc:
        raise OperationalDateResolutionError(
            f"No fue posible resolver contexto operativo para {code}"
        ) from exc

    return {
        "fecha_operacion": _normalize_date(window.fecha_operacion),
        "metodo_fecha_operacion": str(
            getattr(window, "metodo_fecha_operacion", "") or ""
        ),
        "turno_operativo_codigo": str(
            getattr(window, "turno_operativo_codigo", "") or ""
        ),
        "timestamp_consulta": getattr(window, "timestamp_consulta", None),
    }

def resolve_current_operational_date(unit_code: str) -> date:
    """Compatibilidad: devuelve sólo la fecha del contexto operativo."""
    return resolve_current_operational_context(unit_code)["fecha_operacion"]


def _zero_closed_portion(row: dict[str, Any], policy: str) -> dict[str, Any]:
    result = dict(row)
    result["ventas_cerradas_dia"] = 0
    result["propinas_cerradas_dia"] = 0
    result["tickets_cerrados_dia"] = 0
    result["pax_cerrados_dia"] = 0
    result["total_estimado_dia"] = result.get("ventas_abiertas") or 0
    result["propinas_total"] = result.get("propinas_abiertas") or 0
    result["current_display_policy"] = policy
    return result


def _apply_current_display_policy(
    source_row: dict[str, Any] | None,
    *,
    operation_date: date,
    operation_context: dict[str, Any] | None,
) -> dict[str, Any] | None:
    """Evita arrastrar cierres históricos a Ventas del Día.

    La fecha operativa puede ser ayer por diseño. Eso NO implica que la venta
    cerrada de ayer siga siendo operación vigente:

    - SoftRestaurant: si ya existe porción en ``cheques`` para una fecha
      anterior, esa porción ya pasó por corte y pertenece al histórico. Sólo
      ``tempcheques`` puede seguir visible como arrastre abierto.
    - MPRO: antes del primer turno, las ventas cerradas de la fecha anterior
      son históricas. Durante un turno activo que cruza medianoche sí forman
      parte de la operación vigente.
    """
    if not source_row or not operation_context:
        return source_row

    timestamp = operation_context.get("timestamp_consulta")
    if not isinstance(timestamp, datetime):
        return source_row

    if operation_date >= timestamp.date():
        result = dict(source_row)
        result["current_display_policy"] = "CURRENT_OPERATION_DATE"
        return result

    sistema = str(source_row.get("sistema_origen") or "").strip().upper()
    metodo = str(
        operation_context.get("metodo_fecha_operacion") or ""
    ).strip().upper()

    if "SOFT" in sistema:
        cut_detected = (
            float(source_row.get("ventas_cerradas_dia") or 0) != 0
            or int(source_row.get("tickets_cerrados_dia") or 0) != 0
        )
        if cut_detected:
            return _zero_closed_portion(
                source_row,
                "SOFT_PREVIOUS_DATE_AFTER_CUT_OPEN_ONLY",
            )

        result = dict(source_row)
        result["current_display_policy"] = (
            "SOFT_PREVIOUS_DATE_UNCUT"
        )
        return result

    if "MPRO" in sistema:
        before_first_turn = (
            metodo.startswith("ANTES_PRIMER_TURNO")
            or metodo == "FALLBACK_ENTRE_TURNOS"
        )
        if before_first_turn:
            return _zero_closed_portion(
                source_row,
                "MPRO_PREVIOUS_DATE_BEFORE_FIRST_TURN_OPEN_ONLY",
            )

        result = dict(source_row)
        result["current_display_policy"] = (
            "MPRO_PREVIOUS_DATE_ACTIVE_WINDOW"
        )
        return result

    return source_row

def _snapshot_rows(
    source_row: dict[str, Any] | None,
    *,
    unit_code: str,
    operation_date: date,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    row = source_row or {}

    closed = [{
        "unidad_negocio_id": unit_code,
        "fecha_operacion": operation_date.isoformat(),
        "ventas": row.get("ventas_cerradas_dia") or 0,
        "propinas": row.get("propinas_cerradas_dia") or 0,
        "cheques": row.get("tickets_cerrados_dia") or 0,
        "pax": row.get("pax_cerrados_dia") or 0,
    }]

    opened = [{
        "unidad_negocio_id": unit_code,
        "fecha_operacion": operation_date.isoformat(),
        "ventas": row.get("ventas_abiertas") or 0,
        "propinas": row.get("propinas_abiertas") or 0,
        "cheques": row.get("tickets_abiertos") or 0,
        "pax": row.get("pax_abiertos") or 0,
    }]

    return closed, opened


def build_current_operation(
    *,
    allowed_unit_codes: Iterable[Any],
    date_resolver: OperationalDateResolver | None = None,
    operation_context_resolver: OperationalContextResolver | None = None,
    sales_reader: OpenSalesReader | None = None,
    generated_at: datetime | None = None,
) -> dict[str, Any]:
    """Construye operación vigente por unidad.

    Cada unidad resuelve su propia fecha_operacion vigente. Una unidad sin
    snapshot para esa fecha devuelve ceros. Nunca se consulta otra fecha.
    """
    resolver = date_resolver or resolve_current_operational_date
    context_resolver = operation_context_resolver
    reader = sales_reader or get_ventas_dia_abiertas

    unit_codes = sorted({
        _required(value, "unidad_negocio_id")
        for value in allowed_unit_codes
        if str(value or "").strip()
    })

    if not unit_codes:
        raise PermissionError(
            "El usuario no tiene unidades permitidas"
        )

    items: list[dict[str, Any]] = []
    unresolved_units: list[dict[str, str]] = []

    totals = {
        "cerradas": {
            "ventas": 0.0,
            "propinas": 0.0,
            "cheques": 0,
            "pax": 0,
        },
        "abiertas": {
            "ventas": 0.0,
            "propinas": 0.0,
            "cheques": 0,
            "pax": 0,
        },
        "operacion_estimada": {
            "ventas": 0.0,
            "propinas": 0.0,
            "cheques": 0,
            "pax": 0,
        },
    }

    effective_dates: set[str] = set()

    for unit_code in unit_codes:
        operation_context = None
        try:
            if context_resolver is not None:
                operation_context = context_resolver(unit_code)
                operation_date = _normalize_date(
                    operation_context.get("fecha_operacion")
                )
            elif date_resolver is None:
                operation_context = resolve_current_operational_context(
                    unit_code
                )
                operation_date = _normalize_date(
                    operation_context.get("fecha_operacion")
                )
            else:
                operation_date = _normalize_date(
                    resolver(unit_code)
                )
        except Exception as exc:
            unresolved_units.append({
                "unidad_negocio_id": unit_code,
                "error": str(exc),
            })
            continue

        rows = list(
            reader(operation_date, [unit_code]) or []
        )

        exact_rows = [
            row
            for row in rows
            if str(
                row.get("fecha_operacion") or ""
            )[:10] == operation_date.isoformat()
        ]

        source_row = exact_rows[0] if exact_rows else None
        source_row = _apply_current_display_policy(
            source_row,
            operation_date=operation_date,
            operation_context=operation_context,
        )
        closed_rows, open_rows = _snapshot_rows(
            source_row,
            unit_code=unit_code,
            operation_date=operation_date,
        )

        snapshot = build_operational_snapshot(
            effective_operational_date=operation_date,
            allowed_units=[{
                "unidad_negocio_id": unit_code,
                "unidad_negocio_nombre": (
                    (source_row or {}).get(
                        "unidad_negocio_nombre"
                    )
                    or unit_code
                ),
            }],
            closed_rows=closed_rows,
            open_rows=open_rows,
            generated_at=generated_at,
        )

        item = snapshot["items"][0]

        # Metadatos de conexión necesarios para que el Ejecutivo reutilice
        # exactamente el drill-down certificado de Tablero Comercial.
        if source_row:
            item["server_id"] = source_row.get("server_id")
            item["sucursal_id"] = source_row.get("sucursal_id")
            item["sucursal_nombre"] = source_row.get("sucursal_nombre")
            item["sistema_origen"] = source_row.get("sistema_origen")
            item["current_display_policy"] = source_row.get(
                "current_display_policy"
            )

        if operation_context:
            item["metodo_fecha_operacion"] = operation_context.get(
                "metodo_fecha_operacion"
            )
            item["turno_operativo_codigo"] = operation_context.get(
                "turno_operativo_codigo"
            )

        effective_dates.add(item["fecha_operacion"])
        items.append(item)

        for domain in (
            "cerradas",
            "abiertas",
            "operacion_estimada",
        ):
            totals[domain]["ventas"] += (
                item[domain]["ventas"]
            )
            totals[domain]["propinas"] += (
                item[domain]["propinas"]
            )
            totals[domain]["cheques"] += (
                item[domain]["cheques"]
            )
            totals[domain]["pax"] += item[domain]["pax"]

    for domain in totals.values():
        domain["ventas"] = round(
            float(domain["ventas"]),
            2,
        )
        domain["propinas"] = round(
            float(domain["propinas"]),
            2,
        )

    items.sort(
        key=lambda item: (
            -float(
                item["operacion_estimada"]["ventas"]
            ),
            item["unidad_negocio_id"],
        )
    )


    # EDARSAHUB_PER_UNIT_OPERATION_DATE_V2
    # Cada unidad conserva su propia fecha_operacion canónica. Es válido que
    # distintas sucursales estén simultáneamente en fechas operativas distintas
    # por sus horarios/cortes. Nunca neutralizar KPIs a cero para forzar una
    # fecha común artificial.
    common_operation_date = (
        next(iter(effective_dates))
        if len(effective_dates) == 1
        else None
    )

    return {
        "fecha_operacion": (
            next(iter(effective_dates))
            if len(effective_dates) == 1
            else None
        ),
        "fechas_operacion": sorted(effective_dates),
        "fecha_operacion_multiple": (
            len(effective_dates) > 1
        ),
        "items": items,
        "totales": totals,
        "unidades_sin_fecha_operativa": unresolved_units,
        "traceability": {
            "domain": "operacion_en_curso",
            "source": (
                "Comercial_Ventas_Dia_Abiertas_v2"
            ),
            "operational_date_source": (
                "core.utils.operational_window."
                "get_fecha_operacion_now"
            ),
            "temporal_field": "fecha_operacion",
            "formula": (
                "cerradas_vigentes_mas_abiertas_vigentes"
            ),
            "fallback_to_last_data_date": False,
            "fallback_to_civil_date": False,
            "historical": False,
            "live": True,
        },
    }
