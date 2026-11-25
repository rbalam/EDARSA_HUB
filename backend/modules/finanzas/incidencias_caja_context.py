"""Validacion de contexto y catalogos para preparar registros de Cajas V1.

Esta capa recibe datos previamente resueltos por servicios canonicos.
No consulta SQL, no crea catalogos ni realiza operaciones externas.
La unicidad de idempotencia DEBE imponerse transaccionalmente en SQL.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from typing import Iterable

from modules.finanzas.incidencias_caja_contracts import IncidenciaCajaCreate


class CajasContextError(ValueError):
    """Contexto no autorizado, catalogo no validado o entrada incompatible."""


@dataclass(frozen=True)
class AlcanceCaja:
    empresa_id: str
    unidad_id: str
    sucursal_id: str
    usuario_id: int
    sistema_origen: str
    server_id: str


@dataclass(frozen=True)
class MotivoCajaCatalogo:
    codigo_canonico: str
    codigo_origen: str | None
    sistema_origen: str | None
    empresa_id: str | None
    unidad_id: str | None
    sucursal_id: str | None
    activo: bool = True


@dataclass(frozen=True)
class RegistroCajaValidado:
    alcance: AlcanceCaja
    motivo_codigo_canonico: str
    motivo_codigo_origen: str | None
    idempotencia_ambito: str
    solicitud: IncidenciaCajaCreate


def preparar_registro_caja(
    *,
    solicitud: IncidenciaCajaCreate,
    alcance: AlcanceCaja,
    contextos_permitidos: Iterable[tuple[str, str, str]],
    motivos_vigentes: Iterable[MotivoCajaCatalogo],
) -> RegistroCajaValidado:
    """Rechaza entradas ambiguas o fuera de alcance, sin efectos secundarios.

    contextos_permitidos debe provenir del resolver de relaciones
    empresa/unidad/sucursal y RBAC/RLS de EDARSAHUB, nunca del navegador.
    motivos_vigentes debe provenir del Maestro de Catalogos homologado.
    """
    if not (
        alcance.empresa_id and alcance.unidad_id and alcance.sucursal_id
        and alcance.sistema_origen and alcance.server_id and alcance.usuario_id > 0
    ):
        raise CajasContextError("CONTEXTO_CANONICO_INCOMPLETO")
    if (
        alcance.empresa_id, alcance.unidad_id, alcance.sucursal_id
    ) not in frozenset(contextos_permitidos):
        raise CajasContextError("EMPRESA_UNIDAD_SUCURSAL_NO_AUTORIZADA")

    matches = []
    for motivo in motivos_vigentes:
        if not motivo.activo:
            continue
        if motivo.codigo_canonico != solicitud.motivo_codigo:
            continue
        if motivo.empresa_id is not None and motivo.empresa_id != alcance.empresa_id:
            continue
        if motivo.unidad_id is not None and motivo.unidad_id != alcance.unidad_id:
            continue
        if motivo.sucursal_id is not None and motivo.sucursal_id != alcance.sucursal_id:
            continue
        if motivo.sistema_origen is not None and motivo.sistema_origen != alcance.sistema_origen:
            continue
        matches.append(motivo)
    if not matches:
        raise CajasContextError("MOTIVO_NO_DISPONIBLE_EN_CONTEXTO")
    # Prioridad a catalogos de mayor especificidad; sin desempates arbitrarios.
    specificity = lambda m: sum(
        v is not None for v in
        (m.empresa_id, m.unidad_id, m.sucursal_id, m.sistema_origen)
    )
    max_specificity = max(specificity(m) for m in matches)
    selected = [m for m in matches if specificity(m) == max_specificity]
    if len(selected) != 1:
        raise CajasContextError("MOTIVO_HOMOLOGACION_AMBIGUA")

    # Namespace estable: NO sustituye una constraint UNIQUE en SQL.
    namespace = "\x1f".join((
        alcance.empresa_id,
        alcance.unidad_id,
        alcance.sucursal_id,
        alcance.sistema_origen,
        alcance.server_id,
        str(alcance.usuario_id),
        solicitud.solicitud_idempotencia,
    ))
    return RegistroCajaValidado(
        alcance=alcance,
        motivo_codigo_canonico=selected[0].codigo_canonico,
        motivo_codigo_origen=selected[0].codigo_origen,
        idempotencia_ambito=sha256(namespace.encode("utf-8")).hexdigest(),
        solicitud=solicitud,
    )
