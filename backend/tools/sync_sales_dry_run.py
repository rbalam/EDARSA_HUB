#!/usr/bin/env python3
"""
SYNC_SALES DRY-RUN TOOL
=======================
Herramienta de diagnóstico para validar extracción de tickets
hacia Sync_Sales SIN insertar datos.

ALINEADO 100% AL PATRÓN DE sync_comercial_edarsahub.py:
- Usa get_server_connection_config() del módulo comercial_v2
- Usa execute_query_on_server() del módulo comercial_v2
- Lee credenciales de Servidores_Conexiones
- Descifra password con core.secret_manager.decrypt_secret()
- NO usa hardcoded ni variables de entorno para POS

Uso:
    cd /app/backend
    python tools/sync_sales_dry_run.py --unidad CIENFUEGOS --fecha-inicio 2026-06-01 --fecha-fin 2026-06-01 --dry-run

Autor: Agente E1
Fecha: 2026-06-02
"""

import argparse
import json
import logging
import os
import sys
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple

# Agregar backend al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pymssql

# Importar directamente sin cargar todo el módulo (evitar dependencias de security)
from core.db import execute_sql_query

# Configuración EDARSAHUB (igual que repository_comercial_edarsahub.py)
EDARSAHUB_CONFIG = {
    'host': os.getenv('EDARSAHUB_SQL_HOST'),
    'port': 1433,
    'database': 'EDARSAHUB',
    'username': os.getenv('EDARSAHUB_SQL_USER'),
    'password': os.getenv('EDARSAHUB_SQL_PASSWORD')
}

# Enum de estado de conexión
class ConnectionStatus:
    ONLINE = "ONLINE"
    OFFLINE = "OFFLINE"
    TIMEOUT = "TIMEOUT"


def _execute_query(query: str) -> List[Dict]:
    """Ejecuta query en EDARSAHUB."""
    try:
        result = execute_sql_query(
            EDARSAHUB_CONFIG['host'],
            EDARSAHUB_CONFIG['port'],
            EDARSAHUB_CONFIG['database'],
            EDARSAHUB_CONFIG['username'],
            EDARSAHUB_CONFIG['password'],
            query
        )
        return result if result else []
    except Exception as e:
        logger.error(f"Error ejecutando query: {e}")
        return []


def get_server_connection_config(server_id: str) -> Optional[Dict[str, Any]]:
    """
    Obtiene config de servidor desde Servidores_Conexiones.
    Copia del patrón de sync_comercial_edarsahub.py
    """
    try:
        from core.secret_manager import decrypt_secret
    except ImportError:
        decrypt_secret = lambda x: x
    
    try:
        from core.db import parse_sql_server_host
    except ImportError:
        def parse_sql_server_host(host, default_port):
            if ',' in host:
                parts = host.split(',')
                h = parts[0]
                rest = parts[1] if len(parts) > 1 else str(default_port)
                if '\\' in rest:
                    p_str, inst = rest.split('\\', 1)
                    p = int(p_str) if p_str.isdigit() else default_port
                    return (h, p, inst)
                else:
                    p = int(rest) if rest.isdigit() else default_port
                    return (h, p, None)
            return (host, default_port, None)
    
    query = f"""
    SELECT 
        id, nombre, host, port, database_name,
        username, password_encrypted, system_type, activo
    FROM Servidores_Conexiones
    WHERE id = '{server_id}'
    """
    
    rows = _execute_query(query)
    if not rows:
        return None
    
    row = rows[0]
    
    # Descifrar password
    pwd_enc = row.get('password_encrypted', '')
    try:
        password = decrypt_secret(pwd_enc)
    except Exception:
        password = pwd_enc
    
    # Parsear host
    host_raw = row.get('host', '')
    default_port = row.get('port') or 1433
    hostname, parsed_port, instance = parse_sql_server_host(host_raw, default_port)
    
    return {
        'id': str(row['id']),
        'nombre': row['nombre'],
        'host': hostname,
        'host_raw': host_raw,
        'port': parsed_port,
        'instance': instance,
        'database_name': row['database_name'],
        'username': row['username'],
        'password': password,
        'system_type': row['system_type'],
        'activo': row['activo']
    }


def execute_query_on_server(server_config: Dict, query: str) -> Tuple[List[Dict], str]:
    """
    Ejecuta query en servidor POS.
    Copia del patrón de sync_comercial_edarsahub.py
    """
    try:
        host = server_config.get('host_raw') or server_config.get('host', '')
        port = server_config.get('port', 1433)
        database = server_config.get('database_name', '')
        username = server_config.get('username', '')
        password = server_config.get('password', '')
        
        result = execute_sql_query(host, port, database, username, password, query)
        
        if result is None:
            return [], ConnectionStatus.OFFLINE
        
        if result:
            return result, ConnectionStatus.ONLINE
        
        # Sin resultados, verificar conectividad
        test_result = execute_sql_query(host, port, database, username, password, "SELECT 1 AS test")
        if test_result:
            return [], ConnectionStatus.ONLINE
        else:
            return [], ConnectionStatus.OFFLINE
        
    except Exception as e:
        error_str = str(e).lower()
        if 'timeout' in error_str:
            return [], ConnectionStatus.TIMEOUT
        return [], ConnectionStatus.OFFLINE

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Unidades permitidas - TODAS las unidades activas
# (Se eliminó la restricción de choices para permitir MPRO y otras)
UNIDADES_PERMITIDAS = None  # Ya no se restringe por lista fija


# =============================================================================
# FUNCIONES DE CONFIGURACIÓN (usando patrón de sync_comercial_edarsahub.py)
# =============================================================================

