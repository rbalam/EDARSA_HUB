"""Aplicacion de Cajas V1: prepara un expediente sin persistencia implicita.

El repositorio transaccional y los resolutores canonicos se inyectan cuando
la migracion SQL sea certificada. No se crea una base de datos alternativa.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from modules.finanzas.incidencias_caja_context import (
    AlcanceCaja, MotivoCajaCatalogo, RegistroCajaValidado, preparar_registro_caja,
)
from modules.finanzas.incidencias_caja_contracts import IncidenciaCajaCreate


class PersistenciaCajaNoDisponible(RuntimeError):
    pass


class RepositorioExpedientesCaja(Protocol):
    def crear_si_no_existe(self, registro: RegistroCajaValidado) -> str:
        """Transaccion atomica y UNIQUE por idempotencia_ambito.

        Misma solicitud debe devolver el mismo folio.
        Misma clave con contenido distinto debe rechazarse.
        No puede implementarse sin SQL validado.
        """
        ...


@dataclass(frozen=True)
class DependenciasCrearCaja:
    contextos_permitidos: frozenset[tuple[str, str, str]]
    motivos_vigentes: tuple[MotivoCajaCatalogo, ...]
    repositorio: RepositorioExpedientesCaja | None = None


def preparar_expediente_v1(
    solicitud: IncidenciaCajaCreate,
    alcance: AlcanceCaja,
    dependencias: DependenciasCrearCaja,
) -> RegistroCajaValidado:
    """Valida contexto y catalogos exclusivamente contra datos canonicos ya resueltos."""
    return preparar_registro_caja(
        solicitud=solicitud,
        alcance=alcance,
        contextos_permitidos=dependencias.contextos_permitidos,
        motivos_vigentes=dependencias.motivos_vigentes,
    )


def registrar_expediente_v1(
    solicitud: IncidenciaCajaCreate,
    alcance: AlcanceCaja,
    dependencias: DependenciasCrearCaja,
) -> str:
    """No declara exito sin repositorio SQL transaccional autorizado."""
    registro = preparar_expediente_v1(solicitud, alcance, dependencias)
    if dependencias.repositorio is None:
        raise PersistenciaCajaNoDisponible("CAJAS_SQL_PERSISTENCE_NOT_CERTIFIED")
    folio = dependencias.repositorio.crear_si_no_existe(registro)
    if not isinstance(folio, str) or not folio.strip():
        raise PersistenciaCajaNoDisponible("CAJAS_SQL_INSERT_NOT_CONFIRMED")
    return folio
