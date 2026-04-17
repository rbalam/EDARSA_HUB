"""
Utilidades de Base de Datos para Fase 2A
CAB-003 | EDARSA HUB

Proporciona acceso a la conexión de MongoDB para el módulo operativo.
"""
import os
from pymongo import MongoClient

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
        mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
        db_name = os.environ.get('DB_NAME', 'test_database')
        
        _client = MongoClient(mongo_url)
        _db = _client[db_name]
    
    return _db


def close_database():
    """Cierra la conexión a la base de datos."""
    global _client, _db
    
    if _client:
        _client.close()
        _client = None
        _db = None
