"""
Repositorio para responsabilidad_economica
CAB-003 | EDARSA HUB - Fase 2C.1

Gestiona el acceso a datos de cálculos de impacto económico.
"""
from typing import Optional, List, Dict
from datetime import datetime, timezone
from .base_repository import BaseRepository


class ResponsabilidadRepository(BaseRepository):
    """Repository para la colección responsabilidad_economica."""
    
    def __init__(self, db):
        super().__init__(db, "responsabilidad_economica")
    
    async def get_by_workflow(self, workflow_id: str) -> Optional[Dict]:
        """
        Obtiene el cálculo de responsabilidad de un workflow.
        
        Args:
            workflow_id: ID del workflow
            
        Returns:
            Registro de responsabilidad o None si no existe
        """
        doc = self.collection.find_one({"workflow_id": workflow_id})
        return self._serialize_id(doc)
    
    async def existe_calculo(self, workflow_id: str) -> bool:
        """
        Verifica si ya existe un cálculo para el workflow.
        
        Args:
            workflow_id: ID del workflow
            
        Returns:
            True si existe, False si no
        """
        return self.collection.count_documents({"workflow_id": workflow_id}) > 0
    
    async def crear_calculo(self, data: Dict) -> Dict:
        """
        Crea un nuevo registro de responsabilidad económica.
        
        Args:
            data: Datos del cálculo
            
        Returns:
            Registro creado con ID
        """
        now = datetime.now(timezone.utc)
        data["fecha_creacion"] = now
        data["fecha_actualizacion"] = now
        
        return await self.create(data)
    
    async def actualizar_calculo(self, workflow_id: str, data: Dict) -> Optional[Dict]:
        """
        Actualiza un cálculo existente.
        
        Args:
            workflow_id: ID del workflow
            data: Datos a actualizar
            
        Returns:
            Registro actualizado o None si no existe
        """
        existente = await self.get_by_workflow(workflow_id)
        if not existente:
            return None
        
        data["fecha_actualizacion"] = datetime.now(timezone.utc)
        # Use _id (MongoDB ObjectId) for update, not id (UUID)
        result = self.collection.find_one_and_update(
            {"workflow_id": workflow_id},
            {"$set": data},
            return_document=True
        )
        return self._serialize_id(result)
    
    async def listar_por_sucursal(self, sucursal_id: str, skip: int = 0, limit: int = 50) -> List[Dict]:
        """
        Lista cálculos de responsabilidad por sucursal.
        
        Args:
            sucursal_id: ID de la sucursal
            skip: Registros a saltar
            limit: Límite de registros
            
        Returns:
            Lista de cálculos
        """
        return await self.get_all(
            filter_dict={"sucursal_id": sucursal_id},
            skip=skip,
            limit=limit,
            sort=[("fecha_calculo", -1)]
        )
    
    async def listar_por_estado(self, estado: str, skip: int = 0, limit: int = 50) -> List[Dict]:
        """
        Lista cálculos por estado.
        
        Args:
            estado: Estado a filtrar
            skip: Registros a saltar
            limit: Límite de registros
            
        Returns:
            Lista de cálculos
        """
        return await self.get_all(
            filter_dict={"estado": estado},
            skip=skip,
            limit=limit,
            sort=[("fecha_calculo", -1)]
        )
    
    async def listar_con_filtros(
        self,
        sucursal_id: Optional[str] = None,
        estado: Optional[str] = None,
        excede_minimo: Optional[bool] = None,
        fecha_desde: Optional[datetime] = None,
        fecha_hasta: Optional[datetime] = None,
        skip: int = 0,
        limit: int = 50
    ) -> Dict:
        """
        Lista cálculos con filtros combinados.
        
        Args:
            sucursal_id: Filtrar por sucursal
            estado: Filtrar por estado
            excede_minimo: Filtrar por si excede mínimo
            fecha_desde: Fecha inicial
            fecha_hasta: Fecha final
            skip: Registros a saltar
            limit: Límite de registros
            
        Returns:
            Dict con items y total
        """
        filtro = {}
        
        if sucursal_id:
            filtro["sucursal_id"] = sucursal_id
        
        if estado:
            filtro["estado"] = estado
        
        if excede_minimo is not None:
            filtro["excede_minimo"] = excede_minimo
        
        if fecha_desde or fecha_hasta:
            filtro["fecha_calculo"] = {}
            if fecha_desde:
                filtro["fecha_calculo"]["$gte"] = fecha_desde
            if fecha_hasta:
                filtro["fecha_calculo"]["$lte"] = fecha_hasta
        
        total = await self.count(filtro)
        items = await self.get_all(
            filters=filtro,
            skip=skip,
            limit=limit,
            sort=[("fecha_calculo", -1)]
        )
        
        return {"items": items, "total": total}
    
    async def obtener_metricas_globales(self) -> Dict:
        """
        Obtiene métricas globales de responsabilidad económica.
        
        Returns:
            Dict con métricas agregadas
        """
        pipeline = [
            {
                "$group": {
                    "_id": None,
                    "total_calculos": {"$sum": 1},
                    "total_monto_propuesto": {"$sum": "$monto_propuesto_mxn"},
                    "total_faltantes_valor": {"$sum": "$faltantes_valor_mxn"},
                    "total_sobrantes_valor": {"$sum": "$sobrantes_valor_mxn"},
                    "calculos_exceden_minimo": {
                        "$sum": {"$cond": ["$excede_minimo", 1, 0]}
                    }
                }
            }
        ]
        
        result = list(self.collection.aggregate(pipeline))
        
        if result:
            del result[0]["_id"]
            return result[0]
        
        return {
            "total_calculos": 0,
            "total_monto_propuesto": 0.0,
            "total_faltantes_valor": 0.0,
            "total_sobrantes_valor": 0.0,
            "calculos_exceden_minimo": 0
        }
    
    async def eliminar_por_workflow(self, workflow_id: str) -> bool:
        """
        Elimina el cálculo de un workflow (para rollback).
        
        Args:
            workflow_id: ID del workflow
            
        Returns:
            True si se eliminó, False si no existía
        """
        result = self.collection.delete_one({"workflow_id": workflow_id})
        return result.deleted_count > 0
