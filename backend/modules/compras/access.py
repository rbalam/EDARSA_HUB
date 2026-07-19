"""Acceso canonico para el modulo Compras.

Centraliza el permiso funcional RBAC (Usuario_PermisosRolModulo) para que los
endpoints de /compras/* dejen de depender unicamente de un JWT valido y
verifiquen tambien que el usuario tiene el permiso COMPRAS_FACT_* requerido.

El alcance por servidor/unidad de negocio para Compras ya se resuelve con
`validate_server_access_by_empresa` / `_compras_resolve_scope` en
backend/server.py -- este modulo NO duplica esa logica, solo agrega la capa
de permiso funcional que faltaba (Maxima 7 RBAC SQL-native).
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Iterable, Mapping, Optional

from fastapi import HTTPException, status

from core.rbac_sql.service import RBACSQLService


logger = logging.getLogger(__name__)

COMPRAS_VER = "COMPRAS_FACT_VER"
COMPRAS_CREAR = "COMPRAS_FACT_CREAR"
COMPRAS_EJECUTAR = "COMPRAS_FACT_EJECUTAR"
COMPRAS_CONFIGURAR = "COMPRAS_FACT_CONFIGURAR"
COMPRAS_GESTIONAR = "COMPRAS_FACT_GESTIONAR"


def _normalize(value: Any) -> str:
    return str(value or "").strip()


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


def require_compras_permission(
    current_user: Mapping[str, Any],
    permission_code: str = COMPRAS_VER,
) -> Dict[str, Any]:
    """Exige permiso funcional de Compras desde RBAC SQL canonico."""
    if not isinstance(current_user, Mapping):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario autenticado invalido.",
        )

    usuario_id = _get_sql_usuario_id(current_user)
    if usuario_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No existe identidad SQL canonica para evaluar Compras.",
        )

    normalized = _normalize(permission_code).upper()
    if not normalized:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permiso de compras requerido.",
        )

    try:
        permission = RBACSQLService.get_permission_scope_by_code(
            usuario_id,
            normalized,
        )
    except Exception as exc:
        logger.error("[COMPRAS_RBAC] Error resolviendo permiso: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "No fue posible resolver permisos de compras. "
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


def require_any_compras_permission(
    current_user: Mapping[str, Any],
    permission_codes: Iterable[str],
) -> Dict[str, Any]:
    """Exige al menos uno de los permisos indicados, sin recurrir a roles."""
    last_error: Optional[HTTPException] = None

    for code in permission_codes:
        try:
            return require_compras_permission(current_user, code)
        except HTTPException as exc:
            last_error = exc
            if exc.status_code >= 500:
                raise

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail=(
            "El usuario no tiene un permiso de compras "
            "configurado en RBAC."
        ),
    ) from last_error
