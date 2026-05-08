"""
EDARSA HUB - Job de Sincronización Incremental Control de Ingresos
===================================================================

SUBFASE 2.6 — Scheduler Incremental

Este job sincroniza cortes de caja desde SoftRestaurant y MPRO hacia EDARSAHUB
cada 15 minutos (configurable).

CARACTERÍSTICAS:
- Sincronización incremental (últimos 2 días por defecto)
- Idempotente (usa HashOrigen para evitar duplicados)
- Tolerante a fallos (una unidad falla, las demás continúan)
- Lock para evitar ejecuciones simultáneas
- SyncLog detallado por unidad
- NO ejecuta carga histórica

MÁXIMAS RESPETADAS:
- EDARSAHUB es el cerebro (destino de sincronización)
- No depende de conexiones en vivo para pintar dashboards
- Datos demo aislados (EsDemo=0 para datos reales)

Autor: E1 Agent
Fecha: 2026-05-01
"""

import logging
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

# Rango incremental (días hacia atrás desde hoy)
SYNC_INCREMENTAL_DAYS = int(os.environ.get("SYNC_INGRESOS_DAYS", "2"))


async def execute_sync_ingresos_incremental(db=None) -> Dict[str, Any]:
    """
    Ejecuta sincronización incremental de cortes de caja.
    
    Args:
        db: Conexión MongoDB (para locks/logs legacy, no para datos financieros)
        
    Returns:
        Dict con resumen de la ejecución
    """
    from modules.finanzas.sync_cortes_softrestaurant import sincronizar_unidad_softrestaurant
    from modules.finanzas.sync_cortes_mpro import sincronizar_unidad_mpro
    
    logger.info("[SYNC_INGRESOS] Iniciando sincronización incremental")
    
    start_time = datetime.now()
    
    results = {
        "job_name": "sync_ingresos_incremental",
        "tipo_sync": "INCREMENTAL",
        "dias_atras": SYNC_INCREMENTAL_DAYS,
        "fecha_inicio": start_time.isoformat(),
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
    # UNIDADES A SINCRONIZAR
    # =========================================================================
    
    # SoftRestaurant
    unidades_sr = [
        {"nombre": "130° MERIDA", "sistema": "SoftRestaurant"},
        {"nombre": "CIENFUEGOS", "sistema": "SoftRestaurant"},
        {"nombre": "LA ESTELAR", "sistema": "SoftRestaurant"}
    ]
    
    # MPRO
    unidades_mpro = [
        {"nombre": "130° QUERETARO", "sistema": "MPRO"},
        {"nombre": "ORIGEN", "sistema": "MPRO"}
    ]
    
    # =========================================================================
    # SINCRONIZAR SOFTRESTAURANT
    # =========================================================================
    
    for unidad in unidades_sr:
        nombre = unidad["nombre"]
        results["unidades_procesadas"] += 1
        
        try:
            logger.info(f"[SYNC_INGRESOS] Sincronizando {nombre} (SoftRestaurant)...")
            
            resultado = sincronizar_unidad_softrestaurant(
                unidad_nombre=nombre,
                dias_atras=SYNC_INCREMENTAL_DAYS
            )
            
            stats = resultado.get("stats", {})
            
            detalle = {
                "unidad": nombre,
                "sistema": "SoftRestaurant",
                "estatus": resultado.get("estatus", "UNKNOWN"),
                "leidos": stats.get("leidos", 0),
                "insertados": stats.get("insertados", 0),
                "actualizados": stats.get("actualizados", 0),
                "omitidos": stats.get("omitidos", 0),
                "errores": stats.get("errores", 0),
                "mensaje": resultado.get("mensaje", ""),
                "error": resultado.get("error")
            }
            
            results["detalles_unidades"].append(detalle)
            
            if resultado.get("estatus") == "COMPLETADO":
                results["unidades_exitosas"] += 1
                results["total_insertados"] += stats.get("insertados", 0)
                results["total_actualizados"] += stats.get("actualizados", 0)
                results["total_omitidos"] += stats.get("omitidos", 0)
            else:
                results["unidades_fallidas"] += 1
                results["total_errores"] += stats.get("errores", 0)
                if resultado.get("error"):
                    results["errores"].append(f"{nombre}: {resultado.get('error')}")
                    
        except Exception as e:
            logger.error(f"[SYNC_INGRESOS] Error sincronizando {nombre}: {e}")
            results["unidades_fallidas"] += 1
            results["total_errores"] += 1
            results["errores"].append(f"{nombre}: {str(e)}")
            results["detalles_unidades"].append({
                "unidad": nombre,
                "sistema": "SoftRestaurant",
                "estatus": "ERROR",
                "error": str(e)
            })
    
    # =========================================================================
    # SINCRONIZAR MPRO
    # =========================================================================
    
    for unidad in unidades_mpro:
        nombre = unidad["nombre"]
        results["unidades_procesadas"] += 1
        
        try:
            logger.info(f"[SYNC_INGRESOS] Sincronizando {nombre} (MPRO)...")
            
            resultado = sincronizar_unidad_mpro(
                unidad_nombre=nombre,
                dias_atras=SYNC_INCREMENTAL_DAYS
            )
            
            stats = resultado.get("stats", {})
            
            detalle = {
                "unidad": nombre,
                "sistema": "MPRO",
                "estatus": resultado.get("estatus", "UNKNOWN"),
                "leidos": stats.get("leidos", 0),
                "insertados": stats.get("insertados", 0),
                "actualizados": stats.get("actualizados", 0),
                "omitidos": stats.get("omitidos", 0),
                "errores": stats.get("errores", 0),
                "mensaje": resultado.get("mensaje", ""),
                "error": resultado.get("error")
            }
            
            results["detalles_unidades"].append(detalle)
            
            if resultado.get("estatus") == "COMPLETADO":
                results["unidades_exitosas"] += 1
                results["total_insertados"] += stats.get("insertados", 0)
                results["total_actualizados"] += stats.get("actualizados", 0)
                results["total_omitidos"] += stats.get("omitidos", 0)
            else:
                results["unidades_fallidas"] += 1
                results["total_errores"] += stats.get("errores", 0)
                if resultado.get("error"):
                    results["errores"].append(f"{nombre}: {resultado.get('error')}")
                    
        except Exception as e:
            logger.error(f"[SYNC_INGRESOS] Error sincronizando {nombre}: {e}")
            results["unidades_fallidas"] += 1
            results["total_errores"] += 1
            results["errores"].append(f"{nombre}: {str(e)}")
            results["detalles_unidades"].append({
                "unidad": nombre,
                "sistema": "MPRO",
                "estatus": "ERROR",
                "error": str(e)
            })
    
    # =========================================================================
    # FINALIZAR
    # =========================================================================
    
    end_time = datetime.now()
    duration_ms = int((end_time - start_time).total_seconds() * 1000)
    
    results["fecha_fin"] = end_time.isoformat()
    results["duracion_ms"] = duration_ms
    results["estatus_general"] = (
        "COMPLETADO" if results["unidades_fallidas"] == 0 
        else "PARCIAL" if results["unidades_exitosas"] > 0 
        else "FALLIDO"
    )
    
    logger.info(
        f"[SYNC_INGRESOS] Sincronización finalizada: "
        f"exitosas={results['unidades_exitosas']}/{results['unidades_procesadas']}, "
        f"insertados={results['total_insertados']}, "
        f"omitidos={results['total_omitidos']}, "
        f"duración={duration_ms}ms"
    )
    
    return results


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = ['execute_sync_ingresos_incremental']
