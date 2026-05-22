"""
REPOSITORY EDARSAHUB - Comercial V2
===================================

Funciones de acceso a datos para las tablas Comercial_*_v2 en EDARSAHUB.
Incluye operaciones CRUD y funciones de sincronización.

IMPORTANTE:
- Este repositorio SOLO escribe en tablas con sufijo _v2
- NO toca las tablas existentes (Comercial_KPIs_Historico, etc.)
- Usa upsert idempotente basado en hash_origen
"""

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Dict, Any, Optional, List
import logging

from core.db import execute_sql_query
from .schemas import (
    KPIsDiariosV2,
    VentasDiaAbiertasV2,
    SyncLogV2,
    SyncStatus,
    ConnectionStatus,
    UnidadNegocioConfig,
    SistemaOrigen
)

logger = logging.getLogger(__name__)


# =============================================================================
# CONFIGURACIÓN EDARSAHUB
# =============================================================================

EDARSAHUB_CONFIG = {
    'host': '54.39.104.176',
    'port': 1433,
    'database': 'EDARSAHUB',
    'username': 'HRLectura',
    'password': 'National09$'
}


def _execute_query(query: str, params: dict = None) -> List[Dict]:
    """Ejecuta una query en EDARSAHUB y retorna resultados"""
    try:
        result = execute_sql_query(
            EDARSAHUB_CONFIG['host'],
            EDARSAHUB_CONFIG['port'],
            EDARSAHUB_CONFIG['database'],
            EDARSAHUB_CONFIG['username'],
            EDARSAHUB_CONFIG['password'],
            query
        )
        return result or []
    except Exception as e:
        logger.error(f"Error ejecutando query EDARSAHUB: {e}")
        raise


# =============================================================================
# OBTENER CONFIGURACIÓN DE UNIDADES
# =============================================================================

def get_unidades_negocio_config() -> List[UnidadNegocioConfig]:
    """
    Obtiene la configuración de unidades de negocio desde EDARSAHUB.
    Lee de Servidores_Conexiones para no hardcodear.
    
    Retorna lista de UnidadNegocioConfig con las 5 unidades activas.
    """
    # FIX IDENTIDAD CANÓNICA (2026-05-16): Usar códigos CANÓNICOS, no aliases legacy
    query = """
    SELECT 
        id as server_id,
        nombre as unidad_nombre,
        system_type,
        host,
        CASE 
            WHEN nombre LIKE '%MERIDA%' OR nombre LIKE '%MID%' THEN '130MID'
            WHEN nombre LIKE '%CIENFUEGOS%' AND nombre NOT LIKE '%TABLAJERIA%' THEN 'CIENFUEGOS'
            WHEN nombre LIKE '%ESTELAR%' THEN 'ESTELAR'
            WHEN nombre = 'ManagmentPro' THEN 'MPRO-MULTI'
            ELSE REPLACE(UPPER(nombre), ' ', '-')
        END as unidad_id_calculado
    FROM Servidores_Conexiones
    WHERE activo = 1 
      AND (tipo_conexion = 'DATA_SOURCE' OR tipo_conexion IS NULL)
      AND nombre NOT LIKE '%TABLAJERIA%'
      AND nombre NOT LIKE '%PRUEBA%'
      AND nombre NOT LIKE '%ESCRITURA%'
    ORDER BY nombre
    """
    
    rows = _execute_query(query)
    
    configs = []
    for row in rows:
        system_type = row.get('system_type', '').upper()
        if 'SOFT' in system_type:
            sistema = SistemaOrigen.SOFTRESTAURANT
        elif 'MPRO' in system_type or 'MANAG' in system_type:
            sistema = SistemaOrigen.MPRO
        else:
            continue  # Ignorar tipos desconocidos
        
        configs.append(UnidadNegocioConfig(
            unidad_negocio_id=row['unidad_id_calculado'],
            unidad_negocio_nombre=row['unidad_nombre'],
            server_id=str(row['server_id']),  # Convertir UUID a string
            sucursal_id='DEFAULT',
            sucursal_nombre=row['unidad_nombre'],
            sistema_origen=sistema,
            activo=True
        ))
    
    return configs


