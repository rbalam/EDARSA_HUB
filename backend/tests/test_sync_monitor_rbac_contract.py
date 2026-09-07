from pathlib import Path


def test_sync_monitor_routes_require_explicit_sql_rbac():
    routes = (
        Path(__file__).resolve().parents[1]
        / "modules"
        / "sync_monitor"
        / "routes.py"
    ).read_text(encoding="utf-8")

    assert "from core.rbac.middleware import require_explicit_permission" in routes
    assert routes.count("Depends(require_explicit_permission(\"sync_monitor_VER\"))") == 3


def test_sync_monitor_rbac_contract_covers_all_public_routes():
    routes = (
        Path(__file__).resolve().parents[1]
        / "modules"
        / "sync_monitor"
        / "routes.py"
    ).read_text(encoding="utf-8")

    assert '@router.get("/sync-monitor")' in routes
    assert '@router.get("/sync-monitor/kpis")' in routes
    assert '@router.get("/sync-monitor/servidor/{server_id}")' in routes
