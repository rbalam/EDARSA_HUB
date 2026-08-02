from datetime import date

from core.comercial_temporal_availability import (
    build_temporal_availability,
)


def test_builds_years_months_and_limits():
    captured = {}

    def query(sql):
        captured["sql"] = sql
        return [
            {
                "anio": 2026,
                "mes": 7,
                "fecha_inicio": date(2026, 7, 1),
                "fecha_fin": date(2026, 7, 31),
                "dias_disponibles": 31,
            },
            {
                "anio": 2026,
                "mes": 8,
                "fecha_inicio": date(2026, 8, 1),
                "fecha_fin": date(2026, 8, 2),
                "dias_disponibles": 2,
            },
            {
                "anio": 2025,
                "mes": 12,
                "fecha_inicio": date(2025, 12, 1),
                "fecha_fin": date(2025, 12, 31),
                "dias_disponibles": 31,
            },
        ]

    result = build_temporal_availability(
        units=["A", "B"],
        readonly_query=query,
        units_where_builder=lambda units: (
            "unidad_negocio_id IN ('A','B')"
        ),
    )

    assert result["fecha_minima"] == "2025-12-01"
    assert result["fecha_maxima"] == "2026-08-02"
    assert result["total_anios"] == 2
    assert result["total_periodos"] == 3
    assert result["anios"][0]["anio"] == 2026
    assert len(result["anios"][0]["meses"]) == 2
    assert "vw_Comercial_KPIs_Diarios_v2_Runtime" in (
        captured["sql"]
    )


def test_empty_rows_return_empty_coverage():
    result = build_temporal_availability(
        units=["A"],
        readonly_query=lambda sql: [],
        units_where_builder=lambda units: "1 = 1",
    )

    assert result["anios"] == []
    assert result["fecha_minima"] is None
    assert result["fecha_maxima"] is None


def test_units_are_required():
    try:
        build_temporal_availability(
            units=[],
            readonly_query=lambda sql: [],
            units_where_builder=lambda units: "1 = 1",
        )
    except RuntimeError as exc:
        assert "unidad" in str(exc).lower()
    else:
        raise AssertionError(
            "Debía rechazar alcance sin unidades"
        )
