"""
EDARSA HUB - Conexiones a Base de Datos
=======================================
Gestión centralizada de conexiones a MongoDB y SQL Server.

NOTA: Este archivo es parte del refactor modular.
Las conexiones actuales siguen en server.py hasta que se autorice la migración.

USO FUTURO:
    from core.db import get_mongo_db, execute_sql_query
"""

from typing import Optional, Dict, Any, List
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo import MongoClient
import logging

# Variables globales para conexiones (se inicializarán en la migración)
_mongo_client: Optional[AsyncIOMotorClient] = None
_mongo_db: Optional[AsyncIOMotorDatabase] = None
_sync_mongo_client: Optional[MongoClient] = None


async def get_mongo_client() -> AsyncIOMotorClient:
    """
    Obtiene el cliente MongoDB async.
    NOTA: No implementado aún - usar conexión de server.py
    """
    global _mongo_client
    if _mongo_client is None:
        raise RuntimeError("MongoDB client not initialized. Use server.py connection.")
    return _mongo_client


async def get_mongo_db() -> AsyncIOMotorDatabase:
    """
    Obtiene la base de datos MongoDB async.
    NOTA: No implementado aún - usar conexión de server.py
    """
    global _mongo_db
    if _mongo_db is None:
        raise RuntimeError("MongoDB database not initialized. Use server.py connection.")
    return _mongo_db


def get_sync_mongo_db():
    """
    Obtiene la base de datos MongoDB síncrona.
    NOTA: No implementado aún - usar conexión de server.py
    """
    global _sync_mongo_client
    if _sync_mongo_client is None:
        raise RuntimeError("Sync MongoDB client not initialized. Use server.py connection.")
    return _sync_mongo_client


def execute_sql_query(
    host: str,
    port: int,
    database: str,
    username: str,
    password: str,
    query: str,
    timeout: int = 30
) -> List[Dict[str, Any]]:
    """
    Ejecuta una query SQL en SQL Server.
    
    NOTA: No implementado aún - usar execute_sql_query de server.py
    Esta función se migrará en fases posteriores.
    
    Args:
        host: Hostname del servidor SQL
        port: Puerto
        database: Nombre de la base de datos
        username: Usuario
        password: Contraseña
        query: Query SQL a ejecutar
        timeout: Timeout en segundos
        
    Returns:
        Lista de diccionarios con los resultados
    """
    raise NotImplementedError("Use execute_sql_query from server.py until migration is complete.")


# Placeholder para inicialización futura
def init_db_connections(mongo_url: str, db_name: str):
    """
    Inicializa las conexiones a bases de datos.
    NOTA: Se usará cuando se migre desde server.py
    """
    pass
