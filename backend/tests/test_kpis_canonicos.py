"""Tests del servicio CANÓNICO de KPIs.
- Intérprete PURO (aplicar_definicion): sin BD.
- Catálogo SQL (resolver_metrica/calcular_metrica): integración (skip si no hay BD).

CANÓNICO:
- ventas = ventas_total con IVA; propinas se informan separadas.
- cheque_promedio y ticket_promedio = ventas / cheques.
- consumo_persona = ventas / pax.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pytest  # noqa: E402
from core.kpis_canonicos import aplicar_definicion  # noqa: E402

AGG = {"ventas": 1100.0, "propinas": 100.0, "cheques": 50.0, "pax": 80.0}

DEF_VENTAS = {"operacion": "campo", "campo_base": "ventas"}
DEF_CHEQUE_PROM = {"operacion": "ratio", "numerador": "ventas", "denominador": "cheques"}
DEF_TICKET_PROM = {"operacion": "ratio", "numerador": "ventas", "denominador": "cheques"}
DEF_CONSUMO_PERSONA = {"operacion": "ratio", "numerador": "ventas", "denominador": "pax"}


# ---- Intérprete PURO (sin BD) ----
def test_interprete_campo_ventas_total():
    assert aplicar_definicion(AGG, DEF_VENTAS) == 1100.0
    assert AGG["propinas"] == 100.0


def test_interprete_ratios_canonicos():
    assert aplicar_definicion(AGG, DEF_CHEQUE_PROM) == 22.0
    assert aplicar_definicion(AGG, DEF_TICKET_PROM) == 22.0
    assert aplicar_definicion(AGG, DEF_CONSUMO_PERSONA) == 13.75


def test_interprete_division_cero_segura():
    a = {"ventas": 90.0, "cheques": 0.0, "pax": 0.0}
    assert aplicar_definicion(a, DEF_CHEQUE_PROM) is None
    assert aplicar_definicion(a, DEF_TICKET_PROM) is None
    assert aplicar_definicion(a, DEF_CONSUMO_PERSONA) is None


def test_interprete_operacion_invalida():
    with pytest.raises(ValueError):
        aplicar_definicion(AGG, {"operacion": "potencia"})


# ---- Catálogo SQL (integración; skip si no hay conexión) ----
def _sql_ok():
    try:
        from core.kpis_canonicos import KPIsCanonicosService
        KPIsCanonicosService.refrescar_catalogo()
        return True
    except Exception:
        return False


@pytest.mark.skipif(not _sql_ok(), reason="SQL no disponible")
def test_sql_glosario_y_sinonimos():
    from core.kpis_canonicos import KPIsCanonicosService, resolver_metrica
    assert resolver_metrica("tickets") == "cheques"
    assert resolver_metrica("ventas_total") == "ventas"
    assert resolver_metrica("cheque_promedio") == "cheque_promedio"
    assert resolver_metrica("ticket_promedio") == "ticket_promedio"
    assert resolver_metrica("venta_por_pax") == "ticket_promedio"
    ids = {m["id"] for m in KPIsCanonicosService.metricas_disponibles()}
    assert {"ventas", "cheques", "cheque_promedio", "ticket_promedio", "pax"} <= ids


@pytest.mark.skipif(not _sql_ok(), reason="SQL no disponible")
def test_sql_calcular_metrica():
    from core.kpis_canonicos import KPIsCanonicosService
    assert KPIsCanonicosService.calcular_metrica(AGG, "cheque_promedio") == 22.0
    assert KPIsCanonicosService.calcular_metrica(AGG, "ticket_promedio") == 22.0
    assert KPIsCanonicosService.calcular_metrica(AGG, "ventas") == 1100.0