def get_unidad_config(unidad_codigo: str) -> Optional[Dict[str, Any]]:
    """
    Obtiene la configuración completa de una unidad.
    Patrón: Unidades_Negocio -> server_id -> Servidores_Conexiones
    Soporta: SoftRestaurant, MPRO (ManagmentPro)
    """
    # Mapeo de códigos a nombres en Unidades_Negocio
    nombre_map = {
        "CIENFUEGOS": "CIENFUEGOS",
        "130MID": "130° MERIDA",
        "130QRO": "130° QUERETARO",
        "ESTELAR": "LA ESTELAR",
        "ORIGEN": "ORIGEN",
    }
    
    nombre_buscar = nombre_map.get(unidad_codigo, unidad_codigo)
    
    # 1. Buscar en Unidades_Negocio - ahora también por código
    query_unidad = f"""
    SELECT 
        id,
        codigo,
        nombre,
        server_id,
        sucursal_origen_id,
        system_type,
        activo
    FROM Unidades_Negocio
    WHERE (nombre LIKE '%{nombre_buscar}%' OR codigo = '{unidad_codigo}')
      AND ISNULL(activo, 1) = 1
    """
    
    try:
        unidades = _execute_query(query_unidad)
        if not unidades:
            logger.error(f"No se encontró unidad '{nombre_buscar}' en Unidades_Negocio")
            return None
        
        unidad = unidades[0]
        server_id = unidad.get('server_id')
        
        if not server_id:
            logger.error(f"Unidad '{nombre_buscar}' no tiene server_id asignado")
            return None
        
        logger.info(f"Unidad encontrada: {unidad['nombre']} (ID: {unidad['id']})")
        logger.info(f"Server ID: {server_id}")
        logger.info(f"Sistema: {unidad.get('system_type')}")
        
        # 2. Obtener configuración del servidor usando la función del módulo
        server_config = get_server_connection_config(str(server_id))
        if not server_config:
            logger.error(f"No se pudo obtener configuración del servidor {server_id}")
            return None
        
        # Verificar credenciales
        if not server_config.get('username') or not server_config.get('password'):
            logger.error(f"Servidor {server_config.get('nombre')} no tiene credenciales")
            return None
        
        # 3. Combinar información - incluir sucursal_origen_id para MPRO
        return {
            "unidad_id": str(unidad['id']),
            "unidad_codigo": unidad.get('codigo') or unidad_codigo,
            "unidad_nombre": unidad['nombre'],
            "server_id": str(server_id),
            "system_type": unidad.get('system_type', '').upper(),
            "sucursal_origen_id": unidad.get('sucursal_origen_id'),  # IMPORTANTE para MPRO
            "server_config": server_config,  # Config completa del servidor
        }
        
    except Exception as e:
        logger.error(f"Error obteniendo config de unidad {unidad_codigo}: {e}")
        return None


# =============================================================================
# QUERIES DE EXTRACCIÓN
# =============================================================================

def get_softrestaurant_query(fecha_inicio: str, fecha_fin: str) -> str:
    """
    Query para extraer ventas cerradas de SoftRestaurant.
    COMPATIBLE CON SQL SERVER LEGACY - NO USA FOR JSON PATH.
    Devuelve filas planas ticket+detalle para agrupar en Python.
    
    Incluye múltiples columnas candidatas de importe para fallback:
    - cheques: total, subtotal, totalsindescuento
    - cheqdet: totalsrx, subtotalsrx, precio, cantidad
    """
    return f"""
    SELECT 
        CONVERT(VARCHAR(64), ch.folio) AS NumeroTicket,
        ch.nopersonas AS Pax,
        ch.total AS MontoTotal,
        ch.subtotal AS SubtotalCheque,
        ch.totalsindescuento AS TotalSinDescuento,
        t.apertura AS FechaHora,
        dc.idproducto AS item_id,
        p.descripcion AS item_name,
        dc.cantidad AS item_quantity,
        dc.precio AS item_price,
        dc.totalsrx AS item_totalsrx,
        dc.subtotalsrx AS item_subtotalsrx,
        dc.preciosinimpuestos AS item_preciosinimpuestos
    FROM cheques ch
    INNER JOIN turnos t ON t.idturno = ch.idturno
    LEFT JOIN cheqdet dc ON dc.foliodet = ch.folio
    LEFT JOIN productos p ON dc.idproducto = p.idproducto
    WHERE CAST(t.apertura AS DATE) >= '{fecha_inicio}'
      AND CAST(t.apertura AS DATE) <= '{fecha_fin}'
      AND ch.cancelado = 0
      AND ch.total > 0
    ORDER BY ch.folio, dc.idproducto
    """


def _safe_float(value):
    """Convierte a float de forma segura. Ignora valores negativos (centinelas)."""
    if value is None:
        return 0.0
    try:
        f = float(value)
        # Ignorar valores negativos (centinelas como -1)
        return f if f >= 0 else 0.0
    except:
        return 0.0


def _safe_int(value):
    """Convierte a int de forma segura."""
    if value is None:
        return 0
    try:
        return int(value)
    except:
        return 0


# =============================================================================
# REGLA PERMANENTE: SOFTRESTAURANT LEGACY
# =============================================================================
# Documento rector: /app/docs/rules/RULE_SYNC_SALES_SOFTRESTAURANT_LEGACY_AMOUNTS.md
#
# PROHIBIDO:
# - Usar FOR JSON PATH contra SoftRestaurant legacy
# - Usar cheqdet.totalsrx como importe (puede ser -1)
# - Usar cheqdet.subtotalsrx como importe (puede ser -1)
#
# OBLIGATORIO:
# - Calcular item_total como cantidad * precio
# - Usar json.dumps() para construir items JSON en Python
# =============================================================================

def calculate_softrestaurant_item_total(row: Dict) -> float:
    """
    REGLA PERMANENTE - SoftRestaurant Legacy:
    
    NO usar totalsrx/subtotalsrx como importe porque pueden venir en -1.
    SoftRestaurant legacy DEBE calcular item_total como cantidad * precio.
    
    Args:
        row: Fila con campos item_quantity e item_price
        
    Returns:
        float: El importe calculado como quantity * price
    """
    quantity = _safe_float(row.get("item_quantity"))
    price = _safe_float(row.get("item_price"))
    
    # Regla permanente: item_total = cantidad * precio
    # NO usar totalsrx ni subtotalsrx
    return round(quantity * price, 2)


