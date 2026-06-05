"""
EDARSA HUB - Repositorio de Ingresos desde EDARSAHUB
=====================================================

SUBFASE 2.4 — Control de Ingresos

Este repositorio lee cortes de caja sincronizados desde EDARSAHUB.
NO depende de conexiones en vivo a SoftRestaurant/MPRO.
NO usa datos demo.
SIEMPRE filtra EsDemo=0 para datos reales.

MÁXIMAS RESPETADAS:
- EDARSAHUB es el cerebro del sistema
- No dependemos de conexiones en vivo para dashboards
- No usamos datos demo en operación real
- Respetamos RBAC y filtros por unidad

Fecha: 2026-05-01
Autor: E1 Agent
"""

import logging
import os
import pymssql
from datetime import datetime, date
from typing import Dict, List, Optional, Any
from core.config.edarsahub_config import get_edarsahub_sql_config
_edarsa_cfg = get_edarsahub_sql_config()


logger = logging.getLogger(__name__)

# ============================================================================
# CONFIGURACIÓN EDARSAHUB
# ============================================================================

EDARSAHUB_CONFIG = {
    'server': _edarsa_cfg.host,
    'port': _edarsa_cfg.port,
    'database': _edarsa_cfg.database,
    'user': _edarsa_cfg.user,
    'password': _edarsa_cfg.password
}


def get_edarsahub_connection():
    """Obtiene conexión a EDARSAHUB"""
    return pymssql.connect(
        server=EDARSAHUB_CONFIG['server'],
        port=EDARSAHUB_CONFIG['port'],
        database=EDARSAHUB_CONFIG['database'],
        user=EDARSAHUB_CONFIG['user'],
        password=EDARSAHUB_CONFIG['password'],
        login_timeout=30,
        autocommit=False
    )


# ============================================================================
# MAPPING DE UNIDADES DE NEGOCIO
# ============================================================================

async def get_unidades_activas() -> List[Dict]:
    """
    Obtiene lista de unidades de negocio activas desde EDARSAHUB.
    Usado para RBAC y filtros.
    """
    conn = get_edarsahub_connection()
    cursor = conn.cursor(as_dict=True)
    
    try:
        cursor.execute("""
            SELECT 
                id as unidad_negocio_id,
                nombre,
                codigo,
                activo
            FROM Unidades_Negocio
            WHERE activo = 1
            ORDER BY nombre
        """)
        
        unidades = cursor.fetchall()
        return [
            {
                'unidad_negocio_id': str(u['unidad_negocio_id']),
                'nombre': u['nombre'],
                'codigo': u['codigo']
            }
            for u in unidades
        ]
    finally:
        conn.close()


async def get_unidad_por_nombre(nombre: str) -> Optional[Dict]:
    """Obtiene una unidad por nombre"""
    conn = get_edarsahub_connection()
    cursor = conn.cursor(as_dict=True)
    
    try:
        cursor.execute("""
            SELECT 
                id as unidad_negocio_id,
                nombre,
                codigo
            FROM Unidades_Negocio
            WHERE nombre = %s AND activo = 1
        """, (nombre,))
        
        row = cursor.fetchone()
        if row:
            return {
                'unidad_negocio_id': str(row['unidad_negocio_id']),
                'nombre': row['nombre'],
                'codigo': row['codigo']
            }
        return None
    finally:
        conn.close()


# ============================================================================
# REPOSITORIO PRINCIPAL DE INGRESOS
# ============================================================================

