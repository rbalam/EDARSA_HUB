#!/usr/bin/env python3
"""
SYNC_SALES DRY-RUN TOOL
=======================
Herramienta de diagnóstico para validar extracción de tickets
hacia Sync_Sales SIN insertar datos.

Patrón de conexión: Igual que sync_comercial_edarsahub.py
- Lee Unidades_Negocio para resolver server_id
- Lee Servidores_Conexiones para credenciales
- Descifra password con core.secret_manager.decrypt_secret()
- NO usa hardcoded ni variables de entorno

Uso:
    python3 sync_sales_dry_run.py --unidad CIENFUEGOS --fecha-inicio 2026-06-01 --fecha-fin 2026-06-02 --dry-run

Autor: Agente E1
Fecha: 2026-06-02
"""

import argparse
import json
import logging
import os
import sys
from datetime import datetime
from typing import Dict, List, Optional, Any

# Agregar backend al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pymssql

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# =============================================================================
# CONFIGURACIÓN EDARSAHUB (Destino)
# =============================================================================

EDARSAHUB_CONFIG = {
    "host": os.environ.get("EDARSAHUB_HOST", "54.39.104.176"),
    "port": int(os.environ.get("EDARSAHUB_PORT", "1433")),
    "database": os.environ.get("EDARSAHUB_DATABASE", "EDARSAHUB"),
    "user": os.environ.get("EDARSAHUB_USERNAME", "HRLectura"),
    "password": os.environ.get("EDARSAHUB_PASSWORD", "National09$"),
}

# Mapeo de códigos de unidad a nombres canónicos
UNIDADES_PERMITIDAS = ["CIENFUEGOS", "130MID", "ESTELAR"]  # Solo SoftRestaurant con credenciales

# =============================================================================
# FUNCIONES DE CONEXIÓN Y CONFIGURACIÓN
# =============================================================================

def get_edarsahub_connection():
    """Conexión a EDARSAHUB (destino)."""
    return pymssql.connect(
        server=EDARSAHUB_CONFIG["host"],
        port=EDARSAHUB_CONFIG["port"],
        user=EDARSAHUB_CONFIG["user"],
        password=EDARSAHUB_CONFIG["password"],
        database=EDARSAHUB_CONFIG["database"],
        timeout=60,
        login_timeout=15,
        autocommit=False,
        as_dict=True
    )


def execute_edarsahub_query(query: str) -> List[Dict]:
    """Ejecuta query en EDARSAHUB."""
    conn = get_edarsahub_connection()
    cursor = conn.cursor()
    cursor.execute(query)
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows


def get_unidad_config(unidad_codigo: str) -> Optional[Dict[str, Any]]:
    """
    Obtiene la configuración de una unidad desde Unidades_Negocio y Servidores_Conexiones.
    Patrón igual a sync_comercial_edarsahub.py.
    """
    # Mapeo de códigos a nombres en Unidades_Negocio
    nombre_map = {
        "CIENFUEGOS": "CIENFUEGOS",
        "130MID": "130° MERIDA",
        "ESTELAR": "LA ESTELAR",
    }
    
    nombre_buscar = nombre_map.get(unidad_codigo, unidad_codigo)
    
    # 1. Buscar en Unidades_Negocio para obtener server_id
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
        unidades = execute_edarsahub_query(query_unidad)
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
        
        # 2. Obtener configuración del servidor
        server_config = get_server_connection_config(server_id)
        if not server_config:
            logger.error(f"No se pudo obtener configuración del servidor {server_id}")
            return None
        
        # 3. Combinar información
        return {
            "unidad_id": str(unidad['id']),
            "unidad_codigo": unidad.get('codigo') or unidad_codigo,
            "unidad_nombre": unidad['nombre'],
            "server_id": server_id,
            "server_nombre": server_config['nombre'],
            "system_type": server_config['system_type'],
            "host": server_config['host'],
            "host_raw": server_config['host_raw'],
            "port": server_config['port'],
            "database": server_config['database_name'],
            "username": server_config['username'],
            "password": server_config['password'],
            "has_credentials": bool(server_config['username'] and server_config['password']),
        }
        
    except Exception as e:
        logger.error(f"Error obteniendo config de unidad {unidad_codigo}: {e}")
        return None


