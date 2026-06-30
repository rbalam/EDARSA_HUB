import importlib.util
import sys
import types
from pathlib import Path

import pytest


class _DummyJobLogger:
    async def start_execution(self, *args, **kwargs):
        return {}

    async def finish_execution(self, *args, **kwargs):
        return None


def _load_detector_module(monkeypatch):
    """Carga solo el detector para evitar importar todo el scheduler en este test."""
    scheduler_pkg = types.ModuleType("core.scheduler")
    scheduler_pkg.__path__ = []
    jobs_pkg = types.ModuleType("core.scheduler.jobs")
    jobs_pkg.__path__ = []

    job_logger = types.ModuleType("core.scheduler.job_logger")
    job_logger.get_job_logger = lambda db: _DummyJobLogger()

    sql_repository = types.ModuleType("core.scheduler.sql_repository")

    async def _noop(*args, **kwargs):
        return []

    sql_repository.get_active_servers = _noop
    sql_repository.get_server_by_id = _noop
    sql_repository.inventario_existe = _noop
    sql_repository.registrar_inventario_procesando = _noop
    sql_repository.actualizar_inventario_completado = _noop
    sql_repository.actualizar_inventario_error = _noop
    sql_repository.get_inventarios_pendientes_reintento = _noop
    sql_repository.registrar_bitacora_job = _noop

    monkeypatch.setitem(sys.modules, "core.scheduler", scheduler_pkg)
    monkeypatch.setitem(sys.modules, "core.scheduler.jobs", jobs_pkg)
    monkeypatch.setitem(sys.modules, "core.scheduler.job_logger", job_logger)
    monkeypatch.setitem(sys.modules, "core.scheduler.sql_repository", sql_repository)

    module_path = (
        Path(__file__).resolve().parents[1]
        / "core"
        / "scheduler"
        / "jobs"
        / "inventarios_detector_job.py"
    )
    spec = importlib.util.spec_from_file_location(
        "core.scheduler.jobs.inventarios_detector_job",
        module_path,
    )
    module = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, spec.name, module)
    spec.loader.exec_module(module)
    return module


def test_normalizar_system_type_softrestaurant_variantes(monkeypatch):
    detector_module = _load_detector_module(monkeypatch)

    assert detector_module._normalizar_system_type("SoftRestaurant") == "SoftRestaurant"
    assert detector_module._normalizar_system_type("SOFTRESTAURANT_PRO") == "SoftRestaurant"
    assert detector_module._normalizar_system_type("softrestaurantpro") == "SoftRestaurant"
    assert detector_module._normalizar_system_type("sr") == "SoftRestaurant"


def test_normalizar_system_type_mpro_variantes(monkeypatch):
    detector_module = _load_detector_module(monkeypatch)

    assert detector_module._normalizar_system_type("MPRO") == "MPRO"
    assert detector_module._normalizar_system_type("MANAGEMENTPRO") == "MPRO"


@pytest.mark.asyncio
async def test_obtener_servidores_incluye_la_estelar_softrestaurant_pro(monkeypatch):
    detector_module = _load_detector_module(monkeypatch)

    async def fake_get_active_servers(server_id_filter=None):
        return [
            {
                "id": "a5ff0e25-f029-43db-b634-d4ac814c904f",
                "name": "LA ESTELAR",
                "system_type": "SOFTRESTAURANT_PRO",
            },
            {
                "id": "ignored",
                "name": "NO SOPORTADO",
                "system_type": "DESCONOCIDO",
            },
        ]

    monkeypatch.setattr(detector_module, "get_active_servers", fake_get_active_servers)

    job = detector_module.InventariosDetectorJob(db={})
    servidores = await job._obtener_servidores()

    assert len(servidores) == 1
    assert servidores[0]["name"] == "LA ESTELAR"
    assert servidores[0]["system_type_canonical"] == "SoftRestaurant"
