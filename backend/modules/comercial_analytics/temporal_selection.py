from __future__ import annotations

from calendar import monthrange
from datetime import date, datetime, timedelta
from typing import Any, Callable, Iterable


class TemporalSelectionError(ValueError):
    """La selección temporal no cumple el contrato canónico."""


KeyDateResolver = Callable[
    [str, list[int]],
    Iterable[dict[str, Any]],
]


def _date(value: Any, field: str) -> date:
    if isinstance(value, datetime):
        return value.date()

    if isinstance(value, date):
        return value

    try:
        return date.fromisoformat(
            str(value or "").strip()[:10]
        )
    except ValueError as exc:
        raise TemporalSelectionError(
            f"{field} inválida"
        ) from exc


def _date_optional(value: Any, field: str) -> date | None:
    if value in (None, ""):
        return None

    return _date(value, field)


def _integer(value: Any, field: str) -> int:
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise TemporalSelectionError(
            f"{field} inválido"
        ) from exc


def _scope(
    selection: dict[str, Any],
    *,
    minimum_date: date,
    maximum_date: date,
) -> tuple[date, date]:
    scope = selection.get("scope") or {}

    start = _date_optional(
        scope.get("start_date"),
        "scope.start_date",
    ) or minimum_date

    end = _date_optional(
        scope.get("end_date"),
        "scope.end_date",
    ) or maximum_date

    if start > end:
        raise TemporalSelectionError(
            "scope.start_date no puede ser posterior a scope.end_date"
        )

    if start < minimum_date or end > maximum_date:
        raise TemporalSelectionError(
            "El alcance está fuera de la cobertura disponible"
        )

    return start, end


def _daterange(start: date, end: date) -> Iterable[date]:
    current = start

    while current <= end:
        yield current
        current += timedelta(days=1)


def _validate_coverage(
    values: Iterable[date],
    *,
    minimum_date: date,
    maximum_date: date,
) -> set[date]:
    result = set()

    for value in values:
        if value < minimum_date or value > maximum_date:
            raise TemporalSelectionError(
                f"Fecha fuera de cobertura: {value.isoformat()}"
            )

        result.add(value)

    return result


def _resolve_specific_dates(
    selection: dict[str, Any],
) -> set[date]:
    values = selection.get("dates") or []

    if not values:
        raise TemporalSelectionError(
            "dates debe contener al menos una fecha"
        )

    return {
        _date(value, "dates")
        for value in values
    }


def _resolve_ranges(
    selection: dict[str, Any],
) -> set[date]:
    ranges = selection.get("ranges") or []

    if not ranges:
        raise TemporalSelectionError(
            "ranges debe contener al menos un rango"
        )

    resolved: set[date] = set()

    for index, item in enumerate(ranges):
        start = _date(
            item.get("start_date"),
            f"ranges[{index}].start_date",
        )
        end = _date(
            item.get("end_date"),
            f"ranges[{index}].end_date",
        )

        if start > end:
            raise TemporalSelectionError(
                f"Rango inválido en posición {index}"
            )

        resolved.update(_daterange(start, end))

    return resolved


