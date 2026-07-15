"""
Resolvedor canónico de UNIDAD para tableros (Operaciones / Inventarios).
========================================================================
P0 (2026-06): "puerta única" de resolución.

CONTRATO:
- El frontend envía SOLO la unidad canónica (unidad_codigo o id).
- El frontend NO resuelve server_id.
- Este módulo:
    1. Valida el permiso del usuario reutilizando el RBAC EXISTENTE
       (empresas_permitidas -> server_ids). No crea otro sistema de permisos.
    2. Resuelve server_id y sucursal_origen_id desde EDARSAHUB
       (dbo.Unidades_Negocio vía UnidadesService).
    3. NUNCA conecta a POS / no consulta en vivo.

COMPATIBILIDAD TEMPORAL:
- server_id directo queda DEPRECATED: se acepta pero se loguea un warning.

NOTA MPRO:
- Un mismo server_id puede alojar 2 unidades (ORIGEN y 130QRO).
- Para INVENTARIOS la desambiguación correcta es sucursal_origen_id (0021/0023).
- Para OPERATIVO (Workflow_Inventarios) la columna sucursal_id guarda el
  CÓDIGO o NOMBRE de la sucursal, por eso se exponen sucursal_labels
  (codigo + nombre) resueltos canónicamente desde la unidad (sin hardcode).
"""
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
import logging

from core.unidades_service import UnidadesService
from core.connections.edarsahub_readonly_repository import (
    get_unit_scope_metadata_readonly,
)
from core.connections.hrlectura_connection_factory import (
    build_hrlectura_connection_factory,
)
from core.rbac_sql.runtime import (
    can_access_unit_metadata_sql,
)

logger = logging.getLogger(__name__)

# Centinela: unidad sin acceso / no resuelta -> resultados vacíos (nunca expone datos)
NO_ACCESS_SENTINEL_SERVER_ID = "00000000-0000-0000-0000-000000000000"


@dataclass
class UnidadScope:
    """Resultado canónico de la resolución de una unidad para un request."""
    is_global: bool = False
    access_denied: bool = False
    legacy_server_id_used: bool = False
    unidad_codigo: Optional[str] = None
    unidad_nombre: Optional[str] = None
    unidad_pk: Optional[str] = None
    server_id: Optional[str] = None
    sucursal_origen_id: Optional[str] = None
    system_type: Optional[str] = None
    active_units_on_server: int = 0
    denial_reason: Optional[str] = None
    allowed_server_ids: List[str] = field(default_factory=list)
    effective_server_ids: List[str] = field(default_factory=list)
    sucursal_labels: Optional[List[str]] = None


def _find_unidad(valor: Optional[str]) -> Optional[Dict[str, Any]]:
    if not valor:
        return None
    return UnidadesService.get_by_codigo(valor) or UnidadesService.get_by_pk(valor)


def _find_unidad_by_server(server_id: Optional[str]) -> Optional[Dict[str, Any]]:
    """
    Compatibilidad legacy únicamente para servidores no ambiguos.

    Un servidor compartido nunca puede resolverse eligiendo la primera unidad.
    """
    if not server_id:
        return None

    sid = str(server_id).strip().lower()

    matches = [
        unit
        for unit in UnidadesService.get_all()
        if str(
            unit.get("server_id", "")
        ).strip().lower() == sid
    ]

    if len(matches) != 1:
        return None

    return matches[0]


def _shared_server(server_id: Optional[str]) -> bool:
    """True si el server_id aloja más de una unidad (caso MPRO)."""
    if not server_id:
        return False
    sid = str(server_id).strip().lower()
    n = sum(
        1 for u in UnidadesService.get_all()
        if str(u.get("server_id", "")).strip().lower() == sid
    )
    return n > 1


async def _get_allowed_server_ids(current_user: Optional[Dict[str, Any]]) -> List[str]:
    """
    RBAC reutilizado: server_ids permitidos del usuario.
    Lista vacía = sin restricción (ej. SuperAdministrador) => acceso a todo.
    """
    try:
        from core.security import get_user_empresas_permitidas, get_servers_for_empresas
        empresas = await get_user_empresas_permitidas(current_user or {})
        if not empresas:
            return []
        return await get_servers_for_empresas(empresas) or []
    except Exception as e:
        logger.warning("[UNIDAD_SCOPE] No se pudo resolver RBAC del usuario: %s", e)
        return []


