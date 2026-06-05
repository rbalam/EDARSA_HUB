#!/usr/bin/env python3
"""
EDARSA HUB - Script de Reconciliación SQL ↔ MongoDB
====================================================

FASE 3B.2: Compara servidores entre EDARSAHUB SQL y MongoDB.

USO:
    python reconcile_servers_sql_mongo.py [--apply]

    Sin --apply: modo dry-run (solo reporta diferencias)
    Con --apply: sincroniza MongoDB para que sea espejo de SQL

SALIDA:
    /app/docs/reports/servers_reconciliation_report.json

SEGURIDAD:
    - No imprime passwords ni api_keys
    - No modifica SQL (solo lee)
    - Solo escribe en MongoDB si --apply está presente

CREADO: FASE 3B.2 - Diciembre 2025
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
from dotenv import load_dotenv

# Cargar env
load_dotenv(Path(__file__).parent.parent / '.env')

# Importar funciones del registry
from core.server_registry import (
    EDARSAHUB_CONFIG,
    _get_servers_from_sql,
    build_legacy_mongo_server_document,
)
from core.db import execute_sql_query

# Campos sensibles que NO se deben imprimir
SENSITIVE_FIELDS = ['password', 'password_encrypted', 'api_key', 'api_key_encrypted']


def safe_server_summary(server: dict) -> dict:
    """Retorna resumen de servidor sin campos sensibles."""
    return {
        'id': server.get('id', 'N/A'),
        'name': server.get('name', server.get('nombre', 'N/A')),
        'system_type': server.get('system_type', 'N/A'),
        'host': server.get('host', 'N/A'),
        'active': server.get('active', server.get('activo', 'N/A')),
        'tipo_conexion': server.get('tipo_conexion', 'N/A'),
    }


async def reconcile(apply: bool = False) -> dict:
    """
    Ejecuta reconciliación SQL ↔ MongoDB.
    
    Args:
        apply: Si True, sincroniza MongoDB con SQL
        
    Returns:
        Reporte de reconciliación
    """
    report = {
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'mode': 'APPLY' if apply else 'DRY_RUN',
        'status': 'SUCCESS',
        'sql_count': 0,
        'mongo_count': 0,
        'matched': 0,
        'sql_only': [],
        'mongo_only': [],
        'diffs': [],
        'synced': [],
        'warnings': [],
        'errors': []
    }
    
    try:
        # 1. Obtener servidores desde SQL
        print("Obteniendo servidores desde SQL...")
        sql_servers = _get_servers_from_sql(
            filter_active=False,
            filter_visible_listado=False,
            exclude_core=False
        )
        report['sql_count'] = len(sql_servers)
        print(f"  → {len(sql_servers)} servidores en SQL")
        
        # Indexar por ID y mongodb_id
        sql_by_id = {s['id']: s for s in sql_servers}
        sql_by_mongodb_id = {s['mongodb_id']: s for s in sql_servers if s.get('mongodb_id')}
        
        # 2. Obtener servidores desde MongoDB
        print("Obteniendo servidores desde MongoDB...")
        mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
        db_name = os.environ.get('DB_NAME', 'edarsa_hub')
        
        client = AsyncIOMotorClient(mongo_url)
        db = client[db_name]
        
        mongo_servers = await db.servers.find({}, {'_id': 0}).to_list(1000)
        report['mongo_count'] = len(mongo_servers)
        print(f"  → {len(mongo_servers)} servidores en MongoDB")
        
        # Indexar por ID
        mongo_by_id = {s['id']: s for s in mongo_servers}
        
        # 3. Comparar SQL → MongoDB
        print("\nComparando SQL → MongoDB...")
        for sql_id, sql_server in sql_by_id.items():
            mongo_server = mongo_by_id.get(sql_id) or mongo_by_id.get(sql_server.get('mongodb_id'))
            
            if not mongo_server:
                # Servidor en SQL pero no en MongoDB
                report['sql_only'].append(safe_server_summary(sql_server))
                print(f"  [SQL_ONLY] {sql_server.get('name', sql_id)}")
                
                if apply:
                    try:
                        mongo_doc = build_legacy_mongo_server_document(sql_server)
                        # Remover campos sensibles del doc antes de insertar
                        await db.servers.insert_one(mongo_doc)
                        report['synced'].append(sql_id)
                        print("    → Sincronizado a MongoDB")
                    except Exception as e:
                        report['errors'].append(f"Error insertando {sql_id}: {str(e)}")
                        print(f"    → ERROR: {e}")
            else:
                report['matched'] += 1
                
                # Comparar campos críticos
                diffs = []
                
                sql_name = sql_server.get('name', sql_server.get('nombre', ''))
                mongo_name = mongo_server.get('name', mongo_server.get('nombre', ''))
                if sql_name != mongo_name:
                    diffs.append(f"name: SQL='{sql_name}' vs Mongo='{mongo_name}'")
                
                if sql_server.get('system_type') != mongo_server.get('system_type'):
                    diffs.append(f"system_type: SQL='{sql_server.get('system_type')}' vs Mongo='{mongo_server.get('system_type')}'")
                
                sql_active = sql_server.get('active', sql_server.get('activo'))
                mongo_active = mongo_server.get('active', mongo_server.get('activo'))
                if sql_active != mongo_active:
                    diffs.append(f"active: SQL={sql_active} vs Mongo={mongo_active}")
                
                if sql_server.get('host') != mongo_server.get('host'):
                    diffs.append(f"host: SQL='{sql_server.get('host')}' vs Mongo='{mongo_server.get('host')}'")
                
                if diffs:
                    report['diffs'].append({
                        'id': sql_id,
                        'name': sql_name,
                        'differences': diffs
                    })
                    print(f"  [DIFF] {sql_name}: {len(diffs)} diferencias")
                    
                    if apply:
                        try:
                            mongo_doc = build_legacy_mongo_server_document(sql_server)
                            await db.servers.update_one({'id': sql_id}, {'$set': mongo_doc})
                            report['synced'].append(sql_id)
                            print("    → Actualizado en MongoDB")
                        except Exception as e:
                            report['errors'].append(f"Error actualizando {sql_id}: {str(e)}")
                            print(f"    → ERROR: {e}")
        
        # 4. Comparar MongoDB → SQL (detectar huérfanos)
        print("\nComparando MongoDB → SQL...")
        for mongo_id, mongo_server in mongo_by_id.items():
            if mongo_id not in sql_by_id and mongo_id not in sql_by_mongodb_id:
                report['mongo_only'].append(safe_server_summary(mongo_server))
                report['warnings'].append(f"Servidor {mongo_id} existe en MongoDB pero NO en SQL (huérfano)")
                print(f"  [MONGO_ONLY] {mongo_server.get('name', mongo_id)} (huérfano)")
        
        # 5. Determinar status final
        if report['errors']:
            report['status'] = 'ERROR'
        elif report['sql_only'] or report['mongo_only'] or report['diffs']:
            report['status'] = 'DIFFS_FOUND'
        
        client.close()
        
    except Exception as e:
        report['status'] = 'ERROR'
        report['errors'].append(str(e))
        print(f"\nERROR: {e}")
    
    return report


def print_report(report: dict):
    """Imprime resumen del reporte."""
    print("\n" + "="*60)
    print("REPORTE DE RECONCILIACIÓN SQL ↔ MONGODB")
    print("="*60)
    print(f"Timestamp: {report['timestamp']}")
    print(f"Modo: {report['mode']}")
    print(f"Status: {report['status']}")
    print(f"\nServidores SQL: {report['sql_count']}")
    print(f"Servidores MongoDB: {report['mongo_count']}")
    print(f"Coincidentes: {report['matched']}")
    print(f"Solo en SQL: {len(report['sql_only'])}")
    print(f"Solo en MongoDB: {len(report['mongo_only'])}")
    print(f"Con diferencias: {len(report['diffs'])}")
    print(f"Sincronizados: {len(report['synced'])}")
    
    if report['warnings']:
        print(f"\nWarnings ({len(report['warnings'])}):")
        for w in report['warnings'][:5]:
            print(f"  - {w}")
        if len(report['warnings']) > 5:
            print(f"  ... y {len(report['warnings'])-5} más")
    
    if report['errors']:
        print(f"\nErrores ({len(report['errors'])}):")
        for e in report['errors'][:5]:
            print(f"  - {e}")
        if len(report['errors']) > 5:
            print(f"  ... y {len(report['errors'])-5} más")
    
    print("="*60)


def main():
    apply = '--apply' in sys.argv
    
    print("="*60)
    print("EDARSA HUB - Reconciliación SQL ↔ MongoDB")
    print(f"Modo: {'APPLY (sincronizará MongoDB)' if apply else 'DRY-RUN (solo reporta)'}")
    print("="*60 + "\n")
    
    report = asyncio.run(reconcile(apply=apply))
    
    print_report(report)
    
    # Guardar reporte
    report_path = Path('/app/docs/reports/servers_reconciliation_report.json')
    report_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    print(f"\nReporte guardado en: {report_path}")
    
    return 0 if report['status'] == 'SUCCESS' else 1


if __name__ == '__main__':
    sys.exit(main())
