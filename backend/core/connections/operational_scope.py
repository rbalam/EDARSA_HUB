"""Canonical operational-scope rules for EDARSAHUB connections.

A connection may exist without an operational business unit (technical/query-only),
but it must not become operational until at least one active Unidad_Negocio maps to
its server_id. Shared connections are represented by multiple unit mappings, not
by duplicated connection records.
"""

from __future__ import annotations

from typing import Dict, List

from core.unidades_service import UnidadesService


def classify_operational_scope(
    unit_count: int,
    visible_en_operaciones: bool,
) -> str:
    if unit_count > 1:
        return "SHARED"
    if unit_count == 1:
        return "OPERATIONAL"
    if visible_en_operaciones:
        return "INVALID_OPERATIONAL_UNMAPPED"
    return "TECHNICAL"


def active_units_for_server(server_id: str) -> List[Dict]:
    wanted = str(server_id or "").strip().lower()
    if not wanted:
        return []

    return [
        unit
        for unit in UnidadesService.get_all()
        if str(unit.get("server_id") or "").strip().lower() == wanted
    ]


def require_operational_mapping(
    server_id: str,
    visible_en_operaciones: bool,
) -> None:
    if not visible_en_operaciones:
        return

    units = active_units_for_server(server_id)
    if not units:
        raise ValueError(
            "La conexion no puede habilitarse para operaciones sin una "
            "Unidad de Negocio activa vinculada en el Catalogo Maestro"
        )


def connection_scope_summary(
    server_id: str,
    visible_en_operaciones: bool,
) -> Dict:
    units = active_units_for_server(server_id)
    unit_ids = [
        str(unit.get("unidad_negocio_pk") or "").strip()
        for unit in units
        if unit.get("unidad_negocio_pk")
    ]
    return {
        "classification": classify_operational_scope(
            len(unit_ids),
            bool(visible_en_operaciones),
        ),
        "unit_count": len(unit_ids),
        "unidad_negocio_ids": unit_ids,
        "operational_allowed": bool(unit_ids),
    }