def canonical_server_id(token: Optional[str]) -> Optional[str]:
    """
    Puerta única (regla de centralización) para resolver un token recibido del
    frontend al **server_id real del POS** registrado en EDARSAHUB.

    - Si el token es una unidad canónica (codigo o pk) → devuelve su server_id.
    - Si el token es un server_id legacy (deprecated) → lo devuelve sin cambios
      (compatibilidad limpia).
    - Si no resuelve a nada → devuelve el token original (que aguas abajo dará
      404 "Servidor no encontrado", comportamiento legacy preservado).

    NO conecta a POS ni consulta en vivo: solo lee el catálogo canónico
    (dbo.Unidades_Negocio vía UnidadesService).
    """
    if not token:
        return token
    u, matched_by = resolve_unidad_simple(token)
    if u and u.get("server_id"):
        if matched_by == 'unidad':
            logger.debug(
                "[CANONICAL-UNIDAD] token unidad '%s' → server %s (%s)",
                token, u.get("server_id"), u.get("codigo"),
            )
        else:
            logger.warning(
                "[DEPRECATED-PARAM] server_id directo recibido (deprecated). "
                "Migrar a 'unidad'. token=%s", token,
            )
        return u.get("server_id")
    return token


def resolve_unidad_simple(valor: Optional[str]):
    """
    Resolución PURA (sin RBAC) de un token a unidad.
    Útil para endpoints (ej. inventarios) donde el RBAC se aplica aguas abajo
    (validate_server_access_by_empresa).

    Retorna (unidad_dict | None, matched_by) con matched_by ∈ {'unidad','server','none'}:
      - 'unidad': el token es unidad canónica (codigo o pk) → se puede desambiguar sucursal.
      - 'server': el token es un server_id (deprecated) → NO desambigua sucursal.
    """
    if not valor:
        return None, 'none'
    u = _find_unidad(valor)
    if u:
        return u, 'unidad'
    u = _find_unidad_by_server(valor)
    if u:
        return u, 'server'
    return None, 'none'


async def resolve_unidad_scope(
    current_user: Optional[Dict[str, Any]],
    unidad: Optional[str] = None,
    server_id_legacy: Optional[str] = None,
) -> UnidadScope:
    """
    Resuelve la unidad canónica para un request.

    Prioridad:
      1. unidad (codigo o id)  -> contrato nuevo
      2. server_id_legacy      -> compatibilidad temporal (deprecated)
      3. ninguno               -> GLOBAL (todas las unidades permitidas del usuario)
    """
    allowed = await _get_allowed_server_ids(current_user)
    scope = UnidadScope(allowed_server_ids=allowed)

    # 1) GLOBAL
    if not unidad and not server_id_legacy:
        scope.is_global = True
        scope.effective_server_ids = list(allowed)  # [] => sin restricción / todas
        return scope

    # 2) Resolver unidad (prioridad a 'unidad')
    u = _find_unidad(unidad) if unidad else None

    if u is None and server_id_legacy:
        scope.legacy_server_id_used = True
        logger.warning(
            "[DEPRECATED-PARAM] Se recibió server_id directo (deprecated). "
            "Migrar a 'unidad'. user=%s server_id=%s",
            (current_user or {}).get("email"), server_id_legacy,
        )
        u = _find_unidad(server_id_legacy) or _find_unidad_by_server(server_id_legacy)

    if u is None:
        # No se pudo resolver -> sin datos
        scope.access_denied = True
        scope.effective_server_ids = [NO_ACCESS_SENTINEL_SERVER_ID]
        return scope

    server_id = u.get("server_id")
    scope.unidad_codigo = u.get("codigo")
    scope.unidad_nombre = u.get("nombre")
    scope.unidad_pk = u.get("unidad_negocio_pk")
    scope.server_id = server_id
    scope.sucursal_origen_id = u.get("sucursal_origen_id")
    scope.system_type = u.get("system_type")

    # 3) RBAC: usuario con restricción que no incluye este server -> denegar
    if allowed and server_id not in allowed:
        logger.warning(
            "[RBAC-DENEGADO] user=%s sin acceso a unidad=%s server=%s",
            (current_user or {}).get("email"), scope.unidad_codigo, server_id,
        )
        scope.access_denied = True
        scope.effective_server_ids = [NO_ACCESS_SENTINEL_SERVER_ID]
        return scope

    scope.effective_server_ids = [server_id]

    # 4) Desambiguación por sucursal SOLO si el server aloja >1 unidad (MPRO)
    #    y NO venimos por server_id legacy (que no puede distinguir sucursal).
    if not scope.legacy_server_id_used and _shared_server(server_id):
        labels = []
        if scope.unidad_codigo:
            labels.append(scope.unidad_codigo)
        if scope.unidad_nombre:
            labels.append(scope.unidad_nombre)
        scope.sucursal_labels = labels or None

    return scope

