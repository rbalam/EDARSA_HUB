#!/usr/bin/env python3
"""
EDARSA Sync Agent - Piloto SoftRestaurant (FASE 1)
=================================================

Script standalone para extraer KPIs de un servidor SoftRestaurant local
y enviarlos a EDARSA HUB.

USO:
    python sync_agent_piloto.py --config config.yaml

REQUISITOS:
    - Python 3.9+
    - pymssql (pip install pymssql)
    - requests (pip install requests)
    - pyyaml (pip install pyyaml)

Fecha: 2026-04-23
Versión: 1.0 (Piloto)
"""

import argparse
import json
import logging
import os
import sys
from datetime import datetime, timezone
from typing import Dict, Optional, List

try:
    import yaml
except ImportError:
    print("ERROR: Falta pyyaml. Ejecutar: pip install pyyaml")
    sys.exit(1)

try:
    import requests
except ImportError:
    print("ERROR: Falta requests. Ejecutar: pip install requests")
    sys.exit(1)

# Configurar logging
LOG_FILE = f"sync_agent_piloto_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s [%(name)s] %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOG_FILE, mode='a')
    ]
)
logger = logging.getLogger('SYNC_AGENT_PILOTO')


# ============================================================================
# CONFIGURACIÓN
# ============================================================================

def load_config(config_path: str) -> Dict:
    """Carga configuración desde archivo YAML."""
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Archivo de configuración no encontrado: {config_path}")
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    # Validar campos requeridos
    required = ['agent_id', 'hub_url', 'hub_token', 'server_id', 'sql_local']
    for field in required:
        if field not in config:
            raise ValueError(f"Campo requerido faltante en config: {field}")
    
    sql_required = ['host', 'port', 'database', 'username', 'password']
    for field in sql_required:
        if field not in config['sql_local']:
            raise ValueError(f"Campo SQL requerido faltante: {field}")
    
    return config


# ============================================================================
# EXTRACCIÓN SQL
# ============================================================================

def connect_sql(config: Dict):
    """Conecta a SQL Server local usando pymssql."""
    sql_config = config['sql_local']
    host = sql_config['host']
    port = sql_config['port']
    database = sql_config['database']
    username = sql_config['username']
    password = sql_config['password']
    
    try:
        import pymssql
    except ImportError:
        logger.error("ERROR: Falta pymssql. Ejecutar: pip install pymssql")
        sys.exit(1)
    
    try:
        conn = pymssql.connect(
            server=host,
            port=port,
            database=database,
            user=username,
            password=password,
            timeout=30,
            login_timeout=30
        )
        logger.info(f"✅ Conectado a SQL Server: {host}:{port}/{database}")
        return conn
    except Exception as e:
        logger.error(f"❌ Error conectando a SQL Server: {e}")
        raise


def execute_query(conn, query: str) -> List[Dict]:
    """Ejecuta query y retorna resultados como lista de diccionarios."""
    cursor = conn.cursor()
    cursor.execute(query)
    
    # Obtener nombres de columnas
    columns = [col[0] for col in cursor.description]
    
    # Convertir filas a diccionarios
    results = []
    for row in cursor.fetchall():
        results.append(dict(zip(columns, row)))
    
    cursor.close()
    return results


