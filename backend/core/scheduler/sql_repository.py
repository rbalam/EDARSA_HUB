import os
"""
EDARSA HUB - Scheduler SQL Repository
=====================================
Funciones SQL para los jobs del scheduler (reemplazo de MongoDB).

Tablas usadas:
- Scheduler_InventariosProcesados
- Scheduler_PedidosProcesados
- Scheduler_BitacoraJobs
- Servidores_Conexiones (lectura)

Autor: Agente E1
Fecha: Mayo 2026
"""

import logging
import json
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
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


def _decrypt_password_for_internal_use(password_value: str) -> str:
    """
    Devuelve el password usable por jobs internos.

    Servidores_Conexiones guarda password_encrypted para producción, pero algunos
    registros legacy aún pueden venir en texto plano. No se loguea el valor.
    """
    if not password_value:
        return ""

    encrypted = False
    try:
        from core.secret_manager import decrypt_secret, is_encrypted_secret

        encrypted = is_encrypted_secret(password_value)
        if encrypted:
            return decrypt_secret(password_value)
    except Exception as exc:
        logger.warning(
            "[SCHEDULER_SQL] No se pudo descifrar password de servidor externo: %s",
            type(exc).__name__,
        )
        if encrypted:
            return ""

    return password_value


def _execute_sql(query: str, params: tuple = None, fetch: bool = True) -> List[Dict]:
    """Ejecuta una query SQL de forma síncrona."""
    import pymssql
    
    try:
        conn = get_sql_connection()
        cursor = conn.cursor(as_dict=True)
        
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        
        if fetch:
            try:
                results = list(cursor.fetchall())
            except Exception:
                results = []
        else:
            conn.commit()
            results = []
        
        cursor.close()
        conn.close()
        return results
        
    except Exception as e:
        logger.error(f"[SCHEDULER_SQL] Error ejecutando query: {e}")
        return []


async def _execute_sql_async(query: str, params: tuple = None, fetch: bool = True) -> List[Dict]:
    """Ejecuta una query SQL de forma asíncrona."""
    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor() as executor:
        return await loop.run_in_executor(
            executor, 
            lambda: _execute_sql(query, params, fetch)
        )


# =============================================================================
# SERVIDORES (Lectura desde Servidores_Conexiones)
# =============================================================================

async def get_active_servers(server_id_filter: str = None) -> List[Dict]:
    """
    Obtiene servidores activos desde SQL Server.
    
    Args:
        server_id_filter: ID de servidor específico (opcional)
        
    Returns:
        Lista de servidores en formato compatible con los jobs
    """
    query = """
        SELECT 
            CAST(id AS VARCHAR(50)) as id,
            nombre as name,
            host,
            port,
            username,
            password_encrypted as password,
            database_name,
            system_type,
            activo as active,
            sucursales
        FROM Servidores_Conexiones
        WHERE activo = 1
    """
    
    if server_id_filter:
        query += " AND CAST(id AS VARCHAR(50)) = %s"
        params = (server_id_filter,)
    else:
        params = None
    
    rows = await _execute_sql_async(query, params)
    
    # Convertir a formato esperado por los jobs
    servers = []
    for row in rows:
        server = {
            'id': row.get('id'),
            'name': row.get('name'),
            'host': row.get('host'),
            'port': row.get('port'),
            'username': row.get('username'),
            'password': _decrypt_password_for_internal_use(row.get('password')),
            'database': row.get('database_name'),
            'system_type': row.get('system_type', 'softrestaurant'),
            'active': bool(row.get('active', True)),
        }
        
        # Parsear sucursales si existe
        sucursales_raw = row.get('sucursales')
        if sucursales_raw:
            try:
                if isinstance(sucursales_raw, str):
                    server['sucursales'] = json.loads(sucursales_raw)
                else:
                    server['sucursales'] = sucursales_raw
            except Exception:
                server['sucursales'] = []
        else:
            server['sucursales'] = []
        
        servers.append(server)
    
    logger.debug(f"[SCHEDULER_SQL] Obtenidos {len(servers)} servidores activos")
    return servers


async def get_server_by_id(server_id: str) -> Optional[Dict]:
    """Obtiene un servidor por ID."""
    servers = await get_active_servers(server_id)
    return servers[0] if servers else None


# =============================================================================
# INVENTARIOS PROCESADOS
# =============================================================================

