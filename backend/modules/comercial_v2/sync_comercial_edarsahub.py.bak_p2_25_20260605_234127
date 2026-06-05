"""
SYNC COMERCIAL EDARSAHUB - Comercial V2
=======================================

Sincronizador de datos comerciales hacia EDARSAHUB.
Extrae datos de SoftRestaurant y MPRO, los transforma y guarda en tablas v2.

IMPORTANTE:
- Este módulo NO está conectado al Tablero Ejecutivo actual
- NO modifica el módulo comercial existente
- Escribe SOLO en tablas con sufijo _v2 en EDARSAHUB
- NO tiene scheduler activo (ejecución manual)

Sistemas soportados:
- SoftRestaurant: cheques + turnos + tempcheques
- MPRO: Venta_Encabezado + Comanda
"""

import uuid
import time
import logging
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Dict, Any, Optional, List, Tuple

from core.db import execute_sql_query

from .schemas import (
    KPIsDiariosV2,
    VentasDiaAbiertasV2,
    SyncLogV2,
    SyncRunType,
    SyncStatus,
    ConnectionStatus,
    UnidadNegocioConfig,
    SistemaOrigen,
    SyncResult
)
from .mappers import (
    map_softrestaurant_ventas_cerradas,
    map_softrestaurant_ventas_abiertas,
    map_mpro_ventas_cerradas,
    map_mpro_ventas_abiertas
)
from core.unidades_service import UnidadesService
from .repository_comercial_edarsahub import (
    EDARSAHUB_CONFIG,
    get_unidades_negocio_config,
    get_sucursales_mpro,
    upsert_kpi_diario,
    upsert_ventas_dia_abiertas,
    insert_sync_log
)

logger = logging.getLogger(__name__)


# =============================================================================
# CONFIGURACIÓN DE CONEXIONES A ORÍGENES
# =============================================================================

def get_server_connection_config(server_id: str) -> Optional[Dict[str, Any]]:
    """
    Obtiene la configuración de conexión de un servidor desde EDARSAHUB.
    NO hardcodea credenciales - las lee de la tabla Servidores_Conexiones.
    Descifra automáticamente la contraseña usando SERVER_SECRET_KEY.
    """
    try:
        from core.secret_manager import decrypt_secret
    except ImportError:
        decrypt_secret = lambda x: x
    
    try:
        from core.db import parse_sql_server_host
    except ImportError:
        def parse_sql_server_host(host, default_port):
            return (host, default_port, None)
    
    query = f"""
    SELECT 
        id,
        nombre,
        host,
        port,
        database_name,
        username,
        password_encrypted,
        system_type,
        activo
    FROM Servidores_Conexiones
    WHERE CAST(id AS VARCHAR(50)) = '{server_id}'
    """
    
    try:
        result = execute_sql_query(
            EDARSAHUB_CONFIG['host'],
            EDARSAHUB_CONFIG['port'],
            EDARSAHUB_CONFIG['database'],
            EDARSAHUB_CONFIG['username'],
            EDARSAHUB_CONFIG['password'],
            query
        )
        if not result:
            return None
        
        row = result[0]
        
        # Descifrar password
        pwd_enc = row.get('password_encrypted', '')
        try:
            password = decrypt_secret(pwd_enc)
        except Exception:
            password = pwd_enc  # Fallback a texto plano si falla
        
        # Parsear host (puede incluir puerto e instancia)
        host_raw = row.get('host', '')
        default_port = row.get('port') or 1433
        hostname, parsed_port, instance = parse_sql_server_host(host_raw, default_port)
        
        return {
            'id': str(row['id']),
            'nombre': row['nombre'],
            'host': hostname,
            'host_raw': host_raw,
            'port': parsed_port,
            'instance': instance,
            'database_name': row['database_name'],
            'username': row['username'],
            'password': password,
            'system_type': row['system_type'],
            'activo': row['activo']
        }
        
    except Exception as e:
        logger.error(f"Error obteniendo config de servidor {server_id}: {e}")
        return None


