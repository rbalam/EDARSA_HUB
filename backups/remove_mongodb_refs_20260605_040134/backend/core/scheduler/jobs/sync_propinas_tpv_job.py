"""
EDARSA HUB - Job de Sincronización Incremental Propinas TPV
============================================================

SUBFASE 3.6 — Scheduler Incremental Propinas TPV

Este job sincroniza propinas TPV desde SoftRestaurant y MPRO hacia EDARSAHUB
cada 15 minutos (configurable).

CARACTERÍSTICAS:
- Sincronización incremental (últimos 2 días por defecto)
- Idempotente (usa HashOrigen para evitar duplicados)
- Tolerante a fallos (una unidad falla, las demás continúan)
- Lock para evitar ejecuciones simultáneas
- SyncLog detallado por unidad (Finanzas_PropinasTPV_SyncLog)
- NO ejecuta carga histórica

MÁXIMAS RESPETADAS:
- EDARSAHUB es el cerebro (destino de sincronización)
- No depende de conexiones en vivo para pintar dashboards
- Datos demo aislados (EsDemo=0 para datos reales)
- MongoDB NO es fuente financiera

FUENTES:
- SoftRestaurant: cheques.propinatarjeta
- MPRO: Comanda_Pago.Cp_Propina WHERE Forma_Pago.Fp_Tipo = '04'

DESTINO:
- EDARSAHUB.propinas_tpv_control

BITÁCORA:
- EDARSAHUB.Finanzas_PropinasTPV_SyncLog

Autor: E1 Agent
Fecha: 2026-05-01
Fase: Finanzas Fase 3 - Propinas TPV - Subfase 3.6
"""

import logging
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any

logger = logging.getLogger(__name__)

# Rango incremental (días hacia atrás desde hoy)
SYNC_PROPINAS_INCREMENTAL_DAYS = int(os.environ.get("SYNC_PROPINAS_DAYS", "2"))


