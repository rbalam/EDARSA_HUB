#!/usr/bin/env python3
"""
EDARSA HUB - Rotación Controlada de Claves de Cifrado
=====================================================

FASE 4C: Script para rotar SERVER_SECRET_KEY de forma segura.

USO:
    # Dry-run (solo reporta, no modifica)
    python rotate_server_secret_key.py --dry-run
    
    # Apply (requiere confirmación)
    SERVER_SECRET_KEY_NEW="nueva_clave" SECRET_ROTATION_CONFIRM=YES python rotate_server_secret_key.py --apply

VARIABLES DE ENTORNO:
    SERVER_SECRET_KEY       - Clave de cifrado actual (obligatoria)
    SERVER_SECRET_KEY_NEW   - Nueva clave de cifrado (obligatoria para apply)
    SECRET_ROTATION_CONFIRM - Debe ser "YES" para ejecutar apply

OPCIONES:
    --dry-run           Solo verificar, no modificar (default)
    --apply             Ejecutar rotación real
    --include-mongo     Sincronizar MongoDB espejo
    --only-sql          Solo SQL, ignorar MongoDB
    --only-active       Solo servidores activos
    --include-core      Incluir servidores CORE
    --output PATH       Ruta del reporte JSON

SEGURIDAD:
    - NUNCA imprime claves ni secretos
    - Solo muestra fingerprints de claves
    - Valida descifrado antes y después de rotar
    - Aborta si hay errores de descifrado

CREADO: FASE 4C - Abril 2026
"""

import argparse
import json
import sys
import os
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any

# Agregar path del backend
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

# Cargar variables de entorno
from dotenv import load_dotenv
env_path = backend_path / '.env'
if env_path.exists():
    load_dotenv(env_path)

# Configurar logging seguro
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


# =============================================================================
# CONSTANTES
# =============================================================================

SECRET_FIELDS = ['password_encrypted', 'api_key_encrypted']
REPORT_PATH = '/app/docs/reports/server_secret_key_rotation_report.json'


# =============================================================================
# FUNCIONES DE ROTACIÓN
# =============================================================================

def get_environment_keys() -> Dict[str, Optional[str]]:
    """Obtiene las claves del entorno sin imprimirlas."""
    return {
        'current': os.environ.get('SERVER_SECRET_KEY'),
        'new': os.environ.get('SERVER_SECRET_KEY_NEW'),
        'confirm': os.environ.get('SECRET_ROTATION_CONFIRM', '').upper()
    }


def validate_prerequisites(keys: Dict, apply_mode: bool) -> Dict:
    """
    Valida que estén las claves necesarias.
    
    SEGURIDAD: No imprime claves.
    """
    from core.secret_manager import validate_rotation_keys, validate_fernet_key
    
    result = {
        'valid': False,
        'current_key_fingerprint': None,
        'new_key_fingerprint': None,
        'issues': []
    }
    
    # Validar clave actual
    if not keys['current']:
        result['issues'].append("SERVER_SECRET_KEY no está configurada")
        return result
    
    current_validation = validate_fernet_key(keys['current'])
    if not current_validation['valid']:
        result['issues'].append(f"SERVER_SECRET_KEY inválida: {current_validation['issues']}")
        return result
    result['current_key_fingerprint'] = current_validation['fingerprint']
    
    # Para apply, necesitamos clave nueva y confirmación
    if apply_mode:
        if not keys['new']:
            result['issues'].append("SERVER_SECRET_KEY_NEW no está configurada (requerida para apply)")
            return result
        
        if keys['confirm'] != 'YES':
            result['issues'].append("SECRET_ROTATION_CONFIRM debe ser 'YES' para ejecutar apply")
            return result
        
        # Validar rotación de claves
        rotation_validation = validate_rotation_keys(keys['current'], keys['new'])
        if not rotation_validation['valid']:
            result['issues'].extend(rotation_validation['issues'])
            return result
        
        result['new_key_fingerprint'] = rotation_validation['new_fingerprint']
    else:
        # Para dry-run, clave nueva es opcional pero la validamos si existe
        if keys['new']:
            new_validation = validate_fernet_key(keys['new'])
            if new_validation['valid']:
                result['new_key_fingerprint'] = new_validation['fingerprint']
            else:
                result['issues'].append(f"SERVER_SECRET_KEY_NEW presente pero inválida: {new_validation['issues']}")
    
    result['valid'] = True
    return result


