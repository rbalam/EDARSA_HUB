#!/usr/bin/env python3
"""
SYNC_SALES DRY-RUN TOOL
=======================
Herramienta de diagnóstico para validar extracción de tickets
hacia Sync_Sales SIN insertar datos.

Uso:
    python3 sync_sales_dry_run.py --unidad CIENFUEGOS --fecha-inicio 2026-06-01 --fecha-fin 2026-06-02 --dry-run
    python3 sync_sales_dry_run.py --unidad CIENFUEGOS --fecha-inicio 2026-06-01 --fecha-fin 2026-06-02 --execute

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

import pymssql

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# =============================================================================
# CONFIGURACIÓN
# =============================================================================

EDARSAHUB_CONFIG = {
    "host": os.environ.get("EDARSAHUB_HOST", "54.39.104.176"),
    "port": int(os.environ.get("EDARSAHUB_PORT", "1433")),
    "database": os.environ.get("EDARSAHUB_DATABASE", "EDARSAHUB"),
    "user": os.environ.get("EDARSAHUB_USERNAME", "HRLectura"),
    "password": os.environ.get("EDARSAHUB_PASSWORD", "National09$"),
}

# Mapeo de unidades a nombres en Servidores_Conexiones
UNIDAD_TO_SERVIDOR = {
    "CIENFUEGOS": "CIENFUEGOS",
    "130MID": "130° MERIDA",
    "ESTELAR": "LA ESTELAR",
    "130QRO": "ManagmentPro",  # MPRO usa el servidor central
    "ORIGEN": "ManagmentPro",
}

# Mapeo de system_type
SYSTEM_TYPE_MAP = {
    "SOFTRESTAURANT_PRO": "SoftRestaurant",
    "SOFTRESTAURANT": "SoftRestaurant",
    "MPRO": "MPRO",
}


def get_servidor_config_from_db(servidor_nombre: str) -> Optional[Dict]:
    """Obtiene configuración del servidor desde Servidores_Conexiones."""
    try:
        conn = pymssql.connect(
            server=EDARSAHUB_CONFIG["host"],
            port=EDARSAHUB_CONFIG["port"],
            user=EDARSAHUB_CONFIG["user"],
            password=EDARSAHUB_CONFIG["password"],
            database=EDARSAHUB_CONFIG["database"],
            as_dict=True
        )
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                nombre,
                host,
                port,
                database_name,
                username,
                password_encrypted,
                system_type
            FROM Servidores_Conexiones
            WHERE nombre = %s AND activo = 1
        """, (servidor_nombre,))
        
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if not row:
            return None
        
        # Descifrar password
        password = row['password_encrypted']
        try:
            # Intentar descifrar si está cifrada
            sys.path.insert(0, '/app/backend')
            from core.secret_manager import decrypt_secret
            password = decrypt_secret(password)
        except:
            # Si falla, usar como texto plano
            pass
        
        system_type = SYSTEM_TYPE_MAP.get(row['system_type'], row['system_type'])
        
        return {
            "system_type": system_type,
            "host": row['host'],
            "port": row['port'] or 1433,
            "database": row['database_name'],
            "username": row['username'],
            "password": password,
        }
        
    except Exception as e:
        logger.error(f"Error obteniendo config de {servidor_nombre}: {e}")
        return None


def get_unidad_config(unidad: str) -> Optional[Dict]:
    """Obtiene configuración de unidad desde BD."""
    servidor_nombre = UNIDAD_TO_SERVIDOR.get(unidad)
    if not servidor_nombre:
        logger.error(f"Unidad {unidad} no mapeada a servidor")
        return None
    
    config = get_servidor_config_from_db(servidor_nombre)
    if not config:
        logger.error(f"No se encontró configuración para servidor {servidor_nombre}")
        return None
    
    return config

