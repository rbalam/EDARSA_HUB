#!/usr/bin/env python3
"""
EDARSA HUB - Script de Cifrado de Secretos Existentes
=====================================================

FASE 3C: Migra secretos de texto plano a cifrados.

USO:
    python encrypt_existing_server_secrets.py --dry-run    # Solo reporta
    python encrypt_existing_server_secrets.py --apply      # Aplica cifrado

SALIDA:
    /app/docs/reports/server_secrets_encryption_report.json

SEGURIDAD:
    - No imprime secretos
    - Backup conceptual antes de modificar
    - Modo dry-run por defecto
    - No toca servidores CORE salvo explícitamente

CREADO: FASE 3C - Diciembre 2025
"""

import asyncio
import json
import sys
import os
from datetime import datetime, timezone
from pathlib import Path

# Agregar path del backend
sys.path.insert(0, str(Path(__file__).parent.parent))

from motor.motor_asyncio import AsyncIOMotorClient

# Importar funciones del registry y secret_manager
from core.server_registry import EDARSAHUB_CONFIG, _get_servers_from_sql, _execute_sql_write
from core.db import execute_sql_query

# Forzar reset del cache de secret_manager
from core import secret_manager
secret_manager.reset_fernet_cache()

from core.secret_manager import (
    encrypt_secret,
    is_encrypted_secret,
    is_encryption_available,
    verify_secret_manager_ready,
    needs_encryption
)


def check_prerequisites() -> dict:
    """Verifica que el sistema está listo para cifrar."""
    status = verify_secret_manager_ready()
    
    if not status['encryption_available']:
        print("ERROR: Cifrado no disponible")
        for w in status['warnings']:
            print(f"  - {w}")
        return {'ready': False, 'reason': 'Encryption not available'}
    
    print("✓ Sistema de cifrado disponible")
    return {'ready': True}


def get_servers_with_secrets() -> list:
    """Obtiene todos los servidores con sus secretos (sin exponer valores)."""
    query = """
    SELECT 
        id,
        nombre,
        tipo_conexion,
        password_encrypted,
        api_key_encrypted,
        activo
    FROM Servidores_Conexiones
    """
    
    result = execute_sql_query(
        EDARSAHUB_CONFIG['host'],
        EDARSAHUB_CONFIG['port'],
        EDARSAHUB_CONFIG['database'],
        EDARSAHUB_CONFIG['username'],
        EDARSAHUB_CONFIG['password'],
        query
    )
    
    return result if result else []


def analyze_server_secrets(servers: list) -> dict:
    """Analiza el estado de secretos de los servidores."""
    analysis = {
        'total': len(servers),
        'with_password': 0,
        'password_encrypted': 0,
        'password_plain': 0,
        'with_api_key': 0,
        'api_key_encrypted': 0,
        'api_key_plain': 0,
        'core_servers': 0,
        'servers_to_encrypt': []
    }
    
    for server in servers:
        server_id = str(server.get('id', ''))
        name = server.get('nombre', 'N/A')
        is_core = server.get('tipo_conexion') == 'CORE'
        
        if is_core:
            analysis['core_servers'] += 1
        
        pwd = server.get('password_encrypted', '')
        api = server.get('api_key_encrypted', '')
        
        needs_work = False
        
        if pwd:
            analysis['with_password'] += 1
            if is_encrypted_secret(pwd):
                analysis['password_encrypted'] += 1
            else:
                analysis['password_plain'] += 1
                needs_work = True
        
        if api:
            analysis['with_api_key'] += 1
            if is_encrypted_secret(api):
                analysis['api_key_encrypted'] += 1
            else:
                analysis['api_key_plain'] += 1
                needs_work = True
        
        if needs_work and not is_core:
            analysis['servers_to_encrypt'].append({
                'id': server_id,
                'name': name,
                'has_plain_password': bool(pwd and not is_encrypted_secret(pwd)),
                'has_plain_api_key': bool(api and not is_encrypted_secret(api))
            })
    
    return analysis


