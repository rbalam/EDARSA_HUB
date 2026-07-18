"""
EDARSA HUB - SYNC-S: Sincronización Corta de KPIs Comerciales
=============================================================

Frecuencia: Cada 15 minutos
Ventana: Últimas 48 horas

Proceso:
1. Para cada servidor activo (DATA_SOURCE)
2. Consultar KPIs de los últimos 2 días
3. UPSERT en kpis_comercial
4. Solo actualiza documentos en estado ABIERTO

REGLAS:
- Idempotente: ejecutar múltiples veces produce el mismo resultado
- No modifica documentos CERRADOS ni RECONCILIADOS
- Registra trazabilidad completa de origen

Fecha: 2026-04-22
Versión: 1.0
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional


JOB_NAME = "sync_short_comercial"
VENTANA_HORAS = 48  # 2 días


async def execute_sync_short_comercial(db, context: Optional[Dict] = None) -> Dict:
    """
    Ejecuta la sincronización corta de KPIs comerciales.
    
    Args:
        db: Dependencia técnica legacy opcional para locks/logs
        context: Contexto opcional de ejecución
        
    Returns:
        Dict con resultados de la ejecución
    """
    from modules.comercial.kpis_repository import (
        init_kpis_repository,
        upsert_kpi_comercial,
        ESTADO_ABIERTO
    )
    from modules.comercial.repository import get_servers_for_tablero, init_comercial_repository
    
    start_time = datetime.now(timezone.utc)
    
    # Inicializar repositorios
    init_comercial_repository(db)
    init_kpis_repository(db)
    
    # Calcular rango de fechas (últimas 48 horas)
    fecha_fin = datetime.now().date()
    fecha_ini = fecha_fin - timedelta(days=2)
    
    fecha_ini_str = fecha_ini.strftime('%Y-%m-%d')
    fecha_fin_str = fecha_fin.strftime('%Y-%m-%d')
    
    logging.info(
        f"[SYNC-S] Iniciando sincronización corta: {fecha_ini_str} a {fecha_fin_str}"
    )
    
    # Obtener servidores activos
    servers = await get_servers_for_tablero()
    
    results = {
        "job_name": JOB_NAME,
        "start_time": start_time.isoformat(),
        "fecha_inicio": fecha_ini_str,
        "fecha_fin": fecha_fin_str,
        "servers_procesados": 0,
        "inserts": 0,
        "updates": 0,
        "skips": 0,
        "rejected": 0,
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
            "errors": []
        }
        
        try:
            kpis_list = await _query_kpis_rango(
                server, fecha_ini_str, fecha_fin_str
            )
            
            for kpi_dia in kpis_list:
                sucursal_id = kpi_dia.get("sucursal_id", kpi_dia.get("id", "DEFAULT"))
                fecha = kpi_dia.get("fecha", fecha_fin_str)
                
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
                
                # UPSERT idempotente
                result = await upsert_kpi_comercial(
                    server_id=server_id,
                    empresa_id=empresa_id,
                    sucursal_id=str(sucursal_id),
                    fecha=fecha,
                    kpis=kpis,
                    source_info=source_info,
                    updated_by="scheduler_sync_s",
                    metadata=metadata,
                    force_update=False  # SYNC-S no fuerza en CERRADOS
                )
                
                action = result.get("action", "UNKNOWN")
                if action == "INSERT":
                    server_result["inserts"] += 1
                    results["inserts"] += 1
                elif action == "UPDATE":
                    server_result["updates"] += 1
                    results["updates"] += 1
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
            logging.error(f"[SYNC-S] Error en {server_name}: {e}")
        
        results["detalles_por_server"].append(server_result)
    
    # Calcular duración
    end_time = datetime.now(timezone.utc)
    results["end_time"] = end_time.isoformat()
    results["duration_seconds"] = (end_time - start_time).total_seconds()
    
    logging.info(
        f"[SYNC-S] Completado: {results['servers_procesados']} servers, "
        f"{results['inserts']} inserts, {results['updates']} updates, "
        f"{results['skips']} skips, {len(results['errors'])} errores"
    )
    
    return results


async def _query_kpis_rango(
    server: dict, 
    fecha_ini: str, 
    fecha_fin: str
) -> List[dict]:
    """
    Consulta KPIs de un servidor para un rango de fechas.
    
    Returns:
        Lista de dicts con KPIs por sucursal/día
    """
    from modules.comercial.service import (
        get_kpis_softrestaurant,
        get_kpis_mpro_por_sucursal
    )
    
    system_type = server.get("system_type", "")
    
    results = []
    
    try:
        if system_type == "SoftRestaurant":
            kpis = get_kpis_softrestaurant(
                server=server,
                fecha_ini=fecha_ini,
                fecha_fin=fecha_fin,
                fecha_ini_ant=fecha_ini,
                fecha_fin_ant=fecha_fin,
                fecha_ini_año_ant=fecha_ini,
                fecha_fin_año_ant=fecha_fin,
                dias_transcurridos=1,
                dias_mes=30,
                solo_ventas_dia=False
            )
            
            if kpis:
                kpis["fecha"] = fecha_fin
                kpis["sucursal_id"] = server.get("sucursal_id", "DEFAULT")
                results.append(kpis)
                
        elif system_type == "MPRO":
            kpis_list = get_kpis_mpro_por_sucursal(
                server=server,
                fecha_ini=fecha_ini,
                fecha_fin=fecha_fin,
                fecha_ini_ant=fecha_ini,
                fecha_fin_ant=fecha_fin,
                fecha_ini_año_ant=fecha_ini,
                fecha_fin_año_ant=fecha_fin,
                dias_transcurridos=1,
                dias_mes=30,
                solo_ventas_dia=False
            )
            
            if isinstance(kpis_list, list):
                for kpi in kpis_list:
                    kpi["fecha"] = fecha_fin
                    results.append(kpi)
            elif kpis_list:
                kpis_list["fecha"] = fecha_fin
                results.append(kpis_list)
                
    except Exception as e:
        logging.warning(f"[SYNC-S] Error consultando {server.get('name')}: {e}")
    
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
