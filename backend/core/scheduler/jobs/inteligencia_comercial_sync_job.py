"""
EDARSA HUB - Job: Sincronización Inteligencia Comercial
=======================================================
Extrae datos de ventas desde sistemas POS origen y los consolida en EDARSAHUB.

Sistemas origen:
- SoftRestaurant: 130MID, CIENFUEGOS, ESTELAR
- MPRO: 130QRO, ORIGEN

Tablas destino en EDARSAHUB:
- Sync_Sales (detalle de transacciones con items JSON)
- Comercial_KPIs_Diarios_v2 (KPIs consolidados por día)
"""

import logging
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import pymssql
import os
from core.config.edarsahub_config import get_edarsahub_sql_config
from core.sql_first.db import get_sql_connection
_edarsa_cfg = get_edarsahub_sql_config()


logger = logging.getLogger(__name__)

# ============================================================================
# CONFIGURACIÓN
# ============================================================================

EDARSAHUB_CONFIG = {
    "host": _edarsa_cfg.host,
    "port": _edarsa_cfg.port,
    "database": _edarsa_cfg.database,
    "user": _edarsa_cfg.user,
    "password": _edarsa_cfg.password,
}

# Configuración de cada unidad de negocio y su servidor POS
UNIDADES_CONFIG = {
    "CIENFUEGOS": {
        "system_type": "SoftRestaurant",
        "host": "servercienfuegos.ddns.net,6669\\nationalsoft",
        "port": 1433,
        "database": "softrestaurant95pro",
        "username": os.environ.get("CIENFUEGOS_DB_USER", "sa"),
        "password": os.environ.get("CIENFUEGOS_DB_PASS", ""),
    },
    "130MID": {
        "system_type": "SoftRestaurant",
        "host": "130mid.ddns.net",
        "port": 1433,
        "database": "softrestaurant10",
        "username": os.environ.get("130MID_DB_USER", "sa"),
        "password": os.environ.get("130MID_DB_PASS", ""),
    },
    "ESTELAR": {
        "system_type": "SoftRestaurant",
        "host": "serverestelar.ddns.net,6969",
        "port": 6969,
        "database": "softrestaurant12",
        "username": os.environ.get("ESTELAR_DB_USER", "sa"),
        "password": os.environ.get("ESTELAR_DB_PASS", ""),
    },
    "130QRO": {
        "system_type": "MPRO",
        "host": os.getenv('EDARSAHUB_SQL_HOST'),
        "port": 1433,
        "database": "QUERETARO",
        "username": os.environ.get("130QRO_DB_USER", os.getenv('EDARSAHUB_SQL_USER')),
        "password": os.environ.get("130QRO_DB_PASS", os.getenv('EDARSAHUB_SQL_PASSWORD')),
    },
    "ORIGEN": {
        "system_type": "MPRO",
        "host": os.getenv('EDARSAHUB_SQL_HOST'),
        "port": 1433,
        "database": "ORIGEN",
        "username": os.environ.get("ORIGEN_DB_USER", os.getenv('EDARSAHUB_SQL_USER')),
        "password": os.environ.get("ORIGEN_DB_PASS", os.getenv('EDARSAHUB_SQL_PASSWORD')),
    },
}


# ============================================================================
# FUNCIONES DE CONEXIÓN
# ============================================================================

def get_edarsahub_connection():
    """Conexión a EDARSAHUB (destino)."""
    return get_sql_connection()


def get_pos_connection(config: Dict) -> Optional[pymssql.Connection]:
    """Conexión a servidor POS origen."""
    try:
        return get_sql_connection()
    except Exception as e:
        logger.error(f"[SYNC] Error conectando a {config['host']}: {e}")
        return None


# ============================================================================
# QUERIES DE EXTRACCIÓN POR SISTEMA
# ============================================================================

