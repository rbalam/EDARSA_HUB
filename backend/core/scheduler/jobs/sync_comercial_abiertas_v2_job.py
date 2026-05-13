"""
EDARSA HUB - Job de Sincronización de Ventas Abiertas Comercial V2
===================================================================

P0 JOB VENTAS ABIERTAS COMERCIAL V2 CADA 5 MINUTOS

Este job sincroniza ventas del día en curso (operación abierta) desde 
SoftRestaurant y MPRO hacia EDARSAHUB cada 5 minutos (configurable).

CARACTERÍSTICAS:
- Sincroniza SOLO ventas abiertas del día actual (sin CORTE_Z)
- Idempotente: upsert por unidad (sobrescribe snapshot anterior)
- Tolerante a fallos (una unidad falla, las demás continúan)
- Lock distribuido (MongoDB) para evitar ejecuciones simultáneas
- SyncLog detallado por unidad

UNIDADES SOPORTADAS (5):
- SoftRestaurant: 130MID (130° MÉRIDA), CIENFUEGOS, ESTELAR (LA ESTELAR)
- MPRO: 130QRO (130° QUERETARO, sucursal 0021), ORIGEN (sucursal 0023)

DIFERENCIA CON JOB DE CERRADAS (sync_comercial_v2_job.py):
- sync_comercial_v2_job.py: Ventas cerradas (CORTE_Z NOT NULL) → Comercial_KPIs_Diarios_v2
- sync_comercial_abiertas_v2_job.py: Ventas abiertas (CORTE_Z IS NULL) → Comercial_Ventas_Dia_Abiertas_v2

NO DUPLICAN:
- Tablas diferentes
- Filtros opuestos (CORTE_Z NULL vs NOT NULL)

MÁXIMAS RESPETADAS:
- EDARSAHUB es el cerebro (destino de sincronización)
- No depende de conexiones en vivo para pintar dashboards
- Datos demo aislados (es_demo=0 para datos reales)
- MongoDB solo para locks técnicos, NO para datos de negocio

FASE P0 (2026-05-13):
- Códigos canónicos desde Unidades_Negocio.codigo (EDARSAHUB)
- NO usar códigos legacy (130-MER, 130-QRO, LA-ESTELAR)
- CÓDIGOS OFICIALES: 130MID, 130QRO, CIENFUEGOS, ESTELAR, ORIGEN

Autor: E1 Agent
Fecha: 2026-05-01
Actualizado: 2026-05-13 (FASE P0 - códigos canónicos)
"""

import os
import uuid
import logging
from datetime import datetime, date, timezone
from decimal import Decimal
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

# Configuración
JOB_NAME = "sync_comercial_abiertas_v2"
SYNC_INTERVAL_SECONDS = int(os.environ.get("SCHEDULER_SYNC_COMERCIAL_ABIERTAS_V2_INTERVAL_SECONDS", "300"))


# =============================================================================
# CONFIGURACIÓN DE UNIDADES - FASE P0
# =============================================================================
# Las unidades se cargan dinámicamente desde EDARSAHUB.Unidades_Negocio
# usando el módulo core.unidades_registry
# 
# CÓDIGOS OFICIALES (Unidades_Negocio.codigo):
# - 130MID (130° MÉRIDA)
# - CIENFUEGOS
# - ESTELAR (LA ESTELAR)
# - 130QRO (130° QUERETARO)
# - ORIGEN
# =============================================================================

