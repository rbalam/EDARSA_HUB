"""Integracion de lectura entre autorizaciones SQL canonicas y seguimiento Cajas.

No crea autorizaciones ni las resuelve: solo proyecta una fila ya filtrada por
RBAC/RLS y vinculada a un expediente previamente autenticado.
"""
from __future__ import annotations

from dataclasses import replace
from typing import Any, Mapping

from modules.finanzas.incidencias_caja_authorization_adapter import (
    proyectar_autorizacion_caja,
)
from modules.finanzas.incidencias_caja_workflow import (
    SituacionIncidenciaCaja,
    SeguimientoIncidenciaCaja,
    evaluar_seguimiento_v1,
)


def evaluar_seguimiento_con_autorizacion_sql(
    *,
    expediente: SituacionIncidenciaCaja,
    fila_autorizacion: Mapping[str, Any] | None,
    entidad_nombre: str,
    entidad_id: str,
) -> SeguimientoIncidenciaCaja:
    """Requiere evidencia SQL del motor de autorizaciones, nunca un booleano del cliente.

    No permite inventar NO_REQUERIDA al faltar una fila. Los estados AUTORIZADA
    y APROBADA se homologan solo a partir de evidencia SQL real.
    """
    if not expediente.permiso_edarsahub or not expediente.alcance_valido:
        return evaluar_seguimiento_v1(replace(expediente, autorizacion_ref=None))
    autorizacion = proyectar_autorizacion_caja(
        fila_autorizacion,
        entidad_nombre_esperada=entidad_nombre,
        entidad_id_esperada=entidad_id,
    )
    return evaluar_seguimiento_v1(
        replace(
            expediente,
            autorizacion=autorizacion.estado,
            autorizacion_ref=autorizacion.autorizacion_id,
        )
    )
