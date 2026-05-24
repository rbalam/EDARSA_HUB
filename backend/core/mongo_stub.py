"""
EDARSA HUB - MongoDB Stub Database
==================================
Implementación stub de MongoDB que no falla cuando se accede a colecciones.

Este módulo proporciona un objeto 'db' que simula la interfaz de MongoDB
pero no hace nada (no persiste datos). Útil durante la transición a SQL Server.

Autor: Agente E1
Fecha: Mayo 2026
"""

from typing import Optional, List, Dict, Any
import logging

logger = logging.getLogger(__name__)


class StubCollection:
    """
    Colección stub que simula una colección de MongoDB.
    Todas las operaciones retornan valores vacíos/False sin fallar.
    """
    
    def __init__(self, name: str):
        self.name = name
        self._warned = False
    
    def _log_access(self, operation: str):
        """Loguea el acceso a la colección (solo una vez por colección)."""
        if not self._warned:
            logger.debug(f"[MONGO_STUB] Acceso a colección '{self.name}' - MongoDB eliminado")
            self._warned = True
    
    async def find_one(self, filter_query: Dict = None, projection: Dict = None, **kwargs) -> Optional[Dict]:
        """Simula find_one - retorna None."""
        self._log_access("find_one")
        return None
    
    def find(self, filter_query: Dict = None, projection: Dict = None) -> 'StubCursor':
        """Simula find - retorna cursor stub."""
        self._log_access("find")
        return StubCursor(self.name)
    
    async def insert_one(self, document: Dict) -> 'StubInsertResult':
        """Simula insert_one - retorna resultado stub."""
        self._log_access("insert_one")
        return StubInsertResult(document.get('id'))
    
    async def insert_many(self, documents: List[Dict]) -> 'StubInsertManyResult':
        """Simula insert_many - retorna resultado stub."""
        self._log_access("insert_many")
        return StubInsertManyResult([d.get('id') for d in documents])
    
    async def update_one(self, filter_query: Dict, update: Dict, upsert: bool = False) -> 'StubUpdateResult':
        """Simula update_one - retorna resultado stub."""
        self._log_access("update_one")
        return StubUpdateResult(0, None)
    
    async def update_many(self, filter_query: Dict, update: Dict) -> 'StubUpdateResult':
        """Simula update_many - retorna resultado stub."""
        self._log_access("update_many")
        return StubUpdateResult(0, None)
    
    async def delete_one(self, filter_query: Dict) -> 'StubDeleteResult':
        """Simula delete_one - retorna resultado stub."""
        self._log_access("delete_one")
        return StubDeleteResult(0)
    
    async def delete_many(self, filter_query: Dict) -> 'StubDeleteResult':
        """Simula delete_many - retorna resultado stub."""
        self._log_access("delete_many")
        return StubDeleteResult(0)
    
    async def count_documents(self, filter_query: Dict = None) -> int:
        """Simula count_documents - retorna 0."""
        self._log_access("count_documents")
        return 0
    
    def aggregate(self, pipeline: List[Dict]) -> 'StubCursor':
        """Simula aggregate - retorna cursor stub."""
        self._log_access("aggregate")
        return StubCursor(self.name)
    
    async def create_index(self, keys, **kwargs):
        """Simula create_index - no hace nada."""
        self._log_access("create_index")
        return None
    
    async def drop_index(self, index_name: str):
        """Simula drop_index - no hace nada."""
        self._log_access("drop_index")
        return None


class StubCursor:
    """
    Cursor stub que simula un cursor de MongoDB.
    """
    
    def __init__(self, collection_name: str):
        self.collection_name = collection_name
        self._sort_spec = None
        self._limit_val = None
        self._skip_val = None
    
    def sort(self, key_or_list, direction=None) -> 'StubCursor':
        """Simula sort - retorna self."""
        return self
    
    def limit(self, limit: int) -> 'StubCursor':
        """Simula limit - retorna self."""
        self._limit_val = limit
        return self
    
    def skip(self, skip: int) -> 'StubCursor':
        """Simula skip - retorna self."""
        self._skip_val = skip
        return self
    
    async def to_list(self, length: int = None) -> List[Dict]:
        """Simula to_list - retorna lista vacía."""
        return []
    
    def __aiter__(self):
        """Soporte para async iteration."""
        return self
    
    async def __anext__(self):
        """Simula iteración - siempre termina."""
        raise StopAsyncIteration


class StubInsertResult:
    """Resultado stub de insert_one."""
    
    def __init__(self, inserted_id=None):
        self.inserted_id = inserted_id
        self.acknowledged = True


class StubInsertManyResult:
    """Resultado stub de insert_many."""
    
    def __init__(self, inserted_ids=None):
        self.inserted_ids = inserted_ids or []
        self.acknowledged = True


class StubUpdateResult:
    """Resultado stub de update_one/update_many."""
    
    def __init__(self, modified_count=0, upserted_id=None):
        self.modified_count = modified_count
        self.matched_count = 0
        self.upserted_id = upserted_id
        self.acknowledged = True


class StubDeleteResult:
    """Resultado stub de delete_one/delete_many."""
    
    def __init__(self, deleted_count=0):
        self.deleted_count = deleted_count
        self.acknowledged = True


class StubDatabase:
    """
    Base de datos stub que simula una base de datos de MongoDB.
    Acceder a cualquier colección retorna un StubCollection.
    """
    
    def __init__(self):
        self._collections: Dict[str, StubCollection] = {}
        self._logged_init = False
    
    def __getattr__(self, name: str) -> StubCollection:
        """Acceder a cualquier atributo retorna una StubCollection."""
        if name.startswith('_'):
            raise AttributeError(name)
        
        if not self._logged_init:
            logger.info("[MONGO_STUB] Base de datos stub activa - MongoDB ELIMINADO")
            self._logged_init = True
        
        if name not in self._collections:
            self._collections[name] = StubCollection(name)
        
        return self._collections[name]
    
    def __getitem__(self, name: str) -> StubCollection:
        """Acceso por índice también retorna StubCollection."""
        return self.__getattr__(name)


# Instancia global del stub
_stub_db = StubDatabase()


def get_stub_database() -> StubDatabase:
    """Obtiene la instancia del stub database."""
    return _stub_db


__all__ = [
    'StubDatabase',
    'StubCollection',
    'StubCursor',
    'get_stub_database',
]