def get_sucursales_mpro(server_id: str) -> List[Dict[str, str]]:
    """
    Para MPRO, obtiene las sucursales específicas (QRO=0021, ORIGEN=0023).
    MPRO tiene múltiples sucursales en un solo server_id.
    
    FIX IDENTIDAD CANÓNICA (2026-05-16): Usar códigos CANÓNICOS
    """
    # Mapeo conocido de sucursales MPRO con códigos CANÓNICOS
    return [
        {'sucursal_id': '0021', 'nombre': '130° QUERÉTARO', 'unidad_id': '130QRO'},
        {'sucursal_id': '0023', 'nombre': 'ORIGEN', 'unidad_id': 'ORIGEN'},
    ]


# =============================================================================
# OPERACIONES EN Comercial_KPIs_Diarios_v2
# =============================================================================

def upsert_kpi_diario(kpi: KPIsDiariosV2) -> Dict[str, Any]:
    """
    Inserta o actualiza un KPI diario en Comercial_KPIs_Diarios_v2.
    
    Lógica:
    1. Busca registro existente por (unidad_negocio_id, sucursal_id, fecha_operacion)
    2. Si existe con mismo hash_origen → SKIP
    3. Si existe con diferente hash → UPDATE con version++
    4. Si no existe → INSERT
    
    Retorna: {'action': 'INSERT'|'UPDATE'|'SKIP', 'id': uuid}
    """
    # Verificar si existe
    check_query = f"""
    SELECT id, hash_origen, version 
    FROM Comercial_KPIs_Diarios_v2
    WHERE unidad_negocio_id = '{kpi.unidad_negocio_id}'
      AND sucursal_id = '{kpi.sucursal_id}'
      AND fecha_operacion = '{kpi.fecha_operacion.isoformat()}'
    """
    
    existing = _execute_query(check_query)
    
    if existing:
        record = existing[0]
        if record.get('hash_origen') == kpi.hash_origen:
            # Mismos datos, no actualizar
            return {'action': 'SKIP', 'id': record.get('id')}
        else:
            # Datos diferentes, actualizar
            new_version = (record.get('version') or 1) + 1
            update_query = f"""
            UPDATE Comercial_KPIs_Diarios_v2 SET
                ventas_total = {kpi.ventas_total},
                ventas_sin_propina = {kpi.ventas_sin_propina},
                propinas_total = {kpi.propinas_total},
                tickets_total = {kpi.tickets_total},
                pax_total = {kpi.pax_total},
                ticket_promedio = {kpi.ticket_promedio},
                pax_promedio = {kpi.pax_promedio},
                ventas_cerradas = {kpi.ventas_cerradas},
                ventas_abiertas = {kpi.ventas_abiertas},
                total_estimado_dia = {kpi.total_estimado_dia},
                es_corte_cerrado = {1 if kpi.es_corte_cerrado else 0},
                hash_origen = '{kpi.hash_origen}',
                sync_run_id = '{kpi.sync_run_id}',
                fecha_ultima_actualizacion = SYSUTCDATETIME(),
                version = {new_version}
            WHERE id = '{record.get("id")}'
            """
            _execute_query(update_query)
            return {'action': 'UPDATE', 'id': record.get('id')}
    else:
        # No existe, insertar
        new_id = str(uuid.uuid4())
        insert_query = f"""
        INSERT INTO Comercial_KPIs_Diarios_v2 (
            id, unidad_negocio_id, unidad_negocio_nombre, server_id, sucursal_id,
            sucursal_nombre, sistema_origen, fecha_operacion, anio, mes, dia,
            ventas_total, ventas_sin_propina, propinas_total, tickets_total, pax_total,
            ticket_promedio, pax_promedio, ventas_cerradas, ventas_abiertas, total_estimado_dia,
            es_venta_abierta, es_corte_cerrado, es_demo, activo,
            fuente_original, id_origen, hash_origen, sync_run_id,
            fecha_sincronizacion, fecha_alta, fecha_ultima_actualizacion, version
        ) VALUES (
            '{new_id}', 
            '{kpi.unidad_negocio_id}', 
            '{kpi.unidad_negocio_nombre}',
            '{kpi.server_id}', 
            '{kpi.sucursal_id}',
            {f"'{kpi.sucursal_nombre}'" if kpi.sucursal_nombre else 'NULL'},
            '{kpi.sistema_origen}',
            '{kpi.fecha_operacion.isoformat()}',
            {kpi.anio}, {kpi.mes}, {kpi.dia},
            {kpi.ventas_total}, {kpi.ventas_sin_propina}, {kpi.propinas_total},
            {kpi.tickets_total}, {kpi.pax_total}, {kpi.ticket_promedio}, {kpi.pax_promedio},
            {kpi.ventas_cerradas}, {kpi.ventas_abiertas}, {kpi.total_estimado_dia},
            {1 if kpi.es_venta_abierta else 0},
            {1 if kpi.es_corte_cerrado else 0},
            {1 if kpi.es_demo else 0},
            {1 if kpi.activo else 0},
            '{kpi.fuente_original}',
            {f"'{kpi.id_origen}'" if kpi.id_origen else 'NULL'},
            '{kpi.hash_origen}',
            '{kpi.sync_run_id}',
            SYSUTCDATETIME(), SYSUTCDATETIME(), SYSUTCDATETIME(), 1
        )
        """
        _execute_query(insert_query)
        return {'action': 'INSERT', 'id': new_id}