def build_sales_from_flat_rows(rows: List[Dict], unidad_codigo: str) -> List[Dict]:
    """
    Agrupa filas planas de ticket+detalle en registros de venta con items JSON.
    Compatible con SQL Server legacy (NO depende de FOR JSON PATH).
    
    REGLA PERMANENTE APLICADA:
    - El importe de cada item se calcula con calculate_softrestaurant_item_total()
    - NO se usa totalsrx ni subtotalsrx como fuente de importe
    - El JSON items se construye con json.dumps() en Python
    - Si MontoTotal <= 0, se recalcula como suma de items
    - Si hay items pero total calculado es 0, se genera error
    """
    from collections import defaultdict
    
    # Agrupar por ticket
    tickets = defaultdict(lambda: {
        "NumeroTicket": None,
        "Pax": 0,
        "MontoTotal": 0.0,
        "SubtotalCheque": 0.0,
        "TotalSinDescuento": 0.0,
        "FechaHora": None,
        "items": []
    })
    
    for row in rows:
        numero_ticket = str(row.get("NumeroTicket", "") or "").strip()
        if not numero_ticket:
            continue
        
        ticket = tickets[numero_ticket]
        
        # Solo llenar datos del ticket una vez
        if ticket["NumeroTicket"] is None:
            ticket["NumeroTicket"] = numero_ticket
            ticket["Pax"] = _safe_int(row.get("Pax"))
            ticket["MontoTotal"] = _safe_float(row.get("MontoTotal"))
            ticket["SubtotalCheque"] = _safe_float(row.get("SubtotalCheque"))
            ticket["TotalSinDescuento"] = _safe_float(row.get("TotalSinDescuento"))
            ticket["FechaHora"] = row.get("FechaHora")
        
        # Agregar item si existe
        item_id = row.get("item_id")
        if item_id is not None:
            # REGLA PERMANENTE: Calcular importe con calculate_softrestaurant_item_total
            # NO usar totalsrx/subtotalsrx
            quantity = _safe_float(row.get("item_quantity"))
            price = _safe_float(row.get("item_price"))
            item_total = calculate_softrestaurant_item_total(row)
            
            ticket["items"].append({
                "id": str(item_id),
                "name": str(row.get("item_name", "") or ""),
                "quantity": quantity,
                "price": price,
                "total": item_total
            })
    
    # Convertir a lista de registros con items como JSON string
    sales = []
    for numero_ticket, ticket in tickets.items():
        # Calcular suma de items
        items_total = sum(_safe_float(item.get("total")) for item in ticket["items"])
        
        # REGLA PERMANENTE: Si MontoTotal <= 0, recalcular como suma de items
        monto_total = _safe_float(ticket["MontoTotal"])
        if monto_total <= 0:
            monto_total = items_total
        
        # REGLA PERMANENTE: Validar que si hay items, el total no sea cero
        if ticket["items"] and items_total <= 0:
            logger.warning(
                f"⚠️ Ticket {numero_ticket} tiene {len(ticket['items'])} items pero total calculado = 0. "
                "Revisar cantidad/precio SoftRestaurant legacy."
            )
        
        sales.append({
            "NumeroTicket": ticket["NumeroTicket"],
            "IdTransaccion": ticket["NumeroTicket"],
            "Pax": ticket["Pax"],
            "MontoTotal": round(monto_total, 2),
            "MontoItems": round(items_total, 2),  # Para diagnóstico
            "FechaHora": ticket["FechaHora"],
            "status": "COMPLETED",
            "items": json.dumps(ticket["items"], ensure_ascii=False) if ticket["items"] else "[]",
            "UnidadNegocio": unidad_codigo
        })
    
    return sales


def get_mpro_query(fecha_inicio: str, fecha_fin: str, sucursal_id: str) -> str:
    """
    Query para extraer ventas cerradas de MPRO (ManagmentPro).
    COMPATIBLE CON SQL SERVER LEGACY - NO USA FOR JSON PATH.
    Devuelve filas planas ticket+detalle para agrupar en Python.
    
    NOTA: MPRO usa la tabla 'Venta' que contiene tanto encabezado como detalle.
    La tabla 'Venta_Encabezado' es solo el resumen (totales por folio).
    Vn_Tabla = 'Comanda' indica ventas cerradas desde el módulo de restaurante.
    """
    return f"""
    SELECT 
        CONVERT(VARCHAR(64), v.Vn_Folio) AS NumeroTicket,
        ISNULL(c.Co_Personas, 1) AS Pax,
        ve.Vn_Precio_Neto_Importe AS MontoTotal,
        v.Vn_Fecha AS FechaHora,
        v.Pr_Cve_Producto AS item_id,
        v.Vn_Concepto AS item_name,
        v.Vn_Cantidad_1 AS item_quantity,
        v.Vn_Precio_Neto AS item_price,
        v.Vn_Precio_Neto_Importe AS item_total
    FROM Venta v
    INNER JOIN Venta_Encabezado ve 
        ON v.Vn_Folio = ve.Vn_Folio 
        AND v.Sc_Cve_Sucursal = ve.Sc_Cve_Sucursal
    LEFT JOIN Comanda c 
        ON ve.Vn_Documento = c.Co_Folio 
        AND ve.Sc_Cve_Sucursal = c.Sc_Cve_Sucursal
    WHERE CAST(v.Vn_Fecha AS DATE) >= '{fecha_inicio}'
      AND CAST(v.Vn_Fecha AS DATE) <= '{fecha_fin}'
      AND v.Sc_Cve_Sucursal = '{sucursal_id}'
      AND ve.Vn_Tabla = 'Comanda'
    ORDER BY v.Vn_Folio, v.Pr_Cve_Producto
    """


# =============================================================================
# FUNCIONES DE EXTRACCIÓN (usando execute_query_on_server del módulo)
# =============================================================================

