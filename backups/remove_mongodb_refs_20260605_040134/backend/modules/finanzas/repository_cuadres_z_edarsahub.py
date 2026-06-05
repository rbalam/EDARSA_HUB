"""
Repository EDARSAHUB para Cuadres Z

Fase 4 - Tesorería - Subfase 4.3
EDARSAHUB como fuente de verdad financiera para Cuadres Z.

Tablas utilizadas:
- Finanzas_CuadresZ (principal)
- Finanzas_Cat_EstatusCuadreZ (catálogo)
- Finanzas_Cat_EstatusTesoreria (catálogo)
- Finanzas_CuadresZ_SyncLog (bitácora)

Autor: E1 Agent
Fecha: 1 Mayo 2026
"""

import os
import hashlib
import logging
from datetime import datetime, date
from typing import Dict, List, Any, Optional
from decimal import Decimal
import pymssql
from core.config.edarsahub_config import get_edarsahub_sql_config
_edarsa_cfg = get_edarsahub_sql_config()


logger = logging.getLogger(__name__)


def get_edarsahub_connection():
    """Obtiene conexión a EDARSAHUB."""
    config = {
        'server': _edarsa_cfg.host,
        'port': int(os.environ.get('EDARSAHUB_PORT', '1433')),
        'database': _edarsa_cfg.database,
        'user': _edarsa_cfg.user,
        'password': _edarsa_cfg.password
    }
    return pymssql.connect(**config, login_timeout=30)


def calcular_hash_origen(data: Dict) -> str:
    """
    Calcula HashOrigen único para un cuadre Z.
    
    Componentes:
    - SistemaOrigen
    - ServerID
    - FolioCorte
    - FechaCorte
    - CajaID
    - TurnoID
    """
    componentes = [
        str(data.get('sistema_origen', '')),
        str(data.get('server_id', '')),
        str(data.get('folio_corte', '')),
        str(data.get('fecha_corte', '')),
        str(data.get('caja_id', '')),
        str(data.get('turno_id', ''))
    ]
    cadena = '|'.join(componentes)
    return hashlib.sha256(cadena.encode()).hexdigest()


def validar_hash_origen(data: Dict) -> bool:
    """Valida si el HashOrigen calculado coincide con el proporcionado."""
    hash_calculado = calcular_hash_origen(data)
    hash_proporcionado = data.get('hash_origen', '')
    return hash_calculado == hash_proporcionado


