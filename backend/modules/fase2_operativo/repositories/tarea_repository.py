from core.unidades_service import UnidadesService
from core.corporate_filters.service import CorporateFilterService
"""
Repositorio para tareas_inventario
FASE B-P1-B | EDARSA HUB - Migración SQL Explícita

ARQUITECTURA:
- Todo acceso productivo a EDARSAHUB SQL Server
- CERO MongoDB productivo
- CERO conexiones LIVE

Gestiona el acceso a datos de tareas de inventario.
"""
from typing import Optional, List, Dict
from datetime import datetime, timezone
import logging

from .base_repository import BaseRepository, SQLBaseRepository

logger = logging.getLogger(__name__)

# Constantes para ordenamiento (reemplazan pymongo.ASCENDING/DESCENDING)
ASCENDING = 1
DESCENDING = -1


class TareaRepository(BaseRepository):
    """
    Repository para la tabla Tareas_Inventario.
    
    FASE B-P1-B: Migrado a SQL explícito.
    Hereda de BaseRepository que internamente usa SQLBaseRepository.
    
    NOTA: server_id no existe en Tareas_Inventario.
    Para filtrar por server_id se requiere JOIN con Workflow_Inventarios.
    """
    
    # Estados válidos de tareas
    ESTADOS_VALIDOS = [
        "PENDIENTE",
        "EN_PROGRESO",
        "COMPLETADA",
        "VENCIDA",
        "CANCELADA"
    ]
    
    def __init__(self, db):
        """
        Inicializa el repository.
        
        Args:
            db: IGNORADO - Solo para compatibilidad. Todo va a SQL.
        """
        super().__init__(db, "tareas_inventario")
        logger.info(f"[TAREA_REPO] Inicializado usando SQL: {self.table_name}")
    
    async def get_by_workflow(self, workflow_id: str) -> List[Dict]:
        """
        Obtiene todas las tareas de un workflow.
        
        MIGRADO A SQL: Usa SQLCursor con filtro WorkflowID.
        
        Args:
            workflow_id: ID del workflow
            
        Returns:
            Lista de tareas
        """
        cursor = self._sql_repo.find({"workflow_id": workflow_id})
        cursor = cursor.sort("fecha_creacion", DESCENDING)
        
        return list(cursor)
    
    async def get_by_usuario(
        self, 
        usuario_id: str, 
        solo_pendientes: bool = False
    ) -> List[Dict]:
        """
        Obtiene tareas asignadas a un usuario.
        
        MIGRADO A SQL: Usa SQLCursor con filtro UsuarioAsignadoID.
        
        Args:
            usuario_id: ID del usuario
            solo_pendientes: Si True, solo retorna tareas pendientes/en progreso
            
        Returns:
            Lista de tareas
        """
        filters = {"usuario_asignado_id": usuario_id}
        
        if solo_pendientes:
            filters["estado_tarea"] = {"$in": ["PENDIENTE", "EN_PROGRESO"]}
        
        cursor = self._sql_repo.find(filters)
        cursor = cursor.sort("fecha_limite", ASCENDING)
        
        return list(cursor)
    
    async def get_pendientes_globales(self, limit: int = 100, workflow_ids: Optional[List[str]] = None) -> List[Dict]:
        """
        Obtiene todas las tareas pendientes del sistema.
        
        MIGRADO A SQL: Usa SQLCursor con filtro de estados.
        Soporta filtro por workflow_ids (para acotar por unidad de negocio).
        
        Args:
            limit: Límite de resultados
            workflow_ids: Lista opcional de workflow uuid para filtrar por unidad
            
        Returns:
            Lista de tareas pendientes
        """
        # workflow_ids == [] significa "unidad sin workflows" → sin tareas
        if workflow_ids is not None and len(workflow_ids) == 0:
            return []
        
        filters = {"estado_tarea": {"$in": ["PENDIENTE", "EN_PROGRESO"]}}
        if workflow_ids:
            filters["workflow_id"] = {"$in": workflow_ids}
        
        cursor = self._sql_repo.find(filters)
        cursor = cursor.sort("fecha_limite", ASCENDING)
        cursor = cursor.limit(limit)
        
        return list(cursor)
    
    async def get_sin_asignar(self, limit: int = 100) -> List[Dict]:
        """
        Obtiene tareas que no tienen usuario asignado.
        
        MIGRADO A SQL: Usa SQL con IS NULL en lugar de $or/$exists.
        
        Args:
            limit: Límite de resultados
            
        Returns:
            Lista de tareas sin asignar
        """
        # En SQL, usamos IS NULL para campos vacíos
        # El SQLCursor no soporta $or directamente, hacemos query manual
        filters = {
            "usuario_asignado_id": None,
            "estado_tarea": "PENDIENTE"
        }
        
        cursor = self._sql_repo.find(filters)
        cursor = cursor.limit(limit)
        
        return list(cursor)
    
    async def get_vencidas(self, server_ids: Optional[List[str]] = None, workflow_ids: Optional[List[str]] = None) -> List[Dict]:
        """
        Obtiene tareas que han excedido su fecha límite.
        
        MIGRADO A SQL: Usa comparación de fechas.
        El filtro real por unidad se hace vía workflow_ids (resuelto en service),
        ya que Tareas_Inventario no tiene server_id.
        
        Args:
            server_ids: (obsoleto a este nivel) se ignora; usar workflow_ids
            workflow_ids: Lista opcional de workflow uuid para filtrar por unidad
        
        Returns:
            Lista de tareas vencidas
        """
        # workflow_ids == [] significa "unidad sin workflows" → sin tareas
        if workflow_ids is not None and len(workflow_ids) == 0:
            return []
        
        ahora = datetime.now(timezone.utc)
        
        filters = {
            "estado_tarea": {"$nin": ["COMPLETADA", "VENCIDA"]},
            "fecha_limite": {"$lt": ahora}
        }
        
        if workflow_ids:
            filters["workflow_id"] = {"$in": workflow_ids}
        
        cursor = self._sql_repo.find(filters)
        return list(cursor)
    
    async def asignar(
        self, 
        id: str, 
        usuario_id: str, 
        fecha_limite: Optional[datetime] = None
    ) -> Optional[Dict]:
        """
        Asigna una tarea a un usuario.
        
        MIGRADO A SQL: Usa update() de BaseRepository.
        
        Args:
            id: ID de la tarea (TareaID en SQL)
            usuario_id: ID del usuario
            fecha_limite: Fecha límite opcional
            
        Returns:
            Tarea actualizada
        """
        data = {
            "usuario_asignado_id": usuario_id,
            "fecha_asignacion": datetime.now(timezone.utc),
            "estado_tarea": "PENDIENTE"
        }
        
        if fecha_limite:
            data["fecha_limite"] = fecha_limite
        
        return await self.update(id, data)
    
    async def actualizar_estado(self, id: str, nuevo_estado: str) -> Optional[Dict]:
        """
        Actualiza el estado de una tarea.
        
        MIGRADO A SQL: Usa update() de BaseRepository con validación.
        
        Args:
            id: ID de la tarea (TareaID en SQL)
            nuevo_estado: Nuevo estado
            
        Returns:
            Tarea actualizada
        """
        if nuevo_estado not in self.ESTADOS_VALIDOS:
            logger.warning(f"[TAREA_REPO] Estado inválido: {nuevo_estado}")
        
        data = {
            "estado_tarea": nuevo_estado,
            "fecha_actualizacion": datetime.now(timezone.utc)
        }
        
        # Si se completa, registrar fecha
        if nuevo_estado == "COMPLETADA":
            data["fecha_completada"] = datetime.now(timezone.utc)
        
        return await self.update(id, data)
    
    async def completar(self, id: str) -> Optional[Dict]:
        """Marca una tarea como completada."""
        return await self.actualizar_estado(id, "COMPLETADA")
    
    async def marcar_en_progreso(self, id: str) -> Optional[Dict]:
        """Marca una tarea como en progreso."""
        return await self.actualizar_estado(id, "EN_PROGRESO")
    
    async def marcar_vencida(self, id: str) -> Optional[Dict]:
        """Marca una tarea como vencida."""
        data = {
            "estado_tarea": "VENCIDA",
            "vencida": True,
            "fecha_actualizacion": datetime.now(timezone.utc)
        }
        return await self.update(id, data)
    
    async def contar_por_estado(self, server_ids: Optional[List[str]] = None, workflow_ids: Optional[List[str]] = None) -> Dict[str, int]:
        """
        Cuenta tareas agrupadas por estado.
        
        MIGRADO A SQL: Usa aggregate() con GROUP BY.
        El filtro por unidad se hace vía workflow_ids (resuelto en service),
        ya que Tareas_Inventario no tiene server_id.
        
        Args:
            server_ids: (obsoleto a este nivel) se ignora; usar workflow_ids
            workflow_ids: Lista opcional de workflow uuid para filtrar por unidad
        
        Returns:
            Diccionario con conteos por estado {estado: count}
        """
        # workflow_ids == [] significa "unidad sin workflows" → 0 tareas
        if workflow_ids is not None and len(workflow_ids) == 0:
            return {}
        
        pipeline = []
        
        if workflow_ids:
            pipeline.append({"$match": {"workflow_id": {"$in": workflow_ids}}})
        
        # Group by estado
        pipeline.append({
            "$group": {
                "_id": "$estado_tarea",
                "count": {"$sum": 1}
            }
        })
        
        result = self._sql_repo.aggregate(pipeline)
        
        # Convertir a diccionario
        return {
            item.get("_id") or item.get("estado_tarea", "DESCONOCIDO"): 
            item.get("count", 0) 
            for item in result 
            if item.get("_id") or item.get("estado_tarea")
        }
    
    async def contar_por_usuario(self, usuario_id: str) -> Dict[str, int]:
        """
        Cuenta tareas de un usuario agrupadas por estado.
        
        MIGRADO A SQL: Usa aggregate() con $match y GROUP BY.
        
        Args:
            usuario_id: ID del usuario
            
        Returns:
            Diccionario con conteos por estado
        """
        pipeline = [
            {"$match": {"usuario_asignado_id": usuario_id}},
            {"$group": {"_id": "$estado_tarea", "count": {"$sum": 1}}}
        ]
        
        result = self._sql_repo.aggregate(pipeline)
        
        return {
            item.get("_id") or item.get("estado_tarea", "DESCONOCIDO"): 
            item.get("count", 0) 
            for item in result 
            if item.get("_id") or item.get("estado_tarea")
        }
    
    async def get_tareas_con_rbac(
        self,
        server_ids: List[str],
        estado: Optional[str] = None,
        usuario_id: Optional[str] = None,
        solo_vencidas: bool = False,
        skip: int = 0,
        limit: int = 100
    ) -> Dict:
        """
        Obtiene tareas con filtro RBAC mediante JOIN a Workflow_Inventarios.
        
        MÉTODO SQL NATIVO agregado en FASE B-P1-B.
        
        Este método hace JOIN para filtrar tareas por server_id,
        ya que Tareas_Inventario no tiene ese campo directamente.
        
        Args:
            server_ids: Lista de server_ids para RBAC
            estado: Filtro opcional por estado
            usuario_id: Filtro opcional por usuario asignado
            solo_vencidas: Si True, solo tareas vencidas
            skip: Paginación
            limit: Límite
            
        Returns:
            {items: [...], total: int}
        """
        import pymssql
        
        # Construir query con JOIN
        base_select = """
            SELECT t.*, w.ServerID, w.SucursalID, w.SucursalNombre
            FROM Tareas_Inventario t
            INNER JOIN Workflow_Inventarios w ON t.WorkflowID = w.WorkflowID
            WHERE 1=1
        """
        
        conditions = []
        params = []
        
        # Filtro RBAC por server_ids
        if server_ids:
            placeholders = ", ".join(["%s"] * len(server_ids))
            conditions.append(f"w.ServerID IN ({placeholders})")
            params.extend(server_ids)
        
        # Filtro por estado
        if estado:
            conditions.append("t.EstadoTarea = %s")
            params.append(estado)
        
        # Filtro por usuario
        if usuario_id:
            conditions.append("t.UsuarioAsignadoID = %s")
            params.append(usuario_id)
        
        # Filtro vencidas
        if solo_vencidas:
            conditions.append("t.FechaLimite < GETUTCDATE()")
            conditions.append("t.EstadoTarea NOT IN ('COMPLETADA', 'VENCIDA')")
        
        # Construir WHERE
        where_clause = ""
        if conditions:
            where_clause = " AND " + " AND ".join(conditions)
        
        # Query de conteo
        count_sql = f"""
            SELECT COUNT(*) as total
            FROM Tareas_Inventario t
            INNER JOIN Workflow_Inventarios w ON t.WorkflowID = w.WorkflowID
            WHERE 1=1 {where_clause}
        """
        
        # Query de datos con paginación
        data_sql = f"""
            {base_select} {where_clause}
            ORDER BY t.FechaCreacion DESC
            OFFSET {skip} ROWS FETCH NEXT {limit} ROWS ONLY
        """
        
        try:
            conn = self._sql_repo._get_connection()
            cursor = conn.cursor()
            
            # Ejecutar conteo
            cursor.execute(count_sql, params)
            total = cursor.fetchone()["total"]
            
            # Ejecutar query de datos
            cursor.execute(data_sql, params)
            rows = cursor.fetchall()
            
            cursor.close()
            conn.close()
            
            # Convertir rows a dicts
            items = [self._sql_repo._row_to_dict(row) for row in rows]
            
            return {"items": items, "total": total}
            
        except Exception as e:
            logger.error(f"[TAREA_REPO] Error en get_tareas_con_rbac: {e}")
            return {"items": [], "total": 0}
    
    async def buscar_tareas(
        self,
        workflow_id: Optional[str] = None,
        estado: Optional[str] = None,
        usuario_id: Optional[str] = None,
        tipo_tarea: Optional[str] = None,
        solo_vencidas: bool = False,
        skip: int = 0,
        limit: int = 50
    ) -> Dict:
        """
        Búsqueda avanzada de tareas con múltiples filtros.
        
        MÉTODO SQL NATIVO agregado en FASE B-P1-B.
        
        Args:
            workflow_id: Filtro por workflow
            estado: Filtro por estado
            usuario_id: Filtro por usuario asignado
            tipo_tarea: Filtro por tipo de tarea
            solo_vencidas: Si True, solo tareas vencidas
            skip: Paginación
            limit: Límite
            
        Returns:
            {items: [...], total: int}
        """
        filters = {}
        
        if workflow_id:
            filters["workflow_id"] = workflow_id
        if estado:
            filters["estado_tarea"] = estado
        if usuario_id:
            filters["usuario_asignado_id"] = usuario_id
        if tipo_tarea:
            filters["tipo_tarea"] = tipo_tarea
        if solo_vencidas:
            filters["vencida"] = True
        
        # Contar total
        total = await self.count(filters)
        
        # Obtener items
        cursor = self._sql_repo.find(filters)
        cursor = cursor.sort("fecha_creacion", DESCENDING)
        cursor = cursor.skip(skip)
        cursor = cursor.limit(limit)
        
        items = list(cursor)
        
        return {"items": items, "total": total}
    
    # =========================================================================
    # MÉTODOS DEPRECADOS (Compatibilidad)
    # =========================================================================
    
    def _serialize_list(self, docs: List[Dict]) -> List[Dict]:
        """
        DEPRECADO: No se necesita serialización en SQL.
        Mantenido para compatibilidad.
        """
        return docs
    
    def _get_timestamp(self) -> datetime:
        """Retorna timestamp actual UTC."""
        return datetime.now(timezone.utc)
