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
    - pyodbc o pymssql
    - requests
    - pyyaml

ACCIONES:
    1. Lee configuración de config.yaml
    2. Conecta a SQL Server local
    3. Extrae KPIs del día
    4. Envía a HUB via POST /api/sync/kpis
    5. Envía heartbeat via POST /api/sync/heartbeat
    6. Registra resultado en log local

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

import yaml
import requests

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s [%(name)s] %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('sync_agent_piloto.log', mode='a')
    ]
)
logger = logging.getLogger('SYNC_AGENT_PILOTO')


# ============================================================================
# CONFIGURACIÓN
# ============================================================================

def load_config(config_path: str) -> Dict:
    """Carga configuración desde archivo YAML."""
    with open(config_path, 'r') as f:
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
    """
    Conecta a SQL Server local usando pyodbc o pymssql.
    
    Intenta pyodbc primero, si falla usa pymssql.
    """
    sql_config = config['sql_local']
    host = sql_config['host']
    port = sql_config['port']
    database = sql_config['database']
    username = sql_config['username']
    password = sql_config['password']
    
    # Intentar con pymssql primero (más portable)
    try:
        import pymssql
        conn = pymssql.connect(
            server=host,
            port=port,
            database=database,
            user=username,
            password=password,
            timeout=30,
            login_timeout=30
        )
        logger.info(f"Conectado a SQL Server via pymssql: {host}:{port}/{database}")
        return conn, 'pymssql'
    except ImportError:
        logger.warning("pymssql no disponible, intentando pyodbc")
    except Exception as e:
        logger.warning(f"pymssql falló: {e}, intentando pyodbc")
    
    # Fallback a pyodbc
    try:
        import pyodbc
        conn_str = (
            f"DRIVER={{ODBC Driver 17 for SQL Server}};"
            f"SERVER={host},{port};"
            f"DATABASE={database};"
            f"UID={username};"
            f"PWD={password};"
            f"Connection Timeout=30"
        )
        conn = pyodbc.connect(conn_str)
        logger.info(f"Conectado a SQL Server via pyodbc: {host}:{port}/{database}")
        return conn, 'pyodbc'
    except Exception as e:
        logger.error(f"No se pudo conectar a SQL Server: {e}")
        raise


def execute_query(conn, query: str, driver_type: str) -> List[Dict]:
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


def extract_kpis_softrestaurant(conn, driver_type: str, fecha: str) -> List[Dict]:
    """
    Extrae KPIs de SoftRestaurant para una fecha.
    
    QUERY: Basada en query centralizada de queries/softrestaurant.py
    
    Args:
        conn: Conexión SQL
        driver_type: 'pymssql' o 'pyodbc'
        fecha: Fecha en formato YYYY-MM-DD
    
    Returns:
        Lista de KPIs por sucursal
    """
    # Convertir fecha a formato YYYYMMDD
    fecha_sql = fecha.replace('-', '')
    
    # Query de KPIs consolidados por sucursal (si hay campo sucursal) o total
    # NOTA: SoftRestaurant típicamente no tiene campo sucursal en cheques,
    # así que extraemos totales del servidor
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
    results = execute_query(conn, query, driver_type)
    
    if results:
        row = results[0]
        return [{
            'sucursal_id': '01',  # SoftRestaurant típicamente es single-sucursal
            'sucursal_nombre': 'Principal',
            'fecha': fecha,
            'kpis': {
                'ventas': float(row.get('ventas') or 0),
                'pax': int(row.get('pax') or 0),
                'cheques': int(row.get('cheques') or 0)
            }
        }]
    
    return []


# ============================================================================
# ENVÍO A HUB
# ============================================================================

