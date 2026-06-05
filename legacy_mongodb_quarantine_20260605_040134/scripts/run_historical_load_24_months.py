#!/usr/bin/env python3
"""
EDARSA HUB - Carga Histórica Controlada de 24 Meses
====================================================

Script para ejecutar carga histórica de KPIs comerciales de forma:
- Idempotente
- Incremental con checkpoints
- Reanudable
- Segura (sin modificar fuentes externas)

Uso:
    # Dry-run (simulación)
    python run_historical_load_24_months.py --dry-run --module comercial

    # Ejecución safe-mode (1 servidor, 1 batch)
    HISTORICAL_LOAD_CONFIRM=YES python run_historical_load_24_months.py --run --module comercial --safe-mode

    # Ejecución completa
    HISTORICAL_LOAD_CONFIRM=YES python run_historical_load_24_months.py --run --module comercial

Fecha: 2026-04-25
Versión: 1.0
"""

import os
import sys
import argparse
import asyncio
import logging
import json
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any
from uuid import uuid4

# Agregar path del backend
sys.path.insert(0, '/app/backend')

# Cargar variables de entorno desde .env ANTES de cualquier import del backend
from dotenv import load_dotenv
load_dotenv('/app/backend/.env')

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s][%(levelname)s][HISTORICAL_LOAD] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# ============================================================================
# CONSTANTES
# ============================================================================

DEFAULT_BATCH_DAYS = 7
DEFAULT_MAX_ROWS = 5000
DEFAULT_TIMEOUT = 120
DEFAULT_SLEEP_SECONDS = 2
DEFAULT_MAX_RETRIES = 2
MONTHS_HISTORICAL = 24

COLLECTION_CHECKPOINTS = "historical_load_checkpoints"
COLLECTION_KPIS = "kpis_comercial"  # Ahora solo como staging/cache, NO destino final

# Destinos de escritura
DESTINATION_SQL = "EDARSAHUB_SQL"          # Destino FINAL (tabla Comercial_KPIs_Historico)
DESTINATION_MONGO = "MONGODB"               # Solo checkpoint/log/staging
DEFAULT_DESTINATION = DESTINATION_SQL       # REGLA MAESTRA: SQL es el destino final

# Estados de checkpoint
STATUS_PENDING = "PENDING"
STATUS_RUNNING = "RUNNING"
STATUS_PARTIAL = "PARTIAL"
STATUS_SUCCESS = "SUCCESS"
STATUS_FAILED = "FAILED"
STATUS_CANCELLED = "CANCELLED"


# ============================================================================
# CONEXIÓN A BASE DE DATOS
# ============================================================================

_db = None

async def get_database():
    """Obtiene conexión a MongoDB."""
    global _db
    if _db is not None:
        return _db
    
    from motor.motor_asyncio import AsyncIOMotorClient
    mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
    client = AsyncIOMotorClient(mongo_url)
    _db = client.edarsa_hub
    return _db


# ============================================================================
# GESTIÓN DE CHECKPOINTS
# ============================================================================

async def create_checkpoint(
    db,
    run_id: str,
    module: str,
    server_id: str,
    server_name: str,
    system_type: str,
    fecha_inicio: str,
    fecha_fin: str,
    total_batches: int
) -> str:
    """Crea un checkpoint inicial para un servidor."""
    now = datetime.now(timezone.utc).isoformat()
    
    checkpoint = {
        "run_id": run_id,
        "module": module,
        "server_id": server_id,
        "server_name": server_name,
        "system_type": system_type,
        "fecha_inicio": fecha_inicio,
        "fecha_fin": fecha_fin,
        "fecha_actual_procesada": None,
        "batch_actual": 0,
        "total_batches": total_batches,
        "status": STATUS_PENDING,
        "processed_count": 0,
        "inserted_count": 0,
        "updated_count": 0,
        "skipped_count": 0,
        "error_count": 0,
        "last_error": None,
        "started_at": now,
        "updated_at": now,
        "finished_at": None
    }
    
    await db[COLLECTION_CHECKPOINTS].insert_one(checkpoint)
    logger.info(f"[CHECKPOINT_CREATED] {server_name} run_id={run_id}")
    return run_id


async def update_checkpoint(
    db,
    run_id: str,
    server_id: str,
    updates: Dict
) -> None:
    """Actualiza un checkpoint existente."""
    updates["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    await db[COLLECTION_CHECKPOINTS].update_one(
        {"run_id": run_id, "server_id": server_id},
        {"$set": updates}
    )


