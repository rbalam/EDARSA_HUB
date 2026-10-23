"""Normalización compartida de códigos de movimientos POS.

La selección del usuario se conserva por servidor; este módulo no impone
listas de tipos permitidos ni decisiones de negocio.
"""
from typing import Any, Iterable, List


def normalize_movement_code(value: Any) -> str:
    if isinstance(value, dict):
        for key in ("codigo", "ConceptoOrigen", "concepto_origen",
                    "Tm_Cve_Tipo_Movimiento", "cve", "code", "id", "value"):
            raw = value.get(key)
            if raw is not None and str(raw).strip():
                return str(raw).strip().upper()
        return ""
    return "" if value is None else str(value).strip().upper()


def normalize_movement_codes(values: Iterable[Any] = None) -> List[str]:
    result = []
    seen = set()
    for value in values or []:
        code = normalize_movement_code(value)
        if code and code not in seen:
            seen.add(code)
            result.append(code)
    return result
