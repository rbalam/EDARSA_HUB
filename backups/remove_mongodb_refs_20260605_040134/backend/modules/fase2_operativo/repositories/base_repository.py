"""
Repositorio Base para módulo fase2_operativo
FASE B-P0-C | EDARSA HUB

MIGRADO A SQL SERVER:
- Este módulo ahora usa SQLBaseRepository de sql_base_repository.py
- CERO MongoDB productivo
- CERO conexiones LIVE

ARQUITECTURA:
- Todo acceso productivo va a EDARSAHUB SQL Server
- El parámetro 'db' (MongoDB) se ignora completamente
- Mantiene compatibilidad de interfaz con repositories existentes
"""

# Re-exportar desde sql_base_repository para compatibilidad total
from .sql_base_repository import (
    BaseRepository,
    SQLBaseRepository,
    SQLRepositoryNotImplementedError,
    COLLECTION_TO_TABLE_MAP,
    FIELD_MAPPING,
    get_sql_repository,
)

# Mantener exports para compatibilidad con imports existentes
__all__ = [
    "BaseRepository",
    "SQLBaseRepository", 
    "SQLRepositoryNotImplementedError",
    "COLLECTION_TO_TABLE_MAP",
    "FIELD_MAPPING",
    "get_sql_repository",
]
