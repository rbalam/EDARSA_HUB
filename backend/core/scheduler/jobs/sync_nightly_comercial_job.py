"""
EDARSA HUB - SYNC-N: Sincronización Nocturna de KPIs Comerciales
================================================================

Frecuencia: Diario a las 03:00
Ventana: Últimos 7 días

Proceso:
1. Para cada servidor activo (DATA_SOURCE)
2. Consultar KPIs de los últimos 7 días
3. UPSERT con detección de cambios
4. Cerrar períodos ABIERTOS anteriores a ayer
5. Generar log de cambios detectados

REGLAS:
- Puede actualizar documentos CERRADOS (force_update=True)
- No modifica documentos RECONCILIADOS
- Cierra automáticamente períodos antiguos
- Detecta y registra cambios vs versión anterior

Fecha: 2026-04-22
Versión: 1.0
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional


JOB_NAME = "sync_nightly_comercial"
VENTANA_DIAS = 7


async def execute_sync_nightly_comercial(db, context: Optional[Dict] = None) -> Dict:
    """
    Ejecuta la sincronización nocturna de KPIs comerciales.
    
    Args:
        db: Dependencia técnica legacy opcional para locks/logs
        context: Contexto opcional de ejecución
        
    Returns:
        Dict con resultados de la ejecución
    """
    from modules.comercial.kpis_repository import (
        init_kpis_repository,
        upsert_kpi_comercial,
        cerrar_periodos_anteriores,
        get_kpi_comercial,
        ESTADO_ABIERTO,
        ESTADO_CERRADO
    )
    from modules.comercial.repository import get_servers_for_tablero, init_comercial_repository
    
    start_time = datetime.now(timezone.utc)
    
    # Inicializar repositorios
    init_comercial_repository(db)
    init_kpis_repository(db)
    
    # Calcular rango de fechas
    # SYNC-N trabaja con datos de ayer hacia atrás (7 días)
    fecha_ayer = (datetime.now() - timedelta(days=1)).date()
    fecha_ini = fecha_ayer - timedelta(days=VENTANA_DIAS - 1)
    
    fecha_ini_str = fecha_ini.strftime('%Y-%m-%d')
    fecha_fin_str = fecha_ayer.strftime('%Y-%m-%d')
    
    # Fecha de corte para cierre de períodos (todo antes de ayer)
    fecha_corte = fecha_ayer.strftime('%Y-%m-%d')
    
    logging.info(
        f"[SYNC-N] Iniciando sincronización nocturna: {fecha_ini_str} a {fecha_fin_str}"
    )
    
    # Obtener servidores activos
    servers = await get_servers_for_tablero()
    
    results = {
        "job_name": JOB_NAME,
        "start_time": start_time.isoformat(),
        "fecha_inicio": fecha_ini_str,
        "fecha_fin": fecha_fin_str,
        "fecha_corte_cierre": fecha_corte,
        "servers_procesados": 0,
        "inserts": 0,
        "updates": 0,
        "skips": 0,
        "rejected": 0,
        "periodos_cerrados": 0,
        "cambios_detectados": [],
        "errors": [],
        "detalles_por_server": []
    }
    
    for server in servers:
        server_id = server.get("id")
        server_name = server.get("name", "Unknown")
        system_type = server.get("system_type", "")
        empresa_id = server.get("empresa_id", "")
        empresa_nombre = server.get("empresa_nombre", server.get("name", ""))
        
        if not server_id:
            continue
        
        server_result = {
            "server_id": server_id,
            "server_name": server_name,
            "system_type": system_type,
            "inserts": 0,
            "updates": 0,
            "skips": 0,
            "cambios": [],
            "errors": []
        }
        
        try:
            kpis_list = await _query_kpis_rango_completo(
                server, fecha_ini_str, fecha_fin_str
            )
            
            for kpi_dia in kpis_list:
                sucursal_id = kpi_dia.get("sucursal_id", kpi_dia.get("id", "DEFAULT"))
                fecha = kpi_dia.get("fecha", fecha_fin_str)
                
                # Obtener documento existente para comparar
                existing = await get_kpi_comercial(
                    server_id, empresa_id, str(sucursal_id), fecha
                )
                
                # Construir KPIs normalizados
                kpis = _normalize_kpis(kpi_dia)
                
                # Info de origen
                source_info = {
                    "type": "LIVE",
                    "query_timestamp": datetime.now(timezone.utc).isoformat(),
                    "query_duration_ms": kpi_dia.get("query_duration_ms", 0),
                    "connection_status": "OK",
                    "scheduler_job_id": f"{JOB_NAME}_{start_time.strftime('%Y%m%d_%H%M%S')}"
                }
                
                # Metadata
                metadata = {
                    "sucursal_nombre": kpi_dia.get("nombre", kpi_dia.get("sucursal", "")),
                    "empresa_nombre": empresa_nombre,
                    "system_type": system_type,
                    "unidad_negocio_id": kpi_dia.get("unidad_negocio_id")
                }
                
                # UPSERT con force_update para SYNC-N
                result = await upsert_kpi_comercial(
                    server_id=server_id,
                    empresa_id=empresa_id,
                    sucursal_id=str(sucursal_id),
                    fecha=fecha,
                    kpis=kpis,
                    source_info=source_info,
                    updated_by="scheduler_sync_n",
                    metadata=metadata,
                    force_update=True  # SYNC-N SÍ puede actualizar CERRADOS
                )
                
                action = result.get("action", "UNKNOWN")
                if action == "INSERT":
                    server_result["inserts"] += 1
                    results["inserts"] += 1
                elif action == "UPDATE":
                    server_result["updates"] += 1
                    results["updates"] += 1
                    
                    # Registrar cambio detectado
                    if existing:
                        cambio = {
                            "server": server_name,
                            "sucursal": sucursal_id,
                            "fecha": fecha,
                            "version_anterior": existing.get("version", 0),
                            "version_nueva": result.get("version", 0)
                        }
                        server_result["cambios"].append(cambio)
                        results["cambios_detectados"].append(cambio)
                        
                elif action == "SKIP":
                    server_result["skips"] += 1
                    results["skips"] += 1
                elif action == "REJECTED":
                    results["rejected"] += 1
            
            results["servers_procesados"] += 1
            
        except Exception as e:
            error_msg = f"{server_name}: {str(e)}"
            server_result["errors"].append(error_msg)
            results["errors"].append(error_msg)
            logging.error(f"[SYNC-N] Error en {server_name}: {e}")
        
        results["detalles_por_server"].append(server_result)
    
    # ========================================
    # CIERRE AUTOMÁTICO DE PERÍODOS
    # ========================================
    try:
        periodos_cerrados = await cerrar_periodos_anteriores(
            fecha_corte=fecha_corte,
            updated_by="scheduler_sync_n"
        )
        results["periodos_cerrados"] = periodos_cerrados
        logging.info(f"[SYNC-N] Cerrados {periodos_cerrados} períodos anteriores a {fecha_corte}")
    except Exception as e:
        error_msg = f"Error cerrando períodos: {str(e)}"
        results["errors"].append(error_msg)
        logging.error(f"[SYNC-N] {error_msg}")
    
    # Calcular duración
    end_time = datetime.now(timezone.utc)
    results["end_time"] = end_time.isoformat()
    results["duration_seconds"] = (end_time - start_time).total_seconds()
    
    logging.info(
        f"[SYNC-N] Completado: {results['servers_procesados']} servers, "
        f"{results['inserts']} inserts, {results['updates']} updates, "
        f"{results['skips']} skips, {results['periodos_cerrados']} cierres, "
        f"{len(results['cambios_detectados'])} cambios detectados, "
        f"{len(results['errors'])} errores"
    )
    
    return results


async def _query_kpis_rango_completo(
    server: dict, 
    fecha_ini: str, 
    fecha_fin: str
) -> List[dict]:
    """
    Consulta KPIs de un servidor para un rango completo de fechas.
    Itera día por día para SYNC-N.
    
    Returns:
        Lista de dicts con KPIs por sucursal/día
    """
    from modules.comercial.service import (
        get_kpis_softrestaurant,
        get_kpis_mpro_por_sucursal
    )
    
    system_type = server.get("system_type", "")
    results = []
    
    # Iterar día por día
    fecha_actual = datetime.strptime(fecha_ini, '%Y-%m-%d').date()
    fecha_final = datetime.strptime(fecha_fin, '%Y-%m-%d').date()
    
    while fecha_actual <= fecha_final:
        fecha_str = fecha_actual.strftime('%Y-%m-%d')
        
        try:
            if system_type == "SoftRestaurant":
                kpis = get_kpis_softrestaurant(
                    server=server,
                    fecha_ini=fecha_str,
                    fecha_fin=fecha_str,
                    fecha_ini_ant=fecha_str,
                    fecha_fin_ant=fecha_str,
                    fecha_ini_año_ant=fecha_str,
                    fecha_fin_año_ant=fecha_str,
                    dias_transcurridos=1,
                    dias_mes=30,
                    solo_ventas_dia=False
                )
                
                if kpis:
                    kpis["fecha"] = fecha_str
                    kpis["sucursal_id"] = server.get("sucursal_id", "DEFAULT")
                    results.append(kpis)
                    
            elif system_type == "MPRO":
                kpis_list = get_kpis_mpro_por_sucursal(
                    server=server,
                    fecha_ini=fecha_str,
                    fecha_fin=fecha_str,
                    fecha_ini_ant=fecha_str,
                    fecha_fin_ant=fecha_str,
                    fecha_ini_año_ant=fecha_str,
                    fecha_fin_año_ant=fecha_str,
                    dias_transcurridos=1,
                    dias_mes=30,
                    solo_ventas_dia=False
                )
                
                if isinstance(kpis_list, list):
                    for kpi in kpis_list:
                        kpi["fecha"] = fecha_str
                        results.append(kpi)
                elif kpis_list:
                    kpis_list["fecha"] = fecha_str
                    results.append(kpis_list)
                    
        except Exception as e:
            logging.warning(
                f"[SYNC-N] Error consultando {server.get('name')} "
                f"fecha {fecha_str}: {e}"
            )
        
        fecha_actual += timedelta(days=1)
    
    return results


def _normalize_kpis(raw_kpis: dict) -> dict:
    """
    Normaliza KPIs de diferentes sistemas a un formato común.
    """
    return {
        "ventas": float(raw_kpis.get("ventas", 0) or 0),
        "pax": int(raw_kpis.get("pax", 0) or 0),
        "cheques": int(raw_kpis.get("cheques", raw_kpis.get("cuentas", 0)) or 0),
        "ticket_promedio": float(raw_kpis.get("ticket_promedio", 0) or 0),
        "cheque_promedio": float(raw_kpis.get("cheque_promedio", 0) or 0),
        "propina": float(raw_kpis.get("propina", raw_kpis.get("propinas", 0)) or 0),
        "propina_efectivo": float(raw_kpis.get("propina_efectivo", 0) or 0),
        "propina_tarjeta": float(raw_kpis.get("propina_tarjeta", 0) or 0),
        "descuentos": float(raw_kpis.get("descuentos", 0) or 0),
        "cortesias": float(raw_kpis.get("cortesias", 0) or 0),
        "cancelaciones": float(raw_kpis.get("cancelaciones", 0) or 0),
        "impuestos": float(raw_kpis.get("impuestos", 0) or 0),
        "efectivo": float(raw_kpis.get("efectivo", 0) or 0),
        "tarjeta": float(raw_kpis.get("tarjeta", 0) or 0),
        "otros_pagos": float(raw_kpis.get("otros_pagos", 0) or 0),
    }