def get_softrestaurant_query(fecha_inicio: str, fecha_fin: str) -> str:
    """Query para extraer ventas de SoftRestaurant."""
    return f"""
    SELECT 
        CONVERT(VARCHAR(64), ch.folio) AS NumeroTicket,
        CONVERT(VARCHAR(64), NEWID()) AS IdTransaccion,
        ch.nopersonas AS Pax,
        ch.total AS MontoTotal,
        t.apertura AS FechaHora,
        'COMPLETED' AS status,
        (
            SELECT 
                p.idproducto AS id,
                p.descripcion AS name,
                dc.cantidad AS quantity,
                dc.precio AS price,
                (dc.cantidad * dc.precio) AS total
            FROM cheqdet dc
            INNER JOIN productos p ON dc.idproducto = p.idproducto
            WHERE dc.foliodet = ch.folio
            FOR JSON PATH
        ) AS items
    FROM cheques ch
    INNER JOIN turnos t ON t.idturno = ch.idturno
    WHERE t.apertura >= '{fecha_inicio}'
      AND t.apertura < '{fecha_fin}'
      AND ch.cancelado = 0
      AND ch.total > 0
    ORDER BY t.apertura DESC
    """


def get_mpro_query(fecha_inicio: str, fecha_fin: str) -> str:
    """Query para extraer ventas de MPRO (ManagmentPro)."""
    return f"""
    SELECT 
        CONVERT(VARCHAR(64), v.Vn_Folio) AS NumeroTicket,
        CONVERT(VARCHAR(64), NEWID()) AS IdTransaccion,
        ISNULL(c.Co_Personas, 1) AS Pax,
        v.Vn_Precio_Neto_Importe AS MontoTotal,
        v.Vn_Fecha AS FechaHora,
        CASE WHEN v.Es_Cve_Estado = 'CA' THEN 'CANCELLED' ELSE 'COMPLETED' END AS status,
        (
            SELECT 
                d.Ar_Cve_Articulo AS id,
                a.Ar_Descripcion AS name,
                d.Vd_Cantidad AS quantity,
                d.Vd_Precio_Unitario AS price,
                d.Vd_Importe AS total
            FROM Venta_Detalle d
            LEFT JOIN Articulo a ON d.Ar_Cve_Articulo = a.Ar_Cve_Articulo
            WHERE d.Vn_Folio = v.Vn_Folio 
              AND d.Sc_Cve_Sucursal = v.Sc_Cve_Sucursal
            FOR JSON PATH
        ) AS items
    FROM Venta_Encabezado v
    LEFT JOIN Comanda c ON c.Co_Folio = v.Vn_Folio AND c.Sc_Cve_Sucursal = v.Sc_Cve_Sucursal
    WHERE v.Vn_Fecha >= '{fecha_inicio}'
      AND v.Vn_Fecha < '{fecha_fin}'
      AND ISNULL(v.Es_Cve_Estado, '') <> 'CA'
      AND v.Vn_Precio_Neto_Importe > 0
    ORDER BY v.Vn_Fecha DESC
    """


# ============================================================================
# FUNCIONES DE SINCRONIZACIÓN
# ============================================================================

def extract_sales_from_pos(
    unidad: str, 
    config: Dict, 
    fecha_inicio: str, 
    fecha_fin: str
) -> List[Dict]:
    """Extrae ventas de un POS específico."""
    
    conn = get_pos_connection(config)
    if not conn:
        logger.warning(f"[SYNC] No se pudo conectar a {unidad}")
        return []
    
    try:
        cursor = conn.cursor(as_dict=True)
        
        # Seleccionar query según sistema
        if config["system_type"] == "SoftRestaurant":
            query = get_softrestaurant_query(fecha_inicio, fecha_fin)
        else:  # MPRO
            query = get_mpro_query(fecha_inicio, fecha_fin)
        
        cursor.execute(query)
        rows = cursor.fetchall()
        
        # Agregar unidad de negocio a cada registro
        for row in rows:
            row["UnidadNegocio"] = unidad
        
        logger.info(f"[SYNC] {unidad}: {len(rows)} registros extraídos")
        
        cursor.close()
        conn.close()
        
        return rows
        
    except Exception as e:
        logger.error(f"[SYNC] Error extrayendo de {unidad}: {e}")
        return []


