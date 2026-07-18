"""Contratos de cierre Portal/Inteligencia/Comercial."""

from pathlib import Path


BACKEND = Path(__file__).resolve().parents[1]

MIDDLEWARE = (
    BACKEND / "core/rbac/middleware.py"
).read_text(encoding="utf-8")

RBAC_INIT = (
    BACKEND / "core/rbac/__init__.py"
).read_text(encoding="utf-8")

PORTAL = (
    BACKEND / "routes/portal_inteligencia.py"
).read_text(encoding="utf-8")

INTEL = (
    BACKEND
    / "modules/inteligencia_comercial/routes.py"
).read_text(encoding="utf-8")

KPI_SERVICE = (
    BACKEND / "core/kpis_canonicos/service.py"
).read_text(encoding="utf-8")


def test_portal_no_autoriza_por_texto_de_rol():
    assert '"admin" in role' not in PORTAL
    assert '"super" in role' not in PORTAL
    assert (
        "INTELIGENCIA_COMERCIAL_GESTIONAR"
        in PORTAL
    )


def test_inteligencia_no_autoriza_por_texto_de_rol():
    assert '"admin" in role' not in INTEL
    assert '"super" in role' not in INTEL
    assert (
        "INTELIGENCIA_COMERCIAL_GESTIONAR"
        in INTEL
    )


def test_dependency_dual_reutiliza_rbac_explicito():
    assert (
        "class RBACExplicitDualDependency:"
        in MIDDLEWARE
    )
    assert (
        "self._delegate = RBACExplicitDependency("
        in MIDDLEWARE
    )
    assert (
        "require_explicit_permission_dual"
        in RBAC_INIT
    )


def test_error_sql_no_se_convierte_en_sin_datos():
    block = INTEL[
        INTEL.index("def execute_query("):
        INTEL.index("def execute_write(")
    ]

    assert "raise InteligenciaSQLSourceError()" in block
    assert "return []" not in block


def test_sin_fecha_no_usa_fecha_civil_actual():
    block = INTEL[
        INTEL.index("def _ultimo_dia_con_datos("):
        INTEL.index("def _sql_literal(")
    ]

    assert "date.today()" not in block
    assert (
        "raise InteligenciaNoDataError(unidad_db)"
        in block
    )


def test_contrato_kpi_canonico():
    required = (
        "dbo.vw_Comercial_KPIs_Diarios_v2_Runtime",
        "unidad_negocio_pk",
        "fecha_operacion",
        "ventas_total",
        "propinas_total",
    )

    for marker in required:
        assert marker in KPI_SERVICE


def test_no_reintroduce_ventas_sin_propina():
    assert (
        "ventas_sin_propina"
        not in INTEL + KPI_SERVICE
    )


def test_ticket_promedio_es_alias_legacy():
    assert (
        '"ticket_promedio": cheque_promedio'
        in KPI_SERVICE
    )
    assert (
        '"cheque_promedio": cheque_promedio'
        in KPI_SERVICE
    )
