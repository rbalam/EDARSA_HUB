"""Puente de consultas read-only para el Asistente IA de EDARSA HUB.

El modelo nunca recibe acceso directo a SQL ni a URLs arbitrarias. El catálogo
se deriva del OpenAPI vivo de la misma aplicación y solo permite operaciones
GET internas que pasan una política fail-closed. La autorización efectiva la
vuelven a evaluar los endpoints canónicos del backend en cada llamada.
"""

from __future__ import annotations

import re
from typing import Any, Dict, Iterable, List, Mapping
from urllib.parse import quote

import httpx

MAX_SYSTEM_CALLS = 3
MAX_CATALOG_FOR_PROMPT = 180
MAX_LIST_ITEMS = 50
MAX_DICT_ITEMS = 100
MAX_STRING_CHARS = 4000
MAX_SANITIZE_DEPTH = 7

_SENSITIVE_KEY_MARKERS = (
    "password",
    "passwd",
    "token",
    "api_key",
    "apikey",
    "secret",
    "credential",
    "authorization",
    "cookie",
    "connection_string",
    "connectionstring",
    "private_key",
    "privatekey",
    "access_key",
    "accesskey",
    "refresh_token",
    "refreshtoken",
)

_BLOCKED_PATH_MARKERS = (
    "auth",
    "login",
    "logout",
    "token",
    "secret",
    "credential",
    "config",
    "debug",
    "openapi",
    "docs",
    "sql",
    "query",
    "admin",
    "internal",
    "worker",
)

_MUTATING_PATH_MARKERS = (
    "execute",
    "ejecutar",
    "run",
    "start",
    "stop",
    "restart",
    "delete",
    "create",
    "update",
    "wake",
    "trigger",
    "apply",
    "approve",
    "reject",
    "cancel",
    "import",
    "upload",
    "sync-now",
    "resync",
)


def _normalize_marker(value: Any) -> str:
    return re.sub(r"[^a-z0-9_]+", "_", str(value or "").strip().lower())


def _path_allowed(path: str) -> bool:
    normalized_path = str(path or "").strip()
    if not normalized_path.startswith("/api/"):
        return False

    segments = [
        _normalize_marker(segment)
        for segment in normalized_path.split("/")
        if segment and not segment.startswith("{")
    ]

    if "ia" in segments:
        return False

    for segment in segments:
        if any(marker in segment for marker in _BLOCKED_PATH_MARKERS):
            return False
        if any(marker in segment for marker in _MUTATING_PATH_MARKERS):
            return False

    return True


