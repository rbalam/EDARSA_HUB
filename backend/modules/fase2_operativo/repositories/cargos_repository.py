"""
Repository para Cargos Económicos
CAB-003 | EDARSA HUB - Fase 2C.3

CRUD y consultas para las colecciones:
- cargos_economicos: Registro formal de cargos
- cargos_economicos_log: Auditoría de transiciones
"""
from typing import Optional, List, Dict
from datetime import datetime, timezone
from bson import ObjectId
import uuid
import logging

from .base_repository import BaseRepository

logger = logging.getLogger(__name__)


class CargosEconomicosRepository(BaseRepository):
    """Repository para la colección cargos_economicos."""
    
    def __init__(self, db):
        super().__init__(db, "cargos_economicos")
        self._ensure_indexes()
    
    def _ensure_indexes(self):
        """Crea índices necesarios para la colección."""
        try:
            # Índice único por ID
            self.collection.create_index("id", unique=True)
            # Índices de búsqueda
            self.collection.create_index("responsabilidad_id")
            self.collection.create_index("workflow_id")
            self.collection.create_index("sucursal_id")
            self.collection.create_index("estatus_cargo")
            self.collection.create_index("responsable_id")
            # Índice compuesto para evitar duplicados por responsabilidad activa
            self.collection.create_index(
                [("responsabilidad_id", 1), ("estatus_cargo", 1)],
                name="idx_responsabilidad_estatus"
            )
            # Índice para ordenamiento temporal
            self.collection.create_index([("fecha_propuesta", -1)])
            logger.info("Índices de cargos_economicos verificados/creados")
        except Exception as e:
            logger.warning(f"Error creando índices de cargos_economicos: {e}")
    
    async def crear_cargo(self, datos: Dict) -> str:
        """
        Crea un nuevo registro de cargo económico.
        
        Args:
            datos: Dict con los datos del cargo
            
        Returns:
            ID del cargo creado
        """
        now = datetime.now(timezone.utc)
        cargo_id = datos.get("id") or str(uuid.uuid4())
        
        documento = {
            "id": cargo_id,
            
            # Referencias
            "responsabilidad_id": datos.get("responsabilidad_id"),
            "workflow_id": datos.get("workflow_id"),
            "procesado_id": datos.get("procesado_id", ""),
            "sucursal_id": datos.get("sucursal_id", ""),
            
            # Responsable
            "responsable_id": datos.get("responsable_id"),
            "responsable_nombre": datos.get("responsable_nombre"),
            
            # Montos
            "monto_responsabilidad": datos.get("monto_responsabilidad", 0.0),
            "monto_aplicado": datos.get("monto_aplicado", 0.0),
            "monto_revertido": datos.get("monto_revertido", 0.0),
            
            # Estado
            "estatus_cargo": datos.get("estatus_cargo", "PENDIENTE"),
            "origen": datos.get("origen", "RESPONSABILIDAD_ECONOMICA"),
            
            # Fechas de ciclo de vida
            "fecha_propuesta": datos.get("fecha_propuesta", now),
            "fecha_autorizacion": datos.get("fecha_autorizacion"),
            "fecha_aplicacion": datos.get("fecha_aplicacion"),
            "fecha_reversa": datos.get("fecha_reversa"),
            
            # Usuarios responsables
            "propuesto_por": datos.get("propuesto_por"),
            "autorizado_por": datos.get("autorizado_por"),
            "aplicado_por": datos.get("aplicado_por"),
            "revertido_por": datos.get("revertido_por"),
            
            # Auditoría
            "fecha_creacion": now,
            "fecha_actualizacion": now,
        }
        
        self.collection.insert_one(documento)
        logger.info(f"Cargo económico creado: {cargo_id} para responsabilidad {datos.get('responsabilidad_id')}")
        return cargo_id
    
    async def get_by_id(self, cargo_id: str) -> Optional[Dict]:
        """Obtiene un cargo por su ID."""
        doc = self.collection.find_one({"id": cargo_id})
        return self._serialize_id(doc) if doc else None
    
    async def get_by_responsabilidad(self, responsabilidad_id: str) -> Optional[Dict]:
        """
        Obtiene el cargo asociado a una responsabilidad.
        Retorna el más reciente si hay varios (aunque no debería).
        """
        doc = self.collection.find_one(
            {"responsabilidad_id": responsabilidad_id},
            sort=[("fecha_propuesta", -1)]
        )
        return self._serialize_id(doc) if doc else None
    
    async def get_cargo_activo_por_responsabilidad(self, responsabilidad_id: str) -> Optional[Dict]:
        """
        Obtiene un cargo activo (no terminal) para una responsabilidad.
        Estados activos: PENDIENTE, AUTORIZADO, APLICADO
        """
        estados_activos = ["PENDIENTE", "AUTORIZADO", "APLICADO"]
        doc = self.collection.find_one({
            "responsabilidad_id": responsabilidad_id,
            "estatus_cargo": {"$in": estados_activos}
        })
        return self._serialize_id(doc) if doc else None
    
    async def actualizar_cargo(self, cargo_id: str, datos: Dict) -> Optional[Dict]:
        """Actualiza un cargo existente."""
        datos["fecha_actualizacion"] = datetime.now(timezone.utc)
        result = self.collection.find_one_and_update(
            {"id": cargo_id},
            {"$set": datos},
            return_document=True
        )
        return self._serialize_id(result) if result else None
    
    async def listar_con_filtros(
        self,
        estatus: Optional[str] = None,
        sucursal_id: Optional[str] = None,
        responsable_id: Optional[str] = None,
        workflow_id: Optional[str] = None,
        fecha_desde: Optional[datetime] = None,
        fecha_hasta: Optional[datetime] = None,
        skip: int = 0,
        limit: int = 50
    ) -> Dict:
        """Lista cargos con filtros opcionales."""
        filtro = {}
        
        if estatus:
            filtro["estatus_cargo"] = estatus
        if sucursal_id:
            filtro["sucursal_id"] = sucursal_id
        if responsable_id:
            filtro["responsable_id"] = responsable_id
        if workflow_id:
            filtro["workflow_id"] = workflow_id
        if fecha_desde:
            filtro["fecha_propuesta"] = {"$gte": fecha_desde}
        if fecha_hasta:
            if "fecha_propuesta" in filtro:
                filtro["fecha_propuesta"]["$lte"] = fecha_hasta
            else:
                filtro["fecha_propuesta"] = {"$lte": fecha_hasta}
        
        total = self.collection.count_documents(filtro)
        cursor = self.collection.find(filtro).sort("fecha_propuesta", -1).skip(skip).limit(limit)
        items = [self._serialize_id(doc) for doc in cursor]
        
        return {"total": total, "items": items}
    
    async def contar_por_estatus(self) -> Dict[str, int]:
        """Cuenta cargos agrupados por estatus."""
        pipeline = [
            {"$group": {"_id": "$estatus_cargo", "count": {"$sum": 1}}}
        ]
        result = list(self.collection.aggregate(pipeline))
        return {r["_id"]: r["count"] for r in result}
    
    async def obtener_metricas(self) -> Dict:
        """Obtiene métricas agregadas de cargos."""
        pipeline = [
            {
                "$group": {
                    "_id": None,
                    "total_cargos": {"$sum": 1},
                    "monto_total_propuesto": {"$sum": "$monto_responsabilidad"},
                    "monto_total_aplicado": {"$sum": "$monto_aplicado"},
                    "monto_total_revertido": {"$sum": "$monto_revertido"},
                }
            }
        ]
        result = list(self.collection.aggregate(pipeline))
        
        if result:
            return {
                "total_cargos": result[0].get("total_cargos", 0),
                "monto_total_propuesto": result[0].get("monto_total_propuesto", 0),
                "monto_total_aplicado": result[0].get("monto_total_aplicado", 0),
                "monto_total_revertido": result[0].get("monto_total_revertido", 0),
            }
        return {
            "total_cargos": 0,
            "monto_total_propuesto": 0,
            "monto_total_aplicado": 0,
            "monto_total_revertido": 0,
        }
    
    async def obtener_monto_autorizado_total(self) -> float:
        """Suma de montos de cargos en estado AUTORIZADO."""
        pipeline = [
            {"$match": {"estatus_cargo": "AUTORIZADO"}},
            {"$group": {"_id": None, "total": {"$sum": "$monto_responsabilidad"}}}
        ]
        result = list(self.collection.aggregate(pipeline))
        return result[0]["total"] if result else 0.0