def _get_unidades_from_edarsahub() -> tuple:
    """
    FASE P0: Obtiene unidades desde EDARSAHUB.Unidades_Negocio.
    
    REEMPLAZA los arrays hardcodeados UNIDADES_SOFTRESTAURANT y UNIDADES_MPRO.
    
    Returns:
        (unidades_softrestaurant, unidades_mpro) con códigos canónicos
    """
    try:
        from core.unidades_registry import get_unidades_by_sistema
        
        unidades_sr = []
        unidades_mpro = []
        
        # Obtener unidades SoftRestaurant
        for u in get_unidades_by_sistema('SoftRestaurant'):
            unidades_sr.append({
                "unidad_negocio_id": u.codigo,  # Código canónico oficial
                "nombre": u.nombre,
                "server_id": u.server_id,
                "sucursal_id": u.sucursal_id or "DEFAULT",
                "sistema": "SoftRestaurant"
            })
        
        # Obtener unidades MPRO
        for u in get_unidades_by_sistema('MPRO'):
            unidades_mpro.append({
                "unidad_negocio_id": u.codigo,  # Código canónico oficial
                "nombre": u.nombre,
                "server_id": u.server_id,
                "sucursal_id": u.sucursal_id or "DEFAULT",
                "sistema": "MPRO"
            })
        
        logger.info(f"[SYNC_ABIERTAS_V2] FASE P0: Cargadas {len(unidades_sr)} unidades SoftRestaurant, {len(unidades_mpro)} unidades MPRO desde EDARSAHUB")
        
        return unidades_sr, unidades_mpro
        
    except Exception as e:
        logger.error(f"[SYNC_ABIERTAS_V2] Error cargando unidades desde EDARSAHUB: {e}")
        # Fallback a códigos canónicos hardcodeados (última línea de defensa)
        logger.warning("[SYNC_ABIERTAS_V2] Usando fallback con códigos canónicos hardcodeados")
        return _get_fallback_unidades()


def _get_fallback_unidades() -> tuple:
    """
    Fallback de última línea con códigos canónicos oficiales.
    Solo se usa si falla la conexión a EDARSAHUB.
    """
    unidades_sr = [
        {
            "unidad_negocio_id": "130MID",  # Código canónico oficial
            "nombre": "130° MÉRIDA",
            "server_id": "a5547321-1139-4d2b-9d53-182ca737b6b6",
            "sucursal_id": "DEFAULT",
            "sistema": "SoftRestaurant"
        },
        {
            "unidad_negocio_id": "CIENFUEGOS",  # Código canónico oficial
            "nombre": "CIENFUEGOS",
            "server_id": "6d053c22-523e-48c0-b72b-96081e2d781b",
            "sucursal_id": "DEFAULT",
            "sistema": "SoftRestaurant"
        },
        {
            "unidad_negocio_id": "ESTELAR",  # Código canónico oficial (NO "LA-ESTELAR")
            "nombre": "LA ESTELAR",
            "server_id": "a5ff0e25-f029-43db-b634-d4ac814c904f",
            "sucursal_id": "DEFAULT",
            "sistema": "SoftRestaurant"
        }
    ]
    
    unidades_mpro = [
        {
            "unidad_negocio_id": "130QRO",  # Código canónico oficial (NO "130-QRO")
            "nombre": "130° QUERETARO",
            "server_id": "1b230a06-ffaf-4c70-bd27-b1be3579dea6",
            "sucursal_id": "0021",
            "sistema": "MPRO"
        },
        {
            "unidad_negocio_id": "ORIGEN",  # Código canónico oficial
            "nombre": "ORIGEN",
            "server_id": "1b230a06-ffaf-4c70-bd27-b1be3579dea6",
            "sucursal_id": "0023",
            "sistema": "MPRO"
        }
    ]
    
    return unidades_sr, unidades_mpro


# =============================================================================
# QUERIES PARA VENTAS ABIERTAS
# =============================================================================

# SoftRestaurant: Cuentas abiertas desde tempcheques (operación en curso)
# CORRECCIÓN: tempcheques contiene las cuentas SIN cerrar
# cheques solo tiene cuentas YA cerradas
QUERY_SOFTRESTAURANT_VENTAS_ABIERTAS = """
SELECT 
    CAST(GETDATE() AS DATE) as fecha,
    ISNULL(SUM(total), 0) as ventas_abiertas,
    COUNT(*) as tickets_abiertos,
    ISNULL(SUM(nopersonas), 0) as pax_abiertos,
    MAX(fecha) as ultima_venta
FROM tempcheques
WHERE cancelado = 0
  AND total > 0
"""

