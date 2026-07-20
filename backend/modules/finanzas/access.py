"""Acceso canonico para el modulo Financiero.

Centraliza permiso funcional y alcance por unidad de negocio para evitar que
cada submodulo implemente RBAC, roles o filtros propios.
"""

from __future__ import annotations

import logging
from collections import Counter
from typing import Any, Dict, Iterable, List, Mapping, Optional, Tuple

from fastapi import HTTPException, status

from core.rbac_sql.service import RBACSQLService
from core.unidades_service import UnidadesService


logger = logging.getLogger(__name__)

FINANZAS_VER = "FINANZAS_VER"
FINANZAS_EDITAR = "FINANZAS_EDITAR"
FINANZAS_ADMINISTRAR = "FINANZAS_ADMINISTRAR"


def _normalize(value: Any) -> str:
    return str(value or "").strip()


def _normalize_key(value: Any) -> str:
    return _normalize(value).casefold()


def _get_sql_usuario_id(current_user: Mapping[str, Any]) -> Optional[int]:
    value = (
        current_user.get("_sql_usuario_id")
        or current_user.get("UsuarioID")
        or current_user.get("usuario_id")
    )

    if isinstance(value, bool):
        return None

    try:
        usuario_id = int(value)
    except (TypeError, ValueError):
        return None

    return usuario_id if usuario_id > 0 else None


def require_finanzas_permission(
    current_user: Mapping[str, Any],
    permission_code: str = FINANZAS_VER,
) -> Dict[str, Any]:
    """Exige permiso funcional desde RBAC SQL canonico."""
    if not isinstance(current_user, Mapping):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario autenticado invalido.",
        )

    usuario_id = _get_sql_usuario_id(current_user)
    if usuario_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No existe identidad SQL canonica para evaluar Finanzas.",
        )

    normalized = _normalize(permission_code).upper()
    if not normalized:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permiso financiero requerido.",
        )

    try:
        permission = RBACSQLService.get_permission_scope_by_code(
            usuario_id,
            normalized,
        )
    except Exception as exc:
        logger.error("[FINANZAS_RBAC] Error resolviendo permiso: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "No fue posible resolver permisos financieros. "
                "Acceso cerrado preventivamente."
            ),
        ) from exc

    if not permission:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"El usuario no tiene el permiso requerido: {normalized}.",
        )

    return {
        "permission_code": normalized,
        "permitido": True,
        "restriccion_sucursal": bool(
            permission.get("restriccion_sucursal")
        ),
        "usuario_id": usuario_id,
    }


def require_any_finanzas_permission(
    current_user: Mapping[str, Any],
    permission_codes: Iterable[str],
) -> Dict[str, Any]:
    """Exige al menos uno de los permisos indicados, sin recurrir a roles."""
    last_error: Optional[HTTPException] = None

    for code in permission_codes:
        try:
            return require_finanzas_permission(current_user, code)
        except HTTPException as exc:
            last_error = exc
            if exc.status_code >= 500:
                raise

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail=(
            "El usuario no tiene un permiso financiero de escritura "
            "configurado en RBAC."
        ),
    ) from last_error


def _context_values(rows: Iterable[Mapping[str, Any]], *keys: str) -> set[str]:
    values: set[str] = set()
    for row in rows or []:
        for key in keys:
            value = row.get(key)
            if value not in (None, ""):
                values.add(_normalize_key(value))
    return values


def _branch_pairs(rows: Iterable[Mapping[str, Any]]) -> set[Tuple[str, str]]:
    pairs: set[Tuple[str, str]] = set()
    for row in rows or []:
        server_id = _normalize_key(row.get("ServidorID"))
        branch = _normalize_key(row.get("SucursalCodigo"))
        if server_id and branch:
            pairs.add((server_id, branch))
    return pairs


def get_finanzas_allowed_unidad_pks(
    current_user: Mapping[str, Any],
    permission_code: str = FINANZAS_VER,
) -> Optional[List[str]]:
    """
    Devuelve alcance efectivo por unidad.

    None = permiso global sin restriccion de sucursal.
    [] = permiso funcional existe, pero no hay unidades alcanzables.
    """
    permission = require_finanzas_permission(
        current_user,
        permission_code,
    )

    if not permission["restriccion_sucursal"]:
        return None

    usuario_id = permission["usuario_id"]

    try:
        context = RBACSQLService.build_context(usuario_id)
        units = UnidadesService.get_all()
    except Exception as exc:
        logger.error("[FINANZAS_RBAC] Error resolviendo alcance: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "No fue posible resolver el alcance financiero. "
                "Acceso cerrado preventivamente."
            ),
        ) from exc

    explicit_units = _context_values(
        context.get("unidades_negocio") or [],
        "UnidadNegocioID",
        "unidad_negocio_pk",
        "unidad_negocio_id",
    )
    server_ids = _context_values(
        context.get("servidores") or [],
        "ServidorID",
        "server_id",
    )
    branches = _branch_pairs(context.get("sucursales") or [])
    active_units_by_server = Counter(
        _normalize_key(unit.get("server_id"))
        for unit in units
        if _normalize_key(unit.get("server_id"))
    )

    allowed: list[str] = []
    for unit in units:
        unit_pk = _normalize(unit.get("unidad_negocio_pk"))
        if not unit_pk:
            continue

        server_id = _normalize_key(unit.get("server_id"))
        branch = _normalize_key(unit.get("sucursal_origen_id"))
        unit_key = _normalize_key(unit_pk)

        if unit_key in explicit_units:
            allowed.append(unit_pk)
            continue

        if server_id and branch and (server_id, branch) in branches:
            allowed.append(unit_pk)
            continue

        if (
            server_id
            and server_id in server_ids
            and active_units_by_server.get(server_id, 0) == 1
        ):
            allowed.append(unit_pk)

    return sorted(set(allowed))


def resolve_finanzas_unit_filter(
    current_user: Mapping[str, Any],
    unidad_ref: Optional[str] = None,
    permission_code: str = FINANZAS_VER,
) -> Tuple[Optional[str], Optional[List[str]]]:
    """
    Resuelve un selector recibido del cliente a PK canonica y alcance efectivo.
    """
    allowed_units = get_finanzas_allowed_unidad_pks(
        current_user,
        permission_code,
    )

    selector = _normalize(unidad_ref)
    if not selector or selector.casefold() in {"todas", "todos", "all"}:
        return None, allowed_units

    unidad_pk = UnidadesService.resolver_pk(selector)
    if not unidad_pk:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unidad de negocio canonica invalida o no encontrada.",
        )

    if allowed_units is not None and unidad_pk not in allowed_units:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene alcance para la unidad de negocio solicitada.",
        )

    return unidad_pk, None


def filter_unidades_for_finanzas(
    unidades: Iterable[Mapping[str, Any]],
    current_user: Mapping[str, Any],
    permission_code: str = FINANZAS_VER,
) -> List[Mapping[str, Any]]:
    allowed_units = get_finanzas_allowed_unidad_pks(
        current_user,
        permission_code,
    )

    if allowed_units is None:
        return list(unidades or [])

    allowed_set = set(allowed_units)
    return [
        unit
        for unit in (unidades or [])
        if str(unit.get("unidad_negocio_pk") or "").strip() in allowed_set
    ]