def execute_query_on_server(
    server_config: Dict[str, Any],
    query: str
) -> Tuple[List[Dict], ConnectionStatus]:
    """
    Ejecuta una query en un servidor de origen (SoftRestaurant/MPRO).
    Retorna los resultados y el estado de conexión.
    
    IMPORTANTE: execute_sql_query retorna [] tanto para errores como para 
    consultas sin resultados. Por eso usamos un flag especial para detectar 
    si la conexión realmente funcionó.
    """
    try:
        host = server_config.get('host', '')
        port = server_config.get('port', 1433)
        database = server_config.get('database_name', '')
        username = server_config.get('username', '')
        password = server_config.get('password', '')
        
        # Verificar primero si el servidor está en cooldown
        from core.db import is_server_offline_in_memory
        if is_server_offline_in_memory(host):
            logger.warning(f"Servidor {host} en cooldown - marcado como OFFLINE")
            return [], ConnectionStatus.OFFLINE
        
        result = execute_sql_query(
            host,
            port,
            database,
            username,
            password,
            query
        )
        
        # execute_sql_query retorna [] tanto para error como para consulta vacía.
        # Intentamos una query de prueba simple para confirmar conectividad si no hay resultados.
        if result is None:
            return [], ConnectionStatus.OFFLINE
        
        # Si obtuvimos resultados, claramente está ONLINE
        if result:
            return result, ConnectionStatus.ONLINE
        
        # Si no hay resultados, validamos con una query simple
        # para diferenciar "sin datos" de "sin conexión"
        test_query = "SELECT 1 AS test"
        test_result = execute_sql_query(host, port, database, username, password, test_query)
        
        if test_result:
            return [], ConnectionStatus.ONLINE  # Conexión OK, solo no hay datos
        else:
            logger.warning(f"Servidor {host} no respondió a query de prueba - marcado como OFFLINE")
            return [], ConnectionStatus.OFFLINE
        
    except Exception as e:
        error_str = str(e).lower()
        if 'timeout' in error_str:
            return [], ConnectionStatus.TIMEOUT
        else:
            logger.warning(f"Error conectando a servidor: {e}")
            return [], ConnectionStatus.OFFLINE


# =============================================================================
# QUERIES POR SISTEMA
# =============================================================================

# -------------------- SOFTRESTAURANT --------------------

QUERY_SOFTRESTAURANT_VENTAS_CERRADAS = """
SELECT 
    CAST(fecha AS DATE) as fecha,
    SUM(total) as ventas_total,
    SUM(total - ISNULL(propina, 0)) as ventas_sin_propina,
    SUM(ISNULL(propina, 0)) as propinas,
    COUNT(DISTINCT folio) as num_cheques,
    SUM(ISNULL(nopersonas, 1)) as num_personas
FROM cheques
WHERE CAST(fecha AS DATE) BETWEEN '{fecha_inicio}' AND '{fecha_fin}'
  AND cancelado = 0
  AND cierre IS NOT NULL  -- Solo cheques cerrados
GROUP BY CAST(fecha AS DATE)
ORDER BY fecha
"""

QUERY_SOFTRESTAURANT_VENTAS_ABIERTAS = """
SELECT 
    SUM(total) as ventas_abiertas,
    COUNT(DISTINCT folio) as tickets_abiertos,
    SUM(ISNULL(nopersonas, 1)) as pax_abiertos
FROM cheques
WHERE cancelado = 0
  AND cierre IS NULL  -- Cheques abiertos (sin cerrar)
  AND total > 0
"""


# -------------------- MPRO --------------------

QUERY_MPRO_VENTAS_CERRADAS = """
SELECT 
    CAST(ve.Vn_Fecha AS DATE) as fecha,
    SUM(ve.Vn_Precio_Neto_Importe) as Vn_Precio_Neto_Importe,
    COUNT(DISTINCT ve.Vn_Folio) as num_folios,
    SUM(ISNULL(c.Co_Personas, 1)) as total_personas
FROM Venta_Encabezado ve
LEFT JOIN Comanda c ON ve.Vn_Documento = c.Co_Folio AND ve.Sc_Cve_Sucursal = c.Sc_Cve_Sucursal
WHERE CAST(ve.Vn_Fecha AS DATE) BETWEEN '{fecha_inicio}' AND '{fecha_fin}'
  AND ve.Sc_Cve_Sucursal = '{sucursal_id}'
GROUP BY CAST(ve.Vn_Fecha AS DATE)
ORDER BY fecha
"""

