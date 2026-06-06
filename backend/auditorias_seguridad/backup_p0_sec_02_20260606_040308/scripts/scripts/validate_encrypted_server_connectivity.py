#!/usr/bin/env python3
"""
EDARSA HUB - Validación de Conectividad con Secretos Cifrados
==============================================================

FASE 3D: Valida que los servidores con passwords cifrados pueden
conectarse correctamente usando secret_manager para descifrar.

USO:
    python validate_encrypted_server_connectivity.py --dry-run    # Solo inventario
    python validate_encrypted_server_connectivity.py --run        # Ejecutar pruebas

OPCIONES:
    --server-id <id>        Probar solo un servidor específico
    --system-type <type>    Filtrar por SOFTRESTAURANT|MANAGEMENTPRO|API
    --timeout <seconds>     Timeout de conexión (default: 10)
    --include-inactive      Incluir servidores inactivos
    --include-core          Incluir servidores CORE (solo validación controlada)

SALIDA:
    /app/docs/reports/encrypted_connectivity_validation_report.json

SEGURIDAD:
    - No imprime passwords, api_keys, tokens ni connection strings
    - Logs seguros sin secretos
    - Clasificación clara de errores

CREADO: FASE 3D - Abril 2026
"""

import argparse
import json
import sys
import os
import time
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

# Agregar path del backend
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

# Cargar variables de entorno
from dotenv import load_dotenv
env_path = backend_path / '.env'
if env_path.exists():
    load_dotenv(env_path)
    print(f"✓ Variables de entorno cargadas desde {env_path}")

# Configurar logging seguro
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Imports del proyecto
from core.db import execute_sql_query
from core.server_registry import (
    EDARSAHUB_CONFIG,
    get_decrypted_credentials,
    _get_server_by_id_from_sql
)
from core.secret_manager import (
    is_encrypted_secret,
    decrypt_secret,
    validate_secret_key_config,
    is_encryption_available
)


# =============================================================================
# ESTADOS DE CONECTIVIDAD
# =============================================================================

class ConnectivityStatus:
    SUCCESS = "SUCCESS"
    NO_DATA = "NO_DATA"
    SOURCE_UNREACHABLE = "SOURCE_UNREACHABLE"
    AUTH_FAILED = "AUTH_FAILED"
    SECRET_DECRYPTION_ERROR = "SECRET_DECRYPTION_ERROR"
    QUERY_ERROR = "QUERY_ERROR"
    CONFIGURATION_MISSING = "CONFIGURATION_MISSING"
    UNSUPPORTED_CONNECTION_TYPE = "UNSUPPORTED_CONNECTION_TYPE"
    SKIPPED = "SKIPPED"


# =============================================================================
# FUNCIONES DE VALIDACIÓN
# =============================================================================

def validate_secret_manager() -> Dict:
    """Valida que el secret manager esté listo."""
    result = {
        'encryption_available': is_encryption_available(),
        'key_config': validate_secret_key_config()
    }
    
    if not result['encryption_available']:
        logger.error("[CONNECTIVITY][SECRET_MANAGER] Cifrado no disponible")
    else:
        fp = result['key_config'].get('fingerprint', 'N/A')
        logger.info(f"[CONNECTIVITY][SECRET_MANAGER] OK (fingerprint: {fp})")
    
    return result


