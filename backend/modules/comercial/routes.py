"""
EDARSA HUB - Comercial Module Routes
====================================
Endpoints del módulo comercial.

FASE 5 DEL REFACTOR MODULAR (Diciembre 2025):

ESTRATEGIA DE MIGRACIÓN:
Los endpoints de comercial tienen lógica de negocio MUY compleja (~3300 líneas)
incluyendo:
- Homologación multi-origen (MPRO, SoftRestaurant, APIs locales)
- Tablero ejecutivo consolidado
- Integración con APIs locales en tiempo real
- Lógica de fallback cuando APIs no responden

Para mantener estabilidad, se usa el siguiente enfoque:

1. ESTRUCTURA DEL MÓDULO LISTA:
   - schemas.py: Modelos definidos
   - repository.py: Queries base
   - service.py: Funciones auxiliares

2. ENDPOINTS EN SERVER.PY (lógica compleja, ~3300 líneas):
   - GET /comercial/dashboard/{server_id} (826 líneas)
   - GET /comercial/ticket-perfecto/{server_id} (121 líneas)
   - GET /comercial/metas/{server_id} (100 líneas)
   - GET /comercial/ventas-tiempo/{server_id} (178 líneas)
   - GET /comercial/mesas/{server_id} (228 líneas)
   - GET /comercial/detalle-movimientos/{server_id} (211 líneas)
   - GET /comercial/reporte-pax/{server_id} (1163 líneas)
   - GET /comercial/tablero-ejecutivo (300 líneas) - CRÍTICO
   - GET /comercial/sucursales/{server_id} (61 líneas)
   - GET /comercial/precios-constantes/{server_id} (~100 líneas)

3. DEPENDENCIAS GLOBALES EN SERVER.PY:
   - APIS_MPRO_LOCALES (configuración hardcodeada)
   - query_api_mpro_local() (consulta APIs locales)
   - obtener_ventas_dia_api_local() (ventas en tiempo real)
   - sumar_ventas_api_local_a_sucursal() (homologación)

NOTA: Este router está vacío porque los endpoints permanecen en server.py.
La migración completa se realizará cuando:
1. Se muevan las funciones de APIs locales a core/
2. Se creen tests exhaustivos para los endpoints
3. Se valide la homologación multi-origen
"""

from fastapi import APIRouter

# Router vacío - los endpoints están en server.py
router = APIRouter(tags=["comercial"])


# ============================================================================
# ENDPOINTS PENDIENTES DE MIGRACIÓN (EN SERVER.PY)
# ============================================================================
#
# Los siguientes endpoints permanecen en server.py por su complejidad:
#
# @api_router.get("/comercial/dashboard/{server_id}")
#   - 826 líneas
#   - Homologación MPRO + SoftRestaurant + APIs locales
#   - Usa sumar_ventas_api_local_a_sucursal()
#
# @api_router.get("/comercial/tablero-ejecutivo")
#   - 300 líneas
#   - Consolidación de todas las unidades
#   - Modo "Ventas del Día" con APIs locales
#   - ENDPOINT CRÍTICO para operaciones diarias
#
# @api_router.get("/comercial/reporte-pax/{server_id}")
#   - 1163 líneas (incluye helpers)
#   - Lógica compleja de análisis de PAX
#
# Y otros 7 endpoints más simples pero con dependencias
#
# ============================================================================


__all__ = ['router']
