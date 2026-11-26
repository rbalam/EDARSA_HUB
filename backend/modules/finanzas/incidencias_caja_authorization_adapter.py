"""Proyeccion segura del motor canonico Usuario_Autorizaciones para Cajas V1.

Un consumidor con RBAC/RLS previamente comprobados provee una fila SQL
resuelta por la vinculacion polimorfica EntidadNombre + EntidadID.
No ejecuta SQL ni modifica autorizaciones, tareas o POS.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from modules.finanzas.incidencias_caja_workflow import EstadoAutorizacion


class AutorizacionCajaNoVerificable(PermissionError):
    pass


@dataclass(frozen=True)
class EstadoAutorizacionCajaCanonica:
    autorizacion_id: str
    estado: EstadoAutorizacion
    entidad_nombre: str
    entidad_id: str


_ESTADOS_CANONICOS = {
    "PENDIENTE": EstadoAutorizacion.PENDIENTE,
    "EN_PROCESO": EstadoAutorizacion.EN_PROCESO,
    "AUTORIZADA": EstadoAutorizacion.APROBADA,
    "RECHAZADA": EstadoAutorizacion.RECHAZADA,
}


def proyectar_autorizacion_caja(
    fila: Mapping[str, Any] | None,
    *,
    entidad_nombre_esperada: str,
    entidad_id_esperada: str,
) -> EstadoAutorizacionCajaCanonica:
    """Solo acepta lectura autentica ligada al expediente requerido.

    No confunde ausencia de fila con NO_REQUERIDA y nunca interpreta
    niveles intermedios como autorizacion completa.
    """
    if not isinstance(fila, Mapping):
        raise AutorizacionCajaNoVerificable("AUTORIZACION_SQL_NO_DISPONIBLE")
    if not entidad_nombre_esperada.strip() or not entidad_id_esperada.strip():
        raise AutorizacionCajaNoVerificable("REFERENCIA_EXPEDIENTE_INCOMPLETA")
    raw_id = fila.get("AutorizacionID")
    if isinstance(raw_id, bool):
        raise AutorizacionCajaNoVerificable("AUTORIZACION_ID_INVALIDA")
    try:
        id_numerico = int(raw_id)
    except (TypeError, ValueError, OverflowError):
        raise AutorizacionCajaNoVerificable("AUTORIZACION_ID_INVALIDA") from None
    if id_numerico <= 0 or str(raw_id).strip() != str(id_numerico):
        raise AutorizacionCajaNoVerificable("AUTORIZACION_ID_INVALIDA")
    nombre = fila.get("EntidadNombre")
    entidad_id = fila.get("EntidadID")
    if nombre != entidad_nombre_esperada or entidad_id != entidad_id_esperada:
        raise AutorizacionCajaNoVerificable("AUTORIZACION_ENTIDAD_NO_COINCIDE")
    if fila.get("Activo") is not True and fila.get("Activo") != 1:
        raise AutorizacionCajaNoVerificable("AUTORIZACION_NO_ACTIVA")
    raw_estado = fila.get("EstatusAutorizacion")
    estado = _ESTADOS_CANONICOS.get(raw_estado)
    if estado is None:
        raise AutorizacionCajaNoVerificable("AUTORIZACION_ESTADO_NO_RECONOCIDO")
    return EstadoAutorizacionCajaCanonica(
        autorizacion_id=str(id_numerico),
        estado=estado,
        entidad_nombre=nombre,
        entidad_id=entidad_id,
    )
