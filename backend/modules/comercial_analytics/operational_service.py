from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any, Iterable


class OperationalSnapshotError(ValueError):
    """El contrato de operación en curso recibió datos inválidos."""


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
        raise OperationalSnapshotError(
            f"{field} inválida"
        ) from exc


def _required(value: Any, field: str) -> str:
    normalized = str(value or "").strip()

    if not normalized:
        raise OperationalSnapshotError(
            f"{field} es obligatorio"
        )

    return normalized


def _decimal(value: Any) -> Decimal:
    try:
        return Decimal(str(value or 0))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise OperationalSnapshotError(
            "Importe numérico inválido"
        ) from exc


def _integer(value: Any) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError) as exc:
        raise OperationalSnapshotError(
            "Contador inválido"
        ) from exc


def _normalize_units(
    allowed_units: Iterable[dict[str, Any]],
) -> list[dict[str, str]]:
    normalized = []
    seen = set()

    for unit in allowed_units:
        code = _required(
            unit.get("unidad_negocio_id")
            or unit.get("codigo")
            or unit.get("id"),
            "unidad_negocio_id",
        )

        if code in seen:
            continue

        seen.add(code)

        normalized.append({
            "unidad_negocio_id": code,
            "unidad_negocio_nombre": str(
                unit.get("unidad_negocio_nombre")
                or unit.get("nombre")
                or code
            ).strip(),
        })

    return normalized


def _aggregate_rows(
    rows: Iterable[dict[str, Any]],
    *,
    effective_operational_date: str,
    allowed_codes: set[str],
) -> dict[str, dict[str, Any]]:
    """Agrega únicamente filas de la fecha operativa vigente.

    Cualquier fila de otra fecha_operacion se ignora.
    No existe fallback ni reanclaje.
    """
    totals: dict[str, dict[str, Any]] = defaultdict(
        lambda: {
            "ventas": Decimal("0"),
            "propinas": Decimal("0"),
            "cheques": 0,
            "pax": 0,
        }
    )

    for row in rows:
        unit_code = str(
            row.get("unidad_negocio_id")
            or row.get("unidad")
            or ""
        ).strip()

        if not unit_code or unit_code not in allowed_codes:
            continue

        row_date = _date_string(
            row.get("fecha_operacion"),
            "fecha_operacion",
        )

        if row_date != effective_operational_date:
            continue

        current = totals[unit_code]

        current["ventas"] += _decimal(
            row.get("ventas")
            if row.get("ventas") is not None
            else row.get("ventas_total")
        )

        current["propinas"] += _decimal(
            row.get("propinas")
            if row.get("propinas") is not None
            else row.get("propinas_total")
        )

        current["cheques"] += _integer(
            row.get("cheques")
            if row.get("cheques") is not None
            else row.get("tickets_total")
        )

        current["pax"] += _integer(
            row.get("pax")
            if row.get("pax") is not None
            else row.get("pax_total")
        )

    return totals


