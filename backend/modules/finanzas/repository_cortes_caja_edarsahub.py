from core.unidades_service import UnidadesService
from core.corporate_filters.service import CorporateFilterService
"""
Repository EDARSAHUB SQL para Cortes de Caja (Cortes Z)

FINANZAS-TESORERIA-SQL-001: Migrado de consultas en vivo a EDARSAHUB SQL
- Fecha: 2026-05-25
- Lee de tabla Finanzas_CortesCaja (ya sincronizada)
- NO consulta servidores origen en vivo
- Cumple máxima: "EDARSAHUB SQL es el cerebro"
"""
import logging
from typing import List, Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class CortesCajaRepositoryError(RuntimeError):
    """Falla de infraestructura o consulta en el repositorio de Cortes Z."""


def get_edarsahub_connection():
    """Obtiene conexión a EDARSAHUB SQL Server."""
    from core.unidades_registry import _get_edarsahub_connection
    return _get_edarsahub_connection()


class RepositoryCortesCajaEdarsahub:
    """
    Repository para consultar Cortes de Caja desde EDARSAHUB SQL.
    
    ARQUITECTURA SQL-FIRST:
    - Toda consulta lee de Finanzas_CortesCaja (tabla sincronizada)
    - NO hay consultas en vivo a servidores origen
    - Los datos llegan vía jobs de sincronización
    """
    
    def __init__(self):
        self.tabla_principal = 'Finanzas_CortesCaja'
        self.tabla_estatus = 'Finanzas_EstatusCierre'
        self.logger = logging.getLogger(__name__)
    
    def listar_cortes_caja(
        self,
        filtros: Dict = None
    ) -> List[Dict]:
        """
        Lista Cortes de Caja desde EDARSAHUB SQL.
        
        Args:
            filtros: Dict con:
                - unidad_negocio_pk: UUID de la unidad
                - server_id: UUID del servidor (alias de unidad_negocio_pk)
                - fecha_inicio: YYYY-MM-DD
                - fecha_fin: YYYY-MM-DD
                - limit: int
                - offset: int
                
        Returns:
            Lista de cortes formateados para el frontend
        """
        filtros = filtros or {}
        
        try:
            conn = get_edarsahub_connection()
            if not conn:
                raise CortesCajaRepositoryError(
                    "No se pudo obtener conexión a EDARSAHUB"
                )
        except CortesCajaRepositoryError:
            raise
        except Exception as conn_error:
            self.logger.error(
                f"[CORTES_CAJA_SQL] Error de conexión a EDARSAHUB: {conn_error}"
            )
            raise CortesCajaRepositoryError(
                "Error de conexión a EDARSAHUB"
            ) from conn_error
        
        try:
            cursor = conn.cursor(as_dict=True)
            
            where_clauses = ['cc.Activo = 1']
            params = []
            
            # Filtro por unidad de negocio (server_id o unidad_negocio_pk)
            server_id = filtros.get('server_id') or filtros.get('unidad_negocio_pk')
            if server_id:
                # Buscar por ServerID o UnidadNegocioID
                where_clauses.append('(cc.ServerID = %s OR cc.UnidadNegocioID = %s)')
                params.extend([server_id, server_id])
            
            # Filtro por nombre de unidad (para compatibilidad)
            if filtros.get('unidad_negocio_nombre'):
                where_clauses.append('cc.UnidadNegocioNombre LIKE %s')
                params.append(f"%{filtros['unidad_negocio_nombre']}%")
            
            # Filtro por fechas
            if filtros.get('fecha_inicio'):
                where_clauses.append('cc.FechaCorte >= %s')
                params.append(filtros['fecha_inicio'])
            if filtros.get('fecha_fin'):
                where_clauses.append('cc.FechaCorte <= %s')
                params.append(filtros['fecha_fin'])
            
            where_sql = ' AND '.join(where_clauses)
            
            limit = filtros.get('limit', 100)
            offset = filtros.get('offset', 0)
            
            sql = f'''
                SELECT 
                    cc.CorteCajaID,
                    cc.FolioCorte,
                    cc.FechaCorte,
                    cc.FechaApertura,
                    cc.FechaCierre,
                    cc.UnidadNegocioID,
                    cc.UnidadNegocioNombre,
                    cc.ServerID,
                    cc.EmpresaID,
                    cc.SistemaOrigen,
                    cc.CajaID,
                    cc.CajaNombre,
                    cc.CajeroID,
                    cc.CajeroNombre,
                    cc.TurnoID,
                    cc.TotalEfectivo,
                    cc.TotalTarjetaDebito,
                    cc.TotalTarjetaCredito,
                    cc.TotalAmex,
                    cc.TotalInternacional,
                    cc.TotalVales,
                    cc.TotalOtros,
                    cc.Propinas,
                    cc.Retiros,
                    cc.FondoInicial,
                    cc.TotalVenta,
                    cc.EstatusCierreID,
                    ec.Descripcion as EstatusNombre,
                    NULL as EstatusColor,
                    cc.Observaciones,
                    cc.FechaSincronizacion
                FROM {self.tabla_principal} cc
                LEFT JOIN {self.tabla_estatus} ec ON cc.EstatusCierreID = ec.EstatusCierreID
                WHERE {where_sql}
                ORDER BY cc.FechaCorte DESC, cc.CorteCajaID DESC
                OFFSET {offset} ROWS FETCH NEXT {limit} ROWS ONLY
            '''
            
            cursor.execute(sql, tuple(params))
            rows = cursor.fetchall()
            
            return [self._formatear_corte(row) for row in rows]
        except CortesCajaRepositoryError:
            raise
        except Exception as e:
            self.logger.error(f"[CORTES_CAJA_SQL] Error listando cortes: {e}")
            raise CortesCajaRepositoryError(
                "Error consultando Finanzas_CortesCaja"
            ) from e
        finally:
            try:
                conn.close()
            except Exception:
                pass
    
    def listar_cortes_por_server_id(
        self,
        server_id: str,
        fecha_inicio: Optional[str] = None,
        fecha_fin: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict]:
        """
        Lista Cortes de Caja para un server_id específico.
        
        COMPATIBILIDAD: Este método mantiene la firma del repositorio anterior
        que consultaba en vivo.
        """
        filtros = {
            'server_id': server_id,
            'limit': limit
        }
        if fecha_inicio:
            filtros['fecha_inicio'] = fecha_inicio
        if fecha_fin:
            filtros['fecha_fin'] = fecha_fin
        
        return self.listar_cortes_caja(filtros)
    
    def obtener_cortes_todos_servidores(
        self,
        fecha_inicio: Optional[str] = None,
        fecha_fin: Optional[str] = None,
        limit: int = 200
    ) -> Dict:
        """
        Obtiene cortes de TODOS los servidores (sin filtro de unidad).
        
        COMPATIBILIDAD: Reemplaza get_all_cortes_z_with_status que consultaba en vivo.
        
        ARQUITECTURA SQL-FIRST + RESILIENCIA:
        - Si EDARSAHUB SQL no responde, retorna estado EDARSAHUB_UNREACHABLE
        - NUNCA retorna $0 falso por falla de conexión
        - Incluye source_status: FRESH, STALE, o EDARSAHUB_UNREACHABLE
        
        Returns:
            Dict con:
                - cortes: Lista de cortes
                - estado_general: SUCCESS_WITH_DATA, SUCCESS_EMPTY, o EDARSAHUB_UNREACHABLE
                - source_status: FRESH, STALE, o ERROR
                - fuentes_detalle: Info de la fuente (EDARSAHUB SQL)
        """
        import time
        start_time = time.time()
        
        filtros = {'limit': limit}
        if fecha_inicio:
            filtros['fecha_inicio'] = fecha_inicio
        if fecha_fin:
            filtros['fecha_fin'] = fecha_fin
        
        try:
            cortes = self.listar_cortes_caja(filtros)
            duration_ms = int((time.time() - start_time) * 1000)
            
            if cortes:
                estado = 'SUCCESS_WITH_DATA'
                source_status = 'FRESH'
            else:
                estado = 'SUCCESS_EMPTY'
                source_status = 'FRESH'
            
            return {
                'cortes': cortes,
                'estado_general': estado,
                'data_source': 'EDARSAHUB_SQL',
                'source_status': source_status,
                'fuentes_detalle': [{
                    'status': estado,
                    'query_executed': True,
                    'row_count': len(cortes),
                    'source_type': 'EDARSAHUB_SQL',
                    'source_id': 'Finanzas_CortesCaja',
                    'source_status': source_status,
                    'error_message': '',
                    'timestamp': datetime.utcnow().isoformat(),
                    'duration_ms': duration_ms,
                    'is_retriable': False,
                    'metadata': {
                        'tabla': 'Finanzas_CortesCaja',
                        'arquitectura': 'SQL-FIRST (sin consultas en vivo)'
                    }
                }]
            }
        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            error_msg = str(e)
            self.logger.error(f"[CORTES_CAJA_SQL] Error conexión EDARSAHUB: {error_msg}")
            
            # RESILIENCIA: No lanzar excepción, retornar estado controlado
            # NUNCA retornar $0 falso ni lista vacía silenciosa
            return {
                'cortes': [],
                'estado_general': 'EDARSAHUB_UNREACHABLE',
                'data_source': 'EDARSAHUB_SQL',
                'source_status': 'ERROR',
                'fuentes_detalle': [{
                    'status': 'EDARSAHUB_UNREACHABLE',
                    'query_executed': False,
                    'row_count': 0,
                    'source_type': 'EDARSAHUB_SQL',
                    'source_id': 'Finanzas_CortesCaja',
                    'source_status': 'ERROR',
                    'error_message': f'EDARSAHUB SQL no disponible: {error_msg[:200]}',
                    'timestamp': datetime.utcnow().isoformat(),
                    'duration_ms': duration_ms,
                    'is_retriable': True,
                    'metadata': {
                        'tabla': 'Finanzas_CortesCaja',
                        'arquitectura': 'SQL-FIRST (sin consultas en vivo)',
                        'advertencia': 'Servidor EDARSAHUB no respondió. Datos no disponibles temporalmente.'
                    }
                }],
                'advertencia': 'EDARSAHUB SQL no está respondiendo. Los datos de Cortes Z no están disponibles temporalmente. Esta NO es una falla del sistema, es una situación de infraestructura externa.'
            }
    
    def contar_cortes(self, filtros: Dict = None) -> int:
        """Cuenta cortes con filtros."""
        filtros = filtros or {}
        
        conn = get_edarsahub_connection()
        try:
            cursor = conn.cursor()
            
            where_clauses = ['Activo = 1']
            params = []
            
            server_id = filtros.get('server_id') or filtros.get('unidad_negocio_pk')
            if server_id:
                where_clauses.append('(ServerID = %s OR UnidadNegocioID = %s)')
                params.extend([server_id, server_id])
            
            if filtros.get('fecha_inicio'):
                where_clauses.append('FechaCorte >= %s')
                params.append(filtros['fecha_inicio'])
            if filtros.get('fecha_fin'):
                where_clauses.append('FechaCorte <= %s')
                params.append(filtros['fecha_fin'])
            
            where_sql = ' AND '.join(where_clauses)
            
            cursor.execute(f'SELECT COUNT(*) FROM {self.tabla_principal} WHERE {where_sql}', tuple(params))
            return cursor.fetchone()[0]
        except Exception as e:
            self.logger.error(f"[CORTES_CAJA_SQL] Error contando cortes: {e}")
            raise CortesCajaRepositoryError(
                "Error contando registros de Finanzas_CortesCaja"
            ) from e
        finally:
            conn.close()
    
    def _formatear_corte(self, row: Dict) -> Dict:
        """
        Formatea un registro de corte para el frontend.
        Mantiene compatibilidad con el formato anterior.
        """
        # Calcular totales
        total_efectivo = float(row.get('TotalEfectivo', 0) or 0)
        total_tarjeta = (
            float(row.get('TotalTarjetaDebito', 0) or 0) +
            float(row.get('TotalTarjetaCredito', 0) or 0) +
            float(row.get('TotalAmex', 0) or 0) +
            float(row.get('TotalInternacional', 0) or 0)
        )
        total_otros = (
            float(row.get('TotalVales', 0) or 0) +
            float(row.get('TotalOtros', 0) or 0)
        )
        propinas = float(row.get('Propinas', 0) or 0)
        retiros = float(row.get('Retiros', 0) or 0)
        fondo_inicial = float(row.get('FondoInicial', 0) or 0)
        total_venta = float(row.get('TotalVenta', 0) or 0)
        
        # Monto a depositar = efectivo - retiros
        monto_depositar = total_efectivo - retiros
        
        # Formatear fecha
        fecha_corte = row.get('FechaCorte')
        if hasattr(fecha_corte, 'isoformat'):
            fecha_corte = fecha_corte.isoformat()
        elif fecha_corte:
            fecha_corte = str(fecha_corte)
        
        return {
            # IDs
            'corte_id': row.get('CorteCajaID'),
            'folio_corte': row.get('FolioCorte') or str(row.get('CorteCajaID')),
            
            # Fecha y hora
            'fecha_corte': fecha_corte,
            'fecha_apertura': str(row.get('FechaApertura')) if row.get('FechaApertura') else None,
            'fecha_cierre': str(row.get('FechaCierre')) if row.get('FechaCierre') else None,
            
            # Sucursal/Unidad
            'sucursal_id': row.get('UnidadNegocioID') or row.get('ServerID'),
            'sucursal_nombre': row.get('UnidadNegocioNombre') or 'Sin nombre',
            'server_id': row.get('ServerID') or row.get('UnidadNegocioID'),
            'empresa_id': row.get('EmpresaID'),
            
            # Sistema origen
            'fuente': row.get('SistemaOrigen') or 'EDARSAHUB',
            'sistema_origen': row.get('SistemaOrigen'),
            
            # Caja y cajero
            'caja_id': row.get('CajaID'),
            'caja_nombre': row.get('CajaNombre'),
            'cajero_id': row.get('CajeroID'),
            'cajero_nombre': row.get('CajeroNombre'),
            'turno_id': row.get('TurnoID'),
            
            # Montos
            'efectivo_inicial': fondo_inicial,
            'efectivo_ventas': total_efectivo,
            'total_efectivo': total_efectivo,
            'tarjeta': total_tarjeta,
            'tarjeta_debito': float(row.get('TotalTarjetaDebito', 0) or 0),
            'tarjeta_credito': float(row.get('TotalTarjetaCredito', 0) or 0),
            'vales': float(row.get('TotalVales', 0) or 0),
            'otros': total_otros,
            'propinas': propinas,
            'retiros': retiros,
            'total_venta': total_venta or (total_efectivo + total_tarjeta + total_otros),
            'monto_a_depositar': monto_depositar,
            
            # Estatus
            'estatus_cierre_id': row.get('EstatusCierreID'),
            'estatus_nombre': row.get('EstatusNombre'),
            'estatus_color': row.get('EstatusColor'),
            
            # Metadata
            'observaciones': row.get('Observaciones'),
            'fecha_sincronizacion': str(row.get('FechaSincronizacion')) if row.get('FechaSincronizacion') else None,
            
            # Campos para compatibilidad con UI de cuadre
            'tiene_cuadre': False,  # Se actualiza en el endpoint
            'cuadre_id': None,
            'estado_cuadre': None,
            'fecha_deposito_esperada': None  # Se calcula en el endpoint
        }


