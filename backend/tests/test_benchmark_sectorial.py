"""Regresión de funciones puras del Benchmark Sectorial e Ingesta.
No requieren DB. Ejecutar: cd /app/backend && python -m pytest tests/test_benchmark_sectorial.py -q
"""
from modules.comercial.services.benchmark_sectorial_service import _desviacion, _semaforo
from modules.comercial.services.ingesta_competencia_service import _parse_json_array, _normaliza_filas


def test_desviacion():
    assert _desviacion(150, 100) == 50.0
    assert _desviacion(80, 100) == -20.0
    assert _desviacion(100, 100) == 0.0
    assert _desviacion(None, 100) is None
    assert _desviacion(100, 0) is None
    assert _desviacion(100, None) is None


def test_semaforo_caro_barato_alineado():
    assert _semaforo(30, 15)["oportunidad"] == "CARO"
    assert _semaforo(30, 15)["semaforo"] == "rojo"
    assert _semaforo(-30, 15)["oportunidad"] == "BARATO"
    assert _semaforo(-30, 15)["semaforo"] == "verde"
    assert _semaforo(5, 15)["oportunidad"] == "ALINEADO"
    assert _semaforo(None, 15)["oportunidad"] == "SIN_DATO"


def test_parse_json_array_con_fences():
    txt = '```json\n[{"competidor":"X","categoria":"C","producto":"P","precio":10,"moneda":"MXN"}]\n```'
    rows = _parse_json_array(txt)
    assert isinstance(rows, list) and len(rows) == 1
    assert rows[0]["producto"] == "P"


def test_parse_json_array_invalido():
    assert _parse_json_array("no soy json") == []
    assert _parse_json_array("") == []


def test_normaliza_filas_filtra_invalidos():
    crudas = [
        {"competidor": "A", "categoria": "Carnes", "producto": "Rib Eye", "precio": "$480.00", "moneda": "mxn"},
        {"producto": "", "precio": 100},          # sin producto -> fuera
        {"producto": "Sopa", "precio": 0},          # precio 0 -> fuera
        {"producto": "Agua", "precio": "abc"},      # precio no numerico -> fuera
        {"producto": "Vino", "precio": -50},        # negativo -> fuera
    ]
    norm = _normaliza_filas(crudas)
    assert len(norm) == 1
    assert norm[0]["producto"] == "Rib Eye"
    assert norm[0]["precio"] == 480.0
    assert norm[0]["moneda"] == "MXN"