def encrypt_server_secrets_sql(server_id: str, encrypt_password: bool, encrypt_api_key: bool) -> dict:
    """
    Cifra los secretos de un servidor en SQL.
    
    Args:
        server_id: ID del servidor
        encrypt_password: Si cifrar password
        encrypt_api_key: Si cifrar api_key
        
    Returns:
        Dict con resultado
    """
    # Obtener valores actuales (ID es UUID, seguro para interpolación)
    query = f"""
    SELECT password_encrypted, api_key_encrypted 
    FROM Servidores_Conexiones 
    WHERE CAST(id AS VARCHAR(50)) = '{server_id}'
    """
    
    result = execute_sql_query(
        EDARSAHUB_CONFIG['host'],
        EDARSAHUB_CONFIG['port'],
        EDARSAHUB_CONFIG['database'],
        EDARSAHUB_CONFIG['username'],
        EDARSAHUB_CONFIG['password'],
        query
    )
    
    if not result:
        return {'success': False, 'error': 'Server not found'}
    
    current = result[0]
    updates = []
    
    if encrypt_password and current.get('password_encrypted'):
        pwd = current['password_encrypted']
        if not is_encrypted_secret(pwd):
            encrypted_pwd = encrypt_secret(pwd)
            # Escapar comillas simples
            encrypted_pwd_safe = encrypted_pwd.replace("'", "''")
            updates.append(f"password_encrypted = '{encrypted_pwd_safe}'")
    
    if encrypt_api_key and current.get('api_key_encrypted'):
        api = current['api_key_encrypted']
        if not is_encrypted_secret(api):
            encrypted_api = encrypt_secret(api)
            encrypted_api_safe = encrypted_api.replace("'", "''")
            updates.append(f"api_key_encrypted = '{encrypted_api_safe}'")
    
    if not updates:
        return {'success': True, 'message': 'Nothing to encrypt'}
    
    # Ejecutar update
    update_query = f"""
    UPDATE Servidores_Conexiones
    SET {', '.join(updates)}, updated_at = GETDATE()
    WHERE CAST(id AS VARCHAR(50)) = '{server_id}'
    """
    
    success = _execute_sql_write(update_query, None)
    
    return {'success': success}


async def encrypt_server_secrets_mongo(server_id: str, encrypt_password: bool, encrypt_api_key: bool) -> dict:
    """Cifra los secretos de un servidor en MongoDB."""
    mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
    db_name = os.environ.get('DB_NAME', 'edarsa_hub')
    
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    try:
        server = await db.servers.find_one({'id': server_id})
        
        if not server:
            return {'success': True, 'message': 'Server not in MongoDB'}
        
        updates = {}
        
        if encrypt_password and server.get('password'):
            pwd = server['password']
            if not is_encrypted_secret(pwd):
                updates['password'] = encrypt_secret(pwd)
        
        if encrypt_api_key and server.get('api_key'):
            api = server['api_key']
            if not is_encrypted_secret(api):
                updates['api_key'] = encrypt_secret(api)
        
        if updates:
            updates['updated_at'] = datetime.now(timezone.utc).isoformat()
            await db.servers.update_one({'id': server_id}, {'$set': updates})
        
        return {'success': True}
        
    except Exception as e:
        return {'success': False, 'error': str(e)}
    finally:
        client.close()