# SoftRestaurant: Ventas cerradas del día (para total estimado)
QUERY_SOFTRESTAURANT_CERRADAS_HOY = """
SELECT 
    SUM(ISNULL(total, 0)) as ventas_cerradas_dia,
    COUNT(DISTINCT folio) as tickets_cerrados_dia,
    SUM(ISNULL(nopersonas, 1)) as pax_cerrados_dia
FROM cheques
WHERE cancelado = 0
  AND cierre IS NOT NULL
  AND CAST(fecha AS DATE) = CAST(GETDATE() AS DATE)
"""

# MPRO: Ventas sin tabla definitiva (operación en curso)
# MPRO identifica ventas "abiertas" via Vn_Tabla = 'Comanda'
QUERY_MPRO_VENTAS_ABIERTAS = """
SELECT 
    CAST(GETDATE() AS DATE) as fecha,
    SUM(ISNULL(ve.Vn_Precio_Neto_Importe, 0)) as ventas_abiertas,
    COUNT(DISTINCT ve.Vn_Folio) as tickets_abiertos,
    SUM(ISNULL(c.Co_Personas, 1)) as pax_abiertos
FROM Venta_Encabezado ve
LEFT JOIN Comanda c ON ve.Vn_Documento = c.Co_Folio AND ve.Sc_Cve_Sucursal = c.Sc_Cve_Sucursal
WHERE CAST(ve.Vn_Fecha AS DATE) = CAST(GETDATE() AS DATE)
  AND ve.Sc_Cve_Sucursal = '{sucursal_id}'
  AND ve.Vn_Tabla = 'Comanda'
"""

# MPRO: Ventas cerradas del día (ya en tabla definitiva)
QUERY_MPRO_CERRADAS_HOY = """
SELECT 
    SUM(ISNULL(ve.Vn_Precio_Neto_Importe, 0)) as ventas_cerradas_dia,
    COUNT(DISTINCT ve.Vn_Folio) as tickets_cerrados_dia,
    SUM(ISNULL(c.Co_Personas, 1)) as pax_cerrados_dia
FROM Venta_Encabezado ve
LEFT JOIN Comanda c ON ve.Vn_Documento = c.Co_Folio AND ve.Sc_Cve_Sucursal = c.Sc_Cve_Sucursal
WHERE CAST(ve.Vn_Fecha AS DATE) = CAST(GETDATE() AS DATE)
  AND ve.Sc_Cve_Sucursal = '{sucursal_id}'
  AND ve.Vn_Tabla <> 'Comanda'
"""


# =============================================================================
# FUNCIÓN PRINCIPAL DEL JOB
# =============================================================================

