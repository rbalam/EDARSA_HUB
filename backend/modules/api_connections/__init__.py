from core.unidades_service import UnidadesService
from core.corporate_filters.service import CorporateFilterService
"""
Módulo de Conexiones API Locales
================================
Gestiona conexiones a APIs locales (MPRO, etc.) para obtener ventas del día
en tiempo real desde servidores locales.

ARQUITECTURA:
- Fuente primaria: EDARSAHUB SQL (Servidores_Conexiones con tipo_conexion='API_LOCAL')
- Caché/Fallback: MongoDB (colección api_connections)
- Sincronización bidireccional entre ambas fuentes

FUNCIONALIDAD:
- CRUD completo de conexiones API
- Prueba de conexión a APIs
- Sincronización automática con MongoDB
"""

from .repository import (
    list_api_connections,
    get_api_connection,
    create_api_connection,
    update_api_connection,
    delete_api_connection,
    sync_all_to_mongo_cache,
    test_api_connection_health,
    get_api_connections_for_adapters
)

from .routes import router as api_connections_router
from .universal_test_routes import router as api_universal_test_router
from .universal_test_routes import set_verify_token as set_api_uqt_verify_token

# GATE 5B: la fachada administrativa se monta sobre este APIRouter sin prefijo,
# que ya es registrado por backend/server.py dentro de /api. Esto evita tocar
# el bootstrap monolítico y conserva /api/integrations-center/*.
from modules.integrations_center import router as integrations_center_router
api_universal_test_router.include_router(integrations_center_router)

__all__ = [
    'list_api_connections',
    'get_api_connection', 
    'create_api_connection',
    'update_api_connection',
    'delete_api_connection',
    'sync_all_to_mongo_cache',
    'test_api_connection_health',
    'get_api_connections_for_adapters',
    'api_connections_router',
    'api_universal_test_router',
    'set_api_uqt_verify_token',
    'integrations_center_router'
]