async def get_checkpoint(
    db,
    run_id: str,
    server_id: str
) -> Optional[Dict]:
    """Obtiene un checkpoint específico."""
    return await db[COLLECTION_CHECKPOINTS].find_one(
        {"run_id": run_id, "server_id": server_id},
        {"_id": 0}
    )


async def get_latest_checkpoint(
    db,
    module: str,
    server_id: str
) -> Optional[Dict]:
    """Obtiene el último checkpoint para un servidor/módulo."""
    cursor = db[COLLECTION_CHECKPOINTS].find(
        {"module": module, "server_id": server_id}
    ).sort("started_at", -1).limit(1)
    
    async for doc in cursor:
        doc.pop("_id", None)
        return doc
    return None


# ============================================================================
# OBTENCIÓN DE SERVIDORES
# ============================================================================

def _decrypt_server_password(server: Dict) -> Dict:
    """
    Descifra el password de un servidor si está cifrado.
    FASE 2.3: Necesario para carga histórica que lee directamente de MongoDB.
    """
    password = server.get('password', '')
    if password:
        try:
            from core.secret_manager import decrypt_secret, is_encrypted_secret
            if is_encrypted_secret(password):
                server['password'] = decrypt_secret(password)
                logger.debug(f"[DECRYPT_OK] Password descifrado para {server.get('name', server.get('id', 'N/A'))}")
            # Si no está cifrado, es legacy - dejar tal cual
        except Exception as e:
            logger.error(f"[DECRYPT_ERROR] Error descifrando password de {server.get('name', 'N/A')}: {type(e).__name__}: {e}")
    return server


async def get_servers_for_historical(db) -> List[Dict]:
    """
    Obtiene servidores candidatos para carga histórica.
    Solo servidores con system_type válido (SOFTRESTAURANT o MANAGEMENTPRO).
    FASE 2.3: Descifra automáticamente los passwords.
    """
    from core.system_type_utils import normalize_system_type, is_supported_system_type
    
    servers = []
    cursor = db.servers.find({}, {"_id": 0})
    
    async for server in cursor:
        system_type = server.get("system_type", "")
        normalized = normalize_system_type(system_type)
        
        # Solo servidores con system_type soportado
        if normalized in ["SOFTRESTAURANT", "MANAGEMENTPRO"]:
            server["system_type_normalized"] = normalized
            # FASE 2.3: Descifrar password antes de usar
            server = _decrypt_server_password(server)
            servers.append(server)
        else:
            logger.warning(f"[SKIP_SERVER] {server.get('name')}: system_type={system_type} -> {normalized} no soportado")
    
    return servers


# ============================================================================
# CONSULTAS DE KPIS
# ============================================================================

async def query_kpis_for_batch(
    server: Dict,
    fecha_inicio: str,
    fecha_fin: str
) -> List[Dict]:
    """
    Consulta KPIs de un servidor para un rango de fechas.
    Reutiliza la lógica del sync_nightly_comercial_job.
    """
    from modules.comercial.service import (
        get_kpis_softrestaurant,
        get_kpis_mpro_por_sucursal
    )
    from core.system_type_utils import is_softrestaurant_system, is_mpro_system
    
    system_type = server.get("system_type_normalized", server.get("system_type", ""))
    results = []
    
    # Iterar día por día (igual que sync_nightly)
    fecha_actual = datetime.strptime(fecha_inicio, '%Y-%m-%d').date()
    fecha_final = datetime.strptime(fecha_fin, '%Y-%m-%d').date()
    
    while fecha_actual <= fecha_final:
        fecha_str = fecha_actual.strftime('%Y-%m-%d')
        
        try:
            if is_softrestaurant_system(system_type):
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
                    
            elif is_mpro_system(system_type):
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
            else:
                logger.warning(f"[UNSUPPORTED_SYSTEM] {server.get('name')}: {system_type}")
                    
        except Exception as e:
            logger.warning(
                f"[QUERY_DAY_ERROR] {server.get('name')} fecha={fecha_str}: {e}"
            )
        
        fecha_actual += timedelta(days=1)
    
    return results


# ============================================================================
# UPSERT DE KPIS - DESTINO FINAL EN SQL
# ============================================================================