def extract_sales_from_pos(config: Dict, fecha_inicio: str, fecha_fin: str) -> Tuple[List[Dict], str]:
    """
    Extrae ventas de un POS usando execute_query_on_server del módulo comercial_v2.
    Compatible con SQL Server legacy - NO usa FOR JSON PATH.
    Soporta: SoftRestaurant, MPRO (ManagmentPro)
    Retorna (registros, connection_status)
    """
    server_config = config['server_config']
    # Usar system_type de la unidad (más preciso) o del servidor
    system_type = config.get('system_type', '').upper() or server_config.get('system_type', '').upper()
    
    # Determinar qué query usar según el sistema
    if 'SOFT' in system_type:
        # SoftRestaurant
        query = get_softrestaurant_query(fecha_inicio, fecha_fin)
        logger.info(f"Sistema: SoftRestaurant")
    elif 'MPRO' in system_type:
        # ManagmentPro - requiere sucursal_origen_id
        sucursal_id = config.get('sucursal_origen_id')
        if not sucursal_id:
            logger.error(f"MPRO requiere sucursal_origen_id pero no está configurado")
            return [], "CONFIG_INCOMPLETA"
        query = get_mpro_query(fecha_inicio, fecha_fin, sucursal_id)
        logger.info(f"Sistema: MPRO (Sucursal: {sucursal_id})")
    else:
        logger.error(f"Sistema {system_type} no soportado")
        return [], "SISTEMA_NO_SOPORTADO"
    
    logger.info(f"Ejecutando query en {server_config['nombre']}...")
    logger.info(f"Host: {server_config.get('host_raw', server_config.get('host'))}")
    logger.info(f"Database: {server_config['database_name']}")
    
    # Usar la función del módulo (misma que usa sync_comercial_edarsahub.py)
    rows, conn_status = execute_query_on_server(server_config, query)
    
    # Mapear estado de conexión
    status_map = {
        ConnectionStatus.ONLINE: "OK",
        ConnectionStatus.OFFLINE: "OFFLINE",
        ConnectionStatus.TIMEOUT: "TIMEOUT",
    }
    connection_status = status_map.get(conn_status, str(conn_status))
    
    if conn_status != ConnectionStatus.ONLINE:
        logger.warning(f"Estado de conexión: {connection_status}")
        return [], connection_status
    
    # NUEVO: Agrupar filas planas en tickets con items JSON (Python-side)
    logger.info(f"Filas planas recibidas: {len(rows)}")
    sales = build_sales_from_flat_rows(rows, config["unidad_codigo"])
    
    logger.info(f"✅ {len(sales)} tickets agrupados con items JSON")
    
    return sales, connection_status


# =============================================================================
# FUNCIONES DE VALIDACIÓN
# =============================================================================

def get_sync_sales_count() -> Dict:
    """Obtiene el estado actual de Sync_Sales."""
    query = """
    SELECT
        COUNT(*) AS registros,
        MIN(FechaHora) AS fecha_minima,
        MAX(FechaHora) AS fecha_maxima,
        MAX(last_modified) AS ultima_modificacion
    FROM dbo.Sync_Sales
    """
    rows = _execute_query(query)
    return rows[0] if rows else {"registros": 0}


def get_kpis_count() -> int:
    """Obtiene el conteo de Comercial_KPIs_Diarios_v2."""
    query = "SELECT COUNT(*) AS total FROM Comercial_KPIs_Diarios_v2"
    rows = _execute_query(query)
    return rows[0]['total'] if rows else 0


def check_duplicates_in_sync_sales(sales: List[Dict]) -> Dict[str, int]:
    """Verifica cuántos registros ya existen en Sync_Sales."""
    if not sales:
        return {"nuevos": 0, "duplicados": 0}
    
    stats = {"nuevos": 0, "duplicados": 0}
    
    for sale in sales:
        query = f"""
        SELECT COUNT(*) AS cnt FROM Sync_Sales 
        WHERE NumeroTicket = '{sale["NumeroTicket"]}' 
          AND UnidadNegocio = '{sale["UnidadNegocio"]}' 
          AND CAST(FechaHora AS DATE) = CAST('{sale["FechaHora"]}' AS DATE)
        """
        rows = _execute_query(query)
        if rows and rows[0]['cnt'] > 0:
            stats["duplicados"] += 1
        else:
            stats["nuevos"] += 1
    
    return stats


def validate_json_items(sales: List[Dict]) -> Dict[str, int]:
    """Valida la estructura JSON de items."""
    stats = {"validos": 0, "nulos": 0, "invalidos": 0}
    
    for sale in sales:
        items = sale.get("items")
        if items is None:
            stats["nulos"] += 1
        else:
            try:
                if isinstance(items, str):
                    json.loads(items)
                stats["validos"] += 1
            except:
                stats["invalidos"] += 1
    
    return stats


