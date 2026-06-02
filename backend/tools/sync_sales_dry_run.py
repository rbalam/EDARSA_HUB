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
    'host': '54.39.104.176',
    'port': 1433,
    'database': 'EDARSAHUB',
    'username': 'HRLectura',
    'password': 'National09$'
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

# Unidades permitidas (solo SoftRestaurant con credenciales completas)
UNIDADES_PERMITIDAS = ["CIENFUEGOS", "130MID", "ESTELAR"]


# =============================================================================
# FUNCIONES DE CONFIGURACIÓN (usando patrón de sync_comercial_edarsahub.py)
# =============================================================================

def get_unidad_config(unidad_codigo: str) -> Optional[Dict[str, Any]]:
    """
    Obtiene la configuración completa de una unidad.
    Patrón: Unidades_Negocio -> server_id -> Servidores_Conexiones
    """
    # Mapeo de códigos a nombres en Unidades_Negocio
    nombre_map = {
        "CIENFUEGOS": "CIENFUEGOS",
        "130MID": "130° MERIDA",
        "ESTELAR": "LA ESTELAR",
    }
    
    nombre_buscar = nombre_map.get(unidad_codigo, unidad_codigo)
    
    # 1. Buscar en Unidades_Negocio
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
    WHERE nombre LIKE '%{nombre_buscar}%'
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
        
        # 2. Obtener configuración del servidor usando la función del módulo
        server_config = get_server_connection_config(str(server_id))
        if not server_config:
            logger.error(f"No se pudo obtener configuración del servidor {server_id}")
            return None
        
        # Verificar credenciales
        if not server_config.get('username') or not server_config.get('password'):
            logger.error(f"Servidor {server_config.get('nombre')} no tiene credenciales")
            return None
        
        # 3. Combinar información
        return {
            "unidad_id": str(unidad['id']),
            "unidad_codigo": unidad.get('codigo') or unidad_codigo,
            "unidad_nombre": unidad['nombre'],
            "server_id": str(server_id),
            "server_config": server_config,  # Config completa del servidor
        }
        
    except Exception as e:
        logger.error(f"Error obteniendo config de unidad {unidad_codigo}: {e}")
        return None


# =============================================================================
# QUERIES DE EXTRACCIÓN
# =============================================================================

