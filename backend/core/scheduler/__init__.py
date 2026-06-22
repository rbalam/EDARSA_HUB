"""
EDARSA HUB - Core Scheduler Module
==================================
Subfase 2B.5.2 - Scheduler automático empresarial.

Sistema de jobs periódicos para:
- Procesamiento de motor SLA
- Despacho de notificaciones
- Alertas y escalamientos automáticos

Arquitectura:
- APScheduler AsyncIOScheduler
- Locks de ejecución mediante capa de compatibilidad SQL-only/legacy
- Logging completo de ejecuciones
- Endpoints de administración
"""

from .scheduler_manager import (
    SchedulerManager,
    get_scheduler_manager,
    start_scheduler,
    stop_scheduler,
)
from .config import SchedulerConfig, JobConfig
from .routes import router as scheduler_router, init_scheduler_routes

__all__ = [
    'SchedulerManager',
    'get_scheduler_manager',
    'start_scheduler',
    'stop_scheduler',
    'SchedulerConfig',
    'JobConfig',
    'scheduler_router',
    'init_scheduler_routes',
]