def validate_importes(sales: List[Dict]) -> Dict[str, Any]:
    """
    Valida integridad de importes.
    Rechaza dry-run si:
    - tickets > 0 y monto_total_global <= 0
    - items tienen importe <= 0 de forma masiva (>50%)
    """
    if not sales:
        return {
            "valido": True,
            "tickets_total": 0,
            "tickets_con_monto": 0,
            "tickets_sin_monto": 0,
            "monto_total_global": 0.0,
            "items_con_importe": 0,
            "items_sin_importe": 0,
            "porcentaje_items_sin_importe": 0.0,
            "errores": []
        }
    
    tickets_con_monto = 0
    tickets_sin_monto = 0
    monto_total_global = 0.0
    items_con_importe = 0
    items_sin_importe = 0
    errores = []
    
    for sale in sales:
        monto = float(sale.get("MontoTotal", 0) or 0)
        monto_total_global += monto
        
        if monto > 0:
            tickets_con_monto += 1
        else:
            tickets_sin_monto += 1
        
        # Contar items con/sin importe
        items_str = sale.get("items", "[]")
        try:
            items = json.loads(items_str) if isinstance(items_str, str) else items_str
            for item in items:
                if float(item.get("total", 0) or 0) > 0:
                    items_con_importe += 1
                else:
                    items_sin_importe += 1
        except:
            pass
    
    total_items = items_con_importe + items_sin_importe
    porcentaje_sin_importe = (items_sin_importe / total_items * 100) if total_items > 0 else 0
    
    # Validaciones
    valido = True
    
    if len(sales) > 0 and monto_total_global <= 0:
        errores.append(f"ERROR CRÍTICO: {len(sales)} tickets pero monto_total_global = ${monto_total_global:.2f}")
        valido = False
    
    if porcentaje_sin_importe > 50:
        errores.append(f"WARNING: {porcentaje_sin_importe:.1f}% de items sin importe ({items_sin_importe}/{total_items})")
        # No marca como inválido, solo warning
    
    if tickets_sin_monto > 0 and tickets_sin_monto == len(sales):
        errores.append(f"ERROR CRÍTICO: TODOS los tickets ({tickets_sin_monto}) tienen MontoTotal = 0")
        valido = False
    
    return {
        "valido": valido,
        "tickets_total": len(sales),
        "tickets_con_monto": tickets_con_monto,
        "tickets_sin_monto": tickets_sin_monto,
        "monto_total_global": round(monto_total_global, 2),
        "items_con_importe": items_con_importe,
        "items_sin_importe": items_sin_importe,
        "porcentaje_items_sin_importe": round(porcentaje_sin_importe, 2),
        "errores": errores
    }


# =============================================================================
# FUNCIÓN DE INSERCIÓN (--execute)
# =============================================================================

def insert_sales_to_sync_sales(sales: List[Dict], unidad_codigo: str) -> Dict[str, Any]:
    """
    Inserta los registros de venta en la tabla Sync_Sales.
    
    IMPORTANTE:
    - Solo se ejecuta con --execute explícito
    - No modifica Comercial_KPIs_Diarios_v2
    - Verifica duplicados antes de insertar
    
    Estructura de Sync_Sales:
    - id: varchar NOT NULL (generado como unidad-ticket-fecha)
    - branch: nvarchar NOT NULL (UnidadNegocio)
    - total: numeric NOT NULL
    - items: nvarchar (JSON)
    - NumeroTicket, FechaHora, Pax, MontoTotal, UnidadNegocio, etc.
    
    Returns:
        Dict con estadísticas de inserción
    """
    from datetime import datetime
    import uuid
    
    if not sales:
        return {
            "success": True,
            "inserted": 0,
            "skipped": 0,
            "errors": 0,
            "error_messages": []
        }
    
    inserted = 0
    skipped = 0
    errors = 0
    error_messages = []
    
    for sale in sales:
        try:
            # Verificar si ya existe (por NumeroTicket + UnidadNegocio + Fecha)
            numero_ticket = sale.get("NumeroTicket", "")
            fecha_hora = sale.get("FechaHora")
            
            # Formatear fecha para SQL
            if fecha_hora:
                if isinstance(fecha_hora, str):
                    fecha_str = fecha_hora[:19]
                else:
                    fecha_str = fecha_hora.isoformat()[:19] if hasattr(fecha_hora, 'isoformat') else str(fecha_hora)[:19]
            else:
                fecha_str = datetime.now().isoformat()[:19]
            
            fecha_date = fecha_str[:10]  # Solo la fecha YYYY-MM-DD
            
            # Generar ID único: UNIDAD-TICKET-FECHA
            sale_id = f"{unidad_codigo}-{numero_ticket}-{fecha_date}"
            
            # Check duplicado por id
            check_query = f"""
            SELECT COUNT(*) as cnt 
            FROM Sync_Sales 
            WHERE id = '{sale_id}'
            """
            result = _execute_query(check_query)
            if result and result[0].get('cnt', 0) > 0:
                skipped += 1
                continue
            
            # Preparar valores para INSERT
            monto_total = float(sale.get("MontoTotal", 0) or 0)
            pax = int(sale.get("Pax", 0) or 0)
            items_json = sale.get("items", "[]")
            status = sale.get("status", "COMPLETED")
            
            # Escapar comillas en JSON
            items_json_escaped = items_json.replace("'", "''") if items_json else "[]"
            
            # INSERT con todos los campos requeridos
            insert_query = f"""
            INSERT INTO Sync_Sales (
                id,
                branch,
                customer_id,
                items,
                total,
                currency,
                status,
                created_at,
                last_modified,
                IdTransaccion,
                UnidadNegocio,
                MontoTotal,
                Pax,
                NumeroTicket,
                FechaHora
            ) VALUES (
                '{sale_id}',
                N'{unidad_codigo}',
                NULL,
                N'{items_json_escaped}',
                {monto_total},
                'MXN',
                '{status}',
                GETDATE(),
                GETDATE(),
                '{numero_ticket}',
                N'{unidad_codigo}',
                {monto_total},
                {Pax},
                '{numero_ticket}',
                '{fecha_str}'
            )
            """
            
            _execute_query(insert_query)
            inserted += 1
            
        except Exception as e:
            errors += 1
            error_messages.append(f"Ticket {sale.get('NumeroTicket', 'N/A')}: {str(e)[:100]}")
            if errors >= 5:
                error_messages.append("Demasiados errores, deteniendo inserción")
                break
    
    return {
        "success": errors == 0,
        "inserted": inserted,
        "skipped": skipped,
        "errors": errors,
        "error_messages": error_messages
    }


# =============================================================================
# GENERACIÓN DE REPORTE
# =============================================================================