def get_servers_inventory(
    include_inactive: bool = False,
    include_core: bool = False,
    system_type_filter: Optional[str] = None,
    server_id_filter: Optional[str] = None
) -> List[Dict]:
    """Obtiene inventario de servidores para probar."""
    
    conditions = []
    
    if not include_inactive:
        conditions.append("activo = 1")
    
    if not include_core:
        conditions.append("(tipo_conexion != 'CORE' OR tipo_conexion IS NULL)")
    
    if system_type_filter:
        # Normalizar filtro
        st_upper = system_type_filter.upper()
        if st_upper in ['MPRO', 'MANAGEMENTPRO', 'MANAGMENT', 'MANAGEMENT']:
            conditions.append("(system_type LIKE '%MPRO%' OR system_type LIKE '%MANAGEMENT%')")
        elif st_upper in ['SR', 'SOFTRESTAURANT', 'SOFT']:
            conditions.append("system_type LIKE '%SOFT%'")
        elif st_upper == 'API':
            conditions.append("system_type = 'API'")
        else:
            conditions.append(f"system_type LIKE '%{system_type_filter}%'")
    
    if server_id_filter:
        safe_id = server_id_filter.replace("'", "''")
        conditions.append(f"CAST(id AS VARCHAR(50)) = '{safe_id}'")
    
    where_clause = " AND ".join(conditions) if conditions else "1=1"
    
    query = f"""
    SELECT 
        CAST(id AS VARCHAR(50)) as id,
        nombre,
        system_type,
        tipo_conexion,
        host,
        port,
        database_name,
        username,
        activo,
        password_encrypted,
        api_key_encrypted,
        api_url
    FROM Servidores_Conexiones
    WHERE {where_clause}
    ORDER BY tipo_conexion, activo DESC, nombre
    """
    
    result = execute_sql_query(
        EDARSAHUB_CONFIG['host'],
        EDARSAHUB_CONFIG['port'],
        EDARSAHUB_CONFIG['database'],
        EDARSAHUB_CONFIG['username'],
        EDARSAHUB_CONFIG['password'],
        query
    )
    
    servers = []
    for row in result:
        pwd = row.get('password_encrypted', '')
        api = row.get('api_key_encrypted', '')
        
        # Determinar estado de secretos sin exponer valores
        if pwd:
            pwd_status = 'ENCRYPTED' if is_encrypted_secret(pwd) else 'LEGACY_PLAINTEXT'
        else:
            pwd_status = 'NOT_CONFIGURED'
        
        if api:
            api_status = 'ENCRYPTED' if is_encrypted_secret(api) else 'LEGACY_PLAINTEXT'
        else:
            api_status = 'NOT_CONFIGURED'
        
        # Normalizar system_type
        sys_type = (row.get('system_type') or '').upper()
        if 'MPRO' in sys_type or 'MANAGEMENT' in sys_type:
            system_type_normalized = 'MANAGEMENTPRO'
        elif 'SOFT' in sys_type:
            system_type_normalized = 'SOFTRESTAURANT'
        elif sys_type == 'API':
            system_type_normalized = 'API'
        else:
            system_type_normalized = sys_type or 'UNKNOWN'
        
        servers.append({
            'id': row['id'],
            'name': row['nombre'],
            'system_type': row.get('system_type', ''),
            'system_type_normalized': system_type_normalized,
            'connection_type': row.get('tipo_conexion', 'DATA_SOURCE'),
            'host': row.get('host', ''),
            'port': row.get('port', 1433),
            'database': row.get('database_name', ''),
            'username': row.get('username', ''),
            'active': bool(row.get('activo', False)),
            'password_status': pwd_status,
            'api_key_status': api_status,
            'api_url': row.get('api_url', ''),
            'config_origin': 'EDARSAHUB_SQL',
            # Guardamos los secretos cifrados para descifrar internamente
            '_password_encrypted': pwd,
            '_api_key_encrypted': api
        })
    
    return servers


