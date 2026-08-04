from pathlib import Path

from modules.comercial_analytics.temporal_selection import (
    TemporalSelectionError,
    resolve_temporal_selection,
)


MIN_DATE = "2026-01-01"
MAX_DATE = "2026-08-02"


def resolve(
    selection,
    key_date_resolver=None,
    minimum_date=MIN_DATE,
    maximum_date=MAX_DATE,
):
    return resolve_temporal_selection(
        selection=selection,
        minimum_date=minimum_date,
        maximum_date=maximum_date,
        key_date_resolver=key_date_resolver,
    )


def test_specific_single_date():
    result = resolve({
        "mode": "specific_dates",
        "dates": ["2026-08-01"],
    })

    assert result["resolved_dates"] == ["2026-08-01"]
    assert result["selection_semantics"]["sales_label"] == (
        "Ventas del día seleccionado"
    )


def test_specific_non_contiguous_dates_are_sorted():
    result = resolve({
        "mode": "specific_dates",
        "dates": [
            "2026-07-31",
            "2026-07-03",
            "2026-07-17",
        ],
    })

    assert result["resolved_dates"] == [
        "2026-07-03",
        "2026-07-17",
        "2026-07-31",
    ]


def test_multiple_ranges_are_unified_without_duplicates():
    result = resolve({
        "mode": "date_ranges",
        "ranges": [
            {
                "start_date": "2026-07-01",
                "end_date": "2026-07-03",
            },
            {
                "start_date": "2026-07-03",
                "end_date": "2026-07-05",
            },
        ],
    })

    assert result["resolved_dates"] == [
        "2026-07-01",
        "2026-07-02",
        "2026-07-03",
        "2026-07-04",
        "2026-07-05",
    ]


def test_all_fridays():
    result = resolve({
        "mode": "date_rules",
        "scope": {
            "start_date": "2026-07-01",
            "end_date": "2026-07-31",
        },
        "rules": [{
            "type": "weekdays",
            "weekdays": [5],
        }],
    })

    assert result["resolved_dates"] == [
        "2026-07-03",
        "2026-07-10",
        "2026-07-17",
        "2026-07-24",
        "2026-07-31",
    ]


def test_friday_saturday_sunday_in_weeks_one_and_three():
    result = resolve({
        "mode": "date_rules",
        "scope": {
            "start_date": "2026-07-01",
            "end_date": "2026-07-31",
        },
        "rules": [{
            "type": "weekdays_in_month_weeks",
            "weekdays": [5, 6, 7],
            "month_weeks": [1, 3],
        }],
    })

    assert result["resolved_dates"] == [
        "2026-07-03",
        "2026-07-04",
        "2026-07-05",
        "2026-07-17",
        "2026-07-18",
        "2026-07-19",
    ]


def test_first_friday_of_each_month():
    result = resolve({
        "mode": "date_rules",
        "scope": {
            "start_date": "2026-05-01",
            "end_date": "2026-07-31",
        },
        "rules": [{
            "type": "nth_weekday_of_month",
            "weekday": 5,
            "occurrence": 1,
        }],
    })

    assert result["resolved_dates"] == [
        "2026-05-01",
        "2026-06-05",
        "2026-07-03",
    ]


def test_last_sunday_of_each_month():
    result = resolve({
        "mode": "date_rules",
        "scope": {
            "start_date": "2026-05-01",
            "end_date": "2026-07-31",
        },
        "rules": [{
            "type": "nth_weekday_of_month",
            "weekday": 7,
            "occurrence": -1,
        }],
    })

    assert result["resolved_dates"] == [
        "2026-05-31",
        "2026-06-28",
        "2026-07-26",
    ]


def test_key_date_uses_catalog_resolver():
    def key_date_resolver(code, years):
        assert code == "DIA_MADRES"
        assert years == [2025, 2026]

        return [
            {
                "start_date": "2025-05-10",
                "end_date": "2025-05-10",
            },
            {
                "start_date": "2026-05-10",
                "end_date": "2026-05-10",
            },
        ]

    result = resolve(
        {
            "mode": "key_dates",
            "key_date_code": "DIA_MADRES",
            "key_date_label": "Día de las Madres",
            "years": [2025, 2026],
        },
        key_date_resolver=key_date_resolver,
        minimum_date="2025-01-01",
        maximum_date="2026-08-02",
    )

    assert result["resolved_dates"] == [
        "2025-05-10",
        "2026-05-10",
    ]
    assert result["selection_semantics"]["sales_label"] == (
        "Ventas de Día de las Madres"
    )


def test_exclusions_are_applied():
    result = resolve({
        "mode": "specific_dates",
        "dates": [
            "2026-07-03",
            "2026-07-10",
        ],
        "exclude_dates": ["2026-07-10"],
    })

    assert result["resolved_dates"] == [
        "2026-07-03",
    ]


def test_future_or_out_of_coverage_date_is_rejected():
    try:
        resolve({
            "mode": "specific_dates",
            "dates": ["2026-09-01"],
        })
    except TemporalSelectionError as exc:
        assert "fuera de cobertura" in str(exc)
    else:
        raise AssertionError(
            "La fecha fuera de cobertura debía rechazarse"
        )


def test_key_dates_are_not_hardcoded():
    result = resolve(
        {
            "mode": "key_dates",
            "key_date_code": "EVENTO_PROPIO",
            "years": [2026],
        },
        key_date_resolver=lambda code, years: [{
            "start_date": "2026-07-15",
            "end_date": "2026-07-17",
        }],
    )

    assert result["traceability"][
        "hardcoded_key_dates"
    ] is False


