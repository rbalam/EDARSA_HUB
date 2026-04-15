"""
Detector de esquema para SoftRestaurant.
Permite adaptar queries a diferentes versiones del sistema.

FASE 1B - Estabilización de lectura SQL
"""

import logging
from typing import Dict, Any, Optional, List

from core.db import execute_sql_query

logger = logging.getLogger(__name__)

# Mapeo de posibles nombres de columnas por versión de SoftRestaurant
COLUMN_ALTERNATIVES = {
    'tipo_movimiento': ['idtipomovtocaja', 'idtipomovto', 'tipo_movimiento', 'tipo'],
    'estacion_id': ['idestacion', 'estacion_id', 'estacionid', 'id_estacion'],
    'concepto_id': ['idconcepto', 'concepto_id', 'conceptoid', 'id_concepto', 'concepto', 'idtipo', 'tipo_concepto'],
    'movimiento_id': ['idmovtocaja', 'movimiento_id', 'id_movtocaja', 'idmovimiento'],
    'importe': ['importe', 'monto', 'cantidad', 'valor', 'total'],
    'saldo': ['saldo', 'saldo_final', 'total', 'totalsaldo'],
    'folio': ['folio', 'numero', 'num_folio', 'numfolio'],
    'fecha': ['fecha', 'fecha_corte', 'fechacorte', 'fechahora'],
}

TABLE_ALTERNATIVES = {
    'detalle': ['movtoscajadetalles', 'movtoscajadetalle', 'movtocajadetalles', 'movtocajadetalle'],
    'estaciones': ['estaciones', 'estacion', 'cat_estaciones'],
    'cortes': ['movtoscaja', 'movtocaja', 'cortescaja'],
}


