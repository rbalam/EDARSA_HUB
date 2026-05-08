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

__all__ = [
    'list_api_connections',
    'get_api_connection', 
    'create_api_connection',
    'update_api_connection',
    'delete_api_connection',
    'sync_all_to_mongo_cache',
    'test_api_connection_health',
    'get_api_connections_for_adapters',
    'api_connections_router'
]