def insert_into_sync_sales(conn, sales: List[Dict]) -> int:
    """Inserta registros en Sync_Sales."""
    if not sales:
        return 0
    
    cursor = conn.cursor()
    inserted = 0
    
    for sale in sales:
        try:
            # Verificar si ya existe (por NumeroTicket + UnidadNegocio + FechaHora)
            cursor.execute("""
                SELECT COUNT(*) FROM Sync_Sales 
                WHERE NumeroTicket = %s AND UnidadNegocio = %s 
                  AND CAST(FechaHora AS DATE) = CAST(%s AS DATE)
            """, (sale["NumeroTicket"], sale["UnidadNegocio"], sale["FechaHora"]))
            
            if cursor.fetchone()[0] > 0:
                continue  # Ya existe, skip
            
            # Insertar nuevo registro
            cursor.execute("""
                INSERT INTO Sync_Sales (
                    id, branch, UnidadNegocio, NumeroTicket, 
                    MontoTotal, Pax, FechaHora, status, items,
                    created_at, total
                ) VALUES (
                    %s, %s, %s, %s, 
                    %s, %s, %s, %s, %s,
                    GETDATE(), %s
                )
            """, (
                sale.get("IdTransaccion", str(datetime.now().timestamp())),
                sale["UnidadNegocio"],
                sale["UnidadNegocio"],
                sale["NumeroTicket"],
                sale["MontoTotal"],
                sale["Pax"],
                sale["FechaHora"],
                sale.get("status", "COMPLETED"),
                sale.get("items", "[]"),
                sale["MontoTotal"]
            ))
            
            inserted += 1
            
        except Exception as e:
            logger.warning(f"[SYNC] Error insertando ticket {sale.get('NumeroTicket')}: {e}")
    
    cursor.close()
    return inserted


def update_kpis_diarios(conn, unidad: str, fecha: str) -> bool:
    """Actualiza/inserta KPIs diarios para una unidad y fecha."""
    cursor = conn.cursor(as_dict=True)
    
    try:
        # Calcular KPIs desde Sync_Sales
        cursor.execute("""
            SELECT 
                COUNT(DISTINCT NumeroTicket) AS tickets,
                SUM(MontoTotal) AS ventas,
                SUM(Pax) AS Pax
            FROM Sync_Sales
            WHERE UnidadNegocio = %s
              AND CAST(FechaHora AS DATE) = %s
              AND status = 'COMPLETED'
        """, (unidad, fecha))
        
        kpis = cursor.fetchone()
        
        if not kpis or not kpis["ventas"]:
            return False
        
        # Verificar si ya existe registro
        cursor.execute("""
            SELECT id FROM Comercial_KPIs_Diarios_v2
            WHERE unidad_negocio_nombre = %s AND fecha_operacion = %s
        """, (unidad, fecha))
        
        existing = cursor.fetchone()
        
        if existing:
            # Actualizar
            cursor.execute("""
                UPDATE Comercial_KPIs_Diarios_v2
                SET ventas_total = %s,
                    pax_total = %s,
                    tickets_total = %s,
                    ticket_promedio = CASE WHEN %s > 0 THEN %s / %s ELSE 0 END,
                    fecha_ultima_actualizacion = GETDATE()
                WHERE id = %s
            """, (
                kpis["ventas"], kpis["pax"], kpis["tickets"],
                kpis["tickets"], kpis["ventas"], kpis["tickets"],
                existing["id"]
            ))
        else:
            # Insertar nuevo
            fecha_dt = datetime.strptime(fecha, "%Y-%m-%d")
            cursor.execute("""
                INSERT INTO Comercial_KPIs_Diarios_v2 (
                    id, unidad_negocio_id, unidad_negocio_nombre,
                    server_id, sucursal_id, sistema_origen,
                    fecha_operacion, anio, mes, dia,
                    ventas_total, pax_total, tickets_total, ticket_promedio,
                    activo, fuente_original, fecha_alta
                ) VALUES (
                    NEWID(), %s, %s,
                    %s, %s, %s,
                    %s, %s, %s, %s,
                    %s, %s, %s, %s,
                    1, 'SYNC_JOB', GETDATE()
                )
            """, (
                unidad, unidad,
                unidad, unidad, "SYNC_JOB",
                fecha, fecha_dt.year, fecha_dt.month, fecha_dt.day,
                kpis["ventas"], kpis["pax"], kpis["tickets"],
                kpis["ventas"] / kpis["tickets"] if kpis["tickets"] > 0 else 0
            ))
        
        cursor.close()
        return True
        
    except Exception as e:
        logger.error(f"[SYNC] Error actualizando KPIs para {unidad}/{fecha}: {e}")
        cursor.close()
        return False


