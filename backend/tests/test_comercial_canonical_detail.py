from datetime import date

import pytest

from modules.comercial.canonical_detail import (
    CanonicalDailyDuplicateError,
    CanonicalUnitResolutionError,
    assert_one_row_per_operation_date,
    build_canonical_unit_query,
    build_daily_folio,
    build_daily_kpi_detail_query,
    build_daily_kpi_total_query,
    resolve_canonical_unit,
)


def test_specific_selector_uses_parameterized_canonical_lookup():
    query = build_canonical_unit_query("server-1", "0021")

    assert "dbo.Unidades_Negocio" in query.statement
    assert "sucursal_origen_id" in query.statement
    assert "codigo = %s" in query.statement
    assert query.params == ("server-1", "0021", "0021")
    assert "0021" not in query.statement


def test_generic_selector_does_not_guess_unit():
    query = build_canonical_unit_query("server-shared", "DEFAULT")

    assert query.params == ("server-shared",)
    assert "codigo = %s" not in query.statement


def test_resolver_fails_closed_when_shared_server_is_ambiguous():
    def execute_query(statement, params):
        del statement, params
        return [
            {
                "unidad_negocio_pk": "1",
                "codigo": "130QRO",
                "nombre": "130 QUERETARO",
                "server_id": "shared",
                "sucursal_origen_id": "0021",
                "system_type": "MPRO",
            },
            {
                "unidad_negocio_pk": "2",
                "codigo": "ORIGEN",
                "nombre": "ORIGEN",
                "server_id": "shared",
                "sucursal_origen_id": "0023",
                "system_type": "MPRO",
            },
        ]

    with pytest.raises(CanonicalUnitResolutionError):
        resolve_canonical_unit(execute_query, "shared", "DEFAULT")


def test_resolver_returns_exact_canonical_unit():
    def execute_query(statement, params):
        assert "%s" in statement
        assert params == ("shared", "0023", "0023")
        return [
            {
                "unidad_negocio_pk": "2",
                "codigo": "ORIGEN",
                "nombre": "ORIGEN",
                "server_id": "shared",
                "sucursal_origen_id": "0023",
                "system_type": "MPRO",
            }
        ]

    unit = resolve_canonical_unit(execute_query, "shared", "0023")

    assert unit.codigo == "ORIGEN"
    assert unit.sucursal_origen_id == "0023"


def test_runtime_queries_filter_only_by_canonical_unit_code():
    total = build_daily_kpi_total_query(
        "ORIGEN",
        date(2026, 7, 1),
        date(2026, 7, 14),
    )
    detail = build_daily_kpi_detail_query(
        "ORIGEN",
        date(2026, 7, 1),
        date(2026, 7, 14),
        offset=0,
        limit=50,
    )

    for query in (total, detail):
        assert "dbo.vw_Comercial_KPIs_Diarios_v2_Runtime" in query.statement
        assert "unidad_negocio_id = %s" in query.statement
        assert "OR server_id" not in query.statement
        assert "ventas_total" in query.statement
        assert query.params[0] == "ORIGEN"


def test_daily_uniqueness_guard_passes_for_one_row_per_date():
    assert_one_row_per_operation_date({"total": 14, "dias_distintos": 14})


def test_daily_uniqueness_guard_rejects_duplicate_unit_date():
    with pytest.raises(CanonicalDailyDuplicateError):
        assert_one_row_per_operation_date({"total": 28, "dias_distintos": 14})


def test_folio_is_unique_by_unit_and_operation_date():
    qro = build_daily_folio("130QRO", "2026-07-14")
    origen = build_daily_folio("ORIGEN", "2026-07-14")

    assert qro == "DIA-2026-07-14-130QRO"
    assert origen == "DIA-2026-07-14-ORIGEN"
    assert qro != origen


def test_helper_contains_no_live_or_mongo_dependencies():
    import inspect
    import modules.comercial.canonical_detail as module

    source = inspect.getsource(module)

    assert "pymongo" not in source
    assert "motor.motor" not in source
    assert "query_api_mpro_local" not in source
    assert "execute_sql_query(" not in source
