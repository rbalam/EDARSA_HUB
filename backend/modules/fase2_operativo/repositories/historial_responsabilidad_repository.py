"""
Repositorio para responsabilidad_historial
CAB-003 | EDARSA HUB - Fase 2C.2

Gestiona el historial de transiciones de responsabilidad económica.
"""
from typing import Optional, List, Dict
from datetime import datetime, timezone
from .base_repository import BaseRepository


class HistorialResponsabilidadRepository(BaseRepository):
    """Repository para la colección responsabilidad_historial."""
    
    def __init__(self, db):
        super().__init__(db, "responsabilidad_historial")
        self._crear_indices()
    
    def _crear_indices(self):
        """Crea índices necesarios para la colección."""
        try:
            self.collection.create_index("responsabilidad_id", name="idx_responsabilidad_id")
            self.collection.create_index("fecha", name="idx_fecha")
            self.collection.create_index("usuario_id", name="idx_usuario_id")
            self.collection.create_index("accion", name="idx_accion")
        except Exception:
            pass  # Índices ya existen
    
    async def registrar_transicion(
        self,
        transicion_id: str,
        responsabilidad_id: str,
        accion: str,
        estado_anterior: str,
        estado_nuevo: str,
        usuario_id: str,
        usuario_rol: Optional[str],
        comentario: str,
        monto_al_momento: float,
        motivo_codigo: Optional[str] = None
    ) -> Dict:
        """
        Registra una transición de estado en el historial.
        
        Args:
            transicion_id: ID único de la transición
            responsabilidad_id: ID del registro de responsabilidad
            accion: Acción ejecutada (PROPONER, APROBAR, etc.)
            estado_anterior: Estado antes de la transición
            estado_nuevo: Estado después de la transición
            usuario_id: ID del usuario que ejecutó la acción
            usuario_rol: Rol del usuario
            comentario: Comentario obligatorio
            monto_al_momento: Monto propuesto al momento de la transición
            motivo_codigo: Código de motivo predefinido (opcional)
            
        Returns:
            Registro de historial creado
        """
        now = datetime.now(timezone.utc)
        
        documento = {
            "id": transicion_id,
            "responsabilidad_id": responsabilidad_id,
            "accion": accion,
            "estado_anterior": estado_anterior,
            "estado_nuevo": estado_nuevo,
            "usuario_id": usuario_id,
            "usuario_rol": usuario_rol,
            "comentario": comentario,
            "motivo_codigo": motivo_codigo,
            "monto_al_momento": monto_al_momento,
            "fecha": now,
            "fecha_creacion": now
        }
        
        self.collection.insert_one(documento)
        return self._serialize_id(documento)
    
    async def get_by_responsabilidad(
        self,
        responsabilidad_id: str,
        limit: int = 100
    ) -> List[Dict]:
        """
        Obtiene el historial de transiciones de una responsabilidad.
        
        Args:
            responsabilidad_id: ID del registro de responsabilidad
            limit: Límite de registros
            
        Returns:
            Lista de transiciones ordenadas por fecha descendente
        """
        cursor = self.collection.find(
            {"responsabilidad_id": responsabilidad_id}
        ).sort("fecha", -1).limit(limit)
        
        return [self._serialize_id(doc) for doc in cursor]
    
    async def get_ultima_transicion(self, responsabilidad_id: str) -> Optional[Dict]:
        """
        Obtiene la última transición de una responsabilidad.
        
        Args:
            responsabilidad_id: ID del registro de responsabilidad
            
        Returns:
            Última transición o None
        """
        doc = self.collection.find_one(
            {"responsabilidad_id": responsabilidad_id},
            sort=[("fecha", -1)]
        )
        return self._serialize_id(doc) if doc else None
    
    async def contar_transiciones(self, responsabilidad_id: str) -> int:
        """Cuenta las transiciones de una responsabilidad."""
        return self.collection.count_documents({"responsabilidad_id": responsabilidad_id})
    
    async def get_transiciones_por_usuario(
        self,
        usuario_id: str,
        fecha_desde: Optional[datetime] = None,
        fecha_hasta: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Dict]:
        """
        Obtiene transiciones realizadas por un usuario.
        
        Args:
            usuario_id: ID del usuario
            fecha_desde: Fecha inicial (opcional)
            fecha_hasta: Fecha final (opcional)
            limit: Límite de registros
            
        Returns:
            Lista de transiciones
        """
        filtro = {"usuario_id": usuario_id}
        
        if fecha_desde or fecha_hasta:
            filtro["fecha"] = {}
            if fecha_desde:
                filtro["fecha"]["$gte"] = fecha_desde
            if fecha_hasta:
                filtro["fecha"]["$lte"] = fecha_hasta
        
        cursor = self.collection.find(filtro).sort("fecha", -1).limit(limit)
        return [self._serialize_id(doc) for doc in cursor]
    
    async def get_estadisticas_acciones(self) -> Dict:
        """
        Obtiene estadísticas de acciones realizadas.
        
        Returns:
            Dict con conteos por acción
        """
        pipeline = [
            {
                "$group": {
                    "_id": "$accion",
                    "count": {"$sum": 1}
                }
            }
        ]
        
        result = list(self.collection.aggregate(pipeline))
        return {r["_id"]: r["count"] for r in result}