class CargosLogRepository(BaseRepository):
    """Repository para la colección cargos_economicos_log (auditoría)."""
    
    def __init__(self, db):
        super().__init__(db, "cargos_economicos_log")
        self._ensure_indexes()
    
    def _ensure_indexes(self):
        """Crea índices necesarios para la colección de log."""
        try:
            self.collection.create_index("id", unique=True)
            self.collection.create_index("cargo_id")
            self.collection.create_index("usuario_id")
            self.collection.create_index("accion")
            self.collection.create_index([("fecha", -1)])
            # Índice compuesto para consultas frecuentes
            self.collection.create_index([("cargo_id", 1), ("fecha", -1)])
            logger.info("Índices de cargos_economicos_log verificados/creados")
        except Exception as e:
            logger.warning(f"Error creando índices de cargos_economicos_log: {e}")
    
    async def registrar_log(
        self,
        cargo_id: str,
        accion: str,
        estatus_anterior: str,
        estatus_nuevo: str,
        usuario_id: str,
        comentario: str,
        monto_al_momento: float,
        usuario_rol: Optional[str] = None,
        motivo_codigo: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> str:
        """
        Registra una entrada en el log de auditoría.
        
        Args:
            cargo_id: ID del cargo
            accion: Acción ejecutada
            estatus_anterior: Estatus antes de la acción
            estatus_nuevo: Estatus después de la acción
            usuario_id: Usuario que ejecutó
            comentario: Comentario/justificación
            monto_al_momento: Monto del cargo al momento de la acción
            usuario_rol: Rol del usuario
            motivo_codigo: Código de motivo predefinido
            ip_address: IP del cliente
            user_agent: User-Agent del cliente
            
        Returns:
            ID del registro de log
        """
        log_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)
        
        documento = {
            "id": log_id,
            "cargo_id": cargo_id,
            "accion": accion,
            "estatus_anterior": estatus_anterior,
            "estatus_nuevo": estatus_nuevo,
            "usuario_id": usuario_id,
            "usuario_rol": usuario_rol,
            "comentario": comentario,
            "motivo_codigo": motivo_codigo,
            "monto_al_momento": monto_al_momento,
            "fecha": now,
            "ip_address": ip_address,
            "user_agent": user_agent,
        }
        
        self.collection.insert_one(documento)
        logger.info(f"Log de cargo registrado: {accion} sobre cargo {cargo_id}")
        return log_id
    
    async def get_by_cargo(self, cargo_id: str, limit: int = 100) -> List[Dict]:
        """Obtiene el historial de logs de un cargo."""
        cursor = self.collection.find(
            {"cargo_id": cargo_id}
        ).sort("fecha", -1).limit(limit)
        return [self._serialize_id(doc) for doc in cursor]
    
    async def get_ultimos_logs(self, limit: int = 50) -> List[Dict]:
        """Obtiene los últimos logs del sistema."""
        cursor = self.collection.find().sort("fecha", -1).limit(limit)
        return [self._serialize_id(doc) for doc in cursor]
    
    async def contar_acciones_por_usuario(self, usuario_id: str) -> Dict[str, int]:
        """Cuenta las acciones realizadas por un usuario."""
        pipeline = [
            {"$match": {"usuario_id": usuario_id}},
            {"$group": {"_id": "$accion", "count": {"$sum": 1}}}
        ]
        result = list(self.collection.aggregate(pipeline))
        return {r["_id"]: r["count"] for r in result}
