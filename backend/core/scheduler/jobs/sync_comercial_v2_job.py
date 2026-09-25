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
- Lock de ejecución para evitar ejecuciones simultáneas
- SyncLog detallado por unidad (EDARSAHUB.Comercial_SyncLog_v2)

UNIDADES: Se cargan dinámicamente desde EDARSAHUB.Unidades_Negocio

MÁXIMAS RESPETADAS:
- EDARSAHUB es el cerebro (destino de sincronización)
- No depende de conexiones en vivo para pintar dashboards
- Datos demo aislados (es_demo=0 para datos reales)
- EDARSAHUB SQL es la fuente operativa; la dependencia legacy no es fuente de negocio

REFACTORIZADO 2026-06-05:
- Eliminados hardcodes de códigos de unidades
- Usa UnidadesService para cargar unidades dinámicamente
- Fallback también usa UnidadesService (cache)

Autor: E1 Agent
Fecha: 2026-05-01
Actualizado: 2026-06-05 (Refactoring UnidadesService)
"""

import os
import uuid
import logging
from datetime import datetime, date, timedelta, timezone
from core.utils.operational_window import get_fecha_operacion
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

# Configuración
JOB_NAME = "sync_comercial_v2"
SYNC_INCREMENTAL_DAYS = int(os.environ.get("SYNC_COMERCIAL_V2_DAYS", "3"))


def _resolve_estatus_general(results: Dict[str, Any]) -> str:
    """No declara COMPLETADO si detalle o pagos ISCAM tienen fallos."""
    header_failures = int(results.get("unidades_fallidas") or 0)
    detail_failures = int(results.get("detalle_producto_fallidos") or 0)
    payment_failures = int(results.get("pagos_iscam_fallidos") or 0)
    if header_failures == 0 and detail_failures == 0 and payment_failures == 0:
        return "COMPLETADO"
    if int(results.get("unidades_exitosas") or 0) > 0:
        return "PARCIAL"
    return "FALLIDO"


# =============================================================================
# CONFIGURACIÓN DE UNIDADES - REFACTORIZADO CON UnidadesService
# =============================================================================
# Las unidades se cargan dinámicamente desde EDARSAHUB.Unidades_Negocio
# usando el servicio centralizado UnidadesService
# =============================================================================

def _get_unidades_from_edarsahub() -> tuple:
    """
    Obtiene unidades desde EDARSAHUB usando UnidadesService.
    
    REFACTORIZADO 2026-06-05: Usa UnidadesService en lugar de unidades_registry.
    Elimina fallback con hardcodes - UnidadesService tiene su propio cache.
    
    Returns:
        (unidades_softrestaurant, unidades_mpro) con códigos canónicos
    """
    try:
        from core.unidades_service import UnidadesService
        
        unidades_sr = []
        unidades_mpro = []
        
        for u in UnidadesService.get_all():
            sistema = (u.get('system_type') or '').upper()
            entry = {
                "unidad_negocio_pk": u.get('unidad_negocio_pk'),
                "unidad_negocio_id": u.get('codigo'),
                "nombre": u.get('nombre'),
                "server_id": u.get('server_id'),
                "sucursal_id": u.get('sucursal_origen_id') or "DEFAULT",
                "sistema": sistema
            }
            
            if 'SOFTRESTAURANT' in sistema:
                unidades_sr.append(entry)
            elif 'MPRO' in sistema:
                unidades_mpro.append(entry)
        
        logger.info(f"[SYNC_V2] Cargadas {len(unidades_sr)} unidades SoftRestaurant, {len(unidades_mpro)} unidades MPRO desde EDARSAHUB")
        
        return unidades_sr, unidades_mpro
        
    except Exception as e:
        logger.error(f"[SYNC_V2] Error cargando unidades desde EDARSAHUB: {e}")
        # Sin fallback hardcodeado - si falla EDARSAHUB, el job no puede correr
        return [], []


# =============================================================================
# FUNCIÓN PRINCIPAL DEL JOB
# =============================================================================

async def execute_sync_comercial_v2(db=None, detail_commit: bool = True, solo_unidades: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Ejecuta sincronización incremental de KPIs comerciales V2.
    
    Args:
        db: Dependencia técnica legacy opcional para locks/logs; no es fuente de negocio
        
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
    from scripts.poblar_ventas_detalle_producto_canonico import (
        get_unidades_negocio_pos,
        get_pos_config_for_unidad,
        _load_runtime_rows,
        _runtime_for,
        sync_detalle_producto_canonico_dia,
    )
    
    logger.info(f"[SYNC_COMERCIAL_V2] Iniciando sincronización incremental ({SYNC_INCREMENTAL_DAYS} días)")
    
    start_time = datetime.now(timezone.utc)
    run_id = f"INCR-{start_time.strftime('%Y%m%d-%H%M%S')}-{str(uuid.uuid4())[:4]}"
    
    # Calcular rango de fechas (últimos N días)
    
    results = {
        "job_name": JOB_NAME,
        "run_id": run_id,
        "tipo_sync": "INCREMENTAL",
        "dias_atras": SYNC_INCREMENTAL_DAYS,
        "fecha_inicio": None,
        "fecha_fin": None,
        "rango_fecha_operacion_por_unidad": True,
        "solo_unidades": [str(x) for x in solo_unidades] if solo_unidades else None,
        "inicio_ejecucion": start_time.isoformat(),
        "unidades_procesadas": 0,
        "unidades_exitosas": 0,
        "unidades_fallidas": 0,
        "total_insertados": 0,
        "total_actualizados": 0,
        "total_omitidos": 0,
        "total_errores": 0,
        "detalles_unidades": [],
        "errores": [],
        "detalle_producto_exitosos": 0,
        "detalle_producto_fallidos": 0,
        "detalle_producto_omitidos": 0,
        "detalle_producto_filas_insertadas": 0,
        "pagos_iscam_exitosos": 0,
        "pagos_iscam_fallidos": 0,
        "pagos_iscam_extraidos": 0,
        "pagos_iscam_insertados": 0,
    }
    
    def _sync_detalle_post_header(
        unidad_codigo,
        dia,
        detalle_unidad,
    ):
        """
        Ejecuta detalle únicamente después de que el header/KPI
        canónico de la unidad haya sincronizado correctamente.

        El fallo del detalle se registra de forma independiente.
        No invalida un header ya confirmado.
        """
        try:
            unidad_rows = get_unidades_negocio_pos(
                [unidad_codigo]
            )

            if len(unidad_rows) != 1:
                raise RuntimeError(
                    "Contexto POS canónico no único para "
                    f"unidad={unidad_codigo!r}"
                )

            cfg = get_pos_config_for_unidad(
                unidad_rows[0]
            )

            runtime_rows = _load_runtime_rows(
                dia,
                dia + timedelta(days=1),
                unidad_codigo,
            )

            runtime_row = _runtime_for(
                runtime_rows,
                cfg,
                dia,
            )

            if runtime_row is None:
                raise RuntimeError(
                    "Runtime V2 no disponible para "
                    f"unidad={unidad_codigo!r} "
                    f"fecha_operacion={dia}"
                )

            detail_result = (
                sync_detalle_producto_canonico_dia(
                    cfg=cfg,
                    dia=dia,
                    runtime_row=runtime_row,
                    run_id=run_id,
                    commit=detail_commit,
                    excluir_abiertas=True,
                )
            )

            status = detail_result.get("status")

            detail_trace = {
                "fecha_operacion": dia.isoformat(),
                "status": status,
                "filas_insertadas": int(
                    detail_result.get(
                        "filas_insertadas"
                    ) or 0
                ),
                "filas_preparadas": int(
                    detail_result.get(
                        "filas_destino_preparadas"
                    ) or 0
                ),
            }

            detalle_unidad.setdefault(
                "detalle_producto_dias",
                [],
            ).append(detail_trace)

            detalle_unidad[
                "detalle_producto_status"
            ] = status

            detalle_unidad[
                "detalle_producto_filas_insertadas"
            ] = sum(
                int(
                    item.get(
                        "filas_insertadas"
                    ) or 0
                )
                for item in detalle_unidad[
                    "detalle_producto_dias"
                ]
            )

            if status == "OK_HEADER_CANONICO":
                results[
                    "detalle_producto_exitosos"
                ] += 1

                results[
                    "detalle_producto_filas_insertadas"
                ] += detalle_unidad[
                    "detalle_producto_filas_insertadas"
                ]

            elif status == "NO_PROBAR_ABIERTO_REAL":
                results[
                    "detalle_producto_omitidos"
                ] += 1

            else:
                results[
                    "detalle_producto_fallidos"
                ] += 1

                detalle_unidad[
                    "detalle_producto_error"
                ] = status

        except Exception as exc:
            results[
                "detalle_producto_fallidos"
            ] += 1

            detalle_unidad[
                "detalle_producto_status"
            ] = "ERROR"

            detalle_unidad[
                "detalle_producto_error"
            ] = str(exc)

            detalle_unidad.setdefault(
                "detalle_producto_dias",
                [],
            ).append({
                "fecha_operacion": dia.isoformat(),
                "status": "ERROR",
                "filas_insertadas": 0,
                "error": str(exc),
            })

            logger.exception(
                "[SYNC_COMERCIAL_V2] "
                "Fallo detalle producto "
                "unidad=%s fecha=%s",
                unidad_codigo,
                dia,
            )

    def _sync_pagos_post_header(
        unidad_codigo,
        fecha_inicio_unidad,
        fecha_fin_unidad,
        detalle_unidad,
    ):
        """Sincroniza pagos ISCAM por día para cualquier POS tras un header válido."""
        from core.scheduler.jobs.inteligencia_comercial_enrich import (
            resync_pagos_unidad,
        )

        traces = []
        total_days = (fecha_fin_unidad - fecha_inicio_unidad).days + 1

        for offset in range(total_days):
            dia = fecha_inicio_unidad + timedelta(days=offset)
            ff = dia + timedelta(days=1)
            try:
                payment_result = resync_pagos_unidad(
                    unidad_codigo,
                    dia.isoformat(),
                    ff.isoformat(),
                    dry_run=not detail_commit,
                )
            except Exception as exc:
                payment_result = {
                    "unidad": unidad_codigo,
                    "error": f"{type(exc).__name__}: {exc}",
                    "pagos_extraidos": 0,
                    "pagos_insertados": 0,
                }

            trace = {
                "fecha_operacion": dia.isoformat(),
                "status": "ERROR" if payment_result.get("error") else "OK",
                "pagos_extraidos": int(payment_result.get("pagos_extraidos") or 0),
                "pagos_insertados": int(payment_result.get("pagos_insertados") or 0),
            }

            if payment_result.get("error"):
                trace["error"] = str(payment_result.get("error"))
                results["pagos_iscam_fallidos"] += 1
            else:
                results["pagos_iscam_exitosos"] += 1
                results["pagos_iscam_extraidos"] += trace["pagos_extraidos"]
                results["pagos_iscam_insertados"] += trace["pagos_insertados"]

            traces.append(trace)

        detalle_unidad["pagos_iscam_dias"] = traces
        detalle_unidad["pagos_iscam_status"] = (
            "ERROR" if any(item["status"] == "ERROR" for item in traces) else "OK"
        )
        detalle_unidad["pagos_iscam_extraidos"] = sum(
            item["pagos_extraidos"] for item in traces
        )
        detalle_unidad["pagos_iscam_insertados"] = sum(
            item["pagos_insertados"] for item in traces
        )

    # =========================================================================
    # FASE P0: CARGAR UNIDADES DESDE EDARSAHUB (códigos canónicos)
    # =========================================================================
    
    unidades_sr, unidades_mpro = _get_unidades_from_edarsahub()

    if solo_unidades:
        requested = {
            str(value).strip().upper()
            for value in solo_unidades
            if str(value).strip()
        }

        if not requested:
            raise ValueError(
                "solo_unidades fue proporcionado "
                "pero no contiene unidades válidas"
            )

        def _unit_selected(unidad):
            codigo = str(
                unidad.get("unidad_negocio_id") or ""
            ).strip().upper()

            pk = str(
                unidad.get("unidad_negocio_pk") or ""
            ).strip().upper()

            return (
                codigo in requested
                or pk in requested
            )

        unidades_sr = [
            unidad
            for unidad in unidades_sr
            if _unit_selected(unidad)
        ]

        unidades_mpro = [
            unidad
            for unidad in unidades_mpro
            if _unit_selected(unidad)
        ]

        resolved = {
            str(
                unidad.get("unidad_negocio_id") or ""
            ).strip().upper()
            for unidad in (
                unidades_sr + unidades_mpro
            )
        }

        unresolved = sorted(
            requested - resolved
        )

        if unresolved:
            raise ValueError(
                "Unidades solicitadas no resueltas: "
                + ", ".join(unresolved)
            )

    
    logger.info(f"[SYNC_COMERCIAL_V2] FASE P0: Procesando {len(unidades_sr)} SoftRestaurant + {len(unidades_mpro)} MPRO con códigos canónicos")
    
    # =========================================================================
    # SINCRONIZAR SOFTRESTAURANT
    # =========================================================================
    
    for unidad in unidades_sr:
        results["unidades_procesadas"] += 1
        unidad_id = unidad["unidad_negocio_id"]
        nombre = unidad["nombre"]
        
        fecha_fin = get_fecha_operacion(
            unidad["unidad_negocio_pk"]
        )
        fecha_inicio = (
            fecha_fin
            - timedelta(days=SYNC_INCREMENTAL_DAYS)
        )

        try:
            logger.info(f"[SYNC_COMERCIAL_V2] Sincronizando {nombre} (SoftRestaurant)...")
            
            # Crear configuración de la unidad
            config = UnidadNegocioConfig(
                unidad_negocio_pk=unidad["unidad_negocio_pk"],
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
                "fecha_inicio": fecha_inicio.isoformat(),
                "fecha_fin": fecha_fin.isoformat(),
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
                _sync_pagos_post_header(
                    unidad_id,
                    fecha_inicio,
                    fecha_fin,
                    detalle,
                )

                for detail_day_offset in range(
                    (fecha_fin - fecha_inicio).days + 1
                ):
                    detail_day = (
                        fecha_inicio
                        + timedelta(days=detail_day_offset)
                    )

                    _sync_detalle_post_header(
                        unidad_id,
                        detail_day,
                        detalle,
                    )

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
        
        fecha_fin = get_fecha_operacion(
            unidad["unidad_negocio_pk"]
        )
        fecha_inicio = (
            fecha_fin
            - timedelta(days=SYNC_INCREMENTAL_DAYS)
        )

        try:
            logger.info(f"[SYNC_COMERCIAL_V2] Sincronizando {nombre} (MPRO sucursal={sucursal_id})...")
            
            # Crear configuración de la unidad
            config = UnidadNegocioConfig(
                unidad_negocio_pk=unidad["unidad_negocio_pk"],
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
                "fecha_inicio": fecha_inicio.isoformat(),
                "fecha_fin": fecha_fin.isoformat(),
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
                _sync_pagos_post_header(
                    unidad_id,
                    fecha_inicio,
                    fecha_fin,
                    detalle,
                )

                for detail_day_offset in range(
                    (fecha_fin - fecha_inicio).days + 1
                ):
                    detail_day = (
                        fecha_inicio
                        + timedelta(days=detail_day_offset)
                    )

                    _sync_detalle_post_header(
                        unidad_id,
                        detail_day,
                        detalle,
                    )

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
    results["estatus_general"] = _resolve_estatus_general(results)
    
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
    Ejecuta sincronización manual controlada.

    Usa el mismo lock distribuido canónico que el scheduler
    automático para impedir solapamientos.

    Args:
        dias_atras: Número de días hacia atrás para sincronizar.
        solo_unidades: Lista opcional de unidad_negocio_id
            para filtrar.

    Returns:
        Dict con resultados.

    Raises:
        RuntimeError: si el lock canónico está ocupado o no
            puede adquirirse.
    """
    import asyncio

    from core.scheduler.locks import get_lock_manager

    global SYNC_INCREMENTAL_DAYS

    previous_incremental_days = SYNC_INCREMENTAL_DAYS
    SYNC_INCREMENTAL_DAYS = dias_atras

    logger.info(
        "[SYNC_COMERCIAL_V2] Ejecución manual: "
        "%s días, unidades=%s",
        dias_atras,
        solo_unidades or "TODAS",
    )

    async def _run_manual_locked() -> Dict[str, Any]:
        lock_manager = get_lock_manager()
        lock = lock_manager.get_lock(
            "sync_comercial_v2"
        )

        acquired = await lock.acquire(
            timeout_seconds=600
        )

        if not acquired:
            raise RuntimeError(
                "No se pudo adquirir el lock canónico "
                "sync_comercial_v2; existe otra ejecución "
                "en progreso o el mecanismo de lock falló."
            )

        heartbeat_started = False

        try:
            await lock.start_heartbeat_loop(
                interval_seconds=30,
                extend_seconds=600,
            )
            heartbeat_started = True

            return await execute_sync_comercial_v2(
                solo_unidades=solo_unidades,
            )

        finally:
            if heartbeat_started:
                await lock.stop_heartbeat_loop()

            await lock.release()

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        return loop.run_until_complete(
            _run_manual_locked()
        )

    finally:
        SYNC_INCREMENTAL_DAYS = (
            previous_incremental_days
        )

        try:
            asyncio.set_event_loop(None)
        finally:
            loop.close()



# =============================================================================
# EXPORTS
# =============================================================================

__all__ = ['execute_sync_comercial_v2', 'run_sync_comercial_v2_manual', 'JOB_NAME']