QUERY_MPRO_VENTAS_ABIERTAS = """
SELECT 
    SUM(ve.Vn_Precio_Neto_Importe) as ventas_abiertas,
    COUNT(DISTINCT ve.Vn_Folio) as tickets_abiertos,
    SUM(ISNULL(c.Co_Personas, 1)) as pax_abiertos
FROM Venta_Encabezado ve
LEFT JOIN Comanda c ON ve.Vn_Documento = c.Co_Folio AND ve.Sc_Cve_Sucursal = c.Sc_Cve_Sucursal
WHERE CAST(ve.Vn_Fecha AS DATE) = CAST(GETDATE() AS DATE)
  AND ve.Sc_Cve_Sucursal = '{sucursal_id}'
  AND ve.Vn_Tabla = 'Comanda'  -- Ventas aún en comanda (no cerradas)
"""


# =============================================================================
# FUNCIONES DE SYNC POR SISTEMA
# =============================================================================

def sync_softrestaurant_ventas_cerradas(
    config: UnidadNegocioConfig,
    fecha_inicio: date,
    fecha_fin: date,
    run_id: str
) -> SyncResult:
    """
    Sincroniza ventas cerradas de SoftRestaurant hacia EDARSAHUB v2.
    """
    start_time = time.time()
    result = SyncResult(
        success=False,
        run_id=run_id,
        unidad_negocio_id=config.unidad_negocio_id
    )
    
    try:
        # Obtener configuración del servidor
        server_config = get_server_connection_config(config.server_id)
        if not server_config:
            result.error_message = f"No se encontró configuración para server_id {config.server_id}"
            return result
        
        # Ejecutar query
        query = QUERY_SOFTRESTAURANT_VENTAS_CERRADAS.format(
            fecha_inicio=fecha_inicio.isoformat(),
            fecha_fin=fecha_fin.isoformat()
        )
        
        rows, conn_status = execute_query_on_server(server_config, query)
        
        if conn_status != ConnectionStatus.ONLINE:
            result.error_message = f"Conexión fallida: {conn_status}"
            log = SyncLogV2(
                run_id=run_id,
                run_type=SyncRunType.INCREMENTAL,
                unidad_negocio_id=config.unidad_negocio_id,
                server_id=config.server_id,
                fecha_inicio=fecha_inicio,
                fecha_fin=fecha_fin,
                status=SyncStatus.FAILED,
                error_message=result.error_message,
                source_connection_status=conn_status,
                duration_seconds=int(time.time() - start_time)
            )
            insert_sync_log(log)
            return result
        
        # Procesar cada día
        inserted = 0
        updated = 0
        skipped = 0
        errored = 0
        
        for row in rows:
            try:
                kpi = map_softrestaurant_ventas_cerradas(row, config, run_id)
                upsert_result = upsert_kpi_diario(kpi)
                
                if upsert_result['action'] == 'INSERT':
                    inserted += 1
                elif upsert_result['action'] == 'UPDATE':
                    updated += 1
                else:
                    skipped += 1
                    
            except Exception as e:
                logger.error(f"Error procesando fila SR: {e}")
                errored += 1
        
        # Registrar en log
        result.success = errored == 0
        result.records_processed = len(rows)
        result.records_inserted = inserted
        result.records_updated = updated
        result.records_skipped = skipped
        result.records_errored = errored
        result.duration_seconds = int(time.time() - start_time)
        
        log = SyncLogV2(
            run_id=run_id,
            run_type=SyncRunType.INCREMENTAL,
            unidad_negocio_id=config.unidad_negocio_id,
            server_id=config.server_id,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            status=SyncStatus.SUCCESS if result.success else SyncStatus.PARTIAL,
            records_processed=result.records_processed,
            records_inserted=inserted,
            records_updated=updated,
            records_skipped=skipped,
            records_errored=errored,
            source_connection_status=ConnectionStatus.ONLINE,
            duration_seconds=result.duration_seconds
        )
        insert_sync_log(log)
        
        return result
        
    except Exception as e:
        result.error_message = str(e)
        logger.error(f"Error en sync SoftRestaurant: {e}")
        return result


