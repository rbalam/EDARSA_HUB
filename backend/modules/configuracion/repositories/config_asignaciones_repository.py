import os
from core.unidades_service import UnidadesService
from core.corporate_filters.service import CorporateFilterService
"""
Repositorio para Configuración de Asignaciones de Responsables
==============================================================

MIGRADO A SQL SERVER (Mayo 2026)
================================
Este repositorio ahora usa SQL Server (EDARSAHUB) como fuente principal.
Las operaciones legacy de MongoDB pasan por StubDatabase sin fallar.

Gestiona la matriz: UNIDAD DE NEGOCIO + ALMACÉN → USUARIO RESPONSABLE

Fecha: Mayo 2026
"""

from typing import Optional, Dict, List, Any
from datetime import datetime, timezone
import logging
import uuid
import asyncio
from concurrent.futures import ThreadPoolExecutor
from core.sql_first.db import get_sql_connection

logger = logging.getLogger(__name__)

# Configuración EDARSAHUB
EDARSAHUB_CONFIG = {
    'host': os.getenv('EDARSAHUB_SQL_HOST'),
    'port': 1433,
    'database': 'EDARSAHUB',
    'username': os.getenv('EDARSAHUB_SQL_USER'),
    'password': os.getenv('EDARSAHUB_SQL_PASSWORD')
}


def _get_sql_connection():
    """Obtiene conexión a EDARSAHUB."""
    import pymssql
    return get_sql_connection()


def _execute_sql(query: str, params: tuple = None, fetch: bool = True) -> List[Dict]:
    """Ejecuta query SQL de forma síncrona."""
    try:
        conn = _get_sql_connection()
        cursor = conn.cursor(as_dict=True)
        
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        
        if fetch:
            results = list(cursor.fetchall())
        else:
            conn.commit()
            results = []
        
        cursor.close()
        conn.close()
        return results
        
    except Exception as e:
        logger.error(f"[CONFIG_ASIG_SQL] Error: {e}")
        return []


async def _execute_sql_async(query: str, params: tuple = None, fetch: bool = True) -> List[Dict]:
    """Ejecuta query SQL de forma asíncrona."""
    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor() as executor:
        return await loop.run_in_executor(
            executor,
            lambda: _execute_sql(query, params, fetch)
        )


