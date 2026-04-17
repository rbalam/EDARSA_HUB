# =============================================================================
# CAB-003 FASE 1B.1 - REPOSITORY (Acceso a tablas EDARSAHUB)
# =============================================================================
# Funciones de acceso a tablas de automatización en EDARSAHUB
# 
# FASE 1B.1: Solo operaciones de LECTURA (SELECT)
# - No hay INSERT/UPDATE en esta fase
# - No se usa ultimo_folio_conocido en esta fase
# =============================================================================

import logging
from typing import List, Dict, Optional
from datetime import date

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
# SECCIÓN 2: HELPERS DE PERSISTENCIA (NO USADOS EN FASE 1B.1)
# Preparados para Fase 1B.2 cuando se apruebe persistencia
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
    PENDIENTE FASE 1B.2 - No implementar todavía.
    Registra un folio como procesado en automatizacion_inventarios_folios_procesados.
    """
    raise NotImplementedError(
        "Persistencia no habilitada en Fase 1B.1. "
        "Requiere autorización para Fase 1B.2."
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
        "Marca de agua incremental no habilitada en Fase 1B.1. "
        "Requiere autorización para fase posterior."
    )
