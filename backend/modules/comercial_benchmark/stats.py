"""
Estadística de benchmark (PURA, sin BD) — testable de forma aislada.
Calcula el "envelope" comparativo exigido (criterios 46–54).
"""
from __future__ import annotations

import statistics
from typing import Dict, List, Optional


def _percentil(valor: float, poblacion: List[float]) -> Optional[float]:
    """Percentil (0–100) de `valor` dentro de `poblacion` (método rank)."""
    if not poblacion:
        return None
    menores = sum(1 for v in poblacion if v < valor)
    iguales = sum(1 for v in poblacion if v == valor)
    return round(100.0 * (menores + 0.5 * iguales) / len(poblacion), 2)


def _cuantil(poblacion: List[float], q: float) -> Optional[float]:
    if not poblacion:
        return None
    s = sorted(poblacion)
    if len(s) == 1:
        return float(s[0])
    pos = q * (len(s) - 1)
    lo = int(pos)
    frac = pos - lo
    hi = min(lo + 1, len(s) - 1)
    return round(s[lo] + (s[hi] - s[lo]) * frac, 4)


def resumen_benchmark(valor_propio: Optional[float], valores_grupo: List[float]) -> Dict:
    """
    valores_grupo: TODOS los valores del grupo (incluye el propio).
    Devuelve agregados estadísticos + posición del propio.
    """
    poblacion = [float(v) for v in valores_grupo if v is not None]
    n = len(poblacion)
    promedio = round(statistics.fmean(poblacion), 4) if poblacion else None
    mediana = round(statistics.median(poblacion), 4) if poblacion else None
    p25 = _cuantil(poblacion, 0.25)
    p75 = _cuantil(poblacion, 0.75)

    out = {
        "valor_propio": round(float(valor_propio), 4) if valor_propio is not None else None,
        "promedio_grupo": promedio,
        "mediana_grupo": mediana,
        "percentil_25_grupo": p25,
        "percentil_75_grupo": p75,
        "minimo_grupo": round(min(poblacion), 4) if poblacion else None,
        "maximo_grupo": round(max(poblacion), 4) if poblacion else None,
        "cobertura_unidades": n,
        "diferencia_absoluta": None,
        "diferencia_porcentual": None,
        "percentil_propio": None,
        "posicion_relativa": None,
        "cuartil_propio": None,
    }
    if valor_propio is not None and promedio is not None:
        out["diferencia_absoluta"] = round(float(valor_propio) - promedio, 4)
        out["diferencia_porcentual"] = (
            round(100.0 * (float(valor_propio) - promedio) / promedio, 2) if promedio else None
        )
        out["percentil_propio"] = _percentil(float(valor_propio), poblacion)
        # posición: 1 = mejor (mayor valor)
        ordenado = sorted(poblacion, reverse=True)
        try:
            out["posicion_relativa"] = ordenado.index(float(valor_propio)) + 1
        except ValueError:
            out["posicion_relativa"] = None
        pp = out["percentil_propio"]
        if pp is not None:
            out["cuartil_propio"] = 4 if pp >= 75 else 3 if pp >= 50 else 2 if pp >= 25 else 1
    return out