def extract_kpis_softrestaurant(conn, fecha: str) -> List[Dict]:
    """
    Extrae KPIs de SoftRestaurant para una fecha.
    
    Args:
        conn: Conexión SQL
        fecha: Fecha en formato YYYY-MM-DD
    
    Returns:
        Lista de KPIs por sucursal
    """
    # Convertir fecha a formato YYYYMMDD
    fecha_sql = fecha.replace('-', '')
    
    # Query de KPIs consolidados
    query = f"""
SELECT 
    ISNULL(SUM(c.total), 0) as ventas,
    ISNULL(SUM(c.nopersonas), 0) as pax,
    COUNT(*) as cheques
FROM cheques c
JOIN turnos t ON c.turno = t.turno
WHERE CONVERT(varchar, t.apertura, 112) = '{fecha_sql}'
  AND c.cancelado = 0
"""
    
    logger.info(f"Ejecutando query de KPIs para fecha {fecha}")
    logger.debug(f"Query: {query}")
    
    try:
        results = execute_query(conn, query)
        
        if results:
            row = results[0]
            ventas = float(row.get('ventas') or 0)
            pax = int(row.get('pax') or 0)
            cheques = int(row.get('cheques') or 0)
            
            logger.info(f"✅ Datos extraídos: Ventas=${ventas:,.2f}, PAX={pax}, Cheques={cheques}")
            
            return [{
                'sucursal_id': '01',
                'sucursal_nombre': 'Principal',
                'fecha': fecha,
                'kpis': {
                    'ventas': ventas,
                    'pax': pax,
                    'cheques': cheques
                }
            }]
        
        logger.warning(f"⚠️ Query retornó sin resultados para fecha {fecha}")
        return []
        
    except Exception as e:
        logger.error(f"❌ Error ejecutando query: {e}")
        raise


# ============================================================================
# ENVÍO A HUB
# ============================================================================

def send_kpis_to_hub(config: Dict, records: List[Dict]) -> Dict:
    """Envía KPIs a EDARSA HUB via POST /api/sync/kpis."""
    url = f"{config['hub_url']}/api/sync/kpis"
    
    payload = {
        "version": "1.0",
        "agent_id": config['agent_id'],
        "server_id": config['server_id'],
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "payload_type": "KPIS_DIARIOS",
        "records": records
    }
    
    headers = {
        "Authorization": f"Bearer {config['hub_token']}",
        "Content-Type": "application/json"
    }
    
    logger.info(f"Enviando {len(records)} registros a {url}")
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            logger.info(f"✅ Respuesta HUB: status={result.get('status')}, actions={result.get('actions')}")
            return result
        else:
            logger.error(f"❌ Error HTTP {response.status_code}: {response.text}")
            return {"status": "ERROR", "error": response.text}
            
    except requests.exceptions.Timeout:
        logger.error("❌ Timeout conectando a HUB")
        return {"status": "ERROR", "error": "Timeout"}
    except Exception as e:
        logger.error(f"❌ Error enviando a HUB: {e}")
        return {"status": "ERROR", "error": str(e)}


def send_heartbeat(config: Dict, status: str, last_sync: Optional[str], sql_status: str) -> Dict:
    """Envía heartbeat a EDARSA HUB via POST /api/sync/heartbeat."""
    url = f"{config['hub_url']}/api/sync/heartbeat"
    
    payload = {
        "agent_id": config['agent_id'],
        "server_id": config['server_id'],
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "last_sync": last_sync,
        "sql_local_status": sql_status,
        "queue_depth": 0
    }
    
    headers = {
        "Authorization": f"Bearer {config['hub_token']}",
        "Content-Type": "application/json"
    }
    
    logger.info(f"Enviando heartbeat a HUB...")
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            logger.info(f"✅ Heartbeat registrado")
            return result
        else:
            logger.error(f"❌ Error heartbeat HTTP {response.status_code}: {response.text}")
            return {"status": "ERROR", "error": response.text}
            
    except Exception as e:
        logger.error(f"❌ Error enviando heartbeat: {e}")
        return {"status": "ERROR", "error": str(e)}


