from core.unidades_service import UnidadesService
from core.corporate_filters.service import CorporateFilterService
"""
EDARSA HUB - Lecturas desde EDARSA HUB (MongoDB)
================================================

PROPÓSITO:
Centralizar las lecturas de KPIs y datos consolidados desde EDARSA HUB.
Implementar la regla "EDARSA HUB FIRST" para períodos cerrados.

COLECCIONES MONGODB:
- kpis_comercial: KPIs consolidados por (server_id, empresa_id, sucursal_id, fecha)
- dashboard_cache: Caché temporal de datos comerciales
- server_status: Estado de conexión de servidores

PRINCIPIO "EDARSA HUB FIRST":
Para períodos cerrados (días anteriores), los tableros deben:
1. Intentar leer de kpis_comercial primero
2. Solo si no hay datos, hacer fallback a SQL LIVE
3. Guardar el resultado en HUB para futuras lecturas

FUNCIONES A IMPLEMENTAR (Bloques siguientes):
- get_kpis_from_hub: Obtener KPIs para un período desde HUB
- get_kpis_periodo_hub: Obtener KPIs de un rango de fechas
- check_kpis_exist_hub: Verificar si existen KPIs sin traer datos

ESQUEMA kpis_comercial:
{
    "server_id": str,
    "empresa_id": str,
    "sucursal_id": str,
    "fecha": "YYYY-MM-DD",
    "kpis": {
        "ventas": float,
        "pax": int,
        "cheques": int,
        "ticket_promedio": float,
        ...
    },
    "estado_periodo": "ABIERTO" | "CERRADO" | "RECONCILIADO",
    "source": "SYNC-S" | "SYNC-N" | "MANUAL" | "RECONCILIACION",
    "versions": {
        "created_at": datetime,
        "updated_at": datetime,
        "sync_count": int
    }
}

CONSUMIDORES PREVISTOS:
- Tablero Ejecutivo (períodos cerrados)
- Dashboard Comercial (períodos cerrados)
- Reportes históricos
- Comparativos año anterior

Fecha creación: 2026-04-23
Estado: BLOQUE_1 - Estructura preparada, sin implementación
"""

from typing import Dict, Optional, List
from datetime import datetime, date

# =============================================================================
# CONSTANTES
# =============================================================================

# Colección principal de KPIs
COLLECTION_KPIS = "kpis_comercial"

# Colección de caché
COLLECTION_CACHE = "dashboard_cache"

# Colección de estado de servidores
COLLECTION_STATUS = "server_status"

# Estados de período
ESTADO_ABIERTO = "ABIERTO"
ESTADO_CERRADO = "CERRADO"
ESTADO_RECONCILIADO = "RECONCILIADO"

# Fuentes de datos
SOURCE_SYNC_S = "SYNC-S"
SOURCE_SYNC_N = "SYNC-N"
SOURCE_MANUAL = "MANUAL"
SOURCE_RECONCILIACION = "RECONCILIACION"

# Nombre del módulo para logging
MODULE_NAME = "COMERCIAL_QUERIES_HUB"


# =============================================================================
# FUNCIONES BASE - PENDIENTES DE IMPLEMENTACIÓN
# =============================================================================

# BLOQUE 4+: Implementar esta función
# async def get_kpis_from_hub(
#     server_id: str,
#     fecha: str,  # YYYY-MM-DD
#     sucursal_id: Optional[str] = None
# ) -> Optional[Dict]:
#     """
#     Obtiene KPIs de EDARSA HUB para una fecha específica.
#     
#     Args:
#         server_id: ID del servidor
#         fecha: Fecha en formato YYYY-MM-DD
#         sucursal_id: ID de sucursal (opcional, None = consolidado)
#         
#     Returns:
#         Dict con KPIs o None si no existen
#         
#     CONSUMIDORES:
#     - tablero_ejecutivo_service.py
#     - dashboard_comercial_service.py
#     """
#     pass


# BLOQUE 4+: Implementar esta función
# async def get_kpis_periodo_hub(
#     server_id: str,
#     fecha_ini: str,
#     fecha_fin: str,
#     sucursal_id: Optional[str] = None
# ) -> List[Dict]:
#     """
#     Obtiene KPIs de EDARSA HUB para un rango de fechas.
#     
#     Args:
#         server_id: ID del servidor
#         fecha_ini: Fecha inicio YYYY-MM-DD
#         fecha_fin: Fecha fin YYYY-MM-DD
#         sucursal_id: ID de sucursal (opcional)
#         
#     Returns:
#         Lista de documentos KPI ordenados por fecha
#     """
#     pass


# BLOQUE 4+: Implementar esta función
# async def check_kpis_exist_hub(
#     server_id: str,
#     fecha_ini: str,
#     fecha_fin: str
# ) -> Dict[str, bool]:
#     """
#     Verifica qué fechas tienen KPIs en HUB (sin traer datos).
#     Útil para decidir si hacer fallback a LIVE.
#     
#     Returns:
#         Dict {fecha: bool} indicando existencia
#     """
#     pass


# =============================================================================
# UTILIDADES INTERNAS
# =============================================================================

def _build_kpi_filter(
    server_id: str,
    fecha: Optional[str] = None,
    fecha_ini: Optional[str] = None,
    fecha_fin: Optional[str] = None,
    sucursal_id: Optional[str] = None
) -> Dict:
    """
    Construye filtro MongoDB para consultas de KPIs.
    
    Args:
        server_id: ID del servidor (requerido)
        fecha: Fecha exacta (exclusivo con fecha_ini/fecha_fin)
        fecha_ini: Fecha inicio de rango
        fecha_fin: Fecha fin de rango
        sucursal_id: ID de sucursal (opcional)
        
    Returns:
        Dict filtro para MongoDB find()
    """
    filtro = {"server_id": server_id}
    
    if fecha:
        filtro["fecha"] = fecha
    elif fecha_ini and fecha_fin:
        filtro["fecha"] = {"$gte": fecha_ini, "$lte": fecha_fin}
    
    if sucursal_id:
        filtro["sucursal_id"] = sucursal_id
    
    return filtro


def _calculate_source_status(kpi_doc: Optional[Dict]) -> str:
    """
    Determina el source_status basado en el documento KPI.
    
    Returns:
        "HUB" si hay datos de HUB
        "NO_DATA" si no hay documento
    """
    if kpi_doc and kpi_doc.get("kpis"):
        return "HUB"
    return "NO_DATA"