class RepositorioIngresosEDARSAHUB:
    """
    Repositorio para leer cortes de caja desde EDARSAHUB.
    
    Fuente: Finanzas_CortesCaja (datos sincronizados de SoftRestaurant y MPRO)
    Filtro obligatorio: EsDemo = 0
    """
    
    def __init__(self):
        self.config = EDARSAHUB_CONFIG
    
    def _get_connection(self):
        """Obtiene conexión a EDARSAHUB"""
        return get_edarsahub_connection()
    
    async def get_cortes_caja(
        self,
        unidad_negocio_id: Optional[str] = None,
        fecha_inicio: Optional[str] = None,
        fecha_fin: Optional[str] = None,
        sistema_origen: Optional[str] = None,
        solo_pendientes_deposito: bool = False,
        unidades_permitidas: Optional[List[str]] = None,
        limit: int = 500
    ) -> List[Dict]:
        """
        Obtiene cortes de caja desde EDARSAHUB.
        
        Args:
            unidad_negocio_id: UUID de la unidad (opcional, None = todas permitidas)
            fecha_inicio: Fecha inicio YYYY-MM-DD
            fecha_fin: Fecha fin YYYY-MM-DD
            sistema_origen: 'SoftRestaurant', 'MPRO', None = todos
            solo_pendientes_deposito: Solo cortes no depositados
            unidades_permitidas: Lista de UUIDs permitidos por RBAC
            limit: Máximo de registros
            
        Returns:
            Lista de cortes transformados para el frontend
        """
        conn = self._get_connection()
        cursor = conn.cursor(as_dict=True)
        
        try:
            # Construir query con filtros dinámicos
            where_clauses = ["EsDemo = 0", "Activo = 1"]
            params = []
            
            # Filtro por unidad específica
            if unidad_negocio_id:
                where_clauses.append("UnidadNegocioID = %s")
                params.append(unidad_negocio_id)
            
            # Filtro RBAC: solo unidades permitidas
            if unidades_permitidas:
                placeholders = ','.join(['%s'] * len(unidades_permitidas))
                where_clauses.append(f"UnidadNegocioID IN ({placeholders})")
                params.extend(unidades_permitidas)
            
            # Filtro por fechas
            if fecha_inicio:
                where_clauses.append("FechaCorte >= %s")
                params.append(fecha_inicio)
            
            if fecha_fin:
                where_clauses.append("FechaCorte <= %s")
                params.append(fecha_fin)
            
            # Filtro por sistema origen
            if sistema_origen:
                where_clauses.append("SistemaOrigen = %s")
                params.append(sistema_origen)
            
            # Filtro de pendientes de depósito
            if solo_pendientes_deposito:
                where_clauses.append("(DepositadoEfectivo = 0 OR DepositadoDebito = 0 OR DepositadoCredito = 0)")
            
            where_sql = " AND ".join(where_clauses)
            
            query = f"""
                SELECT TOP {limit}
                    CorteCajaID,
                    SucursalID,
                    FechaCorte,
                    TurnoID,
                    TotalEfectivo,
                    TotalTarjetaDebito,
                    TotalTarjetaCredito,
                    TotalAmex,
                    TotalInternacional,
                    TotalVales,
                    TotalOtros,
                    ComisionDebito,
                    ComisionCredito,
                    ComisionAmex,
                    ComisionInternacional,
                    FechaDepositoEfectivo,
                    FechaDepositoDebito,
                    FechaDepositoCredito,
                    FechaDepositoAmex,
                    FechaDepositoInternacional,
                    DepositadoEfectivo,
                    DepositadoDebito,
                    DepositadoCredito,
                    DepositadoAmex,
                    DepositadoInternacional,
                    EstatusCierreID,
                    Observaciones,
                    UnidadNegocioID,
                    UnidadNegocioNombre,
                    SistemaOrigen,
                    FolioCorte,
                    FechaApertura,
                    FechaCierre,
                    CajeroNombre,
                    CajaNombre,
                    Propinas,
                    Retiros,
                    FondoInicial,
                    TotalVenta,
                    HashOrigen,
                    FechaSincronizacion
                FROM Finanzas_CortesCaja
                WHERE {where_sql}
                ORDER BY FechaCorte DESC, CorteCajaID DESC
            """
            
            cursor.execute(query, tuple(params))
            rows = cursor.fetchall()
            
            logger.info(f"[INGRESOS_EDARSAHUB] Query ejecutada: {len(rows)} registros encontrados")
            
            # Transformar a formato del frontend
            cortes = []
            for row in rows:
                corte = self._transform_corte(row)
                cortes.append(corte)
            
            return cortes
            
        except Exception as e:
            logger.error(f"[INGRESOS_EDARSAHUB] Error en get_cortes_caja: {e}")
            raise
        finally:
            conn.close()
    
    def _transform_corte(self, row: Dict) -> Dict:
        """
        Transforma un registro de Finanzas_CortesCaja al formato del frontend.
        Mantiene el contrato de respuesta existente.
        """
        # Extraer valores con defaults
        efectivo = float(row.get('TotalEfectivo') or 0)
        debito = float(row.get('TotalTarjetaDebito') or 0)
        credito = float(row.get('TotalTarjetaCredito') or 0)
        amex = float(row.get('TotalAmex') or 0)
        internacional = float(row.get('TotalInternacional') or 0)
        vales = float(row.get('TotalVales') or 0)
        otros = float(row.get('TotalOtros') or 0)
        
        com_debito = float(row.get('ComisionDebito') or 0)
        com_credito = float(row.get('ComisionCredito') or 0)
        com_amex = float(row.get('ComisionAmex') or 0)
        com_internacional = float(row.get('ComisionInternacional') or 0)
        
        # Calcular netos
        debito_neto = debito - com_debito
        credito_neto = credito - com_credito
        amex_neto = amex - com_amex
        internacional_neto = internacional - com_internacional
        
        # Total venta
        total_venta = efectivo + debito + credito + amex + internacional + vales + otros
        
        # Total comisiones
        total_comisiones = com_debito + com_credito + com_amex + com_internacional
        
        # Formatear fechas
        def format_date(d):
            if d is None:
                return None
            if isinstance(d, (datetime, date)):
                return d.strftime("%Y-%m-%d")
            return str(d)[:10] if d else None
        
        # Determinar día de la semana
        fecha_corte = row.get('FechaCorte')
        dia_semana = ""
        if fecha_corte:
            if isinstance(fecha_corte, (datetime, date)):
                dias = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
                dia_semana = dias[fecha_corte.weekday()]
        
        return {
            # Identificadores
            "corte_id": row.get('CorteCajaID'),
            "sucursal_id": row.get('SucursalID'),
            "sucursal_nombre": row.get('UnidadNegocioNombre') or f"Unidad {row.get('UnidadNegocioID', '')[:8]}",
            "unidad_negocio_id": str(row.get('UnidadNegocioID') or ''),
            "unidad_nombre": row.get('UnidadNegocioNombre'),
            
            # Fechas
            "fecha_corte": format_date(fecha_corte),
            "dia_semana": dia_semana,
            "fecha_apertura": format_date(row.get('FechaApertura')),
            "fecha_cierre": format_date(row.get('FechaCierre')),
            "turno_id": row.get('TurnoID'),
            "folio_corte": row.get('FolioCorte'),
            
            # Efectivo
            "efectivo": round(efectivo, 2),
            "fecha_deposito_efectivo": format_date(row.get('FechaDepositoEfectivo')),
            "efectivo_depositado": bool(row.get('DepositadoEfectivo')),
            "efectivo_referencia_deposito": None,  # A implementar si se requiere
            
            # Tarjetas - Débito
            "debito": round(debito, 2),
            "debito_comision": round(com_debito, 2),
            "debito_neto": round(debito_neto, 2),
            "fecha_deposito_debito": format_date(row.get('FechaDepositoDebito')),
            
            # Tarjetas - Crédito
            "credito": round(credito, 2),
            "credito_comision": round(com_credito, 2),
            "credito_neto": round(credito_neto, 2),
            "fecha_deposito_credito": format_date(row.get('FechaDepositoCredito')),
            
            # Tarjetas - AMEX
            "amex": round(amex, 2),
            "amex_comision": round(com_amex, 2),
            "amex_neto": round(amex_neto, 2),
            "fecha_deposito_amex": format_date(row.get('FechaDepositoAmex')),
            
            # Tarjetas - Internacional
            "internacional": round(internacional, 2),
            "internacional_comision": round(com_internacional, 2),
            "internacional_neto": round(internacional_neto, 2),
            "fecha_deposito_internacional": format_date(row.get('FechaDepositoInternacional')),
            
            # Estado de depósitos
            "tarjetas_depositadas": (
                bool(row.get('DepositadoDebito')) and 
                bool(row.get('DepositadoCredito')) and
                bool(row.get('DepositadoAmex', True)) and  # Default True si no aplica
                bool(row.get('DepositadoInternacional', True))
            ),
            "tarjetas_referencia_netpay": None,  # A implementar si se requiere
            
            # Otros
            "vales": round(vales, 2),
            "otros": round(otros, 2),
            "propinas": round(float(row.get('Propinas') or 0), 2),
            "retiros": round(float(row.get('Retiros') or 0), 2),
            "fondo_inicial": round(float(row.get('FondoInicial') or 0), 2),
            
            # Totales
            "total_venta": round(total_venta, 2),
            "total_comisiones": round(total_comisiones, 2),
            "total_neto_tarjetas": round(debito_neto + credito_neto + amex_neto + internacional_neto, 2),
            
            # Conciliación
            "estatus_cierre_id": row.get('EstatusCierreID'),
            "estatus_nombre": self._get_estatus_nombre(row.get('EstatusCierreID')),
            "conciliado": row.get('EstatusCierreID') == 3,
            "observaciones": row.get('Observaciones'),
            
            # Metadata
            "cajero_nombre": row.get('CajeroNombre'),
            "caja_nombre": row.get('CajaNombre'),
            "sistema_origen": row.get('SistemaOrigen'),
            "hash_origen": row.get('HashOrigen'),
            "fecha_sincronizacion": format_date(row.get('FechaSincronizacion')),
            "fuente": "EDARSAHUB_REAL"
        }
    
    def _get_estatus_nombre(self, estatus_id: int) -> str:
        """Obtiene nombre del estatus de cierre"""
        estatus_map = {
            1: "Pendiente",
            2: "Parcial",
            3: "Conciliado",
            4: "Con Diferencia",
            5: "Cancelado"
        }
        return estatus_map.get(estatus_id, "Pendiente")
    
    async def get_resumen_por_unidad(
        self,
        fecha_inicio: Optional[str] = None,
        fecha_fin: Optional[str] = None,
        unidades_permitidas: Optional[List[str]] = None
    ) -> List[Dict]:
        """
        Obtiene resumen de ingresos agrupado por unidad de negocio.
        """
        conn = self._get_connection()
        cursor = conn.cursor(as_dict=True)
        
        try:
            where_clauses = ["EsDemo = 0", "Activo = 1"]
            params = []
            
            if fecha_inicio:
                where_clauses.append("FechaCorte >= %s")
                params.append(fecha_inicio)
            
            if fecha_fin:
                where_clauses.append("FechaCorte <= %s")
                params.append(fecha_fin)
            
            if unidades_permitidas:
                placeholders = ','.join(['%s'] * len(unidades_permitidas))
                where_clauses.append(f"UnidadNegocioID IN ({placeholders})")
                params.extend(unidades_permitidas)
            
            where_sql = " AND ".join(where_clauses)
            
            query = f"""
                SELECT 
                    UnidadNegocioID,
                    UnidadNegocioNombre,
                    SistemaOrigen,
                    COUNT(*) as total_cortes,
                    SUM(TotalEfectivo) as total_efectivo,
                    SUM(TotalTarjetaDebito) as total_debito,
                    SUM(TotalTarjetaCredito) as total_credito,
                    SUM(TotalAmex) as total_amex,
                    SUM(TotalInternacional) as total_internacional,
                    SUM(TotalVales) as total_vales,
                    SUM(TotalOtros) as total_otros,
                    SUM(ComisionDebito + ComisionCredito + ComisionAmex + ComisionInternacional) as total_comisiones,
                    MIN(FechaCorte) as fecha_min,
                    MAX(FechaCorte) as fecha_max
                FROM Finanzas_CortesCaja
                WHERE {where_sql}
                GROUP BY UnidadNegocioID, UnidadNegocioNombre, SistemaOrigen
                ORDER BY UnidadNegocioNombre
            """
            
            cursor.execute(query, tuple(params))
            rows = cursor.fetchall()
            
            resumen = []
            for row in rows:
                total_tarjetas = (
                    float(row['total_debito'] or 0) +
                    float(row['total_credito'] or 0) +
                    float(row['total_amex'] or 0) +
                    float(row['total_internacional'] or 0)
                )
                
                total_ingresos = (
                    float(row['total_efectivo'] or 0) +
                    total_tarjetas +
                    float(row['total_vales'] or 0) +
                    float(row['total_otros'] or 0)
                )
                
                resumen.append({
                    'unidad_negocio_id': str(row['UnidadNegocioID']),
                    'unidad_nombre': row['UnidadNegocioNombre'],
                    'sistema_origen': row['SistemaOrigen'],
                    'total_cortes': row['total_cortes'],
                    'total_efectivo': round(float(row['total_efectivo'] or 0), 2),
                    'total_tarjetas': round(total_tarjetas, 2),
                    'total_comisiones': round(float(row['total_comisiones'] or 0), 2),
                    'total_vales': round(float(row['total_vales'] or 0), 2),
                    'total_otros': round(float(row['total_otros'] or 0), 2),
                    'total_ingresos': round(total_ingresos, 2),
                    'fecha_min': str(row['fecha_min'])[:10] if row['fecha_min'] else None,
                    'fecha_max': str(row['fecha_max'])[:10] if row['fecha_max'] else None,
                    'fuente': 'EDARSAHUB_REAL'
                })
            
            return resumen
            
        finally:
            conn.close()
    
    async def get_totales_por_rango(
        self,
        fecha_inicio: Optional[str] = None,
        fecha_fin: Optional[str] = None,
        unidad_negocio_id: Optional[str] = None,
        unidades_permitidas: Optional[List[str]] = None
    ) -> Dict:
        """
        Obtiene totales consolidados para un rango de fechas.
        """
        conn = self._get_connection()
        cursor = conn.cursor(as_dict=True)
        
        try:
            where_clauses = ["EsDemo = 0", "Activo = 1"]
            params = []
            
            if unidad_negocio_id:
                where_clauses.append("UnidadNegocioID = %s")
                params.append(unidad_negocio_id)
            
            if unidades_permitidas:
                placeholders = ','.join(['%s'] * len(unidades_permitidas))
                where_clauses.append(f"UnidadNegocioID IN ({placeholders})")
                params.extend(unidades_permitidas)
            
            if fecha_inicio:
                where_clauses.append("FechaCorte >= %s")
                params.append(fecha_inicio)
            
            if fecha_fin:
                where_clauses.append("FechaCorte <= %s")
                params.append(fecha_fin)
            
            where_sql = " AND ".join(where_clauses)
            
            query = f"""
                SELECT 
                    COUNT(*) as total_registros,
                    SUM(TotalEfectivo) as total_efectivo,
                    SUM(TotalTarjetaDebito) as total_debito,
                    SUM(TotalTarjetaCredito) as total_credito,
                    SUM(TotalAmex) as total_amex,
                    SUM(TotalInternacional) as total_internacional,
                    SUM(TotalVales) as total_vales,
                    SUM(TotalOtros) as total_otros,
                    SUM(ComisionDebito) as comision_debito,
                    SUM(ComisionCredito) as comision_credito,
                    SUM(ComisionAmex) as comision_amex,
                    SUM(ComisionInternacional) as comision_internacional,
                    MIN(FechaCorte) as fecha_min,
                    MAX(FechaCorte) as fecha_max
                FROM Finanzas_CortesCaja
                WHERE {where_sql}
            """
            
            cursor.execute(query, tuple(params))
            row = cursor.fetchone()
            
            if not row or row['total_registros'] == 0:
                return {
                    'total_registros': 0,
                    'total_efectivo': 0,
                    'total_tarjetas_bruto': 0,
                    'total_comisiones': 0,
                    'total_neto_tarjetas': 0,
                    'total_ventas': 0,
                    'fecha_min': None,
                    'fecha_max': None,
                    'fuente': 'EDARSAHUB_REAL'
                }
            
            total_tarjetas = (
                float(row['total_debito'] or 0) +
                float(row['total_credito'] or 0) +
                float(row['total_amex'] or 0) +
                float(row['total_internacional'] or 0)
            )
            
            total_comisiones = (
                float(row['comision_debito'] or 0) +
                float(row['comision_credito'] or 0) +
                float(row['comision_amex'] or 0) +
                float(row['comision_internacional'] or 0)
            )
            
            total_efectivo = float(row['total_efectivo'] or 0)
            total_vales = float(row['total_vales'] or 0)
            total_otros = float(row['total_otros'] or 0)
            
            return {
                'total_registros': row['total_registros'],
                'total_efectivo': round(total_efectivo, 2),
                'total_tarjetas_bruto': round(total_tarjetas, 2),
                'total_comisiones': round(total_comisiones, 2),
                'total_neto_tarjetas': round(total_tarjetas - total_comisiones, 2),
                'total_vales': round(total_vales, 2),
                'total_otros': round(total_otros, 2),
                'total_ventas': round(total_efectivo + total_tarjetas + total_vales + total_otros, 2),
                'fecha_min': str(row['fecha_min'])[:10] if row['fecha_min'] else None,
                'fecha_max': str(row['fecha_max'])[:10] if row['fecha_max'] else None,
                'fuente': 'EDARSAHUB_REAL'
            }
            
        finally:
            conn.close()


# ============================================================================
# INSTANCIA GLOBAL
# ============================================================================

_repositorio_ingresos = None

def get_repositorio_ingresos() -> RepositorioIngresosEDARSAHUB:
    """Obtiene instancia del repositorio de ingresos"""
    global _repositorio_ingresos
    if _repositorio_ingresos is None:
        _repositorio_ingresos = RepositorioIngresosEDARSAHUB()
    return _repositorio_ingresos


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    'RepositorioIngresosEDARSAHUB',
    'get_repositorio_ingresos',
    'get_unidades_activas',
    'get_unidad_por_nombre'
]