def get_kpis_diarios_v2(
    unidad_negocio_id: str,
    fecha_inicio: date,
    fecha_fin: date
) -> List[Dict]:
    """Lee KPIs diarios v2 para un rango de fechas"""
    query = f"""
    SELECT *
    FROM Comercial_KPIs_Diarios_v2
    WHERE unidad_negocio_id = '{unidad_negocio_id}'
      AND fecha_operacion BETWEEN '{fecha_inicio.isoformat()}' AND '{fecha_fin.isoformat()}'
      AND activo = 1
    ORDER BY fecha_operacion
    """
    return _execute_query(query)


# =============================================================================
# OPERACIONES EN Comercial_Ventas_Dia_Abiertas_v2
# =============================================================================

def upsert_ventas_dia_abiertas(ventas: VentasDiaAbiertasV2) -> Dict[str, Any]:
    """
    Upsert de snapshot de ventas abiertas.
    Solo mantiene 1 registro por unidad (sobrescribe).
    
    REGLAS:
    1. ANTI-$0 FALSO: Si el nuevo valor es $0 pero existe un snapshot válido 
       con venta > 0 para la MISMA fecha_operacion, NO sobrescribir.
    2. FECHA CORRECTA: Si la nueva fecha_operacion es DIFERENTE, siempre actualizar
       (esto permite corregir datos con fecha incorrecta).
    3. BARRERA P0C: Validar que FechaOperacion coincida con get_operational_window().
    """
    import logging
    import os
    import traceback
    logger = logging.getLogger(__name__)
    
    # =========================================================================
    # BARRERA P0C: Validación de trazabilidad y FechaOperacion
    # =========================================================================
    caller_info = traceback.extract_stack()[-3] if len(traceback.extract_stack()) >= 3 else None
    caller_file = caller_info.filename if caller_info else "UNKNOWN"
    caller_func = caller_info.name if caller_info else "UNKNOWN"
    
    # VALIDACIÓN 1: Debe tener run_id válido
    if not ventas.sync_run_id or not ventas.sync_run_id.startswith("ABIERTA-"):
        logger.error(
            f"[BARRERA-P0C] BLOQUEADO: run_id inválido. "
            f"unidad={ventas.unidad_negocio_id}, run_id={ventas.sync_run_id}, "
            f"caller={caller_file}::{caller_func}, pid={os.getpid()}"
        )
        return {
            'action': 'BLOCKED_INVALID_RUNID',
            'reason': f'run_id inválido: {ventas.sync_run_id}',
            'caller': f'{caller_file}::{caller_func}'
        }
    
    # VALIDACIÓN 2: FechaOperacion debe coincidir con get_operational_window()
    try:
        from core.utils.operational_window import get_operational_window
        resultado_ventana = get_operational_window(ventas.unidad_negocio_id)
        fecha_correcta = resultado_ventana.fecha_operacion
        fecha_recibida = ventas.fecha_operacion
        
        # Convertir a date si es necesario
        if hasattr(fecha_recibida, 'date'):
            fecha_recibida = fecha_recibida.date()
        if hasattr(fecha_correcta, 'date'):
            fecha_correcta = fecha_correcta.date()
        
        if str(fecha_recibida) != str(fecha_correcta):
            logger.error(
                f"[BARRERA-P0C] BLOQUEADO: FechaOperacion incorrecta. "
                f"unidad={ventas.unidad_negocio_id}, "
                f"recibida={fecha_recibida}, correcta={fecha_correcta}, "
                f"run_id={ventas.sync_run_id}, "
                f"caller={caller_file}::{caller_func}, pid={os.getpid()}"
            )
            return {
                'action': 'BLOCKED_WRONG_FECHA',
                'reason': f'FechaOperacion incorrecta: recibida={fecha_recibida}, correcta={fecha_correcta}',
                'caller': f'{caller_file}::{caller_func}',
                'fecha_recibida': str(fecha_recibida),
                'fecha_correcta': str(fecha_correcta)
            }
    except Exception as e:
        logger.warning(f"[BARRERA-P0C] No se pudo validar FechaOperacion: {e}")
    
    # Log diagnóstico obligatorio con call stack
    logger.info(
        f"[UPSERT-DIAG] unidad={ventas.unidad_negocio_id}, "
        f"fecha_op={ventas.fecha_operacion}, "
        f"total=${ventas.total_estimado_dia:,.2f}, "
        f"fuente={ventas.fuente_original}, "
        f"run_id={ventas.sync_run_id}, "
        f"pid={os.getpid()}, "
        f"caller={caller_file}::{caller_func}"
    )
    
    # =================================================================
    # GUARD RAIL P0.H (REPOSITORY): BLOQUEAR FECHA FUTURA
    # Esta es la ÚLTIMA línea de defensa antes de escribir en SQL
    # =================================================================
    from datetime import datetime
    import pytz
    mexico_tz = pytz.timezone('America/Mexico_City')
    fecha_hoy_mx = datetime.now(mexico_tz).date()
    
    if ventas.fecha_operacion > fecha_hoy_mx:
        logger.error(
            f"[UPSERT-GUARD-RAIL] ⛔ BLOQUEADO: fecha_operacion={ventas.fecha_operacion} > "
            f"fecha_hoy={fecha_hoy_mx}. Unidad={ventas.unidad_negocio_id}, run_id={ventas.sync_run_id}"
        )
        return {
            'action': 'BLOCKED_FUTURE_DATE',
            'reason': f'fecha_operacion futura: {ventas.fecha_operacion} > {fecha_hoy_mx}',
            'unidad': ventas.unidad_negocio_id
        }
    
    # Verificar si existe y obtener valores actuales
    check_query = f"""
    SELECT id, total_estimado_dia, fecha_operacion, sync_run_id
    FROM Comercial_Ventas_Dia_Abiertas_v2
    WHERE unidad_negocio_id = '{ventas.unidad_negocio_id}'
      AND sucursal_id = '{ventas.sucursal_id}'
    """
    
    existing = _execute_query(check_query)
    
    if existing:
        record_id = existing[0].get('id')
        existing_total = float(existing[0].get('total_estimado_dia') or 0)
        existing_fecha = str(existing[0].get('fecha_operacion'))
        new_fecha = str(ventas.fecha_operacion)
        
        # =================================================================
        # REGLA 1: Si la fecha_operacion es DIFERENTE, SIEMPRE actualizar
        # Esto permite corregir datos con fecha incorrecta
        # =================================================================
        if existing_fecha != new_fecha:
            logger.warning(
                f"[UPSERT-FECHA] {ventas.unidad_negocio_id}: Actualizando fecha "
                f"{existing_fecha} -> {new_fecha}, "
                f"total existente=${existing_total:,.2f}, nuevo=${ventas.total_estimado_dia:,.2f}"
            )
            # Continuar con UPDATE (no retornar)
        
        # =================================================================
        # REGLA 2: ANTI-$0 FALSO (solo aplica si MISMA fecha_operacion)
        # =================================================================
        elif ventas.total_estimado_dia == 0 and existing_total > 0:
            # Nueva venta es $0 pero existe snapshot válido con venta > 0
            # MISMA fecha_operacion -> NO sobrescribir
            logger.warning(
                f"[ANTI-$0] PROTECCIÓN ACTIVADA para {ventas.unidad_negocio_id}: "
                f"Nuevo=${ventas.total_estimado_dia:,.2f}, Existente=${existing_total:,.2f}, "
                f"FechaOp={new_fecha}. NO se sobrescribe."
            )
            return {
                'action': 'SKIP_ANTI_ZERO', 
                'id': record_id,
                'reason': f'Protección anti-$0: existente=${existing_total:,.2f}',
                'preserved_total': existing_total
            }
        
        update_query = f"""
        UPDATE Comercial_Ventas_Dia_Abiertas_v2 SET
            server_id = '{ventas.server_id}',
            snapshot_timestamp = '{ventas.snapshot_timestamp.isoformat()}',
            fecha_operacion = '{ventas.fecha_operacion.isoformat()}',
            ventas_abiertas = {ventas.ventas_abiertas},
            tickets_abiertos = {ventas.tickets_abiertos},
            pax_abiertos = {ventas.pax_abiertos},
            ventas_cerradas_dia = {ventas.ventas_cerradas_dia},
            tickets_cerrados_dia = {ventas.tickets_cerrados_dia},
            pax_cerrados_dia = {ventas.pax_cerrados_dia},
            total_estimado_dia = {ventas.total_estimado_dia},
            fuente_original = '{ventas.fuente_original}',
            sync_run_id = '{ventas.sync_run_id}',
            fecha_ultima_actualizacion = SYSUTCDATETIME()
        WHERE id = '{record_id}'
        """
        _execute_query(update_query)
        logger.info(f"[UPSERT] UPDATE {ventas.unidad_negocio_id}: ${ventas.total_estimado_dia:,.2f}, fecha={ventas.fecha_operacion}")
        return {'action': 'UPDATE', 'id': record_id}
    else:
        new_id = str(uuid.uuid4())
        insert_query = f"""
        INSERT INTO Comercial_Ventas_Dia_Abiertas_v2 (
            id, unidad_negocio_id, unidad_negocio_nombre, server_id, sucursal_id,
            sucursal_nombre, sistema_origen, snapshot_timestamp, fecha_operacion,
            ventas_abiertas, tickets_abiertos, pax_abiertos,
            ventas_cerradas_dia, tickets_cerrados_dia, pax_cerrados_dia,
            total_estimado_dia, fuente_original, sync_run_id, fecha_ultima_actualizacion
        ) VALUES (
            '{new_id}',
            '{ventas.unidad_negocio_id}',
            '{ventas.unidad_negocio_nombre}',
            '{ventas.server_id}',
            '{ventas.sucursal_id}',
            {f"'{ventas.sucursal_nombre}'" if ventas.sucursal_nombre else 'NULL'},
            '{ventas.sistema_origen}',
            '{ventas.snapshot_timestamp.isoformat()}',
            '{ventas.fecha_operacion.isoformat()}',
            {ventas.ventas_abiertas}, {ventas.tickets_abiertos}, {ventas.pax_abiertos},
            {ventas.ventas_cerradas_dia}, {ventas.tickets_cerrados_dia}, {ventas.pax_cerrados_dia},
            {ventas.total_estimado_dia},
            '{ventas.fuente_original}',
            '{ventas.sync_run_id}',
            SYSUTCDATETIME()
        )
        """
        _execute_query(insert_query)
        logger.info(f"[UPSERT] INSERT {ventas.unidad_negocio_id}: ${ventas.total_estimado_dia:,.2f}")
        return {'action': 'INSERT', 'id': new_id}


