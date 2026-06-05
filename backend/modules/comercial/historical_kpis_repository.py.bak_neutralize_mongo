"""
EDARSA HUB - Repository SQL para KPIs Comerciales Históricos
=============================================================

Funciones de acceso a datos para la tabla `Comercial_KPIs_Historico` en EDARSAHUB SQL.

REGLA MAESTRA:
EDARSAHUB SQL es el cerebro. MongoDB NO es destino final de históricos.

UPSERT IDEMPOTENTE:
- Si existe registro con misma llave única, actualiza métricas y updated_at
- Si no existe, inserta nuevo registro
- Mantiene created_at original en actualizaciones
- Incrementa version en cada actualización

Fecha: 2026-04-26
Versión: 1.0
"""

import os
import logging
import hashlib
import json
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timezone
from dotenv import load_dotenv

# Cargar .env
load_dotenv('/app/backend/.env')

from core.db import execute_sql_query
from core.secret_manager import decrypt_secret, is_encrypted_secret

logger = logging.getLogger(__name__)

# ============================================================================
# CONSTANTES
# ============================================================================

TABLE_NAME = "Comercial_KPIs_Historico"
EDARSAHUB_SERVER_ID = "f8a9049a-96e8-4210-84ae-595ffa2822fa"

# ============================================================================
# CONEXIÓN A EDARSAHUB
# ============================================================================

_edarsahub_credentials = None


async def _get_edarsahub_credentials() -> Dict:
    """Obtiene credenciales de EDARSAHUB desde MongoDB servers."""
    global _edarsahub_credentials
    
    if _edarsahub_credentials:
        return _edarsahub_credentials
    
    from motor.motor_asyncio import AsyncIOMotorClient
    
    client = AsyncIOMotorClient(os.environ.get('MONGO_URL'))
    db = client['edarsa_hub']
    
    server = await db.servers.find_one({'id': EDARSAHUB_SERVER_ID})
    
    if not server:
        client.close()
        raise RuntimeError(f"Servidor EDARSAHUB ({EDARSAHUB_SERVER_ID}) no encontrado")
    
    password = server.get('password', '')
    if password and is_encrypted_secret(password):
        password = decrypt_secret(password)
    
    _edarsahub_credentials = {
        'host': server.get('host'),
        'port': server.get('port', 1433),
        'database': server.get('database'),
        'username': server.get('username'),
        'password': password
    }
    
    client.close()
    return _edarsahub_credentials


def _get_edarsahub_credentials_sync() -> Dict:
    """Versión síncrona para obtener credenciales."""
    import asyncio
    return asyncio.get_event_loop().run_until_complete(_get_edarsahub_credentials())


def _execute_edarsahub_query(query: str, credentials: Dict = None) -> List[Dict]:
    """Ejecuta query en EDARSAHUB."""
    if not credentials:
        credentials = _get_edarsahub_credentials_sync()
    
    return execute_sql_query(
        credentials['host'],
        credentials['port'],
        credentials['database'],
        credentials['username'],
        credentials['password'],
        query
    )


# ============================================================================
# FUNCIONES AUXILIARES
# ============================================================================

def compute_source_hash(kpi_data: Dict) -> str:
    """Calcula hash de los datos de origen para trazabilidad."""
    # Incluir campos clave en el hash
    hash_content = json.dumps({
        'ventas': kpi_data.get('ventas_total', 0),
        'tickets': kpi_data.get('tickets_total', 0),
        'pax': kpi_data.get('pax_total', 0),
        'ticket_promedio': kpi_data.get('ticket_promedio', 0),
        'propinas': kpi_data.get('propinas_total', 0)
    }, sort_keys=True)
    
    return hashlib.sha256(hash_content.encode()).hexdigest()[:64]


def _escape_sql_string(value: Any) -> str:
    """Escapa strings para SQL Server."""
    if value is None:
        return "NULL"
    if isinstance(value, (int, float)):
        return str(value)
    # Escapar comillas simples
    escaped = str(value).replace("'", "''")
    return f"N'{escaped}'"


# ============================================================================
# VERIFICACIÓN DE TABLA
# ============================================================================

async def ensure_historical_kpis_table_exists() -> bool:
    """
    Verifica que la tabla Comercial_KPIs_Historico existe.
    NO la crea automáticamente - debe usarse migración controlada.
    """
    credentials = await _get_edarsahub_credentials()
    
    query = """
    SELECT COUNT(*) as exists_flag 
    FROM INFORMATION_SCHEMA.TABLES 
    WHERE TABLE_NAME = 'Comercial_KPIs_Historico'
    """
    
    try:
        result = _execute_edarsahub_query(query, credentials)
        exists = result[0].get('exists_flag', 0) if result else 0
        return exists > 0
    except Exception as e:
        logger.error(f"[HISTORICAL_KPI_SQL] Error verificando tabla: {e}")
        return False


