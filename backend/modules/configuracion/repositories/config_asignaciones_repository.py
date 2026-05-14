"""
Repositorio para Configuración de Asignaciones de Responsables
==============================================================

Gestiona la matriz: UNIDAD DE NEGOCIO + ALMACÉN → USUARIO RESPONSABLE

PRINCIPIOS:
1. UI trabaja con conceptos de negocio (unidad, almacén, usuario)
2. Backend resuelve internamente los identificadores técnicos (server_id, sucursal_id)
3. Almacenes se sirven desde catálogo local (NO consulta SQL en tiempo real)

Fecha: Abril 2026
"""

from typing import Optional, Dict, List, Any
from datetime import datetime, timezone
import logging
import uuid

logger = logging.getLogger(__name__)


class ConfigAsignacionesRepository:
    """Repositorio para gestionar configuraciones de asignación de responsables."""
    
    def __init__(self, db):
        self.db = db
        self.collection = db.config_asignaciones
        self.almacenes_collection = db.almacenes_catalogo
    
    # =========================================================================
    # CRUD - CONFIGURACIONES DE ASIGNACIÓN
    # =========================================================================
    
    async def listar(
        self,
        unidad_negocio_id: Optional[str] = None,
        activa: Optional[bool] = None,
        skip: int = 0,
        limit: int = 50
    ) -> Dict[str, Any]:
        """
        Lista configuraciones de asignación.
        
        Args:
            unidad_negocio_id: Filtrar por unidad de negocio
            activa: Filtrar por estado
            skip: Offset para paginación
            limit: Límite de resultados
            
        Returns:
            {data: [...], total: int}
        """
        filtro = {}
        if unidad_negocio_id:
            filtro["unidad_negocio_id"] = unidad_negocio_id
        if activa is not None:
            filtro["activa"] = activa
        
        # Contar total
        total = await self.collection.count_documents(filtro)
        
        # Obtener datos (sin campos técnicos internos)
        cursor = self.collection.find(
            filtro,
            {
                "_id": 0,
                "server_id": 0,      # NO exponer
                "sucursal_id": 0     # NO exponer
            }
        ).sort([
            ("unidad_negocio_nombre", 1),
            ("prioridad", -1)
        ]).skip(skip).limit(limit)
        
        data = await cursor.to_list(length=limit)
        
        return {"data": data, "total": total}
    
    async def obtener_por_id(self, config_id: str) -> Optional[Dict]:
        """Obtiene una configuración por su ID (sin campos técnicos)."""
        return await self.collection.find_one(
            {"id": config_id},
            {
                "_id": 0,
                "server_id": 0,
                "sucursal_id": 0
            }
        )
    
    async def crear(
        self,
        unidad_negocio_id: str,
        almacen_id: str,
        usuario_responsable_id: str,
        usuario_creacion: str
    ) -> Dict[str, Any]:
        """
        Crea una nueva configuración de asignación.
        
        Resuelve internamente:
        - server_id desde la unidad de negocio
        - sucursal_id desde la unidad de negocio
        - prioridad según especificidad
        
        Args:
            unidad_negocio_id: ID de la empresa/unidad
            almacen_id: ID del almacén ("" para todos)
            usuario_responsable_id: ID del usuario responsable
            usuario_creacion: Email del usuario que crea
            
        Returns:
            Configuración creada (sin campos técnicos)
            
        Raises:
            ValueError: Si ya existe o datos inválidos
        """
        # 1. Verificar que no existe duplicado
        existente = await self.collection.find_one({
            "unidad_negocio_id": unidad_negocio_id,
            "almacen_id": almacen_id
        })
        if existente:
            raise ValueError("Ya existe configuración para esta combinación")
        
        # 2. Obtener datos de la unidad de negocio
        empresa = await self.db.empresas.find_one(
            {"id": unidad_negocio_id, "activa": True},
            {"_id": 0}
        )
        if not empresa:
            raise ValueError("Unidad de negocio no encontrada o inactiva")
        
        # 3. Resolver server_id y sucursal_id desde sucursal_servidor_map
        sucursal = await self.db.sucursales_catalogo.find_one(
            {"empresa_id": unidad_negocio_id, "activa": True},
            {"_id": 0}
        )
        
        server_id = None
        sucursal_id = None
        
        if sucursal:
            mapeo = await self.db.sucursal_servidor_map.find_one(
                {"sucursal_id": sucursal["id"], "activo": True},
                {"_id": 0}
            )
            if mapeo:
                server_id = mapeo.get("server_id")
                sucursal_id = mapeo.get("sucursal_origen_id") or sucursal.get("codigo")
        
        # 4. Obtener datos del usuario responsable
        usuario = await self.db.users.find_one(
            {"id": usuario_responsable_id},
            {"_id": 0, "id": 1, "name": 1, "email": 1}
        )
        if not usuario:
            raise ValueError("Usuario responsable no encontrado")
        
        # 5. Obtener nombre del almacén si aplica
        almacen_nombre = ""
        if almacen_id:
            almacen = await self.almacenes_collection.find_one(
                {"id": almacen_id, "unidad_negocio_id": unidad_negocio_id},
                {"_id": 0, "nombre": 1}
            )
            almacen_nombre = almacen.get("nombre", almacen_id) if almacen else almacen_id
        
        # 6. Calcular prioridad
        prioridad = 20 if almacen_id else 10
        
        # 7. Crear documento
        now = datetime.now(timezone.utc).isoformat()
        config_id = str(uuid.uuid4())
        
        documento = {
            "id": config_id,
            # Campos funcionales (visibles en UI)
            "unidad_negocio_id": unidad_negocio_id,
            "unidad_negocio_nombre": empresa.get("nombre", ""),
            "almacen_id": almacen_id,
            "almacen_nombre": almacen_nombre,
            "usuario_responsable_id": usuario_responsable_id,
            "usuario_responsable_nombre": usuario.get("name", usuario.get("email", "")),
            "usuario_responsable_email": usuario.get("email", ""),
            "activa": True,
            "prioridad": prioridad,
            # Campos técnicos (internos, NO expuestos en API)
            "server_id": server_id,
            "sucursal_id": sucursal_id,
            # Auditoría
            "fecha_creacion": now,
            "usuario_creacion": usuario_creacion,
            "fecha_modificacion": now,
            "usuario_modificacion": usuario_creacion
        }
        
        await self.collection.insert_one(documento)
        
        # Retornar sin campos técnicos
        documento.pop("server_id", None)
        documento.pop("sucursal_id", None)
        documento.pop("_id", None)
        
        logger.info(f"Config asignación creada: {config_id} - {empresa.get('nombre')}/{almacen_nombre or '(todos)'} → {usuario.get('name')}")
        
        return documento
    
    async def actualizar(
        self,
        config_id: str,
        unidad_negocio_id: Optional[str] = None,
        almacen_id: Optional[str] = None,
        usuario_responsable_id: Optional[str] = None,
        activa: Optional[bool] = None,
        usuario_modificacion: str = None
    ) -> Optional[Dict]:
        """
        Actualiza una configuración existente.
        
        Permite cambiar:
        - unidad_negocio_id
        - almacen_id
        - usuario_responsable_id
        - activa
        """
        config = await self.collection.find_one({"id": config_id})
        if not config:
            return None
        
        actualizaciones = {
            "fecha_modificacion": datetime.now(timezone.utc).isoformat(),
            "usuario_modificacion": usuario_modificacion
        }
        
        # Actualizar unidad de negocio si cambia
        if unidad_negocio_id is not None and unidad_negocio_id != config.get("unidad_negocio_id"):
            empresa = await self.db.empresas.find_one(
                {"id": unidad_negocio_id, "activa": True},
                {"_id": 0, "id": 1, "nombre": 1, "server_id": 1}
            )
            if not empresa:
                raise ValueError("Unidad de negocio no encontrada")
            
            # Obtener server_id y sucursal_id
            server_id = empresa.get("server_id")
            sucursal_id = None
            if server_id:
                # FASE P1.4-F (Dic 2025): Migrado de MongoDB db.servers a server_registry
                # ANTES: server = await self.db.servers.find_one({"id": server_id}, {"_id": 0, "sucursal_origen_id": 1})
                from core.server_registry import get_server_by_id
                server = await get_server_by_id(server_id, db=self.db, mask_secrets=True)
                sucursal_id = server.get("sucursal_origen_id") if server else None
            
            actualizaciones["unidad_negocio_id"] = unidad_negocio_id
            actualizaciones["unidad_negocio_nombre"] = empresa.get("nombre", "")
            actualizaciones["server_id"] = server_id
            actualizaciones["sucursal_id"] = sucursal_id
        
        # Actualizar almacén si cambia
        if almacen_id is not None:
            unidad_para_almacen = unidad_negocio_id or config.get("unidad_negocio_id")
            if almacen_id:
                # Buscar nombre del almacén
                almacen = await self.db.almacenes_catalogo.find_one(
                    {"unidad_negocio_id": unidad_para_almacen, "id": almacen_id},
                    {"_id": 0, "nombre": 1}
                )
                actualizaciones["almacen_id"] = almacen_id
                actualizaciones["almacen_nombre"] = almacen.get("nombre", almacen_id) if almacen else almacen_id
            else:
                # Almacén vacío = todos
                actualizaciones["almacen_id"] = ""
                actualizaciones["almacen_nombre"] = ""
        
        if usuario_responsable_id is not None:
            # Validar y obtener datos del nuevo usuario
            usuario = await self.db.users.find_one(
                {"id": usuario_responsable_id},
                {"_id": 0, "id": 1, "name": 1, "email": 1}
            )
            if not usuario:
                raise ValueError("Usuario responsable no encontrado")
            
            actualizaciones["usuario_responsable_id"] = usuario_responsable_id
            actualizaciones["usuario_responsable_nombre"] = usuario.get("name", usuario.get("email", ""))
            actualizaciones["usuario_responsable_email"] = usuario.get("email", "")
        
        if activa is not None:
            actualizaciones["activa"] = activa
        
        await self.collection.update_one(
            {"id": config_id},
            {"$set": actualizaciones}
        )
        
        logger.info(f"Config asignación actualizada: {config_id}")
        
        return await self.obtener_por_id(config_id)
    
    async def eliminar(self, config_id: str) -> bool:
        """Elimina una configuración (eliminación física)."""
        result = await self.collection.delete_one({"id": config_id})
        if result.deleted_count > 0:
            logger.info(f"Config asignación eliminada: {config_id}")
            return True
        return False
    
    # =========================================================================
    # RESOLUCIÓN DE RESPONSABLE (usado por Orquestador)
    # =========================================================================
    
    async def resolver_responsable(
        self,
        server_id: str,
        almacen_id: str
    ) -> Optional[Dict]:
        """
        Resuelve el usuario responsable para una combinación server/almacén.
        
        USADO POR EL ORQUESTADOR (no por la UI).
        Busca por campos técnicos internos.
        
        Prioridad:
        1. server_id + almacen_id específico
        2. server_id + almacén vacío (todos)
        
        Args:
            server_id: ID del servidor (interno)
            almacen_id: ID del almacén
            
        Returns:
            {id, nombre, email, config_id} o None si no hay configuración
        """
        # Búsqueda ordenada por prioridad descendente
        configs = await self.collection.find({
            "server_id": server_id,
            "$or": [
                {"almacen_id": almacen_id},  # Específico
                {"almacen_id": ""}            # General
            ],
            "activa": True
        }).sort("prioridad", -1).to_list(1)
        
        if not configs:
            return None
        
        config = configs[0]
        
        return {
            "id": config["usuario_responsable_id"],
            "nombre": config["usuario_responsable_nombre"],
            "email": config.get("usuario_responsable_email", ""),
            "config_id": config["id"]
        }
    
    # =========================================================================
    # CATÁLOGO DE ALMACENES (fuente local)
    # =========================================================================
    
    async def listar_almacenes(self, unidad_negocio_id: str) -> List[Dict]:
        """
        Lista almacenes disponibles para una unidad de negocio.
        
        FUENTE: Catálogo local (almacenes_catalogo).
        NO consulta SQL externo en tiempo real.
        
        Args:
            unidad_negocio_id: ID de la empresa/unidad
            
        Returns:
            Lista con opción "(Todos)" + almacenes del catálogo local
        """
        # Siempre incluir opción "todos"
        resultado = [{"id": "", "nombre": "(Todos los almacenes)"}]
        
        # Obtener almacenes del catálogo local
        cursor = self.almacenes_collection.find(
            {"unidad_negocio_id": unidad_negocio_id, "activo": True},
            {"_id": 0, "id": 1, "nombre": 1, "codigo": 1}
        ).sort("nombre", 1)
        
        almacenes = await cursor.to_list(length=100)
        
        for alm in almacenes:
            resultado.append({
                "id": alm.get("id", alm.get("codigo", "")),
                "nombre": alm.get("nombre", "")
            })
        
        return resultado
    
    async def sincronizar_almacenes_unidad(
        self,
        unidad_negocio_id: str,
        almacenes: List[Dict],
        usuario_sync: str = "SISTEMA"
    ) -> int:
        """
        Sincroniza almacenes desde fuente externa al catálogo local.
        
        USADO POR: Job de sincronización o proceso manual.
        NO usado por la UI de configuración.
        
        Args:
            unidad_negocio_id: ID de la unidad
            almacenes: Lista de {id, nombre, codigo}
            usuario_sync: Usuario que ejecuta la sincronización
            
        Returns:
            Cantidad de almacenes sincronizados
        """
        now = datetime.now(timezone.utc).isoformat()
        count = 0
        
        for alm in almacenes:
            alm_id = str(alm.get("id", alm.get("codigo", "")))
            if not alm_id:
                continue
            
            await self.almacenes_collection.update_one(
                {
                    "unidad_negocio_id": unidad_negocio_id,
                    "id": alm_id
                },
                {
                    "$set": {
                        "nombre": alm.get("nombre", alm_id),
                        "codigo": alm.get("codigo", alm_id),
                        "activo": True,
                        "fecha_sync": now,
                        "usuario_sync": usuario_sync
                    },
                    "$setOnInsert": {
                        "id": alm_id,
                        "unidad_negocio_id": unidad_negocio_id,
                        "fecha_creacion": now
                    }
                },
                upsert=True
            )
            count += 1
        
        logger.info(f"Sincronizados {count} almacenes para unidad {unidad_negocio_id}")
        return count
    
    # =========================================================================
    # ÍNDICES
    # =========================================================================
    
    async def ensure_indexes(self):
        """Crea los índices necesarios."""
        # Índice único por clave funcional
        await self.collection.create_index(
            [("unidad_negocio_id", 1), ("almacen_id", 1)],
            unique=True,
            name="idx_unidad_almacen_unique"
        )
        
        # Índice para búsqueda del orquestador (por campos técnicos)
        await self.collection.create_index(
            [("server_id", 1), ("almacen_id", 1), ("activa", 1), ("prioridad", -1)],
            name="idx_resolver_responsable"
        )
        
        # Índice para almacenes
        await self.almacenes_collection.create_index(
            [("unidad_negocio_id", 1), ("id", 1)],
            unique=True,
            name="idx_almacen_unidad_unique"
        )
        
        logger.info("Índices de config_asignaciones creados")


# Factory function
def get_config_asignaciones_repository(db) -> ConfigAsignacionesRepository:
    """Factory function para obtener instancia del repositorio."""
    return ConfigAsignacionesRepository(db)