def update_job_status(conn, status: str = "ACTIVE"):
    """Actualiza el estado del job en Sys_Scheduler_Jobs."""
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE Sys_Scheduler_Jobs 
        SET LastRunDate = GETDATE(), Status = %s 
        WHERE JobName = 'inteligencia_comercial_sync'
    """, (status,))
    cursor.close()


# ============================================================================
# FUNCIÓN PRINCIPAL DEL JOB
# ============================================================================

def job_inteligencia_comercial_sync(
    dias_atras: int = 1,
    unidades: List[str] = None
) -> Dict[str, Any]:
    """
    Job principal de sincronización de Inteligencia Comercial.
    
    Args:
        dias_atras: Cuántos días hacia atrás sincronizar (default: 1)
        unidades: Lista de unidades a sincronizar (default: todas)
    
    Returns:
        Dict con estadísticas de la ejecución
    """
    logger.info("[INTELIGENCIA_SYNC] ========== INICIO ==========")
    
    # Fechas a sincronizar
    fecha_fin = datetime.now()
    fecha_inicio = fecha_fin - timedelta(days=dias_atras)
    fecha_inicio_str = fecha_inicio.strftime("%Y-%m-%d")
    fecha_fin_str = fecha_fin.strftime("%Y-%m-%d")
    
    logger.info(f"[INTELIGENCIA_SYNC] Período: {fecha_inicio_str} a {fecha_fin_str}")
    
    # Unidades a procesar
    if not unidades:
        unidades = list(UNIDADES_CONFIG.keys())
    
    stats = {
        "fecha_inicio": fecha_inicio_str,
        "fecha_fin": fecha_fin_str,
        "unidades_procesadas": 0,
        "registros_extraidos": 0,
        "registros_insertados": 0,
        "kpis_actualizados": 0,
        "errores": []
    }
    
    try:
        # Conexión a EDARSAHUB
        hub_conn = get_edarsahub_connection()
        
        for unidad in unidades:
            config = UNIDADES_CONFIG.get(unidad)
            if not config:
                logger.warning(f"[INTELIGENCIA_SYNC] Configuración no encontrada para {unidad}")
                continue
            
            logger.info(f"[INTELIGENCIA_SYNC] Procesando {unidad} ({config['system_type']})...")
            
            try:
                # 1. Extraer ventas del POS
                sales = extract_sales_from_pos(
                    unidad, config, fecha_inicio_str, fecha_fin_str
                )
                stats["registros_extraidos"] += len(sales)
                
                # 2. Insertar en Sync_Sales
                if sales:
                    inserted = insert_into_sync_sales(hub_conn, sales)
                    stats["registros_insertados"] += inserted
                    hub_conn.commit()
                
                # 3. Actualizar KPIs diarios
                current_date = fecha_inicio
                while current_date <= fecha_fin:
                    fecha_str = current_date.strftime("%Y-%m-%d")
                    if update_kpis_diarios(hub_conn, unidad, fecha_str):
                        stats["kpis_actualizados"] += 1
                    current_date += timedelta(days=1)
                
                hub_conn.commit()
                stats["unidades_procesadas"] += 1
                
            except Exception as e:
                error_msg = f"{unidad}: {str(e)}"
                logger.error(f"[INTELIGENCIA_SYNC] Error: {error_msg}")
                stats["errores"].append(error_msg)
                hub_conn.rollback()
        
        # Actualizar estado del job
        update_job_status(hub_conn, "ACTIVE")
        hub_conn.commit()
        hub_conn.close()
        
    except Exception as e:
        logger.error(f"[INTELIGENCIA_SYNC] Error general: {e}")
        stats["errores"].append(f"General: {str(e)}")
    
    logger.info(f"[INTELIGENCIA_SYNC] ========== FIN ==========")
    logger.info(f"[INTELIGENCIA_SYNC] Stats: {stats}")
    
    return stats


# ============================================================================
# EJECUCIÓN DIRECTA (para testing)
# ============================================================================

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    result = job_inteligencia_comercial_sync(dias_atras=1)
    print(json.dumps(result, indent=2, default=str))
