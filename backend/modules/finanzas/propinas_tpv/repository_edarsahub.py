"""
SUBFASE 3.4 — Repositorio EDARSAHUB para Propinas TPV

Este módulo proporciona acceso a propinas TPV desde EDARSAHUB como fuente de verdad.
Reemplaza la lectura de MongoDB para consultas financieras.

Fuente:
- EDARSAHUB.propinas_tpv_control

Filtros obligatorios:
- EsDemo = 0
- Activo = 1

Autor: E1 Agent
Fecha: 1 Mayo 2026
Fase: Finanzas Fase 3 - Propinas TPV
"""

import os
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path

import pymssql

logger = logging.getLogger(__name__)

# ============================================================================
# CARGAR VARIABLES DE ENTORNO
# ============================================================================

def _load_env():
    """Carga variables de entorno desde /app/backend/.env"""
    env_file = Path('/app/backend/.env')
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    value = value.strip('"').strip("'")
                    if key not in os.environ:
                        os.environ[key] = value

_load_env()

# ============================================================================
# CONFIGURACIÓN
# ============================================================================

EDARSAHUB_CONFIG = {
    'server': os.environ.get('EDARSAHUB_HOST', '54.39.104.176'),
    'port': int(os.environ.get('EDARSAHUB_PORT', '1433')),
    'database': os.environ.get('EDARSAHUB_DATABASE', 'EDARSAHUB'),
    'user': os.environ.get('EDARSAHUB_USERNAME', 'HRLectura'),
    'password': os.environ.get('EDARSAHUB_PASSWORD', 'National09$')
}


# ============================================================================
# CLASE REPOSITORIO EDARSAHUB
# ============================================================================

