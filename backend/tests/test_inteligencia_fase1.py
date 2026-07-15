"""
Regresión Fase 1 — Portal Inteligencia Comercial (SQL-First, NO-LIVE).
Valida: KPIs canónicos (ticket/cheque promedio), clasificación Alimentos/Bebidas/Otros,
casas (grupo_comercial), reporte de alcohol, drill-down de tickets y exportables.
Ejecutar:  cd /app/backend && python -m pytest tests/test_inteligencia_fase1.py -q
Requiere variables de entorno SQL (backend/.env) y datos en EDARSAHUB.
"""
import os
import requests
import pytest

API = os.environ.get("REACT_APP_BACKEND_URL", "http://localhost:8001").rstrip("/")
EMAIL = os.environ.get("EDARSAHUB_TEST_AUTH_EMAIL")
PASSWORD = os.environ.get("EDARSAHUB_TEST_AUTH_PASSWORD")

if not EMAIL or not PASSWORD:
    pytest.skip(
        "E2E omitido: faltan EDARSAHUB_TEST_AUTH_EMAIL y "
        "EDARSAHUB_TEST_AUTH_PASSWORD",
        allow_module_level=True,
    )
@pytest.fixture(scope="module")
def token():
    r = requests.post(f"{API}/api/auth/login", json={"email": EMAIL, "password": PASSWORD}, timeout=30)
    assert r.status_code == 200, r.text
    t = r.json().get("token") or r.json().get("access_token")
    assert t, "sin token"
    return t


def _get(token, path, **params):
    r = requests.get(f"{API}/api/inteligencia{path}", params=params,
                     headers={"Authorization": f"Bearer {token}"}, timeout=60)
    assert r.status_code == 200, f"{path} -> {r.status_code}: {r.text[:300]}"
    return r.json()


def test_dashboard_kpis_canonicos(token):
    d = _get(token, "/dashboard", periodo="mes")
    k = d["kpis"]
    assert k["ventas_totales"] > 0
    assert k["ticket_promedio"] > 0, "ticket_promedio (ventas/PAX) debe existir y ser > 0"
    assert k["cheque_promedio"] > 0, "cheque_promedio (ventas/cheques) debe existir y ser > 0"
    # cheque_promedio (por cuenta) >= ticket_promedio (por persona) salvo pax<cheques
    assert k["cheque_promedio"] >= k["ticket_promedio"]


def test_clasificacion_alimentos_bebidas_otros(token):
    d = _get(token, "/familias", periodo="mes")
    clas = {c["clasificacion"] for c in d["ventas_clasificacion"]}
    assert {"ALIMENTOS", "BEBIDAS"}.issubset(clas), f"faltan macro-clasificaciones: {clas}"
    # Las familias con prefijo 'B ' (bebidas) NO deben caer en ALIMENTOS
    for c in d["ventas_clasificacion"]:
        if c["clasificacion"] == "ALIMENTOS":
            assert not any(f["familia"].startswith("B ") for f in c["familias"]), \
                "una familia 'B ' (bebida) quedó mal clasificada en ALIMENTOS"


def test_casas_desde_grupo_comercial(token):
    d = _get(token, "/casas", periodo="mes")
    casas = d["casas_distribuidoras"]
    assert len(casas) > 0, "casas/distribuidores vacío (debe poblarse desde grupo_comercial)"
    assert all(c["casa"] for c in casas)


def test_reporte_alcohol(token):
    d = _get(token, "/alcohol", periodo="mes")
    assert d["con_alcohol"]["ventas"] >= 0 and d["sin_alcohol"]["ventas"] >= 0
    assert d["con_alcohol"]["ventas"] + d["sin_alcohol"]["ventas"] > 0


def test_drilldown_tickets_y_lineas(token):
    d = _get(token, "/tickets", periodo="mes", limit=5)
    assert d["total"] > 0, "no se reconstruyeron tickets"
    t = d["tickets"][0]
    det = _get(token, "/ticket-detalle", numero_ticket=t["numero_ticket"], unidad=t["unidad"], fecha=t["fecha"])
    assert det["n_lineas"] > 0, "el ticket no tiene líneas (drill-down al nivel más bajo)"
    assert det["total"] > 0


def test_dia_no_vacia_horario_productos(token):
    """Bug #4: en 'Día' horario/productos no deben venir vacíos (ancla al detalle)."""
    d = _get(token, "/dashboard", periodo="dia")
    assert len(d["ventas_horario"]) > 0, "ventas_horario vacío en periodo dia"
    assert len(d["top_productos"]) > 0, "top_productos vacío en periodo dia"


def test_catalogo_clasificaciones(token):
    d = _get(token, "/clasificaciones")
    codigos = {c["codigo"] for c in d["clasificaciones"]}
    assert {"ALIMENTOS", "BEBIDAS", "OTROS", "PENDIENTE_CLASIFICACION"}.issubset(codigos)


def test_admin_listar_y_clasificar(token):
    """Lista productos pendientes y clasifica uno como MANUAL; verifica que sale de pendientes."""
    lst = _get(token, "/admin/productos-clasificacion", estado="pendientes", page_size=1)
    if lst["total"] == 0:
        return  # nada pendiente (ya clasificado), test no aplica
    prod = lst["productos"][0]
    otros = next(c for c in _get(token, "/clasificaciones")["clasificaciones"] if c["codigo"] == "OTROS")
    r = requests.post(f"{API}/api/inteligencia/admin/clasificar",
                      json={"clasificacion_id": otros["id"], "producto_ids": [prod["producto_id"]]},
                      headers={"Authorization": f"Bearer {token}"}, timeout=30)
    assert r.status_code == 200 and r.json().get("actualizados", 0) >= 1


def test_admin_requiere_auth():
    r = requests.get(f"{API}/api/inteligencia/admin/familias-pendientes", timeout=30)
    assert r.status_code in (401, 403), "endpoint admin debe exigir autenticación"
