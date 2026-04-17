# =============================================================================
# CAB-003 FASE 1B.2A - REPOSITORY (Acceso a tablas EDARSAHUB)
# =============================================================================
# Funciones de acceso a tablas de automatización en EDARSAHUB
# 
# FASE 1B.2A: Persistencia controlada de 1 registro manual
# - INSERT parametrizado (sin SQL injection)
# - Estado = 'EN_PROCESO' (compatible con CHECK constraint)
# - Identificador único en created_by
# - No se usa ultimo_folio_conocido
# =============================================================================

import logging
import hashlib
import uuid
from typing import List, Dict, Optional, Tuple
from datetime import date, datetime

logger = logging.getLogger(__name__)


# =============================================================================
# SECCIÓN 1: ACCESO A TABLAS EDARSAHUB (Solo lectura en Fase 1B.1)
# =============================================================================

def get_configuracion_activa(
    execute_sql_func,
    host: str,
    port: int,
    database: str,
    username: str,
    password: str,
    server_id: Optional[str] = None
) -> List[Dict]:
    """
    Lee configuración activa de automatizacion_inventarios_config.
    
    Args:
        execute_sql_func: Función para ejecutar SQL (inyectada)
        host, port, database, username, password: Conexión a EDARSAHUB
        server_id: Filtrar por servidor específico (opcional)
    
    Returns:
        Lista de configuraciones activas
    """
    query = """
        SELECT 
            config_id,
            server_id,
            sucursal_id,
            almacen_id,
            intervalo_minutos,
            hora_inicio,
            hora_fin,
            activo,
            created_at
        FROM automatizacion_inventarios_config
        WHERE activo = 1
    """
    
    if server_id:
        query += f" AND server_id = '{server_id}'"
    
    query += " ORDER BY server_id, sucursal_id, almacen_id"
    
    try:
        result = execute_sql_func(host, port, database, username, password, query)
        return result if result else []
    except Exception as e:
        logger.error(f"Error leyendo configuración: {e}")
        return []


def get_folios_ya_procesados(
    execute_sql_func,
    host: str,
    port: int,
    database: str,
    username: str,
    password: str,
    sistema_origen: str,
    server_id: str
) -> List[Dict]:
    """
    Lee folios ya procesados para un sistema/servidor específico.
    Se usa para comparar y evitar duplicados.
    
    Args:
        execute_sql_func: Función para ejecutar SQL (inyectada)
        host, port, database, username, password: Conexión a EDARSAHUB
        sistema_origen: 'SOFTRESTAURANT' o 'MPRO'
        server_id: UUID del servidor
    
    Returns:
        Lista de folios procesados con clave CAB-003 de 8 campos
    """
    query = f"""
        SELECT 
            sistema_origen,
            server_id,
            sucursal_id,
            almacen_id,
            comentario,
            folio_inventario,
            fecha_inventario,
            estado_inventario_origen,
            estado,
            fecha_procesado,
            created_at
        FROM automatizacion_inventarios_folios_procesados
        WHERE sistema_origen = '{sistema_origen}'
          AND server_id = '{server_id}'
        ORDER BY fecha_inventario DESC, folio_inventario DESC
    """
    
    try:
        result = execute_sql_func(host, port, database, username, password, query)
        return result if result else []
    except Exception as e:
        logger.error(f"Error leyendo folios procesados: {e}")
        return []


def construir_clave_cab003(
    sistema_origen: str,
    server_id: str,
    sucursal_id: str,
    almacen_id: str,
    comentario: Optional[str],
    folio_inventario: str,
    fecha_inventario: date,
    estado_inventario_origen: Optional[str]
) -> str:
    """
    Construye la clave única CAB-003 de 8 campos como string para comparación.
    
    Returns:
        String concatenado de los 8 campos
    """
    return "|".join([
        sistema_origen or "",
        server_id or "",
        sucursal_id or "",
        almacen_id or "",
        comentario or "",
        folio_inventario or "",
        str(fecha_inventario) if fecha_inventario else "",
        estado_inventario_origen or ""
    ])


