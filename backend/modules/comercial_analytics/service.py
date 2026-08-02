from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime, timedelta
from typing import Any, Iterable

from core.kpis_canonicos.service import KPIsCanonicosService

from .schemas import (
    CommercialDrilldownRequest,
    CommercialMetric,
    DrilldownLevel,
)


_METRIC_KEYS = {
    CommercialMetric.VENTAS: (
        "ventas_total",
        "ventas",
        "ventas_totales",
    ),
    CommercialMetric.PAX: (
        "pax_total",
        "pax",
    ),
    CommercialMetric.CHEQUES: (
        "tickets_total",
        "tickets",
        "cheques",
        "cheques_total",
    ),
}


def _number(row: dict[str, Any], *keys: str) -> float:
    containers = [
        row,
        row.get("metricas") if isinstance(row.get("metricas"), dict) else {},
        row.get("atomos") if isinstance(row.get("atomos"), dict) else {},
    ]

    for container in containers:
        for key in keys:
            value = container.get(key)
            if value is not None:
                try:
                    return float(value)
                except (TypeError, ValueError):
                    continue

    return 0.0


def _date_value(row: dict[str, Any]) -> date | None:
    raw = (
        row.get("fecha_operacion")
        or row.get("fecha")
        or row.get("periodo")
    )

    if isinstance(raw, datetime):
        return raw.date()

    if isinstance(raw, date):
        return raw

    if isinstance(raw, str) and len(raw) >= 10:
        try:
            return datetime.strptime(raw[:10], "%Y-%m-%d").date()
        except ValueError:
            return None

    return None


def _unit_identity(row: dict[str, Any]) -> tuple[str, str, str]:
    unit_pk = str(
        row.get("unidad_negocio_pk")
        or row.get("unidad_pk")
        or row.get("business_unit_pk")
        or ""
    )

    unit_code = str(
        row.get("unidad_negocio_id")
        or row.get("unidad_codigo")
        or row.get("business_unit_code")
        or ""
    )

    unit_name = str(
        row.get("unidad_negocio_nombre")
        or row.get("unidad_nombre")
        or row.get("unidad")
        or unit_code
        or unit_pk
    )

    return unit_pk, unit_code, unit_name


def _period_bounds(periods: Iterable[Any]) -> tuple[str, str]:
    starts: list[date] = []
    ends: list[date] = []

    for period in periods:
        for month in period.months:
            start = date(period.year, month, 1)

            if month == 12:
                next_month = date(period.year + 1, 1, 1)
            else:
                next_month = date(period.year, month + 1, 1)

            starts.append(start)
            ends.append(next_month - timedelta(days=1))

    return min(starts).isoformat(), max(ends).isoformat()


def _allowed_dates(periods: Iterable[Any]) -> set[tuple[int, int]]:
    return {
        (period.year, month)
        for period in periods
        for month in period.months
    }


def _series(
    request: CommercialDrilldownRequest,
    unit_name: str | None,
) -> list[dict[str, Any]]:
    start, end_inclusive = _period_bounds(request.scope.periods)

    end_exclusive = (
        datetime.strptime(end_inclusive, "%Y-%m-%d").date()
        + timedelta(days=1)
    ).isoformat()

    rows = KPIsCanonicosService.series_periodo(
        desde=start,
        hasta=end_exclusive,
        nivel="dia",
        unidad_nombre=unit_name,
    )

    return list(rows or [])


def build_drilldown(
    request: CommercialDrilldownRequest,
    *,
    allowed_unit_codes: list[str],
) -> dict[str, Any]:
    allowed_periods = _allowed_dates(request.scope.periods)

    requested_code = request.business_unit_code
    if requested_code and requested_code not in allowed_unit_codes:
        raise PermissionError("La unidad solicitada está fuera del alcance RBAC")

    rows = _series(request, requested_code)

    filtered: list[dict[str, Any]] = []

    for row in rows:
        operation_date = _date_value(row)
        if not operation_date:
            continue

        if (operation_date.year, operation_date.month) not in allowed_periods:
            continue

        unit_pk, unit_code, _ = _unit_identity(row)

        if allowed_unit_codes and unit_code not in allowed_unit_codes:
            continue

        if request.business_unit_pk and unit_pk != request.business_unit_pk:
            continue

        if request.business_unit_code and unit_code != request.business_unit_code:
            continue

        if request.year and operation_date.year != request.year:
            continue

        if request.month and operation_date.month != request.month:
            continue

        if (
            request.operational_date
            and operation_date.isoformat() != request.operational_date
        ):
            continue

        filtered.append(row)

    metric_keys = _METRIC_KEYS[request.metric]
    grouped: dict[str, dict[str, Any]] = defaultdict(
        lambda: {
            "key": "",
            "label": "",
            "value": 0.0,
            "ventas": 0.0,
            "pax": 0,
            "cheques": 0,
        }
    )

    for row in filtered:
        operation_date = _date_value(row)
        unit_pk, unit_code, unit_name = _unit_identity(row)

        if request.level == DrilldownLevel.BUSINESS_UNIT:
            key = unit_pk or unit_code
            label = unit_name
            metadata = {
                "business_unit_pk": unit_pk or None,
                "business_unit_code": unit_code or None,
            }

        elif request.level == DrilldownLevel.YEAR:
            key = str(operation_date.year)
            label = key
            metadata = {"year": operation_date.year}

        elif request.level == DrilldownLevel.MONTH:
            key = f"{operation_date.year}-{operation_date.month:02d}"
            label = key
            metadata = {
                "year": operation_date.year,
                "month": operation_date.month,
            }

        else:
            key = operation_date.isoformat()
            label = key
            metadata = {"operational_date": key}

        item = grouped[key]
        item["key"] = key
        item["label"] = label
        item.update(metadata)

        item["value"] += _number(row, *metric_keys)
        item["ventas"] += _number(
            row,
            "ventas_total",
            "ventas",
            "ventas_totales",
        )
        item["pax"] += int(_number(row, "pax_total", "pax"))
        item["cheques"] += int(
            _number(
                row,
                "tickets_total",
                "tickets",
                "cheques",
                "cheques_total",
            )
        )

    items = list(grouped.values())

    reverse = request.level != DrilldownLevel.OPERATIONAL_DAY
    items.sort(key=lambda item: item["key"], reverse=reverse)

    for item in items:
        if request.metric != CommercialMetric.VENTAS:
            item["value"] = int(item["value"])
        else:
            item["value"] = round(item["value"], 2)

        item["ventas"] = round(item["ventas"], 2)

    return {
        "metric": request.metric.value,
        "level": request.level.value,
        "items": items,
        "total": (
            round(sum(item["value"] for item in items), 2)
            if request.metric == CommercialMetric.VENTAS
            else int(sum(item["value"] for item in items))
        ),
        "traceability": {
            "source": "KPIS_CANONICOS_SERVICE",
            "temporal_field": "fecha_operacion",
            "live": False,
            "frontend_aggregation": False,
        },
    }
