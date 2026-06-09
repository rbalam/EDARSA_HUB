"""Tests del servicio CANÓNICO de KPIs (glosario y fórmulas, sin BD)."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pytest  # noqa: E402
from core.kpis_canonicos import KPIsCanonicosService, METRICAS_CANONICAS, resolver_metrica  # noqa: E402

AGG = {"ventas": 1000.0, "cheques": 50.0, "pax": 80.0}


def test_glosario_sinonimos():
    # ticket == cheque
    assert resolver_metrica("tickets") == "cheques"
    assert resolver_metrica("ticket_promedio") == "cheque_promedio"
    assert resolver_metrica("ticket_medio") == "cheque_promedio"
    assert resolver_metrica("comensales") == "pax"
    assert resolver_metrica("venta_neta") == "ventas"
    # canónico devuelve canónico
    assert resolver_metrica("cheque_promedio") == "cheque_promedio"


def test_metrica_desconocida():
    with pytest.raises(ValueError):
        resolver_metrica("xyz_no_existe")


def test_formulas_canonicas():
    assert KPIsCanonicosService.calcular_metrica(AGG, "ventas") == 1000.0
    assert KPIsCanonicosService.calcular_metrica(AGG, "cheques") == 50.0
    # cheque promedio = ventas / cheques
    assert KPIsCanonicosService.calcular_metrica(AGG, "cheque_promedio") == 20.0
    # ticket_promedio (sinónimo) => misma fórmula
    assert KPIsCanonicosService.calcular_metrica(AGG, "ticket_promedio") == 20.0
    # venta por pax = ventas / pax
    assert KPIsCanonicosService.calcular_metrica(AGG, "venta_por_pax") == 12.5
    assert KPIsCanonicosService.calcular_metrica(AGG, "cheques_por_pax") == 0.625


def test_division_por_cero_segura():
    a = {"ventas": 100.0, "cheques": 0.0, "pax": 0.0}
    assert KPIsCanonicosService.calcular_metrica(a, "cheque_promedio") is None
    assert KPIsCanonicosService.calcular_metrica(a, "venta_por_pax") is None


def test_metricas_disponibles_glosario():
    disp = KPIsCanonicosService.metricas_disponibles()
    ids = {m["id"] for m in disp}
    assert {"ventas", "cheques", "cheque_promedio", "pax", "venta_por_pax"} <= ids
    chq = next(m for m in disp if m["id"] == "cheque_promedio")
    assert "ticket_promedio" in chq["sinonimos"]