# =============================================================================
# OPERACIONES EN Comercial_SyncLog_v2
# =============================================================================

def insert_sync_log(log: SyncLogV2) -> str:
    """Inserta un registro en el log de sincronización"""
    new_id = str(uuid.uuid4())
    
    insert_query = f"""
    INSERT INTO Comercial_SyncLog_v2 (
        id, run_id, run_timestamp, run_type,
        unidad_negocio_id, server_id, sucursal_id,
        fecha_inicio, fecha_fin,
        status, records_processed, records_inserted, records_updated, 
        records_skipped, records_errored,
        error_code, error_message, duration_seconds, source_connection_status,
        created_at
    ) VALUES (
        '{new_id}',
        '{log.run_id}',
        SYSUTCDATETIME(),
        '{log.run_type}',
        {f"'{log.unidad_negocio_id}'" if log.unidad_negocio_id else 'NULL'},
        {f"'{log.server_id}'" if log.server_id else 'NULL'},
        {f"'{log.sucursal_id}'" if log.sucursal_id else 'NULL'},
        {f"'{log.fecha_inicio.isoformat()}'" if log.fecha_inicio else 'NULL'},
        {f"'{log.fecha_fin.isoformat()}'" if log.fecha_fin else 'NULL'},
        '{log.status}',
        {log.records_processed},
        {log.records_inserted},
        {log.records_updated},
        {log.records_skipped},
        {log.records_errored},
        {f"'{log.error_code}'" if log.error_code else 'NULL'},
        {f"'{str(log.error_message)[:500]}'" if log.error_message else 'NULL'},
        {log.duration_seconds if log.duration_seconds else 'NULL'},
        {f"'{log.source_connection_status}'" if log.source_connection_status else 'NULL'},
        SYSUTCDATETIME()
    )
    """
    _execute_query(insert_query)
    return new_id


