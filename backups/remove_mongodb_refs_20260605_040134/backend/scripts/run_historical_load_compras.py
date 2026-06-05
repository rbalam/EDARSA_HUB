#!/usr/bin/env python3
"""
EDARSA HUB - Carga Histórica de Compras (24 Meses)
==================================================

Script para ejecutar carga histórica de KPIs de Compras:
- Inventarios Físicos
- Pedidos/Requisiciones
- Órdenes de Compra
- Entradas de Compra (Facturas Proveedor)

Fuentes:
- SOFTRESTAURANT: Inventarios, Pedidos
- MANAGEMENTPRO: Inventarios, Pedidos, Facturas Proveedor

Uso:
    # Dry-run (simulación)
    python run_historical_load_compras.py --dry-run

    # Ejecución real
    HISTORICAL_LOAD_CONFIRM=YES python run_historical_load_compras.py --run

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
    format='[%(asctime)s][%(levelname)s][COMPRAS_HISTORICAL] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# ============================================================================
# CONSTANTES
# ============================================================================

DEFAULT_BATCH_DAYS = 30
DEFAULT_TIMEOUT = 120
DEFAULT_SLEEP_SECONDS = 2
MONTHS_HISTORICAL = 24

COLLECTION_CHECKPOINTS = "compras_historical_load_checkpoints"

# Estados de checkpoint
STATUS_PENDING = "PENDING"
STATUS_RUNNING = "RUNNING"
STATUS_PARTIAL = "PARTIAL"
STATUS_SUCCESS = "SUCCESS"
STATUS_FAILED = "FAILED"

# Tipos de KPI
KPI_INVENTARIO = "INVENTARIO_FISICO"
KPI_PEDIDO = "PEDIDO"
KPI_ORDEN_COMPRA = "ORDEN_COMPRA"
KPI_ENTRADA = "ENTRADA_COMPRA"

# Servidores excluidos por regla de negocio
EXCLUDED_PATTERNS = ["TABLAJERIA", "HR2020", "PRUEBAS"]


def parse_server_host(host_str: str, default_port: int = 1433) -> tuple:
    """
    Parsea host complejo de SQL Server.
    Formatos soportados:
    - host
    - host,puerto
    - host,puerto\\instancia (ignora instancia, pytds no la soporta con puerto)
    
    Returns: (host, port)
    """
    if ',' in host_str:
        parts = host_str.split(',')
        server_host = parts[0]
        rest = parts[1]
        if '\\' in rest:
            port_str = rest.split('\\')[0]
            port = int(port_str)
        else:
            port = int(rest)
    else:
        server_host = host_str
        port = default_port
    return server_host, port


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


async def update_checkpoint(db, server_id: str, kpi_tipo: str, updates: Dict):
    """Actualiza checkpoint con progreso."""
    updates["updated_at"] = datetime.now(timezone.utc).isoformat()
    await db[COLLECTION_CHECKPOINTS].update_one(
        {"server_id": server_id, "kpi_tipo": kpi_tipo, "status": {"$ne": STATUS_SUCCESS}},
        {"$set": updates}
    )


# ============================================================================
# QUERIES - INVENTARIOS FÍSICOS
# ============================================================================

def query_inventarios_historico_mpro(server: Dict, fecha_inicio: str, fecha_fin: str) -> List[Dict]:
    """Consulta inventarios físicos históricos de MPRO (PDA_Inventario)."""
    import pytds
    
    # MPRO usa PDA_Inventario para conteos de inventario
    query = f"""
    IF EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'PDA_Inventario')
    BEGIN
        SELECT 
            CONVERT(DATE, I.Pi_Fecha) as fecha,
            COUNT(DISTINCT I.Pi_Folio) as conteos_count,
            SUM(ISNULL(d.productos_count, 0)) as productos_count,
            '' as almacenes
        FROM PDA_Inventario I
        LEFT JOIN (
            SELECT Pi_Folio, COUNT(*) as productos_count
            FROM PDA_Inventario_Detalle
            GROUP BY Pi_Folio
        ) d ON d.Pi_Folio = I.Pi_Folio
        WHERE CONVERT(DATE, I.Pi_Fecha) BETWEEN '{fecha_inicio}' AND '{fecha_fin}'
        GROUP BY CONVERT(DATE, I.Pi_Fecha)
        ORDER BY fecha
    END
    """
    
    results = []
    try:
        with pytds.connect(
            server=server.get('host'),
            port=server.get('port', 1433),
            database=server.get('database'),
            user=server.get('username'),
            password=server.get('password'),
            timeout=DEFAULT_TIMEOUT
        ) as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            for row in cursor.fetchall():
                if row[0]:  # Solo si hay fecha
                    results.append({
                        "fecha": str(row[0]),
                        "inv_conteos_count": int(row[1] or 0),
                        "inv_productos_count": int(row[2] or 0),
                        "inv_almacenes": str(row[3] or '')[:500]
                    })
            cursor.close()
    except Exception as e:
        logger.error(f"[INV_MPRO_ERROR] {server.get('name')}: {e}")
    
    return results


def query_inventarios_historico_sr(server: Dict, fecha_inicio: str, fecha_fin: str) -> List[Dict]:
    """Consulta inventarios físicos históricos de SoftRestaurant (folioconteo)."""
    import pytds
    
    host, port = parse_server_host(server.get('host'), server.get('port', 1433))
    
    # Query basada en el repository existente de compras
    query = f"""
    SELECT 
        CONVERT(DATE, F.fecha) as fecha,
        COUNT(DISTINCT F.idfolioconteo) as conteos_count,
        SUM(ISNULL(d.productos_count, 0)) as productos_count,
        '' as almacenes
    FROM folioconteo F
    LEFT JOIN (
        SELECT idfolioconteo, COUNT(*) as productos_count
        FROM detalleconteo
        GROUP BY idfolioconteo
    ) d ON d.idfolioconteo = F.idfolioconteo
    WHERE CONVERT(DATE, F.fecha) BETWEEN '{fecha_inicio}' AND '{fecha_fin}'
    GROUP BY CONVERT(DATE, F.fecha)
    ORDER BY fecha
    """
    
    results = []
    try:
        with pytds.connect(
            server=host,
            port=port,
            database=server.get('database'),
            user=server.get('username'),
            password=server.get('password'),
            timeout=DEFAULT_TIMEOUT
        ) as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            for row in cursor.fetchall():
                if row[0]:  # Solo si hay fecha
                    results.append({
                        "fecha": str(row[0]),
                        "inv_conteos_count": int(row[1] or 0),
                        "inv_productos_count": int(row[2] or 0),
                        "inv_almacenes": str(row[3] or '')
                    })
            cursor.close()
            if results:
                logger.info(f"[INV_SR] {server.get('name')}: {len(results)} registros")
    except Exception as e:
        if "folioconteo" not in str(e).lower() and "invalid object" not in str(e).lower():
            logger.error(f"[INV_SR_ERROR] {server.get('name')}: {e}")
    
    return results


# ============================================================================
# QUERIES - PEDIDOS
# ============================================================================

def query_pedidos_historico_mpro(server: Dict, fecha_inicio: str, fecha_fin: str) -> List[Dict]:
    """Consulta requisiciones de compra históricos de MPRO (Requisicion_Compra)."""
    import pytds
    
    # MPRO usa Requisicion_Compra para pedidos internos
    query = f"""
    SELECT 
        CONVERT(DATE, R.Rc_Fecha) as fecha,
        COUNT(DISTINCT R.Rc_Folio) as pedidos_count,
        0 as total_monto,
        COUNT(*) as productos_count
    FROM Requisicion_Compra R
    WHERE CONVERT(DATE, R.Rc_Fecha) BETWEEN '{fecha_inicio}' AND '{fecha_fin}'
    GROUP BY CONVERT(DATE, R.Rc_Fecha)
    ORDER BY fecha
    """
    
    results = []
    try:
        with pytds.connect(
            server=server.get('host'),
            port=server.get('port', 1433),
            database=server.get('database'),
            user=server.get('username'),
            password=server.get('password'),
            timeout=DEFAULT_TIMEOUT
        ) as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            for row in cursor.fetchall():
                results.append({
                    "fecha": str(row[0]),
                    "ped_pedidos_count": int(row[1] or 0),
                    "ped_total_monto": float(row[2] or 0),
                    "ped_productos_count": int(row[3] or 0)
                })
            cursor.close()
    except Exception as e:
        logger.error(f"[PED_MPRO_ERROR] {server.get('name')}: {e}")
    
    return results


def query_pedidos_historico_sr(server: Dict, fecha_inicio: str, fecha_fin: str) -> List[Dict]:
    """Consulta pedidos históricos de SoftRestaurant (tabla: pedidos)."""
    import pytds
    
    host, port = parse_server_host(server.get('host'), server.get('port', 1433))
    
    # SoftRestaurant usa tabla 'pedidos' con columna 'fechacaptura'
    query = f"""
    SELECT 
        CONVERT(DATE, P.fechacaptura) as fecha,
        COUNT(DISTINCT P.idpedido) as pedidos_count,
        SUM(ISNULL(P.total, 0)) as total_monto,
        0 as productos_count
    FROM pedidos P
    WHERE CONVERT(DATE, P.fechacaptura) BETWEEN '{fecha_inicio}' AND '{fecha_fin}'
      AND (P.cancelado IS NULL OR P.cancelado = 0)
    GROUP BY CONVERT(DATE, P.fechacaptura)
    ORDER BY fecha
    """
    
    results = []
    try:
        with pytds.connect(
            server=host,
            port=port,
            database=server.get('database'),
            user=server.get('username'),
            password=server.get('password'),
            timeout=DEFAULT_TIMEOUT
        ) as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            for row in cursor.fetchall():
                if row[0]:  # Solo si hay fecha
                    results.append({
                        "fecha": str(row[0]),
                        "ped_pedidos_count": int(row[1] or 0),
                        "ped_total_monto": float(row[2] or 0),
                        "ped_productos_count": int(row[3] or 0)
                    })
            cursor.close()
            if results:
                logger.info(f"[PED_SR] {server.get('name')}: {len(results)} registros")
    except Exception as e:
        logger.error(f"[PED_SR_ERROR] {server.get('name')}: {e}")
    
    return results


# ============================================================================
# QUERIES - ENTRADAS DE COMPRA (FACTURAS PROVEEDOR)
# ============================================================================

def query_entradas_historico_mpro(server: Dict, fecha_inicio: str, fecha_fin: str) -> List[Dict]:
    """Consulta compras/entradas históricas de MPRO (Compra_Encabezado)."""
    import pytds
    
    # MPRO usa Compra_Encabezado para entradas de compra
    query = f"""
    SELECT 
        CONVERT(DATE, C.Co_Fecha) as fecha,
        COUNT(DISTINCT C.Co_Folio) as entradas_count,
        SUM(ISNULL(I.total_impuesto, 0)) as total_monto,
        0 as productos_count
    FROM Compra_Encabezado C
    LEFT JOIN (
        SELECT Co_Folio, SUM(Im_Importe) as total_impuesto
        FROM Compra_Impuesto
        GROUP BY Co_Folio
    ) I ON I.Co_Folio = C.Co_Folio
    WHERE CONVERT(DATE, C.Co_Fecha) BETWEEN '{fecha_inicio}' AND '{fecha_fin}'
    GROUP BY CONVERT(DATE, C.Co_Fecha)
    ORDER BY fecha
    """
    
    results = []
    try:
        with pytds.connect(
            server=server.get('host'),
            port=server.get('port', 1433),
            database=server.get('database'),
            user=server.get('username'),
            password=server.get('password'),
            timeout=DEFAULT_TIMEOUT
        ) as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            for row in cursor.fetchall():
                results.append({
                    "fecha": str(row[0]),
                    "ec_entradas_count": int(row[1] or 0),
                    "ec_total_monto": float(row[2] or 0),
                    "ec_productos_count": int(row[3] or 0)
                })
            cursor.close()
    except Exception as e:
        logger.error(f"[ENT_MPRO_ERROR] {server.get('name')}: {e}")
    
    return results


def query_entradas_historico_sr(server: Dict, fecha_inicio: str, fecha_fin: str) -> List[Dict]:
    """Consulta compras históricas de SoftRestaurant agrupados por fecha."""
    import pytds
    
    host, port = parse_server_host(server.get('host'), server.get('port', 1433))
    
    # Query simplificada - SoftRestaurant solo tiene tabla 'compras', no 'detallecompras'
    query = f"""
    SELECT 
        CONVERT(DATE, c.fechaaplicacion) as fecha,
        COUNT(DISTINCT c.idcompra) as entradas_count,
        SUM(ISNULL(c.total, 0)) as total_monto,
        0 as productos_count
    FROM compras c
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
            database=server.get('database'),
            user=server.get('username'),
            password=server.get('password'),
            timeout=DEFAULT_TIMEOUT
        ) as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            for row in cursor.fetchall():
                results.append({
                    "fecha": str(row[0]),
                    "ec_entradas_count": int(row[1] or 0),
                    "ec_total_monto": float(row[2] or 0),
                    "ec_productos_count": int(row[3] or 0)
                })
            cursor.close()
            if results:
                logger.info(f"[ENT_SR] {server.get('name')}: {len(results)} registros")
    except Exception as e:
        logger.error(f"[ENT_SR_ERROR] {server.get('name')}: {e}")
    
    return results


