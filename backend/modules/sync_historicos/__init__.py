"""
EDARSA HUB - Sync Históricos: Módulo de Sincronización
======================================================
FASE SYNC-1: Infraestructura base para sincronización de históricos a EDARSAHUB.

VENTANA OPERATIVA: 13:00 - 11:00 (cruza medianoche)
- Preparado para futuro módulo de Horarios de Operación por unidad

TABLAS DESTINO:
- Sync_Ventas_Historicas
- Sync_Ventas_PorHora
- Sync_Ventas_PorDiaSemana
- Sync_Control_Ejecuciones

REGLAS:
- NO usar date.today() para fecha_operacion
- NO usar datetime.now() sin zona horaria México
- NO guardar $0 si fuente falla
- UPSERT idempotente obligatorio
- Dry-run obligatorio antes de escritura

Autor: Sistema EDARSAHUB
Fecha: 2026-05-15
"""

from .models import (
    SyncVentaHistorica,
    SyncVentaPorHora,
    SyncVentaPorDiaSemana,
    SyncControlEjecucion,
    SyncRunConfig,
    SyncRunResult,
)
from .repository import SyncHistoricosRepository
from .service import SyncHistoricosService

__all__ = [
    'SyncVentaHistorica',
    'SyncVentaPorHora',
    'SyncVentaPorDiaSemana',
    'SyncControlEjecucion',
    'SyncRunConfig',
    'SyncRunResult',
    'SyncHistoricosRepository',
    'SyncHistoricosService',
]