async def inventario_existe(
    sistema_origen: str,
    server_id: str,
    sucursal_id: str,
    almacen_id: str,
    folio_inventario: str
) -> bool:
    """Verifica si un inventario ya fue procesado."""
    query = """
        SELECT COUNT(*) as count
        FROM Scheduler_InventariosProcesados
        WHERE SistemaOrigen = %s
          AND ServerID = %s
          AND SucursalID = %s
          AND AlmacenID = %s
          AND FolioInventario = %s
    """
    params = (sistema_origen, server_id, sucursal_id, almacen_id, folio_inventario)
    
    rows = await _execute_sql_async(query, params)
    return rows[0]['count'] > 0 if rows else False


async def registrar_inventario_procesando(
    sistema_origen: str,
    server_id: str,
    sucursal_id: str,
    almacen_id: str,
    folio_inventario: str,
    detalles: Dict = None
) -> bool:
    """Registra un inventario como EN_PROCESO."""
    query = """
        INSERT INTO Scheduler_InventariosProcesados (
            SistemaOrigen, ServerID, SucursalID, AlmacenID, FolioInventario,
            Estado, DetallesJSON
        ) VALUES (
            %s, %s, %s, %s, %s, 'EN_PROCESO', %s
        )
    """
    params = (
        sistema_origen, server_id, sucursal_id, almacen_id, folio_inventario,
        json.dumps(detalles) if detalles else None
    )
    
    try:
        await _execute_sql_async(query, params, fetch=False)
        return True
    except Exception as e:
        logger.error(f"[SCHEDULER_SQL] Error registrando inventario: {e}")
        return False


async def actualizar_inventario_completado(
    sistema_origen: str,
    server_id: str,
    sucursal_id: str,
    almacen_id: str,
    folio_inventario: str,
    workflow_id: str = None
) -> bool:
    """Marca un inventario como COMPLETADO."""
    query = """
        UPDATE Scheduler_InventariosProcesados
        SET Estado = 'COMPLETADO',
            FechaProcesamiento = GETUTCDATE(),
            WorkflowID = %s
        WHERE SistemaOrigen = %s
          AND ServerID = %s
          AND SucursalID = %s
          AND AlmacenID = %s
          AND FolioInventario = %s
    """
    params = (workflow_id, sistema_origen, server_id, sucursal_id, almacen_id, folio_inventario)
    
    try:
        await _execute_sql_async(query, params, fetch=False)
        return True
    except Exception as e:
        logger.error(f"[SCHEDULER_SQL] Error actualizando inventario: {e}")
        return False


async def actualizar_inventario_error(
    sistema_origen: str,
    server_id: str,
    sucursal_id: str,
    almacen_id: str,
    folio_inventario: str,
    error_mensaje: str
) -> bool:
    """Marca un inventario como ERROR."""
    query = """
        UPDATE Scheduler_InventariosProcesados
        SET Estado = 'ERROR',
            FechaUltimoIntento = GETUTCDATE(),
            Intentos = Intentos + 1,
            ErrorMensaje = %s
        WHERE SistemaOrigen = %s
          AND ServerID = %s
          AND SucursalID = %s
          AND AlmacenID = %s
          AND FolioInventario = %s
    """
    params = (error_mensaje, sistema_origen, server_id, sucursal_id, almacen_id, folio_inventario)
    
    try:
        await _execute_sql_async(query, params, fetch=False)
        return True
    except Exception as e:
        logger.error(f"[SCHEDULER_SQL] Error actualizando inventario: {e}")
        return False


async def get_inventarios_pendientes_reintento(max_intentos: int = 3, limit: int = 5) -> List[Dict]:
    """Obtiene inventarios en ERROR que pueden reintentarse."""
    query = """
        SELECT TOP %s
            SistemaOrigen, ServerID, SucursalID, AlmacenID, FolioInventario,
            Estado, Intentos, FechaDeteccion, DetallesJSON
        FROM Scheduler_InventariosProcesados
        WHERE Estado = 'ERROR'
          AND Intentos < %s
        ORDER BY FechaUltimoIntento ASC
    """
    params = (limit, max_intentos)
    
    return await _execute_sql_async(query, params)


async def get_inventario_error_by_id(record_id: int) -> Optional[Dict]:
    """Obtiene un único registro ERROR por ID para recuperación administrativa controlada."""
    query = """
        SELECT
            ID, SistemaOrigen, ServerID, SucursalID, AlmacenID, FolioInventario,
            Estado, Intentos, FechaDeteccion, FechaUltimoIntento, ErrorMensaje, DetallesJSON
        FROM Scheduler_InventariosProcesados
        WHERE ID = %s
          AND Estado = 'ERROR'
    """
    rows = await _execute_sql_async(query, (record_id,))
    return rows[0] if rows else None


# =============================================================================
# PEDIDOS PROCESADOS
# =============================================================================

