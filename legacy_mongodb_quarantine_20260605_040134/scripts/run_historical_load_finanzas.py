#!/usr/bin/env python3
"""
EDARSA HUB - Carga Histórica de Finanzas (24 Meses)
====================================================

Script para ejecutar carga histórica de KPIs de Finanzas:
- Cortes Z (ingresos diarios)
- Cuentas por Pagar (CxP)

Fuentes:
- SOFTRESTAURANT: Cortes Z y CxP
- MANAGEMENTPRO: Cortes Z

Uso:
    # Dry-run (simulación)
    python run_historical_load_finanzas.py --dry-run

    # Ejecución safe-mode (1 servidor, 1 batch)
    HISTORICAL_LOAD_CONFIRM=YES python run_historical_load_finanzas.py --run --safe-mode

    # Ejecución completa
    HISTORICAL_LOAD_CONFIRM=YES python run_historical_load_finanzas.py --run

Fecha: 2026-04-26
Versión: 1.0
"""

import os
import sys
import argparse
import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any
from uuid import uuid4

# Agregar path del backend
sys.path.insert(0, '/app/backend')

# Cargar variables de entorno
from dotenv import load_dotenv
load_dotenv('/app/backend/.env')

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s][%(levelname)s][FINANZAS_HISTORICAL] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# ============================================================================
# CONSTANTES
# ============================================================================

DEFAULT_BATCH_DAYS = 30  # Finanzas puede usar batches más grandes
DEFAULT_TIMEOUT = 120
DEFAULT_SLEEP_SECONDS = 2
MONTHS_HISTORICAL = 24

COLLECTION_CHECKPOINTS = "finanzas_historical_load_checkpoints"

# Estados de checkpoint
STATUS_PENDING = "PENDING"
STATUS_RUNNING = "RUNNING"
STATUS_PARTIAL = "PARTIAL"
STATUS_SUCCESS = "SUCCESS"
STATUS_FAILED = "FAILED"

# Tipos de KPI
KPI_CORTE_Z = "CORTE_Z"
KPI_CXP = "CXP"


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

async def get_or_create_checkpoint(
    db,
    server_id: str,
    server_name: str,
    run_id: str,
    kpi_tipo: str
) -> Dict:
    """Obtiene o crea checkpoint para un servidor y tipo de KPI."""
    checkpoint = await db[COLLECTION_CHECKPOINTS].find_one({
        "server_id": server_id,
        "kpi_tipo": kpi_tipo,
        "status": {"$in": [STATUS_PENDING, STATUS_RUNNING, STATUS_PARTIAL]}
    })
    
    if checkpoint:
        logger.info(f"[CHECKPOINT_FOUND] {server_name}/{kpi_tipo} - Reanudando desde {checkpoint.get('last_date_processed')}")
        return checkpoint
    
    # Crear nuevo checkpoint
    new_checkpoint = {
        "run_id": run_id,
        "server_id": server_id,
        "server_name": server_name,
        "kpi_tipo": kpi_tipo,
        "status": STATUS_PENDING,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "last_date_processed": None,
        "total_inserted": 0,
        "total_updated": 0,
        "total_errors": 0,
        "batches_completed": 0
    }
    
    await db[COLLECTION_CHECKPOINTS].insert_one(new_checkpoint)
    logger.info(f"[CHECKPOINT_CREATED] {server_name}/{kpi_tipo}")
    return new_checkpoint


async def update_checkpoint(
    db,
    server_id: str,
    kpi_tipo: str,
    updates: Dict
):
    """Actualiza checkpoint con progreso."""
    updates["updated_at"] = datetime.now(timezone.utc).isoformat()
    await db[COLLECTION_CHECKPOINTS].update_one(
        {"server_id": server_id, "kpi_tipo": kpi_tipo, "status": {"$ne": STATUS_SUCCESS}},
        {"$set": updates}
    )


# ============================================================================
# CONSULTAS DE DATOS FINANCIEROS
# ============================================================================

