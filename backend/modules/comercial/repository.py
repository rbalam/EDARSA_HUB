from core.unidades_service import UnidadesService
from core.corporate_filters.service import CorporateFilterService
"""
EDARSA HUB - Comercial Module Repository
========================================
Acceso a datos para el módulo comercial.

FASE 6 MIGRACIÓN SQL-FIRST (Mayo 2026):
- ELIMINADA dependencia de MongoDB completamente
- Todas las funciones usan EDARSAHUB SQL como única fuente
- execute_hub_query como motor central

ARQUITECTURA:
- Servidores: Tabla Servidores_Conexiones
- Metas: Tabla Comercial_Metas (nueva)
- Cache KPIs: Tabla Comercial_KPIs_Cache (nueva)
- Status: Tabla Servidores_Status (existente)
"""

from typing import Dict, List, Optional, Any
import logging
import json
import os
from datetime import datetime, timezone

from core.db import execute_sql_query
from core.pool import execute_hub_query, execute_hub_query_single, execute_hub_insert
from core.config.edarsahub_config import get_edarsahub_sql_config

# P2-01 HELPER: Convierte dataclass a formato diccionario legacy
def _get_edarsahub_config_dict() -> dict:
    cfg = get_edarsahub_sql_config()
    return {
        'host': cfg.host,
        'port': cfg.port,
        'database': cfg.database,
        'username': cfg.user,
        'password': cfg.password,
    }




# ============================================================================
# CONFIGURACIÓN EDARSAHUB SQL - ÚNICA FUENTE DE DATOS
# ============================================================================

EDARSAHUB_CONFIG = _get_edarsahub_config_dict()

# Flag siempre True - SQL es la única fuente
USE_SQL_FOR_SERVERS = True


# ============================================================================
# DEPRECADO: MongoDB ya no se usa (Mayo 2026)
# ============================================================================

def init_comercial_repository(database=None) -> None:
    """DEPRECADO: MongoDB eliminado. No hace nada."""
    logging.info("[COMERCIAL] Repository inicializado - SQL-ONLY mode")


def get_db():
    """DEPRECADO: MongoDB eliminado. Retorna None siempre."""
    return None


def _decrypt_server_password(server: Optional[Dict]) -> Optional[Dict]:
    """Descifra password de servidor (compatibilidad)."""
    if not server:
        return server
    
    password = server.get('password', '')
    if password:
        try:
            from core.secret_manager import decrypt_secret, is_encrypted_secret
            if is_encrypted_secret(password):
                server['password'] = decrypt_secret(password)
        except Exception as e:
            logging.error(f"[DECRYPT_ERROR] Error descifrando password: {e}")
    
    return server


# ============================================================================
# SERVIDORES - LECTURA DESDE EDARSAHUB SQL (Fase 2/3 Migración Abril 2026)
# ============================================================================

