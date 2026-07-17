from datetime import date
import importlib.util
from pathlib import Path
import sys

import pytest


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "modules"
    / "comercial"
    / "canonical_detail.py"
)
MODULE_NAME = "edarsahub_comercial_canonical_detail_under_test"

spec = importlib.util.spec_from_file_location(MODULE_NAME, MODULE_PATH)
if spec is None or spec.loader is None:
    raise RuntimeError(f"No se pudo cargar el helper canónico: {MODULE_PATH}")

module = importlib.util.module_from_spec(spec)
sys.modules[MODULE_NAME] = module
spec.loader.exec_module(module)

CanonicalDailyDuplicateError = module.CanonicalDailyDuplicateError
CanonicalUnit = module.CanonicalUnit
CanonicalUnitAccessError = module.CanonicalUnitAccessError
CanonicalUnitResolutionError = module.CanonicalUnitResolutionError
assert_canonical_unit_access = module.assert_canonical_unit_access
assert_one_row_per_operation_date = module.assert_one_row_per_operation_date
build_canonical_unit_query = module.build_canonical_unit_query
build_daily_folio = module.build_daily_folio
build_daily_kpi_detail_query = module.build_daily_kpi_detail_query
build_daily_kpi_total_query = module.build_daily_kpi_total_query
resolve_canonical_unit = module.resolve_canonical_unit
resolve_allowed_canonical_unit_pks = module.resolve_allowed_canonical_unit_pks


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


def test_shared_server_scope_allows_only_exact_canonical_unit_pk():
    canonical_units = [
        {
            "unidad_negocio_pk": "1",
            "codigo": "130QRO",
        },
        {
            "unidad_negocio_pk": "2",
            "codigo": "ORIGEN",
        },
    ]
    allowed = resolve_allowed_canonical_unit_pks(
        [{"codigo": "130QRO"}],
        canonical_units,
    )
    qro = CanonicalUnit("1", "130QRO", "130 QUERETARO", "shared", "0021", "MPRO")
    origen = CanonicalUnit("2", "ORIGEN", "ORIGEN", "shared", "0023", "MPRO")

    assert_canonical_unit_access(qro, allowed)
    with pytest.raises(CanonicalUnitAccessError):
        assert_canonical_unit_access(origen, allowed)


def test_shared_server_scope_accepts_only_exact_assigned_source_branch():
    qro = CanonicalUnit(
        "1",
        "130QRO",
        "130 QUERETARO",
        "shared",
        "0021",
        "MPRO",
    )
    origen = CanonicalUnit(
        "2",
        "ORIGEN",
        "ORIGEN",
        "shared",
        "0023",
        "MPRO",
    )

    assert_canonical_unit_access(
        qro,
        frozenset(),
        allowed_source_branch_ids=["0021"],
    )
    with pytest.raises(CanonicalUnitAccessError):
        assert_canonical_unit_access(
            origen,
            frozenset(),
            allowed_source_branch_ids=["0021"],
        )


def test_duplicate_canonical_code_fails_closed():
    allowed = resolve_allowed_canonical_unit_pks(
        [{"codigo": "DUPLICADA"}],
        [
            {"unidad_negocio_pk": "1", "codigo": "DUPLICADA"},
            {"unidad_negocio_pk": "2", "codigo": "DUPLICADA"},
        ],
    )

    assert allowed == frozenset()


def test_canonical_unit_scope_fails_closed_when_assignment_is_empty():
    unit = CanonicalUnit("2", "ORIGEN", "ORIGEN", "shared", "0023", "MPRO")

    with pytest.raises(CanonicalUnitAccessError):
        assert_canonical_unit_access(unit, frozenset())


def test_canonical_unit_scope_preserves_explicit_global_access():
    unit = CanonicalUnit("2", "ORIGEN", "ORIGEN", "shared", "0023", "MPRO")

    assert_canonical_unit_access(
        unit,
        frozenset(),
        has_global_access=True,
    )


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
    source = MODULE_PATH.read_text(encoding="utf-8")

    assert "pymongo" not in source
    assert "motor.motor" not in source
    assert "query_api_mpro_local" not in source
    assert "execute_sql_query(" not in source
