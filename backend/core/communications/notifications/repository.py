"""
EDARSA HUB - Notification Repository
====================================
Subfase 2B.5 - Acceso a datos para notificaciones.

Colecciones:
- notification_config
- notification_provider_config
- notification_templates
- notification_queue
- notification_log
"""

from typing import Optional, List, Dict
from datetime import datetime, timezone
import logging

from .schemas import (
    NotificationConfig,
    NotificationTemplate,
    NotificationQueue,
    NotificationLog,
    ProviderConfig,
    NotificationStatus,
)

logger = logging.getLogger(__name__)


class NotificationRepository:
    """
    Repository para operaciones CRUD de notificaciones.
    """
    
    def __init__(self, db):
        self.db = db
        self.config_collection = db.notification_config
        self.provider_collection = db.notification_provider_config
        self.template_collection = db.notification_templates
        self.queue_collection = db.notification_queue
        self.log_collection = db.notification_log
    
    # =========================================================================
    # CONFIGURACIÓN
    # =========================================================================
    
    async def get_config(
        self,
        canal: str,
        modulo: str,
        evento: str
    ) -> Optional[Dict]:
        """Obtiene configuración específica para un evento."""
        return await self.config_collection.find_one(
            {
                "canal": canal,
                "modulo": modulo,
                "evento": evento,
                "activo": True
            },
            {"_id": 0}
        )
    
    async def get_all_configs(
        self,
        modulo: Optional[str] = None,
        canal: Optional[str] = None,
        activo: Optional[bool] = None
    ) -> List[Dict]:
        """Lista configuraciones con filtros opcionales."""
        filtro = {}
        if modulo:
            filtro["modulo"] = modulo
        if canal:
            filtro["canal"] = canal
        if activo is not None:
            filtro["activo"] = activo
        
        cursor = self.config_collection.find(filtro, {"_id": 0})
        return await cursor.to_list(length=500)
    
    async def create_config(self, config: NotificationConfig) -> Dict:
        """Crea una nueva configuración."""
        doc = config.model_dump()
        await self.config_collection.insert_one(doc)
        return {k: v for k, v in doc.items() if k != "_id"}
    
    async def update_config(self, config_id: str, updates: Dict) -> Optional[Dict]:
        """Actualiza una configuración."""
        updates["updated_at"] = datetime.now(timezone.utc).isoformat()
        await self.config_collection.update_one(
            {"id": config_id},
            {"$set": updates}
        )
        return await self.config_collection.find_one({"id": config_id}, {"_id": 0})
    
    async def delete_config(self, config_id: str) -> bool:
        """Elimina una configuración."""
        result = await self.config_collection.delete_one({"id": config_id})
        return result.deleted_count > 0
    
    # =========================================================================
    # PROVIDER CONFIG
    # =========================================================================
    
    async def get_provider_config(self, canal: str, provider: str) -> Optional[Dict]:
        """Obtiene configuración de un provider específico."""
        return await self.provider_collection.find_one(
            {"canal": canal, "provider": provider, "activo": True},
            {"_id": 0}
        )
    
    async def get_active_provider(self, canal: str) -> Optional[Dict]:
        """Obtiene el provider activo para un canal."""
        return await self.provider_collection.find_one(
            {"canal": canal, "activo": True},
            {"_id": 0}
        )
    
    async def create_provider_config(self, config: ProviderConfig) -> Dict:
        """Crea configuración de provider."""
        doc = config.model_dump()
        await self.provider_collection.insert_one(doc)
        return {k: v for k, v in doc.items() if k != "_id"}
    
    async def update_provider_config(self, config_id: str, updates: Dict) -> Optional[Dict]:
        """Actualiza configuración de provider."""
        updates["updated_at"] = datetime.now(timezone.utc).isoformat()
        await self.provider_collection.update_one(
            {"id": config_id},
            {"$set": updates}
        )
        return await self.provider_collection.find_one({"id": config_id}, {"_id": 0})
    
    # =========================================================================
    # TEMPLATES
    # =========================================================================
    
    async def get_template(self, canal: str, codigo: str) -> Optional[Dict]:
        """Obtiene un template por canal y código."""
        return await self.template_collection.find_one(
            {"canal": canal, "codigo": codigo, "activo": True},
            {"_id": 0}
        )
    
    async def get_template_by_id(self, template_id: str) -> Optional[Dict]:
        """Obtiene un template por ID."""
        return await self.template_collection.find_one(
            {"id": template_id},
            {"_id": 0}
        )
    
    async def get_all_templates(
        self,
        canal: Optional[str] = None,
        activo: Optional[bool] = None
    ) -> List[Dict]:
        """Lista templates con filtros opcionales."""
        filtro = {}
        if canal:
            filtro["canal"] = canal
        if activo is not None:
            filtro["activo"] = activo
        
        cursor = self.template_collection.find(filtro, {"_id": 0})
        return await cursor.to_list(length=500)
    
    async def create_template(self, template: NotificationTemplate) -> Dict:
        """Crea un nuevo template."""
        doc = template.model_dump()
        await self.template_collection.insert_one(doc)
        return {k: v for k, v in doc.items() if k != "_id"}
    
    async def update_template(self, template_id: str, updates: Dict) -> Optional[Dict]:
        """Actualiza un template."""
        updates["updated_at"] = datetime.now(timezone.utc).isoformat()
        # Incrementar versión si se modifica el texto
        if "template_texto" in updates:
            await self.template_collection.update_one(
                {"id": template_id},
                {"$set": updates, "$inc": {"version": 1}}
            )
        else:
            await self.template_collection.update_one(
                {"id": template_id},
                {"$set": updates}
            )
        return await self.template_collection.find_one({"id": template_id}, {"_id": 0})
    
    async def delete_template(self, template_id: str) -> bool:
        """Elimina un template (soft delete)."""
        result = await self.template_collection.update_one(
            {"id": template_id},
            {"$set": {"activo": False, "updated_at": datetime.now(timezone.utc).isoformat()}}
        )
        return result.modified_count > 0
    
    # =========================================================================
    # QUEUE
    # =========================================================================
    
    async def enqueue(self, item: NotificationQueue) -> Dict:
        """Agrega item a la cola."""
        doc = item.model_dump()
        await self.queue_collection.insert_one(doc)
        return {k: v for k, v in doc.items() if k != "_id"}
    
    async def get_pending_items(self, limit: int = 50) -> List[Dict]:
        """Obtiene items pendientes de la cola, ordenados por prioridad."""
        ahora = datetime.now(timezone.utc).isoformat()
        cursor = self.queue_collection.find(
            {
                "estado": NotificationStatus.PENDIENTE.value,
                "$and": [
                    {"$or": [
                        {"proximo_intento": None},
                        {"proximo_intento": {"$lte": ahora}}
                    ]},
                    {"$or": [
                        {"locked_at": None},
                        {"locked_at": {"$lt": ahora}}  # Lock expirado
                    ]}
                ]
            },
            {"_id": 0}
        ).sort([("prioridad", 1), ("created_at", 1)]).limit(limit)
        return await cursor.to_list(length=limit)
    
    async def lock_item(self, queue_id: str, worker_id: str) -> bool:
        """Bloquea un item para procesamiento."""
        ahora = datetime.now(timezone.utc).isoformat()
        result = await self.queue_collection.update_one(
            {
                "id": queue_id,
                "$or": [
                    {"locked_at": None},
                    {"locked_at": {"$lt": ahora}}
                ]
            },
            {
                "$set": {
                    "locked_at": ahora,
                    "locked_by": worker_id,
                    "updated_at": ahora
                }
            }
        )
        return result.modified_count > 0
    
    async def update_queue_item(self, queue_id: str, updates: Dict) -> bool:
        """Actualiza un item de la cola."""
        updates["updated_at"] = datetime.now(timezone.utc).isoformat()
        result = await self.queue_collection.update_one(
            {"id": queue_id},
            {"$set": updates}
        )
        return result.modified_count > 0
    
    async def mark_sent(self, queue_id: str) -> bool:
        """Marca item como enviado."""
        return await self.update_queue_item(queue_id, {
            "estado": NotificationStatus.ENVIADO.value,
            "locked_at": None,
            "locked_by": None
        })
    
    async def mark_failed(self, queue_id: str, error: str) -> bool:
        """Marca item como fallido e incrementa intentos."""
        ahora = datetime.now(timezone.utc).isoformat()
        result = await self.queue_collection.update_one(
            {"id": queue_id},
            {
                "$set": {
                    "estado": NotificationStatus.FALLIDO.value,
                    "locked_at": None,
                    "locked_by": None,
                    "updated_at": ahora
                },
                "$inc": {"intentos": 1}
            }
        )
        return result.modified_count > 0
    
    async def get_queue_stats(self) -> Dict:
        """Obtiene estadísticas de la cola."""
        pipeline = [
            {"$group": {"_id": "$estado", "count": {"$sum": 1}}}
        ]
        cursor = self.queue_collection.aggregate(pipeline)
        stats = {}
        async for doc in cursor:
            stats[doc["_id"]] = doc["count"]
        return stats
    
    # =========================================================================
    # LOG
    # =========================================================================
    
    async def create_log(self, log: NotificationLog) -> Dict:
        """Crea entrada de log."""
        doc = log.model_dump()
        await self.log_collection.insert_one(doc)
        return {k: v for k, v in doc.items() if k != "_id"}
    
    async def get_logs(
        self,
        workflow_id: Optional[str] = None,
        referencia_id: Optional[str] = None,
        evento_negocio: Optional[str] = None,
        destinatario: Optional[str] = None,
        estado_envio: Optional[str] = None,
        fecha_desde: Optional[str] = None,
        fecha_hasta: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Dict]:
        """Obtiene logs con filtros."""
        filtro = {}
        if workflow_id:
            filtro["workflow_id"] = workflow_id
        if referencia_id:
            filtro["referencia_id"] = referencia_id
        if evento_negocio:
            filtro["evento_negocio"] = evento_negocio
        if destinatario:
            filtro["destinatario"] = destinatario
        if estado_envio:
            filtro["estado_envio"] = estado_envio
        if fecha_desde:
            filtro["fecha_intento"] = {"$gte": fecha_desde}
        if fecha_hasta:
            if "fecha_intento" in filtro:
                filtro["fecha_intento"]["$lte"] = fecha_hasta
            else:
                filtro["fecha_intento"] = {"$lte": fecha_hasta}
        
        cursor = self.log_collection.find(
            filtro, {"_id": 0}
        ).sort("fecha_intento", -1).skip(skip).limit(limit)
        return await cursor.to_list(length=limit)
    
    async def count_logs(self, filtro: Dict = None) -> int:
        """Cuenta logs con filtro opcional."""
        return await self.log_collection.count_documents(filtro or {})
    
    async def get_log_stats(self, modulo: Optional[str] = None) -> Dict:
        """Obtiene estadísticas de logs."""
        match_stage = {}
        if modulo:
            match_stage["modulo"] = modulo
        
        pipeline = [
            {"$match": match_stage} if match_stage else {"$match": {}},
            {
                "$group": {
                    "_id": {
                        "evento": "$evento_negocio",
                        "estado": "$estado_envio"
                    },
                    "count": {"$sum": 1}
                }
            }
        ]
        
        cursor = self.log_collection.aggregate(pipeline)
        stats = {}
        async for doc in cursor:
            evento = doc["_id"]["evento"]
            estado = doc["_id"]["estado"]
            if evento not in stats:
                stats[evento] = {}
            stats[evento][estado] = doc["count"]
        return stats
    
    # =========================================================================
    # DEDUPLICACIÓN
    # =========================================================================
    
    async def check_duplicate(
        self,
        evento_negocio: str,
        referencia_id: str,
        workflow_id: str,
        destinatario: str,
        template_codigo: str,
        ventana_minutos: int
    ) -> bool:
        """
        Verifica si ya existe un envío duplicado en la ventana de tiempo.
        
        Returns:
            True si es duplicado, False si no
        """
        from datetime import timedelta
        
        ahora = datetime.now(timezone.utc)
        inicio_ventana = (ahora - timedelta(minutes=ventana_minutos)).isoformat()
        
        existente = await self.log_collection.find_one({
            "evento_negocio": evento_negocio,
            "referencia_id": referencia_id,
            "workflow_id": workflow_id,
            "destinatario": destinatario,
            "template_codigo": template_codigo,
            "estado_envio": {"$in": [
                NotificationStatus.ENVIADO.value,
                NotificationStatus.ENTREGADO.value
            ]},
            "fecha_intento": {"$gte": inicio_ventana}
        })
        
        return existente is not None


# =============================================================================
# SINGLETON
# =============================================================================

_repository: Optional[NotificationRepository] = None


def get_notification_repository(db) -> NotificationRepository:
    """Obtiene instancia del repository."""
    global _repository
    if _repository is None:
        _repository = NotificationRepository(db)
    return _repository


def reset_notification_repository():
    """Reset para testing."""
    global _repository
    _repository = None