def generate_report(
    config: Dict,
    fecha_inicio: str,
    fecha_fin: str,
    sales: List[Dict],
    dup_stats: Dict,
    items_stats: Dict,
    sync_sales_before: Dict,
    sync_sales_after: Dict,
    kpis_before: int,
    kpis_after: int,
    connection_status: str,
    importes_stats: Dict = None,
) -> Dict[str, Any]:
    """Genera reporte completo del dry-run."""
    
    server_config = config['server_config']
    
    # Calcular totales
    total_monto = sum(float(s.get("MontoTotal", 0) or 0) for s in sales)
    total_monto_items = sum(float(s.get("MontoItems", 0) or 0) for s in sales)
    total_pax = sum(int(s.get("Pax", 0) or 0) for s in sales)
    
    # Validación de importes si no se proporcionó
    if importes_stats is None:
        importes_stats = validate_importes(sales)
    
    # Determinar recomendación
    recomendacion = "EJECUTAR"
    razones_rechazo = []
    
    if dup_stats["nuevos"] == 0:
        recomendacion = "NO_EJECUTAR"
        razones_rechazo.append("No hay registros nuevos para insertar")
    
    if items_stats["invalidos"] > 0:
        recomendacion = "NO_EJECUTAR"
        razones_rechazo.append(f"{items_stats['invalidos']} items JSON inválidos")
    
    if connection_status != "OK":
        recomendacion = "NO_EJECUTAR"
        razones_rechazo.append(f"Problema de conexión: {connection_status}")
    
    if not importes_stats["valido"]:
        recomendacion = "RECHAZADO_IMPORTES"
        razones_rechazo.extend(importes_stats["errores"])
    
    report = {
        "timestamp": datetime.now().isoformat(),
        "unidad": {
            "codigo": config.get("unidad_codigo"),
            "nombre": config.get("unidad_nombre"),
            "server_id": config.get("server_id"),
        },
        "servidor": {
            "nombre": server_config.get("nombre"),
            "host": server_config.get("host_raw", server_config.get("host")),
            "database": server_config.get("database_name"),
            "system_type": server_config.get("system_type"),
            "usuario_status": "USUARIO_CONFIGURADO" if server_config.get("username") else "SIN_USUARIO",
            "password_status": "PASSWORD_CONFIGURADO" if server_config.get("password") else "SIN_PASSWORD",
        },
        "conexion": {
            "status": connection_status,
        },
        "rango": {
            "fecha_inicio": fecha_inicio,
            "fecha_fin": fecha_fin,
        },
        "extraccion": {
            "registros_leidos": len(sales),
            "monto_total": round(total_monto, 2),
            "monto_items_calculado": round(total_monto_items, 2),
            "pax_total": total_pax,
            "ticket_promedio": round(total_monto / len(sales), 2) if sales else 0,
        },
        "duplicados": {
            "nuevos_a_insertar": dup_stats["nuevos"],
            "duplicados_detectados": dup_stats["duplicados"],
        },
        "validacion_items": items_stats,
        "validacion_importes": importes_stats,
        "verificacion_tablas": {
            "sync_sales_antes": sync_sales_before,
            "sync_sales_despues": sync_sales_after,
            "sync_sales_sin_cambios": sync_sales_before.get('registros') == sync_sales_after.get('registros'),
            "kpis_antes": kpis_before,
            "kpis_despues": kpis_after,
            "kpis_sin_cambios": kpis_before == kpis_after,
        },
        "recomendacion": recomendacion,
        "razones_rechazo": razones_rechazo,
    }
    
    # Muestra anonimizada (5 registros)
    if sales:
        report["muestra_registros"] = []
        for i, sale in enumerate(sales[:5]):
            report["muestra_registros"].append({
                "idx": i + 1,
                "NumeroTicket": sale.get("NumeroTicket"),
                "MontoTotal": round(float(sale.get("MontoTotal", 0) or 0), 2),
                "MontoItems": round(float(sale.get("MontoItems", 0) or 0), 2),
                "Pax": int(sale.get("Pax", 0) or 0),
                "FechaHora": str(sale.get("FechaHora"))[:19],
                "items_valido": bool(sale.get("items")),
                "items_len": len(str(sale.get("items", ""))) if sale.get("items") else 0,
            })
    
    return report