def get_server_connection_config(server_id: str) -> Optional[Dict[str, Any]]:
    """
    Obtiene la configuración de conexión de un servidor desde Servidores_Conexiones.
    Patrón copiado de sync_comercial_edarsahub.py.
    """
    # Importar decrypt_secret
    try:
        from core.secret_manager import decrypt_secret
    except ImportError:
        logger.warning("No se pudo importar decrypt_secret, usando fallback")
        decrypt_secret = lambda x: x
    
    # Importar parse_sql_server_host
    try:
        from core.db import parse_sql_server_host
    except ImportError:
        def parse_sql_server_host(host, default_port):
            # Parseo básico
            if ',' in host:
                parts = host.split(',')
                h = parts[0]
                p = int(parts[1].split('\\')[0]) if len(parts) > 1 else default_port
                return (h, p, None)
            return (host, default_port, None)
    
    query = f"""
    SELECT 
        id,
        nombre,
        host,
        port,
        database_name,
        username,
        password_encrypted,
        system_type,
        activo
    FROM Servidores_Conexiones
    WHERE id = '{server_id}'
    """
    
    try:
        rows = execute_edarsahub_query(query)
        if not rows:
            logger.error(f"Servidor {server_id} no encontrado en Servidores_Conexiones")
            return None
        
        row = rows[0]
        
        # Verificar que tenga credenciales
        if not row.get('username') or not row.get('password_encrypted'):
            logger.error(f"Servidor {row['nombre']} no tiene credenciales configuradas")
            return None
        
        # Descifrar password
        pwd_enc = row.get('password_encrypted', '')
        try:
            password = decrypt_secret(pwd_enc)
            logger.info("Password descifrada correctamente")
        except Exception as e:
            logger.warning(f"Error descifrando password: {e}, usando valor original")
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
            'database_name': row['database_name'],
            'username': row['username'],
            'password': password,
            'system_type': row['system_type'],
            'activo': row['activo']
        }
        
    except Exception as e:
        logger.error(f"Error obteniendo config de servidor {server_id}: {e}")
        return None