def sync_mpro_ventas_cerradas(
    config: UnidadNegocioConfig,
    sucursal_id: str,
    fecha_inicio: date,
    fecha_fin: date,
    run_id: str
) -> SyncResult:
    """
    Sincroniza ventas cerradas de MPRO hacia EDARSAHUB v2.
    MPRO tiene múltiples sucursales por servidor.
    """
    start_time = time.time()
    result = SyncResult(
        success=False,
        run_id=run_id,
        unidad_negocio_id=config.unidad_negocio_id
    )
    
    try:
        # Obtener configuración del servidor
        server_config = get_server_connection_config(config.server_id)
        if not server_config:
            result.error_message = f"No se encontró configuración para server_id {config.server_id}"
            return result
        
        # Ejecutar query con sucursal específica
        query = QUERY_MPRO_VENTAS_CERRADAS.format(
            fecha_inicio=fecha_inicio.isoformat(),
            fecha_fin=fecha_fin.isoformat(),
            sucursal_id=sucursal_id
        )
        
        rows, conn_status = execute_query_on_server(server_config, query)
        
        if conn_status != ConnectionStatus.ONLINE:
            result.error_message = f"Conexión fallida: {conn_status}"
            log = SyncLogV2(
                run_id=run_id,
                run_type=SyncRunType.INCREMENTAL,
                unidad_negocio_id=config.unidad_negocio_id,
                server_id=config.server_id,
                sucursal_id=sucursal_id,
                fecha_inicio=fecha_inicio,
                fecha_fin=fecha_fin,
                status=SyncStatus.FAILED,
                error_message=result.error_message,
                source_connection_status=conn_status,
                duration_seconds=int(time.time() - start_time)
            )
            insert_sync_log(log)
            return result
        
        # Actualizar config con sucursal específica para el mapeo
        config_with_sucursal = UnidadNegocioConfig(
            unidad_negocio_id=config.unidad_negocio_id,
            unidad_negocio_nombre=config.unidad_negocio_nombre,
            server_id=config.server_id,
            sucursal_id=sucursal_id,
            sucursal_nombre=config.sucursal_nombre,
            sistema_origen=SistemaOrigen.MPRO,
            activo=True
        )
        
        # Procesar cada día
        inserted = 0
        updated = 0
        skipped = 0
        errored = 0
        
        for row in rows:
            try:
                kpi = map_mpro_ventas_cerradas(row, config_with_sucursal, run_id)
                upsert_result = upsert_kpi_diario(kpi)
                
                if upsert_result['action'] == 'INSERT':
                    inserted += 1
                elif upsert_result['action'] == 'UPDATE':
                    updated += 1
                else:
                    skipped += 1
                    
            except Exception as e:
                logger.error(f"Error procesando fila MPRO: {e}")
                errored += 1
        
        # Registrar resultado
        result.success = errored == 0
        result.records_processed = len(rows)
        result.records_inserted = inserted
        result.records_updated = updated
        result.records_skipped = skipped
        result.records_errored = errored
        result.duration_seconds = int(time.time() - start_time)
        
        log = SyncLogV2(
            run_id=run_id,
            run_type=SyncRunType.INCREMENTAL,
            unidad_negocio_id=config.unidad_negocio_id,
            server_id=config.server_id,
            sucursal_id=sucursal_id,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            status=SyncStatus.SUCCESS if result.success else SyncStatus.PARTIAL,
            records_processed=result.records_processed,
            records_inserted=inserted,
            records_updated=updated,
            records_skipped=skipped,
            records_errored=errored,
            source_connection_status=ConnectionStatus.ONLINE,
            duration_seconds=result.duration_seconds
        )
        insert_sync_log(log)
        
        return result
        
    except Exception as e:
        result.error_message = str(e)
        logger.error(f"Error en sync MPRO: {e}")
        return result


# =============================================================================
# FUNCIONES DE SYNC DE ALTO NIVEL
# =============================================================================

def sync_unidad_ventas_cerradas(
    unidad_config: UnidadNegocioConfig,
    fecha_inicio: date,
    fecha_fin: date
) -> SyncResult:
    """
    Sincroniza ventas cerradas de una unidad específica.
    Detecta automáticamente si es SoftRestaurant o MPRO.
    """
    run_id = str(uuid.uuid4())[:8]
    
    if unidad_config.sistema_origen == SistemaOrigen.SOFTRESTAURANT:
        return sync_softrestaurant_ventas_cerradas(
            unidad_config, fecha_inicio, fecha_fin, run_id
        )
    elif unidad_config.sistema_origen == SistemaOrigen.MPRO:
        return sync_mpro_ventas_cerradas(
            unidad_config,
            unidad_config.sucursal_id,
            fecha_inicio,
            fecha_fin,
            run_id
        )
    else:
        return SyncResult(
            success=False,
            run_id=run_id,
            unidad_negocio_id=unidad_config.unidad_negocio_id,
            error_message=f"Sistema no soportado: {unidad_config.sistema_origen}"
        )