def get_servers_for_rotation(
    include_inactive: bool = False,
    include_core: bool = False
) -> List[Dict]:
    """
    Obtiene servidores con secretos para rotar.
    
    SEGURIDAD: Incluye secretos cifrados pero no los imprime.
    """
    from core.db import execute_sql_query
    from core.server_registry import EDARSAHUB_CONFIG
    
    conditions = []
    
    if not include_inactive:
        conditions.append("activo = 1")
    
    if not include_core:
        conditions.append("(tipo_conexion != 'CORE' OR tipo_conexion IS NULL)")
    
    # Solo servidores con secretos
    conditions.append("""
        (
            (password_encrypted IS NOT NULL AND password_encrypted != '') OR
            (api_key_encrypted IS NOT NULL AND api_key_encrypted != '')
        )
    """)
    
    where_clause = " AND ".join(conditions) if conditions else "1=1"
    
    query = f"""
    SELECT 
        CAST(id AS VARCHAR(50)) as id,
        nombre,
        system_type,
        tipo_conexion,
        activo,
        password_encrypted,
        api_key_encrypted
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
    
    return result


def analyze_server_secrets(
    servers: List[Dict],
    current_key: str
) -> Dict:
    """
    Analiza secretos de servidores para rotación.
    
    SEGURIDAD: No imprime secretos.
    """
    from core.secret_manager import (
        is_encrypted_secret,
        decrypt_secret_with_key,
        SecretManagerError
    )
    
    analysis = {
        'total_servers': len(servers),
        'servers_with_secrets': 0,
        'encrypted_secrets': 0,
        'plaintext_secrets': 0,
        'decrypt_ok': 0,
        'decrypt_failed': 0,
        'to_rotate': 0,
        'details': []
    }
    
    for server in servers:
        server_detail = {
            'id': server['id'],
            'name': server['nombre'],
            'type': server.get('tipo_conexion', 'DATA_SOURCE'),
            'secrets': []
        }
        
        has_secret = False
        
        for field in SECRET_FIELDS:
            value = server.get(field, '')
            if not value:
                continue
            
            has_secret = True
            secret_detail = {
                'field': field,
                'encrypted': is_encrypted_secret(value),
                'decrypt_ok': False,
                'to_rotate': False
            }
            
            if is_encrypted_secret(value):
                analysis['encrypted_secrets'] += 1
                
                # Intentar descifrar
                try:
                    _ = decrypt_secret_with_key(value, current_key)
                    secret_detail['decrypt_ok'] = True
                    secret_detail['to_rotate'] = True
                    analysis['decrypt_ok'] += 1
                    analysis['to_rotate'] += 1
                except SecretManagerError:
                    secret_detail['error'] = 'DECRYPT_FAILED'
                    analysis['decrypt_failed'] += 1
            else:
                # Texto plano - también se puede rotar (cifrar)
                analysis['plaintext_secrets'] += 1
                secret_detail['decrypt_ok'] = True  # No necesita descifrar
                secret_detail['to_rotate'] = True
                analysis['to_rotate'] += 1
            
            server_detail['secrets'].append(secret_detail)
        
        if has_secret:
            analysis['servers_with_secrets'] += 1
            analysis['details'].append(server_detail)
    
    return analysis


def execute_rotation(
    servers: List[Dict],
    current_key: str,
    new_key: str,
    include_mongo: bool = False
) -> Dict:
    """
    Ejecuta la rotación de secretos.
    
    SEGURIDAD: No imprime claves ni secretos.
    """
    from core.db import execute_sql_query
    from core.server_registry import EDARSAHUB_CONFIG
    from core.secret_manager import (
        is_encrypted_secret,
        rotate_secret,
        decrypt_secret_with_key,
        SecretManagerError
    )
    
    result = {
        'rotated': 0,
        'failed': 0,
        'skipped': 0,
        'mongo_synced': 0,
        'errors': [],
        'details': []
    }
    
    for server in servers:
        server_id = server['id']
        server_name = server['nombre']
        
        logger.info(f"[SECRET_ROTATION][ROTATE_START] {server_name} ({server_id[:8]}...)")
        
        updates = {}
        server_detail = {
            'id': server_id,
            'name': server_name,
            'fields_rotated': [],
            'errors': []
        }
        
        for field in SECRET_FIELDS:
            value = server.get(field, '')
            if not value:
                continue
            
            try:
                # Rotar el secreto
                new_value = rotate_secret(value, current_key, new_key)
                
                # Validar que se puede descifrar con la nueva clave
                _ = decrypt_secret_with_key(new_value, new_key)
                
                updates[field] = new_value
                server_detail['fields_rotated'].append(field)
                
            except SecretManagerError as e:
                error_msg = f"{field}: {str(e)}"
                server_detail['errors'].append(error_msg)
                result['errors'].append(f"{server_name}: {error_msg}")
                result['failed'] += 1
                logger.error(f"[SECRET_ROTATION][ROTATE_ERROR] {server_name}: {field}")
        
        # Si hay updates, aplicar a SQL
        if updates:
            try:
                set_clauses = []
                for field in updates:
                    # Escapar valor para SQL
                    escaped_value = updates[field].replace("'", "''")
                    set_clauses.append(f"{field} = '{escaped_value}'")
                
                update_query = f"""
                UPDATE Servidores_Conexiones
                SET {', '.join(set_clauses)}
                WHERE CAST(id AS VARCHAR(50)) = '{server_id}'
                """
                
                execute_sql_query(
                    EDARSAHUB_CONFIG['host'],
                    EDARSAHUB_CONFIG['port'],
                    EDARSAHUB_CONFIG['database'],
                    EDARSAHUB_CONFIG['username'],
                    EDARSAHUB_CONFIG['password'],
                    update_query
                )
                
                result['rotated'] += len(server_detail['fields_rotated'])
                logger.info(f"[SECRET_ROTATION][ROTATE_SUCCESS] {server_name}: {len(server_detail['fields_rotated'])} campo(s)")
                
                # Sincronizar MongoDB si aplica
                if include_mongo:
                    try:
                        sync_to_mongodb(server_id, updates)
                        result['mongo_synced'] += 1
                        logger.info(f"[SECRET_ROTATION][MONGO_SYNC_SUCCESS] {server_name}")
                    except Exception as e:
                        logger.warning(f"[SECRET_ROTATION][PARTIAL_SYNC] {server_name}: MongoDB sync failed")
                        result['errors'].append(f"{server_name}: MongoDB sync failed - {type(e).__name__}")
                
            except Exception as e:
                error_msg = f"SQL update failed: {type(e).__name__}"
                server_detail['errors'].append(error_msg)
                result['errors'].append(f"{server_name}: {error_msg}")
                result['failed'] += 1
                logger.error(f"[SECRET_ROTATION][ROTATE_ERROR] {server_name}: SQL update failed")
        else:
            result['skipped'] += 1
        
        result['details'].append(server_detail)
    
    return result


def sync_to_mongodb(server_id: str, updates: Dict):
    """P5-3C: NO-MONGO. La rotación de secretos se persiste solo en EDARSAHUB SQL. No-op."""
    return None


def generate_report(
    mode: str,
    prerequisite_check: Dict,
    analysis: Optional[Dict],
    rotation_result: Optional[Dict],
    output_path: str
) -> Dict:
    """
    Genera reporte JSON de la rotación.
    
    SEGURIDAD: No incluye claves ni secretos.
    """
    report = {
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'mode': mode,
        'status': 'SUCCESS',
        'current_key_fingerprint': prerequisite_check.get('current_key_fingerprint'),
        'new_key_fingerprint': prerequisite_check.get('new_key_fingerprint'),
        'servers_checked': 0,
        'secrets_found': 0,
        'encrypted_secrets': 0,
        'plaintext_secrets': 0,
        'decrypt_ok': 0,
        'decrypt_failed': 0,
        'to_rotate': 0,
        'rotated': 0,
        'failed': 0,
        'skipped': 0,
        'mongo_synced': 0,
        'warnings': [],
        'errors': []
    }
    
    if not prerequisite_check.get('valid'):
        report['status'] = 'ERROR'
        report['errors'] = prerequisite_check.get('issues', [])
        return report
    
    if analysis:
        report['servers_checked'] = analysis['total_servers']
        report['secrets_found'] = analysis['encrypted_secrets'] + analysis['plaintext_secrets']
        report['encrypted_secrets'] = analysis['encrypted_secrets']
        report['plaintext_secrets'] = analysis['plaintext_secrets']
        report['decrypt_ok'] = analysis['decrypt_ok']
        report['decrypt_failed'] = analysis['decrypt_failed']
        report['to_rotate'] = analysis['to_rotate']
        
        if analysis['decrypt_failed'] > 0:
            report['status'] = 'PARTIAL'
            report['warnings'].append(f"{analysis['decrypt_failed']} secreto(s) no se pueden descifrar con clave actual")
    
    if rotation_result:
        report['rotated'] = rotation_result['rotated']
        report['failed'] = rotation_result['failed']
        report['skipped'] = rotation_result['skipped']
        report['mongo_synced'] = rotation_result['mongo_synced']
        report['errors'].extend(rotation_result['errors'])
        
        if rotation_result['failed'] > 0:
            report['status'] = 'PARTIAL'
        elif rotation_result['rotated'] == 0 and report['to_rotate'] > 0:
            report['status'] = 'ERROR'
    
    # Guardar reporte
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    return report


def print_report(report: Dict):
    """Imprime resumen del reporte (sin secretos)."""
    print("\n" + "="*70)
    print("REPORTE DE ROTACIÓN DE CLAVES")
    print("="*70)
    print(f"Modo: {report['mode']}")
    print(f"Status: {report['status']}")
    print(f"Timestamp: {report['timestamp']}")
    print()
    print(f"Fingerprint clave actual: {report['current_key_fingerprint']}")
    print(f"Fingerprint clave nueva: {report['new_key_fingerprint'] or 'N/A'}")
    print()
    print(f"Servidores verificados: {report['servers_checked']}")
    print(f"Secretos encontrados: {report['secrets_found']}")
    print(f"  - Cifrados: {report['encrypted_secrets']}")
    print(f"  - Texto plano: {report['plaintext_secrets']}")
    print(f"Descifrado OK: {report['decrypt_ok']}")
    print(f"Descifrado fallido: {report['decrypt_failed']}")
    print(f"A rotar: {report['to_rotate']}")
    print()
    
    if report['mode'] == 'APPLY':
        print(f"Rotados: {report['rotated']}")
        print(f"Fallidos: {report['failed']}")
        print(f"Omitidos: {report['skipped']}")
        print(f"MongoDB sincronizado: {report['mongo_synced']}")
    
    if report['warnings']:
        print(f"\nWarnings ({len(report['warnings'])}):")
        for w in report['warnings']:
            print(f"  - {w}")
    
    if report['errors']:
        print(f"\nErrores ({len(report['errors'])}):")
        for e in report['errors']:
            print(f"  - {e}")
    
    print("="*70)


def main():
    parser = argparse.ArgumentParser(
        description='Rotación controlada de claves de cifrado'
    )
    parser.add_argument('--dry-run', action='store_true', help='Solo verificar, no modificar (default)')
    parser.add_argument('--apply', action='store_true', help='Ejecutar rotación real')
    parser.add_argument('--include-mongo', action='store_true', help='Sincronizar MongoDB espejo')
    parser.add_argument('--only-sql', action='store_true', help='Solo SQL, ignorar MongoDB')
    parser.add_argument('--only-active', action='store_true', default=True, help='Solo servidores activos (default)')
    parser.add_argument('--include-inactive', action='store_true', help='Incluir servidores inactivos')
    parser.add_argument('--include-core', action='store_true', help='Incluir servidores CORE')
    parser.add_argument('--output', type=str, default=REPORT_PATH, help='Ruta del reporte JSON')
    
    args = parser.parse_args()
    
    # Determinar modo
    apply_mode = args.apply and not args.dry_run
    mode = 'APPLY' if apply_mode else 'DRY_RUN'
    
    print("="*70)
    print("EDARSA HUB - Rotación de Claves de Cifrado")
    print(f"Modo: {mode}")
    print("="*70)
    
    # 1. Obtener y validar claves
    print("\n1. Validando claves de cifrado...")
    keys = get_environment_keys()
    prerequisite_check = validate_prerequisites(keys, apply_mode)
    
    if not prerequisite_check['valid']:
        print(f"   ✗ Validación fallida:")
        for issue in prerequisite_check['issues']:
            print(f"     - {issue}")
        
        report = generate_report(mode, prerequisite_check, None, None, args.output)
        print(f"\nReporte guardado en: {args.output}")
        return 1
    
    print(f"   ✓ Clave actual válida (fingerprint: {prerequisite_check['current_key_fingerprint']})")
    if prerequisite_check.get('new_key_fingerprint'):
        print(f"   ✓ Clave nueva válida (fingerprint: {prerequisite_check['new_key_fingerprint']})")
    
    # 2. Obtener servidores
    print("\n2. Obteniendo servidores con secretos...")
    include_inactive = args.include_inactive
    servers = get_servers_for_rotation(
        include_inactive=include_inactive,
        include_core=args.include_core
    )
    print(f"   → {len(servers)} servidores encontrados")
    
    # 3. Analizar secretos
    print("\n3. Analizando secretos...")
    analysis = analyze_server_secrets(servers, keys['current'])
    print(f"   → Servidores con secretos: {analysis['servers_with_secrets']}")
    print(f"   → Secretos cifrados: {analysis['encrypted_secrets']}")
    print(f"   → Secretos en texto plano: {analysis['plaintext_secrets']}")
    print(f"   → Descifrado OK: {analysis['decrypt_ok']}")
    print(f"   → Descifrado fallido: {analysis['decrypt_failed']}")
    print(f"   → A rotar: {analysis['to_rotate']}")
    
    rotation_result = None
    
    # 4. Ejecutar rotación si es apply
    if apply_mode:
        if analysis['decrypt_failed'] > 0:
            print("\n   ⚠ Hay secretos que no se pueden descifrar. Continuar puede dejar datos inconsistentes.")
            print("   Abortando rotación por seguridad.")
            report = generate_report(mode, prerequisite_check, analysis, None, args.output)
            print_report(report)
            print(f"\nReporte guardado en: {args.output}")
            return 1
        
        print("\n4. Ejecutando rotación...")
        logger.info("[SECRET_ROTATION][DRY_RUN_START]" if not apply_mode else "[SECRET_ROTATION][APPLY_START]")
        
        rotation_result = execute_rotation(
            servers,
            keys['current'],
            keys['new'],
            include_mongo=args.include_mongo and not args.only_sql
        )
        
        print(f"   → Secretos rotados: {rotation_result['rotated']}")
        print(f"   → Fallidos: {rotation_result['failed']}")
        print(f"   → Omitidos: {rotation_result['skipped']}")
        if args.include_mongo:
            print(f"   → MongoDB sincronizado: {rotation_result['mongo_synced']}")
        
        logger.info("[SECRET_ROTATION][COMPLETE]")
    else:
        print("\n4. [DRY-RUN] No se ejecutará rotación")
    
    # 5. Generar reporte
    report = generate_report(mode, prerequisite_check, analysis, rotation_result, args.output)
    print_report(report)
    print(f"\nReporte guardado en: {args.output}")
    
    # 6. Instrucciones post-rotación
    if apply_mode and rotation_result and rotation_result['rotated'] > 0:
        print("\n" + "="*70)
        print("PASOS POST-ROTACIÓN")
        print("="*70)
        print("1. Cambiar SERVER_SECRET_KEY en .env a la nueva clave")
        print("2. Reiniciar el backend: sudo supervisorctl restart backend")
        print("3. Validar con: python scripts/validate_encrypted_server_connectivity.py --run")
        print("4. Mantener clave anterior resguardada temporalmente")
        print("5. NUNCA guardar claves en el repositorio")
        print("="*70)
    
    return 0 if report['status'] in ['SUCCESS', 'PARTIAL'] else 1


if __name__ == '__main__':
    sys.exit(main())