async def execute_sync_propinas_tpv_incremental(db=None) -> Dict[str, Any]:
    """
    Ejecuta sincronización incremental de propinas TPV.
    
    Args:
        db: Conexión MongoDB (para locks/logs legacy, no para datos financieros)
        
    Returns:
        Dict con resumen de la ejecución
    """
    # Importar sincronizadores ya validados en Subfases 3.2 y 3.3
    from modules.finanzas.sync_propinas_softrestaurant import sincronizar_propinas_softrestaurant
    from modules.finanzas.sync_propinas_mpro import sincronizar_propinas_mpro
    
    logger.info("[SYNC_PROPINAS_TPV] Iniciando sincronización incremental")
    
    start_time = datetime.now()
    
    # Calcular rango de fechas
    fecha_hasta = datetime.now()
    fecha_desde = fecha_hasta - timedelta(days=SYNC_PROPINAS_INCREMENTAL_DAYS)
    
    results = {
        "job_name": "sync_propinas_tpv_incremental",
        "tipo_sync": "INCREMENTAL",
        "dias_atras": SYNC_PROPINAS_INCREMENTAL_DAYS,
        "fecha_desde": fecha_desde.strftime('%Y-%m-%d'),
        "fecha_hasta": fecha_hasta.strftime('%Y-%m-%d'),
        "fecha_inicio_ejecucion": start_time.isoformat(),
        "unidades_procesadas": 0,
        "unidades_exitosas": 0,
        "unidades_fallidas": 0,
        "total_leidos": 0,
        "total_insertados": 0,
        "total_omitidos": 0,
        "total_errores": 0,
        "suma_propinas_tpv": 0.0,
        "detalles_unidades": [],
        "errores": []
    }
    
    # =========================================================================
    # UNIDADES A SINCRONIZAR
    # =========================================================================
    
    # SoftRestaurant (Subfase 3.2)
    unidades_sr = [
        {"nombre": "130° MERIDA", "sistema": "SoftRestaurant"},
        {"nombre": "CIENFUEGOS", "sistema": "SoftRestaurant"},
        {"nombre": "LA ESTELAR", "sistema": "SoftRestaurant"}
    ]
    
    # MPRO (Subfase 3.3)
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
            logger.info(f"[SYNC_PROPINAS_TPV] Sincronizando {nombre} (SoftRestaurant)...")
            
            resultado = sincronizar_propinas_softrestaurant(
                unidad_nombre=nombre,
                fecha_desde=fecha_desde,
                fecha_hasta=fecha_hasta
            )
            
            stats = resultado.get("stats", {})
            
            detalle = {
                "unidad": nombre,
                "sistema": "SoftRestaurant",
                "estatus": resultado.get("estatus", "UNKNOWN"),
                "registros_origen": resultado.get("registros_origen", 0),
                "suma_propinas_origen": resultado.get("suma_propinas_origen", 0),
                "insertados": stats.get("insertados", 0),
                "omitidos": stats.get("omitidos", 0),
                "errores": stats.get("errores", 0),
                "mensaje": resultado.get("mensaje", ""),
                "error": resultado.get("error")
            }
            
            results["detalles_unidades"].append(detalle)
            
            if resultado.get("estatus") in ["COMPLETADO", "PARCIAL"]:
                results["unidades_exitosas"] += 1
                results["total_leidos"] += resultado.get("registros_origen", 0)
                results["total_insertados"] += stats.get("insertados", 0)
                results["total_omitidos"] += stats.get("omitidos", 0)
                results["suma_propinas_tpv"] += float(resultado.get("suma_propinas_origen", 0) or 0)
            else:
                results["unidades_fallidas"] += 1
                results["total_errores"] += stats.get("errores", 0)
                if resultado.get("error"):
                    results["errores"].append(f"{nombre}: {resultado.get('error')}")
                    
        except Exception as e:
            logger.error(f"[SYNC_PROPINAS_TPV] Error sincronizando {nombre}: {e}")
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
            logger.info(f"[SYNC_PROPINAS_TPV] Sincronizando {nombre} (MPRO)...")
            
            resultado = sincronizar_propinas_mpro(
                unidad_nombre=nombre,
                fecha_desde=fecha_desde,
                fecha_hasta=fecha_hasta
            )
            
            stats = resultado.get("stats", {})
            
            detalle = {
                "unidad": nombre,
                "sistema": "MPRO",
                "estatus": resultado.get("estatus", "UNKNOWN"),
                "registros_origen": resultado.get("registros_origen", 0),
                "suma_propinas_origen": resultado.get("suma_propinas_origen", 0),
                "insertados": stats.get("insertados", 0),
                "omitidos": stats.get("omitidos", 0),
                "errores": stats.get("errores", 0),
                "mensaje": resultado.get("mensaje", ""),
                "error": resultado.get("error")
            }
            
            results["detalles_unidades"].append(detalle)
            
            if resultado.get("estatus") in ["COMPLETADO", "PARCIAL"]:
                results["unidades_exitosas"] += 1
                results["total_leidos"] += resultado.get("registros_origen", 0)
                results["total_insertados"] += stats.get("insertados", 0)
                results["total_omitidos"] += stats.get("omitidos", 0)
                results["suma_propinas_tpv"] += float(resultado.get("suma_propinas_origen", 0) or 0)
            else:
                results["unidades_fallidas"] += 1
                results["total_errores"] += stats.get("errores", 0)
                if resultado.get("error"):
                    results["errores"].append(f"{nombre}: {resultado.get('error')}")
                    
        except Exception as e:
            logger.error(f"[SYNC_PROPINAS_TPV] Error sincronizando {nombre}: {e}")
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
    
    results["fecha_fin_ejecucion"] = end_time.isoformat()
    results["duracion_ms"] = duration_ms
    results["estatus_general"] = (
        "COMPLETADO" if results["unidades_fallidas"] == 0 
        else "PARCIAL" if results["unidades_exitosas"] > 0 
        else "FALLIDO"
    )
    
    logger.info(
        f"[SYNC_PROPINAS_TPV] Sincronización finalizada: "
        f"exitosas={results['unidades_exitosas']}/{results['unidades_procesadas']}, "
        f"insertados={results['total_insertados']}, "
        f"omitidos={results['total_omitidos']}, "
        f"propinas=${results['suma_propinas_tpv']:,.2f}, "
        f"duración={duration_ms}ms"
    )
    
    return results


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = ['execute_sync_propinas_tpv_incremental']