def _sql_row_to_server_dict(row: Dict) -> Dict:
    """
    Convierte una fila de Servidores_Conexiones (SQL) al formato esperado por el sistema.
    Garantiza paridad estructural con el esquema original de MongoDB.
    
    FASE 3C.1: Descifra automáticamente el password si está cifrado.
    """
    # Parsear campos JSON (sucursales, categorias, departamentos, queries)
    def parse_json_field(value):
        if value is None:
            return None
        if isinstance(value, (list, dict)):
            return value
        try:
            return json.loads(value) if value else None
        except (json.JSONDecodeError, TypeError):
            return None
    
    # FASE 3C.1: Descifrar password si está cifrado
    password_encrypted = row.get('password_encrypted', '')
    password_decrypted = ''
    servidor_nombre = row.get('nombre', row.get('id', 'N/A'))
    if password_encrypted:
        try:
            from core.secret_manager import decrypt_secret, is_encrypted_secret
            if is_encrypted_secret(password_encrypted):
                password_decrypted = decrypt_secret(password_encrypted)
                logging.info(f"[DECRYPT_OK] Servidor {servidor_nombre}: Password descifrado correctamente")
            else:
                # Legacy plaintext - usar tal cual pero loguear warning
                password_decrypted = password_encrypted
                logging.debug(f"[LEGACY_PLAINTEXT] Servidor {servidor_nombre} tiene password sin cifrar")
        except Exception as e:
            logging.error(f"[DECRYPT_ERROR] Error descifrando password de servidor {servidor_nombre}: {type(e).__name__} - {e}")
            password_decrypted = password_encrypted  # Fallback a valor original
    else:
        logging.warning(f"[NO_PASSWORD] Servidor {servidor_nombre}: No tiene password_encrypted")
    
    return {
        'id': str(row.get('id', '')),
        'name': row.get('nombre', ''),
        'nombre': row.get('nombre', ''),  # alias para consumidores que esperan 'nombre'
        'system_type': row.get('system_type', ''),
        'tipo_conexion': row.get('tipo_conexion', 'DATA_SOURCE'),
        'host': row.get('host', ''),
        'port': row.get('port', 1433),
        'database': row.get('database_name', ''),
        'username': row.get('username', ''),
        'password': password_decrypted,  # FASE 3C.1: Ahora descifrado
        'active': bool(row.get('activo', False)),
        'visible_en_operaciones': bool(row.get('visible_en_operaciones', True)),
        'visible_en_listado': bool(row.get('visible_en_listado', True)),
        'es_editable_ui': bool(row.get('es_editable_ui', True)),
        'es_eliminable_ui': bool(row.get('es_eliminable_ui', True)),
        'sucursales': parse_json_field(row.get('sucursales')),
        'categorias': parse_json_field(row.get('categorias')),
        'departamentos': parse_json_field(row.get('departamentos')),
        'date_calculation_method': row.get('date_calculation_method'),
        'queries_configured': bool(row.get('queries_configured', False)),
        'query_ventas': parse_json_field(row.get('query_ventas')),
        'query_inventario': parse_json_field(row.get('query_inventario')),
        'query_movimientos': parse_json_field(row.get('query_movimientos')),
        'created_at': row.get('created_at'),
        'updated_at': row.get('updated_at'),
    }


def _get_server_by_id_sql(server_id: str) -> Optional[Dict]:
    """
    Obtiene un servidor activo por ID desde EDARSAHUB SQL.
    Retorna None si no se encuentra o si hay error de conexión.
    """
    try:
        # FIX: usar server_id (antes interpolaba '{id}' = builtin de Python -> nunca match).
        # Escapado de comillas para evitar inyección SQL (server_id viene del path).
        safe_id = str(server_id).replace("'", "''")
        query = f"""
        SELECT * FROM Servidores_Conexiones
        WHERE (id = '{safe_id}' OR mongodb_id = '{safe_id}')
          AND activo = 1
        """
        results = execute_sql_query(
            EDARSAHUB_CONFIG['host'],
            EDARSAHUB_CONFIG['port'],
            EDARSAHUB_CONFIG['database'],
            EDARSAHUB_CONFIG['username'],
            EDARSAHUB_CONFIG['password'],
            query
        )
        if results:
            logging.info(f"[SQL] Servidor {server_id} obtenido desde EDARSAHUB SQL")
            return _sql_row_to_server_dict(results[0])
        return None
    except Exception as e:
        logging.warning(f"[SQL] Error obteniendo servidor {server_id} desde SQL: {e}")
        return None