def verificar_ya_procesado(
    folios_procesados: List[Dict],
    sistema_origen: str,
    server_id: str,
    sucursal_id: str,
    almacen_id: str,
    comentario: Optional[str],
    folio_inventario: str,
    fecha_inventario: date,
    estado_inventario_origen: Optional[str]
) -> tuple:
    """
    Verifica si un inventario ya fue procesado comparando la clave CAB-003.
    
    Returns:
        (ya_procesado: bool, registro_existente: dict or None)
    """
    clave_buscar = construir_clave_cab003(
        sistema_origen, server_id, sucursal_id, almacen_id,
        comentario, folio_inventario, fecha_inventario, estado_inventario_origen
    )
    
    for folio in folios_procesados:
        clave_existente = construir_clave_cab003(
            folio.get('sistema_origen'),
            folio.get('server_id'),
            folio.get('sucursal_id'),
            folio.get('almacen_id'),
            folio.get('comentario'),
            folio.get('folio_inventario'),
            folio.get('fecha_inventario'),
            folio.get('estado_inventario_origen')
        )
        
        if clave_buscar == clave_existente:
            return True, folio
    
    return False, None


# =============================================================================
# SECCIÓN 2: PERSISTENCIA CONTROLADA (FASE 1B.2A)
# Solo 1 registro manual por ejecución
# =============================================================================

def generar_identificador_ejecucion() -> str:
    """
    Genera identificador único para created_by.
    Formato: CAB003_FASE1B2_MANUAL_YYYYMMDD_HHMMSS
    """
    return f"CAB003_FASE1B2_MANUAL_{datetime.now().strftime('%Y%m%d_%H%M%S')}"


def generar_hash_verificacion(
    sistema_origen: str,
    server_id: str,
    sucursal_id: str,
    almacen_id: str,
    comentario: Optional[str],
    folio_inventario: str,
    fecha_inventario: str,
    estado_inventario_origen: Optional[str]
) -> str:
    """
    Genera SHA256 de la clave CAB-003 para verificación.
    """
    clave = "|".join([
        sistema_origen or "",
        server_id or "",
        sucursal_id or "",
        almacen_id or "",
        comentario or "",
        folio_inventario or "",
        str(fecha_inventario) if fecha_inventario else "",
        estado_inventario_origen or ""
    ])
    return hashlib.sha256(clave.encode('utf-8')).hexdigest()


def verificar_duplicado_en_bd(
    execute_sql_func,
    host: str,
    port: int,
    database: str,
    username: str,
    password: str,
    sistema_origen: str,
    server_id: str,
    sucursal_id: str,
    almacen_id: str,
    comentario: Optional[str],
    folio_inventario: str,
    fecha_inventario: str,
    estado_inventario_origen: Optional[str]
) -> Tuple[bool, Optional[Dict]]:
    """
    Verifica si el registro ya existe en la BD usando query parametrizada.
    
    Returns:
        (existe: bool, registro_existente: dict or None)
    """
    # Query parametrizada - manejo de NULL con ISNULL
    # Nota: pytds/pymssql usan %s como placeholder
    query = """
        SELECT TOP 1
            procesado_id,
            sistema_origen,
            server_id,
            sucursal_id,
            almacen_id,
            comentario,
            folio_inventario,
            fecha_inventario,
            estado_inventario_origen,
            estado,
            created_at,
            created_by
        FROM automatizacion_inventarios_folios_procesados
        WHERE sistema_origen = %s
          AND server_id = %s
          AND ISNULL(sucursal_id, '') = ISNULL(%s, '')
          AND almacen_id = %s
          AND ISNULL(comentario, '') = ISNULL(%s, '')
          AND folio_inventario = %s
          AND fecha_inventario = %s
          AND ISNULL(estado_inventario_origen, '') = ISNULL(%s, '')
    """
    
    params = (
        sistema_origen,
        server_id,
        sucursal_id or '',
        almacen_id,
        comentario or '',
        folio_inventario,
        fecha_inventario,
        estado_inventario_origen or ''
    )
    
    try:
        # Usar función de ejecución parametrizada
        result = execute_sql_parametrized(
            host, port, database, username, password, query, params
        )
        
        if result and len(result) > 0:
            return True, result[0]
        return False, None
        
    except Exception as e:
        logger.error(f"Error verificando duplicado: {e}")
        raise