def test_sql_connectivity(server: Dict, timeout: int = 10) -> Dict:
    """
    Prueba conectividad SQL a un servidor.
    
    IMPORTANTE: No imprime secretos.
    """
    server_id = server['id']
    server_name = server['name']
    
    logger.info(f"[CONNECTIVITY][START] {server_name} ({server_id[:8]}...)")
    
    start_time = time.time()
    result = {
        'server_id': server_id,
        'name': server_name,
        'system_type_normalized': server['system_type_normalized'],
        'connection_type': server['connection_type'],
        'config_origin': server['config_origin'],
        'secret_status': server['password_status'],
        'decrypt_ok': False,
        'connectivity_status': ConnectivityStatus.SKIPPED,
        'duration_ms': 0,
        'safe_error': None
    }
    
    # Verificar configuración mínima
    if not server.get('host'):
        result['connectivity_status'] = ConnectivityStatus.CONFIGURATION_MISSING
        result['safe_error'] = 'Host no configurado'
        logger.warning(f"[CONNECTIVITY][CONFIGURATION_MISSING] {server_name}: Host vacío")
        return result
    
    if not server.get('_password_encrypted'):
        result['connectivity_status'] = ConnectivityStatus.CONFIGURATION_MISSING
        result['safe_error'] = 'Password no configurado'
        logger.warning(f"[CONNECTIVITY][CONFIGURATION_MISSING] {server_name}: Password vacío")
        return result
    
    # Descifrar password internamente
    try:
        password = decrypt_secret(server['_password_encrypted'])
        result['decrypt_ok'] = True
        logger.info(f"[CONNECTIVITY][DECRYPT_OK] {server_name}")
    except Exception as e:
        result['connectivity_status'] = ConnectivityStatus.SECRET_DECRYPTION_ERROR
        result['safe_error'] = f'Error de descifrado: {type(e).__name__}'
        logger.error(f"[CONNECTIVITY][SECRET_DECRYPTION_ERROR] {server_name}: {type(e).__name__}")
        result['duration_ms'] = int((time.time() - start_time) * 1000)
        return result
    
    # Intentar conexión SQL
    try:
        import pymssql
        
        host = server['host']
        port = server.get('port', 1433)
        database = server.get('database', 'master')
        username = server.get('username', '')
        
        # Conexión con timeout
        conn = pymssql.connect(
            host,
            username,
            password,  # Password descifrado internamente
            database,
            port=port,
            timeout=timeout,
            login_timeout=timeout
        )
        
        cursor = conn.cursor()
        cursor.execute("SELECT 1 AS connectivity_ok")
        row = cursor.fetchone()
        conn.close()
        
        if row and row[0] == 1:
            result['connectivity_status'] = ConnectivityStatus.SUCCESS
            logger.info(f"[CONNECTIVITY][SUCCESS] {server_name}")
        else:
            result['connectivity_status'] = ConnectivityStatus.QUERY_ERROR
            result['safe_error'] = 'Query no retornó resultado esperado'
            logger.warning(f"[CONNECTIVITY][QUERY_ERROR] {server_name}: Resultado inesperado")
        
    except Exception as e:
        error_msg = str(e).lower()
        error_type = type(e).__name__
        
        # Clasificar error
        if 'timeout' in error_msg or 'timed out' in error_msg:
            result['connectivity_status'] = ConnectivityStatus.SOURCE_UNREACHABLE
            result['safe_error'] = 'Connection timeout'
            logger.warning(f"[CONNECTIVITY][SOURCE_UNREACHABLE] {server_name}: Timeout")
        elif 'login failed' in error_msg or 'access denied' in error_msg:
            result['connectivity_status'] = ConnectivityStatus.AUTH_FAILED
            result['safe_error'] = 'Authentication failed'
            logger.warning(f"[CONNECTIVITY][AUTH_FAILED] {server_name}: Login failed")
        elif 'could not open' in error_msg or 'connection refused' in error_msg or 'network' in error_msg:
            result['connectivity_status'] = ConnectivityStatus.SOURCE_UNREACHABLE
            result['safe_error'] = 'Network unreachable'
            logger.warning(f"[CONNECTIVITY][SOURCE_UNREACHABLE] {server_name}: Network error")
        elif 'unable to connect' in error_msg or 'unavailable' in error_msg or 'adaptive server' in error_msg:
            result['connectivity_status'] = ConnectivityStatus.SOURCE_UNREACHABLE
            result['safe_error'] = 'Server unavailable (network/VPN)'
            logger.warning(f"[CONNECTIVITY][SOURCE_UNREACHABLE] {server_name}: Server unavailable")
        elif 'database' in error_msg and ('not exist' in error_msg or 'cannot open' in error_msg):
            result['connectivity_status'] = ConnectivityStatus.CONFIGURATION_MISSING
            result['safe_error'] = 'Database not found'
            logger.warning(f"[CONNECTIVITY][CONFIGURATION_MISSING] {server_name}: Database error")
        else:
            result['connectivity_status'] = ConnectivityStatus.QUERY_ERROR
            result['safe_error'] = f'{error_type}: {str(e)[:100]}'
            logger.warning(f"[CONNECTIVITY][QUERY_ERROR] {server_name}: {error_type}")
    
    result['duration_ms'] = int((time.time() - start_time) * 1000)
    return result