def print_report(report: Dict[str, Any]):
    """Imprime el reporte de forma legible."""
    print()
    print("=" * 80)
    print("RESULTADO DRY-RUN: Sync_Sales")
    print("=" * 80)
    print()
    print(f"Timestamp: {report['timestamp']}")
    print()
    
    sections = [
        ("1. UNIDAD USADA", [
            f"Código: {report['unidad']['codigo']}",
            f"Nombre: {report['unidad']['nombre']}",
            f"Server ID: {report['unidad']['server_id']}",
        ]),
        ("2. SERVIDOR ORIGEN", [
            f"Nombre: {report['servidor']['nombre']}",
            f"Host: {report['servidor']['host']}",
            f"Database: {report['servidor']['database']}",
            f"Sistema: {report['servidor']['system_type']}",
            f"Usuario: {report['servidor']['usuario_status']}",
            f"Password: {report['servidor']['password_status']}",
        ]),
        ("3. ESTADO DE CONEXIÓN", [
            f"Status: {report['conexion']['status']}",
        ]),
        ("4. EXTRACCIÓN", [
            f"Rango: {report['rango']['fecha_inicio']} a {report['rango']['fecha_fin']}",
            f"Registros leídos: {report['extraccion']['registros_leidos']:,}",
            f"Monto total (encabezado): ${report['extraccion']['monto_total']:,.2f}",
            f"Monto items (calculado): ${report['extraccion'].get('monto_items_calculado', 0):,.2f}",
            f"PAX total: {report['extraccion']['pax_total']:,}",
            f"Ticket promedio: ${report['extraccion']['ticket_promedio']:,.2f}",
        ]),
        ("5. DUPLICADOS", [
            f"Nuevos (insertaría): {report['duplicados']['nuevos_a_insertar']:,}",
            f"Duplicados (skip): {report['duplicados']['duplicados_detectados']:,}",
        ]),
        ("6. VALIDACIÓN JSON ITEMS", [
            f"Válidos: {report['validacion_items']['validos']:,}",
            f"Nulos: {report['validacion_items']['nulos']:,}",
            f"Inválidos: {report['validacion_items']['invalidos']:,}",
        ]),
    ]
    
    for title, lines in sections:
        print("-" * 40)
        print(title)
        print("-" * 40)
        for line in lines:
            print(f"   {line}")
        print()
    
    # Validación de importes
    if report.get("validacion_importes"):
        vi = report["validacion_importes"]
        print("-" * 40)
        print("6b. VALIDACIÓN DE IMPORTES")
        print("-" * 40)
        print(f"   Válido: {'✅ SÍ' if vi['valido'] else '❌ NO'}")
        print(f"   Tickets con monto: {vi['tickets_con_monto']}")
        print(f"   Tickets sin monto: {vi['tickets_sin_monto']}")
        print(f"   Monto total global: ${vi['monto_total_global']:,.2f}")
        print(f"   Items con importe: {vi['items_con_importe']}")
        print(f"   Items sin importe: {vi['items_sin_importe']} ({vi['porcentaje_items_sin_importe']:.1f}%)")
        if vi.get("errores"):
            for err in vi["errores"]:
                print(f"   ⚠️  {err}")
        print()
    
    # Muestra de registros
    if report.get("muestra_registros"):
        print("-" * 40)
        print("7. MUESTRA ANONIMIZADA (5 registros)")
        print("-" * 40)
        for rec in report["muestra_registros"]:
            monto_items = rec.get('MontoItems', 0)
            print(f"   {rec['idx']}. Ticket #{rec['NumeroTicket']} | ${rec['MontoTotal']:,.2f} (items: ${monto_items:,.2f}) | PAX:{rec['Pax']} | {rec['FechaHora']}")
            print(f"      Items: {'✅ válido' if rec['items_valido'] else '❌ nulo'} ({rec['items_len']} chars)")
        print()
    
    # Verificación de tablas
    print("-" * 40)
    print("8. VERIFICACIÓN DE TABLAS")
    print("-" * 40)
    v = report['verificacion_tablas']
    print(f"   Sync_Sales antes: {v['sync_sales_antes'].get('registros', 0)} registros")
    print(f"   Sync_Sales después: {v['sync_sales_despues'].get('registros', 0)} registros")
    print(f"   Sync_Sales SIN CAMBIOS: {'✅ SÍ' if v['sync_sales_sin_cambios'] else '❌ NO'}")
    print()
    print(f"   KPIs_Diarios_v2 antes: {v['kpis_antes']} registros")
    print(f"   KPIs_Diarios_v2 después: {v['kpis_despues']} registros")
    print(f"   KPIs_Diarios_v2 SIN CAMBIOS: {'✅ SÍ' if v['kpis_sin_cambios'] else '❌ NO'}")
    print()
    
    # Recomendación
    print("=" * 80)
    recomendacion = report["recomendacion"]
    if recomendacion == "EJECUTAR":
        print("✅ RECOMENDACIÓN: EJECUTAR")
        print("   Ejecutar con el job oficial para insertar datos reales")
    elif recomendacion == "RECHAZADO_IMPORTES":
        print("❌ RECHAZADO: ERROR DE IMPORTES")
        for razon in report.get("razones_rechazo", []):
            print(f"   - {razon}")
    else:
        print("⚠️  RECOMENDACIÓN: NO EJECUTAR")
        for razon in report.get("razones_rechazo", []):
            print(f"   - {razon}")
    print("=" * 80)
    print()