def parse_server_host(server: Dict) -> tuple:
    """
    Parsea hosts complejos con formatos como:
    - hostname
    - hostname,port
    - hostname\\instance
    - hostname,port\\instance
    
    Returns: (host, port)
    """
    host_str = server.get("host", "")
    port = server.get("port", 1433)
    
    if ',' in host_str:
        # Format: hostname,port or hostname,port\\instance
        parts = host_str.split(',')
        host = parts[0]
        rest = parts[1]
        if '\\' in rest:
            port_part = rest.split('\\')[0]
            port = int(port_part)
        else:
            port = int(rest)
    elif '\\' in host_str:
        host = host_str.split('\\')[0]
    else:
        host = host_str
    
    return host, port


def query_cortes_z_softrestaurant(
    server: Dict,
    fecha_inicio: str,
    fecha_fin: str
) -> List[Dict]:
    """
    Consulta Cortes Z de servidor SoftRestaurant.
    Retorna lista de cortes con ventas por forma de pago.
    """
    import pytds
    
    host, port = parse_server_host(server)
    database = server.get("database")
    username = server.get("username")
    password = server.get("password")
    
    # Query para obtener ventas totales de cheques (sin desglose por forma de pago)
    # SoftRestaurant no siempre tiene la tabla formaspago disponible
    query = f"""
    SELECT 
        CONVERT(DATE, c.fecha) as fecha,
        0 as ventas_efectivo,
        0 as ventas_debito,
        0 as ventas_credito,
        0 as ventas_amex,
        0 as ventas_otros,
        SUM(c.total) as ventas_total,
        SUM(ISNULL(c.propina, 0)) as propinas
    FROM cheques c
    WHERE CONVERT(DATE, c.fecha) BETWEEN '{fecha_inicio}' AND '{fecha_fin}'
      AND c.cancelado = 0
    GROUP BY CONVERT(DATE, c.fecha)
    ORDER BY fecha
    """
    
    results = []
    
    try:
        with pytds.connect(
            server=host,
            port=port,
            database=database,
            user=username,
            password=password,
            timeout=DEFAULT_TIMEOUT
        ) as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            
            for row in cursor.fetchall():
                results.append({
                    "fecha": str(row[0]),
                    "ventas_efectivo": float(row[1] or 0),
                    "ventas_tarjeta_debito": float(row[2] or 0),
                    "ventas_tarjeta_credito": float(row[3] or 0),
                    "ventas_tarjeta_amex": float(row[4] or 0),
                    "ventas_otros": float(row[5] or 0),
                    "ventas_total": float(row[6] or 0),
                    "propinas": float(row[7] or 0)
                })
            
            cursor.close()
            
    except Exception as e:
        logger.error(f"[QUERY_CORTES_Z_ERROR] {server.get('name')}: {e}")
    
    return results


def query_cortes_z_mpro(
    server: Dict,
    fecha_inicio: str,
    fecha_fin: str
) -> List[Dict]:
    """
    Consulta ventas totales de servidor ManagementPro.
    MPRO usa Venta_Encabezado en lugar de tablas de Cortes Z.
    """
    import pytds
    
    host = server.get("host")
    port = server.get("port", 1433)
    database = server.get("database")
    username = server.get("username")
    password = server.get("password")
    
    # Query MPRO para ventas totales por fecha
    # Nota: MPRO no tiene desglose por forma de pago en Venta_Encabezado
    # Los estados válidos son: FA (Facturado), AC (Activo)
    query = f"""
    SELECT 
        CONVERT(DATE, Vn_Fecha) as fecha,
        SUM(ISNULL(Vn_Precio_Neto_Importe, 0)) as ventas_total,
        COUNT(*) as num_transacciones
    FROM Venta_Encabezado
    WHERE CONVERT(DATE, Vn_Fecha) BETWEEN '{fecha_inicio}' AND '{fecha_fin}'
      AND Es_Cve_Estado IN ('FA', 'AC')
    GROUP BY CONVERT(DATE, Vn_Fecha)
    ORDER BY fecha
    """
    
    results = []
    
    try:
        with pytds.connect(
            server=host,
            port=port,
            database=database,
            user=username,
            password=password,
            timeout=DEFAULT_TIMEOUT
        ) as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            
            for row in cursor.fetchall():
                results.append({
                    "fecha": str(row[0]),
                    "ventas_efectivo": 0,  # MPRO no tiene desglose
                    "ventas_tarjeta_debito": 0,
                    "ventas_tarjeta_credito": 0,
                    "ventas_tarjeta_amex": 0,
                    "ventas_otros": 0,
                    "ventas_total": float(row[1] or 0),
                    "propinas": 0,
                    "num_transacciones": int(row[2] or 0)
                })
            
            cursor.close()
            
    except Exception as e:
        logger.error(f"[QUERY_CORTES_Z_MPRO_ERROR] {server.get('name')}: {e}")
    
    return results


