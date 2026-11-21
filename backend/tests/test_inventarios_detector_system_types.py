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
    job_logger.get_job_logger = lambda *args, **kwargs: _DummyJobLogger()

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
    sql_repository.get_inventario_error_by_id = _noop
    sql_repository.registrar_bitacora_job = _noop

    system_type_utils = types.ModuleType("core.system_type_utils")

    def normalize_system_type(value):
        normalized = str(value or "").strip().upper()
        if normalized in {"SOFTRESTAURANT", "SOFTRESTAURANT_PRO", "SOFTRESTAURANTPRO", "SR"}:
            return "SOFTRESTAURANT"
        if normalized in {"MPRO", "MANAGEMENTPRO"}:
            return "MANAGEMENTPRO"
        return "UNKNOWN"

    system_type_utils.normalize_system_type = normalize_system_type

    monkeypatch.setitem(sys.modules, "core.scheduler", scheduler_pkg)
    monkeypatch.setitem(sys.modules, "core.scheduler.jobs", jobs_pkg)
    monkeypatch.setitem(sys.modules, "core.scheduler.job_logger", job_logger)
    monkeypatch.setitem(sys.modules, "core.scheduler.sql_repository", sql_repository)
    monkeypatch.setitem(sys.modules, "core.system_type_utils", system_type_utils)

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


@pytest.mark.asyncio
async def test_detectar_softrestaurant_usa_sync_edarsahub(monkeypatch):
    detector_module = _load_detector_module(monkeypatch)

    modules_pkg = types.ModuleType("modules")
    modules_pkg.__path__ = []
    compras_pkg = types.ModuleType("modules.compras")
    compras_pkg.__path__ = []
    sync_service = types.ModuleType("modules.compras.sync_service")

    def fake_obtener_inventarios_fisicos_sync(**kwargs):
        assert kwargs["server_id"] == "server-estelar"
        return [
            {
                "folio": "200",
                "fecha": "2026-06-30T10:00:00",
                "almacen_id": "1",
                "almacen": "BODEGA",
                "sucursal_id": "",
                "unidad_negocio_codigo": "ESTELAR",
                "comentario": "",
            },
            {
                "folio": "100",
                "fecha": "2026-06-01T09:00:00",
                "almacen_id": "1",
                "almacen": "BODEGA",
                "sucursal_id": "",
                "unidad_negocio_codigo": "ESTELAR",
                "comentario": "",
            },
        ]

    sync_service.obtener_inventarios_fisicos_sync = fake_obtener_inventarios_fisicos_sync
    monkeypatch.setitem(sys.modules, "modules", modules_pkg)
    monkeypatch.setitem(sys.modules, "modules.compras", compras_pkg)
    monkeypatch.setitem(sys.modules, "modules.compras.sync_service", sync_service)

    job = detector_module.InventariosDetectorJob(db={})
    inventarios = await job._detectar_soft({
        "id": "server-estelar",
        "name": "LA ESTELAR",
        "system_type": "SOFTRESTAURANT_PRO",
    })

    assert len(inventarios) == 1
    inv = inventarios[0]
    assert inv.clave.sistema_origen == "SOFTRESTAURANT"
    assert inv.clave.sucursal_id == "ESTELAR"
    assert inv.clave.almacen_id == "1"
    assert inv.clave.folio_inventario == "200"
    assert inv.folio_inicial == "100"
    assert inv.metadata["source"] == "EDARSAHUB_SYNC"


@pytest.mark.asyncio
async def test_reintento_rehidrata_contexto_persistido(monkeypatch):
    detector_module = _load_detector_module(monkeypatch)

    async def fake_get_pendientes(max_intentos=3, limit=5):
        assert max_intentos == detector_module.MAX_INTENTOS
        assert limit == 5
        return [{
            "SistemaOrigen": "MPRO",
            "ServerID": "server-mpro",
            "SucursalID": "0021",
            "AlmacenID": "0001",
            "FolioInventario": "QR-0001041",
            "Intentos": 2,
            "DetallesJSON": (
                '{"server_name":"ManagementPro",'
                '"almacen_nombre":"ALMACEN GENERAL",'
                '"folio_inicial":"QR-0001038",'
                '"fecha_inicial":"2026-08-01",'
                '"fecha_inventario":"2026-09-01",'
                '"metadata":{"source":"EDARSAHUB_SYNC"}}'
            ),
        }]

    monkeypatch.setattr(
        detector_module,
        "get_inventarios_pendientes_reintento",
        fake_get_pendientes,
    )

    capturado = {}

    async def fake_procesar(registro):
        capturado.update(registro)

    job = detector_module.InventariosDetectorJob(db={})
    monkeypatch.setattr(job, "_procesar_inventario_desde_registro", fake_procesar)

    await job._procesar_reintentos()

    assert capturado["clave"] == {
        "sistema_origen": "MPRO",
        "server_id": "server-mpro",
        "sucursal_id": "0021",
        "almacen_id": "0001",
        "folio_inventario": "QR-0001041",
    }
    assert capturado["server_name"] == "ManagementPro"
    assert capturado["almacen_nombre"] == "ALMACEN GENERAL"
    assert capturado["folio_inicial"] == "QR-0001038"
    assert capturado["fecha_inicial"] == "2026-08-01"
    assert capturado["fecha_inventario"] == "2026-09-01"
    assert capturado["metadata"] == {"source": "EDARSAHUB_SYNC"}
    assert capturado["intentos"] == 2
    assert job.stats["inventarios_reintentados"] == 1


@pytest.mark.asyncio
async def test_retry_error_by_id_reintenta_solo_el_registro_objetivo(monkeypatch):
    detector_module = _load_detector_module(monkeypatch)

    async def fake_get_by_id(record_id):
        assert record_id == 373
        return {
            "ID": 373,
            "SistemaOrigen": "SOFTRESTAURANT",
            "ServerID": "server-130mid",
            "SucursalID": "130MID",
            "AlmacenID": "3",
            "FolioInventario": "3913",
            "Estado": "ERROR",
            "Intentos": 3,
            "DetallesJSON": (
                '{"server_name":"130 MERIDA",'
                '"almacen_nombre":"PRODUCCION",'
                '"folio_inicial":"3905",'
                '"fecha_inicial":"2026-09-01T18:21:47",'
                '"fecha_inventario":"2026-09-08T13:49:35"}'
            ),
        }

    monkeypatch.setattr(detector_module, "get_inventario_error_by_id", fake_get_by_id)
    procesados = []

    async def fake_procesar(registro):
        procesados.append(registro)

    job = detector_module.InventariosDetectorJob(db={})
    monkeypatch.setattr(job, "_procesar_inventario_desde_registro", fake_procesar)

    result = await job.retry_error_by_id(373)

    assert result["status"] == "EXECUTED"
    assert result["record_id"] == 373
    assert len(procesados) == 1
    assert procesados[0]["clave"]["folio_inventario"] == "3913"
    assert procesados[0]["folio_inicial"] == "3905"
    assert procesados[0]["fecha_inicial"] == "2026-09-01T18:21:47"
    assert procesados[0]["fecha_inventario"] == "2026-09-08T13:49:35"
    assert procesados[0]["intentos"] == 3
    assert job.stats["inventarios_reintentados"] == 1