# ============================================================================
# QUERIES - ÓRDENES DE COMPRA
# ============================================================================

def query_ordenes_historico_mpro(server: Dict, fecha_inicio: str, fecha_fin: str) -> List[Dict]:
    """Consulta órdenes de compra históricas de MPRO (Orden_Compra)."""
    import pytds
    
    query = f"""
    SELECT 
        CONVERT(DATE, O.Oc_Fecha) as fecha,
        COUNT(DISTINCT O.Oc_Folio) as ordenes_count,
        0 as total_monto,
        COUNT(DISTINCT O.Pv_Cve_Proveedor) as proveedores_count
    FROM Orden_Compra O
    WHERE CONVERT(DATE, O.Oc_Fecha) BETWEEN '{fecha_inicio}' AND '{fecha_fin}'
    GROUP BY CONVERT(DATE, O.Oc_Fecha)
    ORDER BY fecha
    """
    
    results = []
    try:
        with pytds.connect(
            server=server.get('host'),
            port=server.get('port', 1433),
            database=server.get('database'),
            user=server.get('username'),
            password=server.get('password'),
            timeout=DEFAULT_TIMEOUT
        ) as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            for row in cursor.fetchall():
                results.append({
                    "fecha": str(row[0]),
                    "oc_ordenes_count": int(row[1] or 0),
                    "oc_total_monto": float(row[2] or 0),
                    "oc_proveedores_count": int(row[3] or 0)
                })
            cursor.close()
    except Exception as e:
        logger.error(f"[OC_MPRO_ERROR] {server.get('name')}: {e}")
    
    return results