def query_cxp_softrestaurant(
    server: Dict,
    fecha_inicio: str,
    fecha_fin: str
) -> List[Dict]:
    """
    Consulta Cuentas por Pagar de servidor SoftRestaurant.
    
    CxP = Compras - Pagos (compras.total - SUM(pagosproveedores.abono))
    
    Retorna el saldo pendiente de CxP agrupado por fecha de la compra.
    """
    import pytds
    
    host, port = parse_server_host(server)
    database = server.get("database")
    username = server.get("username")
    password = server.get("password")
    
    # Query: CxP = Compras - Pagos, usando LEFT JOIN para evitar subconsultas en agregados
    query = f"""
    SELECT 
        CONVERT(DATE, c.fechaaplicacion) as fecha,
        COUNT(DISTINCT c.idcompra) as facturas_count,
        SUM(c.total) as monto_compras,
        SUM(ISNULL(p.total_pagos, 0)) as monto_pagos,
        SUM(c.total) - SUM(ISNULL(p.total_pagos, 0)) as saldo_cxp
    FROM compras c
    LEFT JOIN (
        SELECT foliocompra, SUM(abono) as total_pagos
        FROM pagosproveedores
        GROUP BY foliocompra
    ) p ON p.foliocompra = c.idcompra
    WHERE CONVERT(DATE, c.fechaaplicacion) BETWEEN '{fecha_inicio}' AND '{fecha_fin}'
      AND (c.cancelado IS NULL OR c.cancelado = 0)
    GROUP BY CONVERT(DATE, c.fechaaplicacion)
    ORDER BY fecha
    """
    
    results = []
    
    try:
        with pytds.connect(
            server=host,
            port=port,
            database=database,
            user=username,
            password=password,
            timeout=DEFAULT_TIMEOUT
        ) as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            
            for row in cursor.fetchall():
                results.append({
                    "fecha": str(row[0]),
                    "cxp_facturas_count": int(row[1] or 0),
                    "cxp_monto_total": float(row[2] or 0),  # Total compras
                    "cxp_monto_pagos": float(row[3] or 0),  # Total pagos
                    "cxp_monto_alimentos": 0,
                    "cxp_monto_bebidas": 0,
                    "cxp_monto_otros": float(row[2] or 0),
                    "cxp_saldo_pendiente": float(row[4] or 0)  # Saldo = Compras - Pagos
                })
            
            cursor.close()
            logger.info(f"[CXP_SR] {server.get('name')}: {len(results)} registros extraídos")
            
    except Exception as e:
        logger.error(f"[QUERY_CXP_ERROR] {server.get('name')}: {e}")
    
    return results