def _get_servers_for_tablero_sql() -> List[Dict]:
    """
    Obtiene servidores visibles para el tablero ejecutivo desde EDARSAHUB SQL.
    Solo devuelve conexiones DATA_SOURCE (excluye CORE del sistema).
    """
    try:
        query = """
        SELECT * FROM Servidores_Conexiones
        WHERE activo = 1
          AND (visible_en_operaciones = 1 OR visible_en_operaciones IS NULL)
          AND (tipo_conexion = 'DATA_SOURCE' OR tipo_conexion IS NULL)
        ORDER BY nombre
        """
        results = execute_sql_query(
            EDARSAHUB_CONFIG['host'],
            EDARSAHUB_CONFIG['port'],
            EDARSAHUB_CONFIG['database'],
            EDARSAHUB_CONFIG['username'],
            EDARSAHUB_CONFIG['password'],
            query
        )
        servers = [_sql_row_to_server_dict(row) for row in results]
        logging.info(f"[SQL] Obtenidos {len(servers)} servidores para tablero desde EDARSAHUB SQL")
        return servers
    except Exception as e:
        logging.warning(f"[SQL] Error obteniendo servidores desde SQL: {e}")
        return []


async def get_server_by_id(server_id: str) -> Optional[Dict]:
    """
    Obtiene un servidor activo por ID desde SQL Server.
    MIGRACIÓN SQL-ONLY (Mayo 2026): MongoDB eliminado.
    """
    server = _get_server_by_id_sql(server_id)
    if server:
        return server
    logging.debug(f"[SQL-ONLY] Servidor {server_id} no encontrado")
    return None


async def get_servers_for_tablero() -> List[Dict]:
    """
    Obtiene servidores visibles para el tablero ejecutivo.
    Solo devuelve conexiones DATA_SOURCE (excluye CORE del sistema).
    MIGRACIÓN SQL-ONLY (Mayo 2026): MongoDB eliminado.
    """
    servers = _get_servers_for_tablero_sql()
    return servers if servers else []


async def get_sucursales_visibles_config(server_id: str) -> Dict[str, bool]:
    """
    Obtiene la configuración de visibilidad de sucursales para un servidor.
    MIGRACIÓN SQL-ONLY (Mayo 2026): Lee de tabla Sistema_SucursalServidorConfig.
    
    Returns:
        Dict con {sucursal_nombre: visible_en_operaciones}
    """
    try:
        query = """
            SELECT SucursalNombre, VisibleEnOperaciones 
            FROM Sistema_SucursalServidorConfig
            WHERE LOWER(ServerID) = LOWER(%s) AND Activa = 1
        """
        configs = execute_hub_query(query, (server_id,))
        
        if not configs:
            return {}
        
        return {
            c.get("SucursalNombre", ""): c.get("VisibleEnOperaciones", True)
            for c in configs
        }
    except Exception as e:
        logging.warning(f"Error obteniendo config de sucursales para {server_id}: {e}")
        return {}


async def filtrar_unidades_por_visibilidad(unidades: List[Dict], server_id: str) -> List[Dict]:
    """
    Filtra una lista de unidades/sucursales según la configuración de visibilidad.
    
    REGLA DE COMPATIBILIDAD:
    - Si NO hay configuración para este servidor -> devuelve TODAS (comportamiento legacy)
    - Si SÍ hay configuración -> devuelve solo las marcadas como visible_en_operaciones=True
    """
    config = await get_sucursales_visibles_config(server_id)
    
    if not config:
        # Sin configuración = todas visibles (backward compatible)
        return unidades
    
    # Filtrar por configuración
    resultado = []
    for unidad in unidades:
        nombre = unidad.get("unidad", "") or unidad.get("sucursal", "")
        # Si el nombre está en la config, usar ese valor; si no está, asumir visible
        if config.get(nombre, True):
            resultado.append(unidad)
        else:
            logging.info(f"Sucursal '{nombre}' oculta por configuración")
    
    return resultado


# ============================================================================
# SUCURSALES - RESOLUCIÓN DE NOMBRES DESDE EDARSAHUB SQL
# ============================================================================

