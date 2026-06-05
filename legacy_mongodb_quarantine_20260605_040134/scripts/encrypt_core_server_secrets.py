#!/usr/bin/env python3
"""
EDARSA HUB - Script de Cifrado Controlado de Secretos CORE
==========================================================

FASE 3C.3: Cifra los secretos de servidores CORE de forma controlada.

USO:
    python encrypt_core_server_secrets.py --dry-run    # Solo reporta
    python encrypt_core_server_secrets.py --apply      # Aplica cifrado

IMPORTANTE:
    - Este script es el ÚNICO método autorizado para modificar secretos CORE
    - Los endpoints normales (POST/PUT/DELETE /api/servers) rechazan CORE
    - Siempre ejecutar --dry-run primero

SALIDA:
    /app/docs/reports/core_secrets_encryption_report.json

SEGURIDAD:
    - No imprime secretos
    - Valida descifrado después de cifrar
    - Requiere SERVER_SECRET_KEY

CREADO: FASE 3C.3 - Diciembre 2025
"""

import asyncio
import json
import sys
import os
from datetime import datetime, timezone
from pathlib import Path

# Agregar path del backend
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

# Cargar variables de entorno desde .env del backend
from dotenv import load_dotenv
env_path = backend_path / '.env'
if env_path.exists():
    load_dotenv(env_path)
    print(f"✓ Variables de entorno cargadas desde {env_path}")

from motor.motor_asyncio import AsyncIOMotorClient

# Importar funciones del registry y secret_manager
from core.server_registry import EDARSAHUB_CONFIG, _execute_sql_write
from core.db import execute_sql_query
from core.secret_manager import (
    encrypt_secret,
    decrypt_secret,
    is_encrypted_secret,
    is_encryption_available,
    verify_secret_manager_ready,
)


def check_prerequisites() -> dict:
    """Verifica que el sistema está listo para cifrar."""
    status = verify_secret_manager_ready()
    
    if not status['encryption_available']:
        print("ERROR: Cifrado no disponible")
        for w in status['warnings']:
            print(f"  - {w}")
        return {'ready': False, 'reason': 'Encryption not available'}
    
    print(f"✓ Sistema de cifrado disponible (fingerprint: {status.get('key_fingerprint', 'N/A')})")
    return {'ready': True}


def get_core_servers_sql() -> list:
    """Obtiene todos los servidores CORE desde SQL (sin exponer secretos)."""
    query = """
    SELECT 
        CAST(id AS VARCHAR(50)) as id,
        nombre,
        tipo_conexion,
        password_encrypted,
        api_key_encrypted,
        activo,
        mongodb_id
    FROM Servidores_Conexiones
    WHERE tipo_conexion = 'CORE'
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


def analyze_core_secrets(servers: list) -> dict:
    """Analiza el estado de secretos de los servidores CORE."""
    analysis = {
        'total': len(servers),
        'active': 0,
        'inactive': 0,
        'with_password': 0,
        'password_encrypted': 0,
        'password_plain': 0,
        'with_api_key': 0,
        'api_key_encrypted': 0,
        'api_key_plain': 0,
        'servers_to_encrypt': []
    }
    
    for server in servers:
        server_id = server.get('id', '')
        name = server.get('nombre', 'N/A')
        is_active = server.get('activo', False)
        
        if is_active:
            analysis['active'] += 1
        else:
            analysis['inactive'] += 1
        
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
        
        if needs_work:
            analysis['servers_to_encrypt'].append({
                'id': server_id,
                'name': name,
                'active': is_active,
                'mongodb_id': server.get('mongodb_id'),
                'has_plain_password': bool(pwd and not is_encrypted_secret(pwd)),
                'has_plain_api_key': bool(api and not is_encrypted_secret(api))
            })
    
    return analysis


def encrypt_core_server_sql(server_id: str, encrypt_password: bool, encrypt_api_key: bool) -> dict:
    """
    Cifra los secretos de un servidor CORE en SQL.
    
    Args:
        server_id: ID del servidor CORE
        encrypt_password: Si cifrar password
        encrypt_api_key: Si cifrar api_key
        
    Returns:
        Dict con resultado
    """
    # Obtener valores actuales
    query = f"""
    SELECT password_encrypted, api_key_encrypted 
    FROM Servidores_Conexiones 
    WHERE CAST(id AS VARCHAR(50)) = '{server_id}'
    AND tipo_conexion = 'CORE'
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
        return {'success': False, 'error': 'CORE server not found'}
    
    current = result[0]
    updates = []
    original_values = {}
    encrypted_values = {}
    
    if encrypt_password and current.get('password_encrypted'):
        pwd = current['password_encrypted']
        if not is_encrypted_secret(pwd):
            original_values['password'] = pwd  # Para validación de descifrado
            encrypted_pwd = encrypt_secret(pwd)
            encrypted_values['password'] = encrypted_pwd
            # Escapar comillas simples para SQL
            encrypted_pwd_safe = encrypted_pwd.replace("'", "''")
            updates.append(f"password_encrypted = '{encrypted_pwd_safe}'")
    
    if encrypt_api_key and current.get('api_key_encrypted'):
        api = current['api_key_encrypted']
        if not is_encrypted_secret(api):
            original_values['api_key'] = api
            encrypted_api = encrypt_secret(api)
            encrypted_values['api_key'] = encrypted_api
            encrypted_api_safe = encrypted_api.replace("'", "''")
            updates.append(f"api_key_encrypted = '{encrypted_api_safe}'")
    
    if not updates:
        return {'success': True, 'message': 'Nothing to encrypt', 'encrypted': 0}
    
    # Ejecutar update
    update_query = f"""
    UPDATE Servidores_Conexiones
    SET {', '.join(updates)}, updated_at = GETDATE()
    WHERE CAST(id AS VARCHAR(50)) = '{server_id}'
    AND tipo_conexion = 'CORE'
    """
    
    success = _execute_sql_write(update_query, None)
    
    if not success:
        return {'success': False, 'error': 'SQL update failed'}
    
    # Validar descifrado
    decrypt_ok = True
    for key in ['password', 'api_key']:
        if key in encrypted_values and key in original_values:
            try:
                decrypted = decrypt_secret(encrypted_values[key])
                if decrypted != original_values[key]:
                    decrypt_ok = False
            except Exception:
                decrypt_ok = False
    
    return {
        'success': True,
        'encrypted': len(updates),
        'decrypt_validation': decrypt_ok
    }