# ============================================================================
# UPSERT IDEMPOTENTE
# ============================================================================

async def upsert_comercial_kpi_historico(
    record: Dict,
    credentials: Dict = None
) -> Dict:
    """
    Realiza UPSERT idempotente de un KPI comercial histórico en SQL.
    
    Args:
        record: Diccionario con los campos del KPI
        credentials: Credenciales de EDARSAHUB (opcional, se obtienen automáticamente)
    
    Returns:
        Dict con resultado: {'action': 'INSERT'|'UPDATE'|'SKIP', 'id': uuid, 'error': str|None}
    """
    if not credentials:
        credentials = await _get_edarsahub_credentials()
    
    # Campos obligatorios
    server_id = record.get('server_id')
    sucursal_id = str(record.get('sucursal_id', 'DEFAULT'))
    system_type = record.get('system_type_normalized', record.get('system_type', 'UNKNOWN'))
    fecha = record.get('fecha')
    kpi_tipo = record.get('kpi_tipo', 'DIARIO')
    run_id = record.get('run_id', 'MANUAL')
    
    if not all([server_id, fecha]):
        return {'action': 'SKIP', 'error': 'Campos obligatorios faltantes (server_id, fecha)'}
    
    # Métricas
    ventas_total = float(record.get('ventas_total', record.get('ventas', 0)) or 0)
    tickets_total = int(record.get('tickets_total', record.get('cheques', 0)) or 0)
    pax_total = int(record.get('pax_total', record.get('pax', 0)) or 0)
    ticket_promedio = float(record.get('ticket_promedio', 0) or 0)
    propinas_total = float(record.get('propinas_total', record.get('propinas', 0)) or 0)
    
    # Metadata
    sucursal_nombre = record.get('sucursal_nombre', '')
    empresa_id = record.get('empresa_id', '')
    unidad_negocio_id = record.get('unidad_negocio_id', '')
    source_batch_start = record.get('source_batch_start')
    source_batch_end = record.get('source_batch_end')
    
    # Calcular hash
    source_hash = compute_source_hash({
        'ventas_total': ventas_total,
        'tickets_total': tickets_total,
        'pax_total': pax_total,
        'ticket_promedio': ticket_promedio,
        'propinas_total': propinas_total
    })
    
    # Metadata JSON
    metadata = {
        'empresa_nombre': record.get('empresa_nombre', ''),
        'source_type': record.get('source_type', 'HISTORICAL_LOAD'),
        'original_run_id': run_id
    }
    metadata_json = json.dumps(metadata, ensure_ascii=False)
    
    try:
        # 1. Verificar si existe
        check_query = f"""
        SELECT id, version, source_hash
        FROM {TABLE_NAME}
        WHERE server_id = {_escape_sql_string(server_id)}
          AND sucursal_id = {_escape_sql_string(sucursal_id)}
          AND system_type_normalized = {_escape_sql_string(system_type)}
          AND fecha = {_escape_sql_string(fecha)}
          AND kpi_tipo = {_escape_sql_string(kpi_tipo)}
        """
        
        existing = _execute_edarsahub_query(check_query, credentials)
        
        if existing and len(existing) > 0:
            # Registro existe - verificar si hay cambios
            existing_record = existing[0]
            existing_hash = existing_record.get('source_hash', '')
            
            if existing_hash == source_hash:
                # Sin cambios - SKIP
                return {
                    'action': 'SKIP',
                    'id': str(existing_record.get('id')),
                    'reason': 'No changes detected'
                }
            
            # Hay cambios - UPDATE
            new_version = (existing_record.get('version', 1) or 1) + 1
            
            update_query = f"""
            UPDATE {TABLE_NAME}
            SET run_id = {_escape_sql_string(run_id)},
                sucursal_nombre = {_escape_sql_string(sucursal_nombre)},
                empresa_id = {_escape_sql_string(empresa_id)},
                unidad_negocio_id = {_escape_sql_string(unidad_negocio_id)},
                ventas_total = {ventas_total},
                tickets_total = {tickets_total},
                pax_total = {pax_total},
                ticket_promedio = {ticket_promedio},
                propinas_total = {propinas_total},
                source_hash = {_escape_sql_string(source_hash)},
                source_batch_start = {_escape_sql_string(source_batch_start) if source_batch_start else 'NULL'},
                source_batch_end = {_escape_sql_string(source_batch_end) if source_batch_end else 'NULL'},
                metadata_json = {_escape_sql_string(metadata_json)},
                version = {new_version},
                updated_at = SYSUTCDATETIME()
            WHERE server_id = {_escape_sql_string(server_id)}
              AND sucursal_id = {_escape_sql_string(sucursal_id)}
              AND system_type_normalized = {_escape_sql_string(system_type)}
              AND fecha = {_escape_sql_string(fecha)}
              AND kpi_tipo = {_escape_sql_string(kpi_tipo)}
            """
            
            _execute_edarsahub_query(update_query, credentials)
            
            logger.info(f"[HISTORICAL_KPI_SQL] UPDATE: server={server_id}, suc={sucursal_id}, fecha={fecha}")
            
            return {
                'action': 'UPDATE',
                'id': str(existing_record.get('id')),
                'version': new_version
            }
        
        else:
            # No existe - INSERT
            insert_query = f"""
            INSERT INTO {TABLE_NAME} (
                run_id, server_id, sucursal_id, sucursal_nombre,
                empresa_id, unidad_negocio_id, system_type_normalized,
                fecha, kpi_tipo, ventas_total, tickets_total, pax_total,
                ticket_promedio, propinas_total, source_hash,
                source_batch_start, source_batch_end, metadata_json,
                version, created_at, updated_at
            ) VALUES (
                {_escape_sql_string(run_id)},
                {_escape_sql_string(server_id)},
                {_escape_sql_string(sucursal_id)},
                {_escape_sql_string(sucursal_nombre)},
                {_escape_sql_string(empresa_id)},
                {_escape_sql_string(unidad_negocio_id)},
                {_escape_sql_string(system_type)},
                {_escape_sql_string(fecha)},
                {_escape_sql_string(kpi_tipo)},
                {ventas_total},
                {tickets_total},
                {pax_total},
                {ticket_promedio},
                {propinas_total},
                {_escape_sql_string(source_hash)},
                {_escape_sql_string(source_batch_start) if source_batch_start else 'NULL'},
                {_escape_sql_string(source_batch_end) if source_batch_end else 'NULL'},
                {_escape_sql_string(metadata_json)},
                1,
                SYSUTCDATETIME(),
                SYSUTCDATETIME()
            )
            """
            
            _execute_edarsahub_query(insert_query, credentials)
            
            logger.info(f"[HISTORICAL_KPI_SQL] INSERT: server={server_id}, suc={sucursal_id}, fecha={fecha}")
            
            return {
                'action': 'INSERT',
                'version': 1
            }
    
    except Exception as e:
        logger.error(f"[HISTORICAL_KPI_SQL] Error en UPSERT: {e}")
        return {
            'action': 'ERROR',
            'error': str(e)
        }