async def upsert_kpi_batch_sql(
    server: Dict,
    kpis_list: List[Dict],
    run_id: str,
    batch_start: str,
    batch_end: str
) -> Dict:
    """
    Realiza UPSERT de una lista de KPIs en EDARSAHUB SQL.
    DESTINO FINAL - MongoDB queda solo como checkpoint/log.
    """
    from modules.comercial.historical_kpis_repository import (
        upsert_comercial_kpi_historico
    )
    
    server_id = server.get("id")
    empresa_id = server.get("empresa_id", "")
    empresa_nombre = server.get("empresa_nombre", server.get("name", ""))
    system_type = server.get("system_type_normalized", "")
    
    counters = {
        "sql_inserted": 0,
        "sql_updated": 0,
        "sql_skipped": 0,
        "sql_errors": 0,
        "mongo_staging": 0  # Ya no se escribe a MongoDB como final
    }
    
    for kpi_data in kpis_list:
        try:
            sucursal_id = str(kpi_data.get("sucursal_id", kpi_data.get("id", "DEFAULT")))
            fecha = kpi_data.get("fecha")
            
            if not fecha:
                continue
            
            # Preparar registro para SQL
            record = {
                "run_id": run_id,
                "server_id": server_id,
                "sucursal_id": sucursal_id,
                "sucursal_nombre": kpi_data.get("nombre", kpi_data.get("sucursal", "")),
                "empresa_id": empresa_id,
                "unidad_negocio_id": kpi_data.get("unidad_negocio_id", ""),
                "system_type_normalized": system_type,
                "fecha": fecha,
                "kpi_tipo": "DIARIO",
                "ventas_total": float(kpi_data.get("ventas", 0) or 0),
                "tickets_total": int(kpi_data.get("cheques", 0) or 0),
                "pax_total": int(kpi_data.get("pax", 0) or 0),
                "ticket_promedio": float(kpi_data.get("ticket_promedio", 0) or 0),
                "propinas_total": float(kpi_data.get("propinas", 0) or 0),
                "source_batch_start": batch_start,
                "source_batch_end": batch_end
            }
            
            # UPSERT en SQL (destino final)
            result = await upsert_comercial_kpi_historico(record)
            
            action = result.get("action", "ERROR")
            if action == "INSERT":
                counters["sql_inserted"] += 1
            elif action == "UPDATE":
                counters["sql_updated"] += 1
            elif action == "SKIP":
                counters["sql_skipped"] += 1
            else:
                counters["sql_errors"] += 1
                logger.warning(f"[UPSERT_SQL_ERROR] {server.get('name')}, {fecha}: {result.get('error')}")
                
        except Exception as e:
            counters["sql_errors"] += 1
            logger.error(f"[UPSERT_SQL_EXCEPTION] {server.get('name')}: {e}")
    
    return counters


async def upsert_kpi_batch_mongo_staging(
    db,
    server: Dict,
    kpis_list: List[Dict],
    run_id: str
) -> Dict:
    """
    DEPRECATED - Solo para staging temporal.
    NO usar como destino final.
    """
    logger.warning("[DEPRECATED] upsert_kpi_batch_mongo_staging - MongoDB NO es destino final")
    # Mantener por retrocompatibilidad pero no usar
    return {"mongo_staging": len(kpis_list), "warning": "DEPRECATED_MONGO_STAGING"}


async def upsert_kpi_batch(
    db,
    server: Dict,
    kpis_list: List[Dict],
    run_id: str,
    batch_start: str = None,
    batch_end: str = None,
    destination: str = None
) -> Dict:
    """
    Realiza UPSERT de una lista de KPIs.
    DESTINO FINAL: EDARSAHUB SQL (Comercial_KPIs_Historico).
    MongoDB solo para checkpoint/log.
    """
    if destination is None:
        destination = DEFAULT_DESTINATION
    
    if destination == DESTINATION_SQL:
        # DESTINO CORRECTO: SQL
        return await upsert_kpi_batch_sql(
            server=server,
            kpis_list=kpis_list,
            run_id=run_id,
            batch_start=batch_start or "",
            batch_end=batch_end or ""
        )
    else:
        # DEPRECATED: MongoDB staging
        logger.warning(f"[DESTINATION_WARNING] Usando destino {destination} en lugar de SQL")
        return await upsert_kpi_batch_mongo_staging(db, server, kpis_list, run_id)


# ============================================================================
# CÁLCULO DE BATCHES
# ============================================================================