def get_softrestaurant_query(fecha_inicio: str, fecha_fin: str) -> str:
    """Query para extraer ventas cerradas de SoftRestaurant."""
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
    WHERE CAST(t.apertura AS DATE) >= '{fecha_inicio}'
      AND CAST(t.apertura AS DATE) <= '{fecha_fin}'
      AND ch.cancelado = 0
      AND ch.total > 0
    ORDER BY t.apertura DESC
    """


# =============================================================================
# FUNCIONES DE EXTRACCIÓN (usando execute_query_on_server del módulo)
# =============================================================================

def extract_sales_from_pos(config: Dict, fecha_inicio: str, fecha_fin: str) -> Tuple[List[Dict], str]:
    """
    Extrae ventas de un POS usando execute_query_on_server del módulo comercial_v2.
    Retorna (registros, connection_status)
    """
    server_config = config['server_config']
    system_type = server_config.get('system_type', '').upper()
    
    # Solo SoftRestaurant por ahora
    if 'SOFT' not in system_type:
        logger.error(f"Sistema {system_type} no soportado en esta versión")
        return [], "SISTEMA_NO_SOPORTADO"
    
    # Construir query
    query = get_softrestaurant_query(fecha_inicio, fecha_fin)
    
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
    
    # Agregar unidad de negocio a cada registro
    for row in rows:
        row["UnidadNegocio"] = config["unidad_codigo"]
    
    logger.info(f"✅ {len(rows)} registros extraídos")
    
    return rows, connection_status


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
) -> Dict[str, Any]:
    """Genera reporte completo del dry-run."""
    
    server_config = config['server_config']
    
    # Calcular totales
    total_monto = sum(float(s.get("MontoTotal", 0) or 0) for s in sales)
    total_pax = sum(int(s.get("Pax", 0) or 0) for s in sales)
    
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
            "pax_total": total_pax,
            "ticket_promedio": round(total_monto / len(sales), 2) if sales else 0,
        },
        "duplicados": {
            "nuevos_a_insertar": dup_stats["nuevos"],
            "duplicados_detectados": dup_stats["duplicados"],
        },
        "validacion_items": items_stats,
        "verificacion_tablas": {
            "sync_sales_antes": sync_sales_before,
            "sync_sales_despues": sync_sales_after,
            "sync_sales_sin_cambios": sync_sales_before.get('registros') == sync_sales_after.get('registros'),
            "kpis_antes": kpis_before,
            "kpis_despues": kpis_after,
            "kpis_sin_cambios": kpis_before == kpis_after,
        },
        "recomendacion": "EJECUTAR" if (
            dup_stats["nuevos"] > 0 and 
            items_stats["invalidos"] == 0 and
            connection_status == "OK"
        ) else "NO_EJECUTAR",
    }
    
    # Muestra anonimizada (5 registros)
    if sales:
        report["muestra_registros"] = []
        for i, sale in enumerate(sales[:5]):
            report["muestra_registros"].append({
                "idx": i + 1,
                "NumeroTicket": sale.get("NumeroTicket"),
                "MontoTotal": round(float(sale.get("MontoTotal", 0) or 0), 2),
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
            f"Monto total: ${report['extraccion']['monto_total']:,.2f}",
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
    
    # Muestra de registros
    if report.get("muestra_registros"):
        print("-" * 40)
        print("7. MUESTRA ANONIMIZADA (5 registros)")
        print("-" * 40)
        for rec in report["muestra_registros"]:
            print(f"   {rec['idx']}. Ticket #{rec['NumeroTicket']} | ${rec['MontoTotal']:,.2f} | PAX:{rec['Pax']} | {rec['FechaHora']}")
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
    if report["recomendacion"] == "EJECUTAR":
        print("✅ RECOMENDACIÓN: EJECUTAR")
        print("   Ejecutar con el job oficial para insertar datos reales")
    else:
        print("⚠️  RECOMENDACIÓN: NO EJECUTAR")
        if report['duplicados']['nuevos_a_insertar'] == 0:
            print("   - No hay registros nuevos para insertar")
        if report['validacion_items']['invalidos'] > 0:
            print("   - Hay items JSON inválidos")
        if report['conexion']['status'] != "OK":
            print(f"   - Problema de conexión: {report['conexion']['status']}")
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
        choices=UNIDADES_PERMITIDAS,
        help="Unidad de negocio (solo SoftRestaurant con credenciales)"
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
    
    if args.execute:
        logger.error("❌ --execute no está disponible en este script de diagnóstico")
        logger.error("   Use el job oficial sync_comercial_edarsahub.py para inserción real")
        sys.exit(1)
    
    logger.info("=" * 60)
    logger.info("SYNC_SALES DRY-RUN")
    logger.info("Patrón: sync_comercial_edarsahub.py")
    logger.info("=" * 60)
    logger.info(f"Unidad: {args.unidad}")
    logger.info(f"Rango: {args.fecha_inicio} a {args.fecha_fin}")
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
    
    # 6. Estado DESPUÉS (debe ser igual)
    logger.info("")
    logger.info("Paso 6: Verificando que las tablas NO cambiaron...")
    sync_sales_after = get_sync_sales_count()
    kpis_after = get_kpis_count()
    
    # 7. Generar reporte
    logger.info("")
    logger.info("Paso 7: Generando reporte...")
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
    )
    
    # Imprimir reporte
    print_report(report)
    
    # Guardar JSON si se especificó
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False, default=str)
        logger.info(f"Reporte JSON guardado en: {args.output}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