class SoftRestaurantSchemaDetector:
    """
    Detecta el esquema de tablas de SoftRestaurant para un servidor específico.
    Cachea los resultados para evitar queries repetidas.
    """
    
    _cache: Dict[str, Dict[str, Any]] = {}
    
    @classmethod
    def detect_schema(cls, server: Dict[str, Any]) -> Dict[str, Any]:
        """
        Detecta el esquema de un servidor SoftRestaurant.
        
        Args:
            server: Diccionario con datos de conexión
            
        Returns:
            Dict con columnas y tablas detectadas, más flag de compatibilidad
        """
        cache_key = f"{server['host']}:{server['port']}/{server['database']}"
        
        if cache_key in cls._cache:
            logger.info(f"Usando esquema cacheado para {cache_key}")
            return cls._cache[cache_key]
        
        logger.info(f"Detectando esquema para {cache_key}...")
        
        try:
            # Query de introspección más amplia - buscar TODAS las tablas que contengan "movto" o "caja"
            query = """
            SELECT 
                TABLE_NAME,
                COLUMN_NAME
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_NAME LIKE '%movto%'
               OR TABLE_NAME LIKE '%caja%'
               OR TABLE_NAME LIKE '%estacion%'
            ORDER BY TABLE_NAME, COLUMN_NAME
            """
            
            result = execute_sql_query(
                server['host'],
                server['port'],
                server['database'],
                server['username'],
                server['password'],
                query
            )
            
            # Organizar columnas por tabla
            tables = {}
            for row in result or []:
                table = row.get('TABLE_NAME', '').lower()
                column = row.get('COLUMN_NAME', '').lower()
                if table not in tables:
                    tables[table] = []
                tables[table].append(column)
            
            # Detectar columnas reales
            schema = cls._map_schema(tables)
            schema['server_name'] = server.get('name', cache_key)
            schema['server_host'] = server.get('host')
            schema['database'] = server.get('database')
            schema['detected_tables'] = list(tables.keys())
            schema['raw_columns'] = tables
            
            # Determinar compatibilidad
            schema['compatible'] = cls._check_compatibility(schema)
            schema['compatibility_issues'] = cls._get_compatibility_issues(schema)
            
            cls._cache[cache_key] = schema
            logger.info(f"Esquema detectado para {server.get('name')}: compatible={schema['compatible']}")
            
            return schema
            
        except Exception as e:
            error_schema = {
                'error': str(e),
                'compatible': False,
                'server_name': server.get('name', cache_key),
                'server_host': server.get('host'),
                'database': server.get('database'),
                'compatibility_issues': [f"Error de conexión: {str(e)}"]
            }
            logger.error(f"Error detectando esquema: {e}")
            return error_schema
    
    @classmethod
    def _map_schema(cls, tables: Dict[str, List[str]]) -> Dict[str, Any]:
        """
        Mapea las columnas encontradas a los nombres estándar.
        """
        schema = {
            'mapping': {}
        }
        
        # Detectar tabla principal de cortes
        for alt in TABLE_ALTERNATIVES['cortes']:
            if alt in tables:
                schema['tabla_cortes'] = alt
                break
        
        # Detectar tabla de detalle
        for alt in TABLE_ALTERNATIVES['detalle']:
            if alt in tables:
                schema['tabla_detalle'] = alt
                break
        
        # Detectar tabla de estaciones (opcional)
        for alt in TABLE_ALTERNATIVES['estaciones']:
            if alt in tables:
                schema['tabla_estaciones'] = alt
                break
        
        # Detectar columnas en tabla de cortes
        tabla_cortes = schema.get('tabla_cortes')
        if tabla_cortes and tabla_cortes in tables:
            cols = [c.lower() for c in tables[tabla_cortes]]
            
            for std_name, alternatives in COLUMN_ALTERNATIVES.items():
                for alt in alternatives:
                    if alt.lower() in cols:
                        schema['mapping'][std_name] = alt
                        schema[f'col_{std_name}'] = alt
                        break
        
        # Detectar columnas en tabla de detalle
        tabla_det = schema.get('tabla_detalle')
        if tabla_det and tabla_det in tables:
            cols = [c.lower() for c in tables[tabla_det]]
            
            # Columna de concepto
            for alt in COLUMN_ALTERNATIVES['concepto_id']:
                if alt.lower() in cols:
                    schema['col_concepto_detalle'] = alt
                    break
            
            # Columna de importe
            for alt in COLUMN_ALTERNATIVES['importe']:
                if alt.lower() in cols:
                    schema['col_importe_detalle'] = alt
                    break
        
        return schema
    
    @classmethod
    def _check_compatibility(cls, schema: Dict[str, Any]) -> bool:
        """
        Verifica si el esquema es compatible para leer propinas.
        
        Requisitos mínimos:
        1. Tabla de cortes existe
        2. Tabla de detalle existe
        3. Columna de concepto en detalle existe
        4. Columna de importe en detalle existe
        """
        required = [
            'tabla_cortes',
            'tabla_detalle',
            'col_concepto_detalle',
            'col_importe_detalle',
        ]
        
        for req in required:
            if not schema.get(req):
                return False
        
        return True
    
    @classmethod
    def _get_compatibility_issues(cls, schema: Dict[str, Any]) -> List[str]:
        """
        Obtiene lista de problemas de compatibilidad.
        """
        issues = []
        
        if not schema.get('tabla_cortes'):
            issues.append("No se encontró tabla de cortes (movtoscaja)")
        
        if not schema.get('tabla_detalle'):
            issues.append("No se encontró tabla de detalle de cortes")
        
        if not schema.get('col_concepto_detalle'):
            issues.append("No se encontró columna de concepto en detalle")
        
        if not schema.get('col_importe_detalle'):
            issues.append("No se encontró columna de importe en detalle")
        
        if not schema.get('col_tipo_movimiento'):
            issues.append("ADVERTENCIA: No se encontró columna de tipo de movimiento (puede afectar filtrado)")
        
        if not schema.get('tabla_estaciones'):
            issues.append("ADVERTENCIA: No se encontró tabla de estaciones (no crítico)")
        
        return issues
    
    @classmethod
    def build_propinas_query(cls, schema: Dict[str, Any], fecha_inicio: str, fecha_fin: str) -> str:
        """
        Construye la query de propinas adaptada al esquema detectado.
        
        Args:
            schema: Esquema detectado
            fecha_inicio: Fecha inicio YYYY-MM-DD
            fecha_fin: Fecha fin YYYY-MM-DD
            
        Returns:
            Query SQL adaptada
        """
        if not schema.get('compatible'):
            raise ValueError(f"Esquema no compatible: {schema.get('compatibility_issues')}")
        
        # Obtener nombres de tablas/columnas del esquema
        tabla_cortes = schema['tabla_cortes']
        tabla_detalle = schema['tabla_detalle']
        col_concepto = schema['col_concepto_detalle']
        col_importe = schema.get('col_importe_detalle', 'importe')
        col_tipo = schema.get('col_tipo_movimiento')
        col_estacion = schema.get('col_estacion_id')
        col_saldo = schema.get('col_saldo', 'saldo')
        col_folio = schema.get('col_folio', 'folio')
        col_fecha = schema.get('col_fecha', 'fecha')
        
        # Formatear fechas
        f_ini = fecha_inicio.replace('-', '')
        f_fin = fecha_fin.replace('-', '')
        
        # Construir SELECT
        select_parts = [
            f"mc.{col_folio} AS folio_corte",
            f"mc.{col_fecha} AS fecha_corte",
        ]
        
        # Estación (opcional)
        if col_estacion:
            select_parts.append(f"ISNULL(CAST(mc.{col_estacion} AS VARCHAR), 'N/A') AS estacion_id")
        else:
            select_parts.append("'N/A' AS estacion_id")
        
        # Propinas (concepto 9)
        select_parts.append(f"""
            ISNULL((
                SELECT SUM(d.{col_importe}) 
                FROM {tabla_detalle} d 
                WHERE d.idmovtocaja = mc.idmovtocaja 
                  AND d.{col_concepto} = 9
            ), 0) AS propinas_totales
        """)
        
        # Tarjeta (conceptos 10, 11, 12)
        select_parts.append(f"""
            ISNULL((
                SELECT SUM(d.{col_importe}) 
                FROM {tabla_detalle} d 
                WHERE d.idmovtocaja = mc.idmovtocaja 
                  AND d.{col_concepto} IN (10, 11, 12)
            ), 0) AS ventas_tarjeta
        """)
        
        # Efectivo (concepto 2)
        select_parts.append(f"""
            ISNULL((
                SELECT SUM(d.{col_importe}) 
                FROM {tabla_detalle} d 
                WHERE d.idmovtocaja = mc.idmovtocaja 
                  AND d.{col_concepto} = 2
            ), 0) AS ventas_efectivo
        """)
        
        # Saldo/Total
        select_parts.append(f"ISNULL(mc.{col_saldo}, 0) AS ventas_totales")
        
        # Construir WHERE
        where_parts = []
        
        # Filtro de tipo (Corte Z = 3) - solo si existe la columna
        if col_tipo:
            where_parts.append(f"mc.{col_tipo} = 3")
        
        # Filtro de fechas
        where_parts.append(f"mc.{col_fecha} >= '{f_ini} 00:00:00'")
        where_parts.append(f"mc.{col_fecha} <= '{f_fin} 23:59:59'")
        
        # Construir query final
        query = f"""
        SELECT 
            {', '.join(select_parts)}
        FROM {tabla_cortes} mc
        WHERE {' AND '.join(where_parts)}
        ORDER BY mc.{col_fecha} DESC
        """
        
        return query
    
    @classmethod
    def clear_cache(cls, server_key: Optional[str] = None):
        """
        Limpia el caché de esquemas.
        
        Args:
            server_key: Opcional, limpiar solo un servidor específico
        """
        if server_key:
            cls._cache.pop(server_key, None)
        else:
            cls._cache.clear()
        logger.info(f"Caché de esquemas limpiado: {server_key or 'todos'}")


def get_schema_summary(schema: Dict[str, Any]) -> Dict[str, Any]:
    """
    Genera un resumen legible del esquema detectado.
    """
    return {
        'servidor': schema.get('server_name'),
        'host': schema.get('server_host'),
        'database': schema.get('database'),
        'compatible': schema.get('compatible', False),
        'tablas_detectadas': schema.get('detected_tables', []),
        'tabla_cortes': schema.get('tabla_cortes'),
        'tabla_detalle': schema.get('tabla_detalle'),
        'problemas': schema.get('compatibility_issues', []),
        'columnas_mapeadas': schema.get('mapping', {}),
    }