def execute_sql_parametrized(
    host: str,
    port: int,
    database: str,
    username: str,
    password: str,
    query: str,
    params: tuple
) -> List[Dict]:
    """
    Ejecuta query con parámetros (previene SQL injection).
    Usa pymssql con parámetros.
    """
    import pymssql
    
    try:
        # Parsear host y puerto si vienen juntos
        if ',' in host:
            parts = host.split(',')
            host_clean = parts[0]
            port = int(parts[1].split('\\')[0]) if '\\' in parts[1] else int(parts[1])
        else:
            host_clean = host
        
        conn = pymssql.connect(
            server=host_clean,
            port=port,
            user=username,
            password=password,
            database=database,
            timeout=30
        )
        
        cursor = conn.cursor(as_dict=True)
        cursor.execute(query, params)
        
        # Si es SELECT, obtener resultados
        if query.strip().upper().startswith('SELECT'):
            result = cursor.fetchall()
        else:
            # Para INSERT/UPDATE/DELETE
            conn.commit()
            result = [{'affected_rows': cursor.rowcount}]
        
        cursor.close()
        conn.close()
        
        return result
        
    except Exception as e:
        logger.error(f"Error ejecutando query parametrizada: {e}")
        raise


def insertar_folio_procesado(
    execute_sql_func,
    host: str,
    port: int,
    database: str,
    username: str,
    password: str,
    sistema_origen: str,
    server_id: str,
    sucursal_id: str,
    almacen_id: str,
    comentario: Optional[str],
    folio_inventario: str,
    fecha_inventario: str,
    estado_inventario_origen: Optional[str],
    identificador_ejecucion: str
) -> Tuple[bool, str, Optional[str]]:
    """
    Inserta 1 registro en automatizacion_inventarios_folios_procesados.
    
    Args:
        Todos los campos de la clave CAB-003 + identificador_ejecucion
    
    Returns:
        (exito: bool, mensaje: str, procesado_id: str or None)
    """
    # Generar UUID y hash
    procesado_id = str(uuid.uuid4())
    hash_verificacion = generar_hash_verificacion(
        sistema_origen, server_id, sucursal_id, almacen_id,
        comentario, folio_inventario, fecha_inventario, estado_inventario_origen
    )
    
    # Query parametrizada para INSERT
    query = """
        INSERT INTO automatizacion_inventarios_folios_procesados (
            procesado_id,
            sistema_origen,
            server_id,
            sucursal_id,
            almacen_id,
            comentario,
            folio_inventario,
            fecha_inventario,
            estado_inventario_origen,
            hash_verificacion,
            estado,
            heartbeat_at,
            fecha_procesado,
            error_detalle,
            ruta_archivo_excel,
            created_at,
            updated_at,
            created_by,
            updated_by
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s, %s, %s, %s, %s
        )
    """
    
    params = (
        procesado_id,
        sistema_origen,
        server_id,
        sucursal_id or '',
        almacen_id,
        comentario,  # Puede ser NULL
        folio_inventario,
        fecha_inventario,
        estado_inventario_origen,  # Puede ser NULL
        hash_verificacion,
        'EN_PROCESO',  # Estado compatible con CHECK constraint
        None,  # heartbeat_at
        None,  # fecha_procesado
        None,  # error_detalle
        None,  # ruta_archivo_excel
        datetime.now(),  # created_at
        None,  # updated_at
        identificador_ejecucion,  # created_by
        None   # updated_by
    )
    
    try:
        result = execute_sql_parametrized(
            host, port, database, username, password, query, params
        )
        
        return True, "Registro insertado correctamente", procesado_id
        
    except Exception as e:
        error_msg = str(e)
        
        # Detectar error de duplicado por UNIQUE constraint
        if 'UQ_folios_clave_unica' in error_msg or 'UNIQUE' in error_msg.upper():
            return False, "Registro duplicado (constraint UNIQUE)", None
        
        logger.error(f"Error insertando registro: {e}")
        return False, f"Error: {error_msg}", None