def query_ordenes_historico_sr(server: Dict, fecha_inicio: str, fecha_fin: str) -> List[Dict]:
    """Consulta órdenes de compra históricas de SoftRestaurant (tabla: ordenescompra)."""
    import pytds
    
    host, port = parse_server_host(server.get('host'), server.get('port', 1433))
    
    # SoftRestaurant usa tabla 'ordenescompra' con columna 'fechacaptura'
    query = f"""
    SELECT 
        CONVERT(DATE, O.fechacaptura) as fecha,
        COUNT(DISTINCT O.idordencompra) as ordenes_count,
        SUM(ISNULL(O.total, 0)) as total_monto,
        COUNT(DISTINCT O.idproveedor) as proveedores_count
    FROM ordenescompra O
    WHERE CONVERT(DATE, O.fechacaptura) BETWEEN '{fecha_inicio}' AND '{fecha_fin}'
      AND (O.cancelado IS NULL OR O.cancelado = 0)
    GROUP BY CONVERT(DATE, O.fechacaptura)
    ORDER BY fecha
    """
    
    results = []
    try:
        with pytds.connect(
            server=host,
            port=port,
            database=server.get('database'),
            user=server.get('username'),
            password=server.get('password'),
            timeout=DEFAULT_TIMEOUT
        ) as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            for row in cursor.fetchall():
                if row[0]:  # Solo si hay fecha
                    results.append({
                        "fecha": str(row[0]),
                        "oc_ordenes_count": int(row[1] or 0),
                        "oc_total_monto": float(row[2] or 0),
                        "oc_proveedores_count": int(row[3] or 0)
                    })
            cursor.close()
            if results:
                logger.info(f"[OC_SR] {server.get('name')}: {len(results)} registros")
    except Exception as e:
        logger.error(f"[OC_SR_ERROR] {server.get('name')}: {e}")
    
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
    """Procesa carga histórica de un servidor para un tipo de KPI."""
    from modules.compras.historical_kpis_repository import upsert_compras_kpi_historico
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
    
    counters = {"inserted": 0, "updated": 0, "errors": 0, "days_processed": 0}
    
    # Actualizar status a RUNNING
    await update_checkpoint(db, server_id, kpi_tipo, {"status": STATUS_RUNNING})
    
    # Procesar en batches
    while current_date <= end_date:
        batch_end = min(current_date + timedelta(days=batch_days - 1), end_date)
        fecha_inicio = current_date.strftime('%Y-%m-%d')
        fecha_fin = batch_end.strftime('%Y-%m-%d')
        
        logger.info(f"[BATCH] {server_name}/{kpi_tipo}: {fecha_inicio} -> {fecha_fin}")
        
        # Consultar datos según tipo
        data = []
        if kpi_tipo == KPI_INVENTARIO:
            if is_mpro_system(system_type):
                data = query_inventarios_historico_mpro(server, fecha_inicio, fecha_fin)
            elif is_softrestaurant_system(system_type):
                data = query_inventarios_historico_sr(server, fecha_inicio, fecha_fin)
        elif kpi_tipo == KPI_PEDIDO:
            if is_mpro_system(system_type):
                data = query_pedidos_historico_mpro(server, fecha_inicio, fecha_fin)
            elif is_softrestaurant_system(system_type):
                data = query_pedidos_historico_sr(server, fecha_inicio, fecha_fin)
        elif kpi_tipo == KPI_ENTRADA:
            if is_mpro_system(system_type):
                data = query_entradas_historico_mpro(server, fecha_inicio, fecha_fin)
            elif is_softrestaurant_system(system_type):
                data = query_entradas_historico_sr(server, fecha_inicio, fecha_fin)
        elif kpi_tipo == KPI_ORDEN_COMPRA:
            if is_mpro_system(system_type):
                data = query_ordenes_historico_mpro(server, fecha_inicio, fecha_fin)
            elif is_softrestaurant_system(system_type):
                data = query_ordenes_historico_sr(server, fecha_inicio, fecha_fin)
        
        logger.info(f"[QUERY_RESULT] {server_name}/{kpi_tipo}: {len(data)} registros")
        
        # Procesar e insertar
        for record in data:
            if dry_run:
                counters["inserted"] += 1
                continue
            
            result = upsert_compras_kpi_historico(
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
        
        if not dry_run:
            await asyncio.sleep(DEFAULT_SLEEP_SECONDS)
    
    # Marcar como completado
    final_status = STATUS_SUCCESS if counters["errors"] == 0 else STATUS_PARTIAL
    await update_checkpoint(db, server_id, kpi_tipo, {"status": final_status})
    
    return counters


async def get_servers_for_compras(db) -> List[Dict]:
    """Obtiene servidores candidatos para carga histórica de compras."""
    from core.system_type_utils import normalize_system_type
    from core.secret_manager import is_encrypted_secret, decrypt_secret
    
    servers = []
    cursor = db.servers.find({"active": True}, {"_id": 0})
    
    async for server in cursor:
        server_name = server.get("name", "").upper()
        
        # Excluir servidores según regla de negocio
        excluded = False
        for pattern in EXCLUDED_PATTERNS:
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
    parser = argparse.ArgumentParser(description='Carga Histórica de Compras')
    parser.add_argument('--dry-run', action='store_true', help='Simulación sin escritura')
    parser.add_argument('--run', action='store_true', help='Ejecutar carga real')
    parser.add_argument('--safe-mode', action='store_true', help='Solo 1 servidor, 1 batch')
    parser.add_argument('--server', type=str, help='ID de servidor específico')
    parser.add_argument('--kpi-tipo', type=str, 
                       choices=['INVENTARIO_FISICO', 'PEDIDO', 'ORDEN_COMPRA', 'ENTRADA_COMPRA', 'ALL'], 
                       default='ALL')
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
    logger.info("CARGA HISTÓRICA COMPRAS - INICIO")
    logger.info(f"Run ID: {run_id}")
    logger.info(f"Modo: {'DRY-RUN' if args.dry_run else 'EJECUCIÓN REAL'}")
    logger.info(f"Meses: {args.months}")
    logger.info("=" * 60)
    
    # Verificar/crear tabla SQL
    from modules.compras.historical_kpis_repository import check_table_exists, create_table_if_not_exists
    
    if not check_table_exists():
        logger.info("[MIGRATION] Creando tabla Compras_KPIs_Historico...")
        result = create_table_if_not_exists()
        logger.info(f"[MIGRATION] {result}")
    
    # Calcular rango de fechas
    end_date = datetime.now()
    start_date = end_date - timedelta(days=args.months * 30)
    
    # Obtener servidores
    servers = await get_servers_for_compras(db)
    logger.info(f"[SERVERS] Encontrados: {len(servers)}")
    
    if args.server:
        servers = [s for s in servers if s.get("id") == args.server]
    
    if args.safe_mode:
        servers = servers[:1]
        logger.info("[SAFE-MODE] Limitando a 1 servidor")
    
    # Determinar tipos de KPI a procesar
    if args.kpi_tipo == 'ALL':
        kpi_tipos = [KPI_INVENTARIO, KPI_PEDIDO, KPI_ORDEN_COMPRA, KPI_ENTRADA]
    else:
        kpi_tipos = [args.kpi_tipo]
    
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
    logger.info("CARGA HISTÓRICA COMPRAS - RESUMEN")
    logger.info("=" * 60)
    logger.info(f"Servidores procesados: {total_results['servers_processed']}")
    logger.info(f"Total insertados: {total_results['total_inserted']}")
    logger.info(f"Total actualizados: {total_results['total_updated']}")
    logger.info(f"Total errores: {total_results['total_errors']}")
    
    # Guardar reporte
    report = {
        "run_id": run_id,
        "phase": "COMPRAS_HISTORICAL_LOAD",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "mode": "DRY_RUN" if args.dry_run else "EXECUTION",
        "results": total_results
    }
    
    report_path = f"/app/docs/reports/compras_historical_load_{run_id[:8]}.json"
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    
    import json
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Reporte guardado: {report_path}")


if __name__ == "__main__":
    asyncio.run(main())