def query_cxp_mpro(
    server: Dict,
    fecha_inicio: str,
    fecha_fin: str
) -> List[Dict]:
    """
    Consulta Cuentas por Pagar de servidor ManagementPro.
    Usa la tabla Cuenta_X_Pagar con estado 'AC' (Activo).
    """
    import pytds
    
    host = server.get("host")
    port = server.get("port", 1433)
    database = server.get("database")
    username = server.get("username")
    password = server.get("password")
    
    # Query para CxP agrupado por fecha
    query = f"""
    SELECT 
        CONVERT(DATE, Cxp_Fecha) as fecha,
        COUNT(*) as facturas_count,
        SUM(Cxp_Precio_Neto_Importe) as monto_total,
        SUM(Cxp_Precio_Neto_Saldo) as saldo_pendiente
    FROM Cuenta_X_Pagar
    WHERE CONVERT(DATE, Cxp_Fecha) BETWEEN '{fecha_inicio}' AND '{fecha_fin}'
      AND Es_Cve_Estado = 'AC'
    GROUP BY CONVERT(DATE, Cxp_Fecha)
    ORDER BY fecha
    """
    
    results = []
    
    try:
        with pytds.connect(
            server=host,
            port=port,
            database=database,
            user=username,
            password=password,
            timeout=DEFAULT_TIMEOUT
        ) as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            
            for row in cursor.fetchall():
                results.append({
                    "fecha": str(row[0]),
                    "cxp_facturas_count": int(row[1] or 0),
                    "cxp_monto_total": float(row[2] or 0),
                    "cxp_monto_alimentos": 0,  # MPRO no tiene desglose por tipo
                    "cxp_monto_bebidas": 0,
                    "cxp_monto_otros": float(row[2] or 0),  # Todo como "otros"
                    "cxp_saldo_pendiente": float(row[3] or 0)
                })
            
            cursor.close()
            
    except Exception as e:
        logger.error(f"[QUERY_CXP_MPRO_ERROR] {server.get('name')}: {e}")
    
    return results


# ============================================================================
# LÓGICA DE CARGA HISTÓRICA
# ============================================================================

async def process_server_historical(
    db,
    server: Dict,
    run_id: str,
    kpi_tipo: str,
    start_date: datetime,
    end_date: datetime,
    dry_run: bool = False,
    batch_days: int = DEFAULT_BATCH_DAYS
) -> Dict:
    """
    Procesa carga histórica de un servidor para un tipo de KPI.
    """
    from modules.finanzas.historical_kpis_repository import upsert_finanzas_kpi_historico
    from core.system_type_utils import normalize_system_type, is_softrestaurant_system, is_mpro_system
    
    server_id = server.get("id")
    server_name = server.get("name")
    system_type = normalize_system_type(server.get("system_type", ""))
    
    # Obtener o crear checkpoint
    checkpoint = await get_or_create_checkpoint(db, server_id, server_name, run_id, kpi_tipo)
    
    # Determinar fecha de inicio desde checkpoint
    if checkpoint.get("last_date_processed"):
        current_date = datetime.strptime(checkpoint["last_date_processed"], '%Y-%m-%d') + timedelta(days=1)
    else:
        current_date = start_date
    
    counters = {
        "inserted": 0,
        "updated": 0,
        "errors": 0,
        "days_processed": 0
    }
    
    # Actualizar status a RUNNING
    await update_checkpoint(db, server_id, kpi_tipo, {"status": STATUS_RUNNING})
    
    # Procesar en batches
    while current_date <= end_date:
        batch_end = min(current_date + timedelta(days=batch_days - 1), end_date)
        fecha_inicio = current_date.strftime('%Y-%m-%d')
        fecha_fin = batch_end.strftime('%Y-%m-%d')
        
        logger.info(f"[BATCH] {server_name}/{kpi_tipo}: {fecha_inicio} -> {fecha_fin}")
        
        # Consultar datos según tipo
        if kpi_tipo == KPI_CORTE_Z:
            if is_softrestaurant_system(system_type):
                data = query_cortes_z_softrestaurant(server, fecha_inicio, fecha_fin)
            elif is_mpro_system(system_type):
                data = query_cortes_z_mpro(server, fecha_inicio, fecha_fin)
            else:
                data = []
        elif kpi_tipo == KPI_CXP:
            if is_softrestaurant_system(system_type):
                data = query_cxp_softrestaurant(server, fecha_inicio, fecha_fin)
            elif is_mpro_system(system_type):
                data = query_cxp_mpro(server, fecha_inicio, fecha_fin)
            else:
                data = []
        else:
            data = []
        
        logger.info(f"[QUERY_RESULT] {server_name}/{kpi_tipo}: {len(data)} registros")
        
        # Procesar e insertar
        for record in data:
            if dry_run:
                counters["inserted"] += 1
                continue
            
            result = upsert_finanzas_kpi_historico(
                run_id=run_id,
                server_id=server_id,
                sucursal_id=server.get("sucursal_id", server_id),
                system_type=system_type,
                fecha=record["fecha"],
                kpi_tipo=kpi_tipo,
                kpi_data=record,
                empresa_id=server.get("empresa_id", ""),
                empresa_nombre=server.get("empresa_nombre", server_name)
            )
            
            if result["status"] == "inserted":
                counters["inserted"] += 1
            elif result["status"] == "updated":
                counters["updated"] += 1
            else:
                counters["errors"] += 1
        
        counters["days_processed"] += (batch_end - current_date).days + 1
        
        # Actualizar checkpoint
        await update_checkpoint(db, server_id, kpi_tipo, {
            "last_date_processed": fecha_fin,
            "total_inserted": checkpoint.get("total_inserted", 0) + counters["inserted"],
            "total_updated": checkpoint.get("total_updated", 0) + counters["updated"],
            "total_errors": checkpoint.get("total_errors", 0) + counters["errors"],
            "batches_completed": checkpoint.get("batches_completed", 0) + 1
        })
        
        current_date = batch_end + timedelta(days=1)
        
        # Sleep entre batches
        if not dry_run:
            await asyncio.sleep(DEFAULT_SLEEP_SECONDS)
    
    # Marcar como completado
    final_status = STATUS_SUCCESS if counters["errors"] == 0 else STATUS_PARTIAL
    await update_checkpoint(db, server_id, kpi_tipo, {"status": final_status})
    
    return counters


