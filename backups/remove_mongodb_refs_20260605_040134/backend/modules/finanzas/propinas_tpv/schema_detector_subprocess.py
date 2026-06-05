"""
Detector de esquema para SoftRestaurant usando subprocess.
Versión con encoding fix para ambiente supervisor.

DEFINICIÓN TÉCNICA FINAL (15/04/2026):
========================================
- Fuente de propinas TPV: cheques.propinatarjeta
- Relación: cheques.idturno → turnos.idturno → movtoscaja (Corte Z)
- Llave: (server_id, estacion_id, folio_corte, fecha_corte)

ESTRATEGIA ÚNICA: CHEQUES_PROPINATARJETA
- Compatible con versiones 10, 12, 95 Pro de SoftRestaurant
- Dato EXACTO (no inferido)

DICIEMBRE 2026: Migrado a usar subprocess para evitar problemas de encoding
"""

import logging
from typing import Dict, Any, Optional, List
import asyncio

# Usar el helper de subprocess para evitar problemas de encoding
from modules.finanzas.sql_subprocess_helper import execute_sql_subprocess

logger = logging.getLogger(__name__)


class SoftRestaurantSchemaDetectorSubprocess:
    """
    Detecta y mapea el esquema de SoftRestaurant usando subprocess.
    Versión con fix de encoding para ambiente supervisor.
    
    ESTRATEGIA FINAL:
    - Fuente de propinas TPV: cheques.propinatarjeta
    - Relación: cheques.idturno → turnos.idturno → movtoscaja (Corte Z)
    """
    
    _cache: Dict[str, Dict[str, Any]] = {}
    
    @classmethod
    async def detect_schema(cls, server: Dict[str, Any]) -> Dict[str, Any]:
        """
        Detecta el esquema de un servidor SoftRestaurant usando subprocess.
        
        Verifica existencia de:
        - Tabla cheques con columna propinatarjeta
        - Tabla turnos
        - Tabla movtoscaja
        """
        cache_key = f"{server['host']}:{server['port']}/{server['database']}"
        
        if cache_key in cls._cache:
            logger.debug(f"Usando esquema cacheado para {cache_key}")
            return cls._cache[cache_key]
        
        logger.info(f"[SchemaDetector] Detectando esquema para {server.get('name')} via subprocess...")
        
        try:
            # Query para verificar tablas y columnas necesarias
            query = """
            SELECT TABLE_NAME, COLUMN_NAME
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_NAME IN ('cheques', 'turnos', 'movtoscaja')
            ORDER BY TABLE_NAME, ORDINAL_POSITION
            """
            
            result = await execute_sql_subprocess(
                host=server['host'],
                port=server['port'],
                database=server['database'],
                username=server['username'],
                password=server['password'],
                query=query,
                timeout=30
            )
            
            if not result.get('success'):
                error_msg = result.get('error', 'Unknown error')
                logger.error(f"[SchemaDetector] Error en query: {error_msg}")
                return {
                    'error': error_msg,
                    'compatible': False,
                    'server_name': server.get('name', cache_key),
                    'server_host': server.get('host'),
                    'database': server.get('database'),
                    'compatibility_issues': [f"Error de conexión: {error_msg}"],
                    'estrategia': None
                }
            
            # Organizar columnas por tabla
            tables = {}
            for row in result.get('data', []):
                table = (row.get('TABLE_NAME') or '').lower()
                column = (row.get('COLUMN_NAME') or '').lower()
                if table not in tables:
                    tables[table] = []
                tables[table].append(column)
            
            logger.info(f"[SchemaDetector] Tablas detectadas: {list(tables.keys())}")
            
            # Construir esquema
            schema = cls._build_schema(tables, server)
            
            # Cachear
            cls._cache[cache_key] = schema
            logger.info(f"[SchemaDetector] Esquema para {server.get('name')}: compatible={schema['compatible']}")
            
            return schema
            
        except Exception as e:
            error_schema = {
                'error': str(e),
                'compatible': False,
                'server_name': server.get('name', cache_key),
                'server_host': server.get('host'),
                'database': server.get('database'),
                'compatibility_issues': [f"Error de conexión: {str(e)}"],
                'estrategia': None
            }
            logger.error(f"[SchemaDetector] Error detectando esquema: {e}")
            return error_schema
    
    @classmethod
    def _build_schema(cls, tables: Dict[str, List[str]], server: Dict) -> Dict[str, Any]:
        """
        Construye el esquema basado en las tablas y columnas detectadas.
        """
        problems = []
        
        # Verificar tabla cheques
        has_cheques = 'cheques' in tables
        cheques_columns = tables.get('cheques', [])
        has_propinatarjeta = 'propinatarjeta' in cheques_columns
        has_idturno = 'idturno' in cheques_columns
        has_idestacion = 'idestacion' in cheques_columns or 'estacion' in cheques_columns
        
        if not has_cheques:
            problems.append("CRÍTICO: No se encontró tabla 'cheques'")
        else:
            if not has_propinatarjeta:
                problems.append("CRÍTICO: No se encontró columna 'propinatarjeta' en cheques")
            if not has_idturno:
                problems.append("ADVERTENCIA: No se encontró columna 'idturno' en cheques")
            if not has_idestacion:
                problems.append("ADVERTENCIA: No se encontró columna 'idestacion' en cheques (usando 'estacion')")
        
        # Verificar tabla turnos
        has_turnos = 'turnos' in tables
        if not has_turnos:
            problems.append("CRÍTICO: No se encontró tabla 'turnos'")
        
        # Verificar tabla movtoscaja (para Cortes Z)
        has_movtoscaja = 'movtoscaja' in tables
        if not has_movtoscaja:
            problems.append("CRÍTICO: No se encontró tabla 'movtoscaja'")
        
        # Determinar compatibilidad
        # Mínimo necesario: cheques con propinatarjeta
        compatible = has_cheques and has_propinatarjeta
        
        # Determinar columna de estación
        estacion_column = 'idestacion' if 'idestacion' in cheques_columns else 'estacion'
        
        schema = {
            'servidor': server.get('name', f"{server['host']}:{server['port']}"),
            'host': server.get('host'),
            'database': server.get('database'),
            'compatible': compatible,
            'estrategia': 'CHEQUES_PROPINATARJETA' if compatible else None,
            'tablas_detectadas': list(tables.keys()),
            'tabla_cheques': 'cheques' if has_cheques else None,
            'tabla_turnos': 'turnos' if has_turnos else None,
            'tabla_cortes': 'movtoscaja' if has_movtoscaja else None,
            'columna_propina_tarjeta': 'propinatarjeta' if has_propinatarjeta else None,
            'columna_estacion': estacion_column if has_cheques else None,
            'columna_idturno': 'idturno' if has_idturno else None,
            'problemas': problems
        }
        
        return schema
    
    @classmethod
    def clear_cache(cls):
        """Limpia el caché de esquemas."""
        cls._cache.clear()
        logger.info("[SchemaDetector] Caché de esquemas limpiado")
    
    @classmethod
    async def detect_all_schemas(cls, servers: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """
        Detecta esquemas de múltiples servidores en paralelo.
        """
        results = {}
        
        tasks = []
        for server in servers:
            tasks.append(cls.detect_schema(server))
        
        schemas = await asyncio.gather(*tasks, return_exceptions=True)
        
        for i, schema in enumerate(schemas):
            server = servers[i]
            server_key = server.get('name', f"{server['host']}:{server['port']}")
            
            if isinstance(schema, Exception):
                results[server_key] = {
                    'error': str(schema),
                    'compatible': False,
                    'server_name': server_key
                }
            else:
                results[server_key] = schema
        
        return results