# =============================================================================
# MAIN
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Sync_Sales Dry-Run Tool - Validación controlada"
    )
    parser.add_argument(
        "--unidad",
        required=True,
        help="Código de unidad de negocio (ej: CIENFUEGOS, 130QRO, ORIGEN)"
    )
    parser.add_argument(
        "--fecha-inicio",
        required=True,
        help="Fecha inicio (YYYY-MM-DD)"
    )
    parser.add_argument(
        "--fecha-fin",
        required=True,
        help="Fecha fin (YYYY-MM-DD) - inclusivo"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=True,
        help="Modo dry-run (default)"
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="NO IMPLEMENTADO - usar job oficial"
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Mostrar detalles adicionales"
    )
    parser.add_argument(
        "--output",
        "-o",
        help="Guardar reporte JSON en archivo"
    )
    
    args = parser.parse_args()
    
    # Modo de ejecución
    execute_mode = args.execute
    mode_str = "EXECUTE (INSERCIÓN REAL)" if execute_mode else "DRY-RUN (SOLO LECTURA)"
    
    logger.info("=" * 60)
    logger.info(f"SYNC_SALES - {mode_str}")
    logger.info("Patrón: sync_comercial_edarsahub.py")
    logger.info("=" * 60)
    logger.info(f"Unidad: {args.unidad}")
    logger.info(f"Rango: {args.fecha_inicio} a {args.fecha_fin}")
    if execute_mode:
        logger.info("⚠️  MODO EXECUTE: Se insertarán datos reales en Sync_Sales")
    logger.info("")
    
    # 1. Estado ANTES
    logger.info("Paso 1: Capturando estado ANTES...")
    sync_sales_before = get_sync_sales_count()
    kpis_before = get_kpis_count()
    logger.info(f"   Sync_Sales: {sync_sales_before.get('registros', 0)} registros")
    logger.info(f"   KPIs_Diarios_v2: {kpis_before} registros")
    
    # 2. Obtener configuración de unidad
    logger.info("")
    logger.info("Paso 2: Obteniendo configuración (Unidades_Negocio -> Servidores_Conexiones)...")
    config = get_unidad_config(args.unidad)
    if not config:
        logger.error(f"❌ No se pudo obtener configuración para {args.unidad}")
        sys.exit(1)
    
    server_config = config['server_config']
    logger.info(f"   Servidor: {server_config['nombre']}")
    logger.info(f"   Host: {server_config.get('host_raw', server_config.get('host'))}")
    logger.info(f"   Database: {server_config['database_name']}")
    logger.info(f"   Sistema: {server_config['system_type']}")
    logger.info(f"   Usuario: CONFIGURADO")
    logger.info(f"   Password: CONFIGURADO")
    
    # 3. Extraer datos del POS
    logger.info("")
    logger.info("Paso 3: Extrayendo datos del POS (usando execute_query_on_server)...")
    sales, connection_status = extract_sales_from_pos(config, args.fecha_inicio, args.fecha_fin)
    logger.info(f"   Estado: {connection_status}")
    logger.info(f"   Registros: {len(sales)}")
    
    # 4. Verificar duplicados
    logger.info("")
    logger.info("Paso 4: Verificando duplicados en Sync_Sales...")
    dup_stats = check_duplicates_in_sync_sales(sales)
    logger.info(f"   Nuevos: {dup_stats['nuevos']}")
    logger.info(f"   Duplicados: {dup_stats['duplicados']}")
    
    # 5. Validar JSON items
    logger.info("")
    logger.info("Paso 5: Validando estructura JSON items...")
    items_stats = validate_json_items(sales)
    logger.info(f"   Válidos: {items_stats['validos']}")
    logger.info(f"   Nulos: {items_stats['nulos']}")
    logger.info(f"   Inválidos: {items_stats['invalidos']}")
    
    # 5b. Validar importes
    logger.info("")
    logger.info("Paso 5b: Validando integridad de importes...")
    importes_stats = validate_importes(sales)
    logger.info(f"   Válido: {'✅ SÍ' if importes_stats['valido'] else '❌ NO'}")
    logger.info(f"   Tickets con monto: {importes_stats['tickets_con_monto']}")
    logger.info(f"   Tickets sin monto: {importes_stats['tickets_sin_monto']}")
    logger.info(f"   Monto total: ${importes_stats['monto_total_global']:,.2f}")
    logger.info(f"   Items con importe: {importes_stats['items_con_importe']}")
    logger.info(f"   Items sin importe: {importes_stats['items_sin_importe']}")
    if importes_stats.get("errores"):
        for err in importes_stats["errores"]:
            logger.warning(f"   ⚠️ {err}")
    
    # 6. EXECUTE: Insertar datos si está habilitado
    insert_stats = None
    if execute_mode:
        logger.info("")
        logger.info("=" * 60)
        logger.info("PASO 6: EJECUTANDO INSERCIÓN EN Sync_Sales")
        logger.info("=" * 60)
        
        # Validaciones previas a inserción
        if not importes_stats['valido']:
            logger.error("❌ ABORTADO: Validación de importes falló")
            logger.error("   No se puede insertar con monto total = 0")
            sys.exit(1)
        
        if items_stats['invalidos'] > 0:
            logger.error("❌ ABORTADO: Hay items JSON inválidos")
            sys.exit(1)
        
        if dup_stats['nuevos'] == 0:
            logger.warning("⚠️ No hay registros nuevos para insertar (todos duplicados)")
        else:
            logger.info(f"   Insertando {dup_stats['nuevos']} registros nuevos...")
            insert_stats = insert_sales_to_sync_sales(sales, config['unidad_codigo'])
            
            logger.info(f"   ✅ Insertados: {insert_stats['inserted']}")
            logger.info(f"   ⏭️  Skipped (duplicados): {insert_stats['skipped']}")
            logger.info(f"   ❌ Errores: {insert_stats['errors']}")
            
            if insert_stats['error_messages']:
                for msg in insert_stats['error_messages']:
                    logger.error(f"      {msg}")
            
            if not insert_stats['success']:
                logger.error("❌ INSERCIÓN FALLÓ - Revisar errores arriba")
                sys.exit(1)
    
    # 7. Estado DESPUÉS
    logger.info("")
    logger.info("Paso 7: Verificando estado de tablas...")
    sync_sales_after = get_sync_sales_count()
    kpis_after = get_kpis_count()
    
    if execute_mode:
        logger.info(f"   Sync_Sales ANTES: {sync_sales_before.get('registros', 0)} registros")
        logger.info(f"   Sync_Sales DESPUÉS: {sync_sales_after.get('registros', 0)} registros")
        logger.info(f"   Diferencia: +{sync_sales_after.get('registros', 0) - sync_sales_before.get('registros', 0)}")
    
    logger.info(f"   KPIs_Diarios_v2 ANTES: {kpis_before} registros")
    logger.info(f"   KPIs_Diarios_v2 DESPUÉS: {kpis_after} registros")
    logger.info(f"   KPIs SIN CAMBIOS: {'✅ SÍ' if kpis_before == kpis_after else '❌ NO'}")
    
    # 8. Generar reporte
    logger.info("")
    logger.info("Paso 8: Generando reporte...")
    report = generate_report(
        config=config,
        fecha_inicio=args.fecha_inicio,
        fecha_fin=args.fecha_fin,
        sales=sales,
        dup_stats=dup_stats,
        items_stats=items_stats,
        sync_sales_before=sync_sales_before,
        sync_sales_after=sync_sales_after,
        kpis_before=kpis_before,
        kpis_after=kpis_after,
        connection_status=connection_status,
        importes_stats=importes_stats,
    )
    
    # Agregar stats de inserción al reporte si aplica
    if insert_stats:
        report["insercion"] = insert_stats
        report["modo"] = "EXECUTE"
    else:
        report["modo"] = "DRY-RUN"
    
    # Imprimir reporte
    print_report(report)
    
    # Resumen final para execute
    if execute_mode and insert_stats:
        print()
        print("=" * 80)
        print(f"✅ INSERCIÓN COMPLETADA: {args.unidad}")
        print(f"   Registros insertados: {insert_stats['inserted']}")
        print(f"   Sync_Sales ahora tiene: {sync_sales_after.get('registros', 0)} registros")
        print("=" * 80)
    
    # Guardar JSON si se especificó
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False, default=str)
        logger.info(f"Reporte JSON guardado en: {args.output}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