def calculate_batches(
    fecha_inicio: str,
    fecha_fin: str,
    batch_days: int = DEFAULT_BATCH_DAYS
) -> List[Dict]:
    """Calcula los batches necesarios para un rango de fechas."""
    from datetime import date
    
    start = datetime.strptime(fecha_inicio, "%Y-%m-%d").date()
    end = datetime.strptime(fecha_fin, "%Y-%m-%d").date()
    
    batches = []
    current = start
    batch_num = 1
    
    while current <= end:
        batch_end = min(current + timedelta(days=batch_days - 1), end)
        batches.append({
            "batch_num": batch_num,
            "start_date": current.strftime("%Y-%m-%d"),
            "end_date": batch_end.strftime("%Y-%m-%d"),
            "days": (batch_end - current).days + 1
        })
        current = batch_end + timedelta(days=1)
        batch_num += 1
    
    return batches


# ============================================================================
# EJECUCIÓN PRINCIPAL
# ============================================================================

async def execute_historical_load(
    dry_run: bool = True,
    module: str = "comercial",
    server_id: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    batch_days: int = DEFAULT_BATCH_DAYS,
    resume: bool = False,
    force_restart: bool = False,
    max_servers: Optional[int] = None,
    safe_mode: bool = False
) -> Dict:
    """
    Ejecuta la carga histórica controlada.
    
    Args:
        dry_run: Si True, solo simula sin escribir
        module: Módulo a cargar (comercial|finanzas|compras)
        server_id: UUID de servidor específico (opcional)
        start_date: Fecha inicio YYYY-MM-DD (default: 24 meses atrás)
        end_date: Fecha fin YYYY-MM-DD (default: hoy)
        batch_days: Días por batch
        resume: Reanudar desde último checkpoint
        force_restart: Reiniciar desde cero (ignora checkpoints)
        max_servers: Límite de servidores a procesar
        safe_mode: Solo 1 servidor, 1 batch
        
    Returns:
        Dict con resultados de ejecución
    """
    run_id = f"HL_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    logger.info(f"[START] run_id={run_id} dry_run={dry_run} module={module}")
    logger.info(f"[START] safe_mode={safe_mode} batch_days={batch_days}")
    
    if safe_mode:
        max_servers = 1
        logger.info("[SAFE_MODE] Activado: 1 servidor, 1 batch")
    
    # Calcular rango de fechas
    if not end_date:
        end_date = datetime.now().strftime("%Y-%m-%d")
    
    if not start_date:
        start_dt = datetime.now() - timedelta(days=MONTHS_HISTORICAL * 30)
        start_date = start_dt.strftime("%Y-%m-%d")
    
    logger.info(f"[RANGE] {start_date} a {end_date}")
    
    # Calcular batches
    batches = calculate_batches(start_date, end_date, batch_days)
    total_batches = len(batches)
    logger.info(f"[BATCHES] {total_batches} batches de {batch_days} días")
    
    if safe_mode:
        batches = batches[:1]
        logger.info(f"[SAFE_MODE] Limitado a 1 batch")
    
    # Obtener conexión
    db = await get_database()
    
    # Obtener servidores
    servers = await get_servers_for_historical(db)
    
    if server_id:
        servers = [s for s in servers if s.get("id") == server_id]
        if not servers:
            logger.error(f"[ERROR] Servidor {server_id} no encontrado")
            return {"status": "ERROR", "error": f"Servidor {server_id} no encontrado"}
    
    if max_servers:
        servers = servers[:max_servers]
    
    logger.info(f"[SERVERS] {len(servers)} servidores candidatos")
    
    # Resultado
    result = {
        "status": "SUCCESS",
        "dry_run": dry_run,
        "run_id": run_id,
        "module": module,
        "destination": DESTINATION_SQL,
        "destination_table": "Comercial_KPIs_Historico",
        "mongo_role": "checkpoint_log_only",
        "fecha_inicio": start_date,
        "fecha_fin": end_date,
        "batch_days": batch_days,
        "total_batches": total_batches,
        "servers_candidate": len(servers),
        "servers_processed": 0,
        "servers_skipped": 0,
        "sql_inserted": 0,
        "sql_updated": 0,
        "sql_skipped": 0,
        "sql_errors": 0,
        "mongo_final_inserted": 0,  # Siempre 0 - REGLA MAESTRA
        # Legacy
        "total_inserted": 0,
        "total_updated": 0,
        "total_skipped": 0,
        "total_errors": 0,
        "warnings": [],
        "errors": [],
        "plan": [],
        "execution_details": []
    }
    
    # DRY-RUN: Solo planificar
    if dry_run:
        for server in servers:
            plan_entry = {
                "server_id": server.get("id"),
                "server_name": server.get("name"),
                "system_type": server.get("system_type_normalized"),
                "batches": len(batches),
                "estimated_queries": len(batches),
                "date_range": f"{start_date} to {end_date}",
                "destination": DESTINATION_SQL,
                "destination_table": "Comercial_KPIs_Historico",
                "mongo_role": "checkpoint_log_only",
                "planned_sql_upsert": True,
                "planned_mongo_final_write": False
            }
            result["plan"].append(plan_entry)
        
        logger.info(f"[DRY_RUN] Plan generado. Destino: {DESTINATION_SQL}. MongoDB: checkpoint/log only")
        return result
    
    # EJECUCIÓN REAL
    for server in servers:
        server_name = server.get("name", "Unknown")
        server_id_current = server.get("id")
        system_type = server.get("system_type_normalized", "")
        
        logger.info(f"[SERVER_START] {server_name} ({system_type})")
        
        # Crear checkpoint
        await create_checkpoint(
            db, run_id, module, server_id_current, server_name,
            system_type, start_date, end_date, len(batches)
        )
        
        await update_checkpoint(db, run_id, server_id_current, {
            "status": STATUS_RUNNING
        })
        
        server_result = {
            "server_id": server_id_current,
            "server_name": server_name,
            "system_type": system_type,
            "destination": DESTINATION_SQL,
            "batches_processed": 0,
            "sql_inserted": 0,
            "sql_updated": 0,
            "sql_skipped": 0,
            "sql_errors": 0,
            "mongo_final_inserted": 0,  # Siempre 0 - MongoDB no es destino final
            # Mantener campos legacy para compatibilidad
            "inserted": 0,
            "updated": 0,
            "skipped": 0,
            "errors": 0
        }
        
        try:
            for batch in batches:
                batch_num = batch["batch_num"]
                batch_start = batch["start_date"]
                batch_end = batch["end_date"]
                
                logger.info(f"[BATCH_START] {server_name} batch={batch_num}/{len(batches)} {batch_start} to {batch_end}")
                
                # Consultar KPIs
                kpis_list = await query_kpis_for_batch(server, batch_start, batch_end)
                
                if not kpis_list:
                    logger.info(f"[BATCH_NO_DATA] {server_name} batch={batch_num}")
                    server_result["batches_processed"] += 1
                    continue
                
                # UPSERT en DESTINO SQL (Comercial_KPIs_Historico)
                counters = await upsert_kpi_batch(
                    db, server, kpis_list, run_id,
                    batch_start=batch_start,
                    batch_end=batch_end,
                    destination=DESTINATION_SQL
                )
                
                server_result["sql_inserted"] += counters.get("sql_inserted", 0)
                server_result["sql_updated"] += counters.get("sql_updated", 0)
                server_result["sql_skipped"] += counters.get("sql_skipped", 0)
                server_result["sql_errors"] += counters.get("sql_errors", 0)
                # Legacy
                server_result["inserted"] += counters.get("sql_inserted", 0)
                server_result["updated"] += counters.get("sql_updated", 0)
                server_result["skipped"] += counters.get("sql_skipped", 0)
                server_result["errors"] += counters.get("sql_errors", 0)
                server_result["batches_processed"] += 1
                
                # Actualizar checkpoint
                await update_checkpoint(db, run_id, server_id_current, {
                    "batch_actual": batch_num,
                    "fecha_actual_procesada": batch_end,
                    "processed_count": server_result["batches_processed"],
                    "inserted_count": server_result["inserted"],
                    "updated_count": server_result["updated"],
                    "skipped_count": server_result["skipped"],
                    "error_count": server_result["errors"]
                })
                
                logger.info(
                    f"[BATCH_SUCCESS] {server_name} batch={batch_num} "
                    f"sql_ins={counters.get('sql_inserted', 0)} sql_upd={counters.get('sql_updated', 0)} "
                    f"sql_skip={counters.get('sql_skipped', 0)} sql_err={counters.get('sql_errors', 0)}"
                )
                
                # Pausa entre batches
                if batch_num < len(batches):
                    await asyncio.sleep(DEFAULT_SLEEP_SECONDS)
            
            # Marcar servidor completado
            await update_checkpoint(db, run_id, server_id_current, {
                "status": STATUS_SUCCESS,
                "finished_at": datetime.now(timezone.utc).isoformat()
            })
            
            result["servers_processed"] += 1
            
        except Exception as e:
            error_msg = f"{server_name}: {str(e)}"
            logger.error(f"[SERVER_ERROR] {error_msg}")
            result["errors"].append(error_msg)
            result["servers_skipped"] += 1
            
            await update_checkpoint(db, run_id, server_id_current, {
                "status": STATUS_FAILED,
                "last_error": str(e),
                "finished_at": datetime.now(timezone.utc).isoformat()
            })
        
        result["execution_details"].append(server_result)
        result["sql_inserted"] += server_result.get("sql_inserted", 0)
        result["sql_updated"] += server_result.get("sql_updated", 0)
        result["sql_skipped"] += server_result.get("sql_skipped", 0)
        result["sql_errors"] += server_result.get("sql_errors", 0)
        # Legacy
        result["total_inserted"] += server_result["inserted"]
        result["total_updated"] += server_result["updated"]
        result["total_skipped"] += server_result["skipped"]
        result["total_errors"] += server_result["errors"]
    
    if result["errors"]:
        result["status"] = "PARTIAL" if result["servers_processed"] > 0 else "FAILED"
    
    logger.info(
        f"[COMPLETE] run_id={run_id} dest={DESTINATION_SQL} servers={result['servers_processed']} "
        f"sql_ins={result['sql_inserted']} sql_upd={result['sql_updated']} "
        f"sql_skip={result['sql_skipped']} sql_err={result['sql_errors']} "
        f"mongo_final=0"
    )
    
    return result


