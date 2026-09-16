from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

ROUTER = (
    ROOT
    / "backend/modules/finanzas/cuentas_por_pagar.py"
)

UI = (
    ROOT
    / "frontend/src/components/finanzas/"
    "FinanzasDecisionPago.jsx"
)


def test_decision_dashboard_sql_first_contract():
    src = ROUTER.read_text(encoding="utf-8")

    assert '@router.get("/decision-dashboard")' in src
    assert "dbo.Compras_Recepciones" in src
    assert "dbo.Finanzas_CxP_Sync" in src
    assert "resolve_finanzas_unit_filter" in src
    assert "FINANZAS_VER" in src

    assert "MongoClient" not in src
    assert "pymongo" not in src


def test_decision_dashboard_backend_authoritative_period():
    src = ROUTER.read_text(encoding="utf-8")

    assert "_decision_dashboard_period" in src
    assert "default_mes_anterior" in src
    assert "promedio_mensual_compras" in src
    assert '"limite_pago"' in src
    assert '"comprometido"' in src
    assert '"disponible"' in src
    assert '"porcentaje_utilizado"' in src


def test_decision_dashboard_frontend_consumes_backend():
    src = UI.read_text(encoding="utf-8")

    assert (
        "/finanzas/cuentas-por-pagar/"
        "decision-dashboard"
    ) in src

    assert "decisionResumen.limite_pago" in src
    assert "renderDashboardAmount('comprometido')" in src
    assert "renderDashboardAmount('saldo_cxp')" in src
    assert "renderDashboardAmount('autorizado')" in src
    assert "decisionResumen.disponible" in src
    assert (
        "decisionResumen.porcentaje_utilizado"
        in src
    )

    # React no es autoridad de la regla financiera.
    assert "promedio_mensual_compras =" not in src


def test_decision_dashboard_drilldown_contract():
    router = ROUTER.read_text(encoding="utf-8")
    ui = UI.read_text(encoding="utf-8")

    assert (
        '@router.get("/decision-dashboard/drilldown")'
        in router
    )
    assert "_decision_dashboard_drilldown" in router
    assert '"nivel_maximo": "RECEPCION_COMPRA"' in router
    assert '"detalle_producto_disponible": False' in router
    assert "r.FolioRecepcion" in router
    assert "r.FechaRecepcion" in router
    assert "r.ProveedorID" in router
    assert "r.Total" in router

    assert (
        "/decision-dashboard/drilldown"
        in ui
    )
    assert "Ver cómo se construye" in ui
    assert "folio_recepcion" in ui
    assert "total_compras" in ui


def test_provider_catalog_is_canonical_for_drilldown():
    router = ROUTER.read_text(encoding="utf-8")
    ui = UI.read_text(encoding="utf-8")

    assert "dbo.Proveedor_Catalogo" in router
    assert "p.NombreComercial" in router
    assert "p.RazonSocial" in router
    assert '"proveedor_nombre"' in router
    assert "proveedor_nombre" in ui


def test_analysis_period_does_not_replace_effective_limit():
    ui = UI.read_text(encoding="utf-8")

    assert "analysisPeriod" in ui
    assert "previous_month" in ui
    assert "last_3_months" in ui
    assert "last_6_months" in ui
    assert "last_12_months" in ui

    # La selección analítica alimenta el drilldown.
    assert "resolveAnalysisPeriod" in ui
    assert "decision-dashboard/drilldown" in ui

    # El endpoint principal del límite no recibe
    # las fechas del selector analítico.
    main_call = (
        "/finanzas/cuentas-por-pagar/"
        "decision-dashboard?"
    )
    assert main_call in ui


def test_frontend_effective_period_override_contract():
    page = (
        ROOT
        / "frontend/src/pages/Finanzas.js"
    ).read_text(encoding="utf-8")

    ui = UI.read_text(encoding="utf-8")

    assert "canApplyPeriodOverride" in page
    assert "finanzasPermissions.canAdmin" in page

    assert "effectivePeriodOverride" in ui
    assert "aplicar_periodo_como_limite" in ui
    assert "Aplicar como límite efectivo" in ui
    assert "Requiere autorización" in ui
    assert "Volver al límite por defecto" in ui