def sync_todas_unidades_ventas_cerradas(
    fecha_inicio: date,
    fecha_fin: date
) -> List[SyncResult]:
    """
    Sincroniza ventas cerradas de TODAS las unidades activas.
    NO EJECUTAR en Subfase 1 - Solo para referencia.
    """
    results = []
    configs = get_unidades_negocio_config()
    
    for config in configs:
        logger.info(f"Sincronizando {config.unidad_negocio_nombre}...")
        
        if config.sistema_origen == SistemaOrigen.MPRO:
            # MPRO tiene múltiples sucursales
            sucursales = get_sucursales_mpro(config.server_id)
            for suc in sucursales:
                suc_config = UnidadNegocioConfig(
                    unidad_negocio_id=suc['unidad_id'],
                    unidad_negocio_nombre=suc['nombre'],
                    server_id=config.server_id,
                    sucursal_id=suc['sucursal_id'],
                    sucursal_nombre=suc['nombre'],
                    sistema_origen=SistemaOrigen.MPRO,
                    activo=True
                )
                result = sync_unidad_ventas_cerradas(suc_config, fecha_inicio, fecha_fin)
                results.append(result)
        else:
            result = sync_unidad_ventas_cerradas(config, fecha_inicio, fecha_fin)
            results.append(result)
    
    return results


# =============================================================================
# FUNCIÓN DE PRUEBA CONTROLADA (Subfase 1)
# =============================================================================

def test_sync_una_unidad_softrestaurant(
    fecha: date = None
) -> SyncResult:
    """
    PRUEBA CONTROLADA: Sincroniza 1 día de 1 unidad SoftRestaurant.
    Usado para validación inicial en Subfase 1.
    
    Unidad de prueba: LA ESTELAR (SoftRestaurant)
    
    FASE P0 (2026-05-13): Actualizado a código canónico ESTELAR
    """
    if fecha is None:
        fecha = date.today() - timedelta(days=1)  # Ayer
    
    # Configuración de LA ESTELAR con código canónico
    config = UnidadNegocioConfig(
        unidad_negocio_id='ESTELAR',  # FASE P0: Código canónico oficial
        unidad_negocio_nombre='LA ESTELAR',
        server_id='a5ff0e25-f029-43db-b634-d4ac814c904f',
        sucursal_id='DEFAULT',
        sucursal_nombre='LA ESTELAR',
        sistema_origen=SistemaOrigen.SOFTRESTAURANT,
        activo=True
    )
    
    return sync_unidad_ventas_cerradas(config, fecha, fecha)


def test_sync_una_unidad_mpro(
    fecha: date = None
) -> SyncResult:
    """
    PRUEBA CONTROLADA: Sincroniza 1 día de 1 unidad MPRO.
    Usado para validación inicial en Subfase 1.
    
    Unidad de prueba: 130° QUERETARO (MPRO sucursal 0021)
    
    FASE P0 (2026-05-13): Actualizado a código canónico 130QRO
    """
    if fecha is None:
        fecha = date.today() - timedelta(days=1)  # Ayer
    
    # Configuración de 130° QRO con código canónico
    config = UnidadNegocioConfig(
        unidad_negocio_id='130QRO',  # FASE P0: Código canónico oficial
        unidad_negocio_nombre='130° QUERETARO',
        server_id='1b230a06-ffaf-4c70-bd27-b1be3579dea6',
        sucursal_id='0021',
        sucursal_nombre='130° QUERETARO',
        sistema_origen=SistemaOrigen.MPRO,
        activo=True
    )
    
    return sync_unidad_ventas_cerradas(config, fecha, fecha)


# =============================================================================
# EJECUCIÓN DIRECTA (Solo para pruebas manuales)
# =============================================================================

if __name__ == "__main__":
    """
    Ejecutar manualmente para probar:
    cd /app/backend && python -m modules.comercial_v2.sync_comercial_edarsahub
    """
    import sys
    logging.basicConfig(level=logging.INFO)
    
    print("=" * 60)
    print("SYNC COMERCIAL V2 - Prueba Manual")
    print("=" * 60)
    print("\nEste script NO debe ejecutarse en producción.")
    print("Para pruebas controladas, usar las funciones test_sync_*")
    print("\nDisponibles:")
    print("  - test_sync_una_unidad_softrestaurant(fecha)")
    print("  - test_sync_una_unidad_mpro(fecha)")


# ============================================================
# P1 - Unidades dinámicas desde SQL
# No usar códigos hardcodeados como llave operativa.
# ============================================================

def _sync_codigos_unidades_activas():
    return UnidadesService.get_codigos()