class ConfigAsignacionesRepository:
    """
    Repositorio para gestionar configuraciones de asignación de responsables.
    
    MIGRACIÓN SQL SERVER (Mayo 2026):
    - Todas las operaciones de persistencia usan SQL Server
    - El parámetro `db` se mantiene por compatibilidad pero NO se usa
    - Usa tabla Config_Asignaciones en EDARSAHUB
    """
    
    def __init__(self, db):
        # db ya no se usa - mantenido por compatibilidad
        self._db_legacy = db
        logger.info("[CONFIG_ASIG] Inicializado con SQL Server")
    
    # =========================================================================
    # CRUD - CONFIGURACIONES DE ASIGNACIÓN
    # =========================================================================
    
    async def listar(
        self,
        unidad_negocio_pk: Optional[str] = None,
        activa: Optional[bool] = None,
        skip: int = 0,
        limit: int = 50
    ) -> Dict[str, Any]:
        """
        Lista configuraciones de asignación desde SQL Server.
        """
        where_clauses = ["1=1"]
        params = []
        
        if unidad_negocio_pk:
            where_clauses.append("UnidadNegocioID = %s")
            params.append(unidad_negocio_pk)
        if activa is not None:
            where_clauses.append("Activa = %s")
            params.append(1 if activa else 0)
        
        where_sql = " AND ".join(where_clauses)
        
        # Contar total
        count_query = f"SELECT COUNT(*) as total FROM Config_Asignaciones WHERE {where_sql}"
        count_result = await _execute_sql_async(count_query, tuple(params) if params else None)
        total = count_result[0]['total'] if count_result else 0
        
        # Obtener datos
        data_query = f"""
            SELECT 
                ConfigID as id,
                UnidadNegocioID as unidad_negocio_pk,
                UnidadNegocioID as unidad_negocio_id,
                UnidadNegocioNombre as unidad_negocio_nombre,
                AlmacenID as almacen_id,
                AlmacenNombre as almacen_nombre,
                UsuarioResponsableID as usuario_responsable_id,
                UsuarioResponsableNombre as usuario_responsable_nombre,
                UsuarioResponsableEmail as usuario_responsable_email,
                Activa as activa,
                Prioridad as prioridad,
                FechaCreacion as fecha_creacion,
                UsuarioCreacion as usuario_creacion,
                FechaModificacion as fecha_modificacion,
                UsuarioModificacion as usuario_modificacion
            FROM Config_Asignaciones
            WHERE {where_sql}
            ORDER BY UnidadNegocioNombre, Prioridad DESC
            OFFSET %s ROWS FETCH NEXT %s ROWS ONLY
        """
        params.extend([skip, limit])
        
        data = await _execute_sql_async(data_query, tuple(params))
        
        # Convertir Activa de bit a bool
        for row in data:
            row['activa'] = bool(row.get('activa', False))
        
        return {"data": data, "total": total}
    
    async def obtener_por_id(self, config_id: str) -> Optional[Dict]:
        """Obtiene una configuración por su ID."""
        query = """
            SELECT 
                ConfigID as id,
                UnidadNegocioID as unidad_negocio_pk,
                UnidadNegocioID as unidad_negocio_id,
                UnidadNegocioNombre as unidad_negocio_nombre,
                AlmacenID as almacen_id,
                AlmacenNombre as almacen_nombre,
                UsuarioResponsableID as usuario_responsable_id,
                UsuarioResponsableNombre as usuario_responsable_nombre,
                UsuarioResponsableEmail as usuario_responsable_email,
                Activa as activa,
                Prioridad as prioridad
            FROM Config_Asignaciones
            WHERE ConfigID = %s
        """
        rows = await _execute_sql_async(query, (config_id,))
        if rows:
            rows[0]['activa'] = bool(rows[0].get('activa', False))
            return rows[0]
        return None
    
    async def crear(
        self,
        unidad_negocio_pk: str,
        almacen_id: str,
        usuario_responsable_id: str,
        usuario_creacion: str,
        unidad_negocio_nombre: str = "",
        server_id: str = ""
    ) -> Dict[str, Any]:
        """
        Crea una nueva configuración de asignación en SQL Server.
        El nombre de la unidad y server_id se resuelven en la ruta (espacio de
        IDs EmpresaMongoUUID) y se reciben como parámetros.
        """
        # 1. Verificar que no existe duplicado
        check_query = """
            SELECT ConfigID FROM Config_Asignaciones
            WHERE UnidadNegocioID = %s AND AlmacenID = %s
        """
        existente = await _execute_sql_async(check_query, (unidad_negocio_pk, almacen_id or ''))
        if existente:
            raise ValueError("Ya existe configuración para esta combinación")
        
        empresa = {"nombre": unidad_negocio_nombre or unidad_negocio_pk, "server_id": server_id}
        
        # 2. Obtener datos del usuario responsable (tabla canónica: Usuario_Catalogo)
        usuario = await self.obtener_usuario(usuario_responsable_id) or {
            "id": usuario_responsable_id, "name": "", "email": ""
        }
        
        # 4. Calcular prioridad
        prioridad = 20 if almacen_id else 10
        
        # 5. Crear registro
        config_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
        
        insert_query = """
            INSERT INTO Config_Asignaciones (
                ConfigID, UnidadNegocioID, UnidadNegocioNombre,
                AlmacenID, AlmacenNombre,
                UsuarioResponsableID, UsuarioResponsableNombre, UsuarioResponsableEmail,
                ServerID, Activa, Prioridad,
                FechaCreacion, UsuarioCreacion, FechaModificacion, UsuarioModificacion
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, 1, %s, %s, %s, %s, %s
            )
        """
        params = (
            config_id, unidad_negocio_pk, empresa.get('nombre', ''),
            almacen_id or '', '',  # almacen_nombre se dejará vacío por ahora
            usuario_responsable_id, usuario.get('name', ''), usuario.get('email', ''),
            empresa.get('server_id', ''),
            prioridad,
            now, usuario_creacion, now, usuario_creacion
        )
        
        await _execute_sql_async(insert_query, params, fetch=False)
        
        logger.info(f"Config asignación creada: {config_id}")
        
        return await self.obtener_por_id(config_id)
    
    async def actualizar(
        self,
        config_id: str,
        unidad_negocio_pk: Optional[str] = None,
        almacen_id: Optional[str] = None,
        usuario_responsable_id: Optional[str] = None,
        activa: Optional[bool] = None,
        usuario_modificacion: str = None
    ) -> Optional[Dict]:
        """
        Actualiza una configuración existente en SQL Server.
        """
        config = await self.obtener_por_id(config_id)
        if not config:
            return None
        
        updates = []
        params = []
        
        if unidad_negocio_pk is not None:
            updates.append("UnidadNegocioID = %s")
            params.append(unidad_negocio_pk)
        
        if almacen_id is not None:
            updates.append("AlmacenID = %s")
            params.append(almacen_id)
        
        if usuario_responsable_id is not None:
            # Obtener datos del usuario (tabla canónica: Usuario_Catalogo)
            usuario = await self.obtener_usuario(usuario_responsable_id) or {"name": "", "email": ""}
            
            updates.append("UsuarioResponsableID = %s")
            params.append(usuario_responsable_id)
            updates.append("UsuarioResponsableNombre = %s")
            params.append(usuario.get('name', ''))
            updates.append("UsuarioResponsableEmail = %s")
            params.append(usuario.get('email', ''))
        
        if activa is not None:
            updates.append("Activa = %s")
            params.append(1 if activa else 0)
        
        if usuario_modificacion:
            updates.append("UsuarioModificacion = %s")
            params.append(usuario_modificacion)
        
        updates.append("FechaModificacion = GETUTCDATE()")
        
        if updates:
            query = f"UPDATE Config_Asignaciones SET {', '.join(updates)} WHERE ConfigID = %s"
            params.append(config_id)
            await _execute_sql_async(query, tuple(params), fetch=False)
        
        logger.info(f"Config asignación actualizada: {config_id}")
        return await self.obtener_por_id(config_id)
    
    async def eliminar(self, config_id: str) -> bool:
        """Elimina una configuración."""
        query = "DELETE FROM Config_Asignaciones WHERE ConfigID = %s"
        await _execute_sql_async(query, (config_id,), fetch=False)
        logger.info(f"Config asignación eliminada: {config_id}")
        return True

    # =========================================================================
    # VALIDACIONES SQL (reemplazan validaciones legacy MongoDB)
    # =========================================================================

    async def obtener_usuario(self, usuario_id: str) -> Optional[Dict]:
        """
        Obtiene un usuario desde la tabla canónica Usuario_Catalogo.
        Acepta UsuarioID (int), MongoLegacyID o PublicUUID.
        Retorna dict con id, name, email, activo o None si no existe.
        """
        query = """
            SELECT
                CAST(UsuarioID AS VARCHAR(50)) as id,
                NombreCompleto as name,
                Email as email,
                Activo as activo
            FROM Usuario_Catalogo
            WHERE CAST(UsuarioID AS VARCHAR(50)) = %s
               OR MongoLegacyID = %s
               OR CAST(PublicUUID AS VARCHAR(50)) = %s
        """
        uid = str(usuario_id)
        rows = await _execute_sql_async(query, (uid, uid, uid))
        if rows:
            rows[0]['activo'] = bool(rows[0].get('activo', True))
            return rows[0]
        return None

    async def existe_duplicado(
        self,
        unidad_negocio_pk: str,
        almacen_id: str,
        usuario_responsable_id: str,
        excluir_config_id: Optional[str] = None
    ) -> bool:
        """
        Verifica si ya existe otra asignación con la misma combinación
        Unidad/Almacén/Usuario (excluyendo opcionalmente un ConfigID).
        """
        query = """
            SELECT TOP 1 ConfigID FROM Config_Asignaciones
            WHERE UnidadNegocioID = %s
              AND AlmacenID = %s
              AND UsuarioResponsableID = %s
        """
        params = [unidad_negocio_pk, almacen_id or '', usuario_responsable_id]
        if excluir_config_id:
            query += " AND ConfigID <> %s"
            params.append(excluir_config_id)
        rows = await _execute_sql_async(query, tuple(params))
        return bool(rows)

    
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
        USADO POR EL ORQUESTADOR.
        """
        query = """
            SELECT TOP 1
                UsuarioResponsableID as ID,
                UsuarioResponsableNombre as nombre,
                UsuarioResponsableEmail as email,
                ConfigID as config_id
            FROM Config_Asignaciones
            WHERE ServerID = %s
              AND (AlmacenID = %s OR AlmacenID = '')
              AND Activa = 1
            ORDER BY 
                CASE WHEN AlmacenID = %s THEN 0 ELSE 1 END,
                Prioridad DESC
        """
        rows = await _execute_sql_async(query, (server_id, almacen_id, almacen_id))
        return rows[0] if rows else None
    
    # =========================================================================
    # CATÁLOGO DE ALMACENES
    # =========================================================================
    
    async def listar_almacenes(self, unidad_negocio_pk: str) -> List[Dict]:
        """Lista almacenes canonicos de una unidad desde EDARSAHUB SQL."""
        resultado = [{"id": "", "nombre": "(Todos los almacenes)", "source": "EDARSAHUB_SQL"}]
        query = """
            WITH inventarios_unidad AS (
                SELECT DISTINCT
                    LTRIM(RTRIM(almacen_id)) AS almacen_id,
                    UPPER(LTRIM(RTRIM(almacen))) AS almacen
                FROM dbo.Compras_Inventarios_Fisicos_Sync
                WHERE unidad_negocio_id = %s
                  AND sync_status IN ('ACTIVE', 'REPLACED')
                  AND NULLIF(LTRIM(RTRIM(almacen_id)), '') IS NOT NULL
            ), candidatos AS (
                SELECT a.SucursalID, COUNT_BIG(*) AS coincidencias
                FROM dbo.Inventario_Almacenes a
                INNER JOIN inventarios_unidad i
                    ON LTRIM(RTRIM(a.CodigoAlmacen)) = i.almacen_id
                   AND UPPER(LTRIM(RTRIM(a.NombreAlmacen))) = i.almacen
                GROUP BY a.SucursalID
            ), sucursal_canonica AS (
                SELECT TOP (1) SucursalID
                FROM candidatos
                ORDER BY coincidencias DESC, SucursalID
            )
            SELECT
                LTRIM(RTRIM(a.CodigoAlmacen)) AS id,
                LTRIM(RTRIM(a.CodigoAlmacen)) AS almacen_id,
                LTRIM(RTRIM(a.NombreAlmacen)) AS nombre,
                LTRIM(RTRIM(a.NombreAlmacen)) AS almacen,
                a.TipoAlmacen AS tipo_almacen,
                'EDARSAHUB_SQL' AS source
            FROM dbo.Inventario_Almacenes a
            INNER JOIN sucursal_canonica s ON s.SucursalID = a.SucursalID
            WHERE a.Activo = 1
            ORDER BY a.NombreAlmacen, a.CodigoAlmacen
        """
        try:
            resultado.extend(await _execute_sql_async(query, (unidad_negocio_pk,)))
        except Exception as e:
            logger.error(f"[CONFIG_ASIG] Error listando almacenes canonicos: {e}")
        return resultado
    
    async def sincronizar_almacenes_unidad(
        self,
        unidad_negocio_pk: str,
        almacenes: List[Dict],
        usuario_sync: str = "SISTEMA"
    ) -> int:
        """
        Sincroniza almacenes - operación placeholder.
        En modo SQL-only, esta operación no persiste en MongoDB.
        """
        logger.info(f"[CONFIG_ASIG] Sincronización de almacenes omitida (SQL-only mode)")
        return len(almacenes)
    
    # =========================================================================
    # ÍNDICES (no aplica en SQL Server - ya están creados)
    # =========================================================================
    
    async def ensure_indexes(self):
        """No aplica en SQL Server - índices ya creados en schema."""
        logger.debug("[CONFIG_ASIG] ensure_indexes: No aplica en SQL Server")


# Factory function
def get_config_asignaciones_repository(db) -> ConfigAsignacionesRepository:
    """Factory function para obtener instancia del repositorio."""
    return ConfigAsignacionesRepository(db)