def test_auth(config: Dict) -> bool:
    """Verifica autenticación contra HUB usando GET /api/sync/test-auth."""
    url = f"{config['hub_url']}/api/sync/test-auth"
    
    headers = {
        "Authorization": f"Bearer {config['hub_token']}"
    }
    
    logger.info(f"Verificando autenticación con HUB ({config['hub_url']})...")
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            logger.info(f"✅ Autenticación OK: agent_id={result.get('agent_id')}, server_id={result.get('server_id')}")
            return True
        elif response.status_code == 401:
            logger.error("❌ Token inválido o expirado")
            return False
        elif response.status_code == 403:
            logger.error("❌ Token no es de tipo sync_agent")
            return False
        else:
            logger.error(f"❌ Error de autenticación: {response.status_code} - {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        logger.error("❌ Timeout conectando a HUB")
        return False
    except requests.exceptions.ConnectionError as e:
        logger.error(f"❌ No se puede conectar a HUB: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Error verificando auth: {e}")
        return False


# ============================================================================
# REPORTE
# ============================================================================

def generate_report(config: Dict, results: Dict) -> str:
    """Genera reporte de ejecución en formato JSON."""
    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "agent_id": config['agent_id'],
        "server_id": config['server_id'],
        "hub_url": config['hub_url'],
        "results": results
    }
    
    report_file = f"reporte_piloto_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    logger.info(f"📄 Reporte guardado en: {report_file}")
    return report_file