# =============================================================================
# QUERIES DE EXTRACCIÓN
# =============================================================================

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
    WHERE CAST(t.apertura AS DATE) >= '{fecha_inicio}'
      AND CAST(t.apertura AS DATE) <= '{fecha_fin}'
      AND ch.cancelado = 0
      AND ch.total > 0
    ORDER BY t.apertura DESC
    """


# =============================================================================
# FUNCIONES DE EXTRACCIÓN Y CONEXIÓN POS
# =============================================================================

def connect_to_pos(config: Dict) -> Optional[pymssql.Connection]:
    """Conecta a un servidor POS usando la configuración obtenida."""
    try:
        # Construir server string con instancia si existe
        server = config['host_raw'] if config.get('host_raw') else config['host']
        
        logger.info(f"Conectando a POS: {server}/{config['database']}")
        
        conn = pymssql.connect(
            server=server,
            port=config.get('port', 1433),
            user=config['username'],
            password=config['password'],
            database=config['database'],
            timeout=30,
            login_timeout=15,
            as_dict=True
        )
        
        logger.info("✅ Conexión a POS exitosa")
        return conn
        
    except Exception as e:
        logger.error(f"❌ Error conectando a POS: {e}")
        return None


def extract_sales_from_pos(config: Dict, fecha_inicio: str, fecha_fin: str) -> List[Dict]:
    """Extrae ventas de un POS específico."""
    
    conn = connect_to_pos(config)
    if not conn:
        return []
    
    try:
        cursor = conn.cursor()
        
        # Solo SoftRestaurant por ahora
        if 'SOFT' in config.get('system_type', '').upper():
            query = get_softrestaurant_query(fecha_inicio, fecha_fin)
        else:
            logger.error(f"Sistema {config['system_type']} no soportado en esta versión")
            return []
        
        logger.info(f"Ejecutando query de extracción para rango {fecha_inicio} a {fecha_fin}...")
        cursor.execute(query)
        rows = cursor.fetchall()
        
        # Agregar unidad de negocio a cada registro
        for row in rows:
            row["UnidadNegocio"] = config["unidad_codigo"]
        
        logger.info(f"✅ {len(rows)} registros extraídos del POS")
        
        cursor.close()
        conn.close()
        
        return rows
        
    except Exception as e:
        logger.error(f"Error extrayendo datos: {e}")
        return []


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
    rows = execute_edarsahub_query(query)
    return rows[0] if rows else {}


def get_kpis_count() -> int:
    """Obtiene el conteo de Comercial_KPIs_Diarios_v2."""
    query = "SELECT COUNT(*) AS total FROM Comercial_KPIs_Diarios_v2"
    rows = execute_edarsahub_query(query)
    return rows[0]['total'] if rows else 0


def check_duplicates_in_sync_sales(sales: List[Dict]) -> Dict[str, int]:
    """Verifica cuántos registros ya existen en Sync_Sales."""
    conn = get_edarsahub_connection()
    cursor = conn.cursor()
    stats = {"nuevos": 0, "duplicados": 0}
    
    for sale in sales:
        cursor.execute("""
            SELECT COUNT(*) AS cnt FROM Sync_Sales 
            WHERE NumeroTicket = %s AND UnidadNegocio = %s 
              AND CAST(FechaHora AS DATE) = CAST(%s AS DATE)
        """, (sale["NumeroTicket"], sale["UnidadNegocio"], sale["FechaHora"]))
        
        result = cursor.fetchone()
        if result['cnt'] > 0:
            stats["duplicados"] += 1
        else:
            stats["nuevos"] += 1
    
    cursor.close()
    conn.close()
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
    verbose: bool = False
) -> Dict[str, Any]:
    """Genera reporte completo del dry-run."""
    
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
            "nombre": config.get("server_nombre"),
            "host": config.get("host_raw"),
            "database": config.get("database"),
            "usuario_status": "USUARIO_CONFIGURADO" if config.get("username") else "SIN_USUARIO",
            "password_status": "PASSWORD_CONFIGURADO" if config.get("password") else "SIN_PASSWORD",
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
            "sync_sales_sin_cambios": sync_sales_before == sync_sales_after,
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
    
    # Muestra anonimizada
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
    
    print("-" * 40)
    print("1. UNIDAD USADA")
    print("-" * 40)
    print(f"   Código: {report['unidad']['codigo']}")
    print(f"   Nombre: {report['unidad']['nombre']}")
    print(f"   Server ID: {report['unidad']['server_id']}")
    print()
    
    print("-" * 40)
    print("2. SERVIDOR ORIGEN")
    print("-" * 40)
    print(f"   Nombre: {report['servidor']['nombre']}")
    print(f"   Host: {report['servidor']['host']}")
    print(f"   Database: {report['servidor']['database']}")
    print(f"   Usuario: {report['servidor']['usuario_status']}")
    print(f"   Password: {report['servidor']['password_status']}")
    print()
    
    print("-" * 40)
    print("3. ESTADO DE CONEXIÓN")
    print("-" * 40)
    print(f"   Status: {report['conexion']['status']}")
    print()
    
    print("-" * 40)
    print("4. EXTRACCIÓN")
    print("-" * 40)
    print(f"   Rango: {report['rango']['fecha_inicio']} a {report['rango']['fecha_fin']}")
    print(f"   Registros leídos: {report['extraccion']['registros_leidos']:,}")
    print(f"   Monto total: ${report['extraccion']['monto_total']:,.2f}")
    print(f"   PAX total: {report['extraccion']['pax_total']:,}")
    print(f"   Ticket promedio: ${report['extraccion']['ticket_promedio']:,.2f}")
    print()
    
    print("-" * 40)
    print("5. DUPLICADOS")
    print("-" * 40)
    print(f"   Nuevos (insertaría): {report['duplicados']['nuevos_a_insertar']:,}")
    print(f"   Duplicados (skip): {report['duplicados']['duplicados_detectados']:,}")
    print()
    
    print("-" * 40)
    print("6. VALIDACIÓN JSON ITEMS")
    print("-" * 40)
    print(f"   Válidos: {report['validacion_items']['validos']:,}")
    print(f"   Nulos: {report['validacion_items']['nulos']:,}")
    print(f"   Inválidos: {report['validacion_items']['invalidos']:,}")
    print()
    
    if report.get("muestra_registros"):
        print("-" * 40)
        print("7. MUESTRA ANONIMIZADA (5 registros)")
        print("-" * 40)
        for rec in report["muestra_registros"]:
            print(f"   {rec['idx']}. Ticket #{rec['NumeroTicket']} | ${rec['MontoTotal']:,.2f} | PAX:{rec['Pax']} | {rec['FechaHora']}")
            print(f"      Items: {'✅ válido' if rec['items_valido'] else '❌ nulo'} ({rec['items_len']} chars)")
        print()
    
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
    
    print("=" * 80)
    if report["recomendacion"] == "EJECUTAR":
        print("✅ RECOMENDACIÓN: EJECUTAR")
        print("   Ejecutar con --execute para insertar datos reales")
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
        help="Ejecutar inserción real (NO IMPLEMENTADO AÚN)"
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
        logger.error("❌ --execute no está implementado en esta versión de dry-run")
        logger.error("   Este script es solo para validación. La inserción real")
        logger.error("   debe hacerse con el job oficial después de aprobar el dry-run.")
        sys.exit(1)
    
    logger.info("=" * 60)
    logger.info("SYNC_SALES DRY-RUN")
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
    logger.info("Paso 2: Obteniendo configuración de unidad...")
    config = get_unidad_config(args.unidad)
    if not config:
        logger.error(f"❌ No se pudo obtener configuración para {args.unidad}")
        sys.exit(1)
    
    if not config.get("has_credentials"):
        logger.error(f"❌ Servidor {config.get('server_nombre')} no tiene credenciales configuradas")
        sys.exit(1)
    
    logger.info(f"   Servidor: {config['server_nombre']}")
    logger.info(f"   Host: {config['host_raw']}")
    logger.info(f"   Database: {config['database']}")
    logger.info(f"   Usuario: CONFIGURADO")
    logger.info(f"   Password: CONFIGURADO")
    
    # 3. Extraer datos del POS
    logger.info("")
    logger.info("Paso 3: Extrayendo datos del POS...")
    connection_status = "ERROR"
    sales = []
    
    try:
        sales = extract_sales_from_pos(config, args.fecha_inicio, args.fecha_fin)
        connection_status = "OK" if sales or True else "NO_DATA"  # OK aunque no haya datos
        if not sales:
            logger.warning("   No se encontraron registros en el rango especificado")
            connection_status = "OK_NO_DATA"
    except Exception as e:
        logger.error(f"   Error: {e}")
        connection_status = f"ERROR: {str(e)[:50]}"
    
    # 4. Verificar duplicados
    logger.info("")
    logger.info("Paso 4: Verificando duplicados en Sync_Sales...")
    dup_stats = check_duplicates_in_sync_sales(sales) if sales else {"nuevos": 0, "duplicados": 0}
    logger.info(f"   Nuevos: {dup_stats['nuevos']}")
    logger.info(f"   Duplicados: {dup_stats['duplicados']}")
    
    # 5. Validar JSON items
    logger.info("")
    logger.info("Paso 5: Validando estructura JSON items...")
    items_stats = validate_json_items(sales) if sales else {"validos": 0, "nulos": 0, "invalidos": 0}
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
        verbose=args.verbose
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
