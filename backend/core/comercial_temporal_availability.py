from __future__ import annotations

from typing import Any, Callable, Iterable


ReadonlyQuery = Callable[[str], list[dict[str, Any]]]
UnitsWhereBuilder = Callable[[list[str]], str]


class TemporalAvailabilityError(RuntimeError):
    """No fue posible construir la cobertura temporal canónica."""


def _required_units(units: Iterable[Any]) -> list[str]:
    normalized = sorted({
        str(value).strip()
        for value in units
        if str(value or "").strip()
    })

    if not normalized:
        raise TemporalAvailabilityError(
            "Se requiere al menos una unidad permitida"
        )

    return normalized


def build_temporal_availability(
    *,
    units: Iterable[Any],
    readonly_query: ReadonlyQuery,
    units_where_builder: UnitsWhereBuilder,
) -> dict[str, Any]:
    """Construye años, meses y límites desde la vista KPI canónica.

    No genera periodos artificiales.
    No usa fecha civil.
    No consulta LIVE ni MongoDB.
    """
    normalized_units = _required_units(units)
    where_units = units_where_builder(normalized_units)

    query = f"""
    SELECT
        YEAR(fecha_operacion) AS anio,
        MONTH(fecha_operacion) AS mes,
        MIN(fecha_operacion) AS fecha_inicio,
        MAX(fecha_operacion) AS fecha_fin,
        COUNT(DISTINCT fecha_operacion) AS dias_disponibles
    FROM vw_Comercial_KPIs_Diarios_v2_Runtime
    WHERE {where_units}
      AND fecha_operacion IS NOT NULL
    GROUP BY
        YEAR(fecha_operacion),
        MONTH(fecha_operacion)
    ORDER BY
        anio DESC,
        mes ASC
    """

    rows = list(readonly_query(query) or [])
    years_map: dict[int, dict[str, Any]] = {}

    for row in rows:
        year = int(row["anio"])
        month = int(row["mes"])

        start_value = row.get("fecha_inicio")
        end_value = row.get("fecha_fin")

        start_iso = (
            start_value.isoformat()
            if hasattr(start_value, "isoformat")
            else str(start_value or "")[:10]
        )
        end_iso = (
            end_value.isoformat()
            if hasattr(end_value, "isoformat")
            else str(end_value or "")[:10]
        )

        if not start_iso or not end_iso:
            continue

        year_entry = years_map.setdefault(
            year,
            {
                "anio": year,
                "fecha_inicio": None,
                "fecha_fin": None,
                "meses": [],
            },
        )

        year_entry["meses"].append({
            "mes": month,
            "fecha_inicio": start_iso,
            "fecha_fin": end_iso,
            "dias_disponibles": int(
                row.get("dias_disponibles") or 0
            ),
        })

        if (
            year_entry["fecha_inicio"] is None
            or start_iso < year_entry["fecha_inicio"]
        ):
            year_entry["fecha_inicio"] = start_iso

        if (
            year_entry["fecha_fin"] is None
            or end_iso > year_entry["fecha_fin"]
        ):
            year_entry["fecha_fin"] = end_iso

    years = [
        years_map[year]
        for year in sorted(years_map.keys(), reverse=True)
    ]

    start_dates = [
        item["fecha_inicio"]
        for item in years
        if item.get("fecha_inicio")
    ]
    end_dates = [
        item["fecha_fin"]
        for item in years
        if item.get("fecha_fin")
    ]

    return {
        "anios": years,
        "fecha_minima": min(start_dates) if start_dates else None,
        "fecha_maxima": max(end_dates) if end_dates else None,
        "total_anios": len(years),
        "total_periodos": sum(
            len(item.get("meses") or [])
            for item in years
        ),
        "traceability": {
            "source": "vw_Comercial_KPIs_Diarios_v2_Runtime",
            "temporal_field": "fecha_operacion",
            "live": False,
            "mongodb": False,
            "hardcode": False,
            "units": normalized_units,
        },
    }
