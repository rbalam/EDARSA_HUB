"""Catalogo runtime para Sincronizacion Historica.

Toda opcion de UI se deriva de fuentes canonicas SQL. No contiene listas fijas de
sistemas, sucursales, categorias o capabilities.
"""
from __future__ import annotations

from collections import defaultdict
from typing import Any, Dict, List, Mapping, Sequence, Tuple

from core.sql_first.db import get_sql_connection
from core.system_capability_resolver import SystemCapabilityResolver
from modules.sistema.sync_catalogo_service import get_historical_registry


def _rows(query: str, params=()) -> List[Dict[str, Any]]:
    conn = get_sql_connection()
    cur = conn.cursor(as_dict=True)
    try:
        cur.execute(query, params)
        return [dict(row) for row in (cur.fetchall() or [])]
    finally:
        cur.close()
        conn.close()


def _unit_rows() -> List[Dict[str, Any]]:
    return _rows(
        """
        SELECT
            CONVERT(varchar(36), u.id) AS unit_id,
            u.codigo AS unit_code,
            u.nombre AS unit_name,
            CONVERT(varchar(36), u.server_id) AS connection_id,
            u.sucursal_origen_id AS branch_origin_id,
            s.system_type AS raw_system_type,
            CONVERT(varchar(36), s.sistema_version_id) AS system_version_id,
            s.nombre AS connection_name,
            s.tipo_conexion AS connection_type,
            s.activo AS connection_active,
            map.SucursalID AS branch_id,
            suc.CodigoSucursal AS branch_code,
            suc.NombreSucursal AS branch_name,
            suc.EmpresaID AS company_id
        FROM dbo.Unidades_Negocio u
        JOIN dbo.Servidores_Conexiones s
          ON LOWER(CONVERT(nvarchar(100), s.id))
           = LOWER(CONVERT(nvarchar(100), u.server_id))
        LEFT JOIN dbo.Sistema_SucursalServidorMapeo map
          ON LOWER(CONVERT(nvarchar(100), map.ServidorID))
           = LOWER(CONVERT(nvarchar(100), u.server_id))
         AND ISNULL(map.Activo,0)=1
         AND (
              NULLIF(LTRIM(RTRIM(CONVERT(nvarchar(100),map.SucursalOrigenID))),'')
              =
              NULLIF(LTRIM(RTRIM(CONVERT(nvarchar(100),u.sucursal_origen_id))),'')
              OR (
                  NULLIF(LTRIM(RTRIM(CONVERT(nvarchar(100),map.SucursalOrigenID))),'') IS NULL
                  AND
                  NULLIF(LTRIM(RTRIM(CONVERT(nvarchar(100),u.sucursal_origen_id))),'') IS NULL
              )
         )
        LEFT JOIN dbo.Sistema_Sucursales suc
          ON suc.SucursalID=map.SucursalID
        WHERE ISNULL(u.activo,1)=1
          AND ISNULL(s.activo,1)=1
        ORDER BY u.codigo
        """
    )


def _internal_catalog() -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    registry = get_historical_registry(
        incluir_inactivos=False,
        incluir_incompletos=False,
    )
    supported_systems = {
        str(item.get("system_code") or "").upper(): item
        for item in registry
        if item.get("system_code")
    }

    resolver = SystemCapabilityResolver()
    unit_contexts: List[Dict[str, Any]] = []
    grouped: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for row in _unit_rows():
        code = str(row.get("unit_code") or "").strip().upper()
        if code:
            grouped[code].append(row)

    for code, candidates in sorted(grouped.items()):
        normalized_candidates = []
        for row in candidates:
            normalized = resolver.normalize_system_type(
                str(row.get("raw_system_type") or "")
            )
            system_code = str(
                normalized.get("codigo_sistema") or ""
            ).strip().upper()
            if system_code in supported_systems:
                normalized_candidates.append((row, system_code))

        if not normalized_candidates:
            continue

        systems_for_unit = {
            system_code for _, system_code in normalized_candidates
        }
        if len(systems_for_unit) != 1:
            continue

        branch_bindings = {
            (
                row.get("branch_id"),
                str(row.get("branch_origin_id") or "").strip(),
            )
            for row, _ in normalized_candidates
            if row.get("branch_id") is not None
        }
        if len(branch_bindings) != 1:
            # Fail-closed: no elegimos una sucursal fisica por posicion,
            # nombre ni primer resultado cuando el mapeo es ambiguo/ausente.
            continue

        row, system_code = normalized_candidates[0]
        branch_id, branch_origin = next(iter(branch_bindings))
        template = supported_systems[system_code]
        unit_contexts.append(
            {
                "unit_id": row.get("unit_id"),
                "unit_code": code,
                "unit_name": row.get("unit_name"),
                "connection_id": row.get("connection_id"),
                "connection_name": row.get("connection_name"),
                "connection_type": row.get("connection_type"),
                "system_version_id": row.get("system_version_id"),
                "branch_id": branch_id,
                "branch_code": row.get("branch_code"),
                "branch_name": row.get("branch_name"),
                "branch_origin_id": branch_origin or None,
                "company_id": row.get("company_id"),
                "system_id": template.get("system_id"),
                "system_code": system_code,
                "system_name": template.get("system_name"),
            }
        )

    return registry, unit_contexts

def planner_inputs():
    return _internal_catalog()


def get_catalog_payload() -> Dict[str, Any]:
    registry, units = _internal_catalog()

    systems: Dict[str, Dict[str, Any]] = {}
    categories: Dict[str, Dict[str, Any]] = {}
    capability_systems: Dict[str, set] = defaultdict(set)

    for item in registry:
        system_code = str(item.get("system_code") or "").upper()
        systems.setdefault(
            system_code,
            {
                "id": item.get("system_id"),
                "code": system_code,
                "name": item.get("system_name"),
            },
        )

        category_key = str(item.get("category_key") or "")
        category = categories.setdefault(
            category_key,
            {
                "key": category_key,
                "name": item.get("category_name"),
                "capabilities": {},
            },
        )
        cap_key = str(item.get("capability_key") or "")
        cap = category["capabilities"].setdefault(
            cap_key,
            {
                "key": cap_key,
                "display_name": item.get("display_name"),
                "entity_key": item.get("entity_key"),
                "supports_resume": bool(item.get("supports_resume")),
                "supports_safe_stop": bool(item.get("supports_safe_stop")),
                "systems": [],
            },
        )
        capability_systems[cap_key].add(system_code)
        cap["systems"] = sorted(capability_systems[cap_key])

    category_list = []
    for category in categories.values():
        caps = sorted(
            category["capabilities"].values(),
            key=lambda value: value["display_name"] or value["key"],
        )
        category_list.append(
            {
                "key": category["key"],
                "name": category["name"],
                "capabilities": caps,
            }
        )
    category_list.sort(key=lambda value: value["name"] or value["key"])

    safe_units = [
        {
            key: unit.get(key)
            for key in (
                "unit_id",
                "unit_code",
                "unit_name",
                "connection_id",
                "connection_name",
                "connection_type",
                "branch_id",
                "branch_code",
                "branch_name",
                "branch_origin_id",
                "system_id",
                "system_code",
                "system_name",
            )
        }
        for unit in units
    ]

    return {
        "source": "EDARSAHUB_CANONICAL_SQL",
        "systems": sorted(
            systems.values(),
            key=lambda value: value["name"] or value["code"],
        ),
        "units": safe_units,
        "categories": category_list,
        "counts": {
            "systems": len(systems),
            "units": len(safe_units),
            "capability_bindings": len(registry),
        },
    }
