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
    # NUEVOS: Campos directos de propinas en movtoscaja (alternativa a movtoscajadetalles)
    'propinas_pagadas': ['propinas_pagadas', 'propinaspagadas', 'propinas', 'propina', 'propina_pagada', 'propinas_monto'],
    'total_tarjeta': ['tarjeta', 'total_tarjeta', 'totaltarjeta', 'ventas_tarjeta', 'pagotarjeta', 'monto_tarjeta'],
    'total_efectivo': ['efectivo', 'total_efectivo', 'totalefectivo', 'ventas_efectivo', 'pagoefectivo', 'monto_efectivo'],
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
        
        ESTRATEGIA DE EXTRACCIÓN DE PROPINAS (Prioridad):
        1. Si existe columna 'propinas_pagadas' en movtoscaja → usar directamente (más confiable)
        2. Si existe 'idconcepto' en movtoscajadetalles → usar concepto=9 (tradicional)
        3. Si nada → marcar incompatible
        """
        schema = {
            'mapping': {},
            'estrategia_propinas': None  # 'COLUMNA_DIRECTA' o 'DETALLE_CONCEPTO'
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
            
            # Mapear columnas estándar
            for std_name, alternatives in COLUMN_ALTERNATIVES.items():
                for alt in alternatives:
                    if alt.lower() in cols:
                        schema['mapping'][std_name] = alt
                        schema[f'col_{std_name}'] = alt
                        break
            
            # PRIORIDAD 1: Buscar columna directa de propinas en movtoscaja
            for alt in COLUMN_ALTERNATIVES['propinas_pagadas']:
                if alt.lower() in cols:
                    schema['col_propinas_directa'] = alt
                    schema['estrategia_propinas'] = 'COLUMNA_DIRECTA'
                    logger.info(f"Detectada columna directa de propinas: {alt}")
                    break
            
            # Buscar columnas directas de tarjeta y efectivo
            for alt in COLUMN_ALTERNATIVES['total_tarjeta']:
                if alt.lower() in cols:
                    schema['col_tarjeta_directa'] = alt
                    break
            
            for alt in COLUMN_ALTERNATIVES['total_efectivo']:
                if alt.lower() in cols:
                    schema['col_efectivo_directa'] = alt
                    break
        
        # Detectar columnas en tabla de detalle (PRIORIDAD 2)
        tabla_det = schema.get('tabla_detalle')
        if tabla_det and tabla_det in tables:
            cols = [c.lower() for c in tables[tabla_det]]
            
            # Columna de concepto
            for alt in COLUMN_ALTERNATIVES['concepto_id']:
                if alt.lower() in cols:
                    schema['col_concepto_detalle'] = alt
                    # Solo usar si no hay estrategia directa
                    if not schema.get('estrategia_propinas'):
                        schema['estrategia_propinas'] = 'DETALLE_CONCEPTO'
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
        
        Requisitos mínimos (UNO de los siguientes):
        OPCIÓN A (Preferida): Columna directa de propinas en movtoscaja
        OPCIÓN B (Tradicional): Tabla detalle con concepto + importe
        """
        # Requisito base: tabla de cortes debe existir
        if not schema.get('tabla_cortes'):
            return False
        
        # OPCIÓN A: Columna directa de propinas (más confiable)
        if schema.get('estrategia_propinas') == 'COLUMNA_DIRECTA':
            return True
        
        # OPCIÓN B: Detalle con concepto + importe
        if (schema.get('estrategia_propinas') == 'DETALLE_CONCEPTO' and 
            schema.get('tabla_detalle') and
            schema.get('col_concepto_detalle') and
            schema.get('col_importe_detalle')):
            return True
        
        return False
    
    @classmethod
    def _get_compatibility_issues(cls, schema: Dict[str, Any]) -> List[str]:
        """
        Obtiene lista de problemas de compatibilidad.
        """
        issues = []
        
        if not schema.get('tabla_cortes'):
            issues.append("CRÍTICO: No se encontró tabla de cortes (movtoscaja)")
            return issues  # Sin tabla de cortes no hay nada más que verificar
        
        # Verificar estrategia de propinas
        estrategia = schema.get('estrategia_propinas')
        
        if estrategia == 'COLUMNA_DIRECTA':
            # Estrategia preferida - Sin problemas
            pass
        elif estrategia == 'DETALLE_CONCEPTO':
            # Estrategia tradicional - verificar requisitos
            if not schema.get('tabla_detalle'):
                issues.append("No se encontró tabla de detalle de cortes")
            if not schema.get('col_concepto_detalle'):
                issues.append("No se encontró columna de concepto en detalle")
            if not schema.get('col_importe_detalle'):
                issues.append("No se encontró columna de importe en detalle")
        else:
            # Sin estrategia válida
            issues.append("No se encontró forma de extraer propinas (ni columna directa ni concepto en detalle)")
        
        # Advertencias (no críticas)
        if not schema.get('col_tipo_movimiento'):
            issues.append("ADVERTENCIA: No se encontró columna de tipo de movimiento (filtrado de Corte Z puede fallar)")
        
        if not schema.get('tabla_estaciones'):
            issues.append("ADVERTENCIA: No se encontró tabla de estaciones (no crítico)")
        
        return issues
    
    @classmethod
    def build_propinas_query(cls, schema: Dict[str, Any], fecha_inicio: str, fecha_fin: str) -> str:
        """
        Construye la query de propinas adaptada al esquema detectado.
        
        ESTRATEGIAS:
        1. COLUMNA_DIRECTA: Lee propinas_pagadas directamente de movtoscaja
        2. DETALLE_CONCEPTO: Lee de movtoscajadetalles filtrando por concepto=9
        
        Args:
            schema: Esquema detectado
            fecha_inicio: Fecha inicio YYYY-MM-DD
            fecha_fin: Fecha fin YYYY-MM-DD
            
        Returns:
            Query SQL adaptada
        """
        if not schema.get('compatible'):
            raise ValueError(f"Esquema no compatible: {schema.get('compatibility_issues')}")
        
        estrategia = schema.get('estrategia_propinas', 'DETALLE_CONCEPTO')
        tabla_cortes = schema['tabla_cortes']
        col_folio = schema.get('col_folio', 'folio')
        col_fecha = schema.get('col_fecha', 'fecha')
        col_tipo = schema.get('col_tipo_movimiento')
        col_saldo = schema.get('col_saldo', 'saldo')
        
        # Formatear fechas
        f_ini = fecha_inicio.replace('-', '')
        f_fin = fecha_fin.replace('-', '')
        
        # Construir SELECT base
        select_parts = [
            f"mc.{col_folio} AS folio_corte",
            f"mc.{col_fecha} AS fecha_corte",
        ]
        
        # Estación (opcional)
        col_estacion = schema.get('col_estacion_id')
        if col_estacion:
            select_parts.append(f"ISNULL(CAST(mc.{col_estacion} AS VARCHAR), 'N/A') AS estacion_id")
        else:
            select_parts.append("'N/A' AS estacion_id")
        
        # ===== PROPINAS según estrategia =====
        if estrategia == 'COLUMNA_DIRECTA':
            # ESTRATEGIA 1: Usar columna directa de movtoscaja
            col_propinas = schema['col_propinas_directa']
            select_parts.append(f"ISNULL(mc.{col_propinas}, 0) AS propinas_totales")
            
            # Tarjeta directa si existe
            if schema.get('col_tarjeta_directa'):
                select_parts.append(f"ISNULL(mc.{schema['col_tarjeta_directa']}, 0) AS ventas_tarjeta")
            else:
                select_parts.append("0 AS ventas_tarjeta")
            
            # Efectivo directo si existe
            if schema.get('col_efectivo_directa'):
                select_parts.append(f"ISNULL(mc.{schema['col_efectivo_directa']}, 0) AS ventas_efectivo")
            else:
                select_parts.append("0 AS ventas_efectivo")
                
        else:
            # ESTRATEGIA 2: Usar movtoscajadetalles con concepto
            tabla_detalle = schema['tabla_detalle']
            col_concepto = schema['col_concepto_detalle']
            col_importe = schema.get('col_importe_detalle', 'importe')
            
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
        
        # Agregar campo de estrategia para debugging
        select_parts.append(f"'{estrategia}' AS estrategia_usada")
        
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
        'estrategia_propinas': schema.get('estrategia_propinas'),
        'tablas_detectadas': schema.get('detected_tables', []),
        'tabla_cortes': schema.get('tabla_cortes'),
        'tabla_detalle': schema.get('tabla_detalle'),
        'columna_propinas_directa': schema.get('col_propinas_directa'),
        'columna_concepto_detalle': schema.get('col_concepto_detalle'),
        'problemas': schema.get('compatibility_issues', []),
        'columnas_mapeadas': schema.get('mapping', {}),
    }