async def pedido_existe(
    sistema_origen: str,
    server_id: str,
    empresa_id: str,
    folio_pedido: str
) -> bool:
    """Verifica si un pedido ya fue detectado."""
    query = """
        SELECT COUNT(*) as count
        FROM Scheduler_PedidosProcesados
        WHERE SistemaOrigen = %s
          AND ServerID = %s
          AND EmpresaID = %s
          AND FolioPedido = %s
    """
    params = (sistema_origen, server_id, empresa_id, folio_pedido)
    
    rows = await _execute_sql_async(query, params)
    return rows[0]['count'] > 0 if rows else False


async def registrar_pedido_detectado(
    sistema_origen: str,
    server_id: str,
    empresa_id: str,
    folio_pedido: str,
    sucursal_id: str = None,
    tipo_documento: str = None,
    detalles: Dict = None
) -> bool:
    """Registra un pedido detectado."""
    query = """
        INSERT INTO Scheduler_PedidosProcesados (
            SistemaOrigen, ServerID, EmpresaID, SucursalID, FolioPedido,
            TipoDocumento, DetallesJSON
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s
        )
    """
    params = (
        sistema_origen, server_id, empresa_id, sucursal_id, folio_pedido,
        tipo_documento, json.dumps(detalles) if detalles else None
    )
    
    try:
        await _execute_sql_async(query, params, fetch=False)
        return True
    except Exception as e:
        logger.error(f"[SCHEDULER_SQL] Error registrando pedido: {e}")
        return False


# =============================================================================
# BITÁCORA DE JOBS
# =============================================================================

async def registrar_bitacora_job(
    job_name: str,
    run_id: str,
    accion: str,
    server_id: str = None,
    detalles: Dict = None,
    exito: bool = True,
    error_mensaje: str = None
) -> bool:
    """Registra una entrada en la bitácora de jobs."""
    query = """
        INSERT INTO Scheduler_BitacoraJobs (
            JobName, RunID, Accion, ServerID, DetallesJSON, Exito, MensajeError
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s
        )
    """
    params = (
        job_name, run_id, accion, server_id,
        json.dumps(detalles) if detalles else None,
        1 if exito else 0,
        error_mensaje
    )
    
    try:
        await _execute_sql_async(query, params, fetch=False)
        return True
    except Exception as e:
        logger.error(f"[SCHEDULER_SQL] Error registrando bitácora: {e}")
        return False


# =============================================================================
# EMPRESAS (Lectura desde SQL)
# =============================================================================

async def get_empresas_activas(empresa_id_filter: str = None) -> List[Dict]:
    """
    Obtiene empresas activas.
    
    Las empresas están en la tabla Empresas o se infieren de Servidores_Conexiones.
    """
    # Intentar obtener de tabla Empresas si existe
    query = """
        SELECT 
            CAST(EmpresaID AS VARCHAR(50)) as id,
            NombreEmpresa as nombre,
            RFC as RFC,
            Activo as active
        FROM Sistema_Empresas
        WHERE Activo = 1
    """
    
    if empresa_id_filter:
        query += " AND CAST(EmpresaID AS VARCHAR(50)) = %s"
        params = (empresa_id_filter,)
    else:
        params = None
    
    try:
        rows = await _execute_sql_async(query, params)
        if rows:
            return [
                {
                    'id': row.get('id'),
                    'nombre': row.get('nombre'),
                    'rfc': row.get('rfc'),
                    'active': bool(row.get('active', True))
                }
                for row in rows
            ]
    except Exception as e:
        logger.debug(f"[SCHEDULER_SQL] Tabla Empresas no disponible: {e}")
    
    # Fallback: obtener empresas de Servidores_Conexiones (usar columnas existentes)
    query_fallback = """
        SELECT DISTINCT
            CAST(id AS VARCHAR(50)) as id,
            nombre as nombre
        FROM Servidores_Conexiones
        WHERE activo = 1
    """
    
    try:
        rows = await _execute_sql_async(query_fallback, None)
        return [
            {
                'id': row.get('id'),
                'nombre': row.get('nombre'),
                'active': True
            }
            for row in rows
        ]
    except Exception as e:
        logger.debug(f"[SCHEDULER_SQL] Error en fallback empresas: {e}")
        return []


__all__ = [
    'get_active_servers',
    'get_server_by_id',
    'inventario_existe',
    'registrar_inventario_procesando',
    'actualizar_inventario_completado',
    'actualizar_inventario_error',
    'get_inventarios_pendientes_reintento',
    'pedido_existe',
    'registrar_pedido_detectado',
    'registrar_bitacora_job',
    'get_empresas_activas',
]