def rollback_por_identificador(
    execute_sql_func,
    host: str,
    port: int,
    database: str,
    username: str,
    password: str,
    identificador_ejecucion: str
) -> Tuple[bool, int, str]:
    """
    Elimina registros por identificador de ejecución.
    
    Args:
        identificador_ejecucion: Ej: CAB003_FASE1B2_MANUAL_20260417_143522
    
    Returns:
        (exito: bool, registros_eliminados: int, mensaje: str)
    """
    # Primero contar cuántos registros se eliminarán
    query_count = """
        SELECT COUNT(*) as total
        FROM automatizacion_inventarios_folios_procesados
        WHERE created_by = %s
    """
    
    query_delete = """
        DELETE FROM automatizacion_inventarios_folios_procesados
        WHERE created_by = %s
    """
    
    params = (identificador_ejecucion,)
    
    try:
        # Contar registros
        result_count = execute_sql_parametrized(
            host, port, database, username, password, query_count, params
        )
        total = result_count[0]['total'] if result_count else 0
        
        if total == 0:
            return True, 0, "No se encontraron registros con ese identificador"
        
        # Eliminar registros
        execute_sql_parametrized(
            host, port, database, username, password, query_delete, params
        )
        
        return True, total, f"{total} registro(s) eliminado(s) correctamente"
        
    except Exception as e:
        logger.error(f"Error en rollback: {e}")
        return False, 0, f"Error: {str(e)}"


def contar_registros_por_identificador(
    execute_sql_func,
    host: str,
    port: int,
    database: str,
    username: str,
    password: str,
    identificador_ejecucion: str
) -> int:
    """
    Cuenta registros por identificador de ejecución.
    """
    query = """
        SELECT COUNT(*) as total
        FROM automatizacion_inventarios_folios_procesados
        WHERE created_by = %s
    """
    
    params = (identificador_ejecucion,)
    
    try:
        result = execute_sql_parametrized(
            host, port, database, username, password, query, params
        )
        return result[0]['total'] if result else 0
    except Exception as e:
        logger.error(f"Error contando registros: {e}")
        return 0


# =============================================================================
# SECCIÓN 3: FUNCIONES NO IMPLEMENTADAS (FASES POSTERIORES)
# =============================================================================

def registrar_folio_procesado(
    execute_sql_func,
    host: str,
    port: int,
    database: str,
    username: str,
    password: str,
    **kwargs
) -> None:
    """
    DEPRECADO - Usar insertar_folio_procesado() en su lugar.
    """
    raise NotImplementedError(
        "Usar insertar_folio_procesado() de Fase 1B.2A"
    )


def actualizar_ultimo_folio_conocido(
    execute_sql_func,
    host: str,
    port: int,
    database: str,
    username: str,
    password: str,
    **kwargs
) -> None:
    """
    PENDIENTE FASE POSTERIOR - No implementar todavía.
    Actualiza la marca de agua en automatizacion_inventarios_ultimo_folio_conocido.
    """
    raise NotImplementedError(
        "Marca de agua incremental no habilitada en Fase 1B.2A. "
        "Requiere autorización para fase posterior."
    )
