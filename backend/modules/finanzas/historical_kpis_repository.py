"""
EDARSA HUB - Finanzas Historical KPIs Repository
=================================================
Repositorio para UPSERT idempotente de KPIs históricos de Finanzas
en EDARSAHUB SQL Server.

Fecha: 2026-04-26
Tabla destino: Finanzas_KPIs_Historico
"""

import logging
import os
import sys
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone

sys.path.insert(0, '/app/backend')

logger = logging.getLogger(__name__)


def get_edarsahub_server():
    """Obtiene configuración del servidor EDARSAHUB desde MongoDB."""
    from dotenv import load_dotenv
    load_dotenv('/app/backend/.env')
    from pymongo import MongoClient
    
    client = MongoClient(os.environ['MONGO_URL'])
    db = client[os.environ['DB_NAME']]
    
    srv = db.servers.find_one({'name': 'EDARSA HUB', 'active': True})
    if not srv:
        raise ValueError("Servidor EDARSA HUB no encontrado en MongoDB")
    
    # Descifrar password si está cifrado
    password = srv.get('password', '')
    if password.startswith('enc:'):
        from core.secret_manager import decrypt_secret
        password = decrypt_secret(password)
    
    return {
        "host": srv.get("host"),
        "port": srv.get("port", 1433),
        "database": srv.get("database"),
        "username": srv.get("username"),
        "password": password,
    }


def get_edarsahub_connection():
    """Obtiene conexión a EDARSAHUB SQL Server."""
    import pytds
    config = get_edarsahub_server()
    return pytds.connect(
        server=config["host"],
        port=config["port"],
        database=config["database"],
        user=config["username"],
        password=config["password"],
        timeout=30
    )


def upsert_finanzas_kpi_historico(
    run_id: str,
    server_id: str,
    sucursal_id: str,
    system_type: str,
    fecha: str,
    kpi_tipo: str,
    kpi_data: Dict[str, Any],
    empresa_id: str = "",
    empresa_nombre: str = ""
) -> Dict[str, Any]:
    """
    Realiza UPSERT de un registro de KPI de Finanzas en SQL Server.
    Usa INSERT con manejo de duplicados mediante verificación previa.
    """
    
    try:
        conn = get_edarsahub_connection()
        cursor = conn.cursor()
        
        # Extraer valores con defaults
        ventas_efectivo = kpi_data.get("ventas_efectivo", 0)
        ventas_tarjeta_debito = kpi_data.get("ventas_tarjeta_debito", 0)
        ventas_tarjeta_credito = kpi_data.get("ventas_tarjeta_credito", 0)
        ventas_tarjeta_amex = kpi_data.get("ventas_tarjeta_amex", 0)
        ventas_otros = kpi_data.get("ventas_otros", 0)
        ventas_total = kpi_data.get("ventas_total", 0)
        propinas = kpi_data.get("propinas", 0)
        comision_debito = kpi_data.get("comision_debito", 0)
        comision_credito = kpi_data.get("comision_credito", 0)
        comision_amex = kpi_data.get("comision_amex", 0)
        comision_total = kpi_data.get("comision_total", 0)
        cxp_facturas_count = kpi_data.get("cxp_facturas_count", 0)
        cxp_monto_total = kpi_data.get("cxp_monto_total", 0)
        cxp_monto_alimentos = kpi_data.get("cxp_monto_alimentos", 0)
        cxp_monto_bebidas = kpi_data.get("cxp_monto_bebidas", 0)
        cxp_monto_otros = kpi_data.get("cxp_monto_otros", 0)
        cxp_saldo_pendiente = kpi_data.get("cxp_saldo_pendiente", 0)
        flujo_efectivo_neto = kpi_data.get("flujo_efectivo_neto", 0)
        
        # Verificar si existe
        check_sql = """
        SELECT id FROM Finanzas_KPIs_Historico 
        WHERE server_id = %s AND sucursal_id = %s AND system_type_normalized = %s 
        AND fecha = %s AND kpi_tipo = %s
        """
        cursor.execute(check_sql, (server_id, sucursal_id, system_type, fecha, kpi_tipo))
        existing = cursor.fetchone()
        
        if existing:
            # UPDATE
            update_sql = """
            UPDATE Finanzas_KPIs_Historico SET
                run_id = %s,
                ventas_efectivo = %s, ventas_tarjeta_debito = %s, ventas_tarjeta_credito = %s,
                ventas_tarjeta_amex = %s, ventas_otros = %s, ventas_total = %s, propinas = %s,
                comision_debito = %s, comision_credito = %s, comision_amex = %s, comision_total = %s,
                cxp_facturas_count = %s, cxp_monto_total = %s, cxp_monto_alimentos = %s,
                cxp_monto_bebidas = %s, cxp_monto_otros = %s, cxp_saldo_pendiente = %s,
                flujo_efectivo_neto = %s, empresa_id = %s, empresa_nombre = %s,
                fecha_actualizacion = GETDATE()
            WHERE id = %s
            """
            cursor.execute(update_sql, (
                run_id, ventas_efectivo, ventas_tarjeta_debito, ventas_tarjeta_credito,
                ventas_tarjeta_amex, ventas_otros, ventas_total, propinas,
                comision_debito, comision_credito, comision_amex, comision_total,
                cxp_facturas_count, cxp_monto_total, cxp_monto_alimentos,
                cxp_monto_bebidas, cxp_monto_otros, cxp_saldo_pendiente,
                flujo_efectivo_neto, empresa_id, empresa_nombre, existing[0]
            ))
            action = "updated"
        else:
            # INSERT
            insert_sql = """
            INSERT INTO Finanzas_KPIs_Historico (
                run_id, server_id, sucursal_id, system_type_normalized, fecha, kpi_tipo,
                ventas_efectivo, ventas_tarjeta_debito, ventas_tarjeta_credito,
                ventas_tarjeta_amex, ventas_otros, ventas_total, propinas,
                comision_debito, comision_credito, comision_amex, comision_total,
                cxp_facturas_count, cxp_monto_total, cxp_monto_alimentos,
                cxp_monto_bebidas, cxp_monto_otros, cxp_saldo_pendiente,
                flujo_efectivo_neto, empresa_id, empresa_nombre, origen
            ) VALUES (
                %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s,
                %s, %s, %s, 'HISTORICAL_LOAD'
            )
            """
            cursor.execute(insert_sql, (
                run_id, server_id, sucursal_id, system_type, fecha, kpi_tipo,
                ventas_efectivo, ventas_tarjeta_debito, ventas_tarjeta_credito,
                ventas_tarjeta_amex, ventas_otros, ventas_total, propinas,
                comision_debito, comision_credito, comision_amex, comision_total,
                cxp_facturas_count, cxp_monto_total, cxp_monto_alimentos,
                cxp_monto_bebidas, cxp_monto_otros, cxp_saldo_pendiente,
                flujo_efectivo_neto, empresa_id, empresa_nombre
            ))
            action = "inserted"
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return {"status": action, "message": f"KPI {kpi_tipo} {fecha} {action}"}
        
    except Exception as e:
        logger.error(f"[UPSERT_ERROR] server={server_id} fecha={fecha}: {e}")
        return {"status": "error", "message": str(e)}