def _get_sucursal_nombre_sql(server_id: str, sucursal_origen_id: str) -> Optional[str]:
    """
    Obtiene el nombre de una sucursal desde EDARSAHUB SQL.
    Busca en la tabla Unidades_Negocio que mapea servidor + código origen -> nombre.
    
    Returns:
        Nombre de la sucursal o None si no se encuentra
    """
    try:
        # Construir condición para sucursal_origen_id (puede ser NULL para SoftRestaurant)
        if sucursal_origen_id and sucursal_origen_id not in ['default', '']:
            suc_condition = f"sucursal_origen_id = '{sucursal_origen_id}'"
        else:
            # Para SoftRestaurant sin código, buscar por server_id con sucursal_origen_id NULL
            suc_condition = "sucursal_origen_id IS NULL"
        
        query = f"""
        SELECT TOP 1 nombre, codigo, system_type
        FROM Unidades_Negocio
        WHERE server_id = '{server_id}'
          AND {suc_condition}
          AND activo = 1
        """
        results = execute_sql_query(
            EDARSAHUB_CONFIG['host'],
            EDARSAHUB_CONFIG['port'],
            EDARSAHUB_CONFIG['database'],
            EDARSAHUB_CONFIG['username'],
            EDARSAHUB_CONFIG['password'],
            query
        )
        if results and results[0].get('nombre'):
            nombre = results[0]['nombre']
            logging.info(f"[EDARSAHUB] Unidad encontrada: {nombre} (server: {server_id[:8]}..., suc: {sucursal_origen_id or 'NULL'})")
            return nombre
        return None
    except Exception as e:
        logging.warning(f"[EDARSAHUB] Error obteniendo nombre unidad: {e}")
        return None


async def get_sucursal_nombre(server_id: str, sucursal_origen_id: str, server_name: str = "") -> tuple:
    """
    Obtiene el nombre de una sucursal desde SQL Server.
    MIGRACIÓN SQL-ONLY (Mayo 2026): MongoDB eliminado.
    
    Returns:
        tuple: (nombre, connection_source)
    """
    # FUENTE ÚNICA: EDARSAHUB SQL
    nombre = _get_sucursal_nombre_sql(server_id, sucursal_origen_id)
    if nombre:
        return nombre, 'EDARSAHUB'
    
    # DEFAULT: Usar nombre del servidor
    return server_name, 'SERVER_DEFAULT'


def get_api_config_from_server(server: Dict) -> Optional[Dict]:
    """
    Obtiene configuración de API local desde los datos del servidor (EDARSAHUB).
    El servidor de EDARSAHUB ya incluye la configuración de API en sus campos.
    
    Returns:
        Dict con configuración de API o None si no está configurada
    """
    # En EDARSAHUB, la config de API está en campos del servidor
    if server.get('api_local_url') or server.get('api_config'):
        return {
            'api_url': server.get('api_local_url', ''),
            'activo': server.get('api_local_activa', False),
            'empresa_id': server.get('api_empresa_id', ''),
            'server_id': server.get('id', '')
        }
    return None


# ============================================================================
# QUERIES SQL - VENTAS MPRO
# ============================================================================

def query_ventas_mpro(server: Dict, mes: int, anio: int, sucursal_id: str = None) -> List[Dict]:
    """
    Obtiene ventas de MPRO para un mes/año específico.
    """
    sucursal_filtro = f"AND Sc_Cve_Sucursal = '{sucursal_id}'" if sucursal_id else ""
    
    query = f"""
    SELECT 
        Sc_Cve_Sucursal as sucursal_id,
        SUM(Cm_Total) as ventas,
        COUNT(DISTINCT Cm_Folio) as cheques,
        SUM(Cm_NumPersonas) as pax
    FROM Comanda
    WHERE MONTH(Cm_Fecha) = {mes}
      AND YEAR(Cm_Fecha) = {anio}
      AND Cm_Estado IN ('C', 'F')
      {sucursal_filtro}
    GROUP BY Sc_Cve_Sucursal
    """
    
    return execute_sql_query(
        server['host'], server['port'], server['database'],
        server['username'], server['password'], query
    )


