from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

import requests

from core.server_registry import get_decrypted_credentials, get_server_by_id
from .read_only_sql import validate_readonly_sql


class ApiLocalSyncError(RuntimeError):
    """Fallo controlado del transport API_LOCAL de sincronizacion."""


DEFAULT_API_LOCAL_TIMEOUT_SECONDS = 30


@dataclass(frozen=True)
class ApiLocalSyncConfig:
    server_id: str
    server_name: str
    api_url: str
    api_key: str = field(repr=False)
    system_type: str = ""
    config_origin: str = ""


async def resolve_api_local_sync_config(server_id: str) -> ApiLocalSyncConfig:
    """Resuelve una conexion API_LOCAL exclusivamente desde EDARSAHUB SQL.

    El helper no abre conexiones remotas. Solo resuelve configuracion canonica
    y secretos internos mediante server_registry.
    """
    server = await get_server_by_id(
        str(server_id),
        prefer_sql=True,
        allow_mongo_fallback=False,
        mask_secrets=False,
    )
    if not server:
        raise ApiLocalSyncError("API_LOCAL_SERVER_NOT_FOUND")

    if str(server.get("tipo_conexion") or "").strip().upper() != "API_LOCAL":
        raise ApiLocalSyncError("API_LOCAL_CONNECTION_TYPE_REQUIRED")

    if not bool(server.get("active")):
        raise ApiLocalSyncError("API_LOCAL_SERVER_INACTIVE")

    credentials = get_decrypted_credentials(server)
    api_url = str(credentials.get("api_url") or "").strip()
    if not api_url:
        raise ApiLocalSyncError("API_LOCAL_URL_REQUIRED")

    api_key = str(credentials.get("api_key") or "").strip()
    if not api_key:
        raise ApiLocalSyncError("API_LOCAL_KEY_REQUIRED")

    return ApiLocalSyncConfig(
        server_id=str(server.get("id") or server_id),
        server_name=str(server.get("name") or ""),
        api_url=api_url,
        api_key=api_key,
        system_type=str(server.get("system_type") or ""),
        config_origin=str(server.get("config_origin") or ""),
    )


def execute_api_local_readonly(
    config: ApiLocalSyncConfig,
    sql: str,
    *,
    timeout_seconds: int = DEFAULT_API_LOCAL_TIMEOUT_SECONDS,
    request_get=requests.get,
) -> List[Dict[str, Any]]:
    """Ejecuta una unica consulta READ_ONLY mediante el contrato API_LOCAL.

    Esta funcion esta destinada exclusivamente a jobs de sincronizacion.
    No persiste resultados y no controla transacciones EDARSAHUB.
    """
    query = validate_readonly_sql(sql)

    try:
        timeout = int(timeout_seconds)
    except (TypeError, ValueError) as exc:
        raise ValueError("API_LOCAL_TIMEOUT_INVALID") from exc
    if timeout <= 0 or timeout > 300:
        raise ValueError("API_LOCAL_TIMEOUT_INVALID")

    try:
        response = request_get(
            config.api_url,
            params={"sql": query},
            headers={"X-API-Key": config.api_key},
            timeout=timeout,
        )
    except requests.exceptions.Timeout as exc:
        raise ApiLocalSyncError("API_LOCAL_TIMEOUT") from exc
    except requests.exceptions.RequestException as exc:
        raise ApiLocalSyncError("API_LOCAL_OFFLINE") from exc

    if int(getattr(response, "status_code", 0) or 0) != 200:
        raise ApiLocalSyncError(
            f"API_LOCAL_HTTP_{int(getattr(response, 'status_code', 0) or 0)}"
        )

    try:
        payload = response.json()
    except ValueError as exc:
        raise ApiLocalSyncError("API_LOCAL_INVALID_JSON") from exc

    if isinstance(payload, dict):
        rows = payload.get("data", [])
    elif isinstance(payload, list):
        rows = payload
    else:
        raise ApiLocalSyncError("API_LOCAL_INVALID_PAYLOAD")

    if rows is None:
        rows = []
    if not isinstance(rows, list):
        raise ApiLocalSyncError("API_LOCAL_INVALID_DATA")

    if not all(isinstance(row, dict) for row in rows):
        raise ApiLocalSyncError("API_LOCAL_ROWS_MUST_BE_OBJECTS")

    return rows
