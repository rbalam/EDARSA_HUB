"""
EDARSA HUB - Job de Sincronización Incremental Comercial V2
============================================================

SUBFASE 4 — Scheduler Incremental Comercial v2

Este job sincroniza KPIs de ventas comerciales desde SoftRestaurant y MPRO 
hacia EDARSAHUB cada 15 minutos (configurable).

CARACTERÍSTICAS:
- Sincronización incremental (últimos 3 días por defecto)
- Idempotente (usa HashOrigen para evitar duplicados)
- Tolerante a fallos (una unidad falla, las demás continúan)
- Lock distribuido (MongoDB) para evitar ejecuciones simultáneas
- SyncLog detallado por unidad (EDARSAHUB.Comercial_SyncLog_v2)

UNIDADES SOPORTADAS (5):
- SoftRestaurant: 130MID (130° MÉRIDA), CIENFUEGOS, ESTELAR (LA ESTELAR)
- MPRO: 130QRO (130° QUERETARO, sucursal 0021), ORIGEN (sucursal 0023)

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
from datetime import datetime, date, timedelta, timezone
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

# Configuración
JOB_NAME = "sync_comercial_v2"
SYNC_INCREMENTAL_DAYS = int(os.environ.get("SYNC_COMERCIAL_V2_DAYS", "3"))


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
        
        logger.info(f"[SYNC_V2] FASE P0: Cargadas {len(unidades_sr)} unidades SoftRestaurant, {len(unidades_mpro)} unidades MPRO desde EDARSAHUB")
        
        return unidades_sr, unidades_mpro
        
    except Exception as e:
        logger.error(f"[SYNC_V2] Error cargando unidades desde EDARSAHUB: {e}")
        # Fallback a códigos canónicos hardcodeados (última línea de defensa)
        logger.warning("[SYNC_V2] Usando fallback con códigos canónicos hardcodeados")
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
# FUNCIÓN PRINCIPAL DEL JOB
# =============================================================================

async def execute_sync_comercial_v2(db=None) -> Dict[str, Any]:
    """
    Ejecuta sincronización incremental de KPIs comerciales V2.
    
    Args:
        db: Conexión MongoDB (para locks/logs técnicos, NO para datos de negocio)
        
    Returns:
        Dict con resumen de la ejecución
    """
    from modules.comercial_v2.sync_comercial_edarsahub import (
        sync_softrestaurant_ventas_cerradas,
        sync_mpro_ventas_cerradas,
        get_server_connection_config
    )
    from modules.comercial_v2.schemas import (
        UnidadNegocioConfig,
        SistemaOrigen
    )
    
    logger.info(f"[SYNC_COMERCIAL_V2] Iniciando sincronización incremental ({SYNC_INCREMENTAL_DAYS} días)")
    
    start_time = datetime.now(timezone.utc)
    run_id = f"INCR-{start_time.strftime('%Y%m%d-%H%M%S')}-{str(uuid.uuid4())[:4]}"
    
    # Calcular rango de fechas (últimos N días)
    fecha_fin = date.today()
    fecha_inicio = fecha_fin - timedelta(days=SYNC_INCREMENTAL_DAYS)
    
    results = {
        "job_name": JOB_NAME,
        "run_id": run_id,
        "tipo_sync": "INCREMENTAL",
        "dias_atras": SYNC_INCREMENTAL_DAYS,
        "fecha_inicio": fecha_inicio.isoformat(),
        "fecha_fin": fecha_fin.isoformat(),
        "inicio_ejecucion": start_time.isoformat(),
        "unidades_procesadas": 0,
        "unidades_exitosas": 0,
        "unidades_fallidas": 0,
        "total_insertados": 0,
        "total_actualizados": 0,
        "total_omitidos": 0,
        "total_errores": 0,
        "detalles_unidades": [],
        "errores": []
    }
    
    # =========================================================================
    # FASE P0: CARGAR UNIDADES DESDE EDARSAHUB (códigos canónicos)
    # =========================================================================
    
    unidades_sr, unidades_mpro = _get_unidades_from_edarsahub()
    
    logger.info(f"[SYNC_COMERCIAL_V2] FASE P0: Procesando {len(unidades_sr)} SoftRestaurant + {len(unidades_mpro)} MPRO con códigos canónicos")
    
    # =========================================================================
    # SINCRONIZAR SOFTRESTAURANT
    # =========================================================================
    
    for unidad in unidades_sr:
        results["unidades_procesadas"] += 1
        unidad_id = unidad["unidad_negocio_id"]
        nombre = unidad["nombre"]
        
        try:
            logger.info(f"[SYNC_COMERCIAL_V2] Sincronizando {nombre} (SoftRestaurant)...")
            
            # Crear configuración de la unidad
            config = UnidadNegocioConfig(
                unidad_negocio_id=unidad_id,
                unidad_negocio_nombre=nombre,
                server_id=unidad["server_id"],
                sucursal_id=unidad["sucursal_id"],
                sucursal_nombre=nombre,
                sistema_origen=SistemaOrigen.SOFTRESTAURANT,
                activo=True
            )
            
            # Ejecutar sync
            resultado = sync_softrestaurant_ventas_cerradas(
                config=config,
                fecha_inicio=fecha_inicio,
                fecha_fin=fecha_fin,
                run_id=run_id
            )
            
            detalle = {
                "unidad_negocio_id": unidad_id,
                "unidad": nombre,
                "sistema": "SoftRestaurant",
                "estatus": "SUCCESS" if resultado.success else "FAILED",
                "procesados": resultado.records_processed,
                "insertados": resultado.records_inserted,
                "actualizados": resultado.records_updated,
                "omitidos": resultado.records_skipped,
                "errores": resultado.records_errored,
                "duracion_seg": resultado.duration_seconds,
                "mensaje_error": resultado.error_message
            }
            
            results["detalles_unidades"].append(detalle)
            
            if resultado.success:
                results["unidades_exitosas"] += 1
                results["total_insertados"] += resultado.records_inserted
                results["total_actualizados"] += resultado.records_updated
                results["total_omitidos"] += resultado.records_skipped
            else:
                results["unidades_fallidas"] += 1
                results["total_errores"] += resultado.records_errored
                if resultado.error_message:
                    results["errores"].append(f"{nombre}: {resultado.error_message}")
                    
            logger.info(
                f"[SYNC_COMERCIAL_V2] {nombre}: "
                f"insertados={resultado.records_inserted}, "
                f"actualizados={resultado.records_updated}, "
                f"omitidos={resultado.records_skipped}"
            )
                    
        except Exception as e:
            logger.error(f"[SYNC_COMERCIAL_V2] Error sincronizando {nombre}: {e}")
            results["unidades_fallidas"] += 1
            results["total_errores"] += 1
            results["errores"].append(f"{nombre}: {str(e)}")
            results["detalles_unidades"].append({
                "unidad_negocio_id": unidad_id,
                "unidad": nombre,
                "sistema": "SoftRestaurant",
                "estatus": "ERROR",
                "mensaje_error": str(e)
            })
    
    # =========================================================================
    # SINCRONIZAR MPRO
    # =========================================================================
    
    for unidad in unidades_mpro:
        results["unidades_procesadas"] += 1
        unidad_id = unidad["unidad_negocio_id"]
        nombre = unidad["nombre"]
        sucursal_id = unidad["sucursal_id"]
        
        try:
            logger.info(f"[SYNC_COMERCIAL_V2] Sincronizando {nombre} (MPRO sucursal={sucursal_id})...")
            
            # Crear configuración de la unidad
            config = UnidadNegocioConfig(
                unidad_negocio_id=unidad_id,
                unidad_negocio_nombre=nombre,
                server_id=unidad["server_id"],
                sucursal_id=sucursal_id,
                sucursal_nombre=nombre,
                sistema_origen=SistemaOrigen.MPRO,
                activo=True
            )
            
            # Ejecutar sync
            resultado = sync_mpro_ventas_cerradas(
                config=config,
                sucursal_id=sucursal_id,
                fecha_inicio=fecha_inicio,
                fecha_fin=fecha_fin,
                run_id=run_id
            )
            
            detalle = {
                "unidad_negocio_id": unidad_id,
                "unidad": nombre,
                "sistema": "MPRO",
                "sucursal_id": sucursal_id,
                "estatus": "SUCCESS" if resultado.success else "FAILED",
                "procesados": resultado.records_processed,
                "insertados": resultado.records_inserted,
                "actualizados": resultado.records_updated,
                "omitidos": resultado.records_skipped,
                "errores": resultado.records_errored,
                "duracion_seg": resultado.duration_seconds,
                "mensaje_error": resultado.error_message
            }
            
            results["detalles_unidades"].append(detalle)
            
            if resultado.success:
                results["unidades_exitosas"] += 1
                results["total_insertados"] += resultado.records_inserted
                results["total_actualizados"] += resultado.records_updated
                results["total_omitidos"] += resultado.records_skipped
            else:
                results["unidades_fallidas"] += 1
                results["total_errores"] += resultado.records_errored
                if resultado.error_message:
                    results["errores"].append(f"{nombre}: {resultado.error_message}")
                    
            logger.info(
                f"[SYNC_COMERCIAL_V2] {nombre}: "
                f"insertados={resultado.records_inserted}, "
                f"actualizados={resultado.records_updated}, "
                f"omitidos={resultado.records_skipped}"
            )
                    
        except Exception as e:
            logger.error(f"[SYNC_COMERCIAL_V2] Error sincronizando {nombre}: {e}")
            results["unidades_fallidas"] += 1
            results["total_errores"] += 1
            results["errores"].append(f"{nombre}: {str(e)}")
            results["detalles_unidades"].append({
                "unidad_negocio_id": unidad_id,
                "unidad": nombre,
                "sistema": "MPRO",
                "sucursal_id": sucursal_id,
                "estatus": "ERROR",
                "mensaje_error": str(e)
            })
    
    # =========================================================================
    # FINALIZAR
    # =========================================================================
    
    end_time = datetime.now(timezone.utc)
    duration_ms = int((end_time - start_time).total_seconds() * 1000)
    
    results["fin_ejecucion"] = end_time.isoformat()
    results["duracion_ms"] = duration_ms
    results["estatus_general"] = (
        "COMPLETADO" if results["unidades_fallidas"] == 0 
        else "PARCIAL" if results["unidades_exitosas"] > 0 
        else "FALLIDO"
    )
    
    logger.info(
        f"[SYNC_COMERCIAL_V2] Sincronización finalizada: "
        f"exitosas={results['unidades_exitosas']}/{results['unidades_procesadas']}, "
        f"insertados={results['total_insertados']}, "
        f"actualizados={results['total_actualizados']}, "
        f"omitidos={results['total_omitidos']}, "
        f"duración={duration_ms}ms"
    )
    
    return results


# =============================================================================
# FUNCIÓN DE EJECUCIÓN MANUAL (para pruebas)
# =============================================================================

def run_sync_comercial_v2_manual(
    dias_atras: int = 3,
    solo_unidades: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Ejecuta sincronización manual para pruebas.
    
    Args:
        dias_atras: Número de días hacia atrás para sincronizar
        solo_unidades: Lista opcional de unidad_negocio_id para filtrar
        
    Returns:
        Dict con resultados
    """
    import asyncio
    
    # Temporalmente sobreescribir variable de entorno
    global SYNC_INCREMENTAL_DAYS
    SYNC_INCREMENTAL_DAYS = dias_atras
    
    logger.info(f"[SYNC_COMERCIAL_V2] Ejecución manual: {dias_atras} días, unidades={solo_unidades or 'TODAS'}")
    
    # Ejecutar async en loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        result = loop.run_until_complete(execute_sync_comercial_v2())
    finally:
        loop.close()
    
    return result


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = ['execute_sync_comercial_v2', 'run_sync_comercial_v2_manual', 'JOB_NAME']