async def sync_core_to_mongo(server_id: str, mongodb_id: str) -> dict:
    """
    Sincroniza el estado de cifrado CORE a MongoDB (si tiene secretos).
    
    Note: MongoDB generalmente no tiene secretos de CORE, solo metadatos.
    Esta función es por completitud y consistencia.
    """
    if not mongodb_id:
        return {'success': True, 'message': 'No mongodb_id'}
    
    mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
    db_name = os.environ.get('DB_NAME', 'edarsa_hub')
    
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    try:
        server = await db.servers.find_one({'id': mongodb_id})
        
        if not server:
            return {'success': True, 'message': 'CORE not in MongoDB (normal)'}
        
        updates = {}
        pwd = server.get('password', '')
        api = server.get('api_key', '')
        
        if pwd and not is_encrypted_secret(pwd):
            updates['password'] = encrypt_secret(pwd)
        
        if api and not is_encrypted_secret(api):
            updates['api_key'] = encrypt_secret(api)
        
        if updates:
            updates['updated_at'] = datetime.now(timezone.utc).isoformat()
            await db.servers.update_one({'id': mongodb_id}, {'$set': updates})
            return {'success': True, 'encrypted_mongo': len(updates)}
        
        return {'success': True, 'message': 'No secrets in MongoDB'}
        
    except Exception as e:
        return {'success': False, 'error': str(e)}
    finally:
        client.close()