def test_configurable_commercial_weekend_is_thursday_to_sunday():
    result = resolve({
        "mode": "date_rules",
        "selection_label": "Fin de semana",
        "scope": {
            "start_date": "2026-07-01",
            "end_date": "2026-07-12",
        },
        "rules": [{
            "type": "weekdays",
            "weekdays": [4, 5, 6, 7],
        }],
    })

    assert result["resolved_dates"] == [
        "2026-07-02",
        "2026-07-03",
        "2026-07-04",
        "2026-07-05",
        "2026-07-09",
        "2026-07-10",
        "2026-07-11",
        "2026-07-12",
    ]

    semantics = result["selection_semantics"]

    assert semantics["title"] == "Fin de semana"
    assert semantics["sales_label"] == (
        "Ventas de fin de semana"
    )
    assert semantics["pax_label"] == (
        "PAX de fin de semana"
    )
    assert semantics["checks_label"] == (
        "Cheques de fin de semana"
    )
    assert semantics["comparison_label"] == (
        "vs fin de semana comparable anterior"
    )


def test_configurable_weekend_for_selected_month_weeks():
    result = resolve({
        "mode": "date_rules",
        "selection_label": "Fin de semana",
        "scope": {
            "start_date": "2026-07-01",
            "end_date": "2026-07-31",
        },
        "rules": [{
            "type": "weekdays_in_month_weeks",
            "weekdays": [4, 5, 6, 7],
            "month_weeks": [1, 3],
        }],
    })

    assert result["resolved_dates"] == [
        "2026-07-02",
        "2026-07-03",
        "2026-07-04",
        "2026-07-05",
        "2026-07-16",
        "2026-07-17",
        "2026-07-18",
        "2026-07-19",
    ]


def test_weekend_definition_is_not_embedded_in_engine():
    source = Path(
        "/app/backend/modules/comercial_analytics/"
        "temporal_selection.py"
    ).read_text(encoding="utf-8")

    assert "Fin de semana" not in source
    assert "[4, 5, 6, 7]" not in source


def test_temporal_request_single_unit_is_compatible():
    from modules.comercial_analytics.schemas import (
        TemporalResolveRequest,
    )

    payload = TemporalResolveRequest(
        selection={
            "mode": "specific_dates",
            "dates": ["2026-08-01"],
        },
        unidad_negocio_id="130MID",
    )

    assert payload.requested_unit_codes() == ["130MID"]
    assert payload.resolve_unit_scope(
        ["130MID", "130QRO"]
    ) == ["130MID"]


def test_temporal_request_multiple_units_are_normalized():
    from modules.comercial_analytics.schemas import (
        TemporalResolveRequest,
    )

    payload = TemporalResolveRequest(
        selection={
            "mode": "specific_dates",
            "dates": ["2026-08-01"],
        },
        unidad_negocio_ids=[
            "130QRO",
            "130MID",
            "130MID",
            " ",
        ],
    )

    assert payload.unidad_negocio_ids == [
        "130MID",
        "130QRO",
    ]

    assert payload.resolve_unit_scope(
        ["130MID", "130QRO", "ORIGEN"]
    ) == [
        "130MID",
        "130QRO",
    ]


def test_temporal_request_without_scope_uses_all_allowed_units():
    from modules.comercial_analytics.schemas import (
        TemporalResolveRequest,
    )

    payload = TemporalResolveRequest(
        selection={
            "mode": "specific_dates",
            "dates": ["2026-08-01"],
        },
    )

    assert payload.resolve_unit_scope([
        "ORIGEN",
        "130MID",
        "130MID",
    ]) == [
        "130MID",
        "ORIGEN",
    ]


def test_temporal_request_rejects_unauthorized_unit():
    from modules.comercial_analytics.schemas import (
        TemporalResolveRequest,
    )

    payload = TemporalResolveRequest(
        selection={
            "mode": "specific_dates",
            "dates": ["2026-08-01"],
        },
        unidad_negocio_ids=[
            "130MID",
            "UNIDAD_NO_PERMITIDA",
        ],
    )

    try:
        payload.resolve_unit_scope(["130MID"])
    except PermissionError as exc:
        assert "UNIDAD_NO_PERMITIDA" in str(exc)
    else:
        raise AssertionError(
            "La unidad no permitida debía rechazarse"
        )


def test_temporal_request_rejects_conflicting_scopes():
    from modules.comercial_analytics.schemas import (
        TemporalResolveRequest,
    )

    payload = TemporalResolveRequest(
        selection={
            "mode": "specific_dates",
            "dates": ["2026-08-01"],
        },
        unidad_negocio_id="130MID",
        unidad_negocio_ids=["130QRO"],
    )

    try:
        payload.requested_unit_codes()
    except ValueError as exc:
        assert "alcances diferentes" in str(exc)
    else:
        raise AssertionError(
            "Los alcances incompatibles debían rechazarse"
        )


def test_temporal_request_accepts_equivalent_single_and_multiple_scope():
    from modules.comercial_analytics.schemas import (
        TemporalResolveRequest,
    )

    payload = TemporalResolveRequest(
        selection={
            "mode": "specific_dates",
            "dates": ["2026-08-01"],
        },
        unidad_negocio_id="130MID",
        unidad_negocio_ids=["130MID"],
    )

    assert payload.requested_unit_codes() == ["130MID"]
