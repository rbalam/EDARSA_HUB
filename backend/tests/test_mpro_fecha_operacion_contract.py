from datetime import date, datetime, timedelta
import importlib
from pathlib import Path
import sys
import types


BACKEND_ROOT = Path(__file__).resolve().parents[1]
COMERCIAL_V2_ROOT = BACKEND_ROOT / "modules" / "comercial_v2"

# Evita ejecutar modules/comercial_v2/__init__.py, que importa rutas,
# seguridad y configuración SQL ajenas a esta prueba unitaria.
package = types.ModuleType("modules.comercial_v2")
package.__path__ = [str(COMERCIAL_V2_ROOT)]
package.__package__ = "modules.comercial_v2"
sys.modules["modules.comercial_v2"] = package

schemas = importlib.import_module("modules.comercial_v2.schemas")

# El agrupador bajo prueba no usa persistencia. Se instala un stub
# fail-closed con el contrato completo importado por el módulo productivo.
repository_stub = types.ModuleType(
    "modules.comercial_v2.repository_comercial_edarsahub"
)
repository_stub.__package__ = "modules.comercial_v2"


def _unexpected_repository_call(*_args, **_kwargs):
    raise AssertionError(
        "La prueba del agrupador no debe invocar persistencia SQL"
    )


# Contrato completo importado por sync_comercial_edarsahub.py.
# La configuración permanece vacía y toda operación del repositorio
# aborta si la unidad bajo prueba intenta utilizar persistencia.
repository_stub.EDARSAHUB_CONFIG = {}

repository_stub.get_sucursales_mpro = (
    _unexpected_repository_call
)
repository_stub.get_unidades_negocio_config = (
    _unexpected_repository_call
)
repository_stub.insert_sync_log = (
    _unexpected_repository_call
)
repository_stub.upsert_kpi_diario = (
    _unexpected_repository_call
)
repository_stub.upsert_ventas_dia_abiertas = (
    _unexpected_repository_call
)

sys.modules[
    "modules.comercial_v2.repository_comercial_edarsahub"
] = repository_stub

sync = importlib.import_module(
    "modules.comercial_v2.sync_comercial_edarsahub"
)

SistemaOrigen = schemas.SistemaOrigen
UnidadNegocioConfig = schemas.UnidadNegocioConfig


def _config(sistema_origen: SistemaOrigen) -> UnidadNegocioConfig:
    return UnidadNegocioConfig(
        unidad_negocio_pk="9BC05CED-6B2B-4A0A-AA90-CE649B78E12C",
        unidad_negocio_nombre="UNIDAD PRUEBA",
        server_id="server-test",
        sucursal_id="0021",
        sucursal_nombre="UNIDAD PRUEBA",
        sistema_origen=sistema_origen,
        activo=True,
    )


def test_mpro_vn_fecha_es_fecha_comercial_y_no_debe_desplazarse(
    monkeypatch,
):
    """
    Contrato MPRO confirmado empíricamente:

    Venta_Encabezado.Vn_Fecha contiene la fecha comercial del ticket,
    pero su componente de hora siempre es 00:00:00.

    No debe tratarse como timestamp operativo, porque una ventana que
    cruza medianoche la desplazaría artificialmente al día anterior.
    """

    def fecha_operativa_simulada(_unidad_pk, timestamp):
        return timestamp.date() - timedelta(days=1)

    monkeypatch.setattr(
        "core.utils.operational_window.get_fecha_operacion",
        fecha_operativa_simulada,
    )

    rows = [
        {
            "Vn_Fecha": datetime(2026, 7, 10, 0, 0, 0),
            "Vn_Folio": "FOLIO-1",
            "Vn_Precio_Neto_Importe": 130405.00,
            "total_personas": 69,
        }
    ]

    result = sync._agrupar_ventas_cerradas_por_fecha_operacion(
        rows,
        _config(SistemaOrigen.MPRO),
        fecha_inicio=date(2026, 7, 9),
        fecha_fin=date(2026, 7, 10),
    )

    assert len(result) == 1
    assert result[0]["fecha_operacion"] == date(2026, 7, 10)


def test_softrestaurant_usa_fecha_calendario_de_turnos_apertura(
    monkeypatch,
):
    """
    SoftRestaurant agrupa por la fecha calendario de fecha_hora proveniente
    de turnos.apertura. Este agrupador no debe aplicar operational_window.
    """

    def operational_window_no_debe_usarse(*_args, **_kwargs):
        raise AssertionError(
            "SoftRestaurant no debe aplicar operational_window en este agrupador"
        )

    monkeypatch.setattr(
        "core.utils.operational_window.get_fecha_operacion",
        operational_window_no_debe_usarse,
    )

    rows = [
        {
            "fecha_hora": datetime(2026, 7, 11, 1, 30, 0),
            "folio": "CHEQUE-1",
            "ventas_total": 1000.00,
            "propinas": 100.00,
            "num_personas": 4,
        }
    ]

    result = sync._agrupar_ventas_cerradas_por_fecha_operacion(
        rows,
        _config(SistemaOrigen.SOFTRESTAURANT),
        fecha_inicio=date(2026, 7, 11),
        fecha_fin=date(2026, 7, 11),
    )

    assert len(result) == 1
    assert result[0]["fecha_operacion"] == date(2026, 7, 11)