async def run_encryption(apply: bool = False) -> dict:
    """
    Ejecuta el proceso de cifrado de CORE.
    
    Args:
        apply: Si True, aplica los cambios. Si False, solo reporta.
        
    Returns:
        Reporte de la operación
    """
    report = {
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'mode': 'APPLY' if apply else 'DRY_RUN',
        'status': 'SUCCESS',
        'core_servers_checked': 0,
        'secrets_found': 0,
        'already_encrypted': 0,
        'to_encrypt': 0,
        'encrypted': 0,
        'decrypt_validation_ok': 0,
        'decrypt_validation_failed': 0,
        'mongo_synced': 0,
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
    
    # Obtener servidores CORE
    print("\nObteniendo servidores CORE...")
    servers = get_core_servers_sql()
    report['core_servers_checked'] = len(servers)
    print(f"  → {len(servers)} servidores CORE encontrados")
    
    # Analizar
    print("\nAnalizando secretos CORE...")
    analysis = analyze_core_secrets(servers)
    
    report['secrets_found'] = analysis['with_password'] + analysis['with_api_key']
    report['already_encrypted'] = analysis['password_encrypted'] + analysis['api_key_encrypted']
    report['to_encrypt'] = len(analysis['servers_to_encrypt'])
    
    print(f"  → CORE activos: {analysis['active']}")
    print(f"  → CORE inactivos: {analysis['inactive']}")
    print(f"  → Passwords: {analysis['with_password']} total, {analysis['password_plain']} en texto plano")
    print(f"  → API Keys: {analysis['with_api_key']} total, {analysis['api_key_plain']} en texto plano")
    print(f"  → Servidores CORE a cifrar: {len(analysis['servers_to_encrypt'])}")
    
    if not apply:
        print("\n[DRY-RUN] No se aplicarán cambios")
        report['details'] = [
            {
                'id': s['id'],
                'name': s['name'],
                'active': s['active'],
                'needs_password_encryption': s['has_plain_password'],
                'needs_api_key_encryption': s['has_plain_api_key']
            }
            for s in analysis['servers_to_encrypt']
        ]
        return report
    
    # Aplicar cifrado
    print("\n[APPLY] Cifrando secretos CORE...")
    
    for server_info in analysis['servers_to_encrypt']:
        server_id = server_info['id']
        name = server_info['name']
        mongodb_id = server_info.get('mongodb_id')
        
        print(f"\n  → Cifrando CORE: {name} ({'ACTIVO' if server_info['active'] else 'INACTIVO'})...")
        
        # Cifrar en SQL
        sql_result = encrypt_core_server_sql(
            server_id,
            server_info['has_plain_password'],
            server_info['has_plain_api_key']
        )
        
        if not sql_result['success']:
            print(f"    ERROR SQL: {sql_result.get('error', 'Unknown')}")
            report['errors'].append(f"{name}: SQL error - {sql_result.get('error', 'Unknown')}")
            continue
        
        report['encrypted'] += sql_result.get('encrypted', 0)
        
        if sql_result.get('decrypt_validation', False):
            report['decrypt_validation_ok'] += 1
            print(f"    ✓ SQL cifrado OK, descifrado validado")
        else:
            report['decrypt_validation_failed'] += 1
            report['warnings'].append(f"{name}: Descifrado no validado")
            print(f"    ⚠ SQL cifrado, descifrado NO validado")
        
        # Sincronizar MongoDB (generalmente no tiene secretos de CORE)
        mongo_result = await sync_core_to_mongo(server_id, mongodb_id)
        
        if mongo_result.get('encrypted_mongo'):
            report['mongo_synced'] += 1
            print(f"    ✓ MongoDB sincronizado")
        elif mongo_result.get('message'):
            print(f"    ✓ MongoDB: {mongo_result.get('message')}")
        
        report['details'].append({
            'id': server_id,
            'name': name,
            'active': server_info['active'],
            'sql': 'OK',
            'mongo': mongo_result.get('message', 'OK'),
            'decrypt_validated': sql_result.get('decrypt_validation', False)
        })
    
    if report['errors']:
        report['status'] = 'PARTIAL'
    elif report['decrypt_validation_failed'] > 0:
        report['status'] = 'WARNING'
    
    return report


def print_report(report: dict):
    """Imprime resumen del reporte."""
    print("\n" + "="*60)
    print("REPORTE DE CIFRADO DE SECRETOS CORE")
    print("="*60)
    print(f"Timestamp: {report['timestamp']}")
    print(f"Modo: {report['mode']}")
    print(f"Status: {report['status']}")
    print(f"\nServidores CORE verificados: {report['core_servers_checked']}")
    print(f"Secretos encontrados: {report['secrets_found']}")
    print(f"Ya cifrados: {report['already_encrypted']}")
    print(f"Pendientes de cifrar: {report['to_encrypt']}")
    print(f"Cifrados en esta ejecución: {report['encrypted']}")
    print(f"Descifrado validado OK: {report['decrypt_validation_ok']}")
    print(f"Descifrado no validado: {report['decrypt_validation_failed']}")
    print(f"MongoDB sincronizado: {report['mongo_synced']}")
    
    if report['warnings']:
        print(f"\nWarnings ({len(report['warnings'])}):")
        for w in report['warnings']:
            print(f"  - {w}")
    
    if report['errors']:
        print(f"\nErrores ({len(report['errors'])}):")
        for e in report['errors']:
            print(f"  - {e}")
    
    print("="*60)


def main():
    apply = '--apply' in sys.argv
    
    print("="*60)
    print("EDARSA HUB - Cifrado Controlado de Secretos CORE")
    print(f"Modo: {'APPLY (cifrará secretos CORE)' if apply else 'DRY-RUN (solo reporta)'}")
    print("="*60)
    
    if apply:
        print("\n⚠️  ADVERTENCIA: Este script modificará servidores CORE")
        print("   Los endpoints normales NO pueden modificar CORE")
        print("   Este es el único método autorizado\n")
    
    report = asyncio.run(run_encryption(apply=apply))
    
    print_report(report)
    
    # Guardar reporte
    report_path = Path('/app/docs/reports/core_secrets_encryption_report.json')
    report_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    print(f"\nReporte guardado en: {report_path}")
    
    return 0 if report['status'] in ['SUCCESS', 'WARNING'] else 1


if __name__ == '__main__':
    sys.exit(main())