# ============================================================================
# SINGLETON PATTERN
# ============================================================================

_repo_instance = None

def get_cortes_caja_repository_sql() -> RepositoryCortesCajaEdarsahub:
    """
    Obtiene instancia singleton del repositorio SQL de Cortes de Caja.
    
    FINANZAS-TESORERIA-SQL-001: Factory method para tesoreria.py
    """
    global _repo_instance
    if _repo_instance is None:
        _repo_instance = RepositoryCortesCajaEdarsahub()
    return _repo_instance


# ============================================================================
# FUNCIÓN AUXILIAR
# ============================================================================

def calcular_fecha_deposito_esperada(fecha_corte: str) -> str:
    """
    Calcula la fecha esperada de depósito (siguiente día hábil).
    
    Args:
        fecha_corte: Fecha del corte en formato YYYY-MM-DD
        
    Returns:
        Fecha esperada de depósito en formato YYYY-MM-DD
    """
    from datetime import datetime, timedelta
    
    try:
        if isinstance(fecha_corte, str):
            fecha = datetime.strptime(fecha_corte[:10], '%Y-%m-%d')
        else:
            fecha = fecha_corte
        
        # Siguiente día
        siguiente = fecha + timedelta(days=1)
        
        # Si cae en fin de semana, mover al lunes
        while siguiente.weekday() >= 5:  # 5=sábado, 6=domingo
            siguiente += timedelta(days=1)
        
        return siguiente.strftime('%Y-%m-%d')
    except Exception:
        return None


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    'CortesCajaRepositoryError',
    'RepositoryCortesCajaEdarsahub',
    'get_cortes_caja_repository_sql',
    'get_edarsahub_connection',
    'calcular_fecha_deposito_esperada'
]