async def get_servers_for_finanzas(db, exclude_tablajeria: bool = True) -> List[Dict]:
    """
    Obtiene servidores candidatos para carga histórica de finanzas.
    Excluye por defecto:
    - Servidores TABLAJERIA
    - HR2020 ESCRITURA (servidor de escritura interno)
    - PRUEBAS SOFTRESTAURANT (servidor de pruebas)
    """
    from core.system_type_utils import normalize_system_type
    from core.secret_manager import is_encrypted_secret, decrypt_secret
    
    # Servidores excluidos por regla de negocio
    EXCLUDED_SERVERS = ["TABLAJERIA", "HR2020", "PRUEBAS"]
    
    servers = []
    cursor = db.servers.find({"active": True}, {"_id": 0})
    
    async for server in cursor:
        server_name = server.get("name", "").upper()
        
        # Excluir servidores según regla de negocio
        excluded = False
        for pattern in EXCLUDED_SERVERS:
            if pattern in server_name:
                logger.info(f"[SKIP] Excluyendo servidor: {server.get('name')} (patrón: {pattern})")
                excluded = True
                break
        
        if excluded:
            continue
        
        system_type = server.get("system_type", "")
        normalized = normalize_system_type(system_type)
        
        # Solo SOFTRESTAURANT y MANAGEMENTPRO
        if normalized in ["SOFTRESTAURANT", "MANAGEMENTPRO"]:
            server["system_type_normalized"] = normalized
            
            # Descifrar password
            password = server.get("password", "")
            if password and is_encrypted_secret(password):
                try:
                    server["password"] = decrypt_secret(password)
                except Exception:
                    pass
            
            servers.append(server)
    
    return servers


# ============================================================================
# MAIN
# ============================================================================

