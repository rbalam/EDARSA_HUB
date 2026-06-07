from core.unidades_service import UnidadesService
from core.corporate_filters.service import CorporateFilterService
"""
Utilidades de Base de Datos para Fase 2A
CAB-003 | EDARSA HUB

Proporciona acceso a la conexión de MongoDB para el módulo operativo.
"""
import os

# Conexión síncrona a MongoDB para los repositories
_client = None
_db = None


def get_database():
    """
    Obtiene la conexión a la base de datos MongoDB.
    Usa conexión síncrona para compatibilidad con los repositories.
    
    Returns:
        Database MongoDB
    """
    global _client, _db
    
    if _db is None:
        mongo_url = None  # P2-07: MongoDB eliminado
        db_name = os.environ.get('DB_NAME', 'test_database')
        
        _client = None  # P2-07: MongoDB eliminado
        # Capa 3: Mongo eliminado. Los repositorios del módulo leen de EDARSAHUB
        # SQL e ignoran este 'db'. Antes hacía None[db_name] => 'NoneType' object
        # is not subscriptable, lo que tiraba todas las rutas v2/compras con 500.
        _db = None
    
    return _db


def close_database():
    """Cierra la conexión a la base de datos."""
    global _client, _db
    
    if _client:
        _client.close()
        _client = None
        _db = None
