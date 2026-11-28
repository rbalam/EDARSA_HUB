"""Acceso a Cajas V1: resuelve RBAC SQL y exige alcance canonico.

NO obtiene contexto del cuerpo HTTP ni concede permisos de Tesoreria.
Un consumidor posterior inyecta relaciones empresa-unidad-sucursal ya
resueltas por el catalogo corporativo y conectores autorizados.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Iterable, Mapping

from core.rbac_sql.service import RBACSQLService
from modules.finanzas.incidencias_caja_context import AlcanceCaja

CAJAS_INCIDENCIAS_CREAR = "CAJAS_INCIDENCIAS_CREAR"


class AccesoCajaDenegado(PermissionError):
    pass


@dataclass(frozen=True)
class AccesoCajaValidado:
    alcance: AlcanceCaja
    relaciones_permitidas: frozenset[tuple[str, str, str]]
    permiso_codigo: str


def validar_acceso_creacion_caja(
    *,
    usuario_autenticado: Mapping[str, Any],
    alcance_resuelto: AlcanceCaja,
    obtener_relaciones_canonicas: Callable[[int], Iterable[tuple[str, str, str]]],
) -> AccesoCajaValidado:
    """Solo prepara acceso si RBAC y RLS son verificables.

    CAJAS_INCIDENCIAS_CREAR debe existir en el registro canonico de permisos
    antes de habilitar una ruta. Ausencia => DENEGADO.
    """
    raw_id = (
        usuario_autenticado.get("_sql_usuario_id")
        or usuario_autenticado.get("UsuarioID")
        or usuario_autenticado.get("usuario_id")
    )
    if isinstance(raw_id, bool):
        raise AccesoCajaDenegado("IDENTIDAD_SQL_INVALIDA")
    try:
        usuario_id = int(raw_id)
    except (TypeError, ValueError, OverflowError):
        raise AccesoCajaDenegado("IDENTIDAD_SQL_INVALIDA") from None
    if usuario_id <= 0 or alcance_resuelto.usuario_id != usuario_id:
        raise AccesoCajaDenegado("IDENTIDAD_SQL_NO_COINCIDE")
    try:
        permiso = RBACSQLService.get_permission_scope_by_code(
            usuario_id, CAJAS_INCIDENCIAS_CREAR
        )
    except Exception:
        raise AccesoCajaDenegado("RBAC_SQL_NO_VERIFICABLE") from None
    if (
        not isinstance(permiso, Mapping)
        or permiso.get("permitido") not in (True, 1)
    ):
        raise AccesoCajaDenegado("CAJAS_INCIDENCIAS_CREAR_DENEGADO")
    try:
        relaciones = frozenset(obtener_relaciones_canonicas(usuario_id))
    except Exception:
        raise AccesoCajaDenegado("RELACIONES_CANONICAS_NO_VERIFICABLES") from None
    if not relaciones or (
        alcance_resuelto.empresa_id,
        alcance_resuelto.unidad_id,
        alcance_resuelto.sucursal_id,
    ) not in relaciones:
        raise AccesoCajaDenegado("ALCANCE_EMPRESA_UNIDAD_SUCURSAL_DENEGADO")
    return AccesoCajaValidado(
        alcance=alcance_resuelto,
        relaciones_permitidas=relaciones,
        permiso_codigo=CAJAS_INCIDENCIAS_CREAR,
    )