def test_api_connectivity(server: Dict, timeout: int = 10) -> Dict:
    """
    Prueba conectividad a un servidor tipo API.
    
    IMPORTANTE: No imprime api_key.
    """
    server_id = server['id']
    server_name = server['name']
    
    logger.info(f"[CONNECTIVITY][API][START] {server_name} ({server_id[:8]}...)")
    
    start_time = time.time()
    result = {
        'server_id': server_id,
        'name': server_name,
        'system_type_normalized': server['system_type_normalized'],
        'connection_type': server['connection_type'],
        'config_origin': server['config_origin'],
        'secret_status': server['api_key_status'],
        'decrypt_ok': False,
        'connectivity_status': ConnectivityStatus.SKIPPED,
        'duration_ms': 0,
        'safe_error': None
    }
    
    api_url = server.get('api_url', '')
    api_key_encrypted = server.get('_api_key_encrypted', '')
    
    if not api_url:
        result['connectivity_status'] = ConnectivityStatus.CONFIGURATION_MISSING
        result['safe_error'] = 'API URL no configurada'
        logger.warning(f"[CONNECTIVITY][API][CONFIGURATION_MISSING] {server_name}: URL vacía")
        return result
    
    # Descifrar api_key si existe
    api_key = None
    if api_key_encrypted:
        try:
            api_key = decrypt_secret(api_key_encrypted)
            result['decrypt_ok'] = True
            logger.info(f"[CONNECTIVITY][API][DECRYPT_OK] {server_name}")
        except Exception as e:
            result['connectivity_status'] = ConnectivityStatus.SECRET_DECRYPTION_ERROR
            result['safe_error'] = f'Error de descifrado: {type(e).__name__}'
            logger.error(f"[CONNECTIVITY][API][SECRET_DECRYPTION_ERROR] {server_name}")
            result['duration_ms'] = int((time.time() - start_time) * 1000)
            return result
    else:
        result['decrypt_ok'] = True  # No hay api_key que descifrar
    
    # Intentar health check
    try:
        import requests
        
        headers = {'Content-Type': 'application/json'}
        if api_key:
            headers['Authorization'] = f'Bearer {api_key}'  # api_key descifrada internamente
        
        # Intentar endpoint de health o raíz
        response = requests.get(api_url, headers=headers, timeout=timeout)
        
        if response.status_code in [200, 201, 204]:
            result['connectivity_status'] = ConnectivityStatus.SUCCESS
            logger.info(f"[CONNECTIVITY][API][SUCCESS] {server_name}: HTTP {response.status_code}")
        elif response.status_code in [401, 403]:
            result['connectivity_status'] = ConnectivityStatus.AUTH_FAILED
            result['safe_error'] = f'HTTP {response.status_code}'
            logger.warning(f"[CONNECTIVITY][API][AUTH_FAILED] {server_name}: HTTP {response.status_code}")
        else:
            result['connectivity_status'] = ConnectivityStatus.QUERY_ERROR
            result['safe_error'] = f'HTTP {response.status_code}'
            logger.warning(f"[CONNECTIVITY][API][QUERY_ERROR] {server_name}: HTTP {response.status_code}")
            
    except Exception as e:
        error_msg = str(e).lower()
        
        if 'timeout' in error_msg or 'timed out' in error_msg:
            result['connectivity_status'] = ConnectivityStatus.SOURCE_UNREACHABLE
            result['safe_error'] = 'Connection timeout'
            logger.warning(f"[CONNECTIVITY][API][SOURCE_UNREACHABLE] {server_name}: Timeout")
        elif 'connection' in error_msg or 'refused' in error_msg:
            result['connectivity_status'] = ConnectivityStatus.SOURCE_UNREACHABLE
            result['safe_error'] = 'Connection refused'
            logger.warning(f"[CONNECTIVITY][API][SOURCE_UNREACHABLE] {server_name}: Refused")
        else:
            result['connectivity_status'] = ConnectivityStatus.QUERY_ERROR
            result['safe_error'] = f'{type(e).__name__}: {str(e)[:100]}'
            logger.warning(f"[CONNECTIVITY][API][QUERY_ERROR] {server_name}: {type(e).__name__}")
    
    result['duration_ms'] = int((time.time() - start_time) * 1000)
    return result