# =============================================================================
# QUERIES
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
    WHERE t.apertura >= '{fecha_inicio}'
      AND t.apertura < '{fecha_fin}'
      AND ch.cancelado = 0
      AND ch.total > 0
    ORDER BY t.apertura DESC
    """


def get_mpro_query(fecha_inicio: str, fecha_fin: str) -> str:
    """Query para extraer ventas de MPRO."""
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


# =============================================================================
# FUNCIONES DE CONEXIÓN
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
        autocommit=False
    )


def get_pos_connection(config: Dict) -> Optional[pymssql.Connection]:
    """Conexión a servidor POS origen."""
    try:
        logger.info(f"Conectando a {config['host']}:{config['port']}/{config['database']}...")
        return pymssql.connect(
            server=config["host"],
            port=config["port"],
            user=config["username"],
            password=config["password"],
            database=config["database"],
            timeout=30,
            login_timeout=10
        )
    except Exception as e:
        logger.error(f"Error conectando a POS: {e}")
        return None


# =============================================================================
# FUNCIONES DE EXTRACCIÓN
# =============================================================================

def extract_sales_from_pos(
    unidad: str,
    config: Dict,
    fecha_inicio: str,
    fecha_fin: str
) -> List[Dict]:
    """Extrae ventas de un POS específico."""
    
    conn = get_pos_connection(config)
    if not conn:
        return []
    
    try:
        cursor = conn.cursor(as_dict=True)
        
        # Seleccionar query según sistema
        if config["system_type"] == "SoftRestaurant":
            query = get_softrestaurant_query(fecha_inicio, fecha_fin)
        else:  # MPRO
            query = get_mpro_query(fecha_inicio, fecha_fin)
        
        logger.info(f"Ejecutando query para {unidad}...")
        cursor.execute(query)
        rows = cursor.fetchall()
        
        # Agregar unidad de negocio a cada registro
        for row in rows:
            row["UnidadNegocio"] = unidad
        
        logger.info(f"{unidad}: {len(rows)} registros extraídos")
        
        cursor.close()
        conn.close()
        
        return rows
        
    except Exception as e:
        logger.error(f"Error extrayendo de {unidad}: {e}")
        return []



def simulate_extraction_from_kpis(unidad: str, fecha_inicio: str, fecha_fin: str) -> List[Dict]:
    """
    Genera datos simulados basados en KPIs existentes.
    Útil para validar estructura sin conectar a POS.
    """
    try:
        conn = get_edarsahub_connection()
        cursor = conn.cursor(as_dict=True)
        
        # Mapeo de unidad a nombre en KPIs
        nombre_map = {
            "CIENFUEGOS": "CIENFUEGOS",
            "130MID": "130° MERIDA",
            "ESTELAR": "LA ESTELAR",
            "130QRO": "130° QUERETARO",
            "ORIGEN": "ORIGEN",
        }
        
        nombre_kpi = nombre_map.get(unidad, unidad)
        
        cursor.execute("""
            SELECT 
                unidad_negocio_nombre,
                fecha_operacion,
                tickets_total,
                ventas_total,
                pax_total
            FROM Comercial_KPIs_Diarios_v2
            WHERE unidad_negocio_nombre LIKE %s
              AND fecha_operacion >= %s
              AND fecha_operacion < %s
        """, (f"%{nombre_kpi}%", fecha_inicio, fecha_fin))
        
        kpis = cursor.fetchall()
        cursor.close()
        conn.close()
        
        if not kpis:
            logger.warning(f"No hay KPIs para {nombre_kpi} en el rango especificado")
            return []
        
        # Generar registros simulados
        sales = []
        for kpi in kpis:
            tickets = int(kpi['tickets_total'] or 1)
            ventas = float(kpi['ventas_total'] or 0)
            pax = int(kpi['pax_total'] or 0)
            
            # Simular distribución de tickets
            ticket_promedio = ventas / tickets if tickets > 0 else 0
            pax_promedio = pax // tickets if tickets > 0 else 1
            
            for i in range(min(tickets, 100)):  # Limitar a 100 para simulación
                sales.append({
                    "IdTransaccion": f"SIM-{unidad}-{kpi['fecha_operacion']}-{i+1}",
                    "UnidadNegocio": unidad,
                    "NumeroTicket": f"SIM{i+1:06d}",
                    "MontoTotal": round(ticket_promedio * (0.8 + 0.4 * (i % 5) / 4), 2),  # Variación
                    "Pax": max(1, pax_promedio + (i % 3) - 1),
                    "FechaHora": kpi['fecha_operacion'],
                    "status": "COMPLETED",
                    "items": '[{"id": "SIM001", "name": "Producto Simulado", "quantity": 1, "price": 100, "total": 100}]'
                })
        
        logger.info(f"[SIMULACIÓN] Generados {len(sales)} registros basados en KPIs")
        return sales
        
    except Exception as e:
        logger.error(f"Error en simulación: {e}")
        return []



def check_existing_in_sync_sales(conn, sales: List[Dict]) -> Dict[str, int]:
    """Verifica cuántos registros ya existen en Sync_Sales."""
    cursor = conn.cursor()
    stats = {"nuevos": 0, "duplicados": 0}
    
    for sale in sales:
        cursor.execute("""
            SELECT COUNT(*) FROM Sync_Sales 
            WHERE NumeroTicket = %s AND UnidadNegocio = %s 
              AND CAST(FechaHora AS DATE) = CAST(%s AS DATE)
        """, (sale["NumeroTicket"], sale["UnidadNegocio"], sale["FechaHora"]))
        
        if cursor.fetchone()[0] > 0:
            stats["duplicados"] += 1
        else:
            stats["nuevos"] += 1
    
    cursor.close()
    return stats


def insert_into_sync_sales(conn, sales: List[Dict], dry_run: bool = True) -> int:
    """Inserta registros en Sync_Sales (o simula si dry_run=True)."""
    if not sales:
        return 0
    
    if dry_run:
        logger.info("🔍 MODO DRY-RUN: No se insertarán datos reales")
        return 0
    
    cursor = conn.cursor()
    inserted = 0
    
    for sale in sales:
        try:
            # Verificar si ya existe
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
            logger.warning(f"Error insertando ticket {sale.get('NumeroTicket')}: {e}")
    
    cursor.close()
    return inserted


# =============================================================================
# FUNCIONES DE REPORTE
# =============================================================================

def generate_dry_run_report(
    unidad: str,
    fecha_inicio: str,
    fecha_fin: str,
    sales: List[Dict],
    stats: Dict[str, int],
    verbose: bool = False
) -> Dict[str, Any]:
    """Genera reporte del dry-run."""
    
    # Calcular totales
    total_monto = sum(float(s.get("MontoTotal", 0) or 0) for s in sales)
    total_pax = sum(int(s.get("Pax", 0) or 0) for s in sales)
    
    # Validar estructura JSON items
    items_validos = 0
    items_nulos = 0
    items_invalidos = 0
    
    for sale in sales:
        items = sale.get("items")
        if items is None:
            items_nulos += 1
        else:
            try:
                if isinstance(items, str):
                    json.loads(items)
                items_validos += 1
            except:
                items_invalidos += 1
    
    report = {
        "timestamp": datetime.now().isoformat(),
        "unidad": unidad,
        "fecha_inicio": fecha_inicio,
        "fecha_fin": fecha_fin,
        "extraccion": {
            "total_registros": len(sales),
            "total_monto": round(total_monto, 2),
            "total_pax": total_pax,
            "ticket_promedio": round(total_monto / len(sales), 2) if sales else 0
        },
        "duplicados": {
            "nuevos_a_insertar": stats["nuevos"],
            "ya_existentes": stats["duplicados"]
        },
        "validacion_items": {
            "validos": items_validos,
            "nulos": items_nulos,
            "invalidos": items_invalidos
        },
        "ready_to_execute": stats["nuevos"] > 0 and items_invalidos == 0
    }
    
    # Muestra de registros si verbose
    if verbose and sales:
        report["muestra_registros"] = []
        for i, sale in enumerate(sales[:5]):
            report["muestra_registros"].append({
                "NumeroTicket": sale.get("NumeroTicket"),
                "MontoTotal": float(sale.get("MontoTotal", 0) or 0),
                "Pax": int(sale.get("Pax", 0) or 0),
                "FechaHora": str(sale.get("FechaHora")),
                "items_preview": str(sale.get("items", ""))[:100] + "..." if sale.get("items") else None
            })
    
    return report


def print_report(report: Dict[str, Any]):
    """Imprime el reporte de forma legible."""
    print()
    print("=" * 80)
    print("REPORTE DRY-RUN: Sync_Sales")
    print("=" * 80)
    print()
    print(f"Timestamp: {report['timestamp']}")
    print(f"Unidad: {report['unidad']}")
    print(f"Rango: {report['fecha_inicio']} a {report['fecha_fin']}")
    print()
    print("-" * 40)
    print("EXTRACCIÓN:")
    print("-" * 40)
    print(f"  Total registros extraídos: {report['extraccion']['total_registros']:,}")
    print(f"  Monto total: ${report['extraccion']['total_monto']:,.2f}")
    print(f"  PAX total: {report['extraccion']['total_pax']:,}")
    print(f"  Ticket promedio: ${report['extraccion']['ticket_promedio']:,.2f}")
    print()
    print("-" * 40)
    print("ANÁLISIS DE DUPLICADOS:")
    print("-" * 40)
    print(f"  Nuevos a insertar: {report['duplicados']['nuevos_a_insertar']:,}")
    print(f"  Ya existentes (skip): {report['duplicados']['ya_existentes']:,}")
    print()
    print("-" * 40)
    print("VALIDACIÓN JSON ITEMS:")
    print("-" * 40)
    print(f"  Items válidos: {report['validacion_items']['validos']:,}")
    print(f"  Items nulos: {report['validacion_items']['nulos']:,}")
    print(f"  Items inválidos: {report['validacion_items']['invalidos']:,}")
    print()
    
    if report.get("muestra_registros"):
        print("-" * 40)
        print("MUESTRA DE REGISTROS (primeros 5):")
        print("-" * 40)
        for i, rec in enumerate(report["muestra_registros"], 1):
            print(f"  {i}. Ticket #{rec['NumeroTicket']} | ${rec['MontoTotal']:,.2f} | PAX:{rec['Pax']} | {rec['FechaHora']}")
        print()
    
    print("=" * 80)
    if report["ready_to_execute"]:
        print("✅ LISTO PARA EJECUTAR")
        print("   Ejecutar con --execute para insertar datos reales")
    else:
        print("⚠️  NO LISTO PARA EJECUTAR")
        if report['duplicados']['nuevos_a_insertar'] == 0:
            print("   - No hay registros nuevos para insertar")
        if report['validacion_items']['invalidos'] > 0:
            print("   - Hay items JSON inválidos")
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
        choices=["CIENFUEGOS", "130MID", "ESTELAR", "130QRO", "ORIGEN"],
        help="Unidad de negocio piloto"
    )
    parser.add_argument(
        "--fecha-inicio",
        required=True,
        help="Fecha inicio (YYYY-MM-DD)"
    )
    parser.add_argument(
        "--fecha-fin",
        required=True,
        help="Fecha fin exclusiva (YYYY-MM-DD)"
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
        help="Ejecutar inserción real"
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Mostrar muestra de registros"
    )
    parser.add_argument(
        "--simulate",
        action="store_true",
        help="Modo simulación: genera datos de prueba sin conectar a POS"
    )
    parser.add_argument(
        "--output",
        "-o",
        help="Guardar reporte JSON en archivo"
    )
    
    args = parser.parse_args()
    
    # Determinar modo
    dry_run = not args.execute
    
    logger.info(f"{'🔍 DRY-RUN' if dry_run else '⚡ EJECUCIÓN REAL'}")
    logger.info(f"Unidad: {args.unidad}")
    logger.info(f"Rango: {args.fecha_inicio} a {args.fecha_fin}")
    
    # Modo simulación
    if args.simulate:
        logger.info("🧪 MODO SIMULACIÓN: Usando datos de KPIs existentes")
        sales = simulate_extraction_from_kpis(args.unidad, args.fecha_inicio, args.fecha_fin)
        if not sales:
            logger.warning("No hay datos para simular")
            sys.exit(0)
    else:
        # Obtener configuración desde BD
        config = get_unidad_config(args.unidad)
        if not config:
            logger.error(f"No se pudo obtener configuración para {args.unidad}")
            logger.info("💡 Intenta con --simulate para usar datos existentes")
            sys.exit(1)
        
        logger.info(f"Configuración obtenida: {config['host']}/{config['database']}")
        
        # Verificar credenciales
        if not config.get("password"):
            logger.error(f"❌ Credenciales no disponibles para {args.unidad}")
            sys.exit(1)
        
        # 1. Extraer datos del POS
        logger.info("Paso 1: Extrayendo datos del POS...")
        sales = extract_sales_from_pos(
            args.unidad,
            config,
            args.fecha_inicio,
            args.fecha_fin
        )
        
        if not sales:
            logger.warning("No se extrajeron registros del POS")
            logger.info("💡 Intenta con --simulate para validar estructura")
            sys.exit(0)
    
    # 2. Conectar a EDARSAHUB y verificar duplicados
    logger.info("Paso 2: Conectando a EDARSAHUB...")
    try:
        hub_conn = get_edarsahub_connection()
    except Exception as e:
        logger.error(f"Error conectando a EDARSAHUB: {e}")
        sys.exit(1)
    
    # 3. Verificar duplicados
    logger.info("Paso 3: Verificando duplicados existentes...")
    stats = check_existing_in_sync_sales(hub_conn, sales)
    
    # 4. Generar reporte
    logger.info("Paso 4: Generando reporte...")
    report = generate_dry_run_report(
        args.unidad,
        args.fecha_inicio,
        args.fecha_fin,
        sales,
        stats,
        args.verbose
    )
    
    # Mostrar reporte
    print_report(report)
    
    # 5. Ejecutar si no es dry-run
    if not dry_run:
        if not report["ready_to_execute"]:
            logger.error("❌ No se puede ejecutar - ver reporte")
            sys.exit(1)
        
        logger.info("Paso 5: Insertando registros...")
        inserted = insert_into_sync_sales(hub_conn, sales, dry_run=False)
        hub_conn.commit()
        logger.info(f"✅ Insertados: {inserted} registros")
        report["ejecutado"] = True
        report["registros_insertados"] = inserted
    else:
        logger.info("ℹ️  Dry-run completado - no se insertaron datos")
    
    hub_conn.close()
    
    # 6. Guardar reporte si se especificó
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False, default=str)
        logger.info(f"Reporte guardado en: {args.output}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
