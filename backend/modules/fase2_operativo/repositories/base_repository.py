"""
Repositorio Base con operaciones CRUD comunes
CAB-003 | EDARSA HUB - Fase 2A

Proporciona métodos reutilizables para todos los repositories del módulo.
Incluye serialización segura de ObjectId a string.
"""
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from bson import ObjectId
from bson.errors import InvalidId


class BaseRepository:
    """
    Clase base para repositories del módulo operativo.
    Maneja serialización de ObjectId y operaciones CRUD comunes.
    """
    
    def __init__(self, db, collection_name: str):
        """
        Inicializa el repository con la conexión a la colección.
        
        Args:
            db: Instancia de la base de datos MongoDB
            collection_name: Nombre de la colección
        """
        self.db = db
        self.collection = db[collection_name]
        self.collection_name = collection_name
    
    def _serialize_id(self, doc: Optional[Dict]) -> Optional[Dict]:
        """
        Convierte ObjectId a string para serialización JSON segura.
        
        Args:
            doc: Documento de MongoDB
            
        Returns:
            Documento con _id serializado como string
        """
        if doc is None:
            return None
        if "_id" in doc and isinstance(doc["_id"], ObjectId):
            doc["_id"] = str(doc["_id"])
        return doc
    
    def _serialize_list(self, docs: List[Dict]) -> List[Dict]:
        """
        Serializa una lista de documentos.
        
        Args:
            docs: Lista de documentos MongoDB
            
        Returns:
            Lista con _id serializados
        """
        return [self._serialize_id(doc) for doc in docs]
    
    def _to_object_id(self, id_str: str) -> Optional[ObjectId]:
        """
        Convierte string a ObjectId de forma segura.
        
        Args:
            id_str: String del ID
            
        Returns:
            ObjectId o None si es inválido
        """
        try:
            return ObjectId(id_str)
        except (InvalidId, TypeError):
            return None
    
    def _get_timestamp(self) -> datetime:
        """Retorna timestamp actual en UTC."""
        return datetime.now(timezone.utc)
    
    async def create(self, data: Dict[str, Any]) -> Dict:
        """
        Crea un nuevo documento.
        
        Args:
            data: Datos del documento a crear
            
        Returns:
            Documento creado con _id serializado
        """
        data["fecha_creacion"] = self._get_timestamp()
        data["fecha_ultima_actualizacion"] = self._get_timestamp()
        
        result = self.collection.insert_one(data)
        data["_id"] = str(result.inserted_id)
        
        return data
    
    async def get_by_id(self, id: str) -> Optional[Dict]:
        """
        Obtiene un documento por su ID.
        
        Args:
            id: ID del documento (string)
            
        Returns:
            Documento serializado o None si no existe
        """
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
        """
        Obtiene todos los documentos con filtros opcionales.
        
        Args:
            filters: Filtros de búsqueda
            skip: Documentos a saltar (paginación)
            limit: Límite de documentos a retornar
            sort: Lista de tuplas (campo, dirección) para ordenamiento
            
        Returns:
            Lista de documentos serializados
        """
        filters = filters or {}
        cursor = self.collection.find(filters).skip(skip).limit(limit)
        
        if sort:
            cursor = cursor.sort(sort)
        
        return self._serialize_list(list(cursor))
    
    async def update(self, id: str, data: Dict[str, Any]) -> Optional[Dict]:
        """
        Actualiza un documento por su ID.
        
        Args:
            id: ID del documento
            data: Datos a actualizar
            
        Returns:
            Documento actualizado o None si no existe
        """
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
        """
        Elimina un documento por su ID.
        
        Args:
            id: ID del documento
            
        Returns:
            True si se eliminó, False si no existía
        """
        object_id = self._to_object_id(id)
        if object_id is None:
            return False
        
        result = self.collection.delete_one({"_id": object_id})
        return result.deleted_count > 0
    
    async def count(self, filters: Optional[Dict] = None) -> int:
        """
        Cuenta documentos que coinciden con los filtros.
        
        Args:
            filters: Filtros de búsqueda
            
        Returns:
            Número de documentos
        """
        filters = filters or {}
        return self.collection.count_documents(filters)
    
    async def exists(self, filters: Dict) -> bool:
        """
        Verifica si existe al menos un documento con los filtros dados.
        
        Args:
            filters: Filtros de búsqueda
            
        Returns:
            True si existe, False si no
        """
        return self.collection.count_documents(filters, limit=1) > 0
