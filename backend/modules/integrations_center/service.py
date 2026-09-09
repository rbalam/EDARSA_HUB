"""Servicio de composicion para Gate 5B.

La fachada reutiliza los contratos existentes:
- DATA_SOURCE: core.server_registry
- API_LOCAL: modules.api_connections
- CORE: api.admin_core_connections (solo SUPERADMIN)
- Health/catalogos: SQL canonico existente

No contiene writers ni resolucion de secretos.
"""

from __future__ import annotations

from collections import Counter
from typing import Dict, List, Optional

from api.admin_core_connections import (
    format_core_connection,
    get_core_connections_from_sql,
)
from core.rbac_helper_sql import es_superadmin
from core.server_registry import filter_servers_by_user_permissions, list_servers

from . import repository

_SECRET_KEYS = {
    "password",
    "password_encrypted",
    "password_decrypted",
    "api_key",
    "api_key_encrypted",
    "api_key_decrypted",
    "token",
    "secret",
}


def _id_key(value) -> str:
    return str(value or "").strip().lower()


def _bool(value, default: bool = False) -> bool:
    if value is None:
        return default
    return bool(value)


def _scope_sucursales(raw: Dict) -> List:
    value = raw.get("sucursales")
    if not isinstance(value, list):
        value = raw.get("config")
    return value if isinstance(value, list) else []


def _normalize_connection(raw: Dict, source_contract: str) -> Dict:
    """Proyecta una conexion a contrato seguro y comun sin valores de secretos."""
    connection_type = (
        raw.get("tipo_conexion")
        or raw.get("connection_type")
        or ("API_LOCAL" if source_contract == "api_connections" else "DATA_SOURCE")
    )
    name = raw.get("name") or raw.get("nombre") or ""
    api_key_marker = raw.get("api_key")

    result = {
        "id": str(raw.get("id") or ""),
        "name": name,
        "connection_type": connection_type,
        "system_type": raw.get("system_type") or raw.get("tipo"),
        "system_type_normalized": raw.get("system_type_normalized"),
        "active": _bool(raw.get("activo", raw.get("active")), False),
        "visible": _bool(
            raw.get("visible_en_listado", raw.get("visible_en_operaciones")),
            True,
        ),
        "editable": _bool(raw.get("es_editable_ui"), connection_type != "CORE"),
        "deletable": _bool(raw.get("es_eliminable_ui"), connection_type != "CORE"),
        "host": raw.get("host") or raw.get("servidor_padre"),
        "port": raw.get("port"),
        "database_name": raw.get("database_name") or raw.get("database") or raw.get("sucursal_destino"),
        "username": raw.get("username"),
        "api_url": raw.get("api_url") or raw.get("url"),
        "sistema_version_id": raw.get("sistema_version_id"),
        "scope": {
            "empresa_id": raw.get("EmpresaID") or raw.get("empresa_id") or raw.get("servidor_padre_id"),
            "unidad_negocio_ids": [],
            "sucursales": _scope_sucursales(raw),
            "source": "dbo.Servidores_Conexiones",
            "unit_mapping_status": "NOT_EXPLICIT_IN_CONNECTION_CONTRACT",
        },
        "secret_metadata": {
            "password_configured": _bool(raw.get("password_configured"), False),
            "api_key_configured": _bool(raw.get("api_key_configured"), api_key_marker == "***CONFIGURED***"),
        },
        "config_origin": raw.get("config_origin") or "EDARSAHUB_SQL",
        "source_contract": source_contract,
        "health": {
            "status": "UNKNOWN",
            "has_evidence": False,
            "source": "dbo.Servidores_ConexionEstado",
        },
    }

    # Defensa adicional: la proyeccion nunca puede arrastrar un valor secreto.
    for key in list(result):
        if key.lower() in _SECRET_KEYS:
            result.pop(key, None)
    return result


def _attach_health(connection: Dict, health: Optional[Dict]) -> None:
    if not health:
        return
    connection["health"] = {
        "status": health.get("EstadoConexion") or "UNKNOWN",
        "has_evidence": True,
        "last_check": health.get("UltimoCheck"),
        "last_test_utc": health.get("UltimaPruebaUTC"),
        "last_success_utc": health.get("UltimoExitoUTC"),
        "last_error_utc": health.get("UltimoErrorUTC"),
        "last_error_code": health.get("UltimoErrorCodigo"),
        "last_error_message": health.get("UltimoErrorMensaje"),
        "latency_ms": health.get("LatenciaMs"),
        "last_sync_utc": health.get("UltimoSyncUTC"),
        "last_successful_sync_utc": health.get("UltimoSyncExitosoUTC"),
        "updated_at_utc": health.get("FechaActualizacionUTC"),
        "source": "dbo.Servidores_ConexionEstado",
    }