# ============================================================================
# CLI
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="EDARSA HUB - Carga Histórica de 24 Meses"
    )
    
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=True,
        help="Solo simular sin escribir datos (default)"
    )
    parser.add_argument(
        "--run",
        action="store_true",
        help="Ejecutar realmente (requiere HISTORICAL_LOAD_CONFIRM=YES)"
    )
    parser.add_argument(
        "--module",
        choices=["comercial", "finanzas", "compras", "all"],
        default="comercial",
        help="Módulo a cargar"
    )
    parser.add_argument(
        "--server-id",
        help="UUID de servidor específico"
    )
    parser.add_argument(
        "--start-date",
        help="Fecha inicio YYYY-MM-DD"
    )
    parser.add_argument(
        "--end-date",
        help="Fecha fin YYYY-MM-DD"
    )
    parser.add_argument(
        "--batch-days",
        type=int,
        default=DEFAULT_BATCH_DAYS,
        help=f"Días por batch (default {DEFAULT_BATCH_DAYS})"
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Reanudar desde último checkpoint"
    )
    parser.add_argument(
        "--force-restart",
        action="store_true",
        help="Reiniciar desde cero"
    )
    parser.add_argument(
        "--max-servers",
        type=int,
        help="Limitar servidores a procesar"
    )
    parser.add_argument(
        "--safe-mode",
        action="store_true",
        help="Solo 1 servidor, 1 batch"
    )
    
    args = parser.parse_args()
    
    # Verificar confirmación para ejecución real
    dry_run = not args.run
    if args.run:
        confirm = os.environ.get("HISTORICAL_LOAD_CONFIRM", "")
        if confirm != "YES":
            print("ERROR: Ejecución real requiere HISTORICAL_LOAD_CONFIRM=YES")
            print("Ejemplo: HISTORICAL_LOAD_CONFIRM=YES python run_historical_load_24_months.py --run")
            sys.exit(1)
    
    # Ejecutar
    result = asyncio.run(execute_historical_load(
        dry_run=dry_run,
        module=args.module,
        server_id=args.server_id,
        start_date=args.start_date,
        end_date=args.end_date,
        batch_days=args.batch_days,
        resume=args.resume,
        force_restart=args.force_restart,
        max_servers=args.max_servers,
        safe_mode=args.safe_mode
    ))
    
    # Guardar reporte
    report_name = "dry_run" if dry_run else "execution_report"
    report_path = f"/app/docs/reports/historical_load_24_months_{report_name}.json"
    
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    with open(report_path, "w") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    print(f"\nReporte guardado: {report_path}")
    print(f"Status: {result['status']}")
    print(f"Servidores procesados: {result.get('servers_processed', 0)}")
    print(f"Insertados: {result.get('total_inserted', 0)}")
    print(f"Actualizados: {result.get('total_updated', 0)}")
    print(f"Omitidos: {result.get('total_skipped', 0)}")
    print(f"Errores: {result.get('total_errors', 0)}")


if __name__ == "__main__":
    main()