def build_operational_snapshot(
    *,
    effective_operational_date: Any,
    allowed_units: Iterable[dict[str, Any]],
    closed_rows: Iterable[dict[str, Any]],
    open_rows: Iterable[dict[str, Any]],
    generated_at: Any | None = None,
) -> dict[str, Any]:
    """Construye el único contrato de Operación en curso.

    Reglas:
    - Todas las unidades permitidas aparecen, incluso en ceros.
    - Solo incluye la fecha_operacion vigente.
    - Cerradas y abiertas se muestran separadas.
    - La estimación operativa es cerradas + abiertas.
    - No consulta ni sustituye por el último día con datos.
    - No modifica ni representa el histórico consolidado.
    """
    operation_date = _date_string(
        effective_operational_date,
        "effective_operational_date",
    )

    units = _normalize_units(allowed_units)
    allowed_codes = {
        unit["unidad_negocio_id"]
        for unit in units
    }

    closed = _aggregate_rows(
        closed_rows,
        effective_operational_date=operation_date,
        allowed_codes=allowed_codes,
    )

    opened = _aggregate_rows(
        open_rows,
        effective_operational_date=operation_date,
        allowed_codes=allowed_codes,
    )

    items = []

    total_closed_sales = Decimal("0")
    total_open_sales = Decimal("0")
    total_closed_tips = Decimal("0")
    total_open_tips = Decimal("0")
    total_closed_checks = 0
    total_open_checks = 0
    total_closed_pax = 0
    total_open_pax = 0

    for unit in units:
        code = unit["unidad_negocio_id"]

        closed_unit = closed.get(code, {
            "ventas": Decimal("0"),
            "propinas": Decimal("0"),
            "cheques": 0,
            "pax": 0,
        })

        open_unit = opened.get(code, {
            "ventas": Decimal("0"),
            "propinas": Decimal("0"),
            "cheques": 0,
            "pax": 0,
        })

        estimated_sales = (
            closed_unit["ventas"]
            + open_unit["ventas"]
        )

        estimated_tips = (
            closed_unit["propinas"]
            + open_unit["propinas"]
        )

        estimated_checks = (
            closed_unit["cheques"]
            + open_unit["cheques"]
        )

        estimated_pax = (
            closed_unit["pax"]
            + open_unit["pax"]
        )

        total_closed_sales += closed_unit["ventas"]
        total_open_sales += open_unit["ventas"]
        total_closed_tips += closed_unit["propinas"]
        total_open_tips += open_unit["propinas"]
        total_closed_checks += closed_unit["cheques"]
        total_open_checks += open_unit["cheques"]
        total_closed_pax += closed_unit["pax"]
        total_open_pax += open_unit["pax"]

        items.append({
            **unit,
            "fecha_operacion": operation_date,
            "cerradas": {
                "ventas": round(float(closed_unit["ventas"]), 2),
                "propinas": round(float(closed_unit["propinas"]), 2),
                "cheques": closed_unit["cheques"],
                "pax": closed_unit["pax"],
            },
            "abiertas": {
                "ventas": round(float(open_unit["ventas"]), 2),
                "propinas": round(float(open_unit["propinas"]), 2),
                "cheques": open_unit["cheques"],
                "pax": open_unit["pax"],
            },
            "operacion_estimada": {
                "ventas": round(float(estimated_sales), 2),
                "propinas": round(float(estimated_tips), 2),
                "cheques": estimated_checks,
                "pax": estimated_pax,
            },
        })

    total_estimated_sales = (
        total_closed_sales
        + total_open_sales
    )

    total_estimated_tips = (
        total_closed_tips
        + total_open_tips
    )

    total_estimated_checks = (
        total_closed_checks
        + total_open_checks
    )

    total_estimated_pax = (
        total_closed_pax
        + total_open_pax
    )

    generated = (
        generated_at.isoformat()
        if isinstance(generated_at, datetime)
        else str(generated_at or "")
    )

    return {
        "fecha_operacion": operation_date,
        "items": items,
        "totales": {
            "cerradas": {
                "ventas": round(float(total_closed_sales), 2),
                "propinas": round(float(total_closed_tips), 2),
                "cheques": total_closed_checks,
                "pax": total_closed_pax,
            },
            "abiertas": {
                "ventas": round(float(total_open_sales), 2),
                "propinas": round(float(total_open_tips), 2),
                "cheques": total_open_checks,
                "pax": total_open_pax,
            },
            "operacion_estimada": {
                "ventas": round(float(total_estimated_sales), 2),
                "propinas": round(float(total_estimated_tips), 2),
                "cheques": total_estimated_checks,
                "pax": total_estimated_pax,
            },
        },
        "traceability": {
            "domain": "operacion_en_curso",
            "historical": False,
            "live": True,
            "fallback_to_last_data_date": False,
            "temporal_field": "fecha_operacion",
            "formula": "cerradas_vigentes_mas_abiertas_vigentes",
            "generated_at": generated or None,
        },
    }
