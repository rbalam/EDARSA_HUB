"""
EDARSA HUB - Módulo Costos y Márgenes
=====================================
FASE 1C-3C: Endpoints NO-LIVE para análisis de costos y márgenes.

Características:
- Lee EXCLUSIVAMENTE de tablas Sync_Productos* en EDARSAHUB SQL
- NO realiza conexiones live a sistemas externos
- NO usa MongoDB
- Respeta RBAC y permisos por empresa/unidad

Source Types Permitidos:
- EDARSAHUB_SQL
- STALE_EDARSAHUB_SQL
- SIN_DATOS_EDARSAHUB

Autor: Sistema EDARSA HUB
Fecha: 24 Mayo 2026
"""

from modules.costos_margenes.routes import router

__all__ = ['router']
