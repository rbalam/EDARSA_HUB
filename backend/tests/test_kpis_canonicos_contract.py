import os

# TEST-ONLY EDARSAHUB SQL CONFIG BOOTSTRAP
# Los módulos canónicos validan configuración al importarse.
# Estos valores no se utilizan para abrir conexiones.
os.environ.setdefault(
    "EDARSAHUB_SQL_HOST",
    "unit-test.invalid",
)
os.environ.setdefault(
    "EDARSAHUB_SQL_PORT",
    "1433",
)
os.environ.setdefault(
    "EDARSAHUB_SQL_DATABASE",
    "EDARSAHUB",
)
os.environ.setdefault(
    "EDARSAHUB_SQL_USER",
    "UNIT_TEST_READONLY",
)
os.environ.setdefault(
    "EDARSAHUB_SQL_PASSWORD",
    "UNIT_TEST_NOT_A_SECRET",
)

from core.kpis_canonicos import service as service_module
from migrations import comercial_metricas_canonicas_20260609 as catalog


def test_metricas_comerciales_v1_contract(monkeypatch):
    monkeypatch.setattr(
        service_module._Catalogo,
        "defs",
        staticmethod(lambda: {}),
    )

    metricas = (
        service_module.KPIsCanonicosService
        ._metricas_para_agregado({
            "ventas": 1200,
            "ventas_sin_propina": 1000,
            "propinas": 200,
            "cheques": 10,
            "pax": 20,
        })
    )

    assert metricas["ventas"] == 1200
    assert metricas["ventas_total"] == 1200
    assert "ventas_sin_propina" not in metricas
    assert metricas["cheque_promedio"] == 120
    assert metricas["ticket_promedio"] == 120
    assert metricas["pax_promedio"] == 60
    assert metricas["consumo_promedio_pax"] == 60
    assert metricas["pax_por_cheque"] == 2


def test_catalogo_declara_formulas_canonicas():
    metricas = {
        row[0]: row
        for row in catalog.METRICAS
    }

    assert metricas["ventas"][5] == "ventas"

    assert metricas["cheque_promedio"][6:8] == (
        "ventas",
        "cheques",
    )

    assert metricas["ticket_promedio"][6:8] == (
        "ventas",
        "cheques",
    )

    assert metricas["pax_promedio"][6:8] == (
        "ventas",
        "pax",
    )

    assert metricas["pax_por_cheque"][6:8] == (
        "pax",
        "cheques",
    )
