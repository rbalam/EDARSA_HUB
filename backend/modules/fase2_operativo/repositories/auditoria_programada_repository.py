"""
Repository para Auditorías Programadas
EDARSA HUB - Módulo Auditorías Programadas

Gestiona acceso a:
- auditorias_programadas
- auditorias_programadas_log

NOTA: Usa PyMongo sync para compatibilidad con el módulo.
"""
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone, timedelta
from .base_repository import BaseRepository


class AuditoriaProgramadaRepository(BaseRepository):
    """Repository para auditorías programadas."""
    
    def __init__(self, db):
        super().__init__(db, "auditorias_programadas")
        self.log_collection = db["auditorias_programadas_log"]
    
    # Override sync versions of BaseRepository methods
    def create(self, data: Dict) -> Dict:
        """Crea un nuevo documento (sync)."""
        from datetime import datetime, timezone
        data["fecha_creacion"] = datetime.now(timezone.utc)
        data["fecha_ultima_actualizacion"] = datetime.now(timezone.utc)
        self.collection.insert_one(data)
        if "_id" in data:
            del data["_id"]
        return data
    
    def get_by_id(self, id: str) -> Optional[Dict]:
        """Obtiene por ID usando campo 'id' (no _id)."""
        doc = self.collection.find_one({"id": id}, {"_id": 0})
        return doc
    
    def get_all(self) -> List[Dict]:
        """Obtiene todas las auditorías."""
        cursor = self.collection.find({}, {"_id": 0})
        return list(cursor)
    
    def update(self, id: str, data: Dict) -> Dict:
        """Actualiza un documento (sync)."""
        from datetime import datetime, timezone
        data["fecha_ultima_actualizacion"] = datetime.now(timezone.utc)
        self.collection.update_one({"id": id}, {"$set": data})
        return self.get_by_id(id)
    
    def delete(self, id: str) -> bool:
        """Elimina un documento (sync)."""
        result = self.collection.delete_one({"id": id})
        return result.deleted_count > 0
    
    # =========================================================================
    # CRUD AUDITORÍAS PROGRAMADAS
    # =========================================================================
    
    def get_activas(self) -> List[Dict]:
        """Obtiene todas las auditorías activas."""
        cursor = self.collection.find(
            {"activo": True},
            {"_id": 0}
        ).sort("proxima_ejecucion", 1)
        return list(cursor)
    
    def get_by_sucursal(self, sucursal_id: str) -> List[Dict]:
        """Obtiene auditorías de una sucursal."""
        cursor = self.collection.find(
            {"sucursal_id": sucursal_id},
            {"_id": 0}
        ).sort("nombre", 1)
        return list(cursor)
    
    def get_pendientes_ejecucion(self, hasta: datetime) -> List[Dict]:
        """
        Obtiene auditorías cuya próxima ejecución es <= hasta.
        Solo activas y con proxima_ejecucion definida.
        """
        cursor = self.collection.find(
            {
                "activo": True,
                "proxima_ejecucion": {"$lte": hasta.isoformat()}
            },
            {"_id": 0}
        )
        return list(cursor)
    
    def get_proximas_24h(self) -> List[Dict]:
        """Obtiene auditorías programadas para las próximas 24 horas."""
        ahora = datetime.now(timezone.utc)
        en_24h = ahora + timedelta(hours=24)
        
        cursor = self.collection.find(
            {
                "activo": True,
                "proxima_ejecucion": {
                    "$gte": ahora.isoformat(),
                    "$lte": en_24h.isoformat()
                }
            },
            {"_id": 0}
        ).sort("proxima_ejecucion", 1)
        return list(cursor)
    
    def actualizar_ejecucion(
        self,
        auditoria_id: str,
        estado: str,
        proxima: Optional[datetime] = None
    ) -> bool:
        """Actualiza estado de última ejecución y próxima."""
        update_data = {
            "ultima_ejecucion": datetime.now(timezone.utc).isoformat(),
            "ultima_ejecucion_status": estado,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        if proxima:
            update_data["proxima_ejecucion"] = proxima.isoformat()
        
        result = self.collection.update_one(
            {"id": auditoria_id},
            {"$set": update_data}
        )
        return result.modified_count > 0
    
    def activar(self, auditoria_id: str) -> bool:
        """Activa una auditoría programada."""
        result = self.collection.update_one(
            {"id": auditoria_id},
            {"$set": {
                "activo": True,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        return result.modified_count > 0
    
    def desactivar(self, auditoria_id: str) -> bool:
        """Desactiva una auditoría programada."""
        result = self.collection.update_one(
            {"id": auditoria_id},
            {"$set": {
                "activo": False,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        return result.modified_count > 0
    
    def contar_por_estado(self) -> Dict[str, int]:
        """Cuenta auditorías por estado activo/inactivo."""
        pipeline = [
            {"$group": {
                "_id": "$activo",
                "count": {"$sum": 1}
            }}
        ]
        cursor = self.collection.aggregate(pipeline)
        
        result = {"activas": 0, "inactivas": 0}
        for doc in cursor:
            if doc["_id"]:
                result["activas"] = doc["count"]
            else:
                result["inactivas"] = doc["count"]
        return result
    
    def get_calendario(self, anio: int, mes: int) -> List[Dict]:
        """
        Obtiene auditorías para un mes específico (vista calendario).
        """
        # Calcular rango del mes
        inicio_mes = datetime(anio, mes, 1, tzinfo=timezone.utc)
        if mes == 12:
            fin_mes = datetime(anio + 1, 1, 1, tzinfo=timezone.utc)
        else:
            fin_mes = datetime(anio, mes + 1, 1, tzinfo=timezone.utc)
        
        cursor = self.collection.find(
            {
                "activo": True,
                "proxima_ejecucion": {
                    "$gte": inicio_mes.isoformat(),
                    "$lt": fin_mes.isoformat()
                }
            },
            {"_id": 0}
        ).sort("proxima_ejecucion", 1)
        return list(cursor)
    
    # =========================================================================
    # LOG DE EJECUCIONES
    # =========================================================================
    
    def crear_log(self, log_data: Dict) -> Dict:
        """Crea un registro de ejecución."""
        self.log_collection.insert_one(log_data)
        return log_data
    
    def get_logs(
        self,
        auditoria_id: Optional[str] = None,
        estado: Optional[str] = None,
        desde: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Dict]:
        """Obtiene logs de ejecución con filtros."""
        filtro = {}
        
        if auditoria_id:
            filtro["auditoria_programada_id"] = auditoria_id
        if estado:
            filtro["estado"] = estado
        if desde:
            filtro["fecha_ejecucion"] = {"$gte": desde.isoformat()}
        
        cursor = self.log_collection.find(
            filtro,
            {"_id": 0}
        ).sort("fecha_ejecucion", -1).limit(limit)
        return list(cursor)
    
    def verificar_ejecucion_duplicada(
        self,
        auditoria_id: str,
        fecha_programada: datetime,
        ventana_minutos: int = 60
    ) -> bool:
        """
        Verifica si ya existe una ejecución para esta auditoría
        dentro de la ventana de tiempo (idempotencia).
        """
        inicio_ventana = fecha_programada - timedelta(minutes=ventana_minutos)
        fin_ventana = fecha_programada + timedelta(minutes=ventana_minutos)
        
        existente = self.log_collection.find_one({
            "auditoria_programada_id": auditoria_id,
            "fecha_programada": {
                "$gte": inicio_ventana.isoformat(),
                "$lte": fin_ventana.isoformat()
            },
            "estado": {"$in": ["COMPLETADA", "EN_PROGRESO"]}
        })
        return existente is not None
    
    def contar_logs_mes(self, anio: int, mes: int) -> Dict[str, int]:
        """Cuenta ejecuciones por estado en un mes."""
        inicio_mes = datetime(anio, mes, 1, tzinfo=timezone.utc)
        if mes == 12:
            fin_mes = datetime(anio + 1, 1, 1, tzinfo=timezone.utc)
        else:
            fin_mes = datetime(anio, mes + 1, 1, tzinfo=timezone.utc)
        
        pipeline = [
            {"$match": {
                "fecha_ejecucion": {
                    "$gte": inicio_mes.isoformat(),
                    "$lt": fin_mes.isoformat()
                }
            }},
            {"$group": {
                "_id": "$estado",
                "count": {"$sum": 1}
            }}
        ]
        
        cursor = self.log_collection.aggregate(pipeline)
        result = {"COMPLETADA": 0, "FALLIDA": 0, "OMITIDA": 0, "EN_PROGRESO": 0}
        for doc in cursor:
            if doc["_id"] in result:
                result[doc["_id"]] = doc["count"]
        return result
    
    # =========================================================================
    # ÍNDICES
    # =========================================================================
    
    def ensure_indexes(self):
        """Crea índices necesarios."""
        # Auditorías programadas
        self.collection.create_index("sucursal_id")
        self.collection.create_index("activo")
        self.collection.create_index("proxima_ejecucion")
        self.collection.create_index([("activo", 1), ("proxima_ejecucion", 1)])
        
        # Log
        self.log_collection.create_index("auditoria_programada_id")
        self.log_collection.create_index("fecha_ejecucion")
        self.log_collection.create_index("estado")
        self.log_collection.create_index(
            [("auditoria_programada_id", 1), ("fecha_programada", 1)]
        )