def query_ventas_softrestaurant(server: Dict, mes: int, anio: int) -> List[Dict]:
    """
    Obtiene ventas de SoftRestaurant para un mes/año específico.
    Usa la Regla J de homologación: cheques + tempcheques con totalprecuenta > 0.
    """
    query = f"""
    SELECT 
        ISNULL(SUM(totalprecuenta), 0) as ventas,
        ISNULL(SUM(nopersonas), 0) as pax,
        COUNT(*) as cheques
    FROM (
        SELECT totalprecuenta, nopersonas 
        FROM cheques 
        WHERE MONTH(fecha) = {mes} AND YEAR(fecha) = {anio}
          AND totalprecuenta > 0 AND cancelado = 0
        UNION ALL
        SELECT totalprecuenta, nopersonas 
        FROM tempcheques 
        WHERE MONTH(fecha) = {mes} AND YEAR(fecha) = {anio}
          AND totalprecuenta > 0 AND cancelado = 0
    ) AS ventas_unificadas
    """
    
    return execute_sql_query(
        server['host'], server['port'], server['database'],
        server['username'], server['password'], query
    )


# ============================================================================
# QUERIES SQL - TICKET PERFECTO
# ============================================================================

def query_ticket_perfecto_mpro(server: Dict, mes: int, anio: int, sucursal_id: str = None) -> List[Dict]:
    """
    Obtiene datos de ticket perfecto para MPRO.
    """
    sucursal_filtro = f"AND C.Sc_Cve_Sucursal = '{sucursal_id}'" if sucursal_id else ""
    
    query = f"""
    SELECT 
        C.Cm_Folio as folio,
        C.Cm_Total as total,
        C.Cm_NumPersonas as pax,
        COUNT(D.Cd_Cantidad) as items,
        SUM(CASE WHEN P.Pr_Tipo = 'B' THEN 1 ELSE 0 END) as bebidas,
        SUM(CASE WHEN P.Pr_Tipo = 'A' THEN 1 ELSE 0 END) as alimentos,
        SUM(CASE WHEN P.Pr_Tipo = 'P' THEN 1 ELSE 0 END) as postres
    FROM Comanda C
    INNER JOIN Comanda_Detalle D ON D.Cm_Folio = C.Cm_Folio
    INNER JOIN Producto P ON P.Pr_Cve_Producto = D.Pr_Cve_Producto
    WHERE MONTH(C.Cm_Fecha) = {mes}
      AND YEAR(C.Cm_Fecha) = {anio}
      AND C.Cm_Estado IN ('C', 'F')
      {sucursal_filtro}
    GROUP BY C.Cm_Folio, C.Cm_Total, C.Cm_NumPersonas
    """
    
    return execute_sql_query(
        server['host'], server['port'], server['database'],
        server['username'], server['password'], query
    )


# ============================================================================
# QUERIES SQL - METAS (MIGRADO A SQL - Mayo 2026)
# ============================================================================

async def get_metas_sucursal(server_id: str, sucursal: str, mes: int, anio: int) -> Optional[Dict]:
    """
    Obtiene las metas de una sucursal desde SQL Server.
    MIGRACIÓN SQL-ONLY (Mayo 2026).
    """
    query = """
        SELECT ServerID as ServerID, Sucursal as Sucursal, Mes as Mes, Anio as Anio,
               MetaVentas as meta_ventas, MetaCheques as meta_cheques, MetaPax as meta_pax,
               MetaTicketPromedio as meta_ticket_promedio
        FROM Comercial_Metas
        WHERE LOWER(ServerID) = LOWER(%s) AND Sucursal = %s AND Mes = %s AND Anio = %s
    """
    result = execute_hub_query_single(query, (server_id, sucursal, mes, anio))
    return result