def _week_of_month(value: date) -> int:
    """Semana estable del mes.

    Semana 1: días 1-7
    Semana 2: días 8-14
    Semana 3: días 15-21
    Semana 4: días 22-28
    Semana 5: días 29-31
    """
    return ((value.day - 1) // 7) + 1


def _resolve_weekdays_rule(
    rule: dict[str, Any],
    *,
    start: date,
    end: date,
) -> set[date]:
    weekdays = {
        _integer(value, "weekdays")
        for value in (rule.get("weekdays") or [])
    }

    if not weekdays:
        raise TemporalSelectionError(
            "La regla weekdays requiere días de semana"
        )

    if any(value < 1 or value > 7 for value in weekdays):
        raise TemporalSelectionError(
            "Los días de semana deben estar entre 1 y 7"
        )

    return {
        value
        for value in _daterange(start, end)
        if value.isoweekday() in weekdays
    }


def _resolve_weekdays_in_month_weeks(
    rule: dict[str, Any],
    *,
    start: date,
    end: date,
) -> set[date]:
    weekdays = {
        _integer(value, "weekdays")
        for value in (rule.get("weekdays") or [])
    }
    month_weeks = {
        _integer(value, "month_weeks")
        for value in (rule.get("month_weeks") or [])
    }

    if not weekdays or not month_weeks:
        raise TemporalSelectionError(
            "La regla requiere weekdays y month_weeks"
        )

    if any(value < 1 or value > 7 for value in weekdays):
        raise TemporalSelectionError(
            "Los días de semana deben estar entre 1 y 7"
        )

    if any(value < 1 or value > 5 for value in month_weeks):
        raise TemporalSelectionError(
            "Las semanas del mes deben estar entre 1 y 5"
        )

    return {
        value
        for value in _daterange(start, end)
        if (
            value.isoweekday() in weekdays
            and _week_of_month(value) in month_weeks
        )
    }


def _nth_weekday(
    *,
    year: int,
    month: int,
    weekday: int,
    occurrence: int,
) -> date | None:
    first = date(year, month, 1)

    offset = (weekday - first.isoweekday()) % 7
    day_number = 1 + offset + ((occurrence - 1) * 7)

    last_day = monthrange(year, month)[1]

    if day_number > last_day:
        return None

    return date(year, month, day_number)


def _last_weekday(
    *,
    year: int,
    month: int,
    weekday: int,
) -> date:
    last_day = monthrange(year, month)[1]
    candidate = date(year, month, last_day)

    offset = (candidate.isoweekday() - weekday) % 7

    return candidate - timedelta(days=offset)


def _resolve_nth_weekday_of_month(
    rule: dict[str, Any],
    *,
    start: date,
    end: date,
) -> set[date]:
    weekday = _integer(
        rule.get("weekday"),
        "weekday",
    )
    occurrence = _integer(
        rule.get("occurrence"),
        "occurrence",
    )

    if weekday < 1 or weekday > 7:
        raise TemporalSelectionError(
            "weekday debe estar entre 1 y 7"
        )

    if occurrence not in {1, 2, 3, 4, 5, -1}:
        raise TemporalSelectionError(
            "occurrence debe ser 1-5 o -1 para último"
        )

    resolved: set[date] = set()
    cursor = date(start.year, start.month, 1)

    while cursor <= end:
        if occurrence == -1:
            candidate = _last_weekday(
                year=cursor.year,
                month=cursor.month,
                weekday=weekday,
            )
        else:
            candidate = _nth_weekday(
                year=cursor.year,
                month=cursor.month,
                weekday=weekday,
                occurrence=occurrence,
            )

        if candidate and start <= candidate <= end:
            resolved.add(candidate)

        if cursor.month == 12:
            cursor = date(cursor.year + 1, 1, 1)
        else:
            cursor = date(
                cursor.year,
                cursor.month + 1,
                1,
            )

    return resolved


def _resolve_rules(
    selection: dict[str, Any],
    *,
    start: date,
    end: date,
) -> set[date]:
    rules = selection.get("rules") or []

    if not rules:
        raise TemporalSelectionError(
            "rules debe contener al menos una regla"
        )

    resolved: set[date] = set()

    for rule in rules:
        rule_type = str(rule.get("type") or "").strip()

        if rule_type == "weekdays":
            resolved.update(
                _resolve_weekdays_rule(
                    rule,
                    start=start,
                    end=end,
                )
            )
        elif rule_type == "weekdays_in_month_weeks":
            resolved.update(
                _resolve_weekdays_in_month_weeks(
                    rule,
                    start=start,
                    end=end,
                )
            )
        elif rule_type == "nth_weekday_of_month":
            resolved.update(
                _resolve_nth_weekday_of_month(
                    rule,
                    start=start,
                    end=end,
                )
            )
        else:
            raise TemporalSelectionError(
                f"Tipo de regla no soportado: {rule_type}"
            )

    return resolved


def _resolve_key_dates(
    selection: dict[str, Any],
    *,
    key_date_resolver: KeyDateResolver | None,
) -> set[date]:
    if key_date_resolver is None:
        raise TemporalSelectionError(
            "No existe resolvedor del catálogo de fechas clave"
        )

    code = str(
        selection.get("key_date_code") or ""
    ).strip()

    if not code:
        raise TemporalSelectionError(
            "key_date_code es obligatorio"
        )

    years = sorted({
        _integer(value, "years")
        for value in (selection.get("years") or [])
    })

    if not years:
        raise TemporalSelectionError(
            "years debe contener al menos un año"
        )

    occurrences = list(
        key_date_resolver(code, years) or []
    )

    if not occurrences:
        raise TemporalSelectionError(
            "La fecha clave no tiene ocurrencias disponibles"
        )

    resolved: set[date] = set()

    for index, occurrence in enumerate(occurrences):
        start = _date(
            occurrence.get("start_date"),
            f"occurrences[{index}].start_date",
        )
        end = _date(
            occurrence.get("end_date")
            or occurrence.get("start_date"),
            f"occurrences[{index}].end_date",
        )

        if start > end:
            raise TemporalSelectionError(
                "La ocurrencia de fecha clave es inválida"
            )

        resolved.update(_daterange(start, end))

    return resolved


def _selection_semantics(
    *,
    mode: str,
    resolved_dates: list[date],
    selection: dict[str, Any],
) -> dict[str, Any]:
    total = len(resolved_dates)

    if mode == "specific_dates":
        if total == 1:
            title = "Día seleccionado"
            period_label = "día seleccionado"
        else:
            title = "Fechas seleccionadas"
            period_label = "fechas seleccionadas"

    elif mode == "date_ranges":
        ranges = selection.get("ranges") or []

        if len(ranges) == 1:
            title = "Periodo seleccionado"
            period_label = "periodo"
        else:
            title = "Periodos seleccionados"
            period_label = "periodos seleccionados"

    elif mode == "date_rules":
        configured_label = str(
            selection.get("selection_label")
            or selection.get("label")
            or ""
        ).strip()

        if configured_label:
            title = configured_label
            period_label = configured_label.lower()
        else:
            title = "Selección recurrente"
            period_label = "selección"

    elif mode == "key_dates":
        title = str(
            selection.get("key_date_label")
            or selection.get("key_date_code")
            or "Fecha clave"
        ).strip()
        period_label = title

    else:
        title = "Periodo seleccionado"
        period_label = "periodo"

    article = (
        "del"
        if period_label in {
            "día seleccionado",
            "periodo",
        }
        else "de"
    )

    comparison_label = (
        f"vs {period_label} comparable anterior"
        if mode in {"date_rules", "key_dates"}
        else "vs periodo comparable anterior"
    )

    return {
        "selection_type": mode,
        "title": title,
        "period_label": period_label,
        "sales_label": (
            f"Ventas {article} {period_label}"
        ),
        "pax_label": (
            f"PAX {article} {period_label}"
        ),
        "checks_label": (
            f"Cheques {article} {period_label}"
        ),
        "tips_label": (
            f"Propinas {article} {period_label}"
        ),
        "comparison_label": comparison_label,
        "resolved_dates_count": total,
    }


def resolve_temporal_selection(
    *,
    selection: dict[str, Any],
    minimum_date: Any,
    maximum_date: Any,
    key_date_resolver: KeyDateResolver | None = None,
) -> dict[str, Any]:
    """Resuelve el contrato temporal a fechas_operacion concretas."""
    minimum = _date(minimum_date, "minimum_date")
    maximum = _date(maximum_date, "maximum_date")

    if minimum > maximum:
        raise TemporalSelectionError(
            "La cobertura temporal es inválida"
        )

    mode = str(selection.get("mode") or "").strip()

    if not mode:
        raise TemporalSelectionError(
            "mode es obligatorio"
        )

    start, end = _scope(
        selection,
        minimum_date=minimum,
        maximum_date=maximum,
    )

    if mode == "specific_dates":
        resolved = _resolve_specific_dates(selection)

    elif mode == "date_ranges":
        resolved = _resolve_ranges(selection)

    elif mode == "date_rules":
        resolved = _resolve_rules(
            selection,
            start=start,
            end=end,
        )

    elif mode == "key_dates":
        resolved = _resolve_key_dates(
            selection,
            key_date_resolver=key_date_resolver,
        )

    else:
        raise TemporalSelectionError(
            f"Modo temporal no soportado: {mode}"
        )

    exclusions = {
        _date(value, "exclude_dates")
        for value in (selection.get("exclude_dates") or [])
    }

    resolved = _validate_coverage(
        resolved,
        minimum_date=minimum,
        maximum_date=maximum,
    )

    resolved.difference_update(exclusions)

    ordered = sorted(resolved)

    if not ordered:
        raise TemporalSelectionError(
            "La selección no resolvió fechas disponibles"
        )

    semantics = _selection_semantics(
        mode=mode,
        resolved_dates=ordered,
        selection=selection,
    )

    return {
        "resolved_dates": [
            value.isoformat()
            for value in ordered
        ],
        "selection_semantics": semantics,
        "coverage": {
            "minimum_date": minimum.isoformat(),
            "maximum_date": maximum.isoformat(),
        },
        "traceability": {
            "domain": "comercial_temporal_selection",
            "temporal_field": "fecha_operacion",
            "hardcoded_key_dates": False,
            "frontend_expands_rules": False,
            "duplicates_removed": True,
            "exclusions_applied": True,
        },
    }
