"""RBAC y alcance canonico para Fase 2 Operativo."""

from __future__ import annotations

import logging
from collections import Counter
from typing import Any, Iterable, List, Mapping, Optional, Sequence, Tuple

from fastapi import HTTPException, status

from core.auth.sql_user_identity import resolve_sql_usuario_id
from core.corporate_filters.service import CorporateFilterService
from core.rbac_sql.service import RBACSQLService
from core.unidades_service import UnidadesService


logger = logging.getLogger(__name__)

AUDITORIA_VER = "AUDITORIA_VER"
AUTOMATIZACIONES_VER = "AUTOMATIZACIONES_VER"
AUDITORIAS_PROGRAMAR = "AUDITORIAS_PROGRAMAR"
AUDITORIAS_GESTIONAR = "AUDITORIAS_GESTIONAR"

AUDITORIA_READ_PERMISSIONS = (AUDITORIA_VER, AUTOMATIZACIONES_VER)


def _normalize(value: Any) -> str:
    return str(value or "").strip()


def _normalize_key(value: Any) -> str:
    return _normalize(value).casefold()


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
        server_id = _normalize_key(row.get("ServidorID") or row.get("server_id"))
        branch = _normalize_key(
            row.get("SucursalCodigo")
            or row.get("sucursal_codigo")
            or row.get("sucursal_origen_id")
        )
        if server_id and branch:
            pairs.add((server_id, branch))
    return pairs


def resolve_unidad_pk(valor: Any) -> Optional[str]:
    """Resuelve PK canonica desde PK, codigo, nombre, sucursal o server legacy."""
    resolved = CorporateFilterService.resolver_unidad(valor).get("pk")
    if resolved:
        return str(resolved)

    needle = _normalize_key(valor)
    if not needle:
        return None

    for unit in UnidadesService.get_all():
        candidates = (
            unit.get("unidad_negocio_pk"),
            unit.get("id"),
            unit.get("codigo"),
            unit.get("unidad_negocio_codigo"),
            unit.get("nombre"),
            unit.get("unidad_negocio_nombre"),
            unit.get("sucursal_origen_id"),
            unit.get("server_id"),
        )
        if needle in {_normalize_key(candidate) for candidate in candidates}:
            return _normalize(unit.get("unidad_negocio_pk") or unit.get("id"))

    return None


def get_unidad_metadata(unidad_ref: Any) -> Mapping[str, Any]:
    unidad_pk = resolve_unidad_pk(unidad_ref)
    if not unidad_pk:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unidad de negocio canonica invalida o no encontrada.",
        )

    unit = UnidadesService.get_by_pk(unidad_pk)
    if not unit:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unidad de negocio canonica invalida o no encontrada.",
        )

    return unit


def _resolve_permission_scopes(
    usuario_id: int,
    permission_codes: Sequence[str],
) -> List[Mapping[str, Any]]:
    scopes: list[Mapping[str, Any]] = []
    for code in permission_codes:
        normalized = _normalize(code).upper()
        if not normalized:
            continue
        try:
            scope = RBACSQLService.get_permission_scope_by_code(
                usuario_id,
                normalized,
            )
        except Exception as exc:
            logger.error("[OPERATIVO_RBAC] Error resolviendo permiso %s: %s", normalized, exc)
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=(
                    "No fue posible resolver permisos operativos. "
                    "Acceso cerrado preventivamente."
                ),
            ) from exc

        if scope:
            scopes.append(scope)

    return scopes


def get_allowed_unidad_pks(
    current_user: Mapping[str, Any],
    permission_codes: Sequence[str] = AUDITORIA_READ_PERMISSIONS,
) -> Optional[List[str]]:
    """
    Devuelve alcance efectivo por unidad.

    None = permiso global sin restriccion de sucursal.
    [] = permiso existe, pero no hay unidades alcanzables.
    """
    usuario_id = resolve_sql_usuario_id(dict(current_user or {}))
    if usuario_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No existe identidad SQL canonica para evaluar Operaciones.",
        )

    scopes = _resolve_permission_scopes(usuario_id, permission_codes)
    if not scopes:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "El usuario no tiene permiso funcional para "
                "Automatizaciones."
            ),
        )

    if any(not bool(scope.get("restriccion_sucursal")) for scope in scopes):
        return None

    try:
        context = RBACSQLService.build_context(usuario_id)
        units = UnidadesService.get_all()
    except Exception as exc:
        logger.error("[OPERATIVO_RBAC] Error resolviendo alcance: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "No fue posible resolver el alcance operativo. "
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
        unit_pk = _normalize(unit.get("unidad_negocio_pk") or unit.get("id"))
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


def resolve_operativo_unit_filter(
    current_user: Mapping[str, Any],
    unidad_ref: Optional[str] = None,
    permission_codes: Sequence[str] = AUDITORIA_READ_PERMISSIONS,
) -> Tuple[Optional[str], Optional[List[str]]]:
    """Resuelve selector de cliente a PK canonica y alcance efectivo."""
    allowed_units = get_allowed_unidad_pks(current_user, permission_codes)

    selector = _normalize(unidad_ref)
    if not selector or selector.casefold() in {"todas", "todos", "all"}:
        return None, allowed_units

    unidad_pk = resolve_unidad_pk(selector)
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