def run_connectivity_validation(
    servers: List[Dict],
    timeout: int = 10,
    dry_run: bool = False
) -> Dict:
    """
    Ejecuta validación de conectividad para todos los servidores.
    """
    report = {
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'mode': 'DRY_RUN' if dry_run else 'RUN',
        'status': 'SUCCESS',
        'servers_checked': len(servers),
        'connectivity_ok': 0,
        'source_unreachable': 0,
        'auth_failed': 0,
        'secret_decryption_error': 0,
        'query_error': 0,
        'configuration_missing': 0,
        'skipped': 0,
        'results': [],
        'warnings': [],
        'errors': []
    }
    
    if dry_run:
        print("\n[DRY-RUN] Solo se mostrará inventario, no se ejecutarán pruebas\n")
        for server in servers:
            report['results'].append({
                'server_id': server['id'],
                'name': server['name'],
                'system_type_normalized': server['system_type_normalized'],
                'connection_type': server['connection_type'],
                'config_origin': server['config_origin'],
                'secret_status': server['password_status'],
                'decrypt_ok': None,
                'connectivity_status': ConnectivityStatus.SKIPPED,
                'duration_ms': 0,
                'safe_error': 'Dry run - no test executed'
            })
            report['skipped'] += 1
        return report
    
    # Ejecutar pruebas
    for server in servers:
        connection_type = server.get('connection_type', 'DATA_SOURCE')
        system_type = server.get('system_type_normalized', '')
        
        # Determinar tipo de prueba
        if system_type == 'API' or connection_type == 'API':
            result = test_api_connectivity(server, timeout)
        else:
            result = test_sql_connectivity(server, timeout)
        
        # Contar resultados
        status = result['connectivity_status']
        if status == ConnectivityStatus.SUCCESS:
            report['connectivity_ok'] += 1
        elif status == ConnectivityStatus.SOURCE_UNREACHABLE:
            report['source_unreachable'] += 1
        elif status == ConnectivityStatus.AUTH_FAILED:
            report['auth_failed'] += 1
        elif status == ConnectivityStatus.SECRET_DECRYPTION_ERROR:
            report['secret_decryption_error'] += 1
        elif status == ConnectivityStatus.QUERY_ERROR:
            report['query_error'] += 1
        elif status == ConnectivityStatus.CONFIGURATION_MISSING:
            report['configuration_missing'] += 1
        else:
            report['skipped'] += 1
        
        # No incluir secretos en resultado
        clean_result = {k: v for k, v in result.items() if not k.startswith('_')}
        report['results'].append(clean_result)
    
    # Determinar status general
    if report['secret_decryption_error'] > 0:
        report['status'] = 'ERROR'
        report['errors'].append('Hay errores de descifrado de secretos')
    elif report['auth_failed'] > 0:
        report['status'] = 'PARTIAL'
        report['warnings'].append('Hay errores de autenticación')
    elif report['connectivity_ok'] == 0 and report['servers_checked'] > 0:
        report['status'] = 'ERROR'
        report['errors'].append('Ningún servidor conectó exitosamente')
    elif report['source_unreachable'] > 0:
        report['status'] = 'PARTIAL'
        report['warnings'].append('Algunos servidores son inaccesibles (red/VPN)')
    
    return report


def print_inventory(servers: List[Dict]):
    """Imprime inventario de servidores de forma segura."""
    print("\n" + "="*80)
    print("INVENTARIO DE SERVIDORES A PROBAR")
    print("="*80)
    
    print(f"\n{'ID':<10} | {'Nombre':<25} | {'System Type':<15} | {'Host':<22} | {'Secret':<12}")
    print("-"*95)
    
    for s in servers:
        id_short = s['id'][:8] + '...'
        name = s['name'][:24]
        sys_type = s['system_type_normalized'][:14]
        host = s['host'][:21]
        secret = s['password_status'][:11]
        active = '✓' if s['active'] else '○'
        
        print(f"{active} {id_short:<8} | {name:<25} | {sys_type:<15} | {host:<22} | {secret:<12}")
    
    print("="*80)
    print(f"Total: {len(servers)} servidores")
    
    # Resumen por tipo
    by_type = {}
    for s in servers:
        t = s['system_type_normalized']
        by_type[t] = by_type.get(t, 0) + 1
    
    print("\nPor tipo:")
    for t, count in sorted(by_type.items()):
        print(f"  - {t}: {count}")


