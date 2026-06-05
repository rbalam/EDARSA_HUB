"""
Módulo de Configuración - EDARSA HUB
====================================

Gestiona configuraciones maestras del sistema:
- Asignaciones de responsables para workflows
"""

from .routes.config_asignaciones_routes import router as config_asignaciones_router

__all__ = ['config_asignaciones_router']
