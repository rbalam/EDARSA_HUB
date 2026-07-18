import os
from unittest.mock import Mock

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


def test_series_periodo_resuelve_nombre_legacy_a_unidad_pk(monkeypatch):
    captured = {}
    unidad_pk = "9bc05ced-6b2b-4a0a-aa90-ce649b78e12c"

    monkeypatch.setattr(
        service_module.UnidadesService,
        "resolver_pk",
        staticmethod(lambda valor: unidad_pk),
    )

    def fake_execute_sql_query_params(*args):
        captured["sql"] = args[-2]
        captured["params"] = args[-1]
        return [{
            "periodo": "2026-07-01",
            "fecha_inicio": "2026-07-01",
            "fecha_fin": "2026-07-01",
            "ventas": 1200,
            "propinas": 200,
            "cheques": 10,
            "pax": 20,
            "dias": 1,
        }]

    monkeypatch.setattr(
        service_module,
        "execute_sql_query_params",
        fake_execute_sql_query_params,
    )
    monkeypatch.setattr(
        service_module._Catalogo,
        "defs",
        staticmethod(lambda: {}),
    )

    rows = service_module.KPIsCanonicosService.series_periodo(
        desde="2026-07-01",
        hasta="2026-07-02",
        nivel="dia",
        unidad_nombre="130° Mérida",
    )

    assert "CONVERT(varchar(36), unidad_negocio_pk) = %s" in captured["sql"]
    assert "unidad_negocio_nombre = %s" not in captured["sql"]
    assert captured["params"] == (
        "2026-07-01",
        "2026-07-02",
        unidad_pk,
    )
    assert rows[0]["ventas"] == 1200
    assert rows[0]["cheque_promedio"] == 120
    assert rows[0]["pax_promedio"] == 60


def test_series_periodo_falla_cerrado_si_unidad_no_resuelve(monkeypatch):
    execute = Mock(side_effect=AssertionError("no debe consultar sin unidad_pk"))

    monkeypatch.setattr(
        service_module.UnidadesService,
        "resolver_pk",
        staticmethod(lambda valor: None),
    )
    monkeypatch.setattr(
        service_module,
        "execute_sql_query_params",
        execute,
    )

    assert service_module.KPIsCanonicosService.series_periodo(
        desde="2026-07-01",
        hasta="2026-07-02",
        nivel="dia",
        unidad_nombre="unidad inexistente",
    ) == []
    execute.assert_not_called()
