from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read(relative):
    return (ROOT / relative).read_text(encoding="utf-8")


def test_inventory_trigger_is_registered_and_packaged():
    server = _read("server.py")
    routes = _read("modules/scheduler_trigger_inventarios/routes.py")
    assert "modules.scheduler_trigger_inventarios.routes" in server
    assert "app.include_router(inventory_scheduler_trigger_router)" in server
    assert 'prefix="/api/internal/inventory-scheduler-trigger"' in routes
    assert '@router.get("/health")' in routes
    assert '@router.post("/sync-compras")' in routes


def test_soft_inventory_sync_loads_authorized_movement_types():
    job = _read("core/scheduler/jobs/sync_compras_job.py")
    assert "s.tipos_movimiento" in job
    assert "'tipos_movimiento': tipos_movimiento" in job
    assert "'tipos_movimiento': server.get('tipos_movimiento', [])" in job
    assert "_execute_inventory_sql_with_timeout" in job


def test_soft_inventory_reads_both_movement_sources_and_filters_authorized():
    source = _read("core/inventarios/sync_movimientos_canonico.py")
    assert "FROM movsinv i" in source
    assert "FROM movtosalmacen m" in source
    assert "NOT EXISTS" in source
    assert "tipos_movimiento_autorizados" in source
    assert "concepto_origen in tipos_movimiento_autorizados" in source
    assert "PARTIAL_WITH_PENDING" in source


def test_soft_selected_concepts_resolve_by_nature():
    source = _read("modules/compras/sync_service.py")
    assert 'if concepto.startswith("E"):' in source
    assert 'if concepto.startswith("S"):' in source


def test_protected_commercial_syncs_are_not_referenced_by_hotfix():
    touched = "\n".join([
        _read("core/inventarios/sync_movimientos_canonico.py"),
        _read("modules/compras/sync_service.py"),
    ])
    assert "sync_comercial_abiertas_v2" not in touched
    assert "sync_comercial_v2" not in touched


def test_sync_compras_run_now_returns_real_result():
    manager = _read("core/scheduler/scheduler_manager.py")
    marker = 'elif job_id == "sync_compras":'
    fragment = manager[manager.index(marker):manager.index(marker) + 700]
    assert "result = await self._run_sync_compras_job()" in fragment
    assert 'return {**result, "job_id": job_id}' in fragment