async def execute_sync_comercial_abiertas_v2(db=None) -> Dict[str, Any]:
    """
    Ejecuta sincronización de ventas abiertas del día actual.
    
    Args:
        db: Conexión MongoDB (para locks/logs técnicos, NO para datos de negocio)
        
    Returns:
        Dict con resumen de la ejecución
    """
    from modules.comercial_v2.sync_comercial_edarsahub import (
        get_server_connection_config,
        execute_query_on_server,
        ConnectionStatus
    )
    from modules.comercial_v2.schemas import (
        VentasDiaAbiertasV2,
        SyncLogV2,
        SyncRunType,
        SyncStatus,
        SistemaOrigen,
        FuenteOriginal
    )
    from modules.comercial_v2.repository_comercial_edarsahub import (
        upsert_ventas_dia_abiertas,
        insert_sync_log
    )
    
    logger.info("[SYNC_ABIERTAS_V2] Iniciando sincronización de ventas abiertas del día")
    
    start_time = datetime.now(timezone.utc)
    run_id = f"ABIERTA-{start_time.strftime('%Y%m%d-%H%M%S')}-{str(uuid.uuid4())[:4]}"
    fecha_hoy = date.today()
    
    results = {
        "job_name": JOB_NAME,
        "run_id": run_id,
        "tipo_sync": "VENTAS_ABIERTAS",
        "fecha": fecha_hoy.isoformat(),
        "inicio_ejecucion": start_time.isoformat(),
        "unidades_procesadas": 0,
        "unidades_exitosas": 0,
        "unidades_fallidas": 0,
        "total_ventas_abiertas": Decimal("0"),
        "total_tickets_abiertos": 0,
        "total_pax_abiertos": 0,
        "total_ventas_cerradas_dia": Decimal("0"),
        "total_estimado_dia": Decimal("0"),
        "detalles_unidades": [],
        "errores": []
    }
    
    # =========================================================================
    # FASE P0: CARGAR UNIDADES DESDE EDARSAHUB (códigos canónicos)
    # =========================================================================
    
    unidades_sr, unidades_mpro = _get_unidades_from_edarsahub()
    
    logger.info(f"[SYNC_ABIERTAS_V2] FASE P0: Procesando {len(unidades_sr)} SoftRestaurant + {len(unidades_mpro)} MPRO con códigos canónicos")
    
    # =========================================================================
    # SINCRONIZAR SOFTRESTAURANT
    # =========================================================================
    
    for unidad in unidades_sr:
        results["unidades_procesadas"] += 1
        unidad_id = unidad["unidad_negocio_id"]
        nombre = unidad["nombre"]
        server_id = unidad["server_id"]
        sucursal_id = unidad["sucursal_id"]
        
        try:
            logger.info(f"[SYNC_ABIERTAS_V2] Procesando {nombre} (SoftRestaurant)...")
            
            # Obtener configuración del servidor
            server_config = get_server_connection_config(server_id)
            if not server_config:
                raise Exception(f"No se encontró configuración para server_id {server_id}")
            
            # 1. Query ventas abiertas
            rows_abiertas, conn_status = execute_query_on_server(
                server_config, 
                QUERY_SOFTRESTAURANT_VENTAS_ABIERTAS
            )
            
            if conn_status != ConnectionStatus.ONLINE:
                raise Exception(f"Conexión fallida: {conn_status}")
            
            # 2. Query ventas cerradas del día (para total estimado)
            rows_cerradas, _ = execute_query_on_server(
                server_config,
                QUERY_SOFTRESTAURANT_CERRADAS_HOY
            )
            
            # Extraer valores
            abiertas_data = rows_abiertas[0] if rows_abiertas else {}
            cerradas_data = rows_cerradas[0] if rows_cerradas else {}
            
            ventas_abiertas = Decimal(str(abiertas_data.get('ventas_abiertas') or 0))
            tickets_abiertos = int(abiertas_data.get('tickets_abiertos') or 0)
            pax_abiertos = int(abiertas_data.get('pax_abiertos') or 0)
            
            ventas_cerradas_dia = Decimal(str(cerradas_data.get('ventas_cerradas_dia') or 0))
            tickets_cerrados_dia = int(cerradas_data.get('tickets_cerrados_dia') or 0)
            pax_cerrados_dia = int(cerradas_data.get('pax_cerrados_dia') or 0)
            
            total_estimado_dia = ventas_abiertas + ventas_cerradas_dia
            
            # 3. Crear modelo y upsert
            ventas_model = VentasDiaAbiertasV2(
                unidad_negocio_id=unidad_id,
                unidad_negocio_nombre=nombre,
                server_id=server_id,
                sucursal_id=sucursal_id,
                sucursal_nombre=nombre,
                sistema_origen=SistemaOrigen.SOFTRESTAURANT,
                snapshot_timestamp=datetime.now(timezone.utc),
                fecha_operacion=fecha_hoy,
                ventas_abiertas=ventas_abiertas,
                tickets_abiertos=tickets_abiertos,
                pax_abiertos=pax_abiertos,
                ventas_cerradas_dia=ventas_cerradas_dia,
                tickets_cerrados_dia=tickets_cerrados_dia,
                pax_cerrados_dia=pax_cerrados_dia,
                total_estimado_dia=total_estimado_dia,
                fuente_original=FuenteOriginal.TEMPCHEQUES,
                sync_run_id=run_id
            )
            
            upsert_result = upsert_ventas_dia_abiertas(ventas_model)
            
            # 4. Registrar detalle
            detalle = {
                "unidad_negocio_id": unidad_id,
                "unidad": nombre,
                "sistema": "SoftRestaurant",
                "estatus": "SUCCESS",
                "accion": upsert_result['action'],
                "ventas_abiertas": float(ventas_abiertas),
                "tickets_abiertos": tickets_abiertos,
                "pax_abiertos": pax_abiertos,
                "ventas_cerradas_dia": float(ventas_cerradas_dia),
                "total_estimado_dia": float(total_estimado_dia)
            }
            results["detalles_unidades"].append(detalle)
            
            # Acumular totales
            results["unidades_exitosas"] += 1
            results["total_ventas_abiertas"] += ventas_abiertas
            results["total_tickets_abiertos"] += tickets_abiertos
            results["total_pax_abiertos"] += pax_abiertos
            results["total_ventas_cerradas_dia"] += ventas_cerradas_dia
            results["total_estimado_dia"] += total_estimado_dia
            
            logger.info(
                f"[SYNC_ABIERTAS_V2] {nombre}: "
                f"abiertas=${ventas_abiertas:,.2f}, "
                f"cerradas=${ventas_cerradas_dia:,.2f}, "
                f"total=${total_estimado_dia:,.2f}"
            )
            
            # Log exitoso
            log = SyncLogV2(
                run_id=run_id,
                run_type=SyncRunType.VENTAS_DIA,
                unidad_negocio_id=unidad_id,
                server_id=server_id,
                fecha_inicio=fecha_hoy,
                fecha_fin=fecha_hoy,
                status=SyncStatus.SUCCESS,
                records_processed=1,
                records_inserted=1 if upsert_result['action'] == 'INSERT' else 0,
                records_updated=1 if upsert_result['action'] == 'UPDATE' else 0,
                source_connection_status=ConnectionStatus.ONLINE
            )
            insert_sync_log(log)
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"[SYNC_ABIERTAS_V2] Error en {nombre}: {error_msg}")
            results["unidades_fallidas"] += 1
            results["errores"].append(f"{nombre}: {error_msg}")
            results["detalles_unidades"].append({
                "unidad_negocio_id": unidad_id,
                "unidad": nombre,
                "sistema": "SoftRestaurant",
                "estatus": "ERROR",
                "mensaje_error": error_msg
            })
            
            # Log de error
            log = SyncLogV2(
                run_id=run_id,
                run_type=SyncRunType.VENTAS_DIA,
                unidad_negocio_id=unidad_id,
                server_id=server_id,
                fecha_inicio=fecha_hoy,
                fecha_fin=fecha_hoy,
                status=SyncStatus.FAILED,
                error_message=error_msg[:500],
                source_connection_status=ConnectionStatus.OFFLINE
            )
            insert_sync_log(log)
    
    # =========================================================================
    # SINCRONIZAR MPRO
    # =========================================================================
    
    for unidad in unidades_mpro:
        results["unidades_procesadas"] += 1
        unidad_id = unidad["unidad_negocio_id"]
        nombre = unidad["nombre"]
        server_id = unidad["server_id"]
        sucursal_id = unidad["sucursal_id"]
        
        try:
            logger.info(f"[SYNC_ABIERTAS_V2] Procesando {nombre} (MPRO sucursal={sucursal_id})...")
            
            # Obtener configuración del servidor
            server_config = get_server_connection_config(server_id)
            if not server_config:
                raise Exception(f"No se encontró configuración para server_id {server_id}")
            
            # 1. Query ventas abiertas
            query_abiertas = QUERY_MPRO_VENTAS_ABIERTAS.format(sucursal_id=sucursal_id)
            rows_abiertas, conn_status = execute_query_on_server(server_config, query_abiertas)
            
            if conn_status != ConnectionStatus.ONLINE:
                raise Exception(f"Conexión fallida: {conn_status}")
            
            # 2. Query ventas cerradas del día
            query_cerradas = QUERY_MPRO_CERRADAS_HOY.format(sucursal_id=sucursal_id)
            rows_cerradas, _ = execute_query_on_server(server_config, query_cerradas)
            
            # Extraer valores
            abiertas_data = rows_abiertas[0] if rows_abiertas else {}
            cerradas_data = rows_cerradas[0] if rows_cerradas else {}
            
            ventas_abiertas = Decimal(str(abiertas_data.get('ventas_abiertas') or 0))
            tickets_abiertos = int(abiertas_data.get('tickets_abiertos') or 0)
            pax_abiertos = int(abiertas_data.get('pax_abiertos') or 0)
            
            ventas_cerradas_dia = Decimal(str(cerradas_data.get('ventas_cerradas_dia') or 0))
            tickets_cerrados_dia = int(cerradas_data.get('tickets_cerrados_dia') or 0)
            pax_cerrados_dia = int(cerradas_data.get('pax_cerrados_dia') or 0)
            
            total_estimado_dia = ventas_abiertas + ventas_cerradas_dia
            
            # 3. Crear modelo y upsert
            ventas_model = VentasDiaAbiertasV2(
                unidad_negocio_id=unidad_id,
                unidad_negocio_nombre=nombre,
                server_id=server_id,
                sucursal_id=sucursal_id,
                sucursal_nombre=nombre,
                sistema_origen=SistemaOrigen.MPRO,
                snapshot_timestamp=datetime.now(timezone.utc),
                fecha_operacion=fecha_hoy,
                ventas_abiertas=ventas_abiertas,
                tickets_abiertos=tickets_abiertos,
                pax_abiertos=pax_abiertos,
                ventas_cerradas_dia=ventas_cerradas_dia,
                tickets_cerrados_dia=tickets_cerrados_dia,
                pax_cerrados_dia=pax_cerrados_dia,
                total_estimado_dia=total_estimado_dia,
                fuente_original=FuenteOriginal.SQL_LIVE,
                sync_run_id=run_id
            )
            
            upsert_result = upsert_ventas_dia_abiertas(ventas_model)
            
            # 4. Registrar detalle
            detalle = {
                "unidad_negocio_id": unidad_id,
                "unidad": nombre,
                "sistema": "MPRO",
                "sucursal_id": sucursal_id,
                "estatus": "SUCCESS",
                "accion": upsert_result['action'],
                "ventas_abiertas": float(ventas_abiertas),
                "tickets_abiertos": tickets_abiertos,
                "pax_abiertos": pax_abiertos,
                "ventas_cerradas_dia": float(ventas_cerradas_dia),
                "total_estimado_dia": float(total_estimado_dia)
            }
            results["detalles_unidades"].append(detalle)
            
            # Acumular totales
            results["unidades_exitosas"] += 1
            results["total_ventas_abiertas"] += ventas_abiertas
            results["total_tickets_abiertos"] += tickets_abiertos
            results["total_pax_abiertos"] += pax_abiertos
            results["total_ventas_cerradas_dia"] += ventas_cerradas_dia
            results["total_estimado_dia"] += total_estimado_dia
            
            logger.info(
                f"[SYNC_ABIERTAS_V2] {nombre}: "
                f"abiertas=${ventas_abiertas:,.2f}, "
                f"cerradas=${ventas_cerradas_dia:,.2f}, "
                f"total=${total_estimado_dia:,.2f}"
            )
            
            # Log exitoso
            log = SyncLogV2(
                run_id=run_id,
                run_type=SyncRunType.VENTAS_DIA,
                unidad_negocio_id=unidad_id,
                server_id=server_id,
                sucursal_id=sucursal_id,
                fecha_inicio=fecha_hoy,
                fecha_fin=fecha_hoy,
                status=SyncStatus.SUCCESS,
                records_processed=1,
                records_inserted=1 if upsert_result['action'] == 'INSERT' else 0,
                records_updated=1 if upsert_result['action'] == 'UPDATE' else 0,
                source_connection_status=ConnectionStatus.ONLINE
            )
            insert_sync_log(log)
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"[SYNC_ABIERTAS_V2] Error en {nombre}: {error_msg}")
            results["unidades_fallidas"] += 1
            results["errores"].append(f"{nombre}: {error_msg}")
            results["detalles_unidades"].append({
                "unidad_negocio_id": unidad_id,
                "unidad": nombre,
                "sistema": "MPRO",
                "sucursal_id": sucursal_id,
                "estatus": "ERROR",
                "mensaje_error": error_msg
            })
            
            # Log de error
            log = SyncLogV2(
                run_id=run_id,
                run_type=SyncRunType.VENTAS_DIA,
                unidad_negocio_id=unidad_id,
                server_id=server_id,
                sucursal_id=sucursal_id,
                fecha_inicio=fecha_hoy,
                fecha_fin=fecha_hoy,
                status=SyncStatus.FAILED,
                error_message=error_msg[:500],
                source_connection_status=ConnectionStatus.OFFLINE
            )
            insert_sync_log(log)
    
    # =========================================================================
    # FINALIZAR
    # =========================================================================
    
    end_time = datetime.now(timezone.utc)
    duration_ms = int((end_time - start_time).total_seconds() * 1000)
    
    # Convertir Decimals a float para serialización
    results["total_ventas_abiertas"] = float(results["total_ventas_abiertas"])
    results["total_ventas_cerradas_dia"] = float(results["total_ventas_cerradas_dia"])
    results["total_estimado_dia"] = float(results["total_estimado_dia"])
    
    results["fin_ejecucion"] = end_time.isoformat()
    results["duracion_ms"] = duration_ms
    results["estatus_general"] = (
        "COMPLETADO" if results["unidades_fallidas"] == 0 
        else "PARCIAL" if results["unidades_exitosas"] > 0 
        else "FALLIDO"
    )
    
    logger.info(
        f"[SYNC_ABIERTAS_V2] Sincronización finalizada: "
        f"exitosas={results['unidades_exitosas']}/{results['unidades_procesadas']}, "
        f"abiertas=${results['total_ventas_abiertas']:,.2f}, "
        f"cerradas=${results['total_ventas_cerradas_dia']:,.2f}, "
        f"total_estimado=${results['total_estimado_dia']:,.2f}, "
        f"duración={duration_ms}ms"
    )
    
    return results


# =============================================================================
# FUNCIÓN DE EJECUCIÓN MANUAL (para pruebas/validación)
# =============================================================================

def run_sync_comercial_abiertas_v2_manual() -> Dict[str, Any]:
    """
    Ejecuta sincronización manual para pruebas/validación.
    
    Uso:
        cd /app/backend
        python -c "from core.scheduler.jobs.sync_comercial_abiertas_v2_job import run_sync_comercial_abiertas_v2_manual; print(run_sync_comercial_abiertas_v2_manual())"
        
    Returns:
        Dict con resultados
    """
    import asyncio
    
    logger.info("[SYNC_ABIERTAS_V2] Ejecución manual iniciada")
    
    # Ejecutar async en loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        result = loop.run_until_complete(execute_sync_comercial_abiertas_v2())
    finally:
        loop.close()
    
    return result


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = ['execute_sync_comercial_abiertas_v2', 'run_sync_comercial_abiertas_v2_manual', 'JOB_NAME']
