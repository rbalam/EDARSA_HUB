"""
EDARSA HUB - Compras Module Routes
==================================
Endpoints del módulo de compras.

FASE 4B DEL REFACTOR MODULAR (Diciembre 2025):

ESTRATEGIA DE MIGRACIÓN:
Los endpoints de compras tienen lógica de negocio compleja (~2000 líneas).
Para mantener estabilidad, se usa el siguiente enfoque:

1. ENDPOINTS MIGRADOS AL MÓDULO (lógica simple):
   - GET /compras/parametros/{server_id} (lectura de config)
   - POST /compras/parametros (escritura de config)

2. ENDPOINTS EN SERVER.PY (lógica compleja, ~1500 líneas):
   - Todos los demás endpoints de compras permanecen en server.py
   - Se migrarán gradualmente en fases posteriores

NOTA: El router del módulo se registra DESPUÉS de los endpoints de server.py
para que server.py tenga prioridad en los endpoints complejos.
"""

from typing import Dict
from fastapi import APIRouter, Depends, Query
from fastapi.security import HTTPAuthorizationCredentials

from core.security import security, verify_token
from modules.compras import service
from modules.compras.schemas import ParametrosCompra

# Router sin prefix - se agregará en server.py como /api
router = APIRouter(tags=["compras"])


# ============================================================================
# PARÁMETROS DE COMPRAS (Migrado - lógica simple)
# ============================================================================
# NOTA: Estos endpoints se desactivan porque server.py tiene la versión activa
# La migración completa se hará cuando se unifique la lógica.

# @router.get("/compras/parametros/{server_id}")
# async def obtener_parametros(...)

# @router.post("/compras/parametros")
# async def guardar_parametros(...)


# ============================================================================
# ENDPOINTS PENDIENTES DE MIGRACIÓN
# ============================================================================
# Los siguientes endpoints permanecen en server.py por su complejidad:
# 
# - GET /compras/inventarios-fisicos/{server_id}
# - GET /compras/pedidos-vigentes/{server_id}
# - GET /compras/detalle-pedido/{server_id}/{folio}
# - GET /compras/detalle-pedido-manual/{server_id}
# - GET /compras/detalle-movimientos/{server_id}
# - GET /compras/detalle-consumos/{server_id}
# - GET /compras/detalle-factura/{server_id}/{folio}
# - GET /compras/facturas-proveedor/{server_id}
# - GET /compras/dashboard/{server_id}
# - POST /compras/calculo-pedido (~420 líneas)
# - POST /compras/auditoria-operativa (~710 líneas)
# - POST /compras/analisis (~140 líneas)
# - POST /compras/productos-para-captura
# - POST /compras/detalle-movimientos
# - POST /compras/detalle-consumos
#
# Estos endpoints se migrarán gradualmente en fases posteriores,
# una vez que se establezca un patrón de migración seguro para
# lógica de negocio compleja.


__all__ = ['router']