def _parameter_rows(path_item: Mapping[str, Any], operation: Mapping[str, Any]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    seen = set()

    for raw in list(path_item.get("parameters") or []) + list(operation.get("parameters") or []):
        if not isinstance(raw, Mapping):
            continue

        location = str(raw.get("in") or "").strip().lower()
        name = str(raw.get("name") or "").strip()

        if location not in {"path", "query"} or not name:
            continue

        key = (location, name)
        if key in seen:
            continue
        seen.add(key)

        schema = raw.get("schema") if isinstance(raw.get("schema"), Mapping) else {}
        rows.append(
            {
                "name": name,
                "in": location,
                "required": bool(raw.get("required")),
                "type": str(schema.get("type") or "string"),
                "description": str(raw.get("description") or "")[:240],
            }
        )

    return rows


def build_readonly_catalog(app: Any) -> List[Dict[str, Any]]:
    """Construye catálogo de operaciones GET internas aptas para la IA."""
    schema = app.openapi()
    paths = schema.get("paths") if isinstance(schema, Mapping) else {}
    if not isinstance(paths, Mapping):
        return []

    catalog: List[Dict[str, Any]] = []

    for path, raw_path_item in paths.items():
        if not isinstance(raw_path_item, Mapping) or not _path_allowed(path):
            continue

        operation = raw_path_item.get("get")
        if not isinstance(operation, Mapping):
            continue

        operation_id = str(operation.get("operationId") or "").strip()
        if not operation_id:
            continue

        catalog.append(
            {
                "operation_id": operation_id,
                "path": str(path),
                "summary": str(
                    operation.get("summary")
                    or operation.get("description")
                    or ""
                )[:300],
                "parameters": _parameter_rows(raw_path_item, operation),
            }
        )

    return sorted(catalog, key=lambda row: (row["path"], row["operation_id"]))


def catalog_for_prompt(
    catalog: Iterable[Mapping[str, Any]],
    user_message: str,
    limit: int = MAX_CATALOG_FOR_PROMPT,
) -> List[Dict[str, Any]]:
    """Reduce el catálogo priorizando operaciones relacionadas con la solicitud."""
    words = {
        token
        for token in re.findall(r"[a-z0-9_áéíóúñ]{3,}", str(user_message or "").lower())
    }

    ranked = []
    for row in catalog:
        compact = {
            "operation_id": str(row.get("operation_id") or ""),
            "path": str(row.get("path") or ""),
            "summary": str(row.get("summary") or ""),
            "parameters": list(row.get("parameters") or []),
        }
        haystack = " ".join(
            (
                compact["operation_id"],
                compact["path"],
                compact["summary"],
            )
        ).lower()
        score = sum(1 for word in words if word in haystack)
        ranked.append((score, compact["path"], compact))

    ranked.sort(key=lambda item: (-item[0], item[1]))
    return [item[2] for item in ranked[: max(1, int(limit))]]


def _is_sensitive_key(key: Any) -> bool:
    normalized = _normalize_marker(key)
    return any(marker in normalized for marker in _SENSITIVE_KEY_MARKERS)


def sanitize_payload(value: Any, depth: int = 0) -> Any:
    """Elimina secretos y limita el tamaño del contexto entregado al modelo."""
    if depth >= MAX_SANITIZE_DEPTH:
        return "[TRUNCADO]"

    if value is None or isinstance(value, (bool, int, float)):
        return value

    if isinstance(value, str):
        if len(value) > MAX_STRING_CHARS:
            return value[:MAX_STRING_CHARS] + "...[TRUNCADO]"
        return value

    if isinstance(value, Mapping):
        result: Dict[str, Any] = {}
        for index, (key, item) in enumerate(value.items()):
            if index >= MAX_DICT_ITEMS:
                result["_truncado"] = True
                break
            text_key = str(key)
            if _is_sensitive_key(text_key):
                result[text_key] = "***REDACTED***"
            else:
                result[text_key] = sanitize_payload(item, depth + 1)
        return result

    if isinstance(value, (list, tuple, set)):
        rows = list(value)
        result = [
            sanitize_payload(item, depth + 1)
            for item in rows[:MAX_LIST_ITEMS]
        ]
        if len(rows) > MAX_LIST_ITEMS:
            result.append("[LISTA_TRUNCADA]")
        return result

    return sanitize_payload(str(value), depth + 1)


def _safe_param_value(value: Any, allow_list: bool = False) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if allow_list and isinstance(value, list):
        if all(item is None or isinstance(item, (str, int, float, bool)) for item in value):
            return value[:50]
    raise ValueError("PARAMETRO_NO_SEGURO")


def _operation_map(catalog: Iterable[Mapping[str, Any]]) -> Dict[str, Mapping[str, Any]]:
    result: Dict[str, Mapping[str, Any]] = {}
    for row in catalog:
        operation_id = str(row.get("operation_id") or "").strip()
        if operation_id:
            result[operation_id] = row
    return result


async def execute_catalog_operation(
    app: Any,
    catalog: Iterable[Mapping[str, Any]],
    request_spec: Mapping[str, Any],
    *,
    authorization: str | None = None,
    cookie: str | None = None,
) -> Dict[str, Any]:
    """Ejecuta una operación previamente catalogada contra la misma app ASGI."""
    operation_id = str(request_spec.get("operation_id") or "").strip()
    operation = _operation_map(catalog).get(operation_id)

    if not operation:
        return {
            "operation_id": operation_id,
            "ok": False,
            "error": "OPERACION_NO_AUTORIZADA",
        }

    path_template = str(operation.get("path") or "")
    if not _path_allowed(path_template):
        return {
            "operation_id": operation_id,
            "ok": False,
            "error": "RUTA_NO_AUTORIZADA",
        }

    declared_path = {
        str(row.get("name"))
        for row in operation.get("parameters") or []
        if row.get("in") == "path"
    }
    declared_query = {
        str(row.get("name"))
        for row in operation.get("parameters") or []
        if row.get("in") == "query"
    }

    raw_path_params = request_spec.get("path_params") or {}
    raw_query_params = request_spec.get("query_params") or {}

    if not isinstance(raw_path_params, Mapping) or not isinstance(raw_query_params, Mapping):
        return {
            "operation_id": operation_id,
            "ok": False,
            "error": "PARAMETROS_INVALIDOS",
        }

    if set(map(str, raw_path_params.keys())) - declared_path:
        return {
            "operation_id": operation_id,
            "ok": False,
            "error": "PARAMETRO_PATH_NO_DECLARADO",
        }

    if set(map(str, raw_query_params.keys())) - declared_query:
        return {
            "operation_id": operation_id,
            "ok": False,
            "error": "PARAMETRO_QUERY_NO_DECLARADO",
        }

    rendered_path = path_template
    try:
        for name in declared_path:
            placeholder = "{" + name + "}"
            if placeholder not in rendered_path:
                continue
            if name not in raw_path_params:
                return {
                    "operation_id": operation_id,
                    "ok": False,
                    "error": "PARAMETRO_PATH_REQUERIDO",
                }
            value = _safe_param_value(raw_path_params[name])
            rendered_path = rendered_path.replace(
                placeholder,
                quote(str(value), safe=""),
            )

        query_params = {
            str(key): _safe_param_value(value, allow_list=True)
            for key, value in raw_query_params.items()
        }
    except ValueError:
        return {
            "operation_id": operation_id,
            "ok": False,
            "error": "PARAMETROS_INVALIDOS",
        }

    if "{" in rendered_path or "}" in rendered_path:
        return {
            "operation_id": operation_id,
            "ok": False,
            "error": "PARAMETRO_PATH_REQUERIDO",
        }

    headers: Dict[str, str] = {}
    if authorization:
        headers["Authorization"] = authorization
    if cookie:
        headers["Cookie"] = cookie

    transport = httpx.ASGITransport(app=app)
    try:
        async with httpx.AsyncClient(
            transport=transport,
            base_url="http://edarsahub.internal",
            timeout=20.0,
        ) as client:
            response = await client.get(
                rendered_path,
                params=query_params,
                headers=headers,
            )
    except httpx.TimeoutException:
        return {
            "operation_id": operation_id,
            "ok": False,
            "error": "TIMEOUT",
        }
    except httpx.RequestError:
        return {
            "operation_id": operation_id,
            "ok": False,
            "error": "SERVICIO_INTERNO_NO_DISPONIBLE",
        }

    content_type = str(response.headers.get("content-type") or "").lower()
    if "json" not in content_type:
        return {
            "operation_id": operation_id,
            "path": rendered_path,
            "status_code": response.status_code,
            "ok": False,
            "error": "RESPUESTA_NO_JSON",
        }

    try:
        payload = response.json()
    except ValueError:
        return {
            "operation_id": operation_id,
            "path": rendered_path,
            "status_code": response.status_code,
            "ok": False,
            "error": "RESPUESTA_JSON_INVALIDA",
        }

    return {
        "operation_id": operation_id,
        "path": rendered_path,
        "status_code": response.status_code,
        "ok": bool(response.is_success),
        "data": sanitize_payload(payload),
    }


async def execute_planned_queries(
    app: Any,
    catalog: Iterable[Mapping[str, Any]],
    planned: Iterable[Mapping[str, Any]],
    *,
    authorization: str | None = None,
    cookie: str | None = None,
) -> List[Dict[str, Any]]:
    results: List[Dict[str, Any]] = []
    for request_spec in list(planned)[:MAX_SYSTEM_CALLS]:
        if not isinstance(request_spec, Mapping):
            continue
        results.append(
            await execute_catalog_operation(
                app,
                catalog,
                request_spec,
                authorization=authorization,
                cookie=cookie,
            )
        )
    return results