def get_finanzas_historico_stats() -> Dict[str, Any]:
    """Obtiene estadísticas de la tabla Finanzas_KPIs_Historico."""
    try:
        conn = get_edarsahub_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                COUNT(*) as total_records,
                COUNT(DISTINCT server_id) as servers,
                COUNT(DISTINCT sucursal_id) as sucursales,
                MIN(fecha) as fecha_min,
                MAX(fecha) as fecha_max,
                SUM(CASE WHEN kpi_tipo = 'CORTE_Z' THEN 1 ELSE 0 END) as cortes_z_count,
                SUM(CASE WHEN kpi_tipo = 'CXP' THEN 1 ELSE 0 END) as cxp_count
            FROM Finanzas_KPIs_Historico
        """)
        
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if row:
            return {
                "total_records": row[0],
                "servers": row[1],
                "sucursales": row[2],
                "fecha_min": str(row[3]) if row[3] else None,
                "fecha_max": str(row[4]) if row[4] else None,
                "cortes_z_count": row[5],
                "cxp_count": row[6]
            }
        return {"total_records": 0}
        
    except Exception as e:
        logger.error(f"[STATS_ERROR] {e}")
        return {"error": str(e)}


def check_table_exists() -> bool:
    """Verifica si la tabla Finanzas_KPIs_Historico existe."""
    try:
        conn = get_edarsahub_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT COUNT(*) FROM sys.objects 
            WHERE object_id = OBJECT_ID(N'[dbo].[Finanzas_KPIs_Historico]') 
            AND type in (N'U')
        """)
        
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        
        return row[0] > 0 if row else False
        
    except Exception as e:
        logger.error(f"[CHECK_TABLE_ERROR] {e}")
        return False


def create_table_if_not_exists() -> Dict[str, Any]:
    """Crea la tabla si no existe (ejecuta migración)."""
    try:
        migration_path = "/app/backend/db/migrations/create_finanzas_kpis_historico.sql"
        
        with open(migration_path, 'r') as f:
            sql_script = f.read()
        
        conn = get_edarsahub_connection()
        cursor = conn.cursor()
        
        # Ejecutar cada batch separado por GO
        batches = sql_script.split('\nGO\n')
        for batch in batches:
            batch = batch.strip()
            if batch and not batch.startswith('--'):
                try:
                    cursor.execute(batch)
                except Exception as e:
                    logger.warning(f"[MIGRATION_BATCH_WARN] {e}")
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return {"status": "success", "message": "Tabla creada o ya existía"}
        
    except Exception as e:
        logger.error(f"[CREATE_TABLE_ERROR] {e}")
        return {"status": "error", "message": str(e)}