# ============================================================================
# MAIN
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description='EDARSA Sync Agent Piloto - SoftRestaurant',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  # Verificar solo autenticación:
  python sync_agent_piloto.py --config config.yaml --test-only

  # Sincronizar datos del día actual:
  python sync_agent_piloto.py --config config.yaml

  # Sincronizar datos de una fecha específica:
  python sync_agent_piloto.py --config config.yaml --fecha 2026-04-22
        """
    )
    parser.add_argument('--config', required=True, help='Ruta al archivo config.yaml')
    parser.add_argument('--fecha', default=None, help='Fecha a sincronizar (YYYY-MM-DD), default=hoy')
    parser.add_argument('--test-only', action='store_true', help='Solo probar conexiones, no sincronizar')
    args = parser.parse_args()
    
    print("=" * 70)
    print("  EDARSA SYNC AGENT - PILOTO SOFTRESTAURANT")
    print("  Versión 1.0")
    print("=" * 70)
    print(f"  Log: {LOG_FILE}")
    print("=" * 70)
    print()
    
    # Resultados para reporte
    results = {
        "config_loaded": False,
        "auth_ok": False,
        "sql_connected": False,
        "extraction_ok": False,
        "kpis_sent": False,
        "heartbeat_sent": False,
        "errors": []
    }
    
    # 1. Cargar configuración
    logger.info(f"[1/6] Cargando configuración de {args.config}")
    try:
        config = load_config(args.config)
        results["config_loaded"] = True
        logger.info(f"  Agent ID: {config['agent_id']}")
        logger.info(f"  Server ID: {config['server_id']}")
        logger.info(f"  HUB URL: {config['hub_url']}")
    except Exception as e:
        logger.error(f"❌ Error cargando config: {e}")
        results["errors"].append(f"Config: {e}")
        generate_report(config if 'config' in dir() else {"agent_id": "unknown", "server_id": "unknown", "hub_url": "unknown"}, results)
        sys.exit(1)
    
    # 2. Verificar autenticación con HUB
    logger.info(f"\n[2/6] Verificando autenticación con HUB")
    if not test_auth(config):
        results["errors"].append("Auth: Fallo de autenticación con HUB")
        generate_report(config, results)
        logger.error("Abortando - Fallo de autenticación")
        sys.exit(1)
    results["auth_ok"] = True
    
    if args.test_only:
        logger.info("\n✅ Modo test-only: Solo se verificó autenticación")
        results["notes"] = "Modo test-only"
        generate_report(config, results)
        sys.exit(0)
    
    # 3. Conectar a SQL local
    logger.info(f"\n[3/6] Conectando a SQL Server local")
    sql_status = "CONNECTED"
    last_sync = None
    
    try:
        conn = connect_sql(config)
        results["sql_connected"] = True
    except Exception as e:
        logger.error(f"❌ No se pudo conectar a SQL local: {e}")
        results["errors"].append(f"SQL: {e}")
        sql_status = "ERROR"
        send_heartbeat(config, "SQL_LOCAL_ERROR", None, sql_status)
        generate_report(config, results)
        sys.exit(1)
    
    # 4. Extraer KPIs
    fecha = args.fecha or datetime.now().strftime('%Y-%m-%d')
    logger.info(f"\n[4/6] Extrayendo KPIs para fecha {fecha}")
    
    try:
        records = extract_kpis_softrestaurant(conn, fecha)
        conn.close()
        
        if not records:
            logger.warning(f"⚠️ No se encontraron datos para fecha {fecha}")
            results["extraction_ok"] = True
            results["notes"] = f"Sin datos para {fecha}"
        else:
            results["extraction_ok"] = True
            results["extracted_records"] = len(records)
            results["kpis"] = records[0]['kpis'] if records else {}
            
    except Exception as e:
        logger.error(f"❌ Error extrayendo KPIs: {e}")
        results["errors"].append(f"Extraction: {e}")
        conn.close()
        send_heartbeat(config, "SQL_LOCAL_ERROR", None, "ERROR")
        generate_report(config, results)
        sys.exit(1)
    
    # 5. Enviar KPIs a HUB
    logger.info(f"\n[5/6] Enviando KPIs a HUB")
    if records:
        sync_result = send_kpis_to_hub(config, records)
        
        if sync_result.get('status') == 'OK':
            results["kpis_sent"] = True
            results["sync_actions"] = sync_result.get('actions', {})
            last_sync = datetime.now(timezone.utc).isoformat()
        elif sync_result.get('status') == 'PARTIAL':
            results["kpis_sent"] = True
            results["sync_actions"] = sync_result.get('actions', {})
            results["sync_errors"] = sync_result.get('errors', [])
            last_sync = datetime.now(timezone.utc).isoformat()
        else:
            results["errors"].append(f"Sync: {sync_result.get('error', 'Unknown')}")
    else:
        logger.info("Sin datos para enviar")
        results["kpis_sent"] = False
        results["notes"] = "Sin datos para enviar"
    
    # 6. Enviar heartbeat
    logger.info(f"\n[6/6] Enviando heartbeat")
    hb_result = send_heartbeat(config, "OK", last_sync, sql_status)
    if hb_result.get('status') == 'OK':
        results["heartbeat_sent"] = True
    else:
        results["errors"].append(f"Heartbeat: {hb_result.get('error', 'Unknown')}")
    
    # Resumen final
    print()
    print("=" * 70)
    print("  RESUMEN DE EJECUCIÓN")
    print("=" * 70)
    print(f"  Config cargada:    {'✅' if results['config_loaded'] else '❌'}")
    print(f"  Auth HUB:          {'✅' if results['auth_ok'] else '❌'}")
    print(f"  SQL conectado:     {'✅' if results['sql_connected'] else '❌'}")
    print(f"  Extracción:        {'✅' if results['extraction_ok'] else '❌'}")
    print(f"  KPIs enviados:     {'✅' if results['kpis_sent'] else '❌'}")
    print(f"  Heartbeat:         {'✅' if results['heartbeat_sent'] else '❌'}")
    
    if results.get('sync_actions'):
        print(f"\n  Acciones UPSERT:")
        for action, count in results['sync_actions'].items():
            print(f"    {action}: {count}")
    
    if results['errors']:
        print(f"\n  ⚠️ Errores: {len(results['errors'])}")
        for err in results['errors']:
            print(f"    - {err}")
    
    print("=" * 70)
    
    # Generar reporte
    report_file = generate_report(config, results)
    
    # Determinar exit code
    all_ok = all([
        results['config_loaded'],
        results['auth_ok'],
        results['sql_connected'],
        results['extraction_ok'],
        results['heartbeat_sent']
    ])
    
    if all_ok and (results['kpis_sent'] or not records):
        logger.info("\n✅ EJECUCIÓN COMPLETADA EXITOSAMENTE")
        sys.exit(0)
    else:
        logger.warning("\n⚠️ EJECUCIÓN COMPLETADA CON OBSERVACIONES")
        sys.exit(1)


if __name__ == '__main__':
    main()
