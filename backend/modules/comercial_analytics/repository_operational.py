from __future__ import annotations

from datetime import date, datetime
from typing import Any, Callable, Iterable

from core.utils.operational_window import get_fecha_operacion_now
from modules.comercial_v2.repository_readonly import (
    get_ventas_dia_abiertas,
)

from .operational_service import build_operational_snapshot


OperationalDateResolver = Callable[[str], date]
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


def resolve_current_operational_date(unit_code: str) -> date:
    """Resuelve la fecha operativa vigente sin fallback.

    Está prohibido sustituirla por:
    - MAX(fecha_operacion) de SQL;
    - la última fecha sincronizada;
    - fecha civil local;
    - fecha UTC.
    """
    code = _required(unit_code, "unidad_negocio_id")

    attempts = (
        lambda: get_fecha_operacion_now(code),
        lambda: get_fecha_operacion_now(
            unidad_negocio_id=code,
        ),
        lambda: get_fecha_operacion_now(
            unidad_negocio_pk=code,
        ),
    )

    last_type_error: TypeError | None = None

    for attempt in attempts:
        try:
            result = attempt()
        except TypeError as exc:
            last_type_error = exc
            continue
        except Exception as exc:
            raise OperationalDateResolutionError(
                f"No fue posible resolver fecha_operacion para {code}"
            ) from exc

        if result is None:
            raise OperationalDateResolutionError(
                f"El motor no devolvió fecha_operacion para {code}"
            )

        return _normalize_date(result)

    raise OperationalDateResolutionError(
        f"Firma no compatible de get_fecha_operacion_now para {code}"
    ) from last_type_error


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
    sales_reader: OpenSalesReader | None = None,
    generated_at: datetime | None = None,
) -> dict[str, Any]:
    """Construye operación vigente por unidad.

    Cada unidad resuelve su propia fecha_operacion vigente. Una unidad sin
    snapshot para esa fecha devuelve ceros. Nunca se consulta otra fecha.
    """
    resolver = date_resolver or resolve_current_operational_date
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
        try:
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