class RepositoryCuadresZEdarsahub:
    """
    Repositorio para operaciones CRUD de Cuadres Z en EDARSAHUB.
    
    NO usa MongoDB como fuente financiera.
    EDARSAHUB es la única fuente de verdad.
    """
    
    def __init__(self):
        self.tabla_principal = 'Finanzas_CuadresZ'
        self.tabla_estatus_cuadre = 'Finanzas_Cat_EstatusCuadreZ'
        self.tabla_estatus_tesoreria = 'Finanzas_Cat_EstatusTesoreria'
        self.tabla_synclog = 'Finanzas_CuadresZ_SyncLog'
    
    # =========================================================================
    # CATÁLOGOS
    # =========================================================================
    
    def obtener_estatus_cuadre_z(self) -> List[Dict]:
        """Obtiene catálogo de estatus de cuadre."""
        conn = get_edarsahub_connection()
        try:
            cursor = conn.cursor(as_dict=True)
            cursor.execute(f'''
                SELECT 
                    EstatusCuadreID,
                    Codigo,
                    Descripcion,
                    ColorHex,
                    Orden
                FROM {self.tabla_estatus_cuadre}
                WHERE Activo = 1
                ORDER BY Orden
            ''')
            return cursor.fetchall()
        finally:
            conn.close()
    
    def obtener_estatus_tesoreria(self) -> List[Dict]:
        """Obtiene catálogo de estatus de tesorería."""
        conn = get_edarsahub_connection()
        try:
            cursor = conn.cursor(as_dict=True)
            cursor.execute(f'''
                SELECT 
                    EstatusTesoreriaID,
                    Codigo,
                    Descripcion,
                    ColorHex,
                    Orden
                FROM {self.tabla_estatus_tesoreria}
                WHERE Activo = 1
                ORDER BY Orden
            ''')
            return cursor.fetchall()
        finally:
            conn.close()
    
    def _mapear_estatus_cuadre(self, codigo: str) -> int:
        """Mapea código de estatus a ID."""
        mapeo = {
            'PENDIENTE': 1,
            'EN_PROCESO': 2,
            'CUADRADO': 3,
            'DESCUADRE': 4,
            'VALIDADO': 5,
            'RECHAZADO': 6
        }
        return mapeo.get(codigo.upper(), 1)
    
    def _mapear_estatus_tesoreria(self, codigo: str) -> int:
        """Mapea código de estatus tesorería a ID."""
        mapeo = {
            'PENDIENTE': 1,
            'DEPOSITADO': 2,
            'CONCILIADO': 3,
            'DISCREPANCIA': 4
        }
        return mapeo.get(codigo.upper(), 1)
    
    # =========================================================================
    # OPERACIONES CRUD
    # =========================================================================
    
    def crear_cuadre_z(self, data: Dict, usuario_id: str = None, usuario_nombre: str = None) -> Dict:
        """
        Crea un nuevo registro de Cuadre Z en EDARSAHUB.
        
        Args:
            data: Datos del cuadre
            usuario_id: ID del usuario que crea
            usuario_nombre: Nombre del usuario
            
        Returns:
            Dict con resultado de la operación
        """
        # Calcular HashOrigen
        hash_origen = calcular_hash_origen(data)
        
        conn = get_edarsahub_connection()
        try:
            cursor = conn.cursor(as_dict=True)
            
            # Verificar si ya existe (idempotencia)
            cursor.execute(f'''
                SELECT CuadreZID FROM {self.tabla_principal}
                WHERE HashOrigen = %s
            ''', (hash_origen,))
            existente = cursor.fetchone()
            
            if existente:
                logger.info(f"[CUADRES_Z_EDARSAHUB] Cuadre ya existe: {existente['CuadreZID']}")
                return {
                    'success': False,
                    'mensaje': 'Cuadre ya existe',
                    'cuadre_z_id': existente['CuadreZID'],
                    'accion': 'omitido'
                }
            
            # Mapear estatus
            estatus_cuadre_id = self._mapear_estatus_cuadre(data.get('estatus_cuadre', 'PENDIENTE'))
            estatus_tesoreria_id = self._mapear_estatus_tesoreria(data.get('estatus_tesoreria', 'PENDIENTE'))
            
            # Insertar
            sql = f'''
                INSERT INTO {self.tabla_principal} (
                    UnidadNegocioID, UnidadNegocioNombre, EmpresaID,
                    ServerID, SistemaOrigen, BaseDatosOrigen,
                    FechaOperacion, FechaCorte, FechaApertura, FechaCierre,
                    FolioCorte, FolioZ, CajaID, CajaNombre,
                    CajeroID, CajeroNombre, TurnoID,
                    TotalVenta, TotalEfectivo,
                    TotalTarjetaDebito, TotalTarjetaCredito, TotalAmex, TotalTarjetaTotal,
                    TotalTransferencia, TotalVales, TotalOtros,
                    TotalPropinasTPV, TotalPropinasEfectivo, TotalRetiros, FondoInicial,
                    TotalDepositar, TotalDeclarado, Diferencia,
                    ConteoEfectivo_Billetes1000, ConteoEfectivo_Billetes500,
                    ConteoEfectivo_Billetes200, ConteoEfectivo_Billetes100,
                    ConteoEfectivo_Billetes50, ConteoEfectivo_Billetes20,
                    ConteoEfectivo_Monedas20, ConteoEfectivo_Monedas10,
                    ConteoEfectivo_Monedas5, ConteoEfectivo_Monedas2,
                    ConteoEfectivo_Monedas1, ConteoEfectivo_Monedas050,
                    ConteoEfectivo_Total,
                    FichaDepositoURL, FichaDepositoFecha, FichaDepositoMonto,
                    FichaDepositoValidada, FichaDepositoBancoID, FichaDepositoCuentaID,
                    EstatusCuadreID, EstatusTesoreriaID, Observaciones,
                    UsuarioCapturaID, UsuarioCapturaNombre, FechaCaptura,
                    CorteCajaID,
                    FuenteOriginal, IdOrigen, HashOrigen,
                    EsDemo, Activo, FechaAlta
                )
                OUTPUT INSERTED.CuadreZID
                VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s
                )
            '''
            
            # Conteo de efectivo
            conteo = data.get('conteo_efectivo', {})
            billetes = conteo.get('billetes', {})
            monedas = conteo.get('monedas', {})
            
            total_conteo = (
                billetes.get('b1000', 0) * 1000 +
                billetes.get('b500', 0) * 500 +
                billetes.get('b200', 0) * 200 +
                billetes.get('b100', 0) * 100 +
                billetes.get('b50', 0) * 50 +
                billetes.get('b20', 0) * 20 +
                monedas.get('m20', 0) * 20 +
                monedas.get('m10', 0) * 10 +
                monedas.get('m5', 0) * 5 +
                monedas.get('m2', 0) * 2 +
                monedas.get('m1', 0) * 1 +
                monedas.get('m050', 0) * 0.50
            )
            
            # Ficha de depósito
            ficha = data.get('ficha_deposito', {})
            
            now = datetime.now()
            
            params = (
                data.get('unidad_negocio_id'),
                data.get('unidad_negocio_nombre'),
                data.get('empresa_id'),
                data.get('server_id'),
                data.get('sistema_origen'),
                data.get('base_datos_origen'),
                data.get('fecha_operacion'),
                data.get('fecha_corte'),
                data.get('fecha_apertura'),
                data.get('fecha_cierre'),
                data.get('folio_corte'),
                data.get('folio_z'),
                data.get('caja_id'),
                data.get('caja_nombre'),
                data.get('cajero_id'),
                data.get('cajero_nombre'),
                data.get('turno_id'),
                data.get('total_venta', 0),
                data.get('total_efectivo', 0),
                data.get('total_tarjeta_debito', 0),
                data.get('total_tarjeta_credito', 0),
                data.get('total_amex', 0),
                data.get('total_tarjeta_total', 0),
                data.get('total_transferencia', 0),
                data.get('total_vales', 0),
                data.get('total_otros', 0),
                data.get('total_propinas_tpv', 0),
                data.get('total_propinas_efectivo', 0),
                data.get('total_retiros', 0),
                data.get('fondo_inicial', 0),
                data.get('total_depositar', 0),
                data.get('total_declarado', 0),
                data.get('diferencia', 0),
                billetes.get('b1000', 0),
                billetes.get('b500', 0),
                billetes.get('b200', 0),
                billetes.get('b100', 0),
                billetes.get('b50', 0),
                billetes.get('b20', 0),
                monedas.get('m20', 0),
                monedas.get('m10', 0),
                monedas.get('m5', 0),
                monedas.get('m2', 0),
                monedas.get('m1', 0),
                monedas.get('m050', 0),
                total_conteo,
                ficha.get('url'),
                ficha.get('fecha'),
                ficha.get('monto'),
                ficha.get('validada', False),
                ficha.get('banco_id'),
                ficha.get('cuenta_id'),
                estatus_cuadre_id,
                estatus_tesoreria_id,
                data.get('observaciones'),
                usuario_id,
                usuario_nombre,
                now,
                data.get('corte_caja_id'),
                data.get('fuente_original', 'EDARSAHUB'),
                data.get('id_origen'),
                hash_origen,
                data.get('es_demo', 0),
                1,  # Activo
                now
            )
            
            cursor.execute(sql, params)
            result = cursor.fetchone()
            conn.commit()
            
            cuadre_z_id = result['CuadreZID'] if result else None
            
            logger.info(f"[CUADRES_Z_EDARSAHUB] Cuadre creado: {cuadre_z_id}")
            
            return {
                'success': True,
                'mensaje': 'Cuadre creado exitosamente',
                'cuadre_z_id': cuadre_z_id,
                'hash_origen': hash_origen,
                'accion': 'insertado'
            }
            
        except Exception as e:
            logger.error(f"[CUADRES_Z_EDARSAHUB] Error al crear cuadre: {e}")
            conn.rollback()
            return {
                'success': False,
                'mensaje': f'Error: {str(e)}',
                'accion': 'error'
            }
        finally:
            conn.close()
    
    def actualizar_cuadre_z(self, cuadre_z_id: int, data: Dict, 
                            usuario_id: str = None, usuario_nombre: str = None) -> Dict:
        """
        Actualiza un Cuadre Z existente.
        
        Args:
            cuadre_z_id: ID del cuadre a actualizar
            data: Datos a actualizar
            usuario_id: ID del usuario
            usuario_nombre: Nombre del usuario
            
        Returns:
            Dict con resultado de la operación
        """
        conn = get_edarsahub_connection()
        try:
            cursor = conn.cursor(as_dict=True)
            
            # Verificar que existe
            cursor.execute(f'''
                SELECT CuadreZID FROM {self.tabla_principal}
                WHERE CuadreZID = %s AND Activo = 1
            ''', (cuadre_z_id,))
            
            if not cursor.fetchone():
                return {
                    'success': False,
                    'mensaje': 'Cuadre no encontrado',
                    'accion': 'no_encontrado'
                }
            
            # Construir SET dinámico
            campos_permitidos = {
                'total_declarado': 'TotalDeclarado',
                'diferencia': 'Diferencia',
                'estatus_cuadre': 'EstatusCuadreID',
                'estatus_tesoreria': 'EstatusTesoreriaID',
                'observaciones': 'Observaciones',
                'ficha_deposito_url': 'FichaDepositoURL',
                'ficha_deposito_fecha': 'FichaDepositoFecha',
                'ficha_deposito_monto': 'FichaDepositoMonto',
                'ficha_deposito_validada': 'FichaDepositoValidada',
            }
            
            sets = []
            params = []
            
            for campo_py, campo_sql in campos_permitidos.items():
                if campo_py in data:
                    valor = data[campo_py]
                    if campo_py == 'estatus_cuadre':
                        valor = self._mapear_estatus_cuadre(valor)
                    elif campo_py == 'estatus_tesoreria':
                        valor = self._mapear_estatus_tesoreria(valor)
                    sets.append(f'{campo_sql} = %s')
                    params.append(valor)
            
            # Conteo de efectivo
            if 'conteo_efectivo' in data:
                conteo = data['conteo_efectivo']
                billetes = conteo.get('billetes', {})
                monedas = conteo.get('monedas', {})
                
                conteo_campos = [
                    ('b1000', 'ConteoEfectivo_Billetes1000'),
                    ('b500', 'ConteoEfectivo_Billetes500'),
                    ('b200', 'ConteoEfectivo_Billetes200'),
                    ('b100', 'ConteoEfectivo_Billetes100'),
                    ('b50', 'ConteoEfectivo_Billetes50'),
                    ('b20', 'ConteoEfectivo_Billetes20'),
                ]
                moneda_campos = [
                    ('m20', 'ConteoEfectivo_Monedas20'),
                    ('m10', 'ConteoEfectivo_Monedas10'),
                    ('m5', 'ConteoEfectivo_Monedas5'),
                    ('m2', 'ConteoEfectivo_Monedas2'),
                    ('m1', 'ConteoEfectivo_Monedas1'),
                    ('m050', 'ConteoEfectivo_Monedas050'),
                ]
                
                for key, col in conteo_campos:
                    if key in billetes:
                        sets.append(f'{col} = %s')
                        params.append(billetes[key])
                
                for key, col in moneda_campos:
                    if key in monedas:
                        sets.append(f'{col} = %s')
                        params.append(monedas[key])
                
                # Calcular total conteo
                total_conteo = (
                    billetes.get('b1000', 0) * 1000 +
                    billetes.get('b500', 0) * 500 +
                    billetes.get('b200', 0) * 200 +
                    billetes.get('b100', 0) * 100 +
                    billetes.get('b50', 0) * 50 +
                    billetes.get('b20', 0) * 20 +
                    monedas.get('m20', 0) * 20 +
                    monedas.get('m10', 0) * 10 +
                    monedas.get('m5', 0) * 5 +
                    monedas.get('m2', 0) * 2 +
                    monedas.get('m1', 0) * 1 +
                    monedas.get('m050', 0) * 0.50
                )
                sets.append('ConteoEfectivo_Total = %s')
                params.append(total_conteo)
            
            if not sets:
                return {
                    'success': False,
                    'mensaje': 'No hay campos para actualizar',
                    'accion': 'sin_cambios'
                }
            
            # Agregar campos de auditoría
            if 'estatus_cuadre' in data and data.get('estatus_cuadre') in ['VALIDADO', 'RECHAZADO']:
                sets.append('UsuarioValidaID = %s')
                params.append(usuario_id)
                sets.append('UsuarioValidaNombre = %s')
                params.append(usuario_nombre)
                sets.append('FechaValidacion = %s')
                params.append(datetime.now())
            
            sets.append('FechaUltimaActualizacion = %s')
            params.append(datetime.now())
            
            params.append(cuadre_z_id)
            
            sql = f'''
                UPDATE {self.tabla_principal}
                SET {', '.join(sets)}
                WHERE CuadreZID = %s
            '''
            
            cursor.execute(sql, tuple(params))
            conn.commit()
            
            logger.info(f"[CUADRES_Z_EDARSAHUB] Cuadre actualizado: {cuadre_z_id}")
            
            return {
                'success': True,
                'mensaje': 'Cuadre actualizado exitosamente',
                'cuadre_z_id': cuadre_z_id,
                'accion': 'actualizado'
            }
            
        except Exception as e:
            logger.error(f"[CUADRES_Z_EDARSAHUB] Error al actualizar cuadre: {e}")
            conn.rollback()
            return {
                'success': False,
                'mensaje': f'Error: {str(e)}',
                'accion': 'error'
            }
        finally:
            conn.close()
    
    def obtener_cuadre_z(self, cuadre_z_id: int) -> Optional[Dict]:
        """Obtiene un Cuadre Z por ID."""
        conn = get_edarsahub_connection()
        try:
            cursor = conn.cursor(as_dict=True)
            cursor.execute(f'''
                SELECT 
                    cz.*,
                    ec.Codigo as EstatusCuadreCodigo,
                    ec.Descripcion as EstatusCuadreDescripcion,
                    ec.ColorHex as EstatusCuadreColor,
                    et.Codigo as EstatusTesoreriaCodigo,
                    et.Descripcion as EstatusTesoreriaDescripcion,
                    et.ColorHex as EstatusTesoreriaColor
                FROM {self.tabla_principal} cz
                LEFT JOIN {self.tabla_estatus_cuadre} ec ON cz.EstatusCuadreID = ec.EstatusCuadreID
                LEFT JOIN {self.tabla_estatus_tesoreria} et ON cz.EstatusTesoreriaID = et.EstatusTesoreriaID
                WHERE cz.CuadreZID = %s AND cz.Activo = 1
            ''', (cuadre_z_id,))
            
            row = cursor.fetchone()
            if row:
                return self._formatear_cuadre(row)
            return None
        finally:
            conn.close()
    
    def listar_cuadres_z(self, filtros: Dict = None) -> List[Dict]:
        """
        Lista Cuadres Z con filtros opcionales.
        
        Filtros soportados:
        - unidad_negocio_id / unidades_permitidas (lista)
        - fecha_inicio
        - fecha_fin
        - estatus_cuadre
        - estatus_tesoreria
        - caja_id
        - cajero_id
        - folio_corte
        - folio_z
        - activo
        - es_demo
        - limit
        - offset
        """
        filtros = filtros or {}
        
        conn = get_edarsahub_connection()
        try:
            cursor = conn.cursor(as_dict=True)
            
            where_clauses = ['cz.Activo = 1']
            params = []
            
            # Filtro por unidad(es)
            if 'unidades_permitidas' in filtros and filtros['unidades_permitidas']:
                placeholders = ','.join(['%s'] * len(filtros['unidades_permitidas']))
                where_clauses.append(f'cz.UnidadNegocioID IN ({placeholders})')
                params.extend(filtros['unidades_permitidas'])
            elif 'unidad_negocio_id' in filtros:
                where_clauses.append('cz.UnidadNegocioID = %s')
                params.append(filtros['unidad_negocio_id'])
            
            # Filtro por fechas
            if 'fecha_inicio' in filtros:
                where_clauses.append('cz.FechaCorte >= %s')
                params.append(filtros['fecha_inicio'])
            if 'fecha_fin' in filtros:
                where_clauses.append('cz.FechaCorte <= %s')
                params.append(filtros['fecha_fin'])
            
            # Filtro por estatus
            if 'estatus_cuadre' in filtros:
                estatus_id = self._mapear_estatus_cuadre(filtros['estatus_cuadre'])
                where_clauses.append('cz.EstatusCuadreID = %s')
                params.append(estatus_id)
            if 'estatus_tesoreria' in filtros:
                estatus_id = self._mapear_estatus_tesoreria(filtros['estatus_tesoreria'])
                where_clauses.append('cz.EstatusTesoreriaID = %s')
                params.append(estatus_id)
            
            # Otros filtros
            if 'caja_id' in filtros:
                where_clauses.append('cz.CajaID = %s')
                params.append(filtros['caja_id'])
            if 'cajero_id' in filtros:
                where_clauses.append('cz.CajeroID = %s')
                params.append(filtros['cajero_id'])
            if 'folio_corte' in filtros:
                where_clauses.append('cz.FolioCorte = %s')
                params.append(filtros['folio_corte'])
            if 'folio_z' in filtros:
                where_clauses.append('cz.FolioZ = %s')
                params.append(filtros['folio_z'])
            if 'es_demo' in filtros:
                where_clauses.append('cz.EsDemo = %s')
                params.append(1 if filtros['es_demo'] else 0)
            
            where_sql = ' AND '.join(where_clauses)
            
            # Paginación
            limit = filtros.get('limit', 100)
            offset = filtros.get('offset', 0)
            
            sql = f'''
                SELECT 
                    cz.*,
                    ec.Codigo as EstatusCuadreCodigo,
                    ec.Descripcion as EstatusCuadreDescripcion,
                    ec.ColorHex as EstatusCuadreColor,
                    et.Codigo as EstatusTesoreriaCodigo,
                    et.Descripcion as EstatusTesoreriaDescripcion,
                    et.ColorHex as EstatusTesoreriaColor
                FROM {self.tabla_principal} cz
                LEFT JOIN {self.tabla_estatus_cuadre} ec ON cz.EstatusCuadreID = ec.EstatusCuadreID
                LEFT JOIN {self.tabla_estatus_tesoreria} et ON cz.EstatusTesoreriaID = et.EstatusTesoreriaID
                WHERE {where_sql}
                ORDER BY cz.FechaCorte DESC, cz.CuadreZID DESC
                OFFSET {offset} ROWS FETCH NEXT {limit} ROWS ONLY
            '''
            
            cursor.execute(sql, tuple(params))
            rows = cursor.fetchall()
            
            return [self._formatear_cuadre(row) for row in rows]
        finally:
            conn.close()
    
    def obtener_resumen_cuadres_z(self, filtros: Dict = None) -> Dict:
        """
        Obtiene resumen de Cuadres Z con filtros.
        
        Retorna:
        - Total de cuadres
        - Total por estatus
        - Suma de TotalVenta
        - Suma de TotalEfectivo
        - Suma de TotalTarjeta
        - Suma de Diferencias
        """
        filtros = filtros or {}
        
        conn = get_edarsahub_connection()
        try:
            cursor = conn.cursor(as_dict=True)
            
            where_clauses = ['cz.Activo = 1', 'cz.EsDemo = 0']
            params = []
            
            if 'unidades_permitidas' in filtros and filtros['unidades_permitidas']:
                placeholders = ','.join(['%s'] * len(filtros['unidades_permitidas']))
                where_clauses.append(f'cz.UnidadNegocioID IN ({placeholders})')
                params.extend(filtros['unidades_permitidas'])
            elif 'unidad_negocio_id' in filtros:
                where_clauses.append('cz.UnidadNegocioID = %s')
                params.append(filtros['unidad_negocio_id'])
            
            if 'fecha_inicio' in filtros:
                where_clauses.append('cz.FechaCorte >= %s')
                params.append(filtros['fecha_inicio'])
            if 'fecha_fin' in filtros:
                where_clauses.append('cz.FechaCorte <= %s')
                params.append(filtros['fecha_fin'])
            
            where_sql = ' AND '.join(where_clauses)
            
            # Totales generales
            sql_totales = f'''
                SELECT 
                    COUNT(*) as total_cuadres,
                    ISNULL(SUM(cz.TotalVenta), 0) as total_venta,
                    ISNULL(SUM(cz.TotalEfectivo), 0) as total_efectivo,
                    ISNULL(SUM(cz.TotalTarjetaTotal), 0) as total_tarjeta,
                    ISNULL(SUM(cz.TotalDepositar), 0) as total_depositar,
                    ISNULL(SUM(cz.TotalDeclarado), 0) as total_declarado,
                    ISNULL(SUM(cz.Diferencia), 0) as total_diferencia,
                    ISNULL(SUM(cz.ConteoEfectivo_Total), 0) as total_conteo_efectivo
                FROM {self.tabla_principal} cz
                WHERE {where_sql}
            '''
            cursor.execute(sql_totales, tuple(params))
            totales = cursor.fetchone()
            
            # Por estatus cuadre
            sql_por_estatus = f'''
                SELECT 
                    ec.Codigo as estatus,
                    ec.ColorHex as color,
                    COUNT(*) as cantidad
                FROM {self.tabla_principal} cz
                LEFT JOIN {self.tabla_estatus_cuadre} ec ON cz.EstatusCuadreID = ec.EstatusCuadreID
                WHERE {where_sql}
                GROUP BY ec.Codigo, ec.ColorHex, ec.Orden
                ORDER BY ec.Orden
            '''
            cursor.execute(sql_por_estatus, tuple(params))
            por_estatus = cursor.fetchall()
            
            return {
                'total_cuadres': totales['total_cuadres'],
                'total_venta': float(totales['total_venta']),
                'total_efectivo': float(totales['total_efectivo']),
                'total_tarjeta': float(totales['total_tarjeta']),
                'total_depositar': float(totales['total_depositar']),
                'total_declarado': float(totales['total_declarado']),
                'total_diferencia': float(totales['total_diferencia']),
                'total_conteo_efectivo': float(totales['total_conteo_efectivo']),
                'por_estatus': [
                    {
                        'estatus': r['estatus'],
                        'color': r['color'],
                        'cantidad': r['cantidad']
                    }
                    for r in por_estatus
                ]
            }
        finally:
            conn.close()
    
    def _formatear_cuadre(self, row: Dict) -> Dict:
        """Formatea un registro de cuadre para respuesta API."""
        return {
            'cuadre_z_id': row['CuadreZID'],
            'unidad_negocio_id': row['UnidadNegocioID'],
            'unidad_negocio_nombre': row['UnidadNegocioNombre'],
            'empresa_id': row.get('EmpresaID'),
            'server_id': row['ServerID'],
            'sistema_origen': row['SistemaOrigen'],
            'fecha_operacion': row['FechaOperacion'].isoformat() if row.get('FechaOperacion') else None,
            'fecha_corte': row['FechaCorte'].isoformat() if row.get('FechaCorte') else None,
            'folio_corte': row['FolioCorte'],
            'folio_z': row.get('FolioZ'),
            'caja_id': row.get('CajaID'),
            'caja_nombre': row.get('CajaNombre'),
            'cajero_id': row.get('CajeroID'),
            'cajero_nombre': row.get('CajeroNombre'),
            'turno_id': row.get('TurnoID'),
            'totales': {
                'venta': float(row.get('TotalVenta') or 0),
                'efectivo': float(row.get('TotalEfectivo') or 0),
                'tarjeta_debito': float(row.get('TotalTarjetaDebito') or 0),
                'tarjeta_credito': float(row.get('TotalTarjetaCredito') or 0),
                'amex': float(row.get('TotalAmex') or 0),
                'tarjeta_total': float(row.get('TotalTarjetaTotal') or 0),
                'transferencia': float(row.get('TotalTransferencia') or 0),
                'vales': float(row.get('TotalVales') or 0),
                'otros': float(row.get('TotalOtros') or 0),
                'propinas_tpv': float(row.get('TotalPropinasTPV') or 0),
                'propinas_efectivo': float(row.get('TotalPropinasEfectivo') or 0),
                'retiros': float(row.get('TotalRetiros') or 0),
                'fondo_inicial': float(row.get('FondoInicial') or 0),
            },
            'cuadre': {
                'total_depositar': float(row.get('TotalDepositar') or 0),
                'total_declarado': float(row.get('TotalDeclarado') or 0),
                'diferencia': float(row.get('Diferencia') or 0),
            },
            'conteo_efectivo': {
                'billetes': {
                    'b1000': row.get('ConteoEfectivo_Billetes1000') or 0,
                    'b500': row.get('ConteoEfectivo_Billetes500') or 0,
                    'b200': row.get('ConteoEfectivo_Billetes200') or 0,
                    'b100': row.get('ConteoEfectivo_Billetes100') or 0,
                    'b50': row.get('ConteoEfectivo_Billetes50') or 0,
                    'b20': row.get('ConteoEfectivo_Billetes20') or 0,
                },
                'monedas': {
                    'm20': row.get('ConteoEfectivo_Monedas20') or 0,
                    'm10': row.get('ConteoEfectivo_Monedas10') or 0,
                    'm5': row.get('ConteoEfectivo_Monedas5') or 0,
                    'm2': row.get('ConteoEfectivo_Monedas2') or 0,
                    'm1': row.get('ConteoEfectivo_Monedas1') or 0,
                    'm050': row.get('ConteoEfectivo_Monedas050') or 0,
                },
                'total': float(row.get('ConteoEfectivo_Total') or 0),
            },
            'ficha_deposito': {
                'url': row.get('FichaDepositoURL'),
                'fecha': row['FichaDepositoFecha'].isoformat() if row.get('FichaDepositoFecha') else None,
                'monto': float(row.get('FichaDepositoMonto') or 0),
                'validada': bool(row.get('FichaDepositoValidada')),
                'banco_id': row.get('FichaDepositoBancoID'),
                'cuenta_id': row.get('FichaDepositoCuentaID'),
            },
            'estatus': {
                'cuadre': {
                    'id': row['EstatusCuadreID'],
                    'codigo': row.get('EstatusCuadreCodigo'),
                    'descripcion': row.get('EstatusCuadreDescripcion'),
                    'color': row.get('EstatusCuadreColor'),
                },
                'tesoreria': {
                    'id': row['EstatusTesoreriaID'],
                    'codigo': row.get('EstatusTesoreriaCodigo'),
                    'descripcion': row.get('EstatusTesoreriaDescripcion'),
                    'color': row.get('EstatusTesoreriaColor'),
                },
            },
            'observaciones': row.get('Observaciones'),
            'auditoria': {
                'usuario_captura_id': row.get('UsuarioCapturaID'),
                'usuario_captura_nombre': row.get('UsuarioCapturaNombre'),
                'fecha_captura': row['FechaCaptura'].isoformat() if row.get('FechaCaptura') else None,
                'usuario_valida_id': row.get('UsuarioValidaID'),
                'usuario_valida_nombre': row.get('UsuarioValidaNombre'),
                'fecha_validacion': row['FechaValidacion'].isoformat() if row.get('FechaValidacion') else None,
            },
            'relaciones': {
                'corte_caja_id': row.get('CorteCajaID'),
            },
            'trazabilidad': {
                'fuente_original': row.get('FuenteOriginal'),
                'id_origen': row.get('IdOrigen'),
                'hash_origen': row.get('HashOrigen'),
            },
            'control': {
                'es_demo': bool(row.get('EsDemo')),
                'activo': bool(row.get('Activo')),
                'fecha_alta': row['FechaAlta'].isoformat() if row.get('FechaAlta') else None,
                'fecha_actualizacion': row['FechaUltimaActualizacion'].isoformat() if row.get('FechaUltimaActualizacion') else None,
            }
        }
    
    # =========================================================================
    # BITÁCORA
    # =========================================================================
    
    def registrar_log_operacion(self, data: Dict) -> int:
        """Registra una operación en la bitácora."""
        conn = get_edarsahub_connection()
        try:
            cursor = conn.cursor()
            
            sql = f'''
                INSERT INTO {self.tabla_synclog} (
                    JobName, TipoOperacion, UnidadNegocioID, UnidadNegocioNombre,
                    FechaDesde, FechaHasta,
                    RegistrosLeidos, RegistrosInsertados, RegistrosActualizados,
                    RegistrosOmitidos, RegistrosError, MensajeError,
                    FechaInicio, FechaFin, DuracionMs,
                    UsuarioID, UsuarioNombre, Estatus, Metadata
                )
                OUTPUT INSERTED.LogID
                VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
            '''
            
            params = (
                data.get('job_name', 'MANUAL'),
                data.get('tipo_operacion', 'CONSULTA'),
                data.get('unidad_negocio_id'),
                data.get('unidad_negocio_nombre'),
                data.get('fecha_desde'),
                data.get('fecha_hasta'),
                data.get('registros_leidos', 0),
                data.get('registros_insertados', 0),
                data.get('registros_actualizados', 0),
                data.get('registros_omitidos', 0),
                data.get('registros_error', 0),
                data.get('mensaje_error'),
                data.get('fecha_inicio', datetime.now()),
                data.get('fecha_fin'),
                data.get('duracion_ms'),
                data.get('usuario_id'),
                data.get('usuario_nombre'),
                data.get('estatus', 'COMPLETADO'),
                data.get('metadata')
            )
            
            cursor.execute(sql, params)
            result = cursor.fetchone()
            conn.commit()
            
            return result[0] if result else None
        finally:
            conn.close()


    # =========================================================================
    # RESOLUCIÓN SERVER_ID → UNIDAD_NEGOCIO_ID
    # FINANZAS-TESORERIA-MONGO-002: Agregado 2026-05-25
    # =========================================================================
    
    def resolver_server_id_a_unidad(self, server_id: str) -> Optional[Dict]:
        """
        Resuelve server_id (UUID) a UnidadNegocioID usando EDARSAHUB SQL.
        
        Camino de resolución:
        server_id → Servidores_Conexiones → Sistema_SucursalServidorMapeo → Sistema_Sucursales
        
        Args:
            server_id: UUID del servidor (frontend)
            
        Returns:
            Dict con unidad_negocio_id, nombre, empresa_id si se encuentra
            None si no se encuentra
        """
        if not server_id:
            return None
            
        conn = get_edarsahub_connection()
        try:
            cursor = conn.cursor(as_dict=True)
            
            # Primero buscar si el server_id coincide directamente con UnidadNegocioID
            # (en algunos casos server_id = unidad_negocio_id)
            cursor.execute('''
                SELECT DISTINCT TOP 1
                    cz.UnidadNegocioID,
                    cz.UnidadNegocioNombre,
                    cz.EmpresaID
                FROM Finanzas_CuadresZ cz
                WHERE cz.ServerID = %s AND cz.Activo = 1
            ''', (server_id,))
            
            row = cursor.fetchone()
            if row:
                logger.debug(f"[CUADRES_Z] server_id={server_id} resuelto desde Finanzas_CuadresZ")
                return {
                    'unidad_negocio_id': row['UnidadNegocioID'],
                    'nombre': row['UnidadNegocioNombre'],
                    'empresa_id': row.get('EmpresaID')
                }
            
            # Si no hay cuadres, buscar en Servidores_Conexiones
            cursor.execute('''
                SELECT 
                    sc.id as servidor_id,
                    sc.name as nombre_servidor,
                    ssm.SucursalId,
                    suc.Nombre as nombre_sucursal,
                    suc.EmpresaId
                FROM Servidores_Conexiones sc
                LEFT JOIN Sistema_SucursalServidorMapeo ssm ON sc.id = ssm.ServidorId
                LEFT JOIN Sistema_Sucursales suc ON ssm.SucursalId = suc.Id
                WHERE sc.id = %s
            ''', (server_id,))
            
            row = cursor.fetchone()
            if row:
                unidad_id = row.get('SucursalId') or row.get('servidor_id')
                nombre = row.get('nombre_sucursal') or row.get('nombre_servidor')
                logger.debug(f"[CUADRES_Z] server_id={server_id} resuelto desde Servidores_Conexiones: {unidad_id}")
                return {
                    'unidad_negocio_id': unidad_id,
                    'nombre': nombre,
                    'empresa_id': row.get('EmpresaId')
                }
            
            logger.warning(f"[CUADRES_Z] server_id={server_id} no encontrado en EDARSAHUB")
            return None
            
        except Exception as e:
            logger.error(f"[CUADRES_Z] Error resolviendo server_id={server_id}: {e}")
            return None
        finally:
            conn.close()
    
    def listar_cuadres_z_por_server_id(self, server_id: str, filtros: Dict = None) -> List[Dict]:
        """
        Lista Cuadres Z filtrando por server_id.
        
        FINANZAS-TESORERIA-MONGO-002: Método agregado para compatibilidad con frontend
        que envía server_id en lugar de unidad_negocio_id.
        
        Args:
            server_id: UUID del servidor
            filtros: Filtros adicionales (fecha_inicio, fecha_fin, estatus_cuadre, etc.)
            
        Returns:
            Lista de cuadres formateados
        """
        filtros = filtros or {}
        
        conn = get_edarsahub_connection()
        try:
            cursor = conn.cursor(as_dict=True)
            
            where_clauses = ['cz.Activo = 1', 'cz.ServerID = %s']
            params = [server_id]
            
            # Filtro por fechas
            if 'fecha_inicio' in filtros:
                where_clauses.append('cz.FechaCorte >= %s')
                params.append(filtros['fecha_inicio'])
            if 'fecha_fin' in filtros:
                where_clauses.append('cz.FechaCorte <= %s')
                params.append(filtros['fecha_fin'])
            
            # Filtro por estatus
            if 'estatus_cuadre' in filtros:
                estatus_id = self._mapear_estatus_cuadre(filtros['estatus_cuadre'])
                where_clauses.append('cz.EstatusCuadreID = %s')
                params.append(estatus_id)
            
            where_sql = ' AND '.join(where_clauses)
            
            limit = filtros.get('limit', 100)
            offset = filtros.get('offset', 0)
            
            sql = f'''
                SELECT 
                    cz.*,
                    ec.Codigo as EstatusCuadreCodigo,
                    ec.Descripcion as EstatusCuadreDescripcion,
                    ec.ColorHex as EstatusCuadreColor,
                    et.Codigo as EstatusTesoreriaCodigo,
                    et.Descripcion as EstatusTesoreriaDescripcion,
                    et.ColorHex as EstatusTesoreriaColor
                FROM {self.tabla_principal} cz
                LEFT JOIN {self.tabla_estatus_cuadre} ec ON cz.EstatusCuadreID = ec.EstatusCuadreID
                LEFT JOIN {self.tabla_estatus_tesoreria} et ON cz.EstatusTesoreriaID = et.EstatusTesoreriaID
                WHERE {where_sql}
                ORDER BY cz.FechaCorte DESC, cz.CuadreZID DESC
                OFFSET {offset} ROWS FETCH NEXT {limit} ROWS ONLY
            '''
            
            cursor.execute(sql, tuple(params))
            rows = cursor.fetchall()
            
            return [self._formatear_cuadre(row) for row in rows]
        finally:
            conn.close()
    
    def obtener_resumen_por_server_id(self, server_id: str, filtros: Dict = None) -> Dict:
        """
        Obtiene resumen de Cuadres Z para un server_id específico.
        
        FINANZAS-TESORERIA-MONGO-002: Método agregado para compatibilidad con frontend.
        
        Args:
            server_id: UUID del servidor
            filtros: Filtros adicionales
            
        Returns:
            Dict con resumen de cuadres
        """
        filtros = filtros or {}
        
        conn = get_edarsahub_connection()
        try:
            cursor = conn.cursor(as_dict=True)
            
            where_clauses = ['cz.Activo = 1', 'cz.EsDemo = 0', 'cz.ServerID = %s']
            params = [server_id]
            
            if 'fecha_inicio' in filtros:
                where_clauses.append('cz.FechaCorte >= %s')
                params.append(filtros['fecha_inicio'])
            if 'fecha_fin' in filtros:
                where_clauses.append('cz.FechaCorte <= %s')
                params.append(filtros['fecha_fin'])
            
            where_sql = ' AND '.join(where_clauses)
            
            # Totales generales
            sql_totales = f'''
                SELECT 
                    COUNT(*) as total_cuadres,
                    ISNULL(SUM(cz.TotalVenta), 0) as total_venta,
                    ISNULL(SUM(cz.TotalEfectivo), 0) as total_efectivo,
                    ISNULL(SUM(cz.TotalTarjetaTotal), 0) as total_tarjeta,
                    ISNULL(SUM(cz.TotalDepositar), 0) as total_depositar,
                    ISNULL(SUM(cz.TotalDeclarado), 0) as total_declarado,
                    ISNULL(SUM(cz.Diferencia), 0) as total_diferencia
                FROM {self.tabla_principal} cz
                WHERE {where_sql}
            '''
            cursor.execute(sql_totales, tuple(params))
            totales = cursor.fetchone()
            
            # Por estatus
            sql_por_estatus = f'''
                SELECT 
                    ec.Codigo as estatus,
                    ec.ColorHex as color,
                    COUNT(*) as cantidad
                FROM {self.tabla_principal} cz
                LEFT JOIN {self.tabla_estatus_cuadre} ec ON cz.EstatusCuadreID = ec.EstatusCuadreID
                WHERE {where_sql}
                GROUP BY ec.Codigo, ec.ColorHex, ec.Orden
                ORDER BY ec.Orden
            '''
            cursor.execute(sql_por_estatus, tuple(params))
            por_estatus = cursor.fetchall()
            
            # Formatear para compatibilidad con contrato anterior (MongoDB)
            resumen_legacy = {
                'PENDIENTE': {'count': 0, 'total_esperado': 0, 'total_depositado': 0},
                'EN_PROCESO': {'count': 0, 'total_esperado': 0, 'total_depositado': 0},
                'CUADRADO': {'count': 0, 'total_esperado': 0, 'total_depositado': 0},
                'DESCUADRE': {'count': 0, 'total_esperado': 0, 'total_depositado': 0}
            }
            
            for r in por_estatus:
                estatus = r.get('estatus', 'PENDIENTE')
                if estatus in resumen_legacy:
                    resumen_legacy[estatus]['count'] = r['cantidad']
            
            return {
                'resumen': resumen_legacy,  # Formato legacy para compatibilidad frontend
                'totales': {
                    'total_cuadres': totales['total_cuadres'],
                    'total_venta': float(totales['total_venta']),
                    'total_efectivo': float(totales['total_efectivo']),
                    'total_tarjeta': float(totales['total_tarjeta']),
                    'total_depositar': float(totales['total_depositar']),
                    'total_declarado': float(totales['total_declarado']),
                    'total_diferencia': float(totales['total_diferencia']),
                },
                'por_estatus': [
                    {
                        'estatus': r['estatus'],
                        'color': r['color'],
                        'cantidad': r['cantidad']
                    }
                    for r in por_estatus
                ]
            }
        finally:
            conn.close()


# ============================================================================
# SINGLETON PATTERN
# ============================================================================

_repo_instance = None

def get_cuadres_z_repository_sql() -> RepositoryCuadresZEdarsahub:
    """
    Obtiene instancia singleton del repositorio SQL de Cuadres Z.
    
    FINANZAS-TESORERIA-MONGO-002: Factory method para tesoreria.py
    """
    global _repo_instance
    if _repo_instance is None:
        _repo_instance = RepositoryCuadresZEdarsahub()
    return _repo_instance


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    'RepositoryCuadresZEdarsahub',
    'calcular_hash_origen',
    'validar_hash_origen',
    'get_edarsahub_connection',
    'get_cuadres_z_repository_sql'
]
