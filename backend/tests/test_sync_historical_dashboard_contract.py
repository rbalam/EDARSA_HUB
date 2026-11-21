from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FRONT = ROOT / "frontend" / "src" / "pages" / "SyncHistorical.jsx"
CATALOG = ROOT / "backend" / "modules" / "sync_historicos" / "catalog_service.py"


def test_historical_dashboard_exposes_full_operational_surface():
    text = FRONT.read_text(encoding="utf-8")

    for label in (
        "Tablas del sistema",
        "Estado de sincronización",
        "Progreso general",
        "Log de errores del sincronizador",
        "Acciones",
        "Ejecutar preflight",
        "Iniciar sincronización",
        "Safe stop",
        "Detalle de unidades atómicas",
        "Historial de ejecuciones",
    ):
        assert label in text


def test_historical_frontend_is_metadata_driven_and_fail_closed():
    text = FRONT.read_text(encoding="utf-8")

    assert "catalog?.categories" in text
    assert "eligible_systems" in text
    assert "execution_enabled" in text
    assert "table_name" in text
    assert "selectableCapabilityKeys" in text
    assert "Pendiente de certificación histórica" in text

    for forbidden in (
        "ventas_encabezado",
        "ventas_detalle",
        "compras_detalle",
        "clientes_contactos",
        "produccion_ordenes",
        "sync_comercial_abiertas_v2",
    ):
        assert forbidden not in text


def test_catalog_exposes_declared_and_executable_capabilities_without_static_tables():
    text = CATALOG.read_text(encoding="utf-8")

    assert "incluir_inactivos=True" in text
    assert "incluir_incompletos=True" in text
    assert "declared_systems" in text
    assert "eligible_systems" in text
    assert "execution_enabled" in text
    assert "table_name" in text
    assert "declared_capabilities" in text
    assert "executable_capabilities" in text
    assert "dbo.Sistema_Tipos" in text
    assert "sync_comercial_abiertas_v2" not in text.lower()
