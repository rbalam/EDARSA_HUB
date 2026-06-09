"""
Regresión — Reporteador BI (Informe Gerencial MECA MPRO), SQL-First NO-LIVE.
Valida las 9 páginas: las disponibles devuelven datos reales; las no
sincronizadas devuelven disponible=false con nota PENDIENTE (sin inventar).
Ejecutar: cd /app/backend && python -m pytest tests/test_reporteador_bi.py -q
"""
import os
import requests
import pytest

API = os.environ.get("REACT_APP_BACKEND_URL", "http://localhost:8001").rstrip("/")


@pytest.fixture(scope="module")
def token():
    r = requests.post(f"{API}/api/auth/login",
                      json={"email": "admin@edarsa.com", "password": "pruebas123"}, timeout=30)
    assert r.status_code == 200, r.text
    return r.json().get("token") or r.json().get("access_token")


def _g(token, path, **params):
    r = requests.get(f"{API}/api/reporteador-bi{path}", params=params,
                     headers={"Authorization": f"Bearer {token}"}, timeout=60)
    assert r.status_code == 200, f"{path} -> {r.status_code}: {r.text[:300]}"
    return r.json()


def test_paginas_son_9(token):
    d = _g(token, "/paginas")
    assert len(d["paginas"]) == 9


def test_analisis_ventas_real(token):
    d = _g(token, "/analisis-ventas", periodo="mes")
    assert d["disponible"] is True
    assert d["kpis"]["ventas"] > 0 and d["kpis"]["ticket_promedio"] > 0
    assert len(d["serie_diaria"]) > 0
    assert any(c["clasificacion"] in ("ALIMENTOS", "BEBIDAS") for c in d["clasificacion"])


def test_ventas_semana_real(token):
    d = _g(token, "/ventas-semana", periodo="anio")
    assert d["disponible"] is True and len(d["series"]) > 0


def test_ventas_mes_real(token):
    d = _g(token, "/ventas-mes", meses=12)
    assert d["disponible"] is True and len(d["series"]) > 0
    assert "var_mes_anterior" in d["comparativos"]


def test_ambientacion_hora_real(token):
    d = _g(token, "/ambientacion", periodo="mes")
    assert d["disponible"] is True and len(d["ventas_por_hora"]) > 0
    assert d["ambientacion_evento"]["disponible"] is False  # bandera evento no sincronizada


def test_revision_tickets_real(token):
    d = _g(token, "/revision-tickets", periodo="mes")
    assert d["disponible"] is True and d["resumen"]["num_tickets"] >= 0


def test_kpis_mes_real(token):
    d = _g(token, "/kpis-mes")
    assert d["disponible"] is True and d["kpis"]["ventas"] > 0
    assert d["metas"]["disponible"] is False  # metas no sincronizadas


@pytest.mark.parametrize("page", ["gastos", "rotacion-mesas", "analisis-documentos"])
def test_paginas_pendientes(token, page):
    d = _g(token, f"/{page}")
    assert d["disponible"] is False
    assert "nota" in d and d.get("fuente_requerida")
