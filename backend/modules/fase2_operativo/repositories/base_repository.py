"""
Repositorio Base con operaciones CRUD comunes
CAB-003 | EDARSA HUB - Fase 2A

NOTA: Este módulo está en proceso de migración a SQL.
Por ahora funciona con MongoDB si está disponible, 
o retorna datos vacíos si no lo está.
"""
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)

# Intentar importar bson, si no está disponible usar stubs
try:
    from bson import ObjectId
    from bson.errors import InvalidId
    BSON_AVAILABLE = True
except ImportError:
    BSON_AVAILABLE = False
    ObjectId = str
    class InvalidId(Exception):
        pass


class BaseRepository:
    """
    Clase base para repositories del módulo operativo.
    
    DEPRECADO: En migración a SQL. Funciona con MongoDB si está disponible.
    """
    
    def __init__(self, db, collection_name: str):
        """
        Inicializa el repository con la conexión a la colección.
        """
        self.db = db
        self.collection_name = collection_name
        self._mongo_available = db is not None
        
        if self._mongo_available:
            self.collection = db[collection_name]
        else:
            self.collection = None
            logger.warning(f"[FASE2] Repository {collection_name} - MongoDB no disponible, funcionando en modo degradado")
    
    def _serialize_id(self, doc: Optional[Dict]) -> Optional[Dict]:
        """Convierte ObjectId a string para serialización JSON segura."""
        if doc is None:
            return None
        if "_id" in doc and BSON_AVAILABLE and isinstance(doc["_id"], ObjectId):
            doc["_id"] = str(doc["_id"])
        return doc
    
    def _serialize_list(self, docs: List[Dict]) -> List[Dict]:
        """Serializa una lista de documentos."""
        return [self._serialize_id(doc) for doc in docs]
    
    def _to_object_id(self, id_str: str) -> Optional[Any]:
        """Convierte string a ObjectId de forma segura."""
        if not BSON_AVAILABLE:
            return id_str
        try:
            return ObjectId(id_str)
        except (InvalidId, TypeError):
            return None
    
    def _get_timestamp(self) -> datetime:
        """Retorna timestamp actual en UTC."""
        return datetime.now(timezone.utc)
    
    async def create(self, data: Dict[str, Any]) -> Dict:
        """Crea un nuevo documento."""
        if not self._mongo_available:
            logger.warning(f"[FASE2] create() en {self.collection_name} - MongoDB no disponible")
            data["_id"] = str(datetime.now().timestamp())
            return data
            
        data["fecha_creacion"] = self._get_timestamp()
        data["fecha_ultima_actualizacion"] = self._get_timestamp()
        
        result = self.collection.insert_one(data)
        data["_id"] = str(result.inserted_id)
        
        return data
    
    async def get_by_id(self, id: str) -> Optional[Dict]:
        """Obtiene un documento por su ID."""
        if not self._mongo_available:
            return None
            
        object_id = self._to_object_id(id)
        if object_id is None:
            return None
        
        doc = self.collection.find_one({"_id": object_id})
        return self._serialize_id(doc)
    
    async def get_all(
        self, 
        filters: Optional[Dict] = None, 
        skip: int = 0, 
        limit: int = 100,
        sort: Optional[List[tuple]] = None
    ) -> List[Dict]:
        """Obtiene todos los documentos con filtros opcionales."""
        if not self._mongo_available:
            return []
            
        filters = filters or {}
        cursor = self.collection.find(filters).skip(skip).limit(limit)
        
        if sort:
            cursor = cursor.sort(sort)
        
        return self._serialize_list(list(cursor))
    
    async def update(self, id: str, data: Dict[str, Any]) -> Optional[Dict]:
        """Actualiza un documento por su ID."""
        if not self._mongo_available:
            return None
            
        object_id = self._to_object_id(id)
        if object_id is None:
            return None
        
        data["fecha_ultima_actualizacion"] = self._get_timestamp()
        
        result = self.collection.find_one_and_update(
            {"_id": object_id},
            {"$set": data},
            return_document=True
        )
        
        return self._serialize_id(result)
    
    async def delete(self, id: str) -> bool:
        """Elimina un documento por su ID."""
        if not self._mongo_available:
            return False
            
        object_id = self._to_object_id(id)
        if object_id is None:
            return False
        
        result = self.collection.delete_one({"_id": object_id})
        return result.deleted_count > 0
    
    async def count(self, filters: Optional[Dict] = None) -> int:
        """Cuenta documentos que coinciden con los filtros."""
        if not self._mongo_available:
            return 0
            
        filters = filters or {}
        return self.collection.count_documents(filters)
    
    async def exists(self, filters: Dict) -> bool:
        """Verifica si existe al menos un documento."""
        if not self._mongo_available:
            return False
            
        return self.collection.count_documents(filters, limit=1) > 0