async def bulk_upsert_comercial_kpis_historico(
    records: List[Dict],
    credentials: Dict = None
) -> Dict:
    """
    Realiza UPSERT masivo de KPIs comerciales históricos.
    
    Returns:
        Dict con contadores: {'inserted': int, 'updated': int, 'skipped': int, 'errors': int}
    """
    if not credentials:
        credentials = await _get_edarsahub_credentials()
    
    counters = {
        'inserted': 0,
        'updated': 0,
        'skipped': 0,
        'errors': 0
    }
    
    for record in records:
        result = await upsert_comercial_kpi_historico(record, credentials)
        action = result.get('action', 'ERROR')
        
        if action == 'INSERT':
            counters['inserted'] += 1
        elif action == 'UPDATE':
            counters['updated'] += 1
        elif action == 'SKIP':
            counters['skipped'] += 1
        else:
            counters['errors'] += 1
    
    return counters


# ============================================================================
# CONSULTAS
# ============================================================================

async def get_existing_kpi_keys(
    server_id: str,
    sucursal_id: str = None,
    fecha_inicio: str = None,
    fecha_fin: str = None,
    kpi_tipo: str = None
) -> List[Dict]:
    """
    Obtiene llaves de KPIs existentes para evitar duplicados.
    """
    credentials = await _get_edarsahub_credentials()
    
    conditions = [f"server_id = {_escape_sql_string(server_id)}"]
    
    if sucursal_id:
        conditions.append(f"sucursal_id = {_escape_sql_string(sucursal_id)}")
    if fecha_inicio:
        conditions.append(f"fecha >= {_escape_sql_string(fecha_inicio)}")
    if fecha_fin:
        conditions.append(f"fecha <= {_escape_sql_string(fecha_fin)}")
    if kpi_tipo:
        conditions.append(f"kpi_tipo = {_escape_sql_string(kpi_tipo)}")
    
    query = f"""
    SELECT server_id, sucursal_id, system_type_normalized, fecha, kpi_tipo, source_hash
    FROM {TABLE_NAME}
    WHERE {' AND '.join(conditions)}
    """
    
    try:
        return _execute_edarsahub_query(query, credentials) or []
    except Exception as e:
        logger.error(f"[HISTORICAL_KPI_SQL] Error en get_existing_kpi_keys: {e}")
        return []