async def list_connections(
    current_user: Dict,
    *,
    include_inactive: bool = True,
    connection_type: Optional[str] = None,
    system_type: Optional[str] = None,
    health_status: Optional[str] = None,
) -> List[Dict]:
    items: List[Dict] = []

    # DATA_SOURCE / SQL: resolver/registry canonico ya existente.
    servers = await list_servers(
        user=current_user,
        prefer_sql=True,
        filter_active=not include_inactive,
        filter_visible_listado=False,
        exclude_core=True,
        mask_secrets=True,
    )
    items.extend(_normalize_connection(server, "server_registry") for server in servers)

    # API_LOCAL: import lazy evita un ciclo de carga entre el paquete existente
    # api_connections y la fachada que se monta sobre su router raiz.
    from modules.api_connections.repository import list_api_connections

    api_rows = await list_api_connections(include_inactive=include_inactive)
    api_rows = filter_servers_by_user_permissions(api_rows, current_user)
    items.extend(_normalize_connection(row, "api_connections") for row in api_rows)

    # CORE conserva su regla existente: solo SUPERADMIN.
    if es_superadmin(current_user):
        core_rows = get_core_connections_from_sql()
        items.extend(
            _normalize_connection(format_core_connection(row), "admin_core_connections")
            for row in core_rows
        )

    # Evitar duplicados si algun adapter legado retorna el mismo UUID con distinta caja.
    deduped: Dict[str, Dict] = {}
    for item in items:
        key = _id_key(item.get("id"))
        if key:
            deduped[key] = item
    items = list(deduped.values())

    ids = [item["id"] for item in items]
    health_map = repository.get_latest_health_map(ids)
    enrichment = repository.get_connection_enrichment(ids)

    for item in items:
        lookup_key = _id_key(item.get("id"))
        extra = enrichment.get(lookup_key, {})
        if not item.get("sistema_version_id"):
            item["sistema_version_id"] = extra.get("sistema_version_id")
        item["scope"]["empresa_id"] = (
            extra.get("EmpresaID")
            or extra.get("empresa_id")
            or item["scope"].get("empresa_id")
        )
        _attach_health(item, health_map.get(lookup_key))

    if connection_type:
        wanted = connection_type.strip().upper()
        items = [item for item in items if str(item.get("connection_type") or "").upper() == wanted]
    if system_type:
        wanted = system_type.strip().upper()
        items = [item for item in items if str(item.get("system_type") or "").upper() == wanted]
    if health_status:
        wanted = health_status.strip().upper()
        items = [item for item in items if str(item.get("health", {}).get("status") or "").upper() == wanted]

    return sorted(items, key=lambda item: (str(item.get("connection_type") or ""), str(item.get("name") or "")))


async def get_connection_detail(current_user: Dict, connection_id: str) -> Optional[Dict]:
    wanted = _id_key(connection_id)
    items = await list_connections(current_user, include_inactive=True)
    return next((item for item in items if _id_key(item.get("id")) == wanted), None)


async def get_overview(current_user: Dict) -> Dict:
    connections = await list_connections(current_user, include_inactive=True)
    type_counts = Counter(str(item.get("connection_type") or "UNKNOWN") for item in connections)
    health_counts = Counter(str(item.get("health", {}).get("status") or "UNKNOWN") for item in connections)

    return {
        "connections": {
            "total": len(connections),
            "active": sum(1 for item in connections if item.get("active")),
            "with_health_evidence": sum(1 for item in connections if item.get("health", {}).get("has_evidence")),
            "by_type": dict(type_counts),
            "by_health": dict(health_counts),
        },
        "sync": repository.get_sync_summary(),
        "universal_infrastructure": repository.get_universal_infra_summary(),
        "communications": {
            "detail_endpoint": "/api/integrations-center/communications",
            "rbac_permission": "NOTIFICACIONES_VER",
            "provider_runtime": "backend/core/communications",
        },
    }


def get_catalogs() -> Dict:
    return repository.get_catalogs()


def get_communications_summary() -> Dict:
    return repository.get_communications_summary()