def _denied_scope(reason: str) -> UnidadScope:
    return UnidadScope(
        access_denied=True,
        denial_reason=reason,
        effective_server_ids=[
            NO_ACCESS_SENTINEL_SERVER_ID
        ],
    )


def _get_sql_usuario_id(
    current_user: Optional[Dict[str, Any]],
) -> Optional[int]:
    user = current_user or {}

    value = user.get("_sql_usuario_id")

    if value in (None, ""):
        value = user.get("UsuarioID")

    if isinstance(value, bool):
        return None

    try:
        usuario_id = int(value)
    except (TypeError, ValueError):
        return None

    if usuario_id <= 0:
        return None

    return usuario_id


async def resolve_authorized_unidad_scope(
    current_user: Optional[Dict[str, Any]],
    permission_code: str,
    unidad: str,
) -> UnidadScope:
    """
    Resuelve y autoriza una unidad mediante SQL canónico.

    El cliente únicamente puede proporcionar código o PK de unidad.
    server_id, sucursal, system_type y alcance se reconstruyen internamente.
    """
    usuario_id = _get_sql_usuario_id(
        current_user
    )

    if usuario_id is None:
        return _denied_scope(
            "sql_usuario_id_required"
        )

    normalized_permission = str(
        permission_code or ""
    ).strip()

    if not normalized_permission:
        return _denied_scope(
            "permission_code_required"
        )

    normalized_unit = str(
        unidad or ""
    ).strip()

    if not normalized_unit:
        return _denied_scope(
            "canonical_unit_required"
        )

    try:
        connection_factory = (
            build_hrlectura_connection_factory()
        )

        metadata = get_unit_scope_metadata_readonly(
            unidad=normalized_unit,
            connection_factory=connection_factory,
        )

        allowed = can_access_unit_metadata_sql(
            usuario_id,
            normalized_permission,
            metadata,
        )

        if not allowed:
            return _denied_scope(
                "unit_scope_denied"
            )

        scope = UnidadScope(
            unidad_codigo=metadata.get(
                "unidad_negocio_codigo"
            ),
            unidad_nombre=metadata.get(
                "unidad_negocio_nombre"
            ),
            unidad_pk=metadata.get(
                "unidad_negocio_pk"
            ),
            server_id=metadata.get("server_id"),
            sucursal_origen_id=metadata.get(
                "sucursal_origen_id"
            ),
            system_type=metadata.get(
                "system_type"
            ),
            active_units_on_server=int(
                metadata.get(
                    "active_units_on_server"
                )
            ),
            effective_server_ids=[
                metadata.get("server_id")
            ],
        )

        if scope.active_units_on_server > 1:
            labels = []

            if scope.unidad_codigo:
                labels.append(scope.unidad_codigo)

            if scope.unidad_nombre:
                labels.append(scope.unidad_nombre)

            scope.sucursal_labels = (
                labels or None
            )

        return scope
    except Exception as exc:
        logger.warning(
            "[UNIDAD_SCOPE] autorización SQL "
            "falló cerrada: %s",
            exc,
        )

        return _denied_scope(
            "authorization_error"
        )