async def save_metas_sucursal(server_id: str, sucursal: str, mes: int, anio: int, metas: Dict) -> None:
    """
    Guarda las metas de una sucursal en SQL Server.
    MIGRACIÓN SQL-ONLY (Mayo 2026).
    """
    # Verificar si existe
    check_query = """
        SELECT 1 FROM Comercial_Metas
        WHERE LOWER(ServerID) = LOWER(%s) AND Sucursal = %s AND Mes = %s AND Anio = %s
    """
    exists = execute_hub_query_single(check_query, (server_id, sucursal, mes, anio))
    
    if exists:
        # UPDATE
        update_query = """
            UPDATE Comercial_Metas SET
                MetaVentas = %s, MetaCheques = %s, MetaPax = %s, MetaTicketPromedio = %s,
                FechaModificacion = GETDATE()
            WHERE LOWER(ServerID) = LOWER(%s) AND Sucursal = %s AND Mes = %s AND Anio = %s
        """
        execute_hub_insert(update_query, (
            metas.get('meta_ventas', 0), metas.get('meta_cheques', 0),
            metas.get('meta_pax', 0), metas.get('meta_ticket_promedio', 0),
            server_id, sucursal, mes, anio
        ))
    else:
        # INSERT
        insert_query = """
            INSERT INTO Comercial_Metas (ServerID, Sucursal, Mes, Anio, MetaVentas, MetaCheques, MetaPax, MetaTicketPromedio)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        execute_hub_insert(insert_query, (
            server_id, sucursal, mes, anio,
            metas.get('meta_ventas', 0), metas.get('meta_cheques', 0),
            metas.get('meta_pax', 0), metas.get('meta_ticket_promedio', 0)
        ))


# ============================================================================
# FUNCIONES DE CACHÉ KPIs - MIGRADO A SQL (Mayo 2026)
# ============================================================================

async def get_cached_kpis(server_id: str, periodo_key: str) -> Optional[Dict]:
    """Obtiene los KPIs cacheados de un servidor desde SQL."""
    query = """
        SELECT ServerID as ServerID, PeriodoKey as periodo_key, KPIsJSON as kpis,
               UpdatedAt as updated_at, Status as Status
        FROM Comercial_KPIs_Cache
        WHERE LOWER(ServerID) = LOWER(%s) AND PeriodoKey = %s
    """
    result = execute_hub_query_single(query, (server_id, periodo_key))
    if result and result.get('kpis'):
        try:
            result['kpis'] = json.loads(result['kpis'])
        except Exception:
            pass
    return result


async def save_kpis_cache(server_id: str, periodo_key: str, kpis: dict) -> None:
    """Guarda los KPIs en caché SQL."""
    kpis_json = json.dumps(kpis, default=str)
    
    # Verificar si existe
    check_query = """
        SELECT 1 FROM Comercial_KPIs_Cache
        WHERE LOWER(ServerID) = LOWER(%s) AND PeriodoKey = %s
    """
    exists = execute_hub_query_single(check_query, (server_id, periodo_key))
    
    if exists:
        update_query = """
            UPDATE Comercial_KPIs_Cache SET
                KPIsJSON = %s, UpdatedAt = GETDATE(), Status = 'online'
            WHERE LOWER(ServerID) = LOWER(%s) AND PeriodoKey = %s
        """
        execute_hub_insert(update_query, (kpis_json, server_id, periodo_key))
    else:
        insert_query = """
            INSERT INTO Comercial_KPIs_Cache (ServerID, PeriodoKey, KPIsJSON, UpdatedAt, Status)
            VALUES (%s, %s, %s, GETDATE(), 'online')
        """
        execute_hub_insert(insert_query, (server_id, periodo_key, kpis_json))


async def get_cached_kpis_by_prefix(server_id: str, periodo_prefix: str) -> List[Dict]:
    """Obtiene KPIs cacheados por prefijo de período."""
    query = """
        SELECT ServerID as ServerID, PeriodoKey as periodo_key, KPIsJSON as kpis,
               UpdatedAt as updated_at, Status as Status
        FROM Comercial_KPIs_Cache
        WHERE LOWER(ServerID) = LOWER(%s) AND PeriodoKey LIKE %s
    """
    results = execute_hub_query(query, (server_id, f"{periodo_prefix}%"))
    for r in results:
        if r.get('kpis'):
            try:
                r['kpis'] = json.loads(r['kpis'])
            except Exception:
                pass
    return results


async def save_server_connection_status(server_id: str, is_online: bool, response_time_ms: int = None) -> None:
    """Guarda el estado de conexión de un servidor en SQL."""
    # Verificar si existe
    check_query = """
        SELECT 1 FROM Servidores_Status
        WHERE LOWER(ServerID) = LOWER(%s)
    """
    exists = execute_hub_query_single(check_query, (server_id,))
    
    if exists:
        update_query = """
            UPDATE Servidores_Status SET
                IsOnline = %s, ResponseTimeMs = %s, LastCheck = GETDATE()
            WHERE LOWER(ServerID) = LOWER(%s)
        """
        execute_hub_insert(update_query, (1 if is_online else 0, response_time_ms, server_id))
    else:
        insert_query = """
            INSERT INTO Servidores_Status (ServerID, IsOnline, ResponseTimeMs, LastCheck)
            VALUES (%s, %s, %s, GETDATE())
        """
        execute_hub_insert(insert_query, (server_id, 1 if is_online else 0, response_time_ms))


async def get_server_connection_status(server_id: str) -> Optional[Dict]:
    """Obtiene el estado de conexión de un servidor desde SQL."""
    query = """
        SELECT ServerID as ServerID, IsOnline as is_online, ResponseTimeMs as response_time_ms,
               LastCheck as last_check
        FROM Servidores_Status
        WHERE LOWER(ServerID) = LOWER(%s)
    """
    result = execute_hub_query_single(query, (server_id,))
    if result:
        result['is_online'] = bool(result.get('is_online', False))
    return result


# ============================================================================
# FASE P0: CIRCUIT BREAKER CORREGIDO - CLASIFICACIÓN LIVE-C/SYNC-S/HUB
# ============================================================================

async def is_server_recently_offline(server_id: str, minutes_threshold: int = 10) -> bool:
    """
    FASE P0: Circuit breaker corregido.
    
    Verifica si un servidor fue marcado como offline recientemente.
    
    CAMBIO ARQUITECTÓNICO:
    - Para datos LIVE-C: El threshold se reduce a 2 minutos (no bloquear operaciones críticas)
    - Para datos HUB: El threshold normal de 10 minutos aplica
    
    Esta función ahora SOLO indica si hubo falla reciente, pero NO bloquea datos LIVE-C.
    El llamador decide si bloquear o reintentar según el tipo de dato.
    """
    status = await get_server_connection_status(server_id)
    if not status:
        return False  # Sin registro, intentar conectar
    
    if status.get('is_online', True):
        return False  # Estaba online, intentar conectar
    
    # Verificar si el último chequeo fue hace menos de X minutos
    last_check = status.get('last_check')
    if last_check:
        try:
            if isinstance(last_check, str):
                last_check_dt = datetime.fromisoformat(last_check.replace('Z', '+00:00'))
            else:
                last_check_dt = last_check
            
            # Asegurar timezone
            now = datetime.now(timezone.utc)
            if last_check_dt.tzinfo is None:
                last_check_dt = last_check_dt.replace(tzinfo=timezone.utc)
            
            diff_minutes = (now - last_check_dt).total_seconds() / 60
            
            if diff_minutes < minutes_threshold:
                return True  # Offline recientemente
        except Exception as e:
            logging.warning(f"Error parsing last_check: {e}")
    
    return False


async def should_attempt_live_query(server_id: str, data_type: str = "HUB") -> bool:
    """
    FASE P0: Determina si se debe intentar una query LIVE al servidor.
    
    Args:
        server_id: ID del servidor
        data_type: Tipo de dato:
            - "LIVE-C": Crítico (ventas_dia, stock actual) - SIEMPRE intentar
            - "SYNC-S": Sync corto (datos recientes) - Intentar con threshold de 2 min
            - "HUB": Datos consolidados - Usar cache si offline recientemente
    
    Returns:
        True si debe intentar la conexión LIVE
        False si debe usar cache/EDARSA HUB directamente
    """
    if data_type == "LIVE-C":
        # Datos críticos: SIEMPRE intentar conexión, ignora circuit breaker
        return True
    
    if data_type == "SYNC-S":
        # Sync corto: Reintentar más rápido (2 min threshold)
        return not await is_server_recently_offline(server_id, minutes_threshold=2)
    
    # HUB: Usar el threshold normal de 10 min
    return not await is_server_recently_offline(server_id, minutes_threshold=10)


# ============================================================================
# CACHÉ PARA DASHBOARD COMERCIAL (MIGRADO SQL - Mayo 2026)
# ============================================================================

async def save_dashboard_cache(server_id: str, periodo_key: str, dashboard_data: Dict) -> None:
    """Guarda el resultado del Dashboard en caché SQL."""
    data_json = json.dumps(dashboard_data, default=str)
    
    # Verificar si existe
    check_query = """
        SELECT 1 FROM Comercial_Dashboard_Cache
        WHERE LOWER(ServerID) = LOWER(%s) AND PeriodoKey = %s
    """
    exists = execute_hub_query_single(check_query, (server_id, periodo_key))
    
    if exists:
        update_query = """
            UPDATE Comercial_Dashboard_Cache SET
                DataJSON = %s, UpdatedAt = GETDATE()
            WHERE LOWER(ServerID) = LOWER(%s) AND PeriodoKey = %s
        """
        execute_hub_insert(update_query, (data_json, server_id, periodo_key))
    else:
        insert_query = """
            INSERT INTO Comercial_Dashboard_Cache (ServerID, PeriodoKey, DataJSON, UpdatedAt)
            VALUES (%s, %s, %s, GETDATE())
        """
        execute_hub_insert(insert_query, (server_id, periodo_key, data_json))


async def get_dashboard_cache(server_id: str, periodo_key: str) -> Optional[Dict]:
    """Obtiene el resultado del Dashboard desde caché SQL."""
    query = """
        SELECT ServerID as ServerID, PeriodoKey as periodo_key, DataJSON as data, UpdatedAt as updated_at
        FROM Comercial_Dashboard_Cache
        WHERE LOWER(ServerID) = LOWER(%s) AND PeriodoKey = %s
    """
    result = execute_hub_query_single(query, (server_id, periodo_key))
    if result and result.get('data'):
        try:
            result['data'] = json.loads(result['data'])
        except Exception:
            pass
    return result


__all__ = [
    'init_comercial_repository',
    'get_db',  # DEPRECADO - retorna None siempre
    'get_server_by_id',
    'get_servers_for_tablero',
    # Funciones SQL-ONLY (Mayo 2026)
    'execute_hub_query',
    'execute_hub_query_single',
    'execute_hub_insert',
    # Configuración SQL
    'EDARSAHUB_CONFIG',
    'USE_SQL_FOR_SERVERS',
    # Sucursales - resolución de nombres
    'get_sucursal_nombre',
    'get_api_config_from_server',
    # Ventas
    'query_ventas_mpro',
    'query_ventas_softrestaurant',
    # Ticket perfecto
    'query_ticket_perfecto_mpro',
    # Metas
    'get_metas_sucursal',
    'save_metas_sucursal',
    # Caché KPIs
    'get_cached_kpis',
    'save_kpis_cache',
    'get_cached_kpis_by_prefix',
    'save_server_connection_status',
    'get_server_connection_status',
    'is_server_recently_offline',
    # FASE P0: Nueva función
    'should_attempt_live_query',
    # Dashboard cache
    'save_dashboard_cache',
    'get_dashboard_cache',
]