class PropinasTPVRepositoryEdarsahub:
    """
    Repositorio para consultas de Propinas TPV desde EDARSAHUB.
    
    FUENTE DE VERDAD:
    - EDARSAHUB.propinas_tpv_control
    - EDARSAHUB.Finanzas_PropinasTPV_SyncLog
    
    FILTROS OBLIGATORIOS:
    - EsDemo = 0
    - Activo = 1
    """
    
    def __init__(self):
        self.config = EDARSAHUB_CONFIG
    
    def _get_connection(self):
        """Obtiene conexión a EDARSAHUB"""
        return pymssql.connect(
            server=self.config['server'],
            port=self.config['port'],
            database=self.config['database'],
            user=self.config['user'],
            password=self.config['password'],
            login_timeout=30,
            autocommit=False
        )
    
    # ========================================================================
    # CONSULTAS DE PROPINAS
    # ========================================================================
    
    def obtener_propinas(
        self,
        fecha_inicio: Optional[str] = None,
        fecha_fin: Optional[str] = None,
        unidad_negocio_id: Optional[str] = None,
        sistema_origen: Optional[str] = None,
        forma_pago: Optional[str] = None,
        page: int = 1,
        limit: int = 50,
        unidades_permitidas: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Obtiene listado de propinas TPV desde EDARSAHUB.
        
        Args:
            fecha_inicio: Fecha inicio YYYY-MM-DD
            fecha_fin: Fecha fin YYYY-MM-DD
            unidad_negocio_id: Filtrar por UnidadNegocioID
            sistema_origen: Filtrar por SistemaOrigen (SoftRestaurant, MPRO)
            forma_pago: Filtrar por FormaPagoNombre
            page: Página
            limit: Registros por página
            unidades_permitidas: Lista de IDs de unidades permitidas (RBAC)
            
        Returns:
            Dict con propinas, total, paginación y totales
        """
        conn = self._get_connection()
        cursor = conn.cursor(as_dict=True)
        
        try:
            # Construir WHERE con filtros obligatorios
            where_clauses = ["EsDemo = 0", "Activo = 1"]
            params = []
            
            if fecha_inicio:
                where_clauses.append("fecha_corte >= %s")
                params.append(fecha_inicio)
            
            if fecha_fin:
                where_clauses.append("fecha_corte <= %s")
                params.append(fecha_fin + ' 23:59:59')
            
            if unidad_negocio_id and unidad_negocio_id.upper() != 'TODAS':
                where_clauses.append("UnidadNegocioID = %s")
                params.append(unidad_negocio_id)
            
            if sistema_origen:
                where_clauses.append("SistemaOrigen = %s")
                params.append(sistema_origen)
            
            if forma_pago:
                where_clauses.append("FormaPagoNombre = %s")
                params.append(forma_pago)
            
            # RBAC: Filtrar por unidades permitidas
            if unidades_permitidas:
                placeholders = ', '.join(['%s'] * len(unidades_permitidas))
                where_clauses.append(f"UnidadNegocioID IN ({placeholders})")
                params.extend(unidades_permitidas)
            
            where_sql = ' AND '.join(where_clauses)
            
            # Contar total
            count_query = f"""
                SELECT COUNT(*) as total FROM propinas_tpv_control
                WHERE {where_sql}
            """
            cursor.execute(count_query, tuple(params))
            total = cursor.fetchone()['total']
            
            # Obtener registros con paginación
            offset = (page - 1) * limit
            
            data_query = f"""
                SELECT 
                    id, server_id, sucursal_id, folio_corte, fecha_corte,
                    server_name, system_type, sucursal_nombre, empresa_id,
                    estacion_id, propinas_totales_corte, propinas_efectivo,
                    propinas_tpv, ventas_tarjeta, ventas_totales, ventas_efectivo,
                    total_cheques, corte_id_origen, turno_id_origen,
                    tipo_dato, metodo_calculo, confianza, query_origen,
                    fecha_sincronizacion,
                    UnidadNegocioID, UnidadNegocioNombre, SistemaOrigen,
                    BaseDatosOrigen, TablaOrigen, IdOrigen, FolioOrigen,
                    HashOrigen, EsDemo, Activo, FormaPagoID, FormaPagoNombre, EsTarjeta
                FROM propinas_tpv_control
                WHERE {where_sql}
                ORDER BY fecha_corte DESC, id DESC
                OFFSET %s ROWS FETCH NEXT %s ROWS ONLY
            """
            cursor.execute(data_query, tuple(params + [offset, limit]))
            rows = cursor.fetchall()
            
            # Transformar a formato de respuesta
            propinas = []
            for row in rows:
                propinas.append(self._transformar_propina(row))
            
            # Calcular totales del conjunto
            totales_query = f"""
                SELECT 
                    ISNULL(SUM(propinas_tpv), 0) as total_propinas_tpv,
                    ISNULL(SUM(propinas_tpv * 0.02), 0) as total_comision,
                    ISNULL(SUM(propinas_tpv * 0.98), 0) as total_a_pagar,
                    COUNT(*) as total_registros
                FROM propinas_tpv_control
                WHERE {where_sql}
            """
            cursor.execute(totales_query, tuple(params))
            totales_row = cursor.fetchone()
            
            totales = {
                'total_propinas_tpv': float(totales_row['total_propinas_tpv'] or 0),
                'total_comision': float(totales_row['total_comision'] or 0),
                'total_a_pagar': float(totales_row['total_a_pagar'] or 0),
                'total_registros': totales_row['total_registros']
            }
            
            return {
                'propinas': propinas,
                'total': total,
                'page': page,
                'limit': limit,
                'pages': (total + limit - 1) // limit if total > 0 else 0,
                'totales': totales,
                'fuente': 'EDARSAHUB_REAL',
                'filtros_aplicados': {
                    'fecha_inicio': fecha_inicio,
                    'fecha_fin': fecha_fin,
                    'unidad_negocio_id': unidad_negocio_id,
                    'sistema_origen': sistema_origen,
                    'forma_pago': forma_pago,
                    'es_demo': False,
                    'activo': True
                }
            }
            
        finally:
            conn.close()
    
    def obtener_resumen(
        self,
        fecha_inicio: str,
        fecha_fin: str,
        unidad_negocio_id: Optional[str] = None,
        sistema_origen: Optional[str] = None,
        unidades_permitidas: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Obtiene resumen agregado de propinas TPV.
        
        Args:
            fecha_inicio: Fecha inicio YYYY-MM-DD
            fecha_fin: Fecha fin YYYY-MM-DD
            unidad_negocio_id: Filtrar por UnidadNegocioID
            sistema_origen: Filtrar por SistemaOrigen
            unidades_permitidas: Lista de IDs de unidades permitidas (RBAC)
            
        Returns:
            Dict con resumen general y por unidad
        """
        conn = self._get_connection()
        cursor = conn.cursor(as_dict=True)
        
        try:
            # Construir WHERE
            where_clauses = ["EsDemo = 0", "Activo = 1"]
            params = []
            
            where_clauses.append("fecha_corte >= %s")
            params.append(fecha_inicio)
            
            where_clauses.append("fecha_corte <= %s")
            params.append(fecha_fin + ' 23:59:59')
            
            if unidad_negocio_id and unidad_negocio_id.upper() != 'TODAS':
                where_clauses.append("UnidadNegocioID = %s")
                params.append(unidad_negocio_id)
            
            if sistema_origen:
                where_clauses.append("SistemaOrigen = %s")
                params.append(sistema_origen)
            
            # RBAC
            if unidades_permitidas:
                placeholders = ', '.join(['%s'] * len(unidades_permitidas))
                where_clauses.append(f"UnidadNegocioID IN ({placeholders})")
                params.extend(unidades_permitidas)
            
            where_sql = ' AND '.join(where_clauses)
            
            # Resumen general
            general_query = f"""
                SELECT 
                    COUNT(*) as total_registros,
                    ISNULL(SUM(propinas_tpv), 0) as total_propinas_tpv,
                    ISNULL(SUM(propinas_tpv * 0.02), 0) as total_comision,
                    ISNULL(SUM(propinas_tpv * 0.98), 0) as total_neto_a_entregar,
                    COUNT(DISTINCT UnidadNegocioID) as unidades_incluidas,
                    MIN(fecha_corte) as fecha_min,
                    MAX(fecha_corte) as fecha_max
                FROM propinas_tpv_control
                WHERE {where_sql}
            """
            cursor.execute(general_query, tuple(params))
            general = cursor.fetchone()
            
            # Resumen por unidad
            unidades_query = f"""
                SELECT 
                    UnidadNegocioID,
                    UnidadNegocioNombre,
                    SistemaOrigen,
                    COUNT(*) as total_registros,
                    ISNULL(SUM(propinas_tpv), 0) as suma_propinas_tpv,
                    ISNULL(SUM(propinas_tpv * 0.02), 0) as suma_comision,
                    ISNULL(SUM(propinas_tpv * 0.98), 0) as suma_neto_a_entregar,
                    MIN(fecha_corte) as fecha_min,
                    MAX(fecha_corte) as fecha_max
                FROM propinas_tpv_control
                WHERE {where_sql}
                GROUP BY UnidadNegocioID, UnidadNegocioNombre, SistemaOrigen
                ORDER BY UnidadNegocioNombre
            """
            cursor.execute(unidades_query, tuple(params))
            unidades_rows = cursor.fetchall()
            
            unidades = []
            for row in unidades_rows:
                unidades.append({
                    'unidad_negocio_id': str(row['UnidadNegocioID']) if row['UnidadNegocioID'] else None,
                    'unidad_negocio_nombre': row['UnidadNegocioNombre'],
                    'sistema_origen': row['SistemaOrigen'],
                    'total_registros': row['total_registros'],
                    'suma_propinas_tpv': float(row['suma_propinas_tpv'] or 0),
                    'suma_comision': float(row['suma_comision'] or 0),
                    'suma_neto_a_entregar': float(row['suma_neto_a_entregar'] or 0),
                    'fecha_min': str(row['fecha_min']) if row['fecha_min'] else None,
                    'fecha_max': str(row['fecha_max']) if row['fecha_max'] else None
                })
            
            # Status de sincronización
            sync_query = """
                SELECT TOP 1
                    LogID, FechaInicio, UnidadNegocioNombre, SistemaOrigen,
                    RegistrosInsertados, RegistrosOmitidos, Estatus
                FROM Finanzas_PropinasTPV_SyncLog
                ORDER BY LogID DESC
            """
            cursor.execute(sync_query)
            last_sync = cursor.fetchone()
            
            return {
                'periodo': {
                    'fecha_inicio': fecha_inicio,
                    'fecha_fin': fecha_fin
                },
                'resumen_general': {
                    'total_registros': general['total_registros'],
                    'total_propinas_tpv': float(general['total_propinas_tpv'] or 0),
                    'total_comision': float(general['total_comision'] or 0),
                    'total_neto_a_entregar': float(general['total_neto_a_entregar'] or 0),
                    'unidades_incluidas': general['unidades_incluidas'],
                    'fecha_min': str(general['fecha_min']) if general['fecha_min'] else None,
                    'fecha_max': str(general['fecha_max']) if general['fecha_max'] else None
                },
                'por_unidad': unidades,
                'status_sincronizacion': {
                    'ultima_sincronizacion': str(last_sync['FechaInicio']) if last_sync else None,
                    'ultima_unidad': last_sync['UnidadNegocioNombre'] if last_sync else None,
                    'ultimo_sistema': last_sync['SistemaOrigen'] if last_sync else None,
                    'ultimo_estatus': last_sync['Estatus'] if last_sync else None
                } if last_sync else None,
                'fuente': 'EDARSAHUB_REAL',
                'filtros_aplicados': {
                    'fecha_inicio': fecha_inicio,
                    'fecha_fin': fecha_fin,
                    'unidad_negocio_id': unidad_negocio_id,
                    'sistema_origen': sistema_origen,
                    'es_demo': False,
                    'activo': True
                }
            }
            
        finally:
            conn.close()
    
    def obtener_detalle(
        self,
        fecha_inicio: str,
        fecha_fin: str,
        unidad_negocio_id: Optional[str] = None,
        sistema_origen: Optional[str] = None,
        forma_pago: Optional[str] = None,
        page: int = 1,
        limit: int = 100,
        unidades_permitidas: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Obtiene detalle de propinas TPV para listado en frontend.
        
        Returns:
            Dict con detalle de propinas, totales y paginación
        """
        conn = self._get_connection()
        cursor = conn.cursor(as_dict=True)
        
        try:
            # Construir WHERE
            where_clauses = ["EsDemo = 0", "Activo = 1"]
            params = []
            
            where_clauses.append("fecha_corte >= %s")
            params.append(fecha_inicio)
            
            where_clauses.append("fecha_corte <= %s")
            params.append(fecha_fin + ' 23:59:59')
            
            if unidad_negocio_id and unidad_negocio_id.upper() != 'TODAS':
                where_clauses.append("UnidadNegocioID = %s")
                params.append(unidad_negocio_id)
            
            if sistema_origen:
                where_clauses.append("SistemaOrigen = %s")
                params.append(sistema_origen)
            
            if forma_pago:
                where_clauses.append("FormaPagoNombre = %s")
                params.append(forma_pago)
            
            # RBAC
            if unidades_permitidas:
                placeholders = ', '.join(['%s'] * len(unidades_permitidas))
                where_clauses.append(f"UnidadNegocioID IN ({placeholders})")
                params.extend(unidades_permitidas)
            
            where_sql = ' AND '.join(where_clauses)
            
            # Contar total
            count_query = f"""
                SELECT COUNT(*) as total FROM propinas_tpv_control
                WHERE {where_sql}
            """
            cursor.execute(count_query, tuple(params))
            total = cursor.fetchone()['total']
            
            # Obtener detalle
            offset = (page - 1) * limit
            
            detail_query = f"""
                SELECT 
                    id,
                    fecha_corte as FechaOperacion,
                    FolioOrigen,
                    folio_corte as FolioCorte,
                    FormaPagoNombre,
                    propinas_tpv as ImportePropinaTPV,
                    propinas_tpv * 0.02 as PorcentajeComision,
                    propinas_tpv * 0.02 as ImporteComision,
                    propinas_tpv * 0.98 as ImporteNetoAEntregar,
                    SistemaOrigen,
                    UnidadNegocioID,
                    UnidadNegocioNombre,
                    sucursal_nombre,
                    BaseDatosOrigen,
                    TablaOrigen,
                    HashOrigen
                FROM propinas_tpv_control
                WHERE {where_sql}
                ORDER BY fecha_corte DESC, id DESC
                OFFSET %s ROWS FETCH NEXT %s ROWS ONLY
            """
            cursor.execute(detail_query, tuple(params + [offset, limit]))
            rows = cursor.fetchall()
            
            detalle = []
            for row in rows:
                detalle.append({
                    'id': row['id'],
                    'fecha_operacion': str(row['FechaOperacion']) if row['FechaOperacion'] else None,
                    'folio_origen': row['FolioOrigen'],
                    'folio_corte': row['FolioCorte'],
                    'forma_pago_nombre': row['FormaPagoNombre'],
                    'importe_propina_tpv': float(row['ImportePropinaTPV'] or 0),
                    'porcentaje_comision': 0.02,
                    'importe_comision': float(row['ImporteComision'] or 0),
                    'importe_neto_a_entregar': float(row['ImporteNetoAEntregar'] or 0),
                    'sistema_origen': row['SistemaOrigen'],
                    'unidad_negocio_id': str(row['UnidadNegocioID']) if row['UnidadNegocioID'] else None,
                    'unidad_negocio_nombre': row['UnidadNegocioNombre'],
                    'sucursal_nombre': row['sucursal_nombre'],
                    'base_datos_origen': row['BaseDatosOrigen'],
                    'tabla_origen': row['TablaOrigen']
                })
            
            # Totales
            totales_query = f"""
                SELECT 
                    ISNULL(SUM(propinas_tpv), 0) as total_propinas_tpv,
                    ISNULL(SUM(propinas_tpv * 0.02), 0) as total_comision,
                    ISNULL(SUM(propinas_tpv * 0.98), 0) as total_neto_a_entregar
                FROM propinas_tpv_control
                WHERE {where_sql}
            """
            cursor.execute(totales_query, tuple(params))
            totales_row = cursor.fetchone()
            
            return {
                'detalle': detalle,
                'total': total,
                'page': page,
                'limit': limit,
                'pages': (total + limit - 1) // limit if total > 0 else 0,
                'totales': {
                    'total_propinas_tpv': float(totales_row['total_propinas_tpv'] or 0),
                    'total_comision': float(totales_row['total_comision'] or 0),
                    'total_neto_a_entregar': float(totales_row['total_neto_a_entregar'] or 0)
                },
                'fuente': 'EDARSAHUB_REAL'
            }
            
        finally:
            conn.close()
    
    def obtener_propina_por_id(self, propina_id: int) -> Optional[Dict[str, Any]]:
        """
        Obtiene una propina por su ID.
        
        Args:
            propina_id: ID de la propina
            
        Returns:
            Dict con datos de la propina o None
        """
        conn = self._get_connection()
        cursor = conn.cursor(as_dict=True)
        
        try:
            cursor.execute("""
                SELECT 
                    id, server_id, sucursal_id, folio_corte, fecha_corte,
                    server_name, system_type, sucursal_nombre, empresa_id,
                    estacion_id, propinas_totales_corte, propinas_efectivo,
                    propinas_tpv, ventas_tarjeta, ventas_totales, ventas_efectivo,
                    total_cheques, corte_id_origen, turno_id_origen,
                    tipo_dato, metodo_calculo, confianza, query_origen,
                    fecha_sincronizacion,
                    UnidadNegocioID, UnidadNegocioNombre, SistemaOrigen,
                    BaseDatosOrigen, TablaOrigen, IdOrigen, FolioOrigen,
                    HashOrigen, EsDemo, Activo, FormaPagoID, FormaPagoNombre, EsTarjeta
                FROM propinas_tpv_control
                WHERE id = %s AND EsDemo = 0 AND Activo = 1
            """, (propina_id,))
            
            row = cursor.fetchone()
            if row:
                return self._transformar_propina(row)
            return None
            
        finally:
            conn.close()
    
    def obtener_formas_pago(self) -> List[Dict[str, Any]]:
        """
        Obtiene lista de formas de pago disponibles.
        
        Returns:
            Lista de formas de pago únicas
        """
        conn = self._get_connection()
        cursor = conn.cursor(as_dict=True)
        
        try:
            cursor.execute("""
                SELECT DISTINCT 
                    FormaPagoID,
                    FormaPagoNombre,
                    SistemaOrigen,
                    COUNT(*) as registros
                FROM propinas_tpv_control
                WHERE EsDemo = 0 AND Activo = 1
                  AND FormaPagoNombre IS NOT NULL
                GROUP BY FormaPagoID, FormaPagoNombre, SistemaOrigen
                ORDER BY SistemaOrigen, FormaPagoNombre
            """)
            
            return [
                {
                    'forma_pago_id': row['FormaPagoID'],
                    'forma_pago_nombre': row['FormaPagoNombre'],
                    'sistema_origen': row['SistemaOrigen'],
                    'registros': row['registros']
                }
                for row in cursor.fetchall()
            ]
            
        finally:
            conn.close()
    
    def obtener_unidades_disponibles(self) -> List[Dict[str, Any]]:
        """
        Obtiene lista de unidades de negocio con propinas TPV.
        
        Returns:
            Lista de unidades disponibles
        """
        conn = self._get_connection()
        cursor = conn.cursor(as_dict=True)
        
        try:
            cursor.execute("""
                SELECT DISTINCT 
                    UnidadNegocioID,
                    UnidadNegocioNombre,
                    SistemaOrigen,
                    COUNT(*) as total_registros,
                    SUM(propinas_tpv) as total_propinas
                FROM propinas_tpv_control
                WHERE EsDemo = 0 AND Activo = 1
                  AND UnidadNegocioID IS NOT NULL
                GROUP BY UnidadNegocioID, UnidadNegocioNombre, SistemaOrigen
                ORDER BY UnidadNegocioNombre
            """)
            
            return [
                {
                    'unidad_negocio_id': str(row['UnidadNegocioID']),
                    'unidad_negocio_nombre': row['UnidadNegocioNombre'],
                    'sistema_origen': row['SistemaOrigen'],
                    'total_registros': row['total_registros'],
                    'total_propinas': float(row['total_propinas'] or 0)
                }
                for row in cursor.fetchall()
            ]
            
        finally:
            conn.close()
    
    def obtener_status_sincronizacion(self) -> Dict[str, Any]:
        """
        Obtiene status de sincronización desde Finanzas_PropinasTPV_SyncLog.
        
        Returns:
            Dict con status de última sincronización por unidad
        """
        conn = self._get_connection()
        cursor = conn.cursor(as_dict=True)
        
        try:
            # Última sincronización global
            cursor.execute("""
                SELECT TOP 1
                    LogID, FechaInicio, FechaFin, UnidadNegocioNombre, SistemaOrigen,
                    FechaDesde, FechaHasta, RegistrosLeidos, RegistrosInsertados,
                    RegistrosActualizados, RegistrosOmitidos, RegistrosConError,
                    TotalPropinasTPV, Estatus, ErrorMensaje, TipoEjecucion
                FROM Finanzas_PropinasTPV_SyncLog
                ORDER BY LogID DESC
            """)
            ultima_global = cursor.fetchone()
            
            # Última sincronización por unidad
            cursor.execute("""
                WITH UltimosPorUnidad AS (
                    SELECT 
                        UnidadNegocioNombre,
                        SistemaOrigen,
                        MAX(LogID) as UltimoLogID
                    FROM Finanzas_PropinasTPV_SyncLog
                    GROUP BY UnidadNegocioNombre, SistemaOrigen
                )
                SELECT 
                    l.LogID, l.FechaInicio, l.UnidadNegocioNombre, l.SistemaOrigen,
                    l.RegistrosInsertados, l.RegistrosOmitidos, l.Estatus
                FROM Finanzas_PropinasTPV_SyncLog l
                INNER JOIN UltimosPorUnidad u 
                    ON l.LogID = u.UltimoLogID
                ORDER BY l.UnidadNegocioNombre
            """)
            por_unidad = cursor.fetchall()
            
            # Conteo total de registros activos
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_registros,
                    COUNT(DISTINCT UnidadNegocioID) as total_unidades,
                    SUM(propinas_tpv) as total_propinas
                FROM propinas_tpv_control
                WHERE EsDemo = 0 AND Activo = 1
            """)
            totales = cursor.fetchone()
            
            return {
                'ultima_sincronizacion': {
                    'fecha': str(ultima_global['FechaInicio']) if ultima_global else None,
                    'unidad': ultima_global['UnidadNegocioNombre'] if ultima_global else None,
                    'sistema': ultima_global['SistemaOrigen'] if ultima_global else None,
                    'estatus': ultima_global['Estatus'] if ultima_global else None,
                    'insertados': ultima_global['RegistrosInsertados'] if ultima_global else 0,
                    'omitidos': ultima_global['RegistrosOmitidos'] if ultima_global else 0
                } if ultima_global else None,
                'por_unidad': [
                    {
                        'unidad': row['UnidadNegocioNombre'],
                        'sistema': row['SistemaOrigen'],
                        'ultima_sync': str(row['FechaInicio']),
                        'estatus': row['Estatus'],
                        'insertados': row['RegistrosInsertados'],
                        'omitidos': row['RegistrosOmitidos']
                    }
                    for row in por_unidad
                ],
                'totales': {
                    'total_registros': totales['total_registros'],
                    'total_unidades': totales['total_unidades'],
                    'total_propinas': float(totales['total_propinas'] or 0)
                },
                'fuente': 'EDARSAHUB_REAL'
            }
            
        finally:
            conn.close()
    
    # ========================================================================
    # HELPERS
    # ========================================================================
    
    def _transformar_propina(self, row: Dict[str, Any]) -> Dict[str, Any]:
        """Transforma una fila de BD a formato de respuesta API"""
        porcentaje_comision = 0.02
        propinas_tpv = float(row['propinas_tpv'] or 0)
        comision = propinas_tpv * porcentaje_comision
        neto = propinas_tpv - comision
        
        return {
            'id': row['id'],
            'server_id': row['server_id'],
            'sucursal_id': row['sucursal_id'],
            'folio_corte': row['folio_corte'],
            'fecha_corte': str(row['fecha_corte']) if row['fecha_corte'] else None,
            'server_name': row['server_name'],
            'system_type': row['system_type'],
            'sucursal_nombre': row['sucursal_nombre'],
            'empresa_id': row['empresa_id'],
            'estacion_id': row['estacion_id'],
            
            # Origen
            'origen': {
                'tipo_dato': row['tipo_dato'],
                'metodo_calculo': row['metodo_calculo'],
                'confianza': float(row['confianza'] or 1.0),
                'propinas_totales_corte': float(row['propinas_totales_corte'] or 0),
                'ventas_tarjeta': float(row['ventas_tarjeta'] or 0),
                'ventas_totales': float(row['ventas_totales'] or 0),
                'ventas_efectivo': float(row['ventas_efectivo'] or 0),
                'propinas_tpv': propinas_tpv,
                'propinas_efectivo': float(row['propinas_efectivo'] or 0),
                'total_cheques': row['total_cheques'],
                'query_origen': row['query_origen'],
                'fecha_sincronizacion': str(row['fecha_sincronizacion']) if row['fecha_sincronizacion'] else None
            },
            
            # Cálculo
            'calculo': {
                'porcentaje_comision': porcentaje_comision,
                'comision_calculada': round(comision, 2),
                'monto_a_pagar_meseros': round(neto, 2)
            },
            
            # EDARSAHUB específicos
            'unidad_negocio_id': str(row['UnidadNegocioID']) if row['UnidadNegocioID'] else None,
            'unidad_negocio_nombre': row['UnidadNegocioNombre'],
            'sistema_origen': row['SistemaOrigen'],
            'base_datos_origen': row['BaseDatosOrigen'],
            'tabla_origen': row['TablaOrigen'],
            'id_origen': row['IdOrigen'],
            'folio_origen': row['FolioOrigen'],
            'hash_origen': row['HashOrigen'],
            'forma_pago_id': row['FormaPagoID'],
            'forma_pago_nombre': row['FormaPagoNombre'],
            'es_tarjeta': bool(row['EsTarjeta']),
            'es_demo': bool(row['EsDemo']),
            'activo': bool(row['Activo']),
            
            # Metadata
            'fuente': 'EDARSAHUB_REAL'
        }


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = ['PropinasTPVRepositoryEdarsahub']