async def count_kpis_by_run_id(run_id: str) -> int:
    """Cuenta KPIs por run_id."""
    credentials = await _get_edarsahub_credentials()
    
    query = f"""
    SELECT COUNT(*) as total
    FROM {TABLE_NAME}
    WHERE run_id = {_escape_sql_string(run_id)}
    """
    
    try:
        result = _execute_edarsahub_query(query, credentials)
        return result[0].get('total', 0) if result else 0
    except Exception as e:
        logger.error(f"[HISTORICAL_KPI_SQL] Error en count_kpis_by_run_id: {e}")
        return 0


async def detect_duplicates(
    server_id: str = None,
    fecha_inicio: str = None,
    fecha_fin: str = None
) -> List[Dict]:
    """
    Detecta duplicados en la tabla (no debería haber si el índice único funciona).
    """
    credentials = await _get_edarsahub_credentials()
    
    conditions = []
    if server_id:
        conditions.append(f"server_id = {_escape_sql_string(server_id)}")
    if fecha_inicio:
        conditions.append(f"fecha >= {_escape_sql_string(fecha_inicio)}")
    if fecha_fin:
        conditions.append(f"fecha <= {_escape_sql_string(fecha_fin)}")
    
    where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    
    query = f"""
    SELECT 
        server_id,
        sucursal_id,
        system_type_normalized,
        fecha,
        kpi_tipo,
        COUNT(*) as total
    FROM {TABLE_NAME}
    {where_clause}
    GROUP BY server_id, sucursal_id, system_type_normalized, fecha, kpi_tipo
    HAVING COUNT(*) > 1
    """
    
    try:
        return _execute_edarsahub_query(query, credentials) or []
    except Exception as e:
        logger.error(f"[HISTORICAL_KPI_SQL] Error en detect_duplicates: {e}")
        return []


# ============================================================================
# MIGRACIÓN DE STAGING MONGODB A SQL
# ============================================================================

async def migrate_staging_mongo_kpis_to_sql(
    run_id: str = None,
    dry_run: bool = True
) -> Dict:
    """
    Migra KPIs de staging en MongoDB a destino final en SQL.
    
    Args:
        run_id: Filtrar por run_id específico (None = todos)
        dry_run: Si True, solo simula sin escribir
    
    Returns:
        Dict con resultados de migración
    """
    from motor.motor_asyncio import AsyncIOMotorClient
    
    client = AsyncIOMotorClient(os.environ.get('MONGO_URL'))
    db = client['edarsa_hub']
    
    # Filtro
    mongo_filter = {}
    if run_id:
        mongo_filter['source.run_id'] = run_id
    
    results = {
        'dry_run': dry_run,
        'run_id_filter': run_id,
        'mongo_records_found': 0,
        'sql_inserted': 0,
        'sql_updated': 0,
        'sql_skipped': 0,
        'sql_errors': 0,
        'records': []
    }
    
    try:
        cursor = db.kpis_comercial.find(mongo_filter, {'_id': 0})
        
        async for doc in cursor:
            results['mongo_records_found'] += 1
            
            # Mapear documento MongoDB a registro SQL
            kpis = doc.get('kpis', {})
            source = doc.get('source', {})
            
            record = {
                'run_id': source.get('run_id', 'MONGO_MIGRATION'),
                'server_id': doc.get('server_id'),
                'sucursal_id': doc.get('sucursal_id'),
                'sucursal_nombre': doc.get('sucursal_nombre'),
                'empresa_id': doc.get('empresa_id'),
                'unidad_negocio_id': doc.get('unidad_negocio_id'),
                'system_type_normalized': doc.get('system_type', 'UNKNOWN'),
                'fecha': doc.get('fecha'),
                'kpi_tipo': 'DIARIO',
                'ventas_total': kpis.get('ventas', 0),
                'tickets_total': kpis.get('cheques', 0),
                'pax_total': kpis.get('pax', 0),
                'ticket_promedio': kpis.get('ticket_promedio', 0),
                'propinas_total': kpis.get('propinas', 0),
                'source_type': 'MONGO_MIGRATION'
            }
            
            if dry_run:
                results['records'].append({
                    'server_id': record['server_id'],
                    'sucursal_id': record['sucursal_id'],
                    'fecha': record['fecha'],
                    'ventas_total': record['ventas_total'],
                    'action': 'WOULD_UPSERT'
                })
            else:
                result = await upsert_comercial_kpi_historico(record)
                action = result.get('action', 'ERROR')
                
                if action == 'INSERT':
                    results['sql_inserted'] += 1
                elif action == 'UPDATE':
                    results['sql_updated'] += 1
                elif action == 'SKIP':
                    results['sql_skipped'] += 1
                else:
                    results['sql_errors'] += 1
    
    finally:
        client.close()
    
    return results