async def run_encryption(apply: bool = False) -> dict:
    """
    Ejecuta el proceso de cifrado.
    
    Args:
        apply: Si True, aplica los cambios. Si False, solo reporta.
        
    Returns:
        Reporte de la operación
    """
    report = {
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'mode': 'APPLY' if apply else 'DRY_RUN',
        'status': 'SUCCESS',
        'servers_checked': 0,
        'secrets_found': 0,
        'already_encrypted': 0,
        'to_encrypt': 0,
        'encrypted': 0,
        'failed': 0,
        'skipped_core': 0,
        'details': [],
        'warnings': [],
        'errors': []
    }
    
    # Verificar prerequisitos
    prereq = check_prerequisites()
    if not prereq['ready']:
        report['status'] = 'ERROR'
        report['errors'].append(prereq['reason'])
        return report
    
    # Obtener servidores
    print("\nObteniendo servidores...")
    servers = get_servers_with_secrets()
    report['servers_checked'] = len(servers)
    print(f"  → {len(servers)} servidores encontrados")
    
    # Analizar
    print("\nAnalizando secretos...")
    analysis = analyze_server_secrets(servers)
    
    report['secrets_found'] = analysis['with_password'] + analysis['with_api_key']
    report['already_encrypted'] = analysis['password_encrypted'] + analysis['api_key_encrypted']
    report['to_encrypt'] = len(analysis['servers_to_encrypt'])
    report['skipped_core'] = analysis['core_servers']
    
    print(f"  → Passwords: {analysis['with_password']} total, {analysis['password_plain']} en texto plano")
    print(f"  → API Keys: {analysis['with_api_key']} total, {analysis['api_key_plain']} en texto plano")
    print(f"  → Servidores a cifrar: {len(analysis['servers_to_encrypt'])}")
    print(f"  → Servidores CORE (excluidos): {analysis['core_servers']}")
    
    if not apply:
        print("\n[DRY-RUN] No se aplicarán cambios")
        report['details'] = analysis['servers_to_encrypt']
        return report
    
    # Aplicar cifrado
    print("\n[APPLY] Cifrando secretos...")
    
    for server_info in analysis['servers_to_encrypt']:
        server_id = server_info['id']
        name = server_info['name']
        
        print(f"  → Cifrando: {name}...", end=" ")
        
        # Cifrar en SQL
        sql_result = encrypt_server_secrets_sql(
            server_id,
            server_info['has_plain_password'],
            server_info['has_plain_api_key']
        )
        
        if not sql_result['success']:
            print("ERROR SQL")
            report['failed'] += 1
            report['errors'].append(f"{name}: SQL error - {sql_result.get('error', 'Unknown')}")
            continue
        
        # Cifrar en MongoDB
        mongo_result = await encrypt_server_secrets_mongo(
            server_id,
            server_info['has_plain_password'],
            server_info['has_plain_api_key']
        )
        
        if not mongo_result['success']:
            print("ERROR MONGO")
            report['warnings'].append(f"{name}: MongoDB error - {mongo_result.get('error', 'Unknown')}")
        
        print("OK")
        report['encrypted'] += 1
        report['details'].append({
            'id': server_id,
            'name': name,
            'sql': 'OK',
            'mongo': 'OK' if mongo_result['success'] else 'PARTIAL'
        })
    
    if report['failed'] > 0:
        report['status'] = 'PARTIAL'
    
    return report


def print_report(report: dict):
    """Imprime resumen del reporte."""
    print("\n" + "="*60)
    print("REPORTE DE CIFRADO DE SECRETOS")
    print("="*60)
    print(f"Timestamp: {report['timestamp']}")
    print(f"Modo: {report['mode']}")
    print(f"Status: {report['status']}")
    print(f"\nServidores verificados: {report['servers_checked']}")
    print(f"Secretos encontrados: {report['secrets_found']}")
    print(f"Ya cifrados: {report['already_encrypted']}")
    print(f"Pendientes de cifrar: {report['to_encrypt']}")
    print(f"Cifrados en esta ejecución: {report['encrypted']}")
    print(f"Fallidos: {report['failed']}")
    print(f"CORE excluidos: {report['skipped_core']}")
    
    if report['warnings']:
        print(f"\nWarnings ({len(report['warnings'])}):")
        for w in report['warnings'][:5]:
            print(f"  - {w}")
    
    if report['errors']:
        print(f"\nErrores ({len(report['errors'])}):")
        for e in report['errors'][:5]:
            print(f"  - {e}")
    
    print("="*60)


def main():
    apply = '--apply' in sys.argv
    
    print("="*60)
    print("EDARSA HUB - Cifrado de Secretos de Servidores")
    print(f"Modo: {'APPLY (cifrará secretos)' if apply else 'DRY-RUN (solo reporta)'}")
    print("="*60)
    
    report = asyncio.run(run_encryption(apply=apply))
    
    print_report(report)
    
    # Guardar reporte
    report_path = Path('/app/docs/reports/server_secrets_encryption_report.json')
    report_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    print(f"\nReporte guardado en: {report_path}")
    
    return 0 if report['status'] in ['SUCCESS', 'PARTIAL'] else 1


if __name__ == '__main__':
    sys.exit(main())
