"""Tests de la estadística de benchmark (pura, sin BD)."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from modules.comercial_benchmark.stats import resumen_benchmark  # noqa: E402


def test_envelope_basico():
    r = resumen_benchmark(100, [100, 80, 60, 40, 20])
    assert r["valor_propio"] == 100
    assert r["promedio_grupo"] == 60
    assert r["mediana_grupo"] == 60
    assert r["minimo_grupo"] == 20 and r["maximo_grupo"] == 100
    assert r["cobertura_unidades"] == 5
    assert r["diferencia_absoluta"] == 40
    assert r["diferencia_porcentual"] == round(100 * 40 / 60, 2)
    assert r["posicion_relativa"] == 1            # mayor valor => 1°
    assert r["percentil_propio"] == 90.0          # mejor que 4, igual a 1 de 5
    assert r["cuartil_propio"] == 4


def test_sin_valor_propio():
    r = resumen_benchmark(None, [10, 20, 30])
    assert r["valor_propio"] is None
    assert r["promedio_grupo"] == 20
    assert r["diferencia_absoluta"] is None
    assert r["percentil_propio"] is None


def test_grupo_vacio():
    r = resumen_benchmark(50, [])
    assert r["promedio_grupo"] is None
    assert r["cobertura_unidades"] == 0


def test_cuartiles():
    pob = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
    r = resumen_benchmark(30, pob)
    assert r["percentil_25_grupo"] == 32.5
    assert r["percentil_75_grupo"] == 77.5
    assert r["cuartil_propio"] in (1, 2)
