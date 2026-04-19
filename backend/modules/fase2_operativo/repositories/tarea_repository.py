"""
Repositorio para tareas_inventario
CAB-003 | EDARSA HUB - Fase 2A

Gestiona el acceso a datos de tareas de inventario.
"""
from typing import Optional, List, Dict
from datetime import datetime, timezone
from pymongo import ASCENDING, DESCENDING
from .base_repository import BaseRepository


class TareaRepository(BaseRepository):
    """Repository para la colección tareas_inventario."""
    
    def __init__(self, db):
        super().__init__(db, "tareas_inventario")
    
    async def get_by_workflow(self, workflow_id: str) -> List[Dict]:
        """
        Obtiene todas las tareas de un workflow.
        
        Args:
            workflow_id: ID del workflow
            
        Returns:
            Lista de tareas
        """
        cursor = self.collection.find(
            {"workflow_id": workflow_id}
        ).sort("fecha_creacion", DESCENDING)
        
        return self._serialize_list(list(cursor))
    
    async def get_by_usuario(
        self, 
        usuario_id: str, 
        solo_pendientes: bool = False
    ) -> List[Dict]:
        """
        Obtiene tareas asignadas a un usuario.
        
        Args:
            usuario_id: ID del usuario
            solo_pendientes: Si True, solo retorna tareas pendientes/en progreso
            
        Returns:
            Lista de tareas
        """
        filters = {"usuario_asignado_id": usuario_id}
        
        if solo_pendientes:
            filters["estado_tarea"] = {"$in": ["PENDIENTE", "EN_PROGRESO"]}
        
        cursor = self.collection.find(filters).sort("fecha_limite", ASCENDING)
        return self._serialize_list(list(cursor))
    
    async def get_pendientes_globales(self, limit: int = 100) -> List[Dict]:
        """
        Obtiene todas las tareas pendientes del sistema.
        
        Returns:
            Lista de tareas pendientes
        """
        cursor = self.collection.find({
            "estado_tarea": {"$in": ["PENDIENTE", "EN_PROGRESO"]}
        }).sort("fecha_limite", ASCENDING).limit(limit)
        
        return self._serialize_list(list(cursor))
    
    async def get_sin_asignar(self, limit: int = 100) -> List[Dict]:
        """
        Obtiene tareas que no tienen usuario asignado.
        
        Returns:
            Lista de tareas sin asignar
        """
        cursor = self.collection.find({
            "$or": [
                {"usuario_asignado_id": None},
                {"usuario_asignado_id": {"$exists": False}}
            ],
            "estado_tarea": "PENDIENTE"
        }).limit(limit)
        
        return self._serialize_list(list(cursor))
    
    async def get_vencidas(self, server_ids: Optional[List[str]] = None) -> List[Dict]:
        """
        Obtiene tareas que han excedido su fecha límite.
        FASE 3.1: Soporta filtrado por server_ids para RBAC.
        
        Args:
            server_ids: Lista opcional de server_ids permitidos para filtrar
        
        Returns:
            Lista de tareas vencidas
        """
        ahora = datetime.now(timezone.utc)
        
        filters = {
            "estado_tarea": {"$nin": ["COMPLETADA", "VENCIDA"]},
            "fecha_limite": {"$lt": ahora}
        }
        if server_ids:
            filters["server_id"] = {"$in": server_ids}
        
        cursor = self.collection.find(filters)
        return self._serialize_list(list(cursor))
    
    async def asignar(
        self, 
        id: str, 
        usuario_id: str, 
        fecha_limite: Optional[datetime] = None
    ) -> Optional[Dict]:
        """
        Asigna una tarea a un usuario.
        
        Args:
            id: ID de la tarea
            usuario_id: ID del usuario
            fecha_limite: Fecha límite opcional
            
        Returns:
            Tarea actualizada
        """
        data = {
            "usuario_asignado_id": usuario_id,
            "fecha_asignacion": self._get_timestamp(),
            "estado_tarea": "PENDIENTE"
        }
        
        if fecha_limite:
            data["fecha_limite"] = fecha_limite
        
        return await self.update(id, data)
    
    async def actualizar_estado(self, id: str, nuevo_estado: str) -> Optional[Dict]:
        """
        Actualiza el estado de una tarea.
        
        Args:
            id: ID de la tarea
            nuevo_estado: Nuevo estado
            
        Returns:
            Tarea actualizada
        """
        return await self.update(id, {"estado_tarea": nuevo_estado})
    
    async def completar(self, id: str) -> Optional[Dict]:
        """Marca una tarea como completada."""
        return await self.actualizar_estado(id, "COMPLETADA")
    
    async def marcar_en_progreso(self, id: str) -> Optional[Dict]:
        """Marca una tarea como en progreso."""
        return await self.actualizar_estado(id, "EN_PROGRESO")
    
    async def marcar_vencida(self, id: str) -> Optional[Dict]:
        """Marca una tarea como vencida."""
        return await self.actualizar_estado(id, "VENCIDA")
    
    async def contar_por_estado(self, server_ids: Optional[List[str]] = None) -> Dict[str, int]:
        """
        Cuenta tareas agrupadas por estado.
        FASE 3.1: Soporta filtrado por server_ids para RBAC.
        
        Args:
            server_ids: Lista opcional de server_ids permitidos para filtrar
        
        Returns:
            Diccionario con conteos por estado
        """
        match_stage = {}
        if server_ids:
            match_stage = {"$match": {"server_id": {"$in": server_ids}}}
        
        pipeline = []
        if match_stage:
            pipeline.append(match_stage)
        pipeline.append({"$group": {"_id": "$estado_tarea", "count": {"$sum": 1}}})
        
        result = list(self.collection.aggregate(pipeline))
        return {item["_id"]: item["count"] for item in result}
    
    async def contar_por_usuario(self, usuario_id: str) -> Dict[str, int]:
        """
        Cuenta tareas de un usuario agrupadas por estado.
        
        Args:
            usuario_id: ID del usuario
            
        Returns:
            Diccionario con conteos por estado
        """
        pipeline = [
            {"$match": {"usuario_asignado_id": usuario_id}},
            {"$group": {"_id": "$estado_tarea", "count": {"$sum": 1}}}
        ]
        
        result = list(self.collection.aggregate(pipeline))
        return {item["_id"]: item["count"] for item in result}