def print_report(report: Dict):
    """Imprime resumen del reporte."""
    print("\n" + "="*80)
    print("REPORTE DE VALIDACIÓN DE CONECTIVIDAD")
    print("="*80)
    print(f"Timestamp: {report['timestamp']}")
    print(f"Modo: {report['mode']}")
    print(f"Status: {report['status']}")
    print()
    print(f"Servidores verificados: {report['servers_checked']}")
    print(f"Conectividad OK: {report['connectivity_ok']}")
    print(f"Source Unreachable: {report['source_unreachable']}")
    print(f"Auth Failed: {report['auth_failed']}")
    print(f"Secret Decryption Error: {report['secret_decryption_error']}")
    print(f"Query Error: {report['query_error']}")
    print(f"Configuration Missing: {report['configuration_missing']}")
    print(f"Skipped: {report['skipped']}")
    
    if report['warnings']:
        print(f"\nWarnings ({len(report['warnings'])}):")
        for w in report['warnings']:
            print(f"  - {w}")
    
    if report['errors']:
        print(f"\nErrores ({len(report['errors'])}):")
        for e in report['errors']:
            print(f"  - {e}")
    
    # Detalle por servidor
    print("\n" + "-"*80)
    print("DETALLE POR SERVIDOR")
    print("-"*80)
    
    for r in report['results']:
        status_icon = '✓' if r['connectivity_status'] == 'SUCCESS' else '✗' if r['connectivity_status'] in ['AUTH_FAILED', 'SECRET_DECRYPTION_ERROR'] else '⚠'
        decrypt_icon = '✓' if r.get('decrypt_ok') else '?' if r.get('decrypt_ok') is None else '✗'
        
        print(f"{status_icon} {r['name'][:30]:<30} | {r['connectivity_status']:<20} | decrypt:{decrypt_icon} | {r.get('duration_ms', 0)}ms")
        if r.get('safe_error'):
            print(f"    └─ {r['safe_error']}")
    
    print("="*80)


def main():
    parser = argparse.ArgumentParser(
        description='Validación de conectividad con secretos cifrados'
    )
    parser.add_argument('--dry-run', action='store_true', help='Solo inventario, no ejecutar pruebas')
    parser.add_argument('--run', action='store_true', help='Ejecutar pruebas de conectividad')
    parser.add_argument('--server-id', type=str, help='Probar solo un servidor específico')
    parser.add_argument('--system-type', type=str, help='Filtrar por SOFTRESTAURANT|MANAGEMENTPRO|API')
    parser.add_argument('--timeout', type=int, default=10, help='Timeout de conexión (default: 10)')
    parser.add_argument('--include-inactive', action='store_true', help='Incluir servidores inactivos')
    parser.add_argument('--include-core', action='store_true', help='Incluir servidores CORE')
    
    args = parser.parse_args()
    
    # Determinar modo
    if not args.dry_run and not args.run:
        args.dry_run = True  # Default es dry-run
    
    print("="*80)
    print("EDARSA HUB - Validación de Conectividad con Secretos Cifrados")
    print(f"Modo: {'DRY-RUN' if args.dry_run else 'EJECUTAR PRUEBAS'}")
    print("="*80)
    
    # 1. Validar secret manager
    print("\n1. Validando Secret Manager...")
    sm_status = validate_secret_manager()
    
    if not sm_status['encryption_available']:
        print("ERROR: Cifrado no disponible")
        return 1
    
    # 2. Obtener inventario
    print("\n2. Obteniendo inventario de servidores...")
    servers = get_servers_inventory(
        include_inactive=args.include_inactive,
        include_core=args.include_core,
        system_type_filter=args.system_type,
        server_id_filter=args.server_id
    )
    
    if not servers:
        print("No hay servidores que probar con los filtros especificados")
        return 0
    
    print_inventory(servers)
    
    # 3. Ejecutar validación
    print("\n3. Ejecutando validación de conectividad...")
    report = run_connectivity_validation(
        servers,
        timeout=args.timeout,
        dry_run=args.dry_run
    )
    
    print_report(report)
    
    # 4. Guardar reporte
    report_path = Path('/app/docs/reports/encrypted_connectivity_validation_report.json')
    report_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    print(f"\nReporte guardado en: {report_path}")
    
    return 0 if report['status'] in ['SUCCESS', 'PARTIAL'] else 1


if __name__ == '__main__':
    sys.exit(main())
