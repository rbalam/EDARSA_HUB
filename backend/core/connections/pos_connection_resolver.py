"""
Resolver seguro de metadata POS por unidad de negocio.

Este módulo:

- No abre conexiones SQL.
- No abre conexiones POS.
- No descifra secretos.
- No acepta ``server_id`` como entrada pública.
- Exige permiso explícito mediante un verificador inyectado.
- Exige contexto autorizado de unidad mediante un resolvedor inyectado.
- Devuelve exclusivamente metadata permitida.

Los adaptadores SQL, RBAC y de contexto se incorporarán por separado.
"""

from __future__ import annotations

import inspect
from typing import Any, Callable, Dict, Mapping


PERMISSION_CONNECTIONS_VIEW = "CONEXIONES_VER"

_FORBIDDEN_SECRET_KEYS = frozenset(
    {
        "password",
        "password_encrypted",
        "password_decrypted",
        "pwd",
        "api_key",
        "api_key_encrypted",
        "token",
        "secret",
        "credential",
        "credentials",
    }
)


class PosConnectionResolverError(RuntimeError):
    """Error base del resolvedor de metadata POS."""


class AuthenticationRequired(PosConnectionResolverError):
    """El usuario autenticado no contiene identidad suficiente."""


class ExplicitPermissionRequired(PosConnectionResolverError):
    """El usuario no posee el permiso explícito requerido."""


class ScopeDenied(PosConnectionResolverError):
    """La unidad solicitada no pertenece al alcance efectivo."""


class CanonicalMappingError(PosConnectionResolverError):
    """La relación canónica unidad-servidor es inexistente o inconsistente."""


class UnsafeMetadataError(PosConnectionResolverError):
    """El registro recibido contiene secretos o campos no permitidos."""


def _normalize_code(value: Any) -> str:
    return str(value or "").strip().upper()


def _first(record: Mapping[str, Any], *keys: str) -> Any:
    for key in keys:
        value = record.get(key)
        if value is not None and str(value).strip() != "":
            return value
    return None


async def _call(callback: Callable[..., Any], *args: Any) -> Any:
    result = callback(*args)

    if inspect.isawaitable(result):
        return await result

    return result


def _find_forbidden_keys(value: Any, prefix: str = "") -> list[str]:
    found: list[str] = []

    if isinstance(value, Mapping):
        for raw_key, nested_value in value.items():
            key = str(raw_key).strip()
            key_lower = key.lower()
            path = f"{prefix}.{key}" if prefix else key

            if key_lower in _FORBIDDEN_SECRET_KEYS:
                found.append(path)

            found.extend(_find_forbidden_keys(nested_value, path))

    elif isinstance(value, (list, tuple, set)):
        for index, nested_value in enumerate(value):
            path = f"{prefix}[{index}]"
            found.extend(_find_forbidden_keys(nested_value, path))

    return found


def _require_mapping(value: Any, error_message: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise CanonicalMappingError(error_message)

    return value


async def resolve_pos_connection_metadata(
    *,
    user: Mapping[str, Any],
    unidad_codigo: str,
    permission_checker: Callable[[Mapping[str, Any], str], Any],
    unidad_context_resolver: Callable[[Mapping[str, Any], str], Any],
    server_resolver: Callable[[str], Any],
) -> Dict[str, Any]:
    """
    Resuelve metadata segura de conexión a partir de una unidad autorizada.

    Las tres dependencias son obligatorias y deben ser adaptadores canónicos:

    - ``permission_checker``: permiso SQL explícito.
    - ``unidad_context_resolver``: contexto efectivo y alcance.
    - ``server_resolver``: relación unidad -> servidor canónico.

    Ninguna dependencia debe entregar valores de secretos.
    """

    if not isinstance(user, Mapping):
        raise AuthenticationRequired("Usuario autenticado requerido")

    email = str(user.get("email") or "").strip()

    if not email:
        raise AuthenticationRequired("Email del usuario autenticado requerido")

    requested_code = _normalize_code(unidad_codigo)

    if not requested_code:
        raise CanonicalMappingError("Código de unidad requerido")

    if not callable(permission_checker):
        raise ExplicitPermissionRequired(
            "Verificador de permiso explícito requerido"
        )

    if not callable(unidad_context_resolver):
        raise ScopeDenied("Resolvedor de alcance requerido")

    if not callable(server_resolver):
        raise CanonicalMappingError("Resolvedor canónico de servidor requerido")

    permission_granted = await _call(
        permission_checker,
        user,
        PERMISSION_CONNECTIONS_VIEW,
    )

    if permission_granted is not True:
        raise ExplicitPermissionRequired(
            f"Se requiere permiso explícito {PERMISSION_CONNECTIONS_VIEW}"
        )

    context_value = await _call(
        unidad_context_resolver,
        user,
        requested_code,
    )
    context = _require_mapping(
        context_value,
        "No se pudo resolver el contexto de unidad",
    )

    context_code = _normalize_code(
        _first(
            context,
            "unidad_negocio_codigo",
            "unidad_codigo",
            "codigo",
        )
    )

    if not context_code or context_code != requested_code:
        raise ScopeDenied("Unidad fuera del alcance efectivo del usuario")

    server_value = await _call(server_resolver, context_code)
    server = _require_mapping(
        server_value,
        "Unidad sin servidor canónico asociado",
    )

    forbidden_keys = _find_forbidden_keys(server)

    if forbidden_keys:
        raise UnsafeMetadataError(
            "El resolvedor entregó campos secretos: "
            + ", ".join(sorted(forbidden_keys))
        )

    server_unit_code = _normalize_code(
        _first(
            server,
            "unidad_negocio_codigo",
            "unidad_codigo",
            "codigo",
        )
    )

    if not server_unit_code or server_unit_code != context_code:
        raise CanonicalMappingError(
            "El servidor no corresponde a la unidad autorizada"
        )

    context_server_id = str(
        _first(context, "server_id", "servidor_id") or ""
    ).strip()
    server_id = str(
        _first(server, "server_id", "servidor_id", "id") or ""
    ).strip()

    if not server_id:
        raise CanonicalMappingError(
            "La unidad no tiene server_id canónico"
        )

    if context_server_id and context_server_id.lower() != server_id.lower():
        raise CanonicalMappingError(
            "El server_id del contexto no coincide con la relación canónica"
        )

    if server.get("unidad_activo") is False:
        raise CanonicalMappingError("Unidad de negocio inactiva")

    if server.get("servidor_activo") is False:
        raise CanonicalMappingError("Servidor asociado inactivo")

    return {
        "unidad_negocio_codigo": context_code,
        "unidad_negocio_nombre": _first(
            server,
            "unidad_negocio_nombre",
            "unidad_nombre",
        ),
        "unidad_negocio_pk": _first(
            server,
            "unidad_negocio_pk",
            "unidad_id",
        ),
        "server_id": server_id,
        "servidor_nombre": _first(
            server,
            "servidor_nombre",
            "server_name",
            "name",
        ),
        "system_type": _first(
            server,
            "servidor_system_type",
            "system_type",
        ),
        "host": server.get("host"),
        "port": server.get("port"),
        "database_name": _first(
            server,
            "database_name",
            "database",
        ),
        "username": server.get("username"),
        "empresa_id": server.get("empresa_id"),
        "visible_en_operaciones": bool(
            server.get("visible_en_operaciones")
        ),
        "config_origin": "EDARSAHUB_SQL_CANONICAL",
        "secrets_exposed": False,
        "pos_connection_executed": False,
    }