def send_kpis_to_hub(config: Dict, records: List[Dict]) -> Dict:
    """
    Envía KPIs a EDARSA HUB via POST /api/sync/kpis.
    
    Returns:
        Respuesta del servidor
    """
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
    logger.debug(f"Payload: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        result = response.json()
        logger.info(f"Respuesta HUB: status={result.get('status')}, processed={result.get('processed')}")
        return result
    except requests.exceptions.HTTPError as e:
        logger.error(f"Error HTTP: {e.response.status_code} - {e.response.text}")
        raise
    except Exception as e:
        logger.error(f"Error enviando a HUB: {e}")
        raise


def send_heartbeat(config: Dict, status: str, last_sync: Optional[str], sql_status: str) -> Dict:
    """
    Envía heartbeat a EDARSA HUB via POST /api/sync/heartbeat.
    """
    url = f"{config['hub_url']}/api/sync/heartbeat"
    
    payload = {
        "agent_id": config['agent_id'],
        "server_id": config['server_id'],
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "last_sync": last_sync,
        "sql_local_status": sql_status,
        "queue_depth": 0  # Piloto no tiene cola
    }
    
    headers = {
        "Authorization": f"Bearer {config['hub_token']}",
        "Content-Type": "application/json"
    }
    
    logger.info(f"Enviando heartbeat a {url}")
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        result = response.json()
        logger.info(f"Heartbeat registrado: {result.get('message')}")
        return result
    except Exception as e:
        logger.error(f"Error enviando heartbeat: {e}")
        raise


def test_auth(config: Dict) -> bool:
    """
    Verifica autenticación contra HUB usando GET /api/sync/test-auth.
    """
    url = f"{config['hub_url']}/api/sync/test-auth"
    
    headers = {
        "Authorization": f"Bearer {config['hub_token']}"
    }
    
    logger.info("Verificando autenticación con HUB...")
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        result = response.json()
        logger.info(f"Autenticación OK: agent_id={result.get('agent_id')}")
        return True
    except requests.exceptions.HTTPError as e:
        logger.error(f"Error de autenticación: {e.response.status_code} - {e.response.text}")
        return False
    except Exception as e:
        logger.error(f"Error verificando auth: {e}")
        return False


# ============================================================================
# MAIN
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description='EDARSA Sync Agent Piloto - SoftRestaurant')
    parser.add_argument('--config', required=True, help='Ruta al archivo config.yaml')
    parser.add_argument('--fecha', default=None, help='Fecha a sincronizar (YYYY-MM-DD), default=hoy')
    parser.add_argument('--test-only', action='store_true', help='Solo probar conexión, no sincronizar')
    args = parser.parse_args()
    
    # Cargar configuración
    logger.info(f"Cargando configuración de {args.config}")
    try:
        config = load_config(args.config)
    except Exception as e:
        logger.error(f"Error cargando config: {e}")
        sys.exit(1)
    
    logger.info(f"Agent ID: {config['agent_id']}")
    logger.info(f"Server ID: {config['server_id']}")
    logger.info(f"HUB URL: {config['hub_url']}")
    
    # Fecha a sincronizar
    fecha = args.fecha or datetime.now().strftime('%Y-%m-%d')
    logger.info(f"Fecha a sincronizar: {fecha}")
    
    # 1. Verificar autenticación
    if not test_auth(config):
        logger.error("Fallo de autenticación - abortando")
        sys.exit(1)
    
    if args.test_only:
        logger.info("Modo test-only: Solo se verificó autenticación")
        sys.exit(0)
    
    # 2. Conectar a SQL local
    sql_status = "CONNECTED"
    last_sync = None
    
    try:
        conn, driver_type = connect_sql(config)
    except Exception as e:
        logger.error(f"No se pudo conectar a SQL local: {e}")
        sql_status = "ERROR"
        # Enviar heartbeat con error
        send_heartbeat(config, "SQL_LOCAL_ERROR", None, sql_status)
        sys.exit(1)
    
    # 3. Extraer KPIs
    try:
        records = extract_kpis_softrestaurant(conn, driver_type, fecha)
        conn.close()
        
        if not records:
            logger.warning(f"No se encontraron datos para fecha {fecha}")
        else:
            logger.info(f"Extraídos {len(records)} registros")
            for r in records:
                kpis = r['kpis']
                logger.info(f"  Sucursal {r['sucursal_id']}: Ventas=${kpis['ventas']:,.2f}, PAX={kpis['pax']}, Cheques={kpis['cheques']}")
    except Exception as e:
        logger.error(f"Error extrayendo KPIs: {e}")
        conn.close()
        send_heartbeat(config, "SQL_LOCAL_ERROR", None, "ERROR")
        sys.exit(1)
    
    # 4. Enviar KPIs a HUB
    if records:
        try:
            result = send_kpis_to_hub(config, records)
            last_sync = datetime.now(timezone.utc).isoformat()
            
            if result.get('status') == 'OK':
                logger.info("✅ Sincronización exitosa")
            else:
                logger.warning(f"⚠️ Sincronización parcial: {result.get('errors')}")
        except Exception as e:
            logger.error(f"❌ Error enviando KPIs: {e}")
            send_heartbeat(config, "OK", None, sql_status)
            sys.exit(1)
    
    # 5. Enviar heartbeat
    try:
        send_heartbeat(config, "OK", last_sync, sql_status)
    except Exception as e:
        logger.warning(f"No se pudo enviar heartbeat: {e}")
    
    logger.info("=" * 60)
    logger.info("SYNC AGENT PILOTO - EJECUCIÓN COMPLETADA")
    logger.info("=" * 60)


if __name__ == '__main__':
    main()