def get_last_sync_log(unidad_negocio_id: str) -> Optional[Dict]:
    """Obtiene el último log de sincronización para una unidad"""
    query = f"""
    SELECT TOP 1 *
    FROM Comercial_SyncLog_v2
    WHERE unidad_negocio_id = '{unidad_negocio_id}'
    ORDER BY run_timestamp DESC
    """
    result = _execute_query(query)
    return result[0] if result else None


# =============================================================================
# ESTADÍSTICAS Y VERIFICACIÓN
# =============================================================================

def get_stats_kpis_diarios_v2() -> Dict[str, Any]:
    """Obtiene estadísticas de la tabla KPIs Diarios v2"""
    query = """
    SELECT 
        COUNT(*) as total_registros,
        COUNT(DISTINCT unidad_negocio_id) as total_unidades,
        MIN(fecha_operacion) as fecha_min,
        MAX(fecha_operacion) as fecha_max,
        SUM(ventas_total) as ventas_totales
    FROM Comercial_KPIs_Diarios_v2
    WHERE activo = 1
    """
    result = _execute_query(query)
    return result[0] if result else {}


def get_stats_by_unidad_v2() -> List[Dict]:
    """Obtiene estadísticas agrupadas por unidad"""
    query = """
    SELECT 
        unidad_negocio_id,
        unidad_negocio_nombre,
        sistema_origen,
        COUNT(*) as registros,
        MIN(fecha_operacion) as desde,
        MAX(fecha_operacion) as hasta,
        SUM(ventas_total) as ventas_totales
    FROM Comercial_KPIs_Diarios_v2
    WHERE activo = 1
    GROUP BY unidad_negocio_id, unidad_negocio_nombre, sistema_origen
    ORDER BY unidad_negocio_id
    """
    return _execute_query(query)
