"""
Repositorio para workflow_inventarios
FASE B-P1-A | EDARSA HUB - Migración SQL Explícita

ARQUITECTURA:
- Todo acceso productivo a EDARSAHUB SQL Server
- CERO MongoDB productivo
- CERO conexiones LIVE

Gestiona el acceso a datos de workflows de inventario.
"""
from typing import Optional, List, Dict
from datetime import datetime, timezone
import logging

from .base_repository import BaseRepository, SQLBaseRepository

logger = logging.getLogger(__name__)

# Constante para ordenamiento descendente (reemplaza pymongo.DESCENDING)
DESCENDING = -1


class WorkflowRepository(BaseRepository):
    """
    Repository para la tabla Workflow_Inventarios.
    
    FASE B-P1-A: Migrado a SQL explícito.
    Hereda de BaseRepository que internamente usa SQLBaseRepository.
    """
    
    # Mapeo de estados para validación
    ESTADOS_VALIDOS = [
        "PENDIENTE_ASIGNACION",
        "EN_REVISION", 
        "PENDIENTE_JUSTIFICACION",
        "EN_AUDITORIA",
        "ESCALADO",
        "CERRADO",
        "CANCELADO"
    ]
    
    def __init__(self, db):
        """
        Inicializa el repository.
        
        Args:
            db: IGNORADO - Solo para compatibilidad. Todo va a SQL.
        """
        super().__init__(db, "workflow_inventarios")
        logger.info(f"[WORKFLOW_REPO] Inicializado usando SQL: {self.table_name}")
    
    async def get_by_procesado_id(self, procesado_id: str) -> Optional[Dict]:
        """
        Obtiene un workflow por su procesado_id (FK a Fase 1).
        
        MIGRADO A SQL: Usa find_one con filtro ProcesadoID.
        
        Args:
            procesado_id: ID del folio procesado
            
        Returns:
            Workflow o None si no existe
        """
        doc = self._sql_repo.find_one({"procesado_id": procesado_id})
        return doc
    
    async def get_by_estado(
        self, 
        estado: str, 
        skip: int = 0, 
        limit: int = 100,
        server_ids: Optional[List[str]] = None
    ) -> List[Dict]:
        """
        Obtiene workflows por estado.
        
        MIGRADO A SQL: Usa SELECT con WHERE EstadoWorkflow y ORDER BY.
        
        Args:
            estado: Estado del workflow
            skip: Paginación
            limit: Límite
            server_ids: Lista opcional de server_ids para filtro RBAC
            
        Returns:
            Lista de workflows
        """
        filters = {"estado_workflow": estado}
        if server_ids:
            filters["server_id"] = {"$in": server_ids}
        
        # Usar SQLCursor encadenable
        cursor = self._sql_repo.find(filters)
        cursor = cursor.sort("fecha_creacion", DESCENDING)
        cursor = cursor.skip(skip)
        cursor = cursor.limit(limit)
        
        return list(cursor)
    
    async def get_pendientes_asignacion(
        self, 
        limit: int = 100,
        server_ids: Optional[List[str]] = None
    ) -> List[Dict]:
        """Obtiene workflows pendientes de asignación."""
        return await self.get_by_estado(
            "PENDIENTE_ASIGNACION", 
            limit=limit,
            server_ids=server_ids
        )
    
    async def get_en_revision(
        self, 
        limit: int = 100,
        server_ids: Optional[List[str]] = None
    ) -> List[Dict]:
        """Obtiene workflows en revisión."""
        return await self.get_by_estado(
            "EN_REVISION", 
            limit=limit,
            server_ids=server_ids
        )
    
    async def get_pendientes_justificacion(
        self, 
        limit: int = 100,
        server_ids: Optional[List[str]] = None
    ) -> List[Dict]:
        """Obtiene workflows pendientes de justificación."""
        return await self.get_by_estado(
            "PENDIENTE_JUSTIFICACION", 
            limit=limit,
            server_ids=server_ids
        )
    
    async def get_en_auditoria(
        self, 
        limit: int = 100,
        server_ids: Optional[List[str]] = None
    ) -> List[Dict]:
        """Obtiene workflows en auditoría."""
        return await self.get_by_estado(
            "EN_AUDITORIA", 
            limit=limit,
            server_ids=server_ids
        )
    
    async def get_escalados(
        self, 
        limit: int = 100, 
        server_ids: Optional[List[str]] = None
    ) -> List[Dict]:
        """
        Obtiene workflows escalados.
        
        MIGRADO A SQL: Soporta filtrado por server_ids para RBAC.
        
        Args:
            limit: Límite de resultados
            server_ids: Lista opcional de server_ids para filtro RBAC
            
        Returns:
            Lista de workflows escalados
        """
        return await self.get_by_estado(
            "ESCALADO",
            limit=limit,
            server_ids=server_ids
        )
    
    async def actualizar_estado(
        self, 
        workflow_id: str, 
        nuevo_estado: str
    ) -> Optional[Dict]:
        """
        Actualiza el estado de un workflow.
        
        MIGRADO A SQL: Usa UPDATE con validación de estado.
        
        Args:
            workflow_id: ID del workflow (WorkflowID en SQL)
            nuevo_estado: Nuevo estado
            
        Returns:
            Workflow actualizado o None si no existe
        """
        if nuevo_estado not in self.ESTADOS_VALIDOS:
            logger.warning(f"[WORKFLOW_REPO] Estado inválido: {nuevo_estado}")
        
        return await self.update(workflow_id, {
            "estado_workflow": nuevo_estado,
            "fecha_ultima_actualizacion": datetime.now(timezone.utc)
        })
    
    async def incrementar_ciclo(self, workflow_id: str) -> Optional[Dict]:
        """
        Incrementa el ciclo de reasignación de un workflow.
        
        MIGRADO A SQL: Usa UPDATE con incremento explícito.
        No usa $inc de MongoDB, hace SELECT + UPDATE.
        
        Args:
            workflow_id: ID del workflow (WorkflowID en SQL)
            
        Returns:
            Workflow actualizado o None si no existe
        """
        # Obtener workflow actual
        workflow = await self.get_by_id(workflow_id)
        if not workflow:
            logger.warning(f"[WORKFLOW_REPO] Workflow no encontrado: {workflow_id}")
            return None
        
        # Calcular nuevo ciclo
        ciclo_actual = workflow.get("ciclo_actual", 0) or 0
        nuevo_ciclo = ciclo_actual + 1
        
        # Actualizar
        return await self.update(workflow_id, {
            "ciclo_actual": nuevo_ciclo,
            "fecha_ultima_actualizacion": datetime.now(timezone.utc)
        })
    
    async def contar_por_estado(
        self, 
        server_ids: Optional[List[str]] = None
    ) -> Dict[str, int]:
        """
        Cuenta workflows agrupados por estado.
        
        MIGRADO A SQL: Usa GROUP BY explícito en lugar de aggregate de MongoDB.
        FASE 3.1: Soporta filtrado por server_ids para RBAC.
        
        Args:
            server_ids: Lista opcional de server_ids permitidos para filtrar
        
        Returns:
            Diccionario con conteos por estado {estado: count}
        """
        # Construir pipeline de agregación
        pipeline = []
        
        # Match por server_ids si se especifica (RBAC)
        if server_ids:
            pipeline.append({"$match": {"server_id": {"$in": server_ids}}})
        
        # Group by estado
        pipeline.append({
            "$group": {
                "_id": "$estado_workflow",
                "count": {"$sum": 1}
            }
        })
        
        # Ejecutar agregación
        result = self._sql_repo.aggregate(pipeline)
        
        # Convertir a diccionario
        return {
            item.get("_id") or item.get("estado_workflow", "DESCONOCIDO"): 
            item.get("count", 0) 
            for item in result 
            if item.get("_id") or item.get("estado_workflow")
        }
    
    async def buscar_workflows(
        self,
        server_ids: Optional[List[str]] = None,
        estado: Optional[str] = None,
        sucursal_id: Optional[str] = None,
        fecha_desde: Optional[datetime] = None,
        fecha_hasta: Optional[datetime] = None,
        skip: int = 0,
        limit: int = 50
    ) -> Dict:
        """
        Búsqueda avanzada de workflows con múltiples filtros.
        
        MÉTODO SQL NATIVO agregado en FASE B-P1-A.
        
        Args:
            server_ids: Lista de server_ids para RBAC
            estado: Filtro por estado
            sucursal_id: Filtro por sucursal
            fecha_desde: Fecha inicio
            fecha_hasta: Fecha fin
            skip: Paginación
            limit: Límite
            
        Returns:
            {items: [...], total: int}
        """
        filters = {}
        
        if server_ids:
            filters["server_id"] = {"$in": server_ids}
        if estado:
            filters["estado_workflow"] = estado
        if sucursal_id:
            filters["sucursal_id"] = sucursal_id
        if fecha_desde:
            filters["fecha_creacion"] = {"$gte": fecha_desde}
        if fecha_hasta:
            if "fecha_creacion" in filters:
                filters["fecha_creacion"]["$lte"] = fecha_hasta
            else:
                filters["fecha_creacion"] = {"$lte": fecha_hasta}
        
        # Contar total
        total = await self.count(filters)
        
        # Obtener items
        cursor = self._sql_repo.find(filters)
        cursor = cursor.sort("fecha_creacion", DESCENDING)
        cursor = cursor.skip(skip)
        cursor = cursor.limit(limit)
        
        items = list(cursor)
        
        return {"items": items, "total": total}
    
    async def get_workflow_completo(self, workflow_id: str) -> Optional[Dict]:
        """
        Obtiene un workflow con todos sus datos.
        
        MÉTODO SQL NATIVO agregado en FASE B-P1-A.
        
        Args:
            workflow_id: ID del workflow
            
        Returns:
            Workflow completo o None
        """
        return await self.get_by_id(workflow_id)
    
    # =========================================================================
    # MÉTODOS DEPRECADOS (Compatibilidad)
    # =========================================================================
    
    def _to_object_id(self, id_str: str):
        """
        DEPRECADO: No se usa ObjectId en SQL.
        Mantenido para compatibilidad, retorna el ID directamente.
        """
        logger.debug(f"[WORKFLOW_REPO] _to_object_id deprecado, retornando ID: {id_str}")
        return id_str
    
    def _serialize_id(self, doc: Optional[Dict]) -> Optional[Dict]:
        """
        DEPRECADO: No se necesita serialización de _id en SQL.
        Mantenido para compatibilidad.
        """
        return doc
    
    def _serialize_list(self, docs: List[Dict]) -> List[Dict]:
        """
        DEPRECADO: No se necesita serialización en SQL.
        Mantenido para compatibilidad.
        """
        return docs
