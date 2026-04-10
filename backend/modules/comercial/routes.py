"""
EDARSA HUB - Comercial Module Routes
====================================
Endpoints del módulo comercial.

FASE 5B DEL REFACTOR MODULAR (Abril 2026):

ESTADO ACTUAL:
- ✅ Adapters (APIs locales MPRO) migrados a adapters.py
- ⏸️ Endpoints pendientes de migrar (permanecen en server.py)

COMPONENTES MIGRADOS:
1. adapters.py:
   - APIS_MPRO_LOCALES (configuración)
   - query_api_mpro_local()
   - obtener_ventas_dia_api_local()
   - sumar_ventas_api_local_a_sucursal()

ENDPOINTS PENDIENTES (10 total en server.py):
- GET /comercial/dashboard/{server_id} - Dashboard principal
- GET /comercial/ticket-perfecto/{server_id} - Análisis de ticket perfecto
- GET /comercial/metas/{server_id} - Metas por sucursal
- GET /comercial/ventas-tiempo/{server_id} - Ventas por tiempo
- GET /comercial/mesas/{server_id} - Estado de mesas
- GET /comercial/detalle-movimientos/{server_id} - Detalle de movimientos
- GET /comercial/reporte-pax/{server_id} - Reporte PAX (más complejo)
- GET /comercial/tablero-ejecutivo - Tablero ejecutivo consolidado (CRÍTICO)
- GET /comercial/sucursales/{server_id} - Lista de sucursales
- GET /comercial/precios-constantes/{server_id} - Precios constantes

HELPERS PENDIENTES DE MIGRAR (en server.py):
- get_kpis_softrestaurant()
- get_kpis_mpro_por_sucursal()
- save_server_connection_status()
- is_server_recently_offline()
- get_cached_kpis() / save_kpis_cache()

NOTA: Los endpoints permanecen en server.py hasta que se migren
los helpers que usan la conexión global a MongoDB.
"""

from fastapi import APIRouter

# Router - los endpoints serán migrados incrementalmente
router = APIRouter(tags=["comercial"])


__all__ = ['router']