async def main():
    parser = argparse.ArgumentParser(description='Carga Histórica de Finanzas')
    parser.add_argument('--dry-run', action='store_true', help='Simulación sin escritura')
    parser.add_argument('--run', action='store_true', help='Ejecutar carga real')
    parser.add_argument('--safe-mode', action='store_true', help='Solo 1 servidor, 1 batch')
    parser.add_argument('--server', type=str, help='ID de servidor específico')
    parser.add_argument('--kpi-tipo', type=str, choices=['CORTE_Z', 'CXP', 'ALL'], default='ALL')
    parser.add_argument('--months', type=int, default=MONTHS_HISTORICAL)
    
    args = parser.parse_args()
    
    if not args.dry_run and not args.run:
        parser.print_help()
        return
    
    # Verificar confirmación para ejecución real
    if args.run and os.environ.get('HISTORICAL_LOAD_CONFIRM') != 'YES':
        logger.error("Ejecución real requiere HISTORICAL_LOAD_CONFIRM=YES")
        return
    
    # Inicializar
    run_id = str(uuid4())
    db = await get_database()
    
    logger.info("=" * 60)
    logger.info("CARGA HISTÓRICA FINANZAS - INICIO")
    logger.info(f"Run ID: {run_id}")
    logger.info(f"Modo: {'DRY-RUN' if args.dry_run else 'EJECUCIÓN REAL'}")
    logger.info(f"Meses: {args.months}")
    logger.info("=" * 60)
    
    # Verificar/crear tabla SQL
    from modules.finanzas.historical_kpis_repository import check_table_exists, create_table_if_not_exists
    
    if not check_table_exists():
        logger.info("[MIGRATION] Creando tabla Finanzas_KPIs_Historico...")
        result = create_table_if_not_exists()
        logger.info(f"[MIGRATION] {result}")
    
    # Calcular rango de fechas
    end_date = datetime.now()
    start_date = end_date - timedelta(days=args.months * 30)
    
    # Obtener servidores
    servers = await get_servers_for_finanzas(db)
    logger.info(f"[SERVERS] Encontrados: {len(servers)}")
    
    if args.server:
        servers = [s for s in servers if s.get("id") == args.server]
    
    if args.safe_mode:
        servers = servers[:1]
        logger.info("[SAFE-MODE] Limitando a 1 servidor")
    
    # Determinar tipos de KPI a procesar
    kpi_tipos = [KPI_CORTE_Z, KPI_CXP] if args.kpi_tipo == 'ALL' else [args.kpi_tipo]
    
    # Procesar servidores
    total_results = {
        "servers_processed": 0,
        "total_inserted": 0,
        "total_updated": 0,
        "total_errors": 0
    }
    
    for server in servers:
        server_name = server.get("name", server.get("id"))
        logger.info(f"\n[SERVER] Procesando: {server_name}")
        
        for kpi_tipo in kpi_tipos:
            try:
                result = await process_server_historical(
                    db=db,
                    server=server,
                    run_id=run_id,
                    kpi_tipo=kpi_tipo,
                    start_date=start_date,
                    end_date=end_date,
                    dry_run=args.dry_run,
                    batch_days=7 if args.safe_mode else DEFAULT_BATCH_DAYS
                )
                
                total_results["total_inserted"] += result["inserted"]
                total_results["total_updated"] += result["updated"]
                total_results["total_errors"] += result["errors"]
                
                logger.info(f"[RESULT] {server_name}/{kpi_tipo}: +{result['inserted']} inserted, ~{result['updated']} updated, {result['errors']} errors")
                
            except Exception as e:
                logger.error(f"[SERVER_ERROR] {server_name}/{kpi_tipo}: {e}")
                total_results["total_errors"] += 1
        
        total_results["servers_processed"] += 1
    
    # Resumen final
    logger.info("\n" + "=" * 60)
    logger.info("CARGA HISTÓRICA FINANZAS - RESUMEN")
    logger.info("=" * 60)
    logger.info(f"Servidores procesados: {total_results['servers_processed']}")
    logger.info(f"Total insertados: {total_results['total_inserted']}")
    logger.info(f"Total actualizados: {total_results['total_updated']}")
    logger.info(f"Total errores: {total_results['total_errors']}")
    
    # Guardar reporte
    report = {
        "run_id": run_id,
        "phase": "FINANZAS_HISTORICAL_LOAD",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "mode": "DRY_RUN" if args.dry_run else "EXECUTION",
        "results": total_results
    }
    
    report_path = f"/app/docs/reports/finanzas_historical_load_{run_id[:8]}.json"
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    
    import json
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Reporte guardado: {report_path}")


if __name__ == "__main__":
    asyncio.run(main())
