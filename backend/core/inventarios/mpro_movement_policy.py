"""Política canónica de movimientos MPRO para Análisis de Inventarios.

Fuente de negocio: tabla validada por usuario (2026-10-23).
Sólo estos conceptos origen participan en la columna MOVIMIENTOS.
Los demás conceptos (incluidos ajustes de inventario) permanecen visibles
en catálogo, pero no son autorizados para el análisis.
"""
from __future__ import annotations

from typing import Any, Iterable, List, Set

MPRO_INVENTORY_MOVEMENT_POLICY = {
    "050": {"descripcion": "ENTRADA POR COMPRA", "grupo": "COMPRA", "tipo": "EN"},
    "106": {"descripcion": "ENTRADA POR TRASPASO", "grupo": "TRASPASO", "tipo": "EN"},
    "108": {"descripcion": "ENTRADA POR CONVERSION", "grupo": "CONVERSION", "tipo": "EN"},
    "109": {"descripcion": "ANULACION ENTRADA POR CONVERSION", "grupo": "CONVERSION", "tipo": "EN"},
    "112": {"descripcion": "ENTRADA TRASPASO TABLAJERIA", "grupo": "TABLAJERIA", "tipo": "EN"},
    "506": {"descripcion": "SALIDA POR TRASPASO", "grupo": "TRASPASO", "tipo": "SA"},
    "508": {"descripcion": "SALIDA POR CONVERSION", "grupo": "CONVERSION", "tipo": "SA"},
    "509": {"descripcion": "ANULACION SALIDA POR CONVERSION", "grupo": "CONVERSION", "tipo": "SA"},
    "510": {"descripcion": "SALIDA POR MERMA", "grupo": "MERMA", "tipo": "SA"},
    "512": {"descripcion": "SALIDA TRASPASO TABLAJERIA", "grupo": "TABLAJERIA", "tipo": "SA"},
}

MPRO_INVENTORY_MOVEMENT_CODES = tuple(MPRO_INVENTORY_MOVEMENT_POLICY.keys())
MPRO_INVENTORY_MOVEMENT_CODE_SET = frozenset(MPRO_INVENTORY_MOVEMENT_CODES)


def normalize_movement_code(value: Any) -> str:
    if isinstance(value, dict):
        for key in (
            "codigo",
            "ConceptoOrigen",
            "concepto_origen",
            "Tm_Cve_Tipo_Movimiento",
            "cve",
            "code",
            "id",
        ):
            raw = value.get(key)
            if raw is not None and str(raw).strip():
                return str(raw).strip().upper()
        return ""
    if value is None:
        return ""
    return str(value).strip().upper()


def normalize_movement_codes(values: Iterable[Any] | None) -> List[str]:
    seen: Set[str] = set()
    result: List[str] = []
    for value in values or []:
        code = normalize_movement_code(value)
        if not code or code in seen:
            continue
        seen.add(code)
        result.append(code)
    return result


def effective_mpro_inventory_codes(
    values: Iterable[Any] | None,
    *,
    default_when_empty: bool = True,
) -> Set[str]:
    selected = set(normalize_movement_codes(values))
    if not selected and default_when_empty:
        return set(MPRO_INVENTORY_MOVEMENT_CODE_SET)
    return selected.intersection(MPRO_INVENTORY_MOVEMENT_CODE_SET)
