from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ROUTES = ROOT / "modules/sync_historicos/routes.py"
CATALOG = ROOT / "modules/sync_historicos/catalog_service.py"
SUBMIT = ROOT / "modules/sync_historicos/worker_submit.py"
CONTROLS = ROOT / "modules/sync_historicos/controls.py"
SERVER = ROOT / "server.py"


def test_historical_api_contract_routes_exist():
    text = ROUTES.read_text(encoding="utf-8")
    for route in (
        '"/catalog"',
        '"/preflight"',
        '"/jobs"',
        '"/jobs/{parent_id}"',
        '"/jobs/{parent_id}/pause"',
        '"/jobs/{parent_id}/resume"',
        '"/jobs/{parent_id}/cancel"',
    ):
        assert route in text
    assert 'require_permission("SCHEDULER_VER")' in text
    assert 'require_explicit_permission("SCHEDULER_ADMIN")' in text


def test_catalog_is_metadata_driven_not_static_lists():
    text = CATALOG.read_text(encoding="utf-8")
    assert "get_historical_registry" in text
    assert "Sistema_SucursalServidorMapeo" in text
    assert "SystemCapabilityResolver" in text
    assert "SOFTRESTAURANT" not in text
    assert "MPRO" not in text


def test_http_enqueues_canonical_worker_instead_of_running_sync():
    routes = ROUTES.read_text(encoding="utf-8")
    submit = SUBMIT.read_text(encoding="utf-8")
    assert "execute_atomic_unit" not in routes
    assert "execute_parent_job" not in routes
    assert "gate_chain_publisher.submit" in submit
    assert '"SYNC_HISTORICAL_PARENT"' in submit
    assert '"production_allowed"' not in routes


def test_controls_are_cooperative_and_resumable():
    text = CONTROLS.read_text(encoding="utf-8")
    assert "PauseRequested=1" in text
    assert "CancelRequested=1" in text
    assert "CANCEL_REQUESTED" in text
    assert "retry_failed" in text


def test_router_is_mounted_once_and_protected_sync_absent():
    server = SERVER.read_text(encoding="utf-8")
    assert server.count("sync_historical_router") == 2
    combined = (
        ROUTES.read_text(encoding="utf-8")
        + CATALOG.read_text(encoding="utf-8")
        + SUBMIT.read_text(encoding="utf-8")
        + CONTROLS.read_text(encoding="utf-8")
    ).lower()
    assert "sync_comercial_abiertas_v2" not in combined
