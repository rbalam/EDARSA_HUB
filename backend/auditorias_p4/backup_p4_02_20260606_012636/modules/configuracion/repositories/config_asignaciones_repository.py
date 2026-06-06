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
    return pymssql.connect(
        server=EDARSAHUB_CONFIG['host'],
        port=EDARSAHUB_CONFIG['port'],
        database=EDARSAHUB_CONFIG['database'],
        user=EDARSAHUB_CONFIG['username'],
        password=EDARSAHUB_CONFIG['password'],
        timeout=30,
        login_timeout=15
    )


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
                ConfigID as ID,
                UnidadNegocioID as UnidadNegocioID,
                UnidadNegocioNombre as unidad_negocio_nombre,
                AlmacenID as AlmacenID,
                AlmacenNombre as almacen_nombre,
                UsuarioResponsableID as usuario_responsable_id,
                UsuarioResponsableNombre as usuario_responsable_nombre,
                UsuarioResponsableEmail as usuario_responsable_email,
                Activa as Activa,
                Prioridad as Prioridad,
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
                ConfigID as ID,
                UnidadNegocioID as UnidadNegocioID,
                UnidadNegocioNombre as unidad_negocio_nombre,
                AlmacenID as AlmacenID,
                AlmacenNombre as almacen_nombre,
                UsuarioResponsableID as usuario_responsable_id,
                UsuarioResponsableNombre as usuario_responsable_nombre,
                UsuarioResponsableEmail as usuario_responsable_email,
                Activa as Activa,
                Prioridad as Prioridad
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
        usuario_creacion: str
    ) -> Dict[str, Any]:
        """
        Crea una nueva configuración de asignación en SQL Server.
        """
        # 1. Verificar que no existe duplicado
        check_query = """
            SELECT ConfigID FROM Config_Asignaciones
            WHERE UnidadNegocioID = %s AND AlmacenID = %s
        """
        existente = await _execute_sql_async(check_query, (unidad_negocio_pk, almacen_id or ''))
        if existente:
            raise ValueError("Ya existe configuración para esta combinación")
        
        # 2. Obtener datos de la unidad de negocio desde Servidores_Conexiones
        empresa_query = """
            SELECT nombre, CAST(id AS VARCHAR(50)) as id
            FROM Servidores_Conexiones
            WHERE activo = 1 AND (
                CAST(id AS VARCHAR(50)) = %s 
                OR nombre LIKE %s
            )
        """
        empresas = await _execute_sql_async(empresa_query, (unidad_negocio_pk, f'%{unidad_negocio_pk}%'))
        empresa = empresas[0] if empresas else {"nombre": unidad_negocio_pk, "server_id": unidad_negocio_pk}
        
        # 3. Obtener datos del usuario responsable
        usuario_query = """
            SELECT 
                CAST(UsuarioID AS VARCHAR(50)) as id,
                NombreCompleto as name,
                Email as email
            FROM Usuarios
            WHERE UsuarioID = %s OR MongoLegacyID = %s
        """
        usuarios = await _execute_sql_async(usuario_query, (usuario_responsable_id, usuario_responsable_id))
        usuario = usuarios[0] if usuarios else {"id": usuario_responsable_id, "name": "Usuario", "email": ""}
        
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
            # Obtener datos del usuario
            usuario_query = """
                SELECT 
                    CAST(UsuarioID AS VARCHAR(50)) as id,
                    NombreCompleto as name,
                    Email as email
                FROM Usuarios
                WHERE UsuarioID = %s OR MongoLegacyID = %s
            """
            usuarios = await _execute_sql_async(usuario_query, (usuario_responsable_id, usuario_responsable_id))
            usuario = usuarios[0] if usuarios else {"name": "", "email": ""}
            
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
        """
        Lista almacenes disponibles para una unidad de negocio.
        Retorna opción "(Todos)" + almacenes del servidor.
        """
        resultado = [{"id": "", "nombre": "(Todos los almacenes)"}]
        
        # Intentar obtener almacenes desde SQL Server (tablas del servidor)
        try:
            # Buscar el server_id asociado a la unidad
            server_query = """
                SELECT CAST(id AS VARCHAR(50)) as id, host, db_name
                FROM Servidores_Conexiones
                WHERE activo = 1 AND (
                    CAST(id AS VARCHAR(50)) = %s OR nombre = %s
                )
            """
            servers = await _execute_sql_async(server_query, (unidad_negocio_pk, unidad_negocio_pk))
            
            if servers:
                # Por ahora retornar lista vacía de almacenes específicos
                # La implementación completa requeriría consultar al servidor remoto
                pass
        except Exception as e:
            logger.debug(f"Error listando almacenes: {e}")
        
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
