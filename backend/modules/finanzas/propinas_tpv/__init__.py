# Módulo de Control y Cuadre de Comisión sobre Propinas TPV
# FASE 1 MVP - Solo SoftRestaurant
# 
# CAB Aprobado: 2026-04-14
# Arquitectura SQL: 2026-04-15 (ARQUITECTURA_PROPINAS_TPV_v3.md)
# Documentos: /app/docs/CAB_MODULO_PROPINAS_TPV.md
#
# ARQUITECTURA:
# - SQL Server EDARSA HUB = Persistencia oficial (propinas_tpv_*)
# - MongoDB = Solo cache de lectura rápida (propinas_cache_*)
#
# ALCANCE FASE 1:
# - La Estelar (SoftRestaurant)
# - Cienfuegos (SoftRestaurant)
# - 130 Mérida (SoftRestaurant)
#
# FUERA DE ALCANCE:
# - MPRO (pendiente para fase posterior)
#
# IMPORTANTE - AISLAMIENTO:
# - NO interfiere con /api/finanzas/tesoreria/*
# - NO modifica el tab de Cuadre Z
# - NO toca colecciones existentes de MongoDB

from .routes_sql import router_sql
from .routes import router
from .service_sql import PropinasTPVSQLService
from .service import PropinasTPVService
from .sql_repository import PropinasTPVSQLRepository
from .cache_manager import PropinasCacheManager
