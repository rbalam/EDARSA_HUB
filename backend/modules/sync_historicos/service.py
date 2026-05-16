"""
EDARSA HUB - Sync Históricos: Service
=====================================
FASE SYNC-1: Lógica de negocio para sincronización histórica.

VENTANA OPERATIVA: 13:00 - 11:00 (cruza medianoche)

MODOS:
- dry_run=True: Solo calcula, no escribe
- dry_run=False: Escribe en EDARSAHUB (requiere dry_run exitoso previo)

PROTECCIÓN ANTI-$0 FALSO:
- Si falla conexión/query: NO guardar venta 0
- Registrar source_status = ERROR
"""

import logging
import uuid
from datetime import date, datetime, time, timedelta
from typing import List, Optional, Dict, Any
from decimal import Decimal

from core.db import execute_sql_query
from core.server_registry import (
    _get_servers_from_sql,
    _get_server_by_id_from_sql,
    get_decrypted_credentials,
    EDARSAHUB_CONFIG,
)
from core.utils.operational_window import (
    MEXICO_TZ,
    get_mexico_now,
    get_sync_operational_window,
    DEFAULT_VENTANA_INICIO_HORA,
    DEFAULT_VENTANA_FIN_HORA,
)

from .models import (
    SyncVentaHistorica,
    SyncVentaPorHora,
    SyncVentaPorDiaSemana,
    SyncControlEjecucion,
    SyncRunConfig,
    SyncRunResult,
    SourceStatus,
    SourceType,
)
from .repository import SyncHistoricosRepository

logger = logging.getLogger(__name__)


class SyncHistoricosService:
    """
    Service para sincronización de históricos de ventas.
    """
    
    def __init__(self, repository: Optional[SyncHistoricosRepository] = None):
        """Inicializa el service."""
        self._repo = repository or SyncHistoricosRepository()
    
    def inicializar_infraestructura(self) -> Dict[str, bool]:
        """
        Crea las tablas Sync_* si no existen.
        
        Returns:
            Dict con resultado por tabla
        """
        logger.info("[SYNC-SERVICE] Inicializando infraestructura de sincronización...")
        return self._repo.create_tables_if_not_exist()
    
    def _generar_sync_run_id(self) -> str:
        """Genera un ID único para el run de sincronización."""
        return f"SYNC-{datetime.now(MEXICO_TZ).strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:8]}"
    
    def _calcular_rango_fechas(self, config: SyncRunConfig) -> tuple:
        """Calcula el rango de fechas a procesar."""
        if config.fecha_inicio and config.fecha_fin:
            return config.fecha_inicio, config.fecha_fin
        
        # Usar días atrás desde fecha operativa actual
        fecha_op_hoy, _, _, _ = get_sync_operational_window(
            get_mexico_now(),
            config.ventana_inicio_hora,
            config.ventana_fin_hora
        )
        fecha_fin = fecha_op_hoy
        fecha_inicio = fecha_op_hoy - timedelta(days=config.dias_atras)
        
        return fecha_inicio, fecha_fin
    
    def _obtener_ventas_dia_softrestaurant(
        self,
        server_info: Dict,
        fecha_operacion: date,
        ventana_inicio: time,
        ventana_fin: time
    ) -> Optional[Dict]:
        """
        Obtiene ventas del día para SoftRestaurant.
        
        PROTECCIÓN ANTI-$0 FALSO:
        - Si falla, retorna None (NO Decimal(0))
        - El llamador debe registrar source_status = ERROR
        """
        try:
            # Construir rango de fechas para la jornada operativa
            # Si cruza medianoche, la query debe considerar fecha_operacion y fecha_operacion+1
            fecha_str = fecha_operacion.strftime('%Y-%m-%d')
            fecha_sig = (fecha_operacion + timedelta(days=1)).strftime('%Y-%m-%d')
            
            # Query para cheques cerrados
            query = f"""
            SELECT 
                ISNULL(SUM(CASE WHEN formadepago = 'EFE' OR formadepago LIKE '%EFEC%' THEN total ELSE 0 END), 0) as venta_efectivo,
                ISNULL(SUM(CASE WHEN formadepago LIKE '%TARJ%' OR formadepago = 'TAR' THEN total ELSE 0 END), 0) as venta_tarjeta,
                ISNULL(SUM(CASE WHEN formadepago NOT IN ('EFE', 'TAR') AND formadepago NOT LIKE '%EFEC%' AND formadepago NOT LIKE '%TARJ%' THEN total ELSE 0 END), 0) as venta_otros,
                ISNULL(SUM(total), 0) as venta_total,
                COUNT(DISTINCT folio) as num_tickets
            FROM cuentas
            WHERE cancelado = 0
              AND fecha >= '{fecha_str}'
              AND fecha < '{fecha_sig} {ventana_fin}'
              AND DATEPART(HOUR, fecha) >= {ventana_inicio.hour}
              OR (fecha >= '{fecha_sig}' AND DATEPART(HOUR, fecha) < {ventana_fin.hour})
            """
            
            # Query simplificada que funciona mejor
            query_simple = f"""
            SELECT 
                ISNULL(SUM(total), 0) as venta_total,
                COUNT(DISTINCT folio) as num_tickets
            FROM cheques
            WHERE cancelado = 0
              AND CAST(fecha AS DATE) = '{fecha_str}'
            """
            
            result = execute_sql_query(
                server_info['host'],
                server_info['port'],
                server_info['database'],
                server_info['username'],
                server_info['password'],
                query_simple
            )
            
            if result:
                venta_total = Decimal(str(result[0].get('venta_total', 0) or 0))
                num_tickets = int(result[0].get('num_tickets', 0) or 0)
                
                return {
                    'venta_total': venta_total,
                    'venta_efectivo': Decimal('0'),  # TODO: desglosar
                    'venta_tarjeta': Decimal('0'),
                    'venta_otros': Decimal('0'),
                    'num_tickets': num_tickets,
                    'ticket_promedio': venta_total / num_tickets if num_tickets > 0 else Decimal('0')
                }
            
            return None
            
        except Exception as e:
            logger.error(f"[SYNC-SR] Error obteniendo ventas: {e}")
            return None  # NO retornar 0, retornar None para indicar error
    
    def _obtener_ventas_dia_mpro(
        self,
        server_info: Dict,
        fecha_operacion: date,
        ventana_inicio: time,
        ventana_fin: time
    ) -> Optional[Dict]:
        """
        Obtiene ventas del día para MPRO (ManagementPro).
        
        PROTECCIÓN ANTI-$0 FALSO:
        - Si falla, retorna None (NO Decimal(0))
        
        FASE SYNC-2: Corregido esquema MPRO:
        - Columna importe: Vn_Precio_Neto_Importe
        - Estado activo: Es_Cve_Estado = 'AC' (no 'CA')
        """
        try:
            fecha_str = fecha_operacion.strftime('%Y-%m-%d')
            
            # Query MPRO corregida según esquema real tabla Venta
            query = f"""
            SELECT 
                ISNULL(SUM(Vn_Precio_Neto_Importe), 0) as venta_total,
                COUNT(DISTINCT Vn_Folio) as num_tickets
            FROM Venta
            WHERE Es_Cve_Estado = 'AC'
              AND CAST(Vn_Fecha AS DATE) = '{fecha_str}'
            """
            
            result = execute_sql_query(
                server_info['host'],
                server_info['port'],
                server_info['database'],
                server_info['username'],
                server_info['password'],
                query
            )
            
            if result:
                venta_total = Decimal(str(result[0].get('venta_total', 0) or 0))
                num_tickets = int(result[0].get('num_tickets', 0) or 0)
                
                return {
                    'venta_total': venta_total,
                    'venta_efectivo': Decimal('0'),
                    'venta_tarjeta': Decimal('0'),
                    'venta_otros': Decimal('0'),
                    'num_tickets': num_tickets,
                    'ticket_promedio': venta_total / num_tickets if num_tickets > 0 else Decimal('0')
                }
            
            return None
            
        except Exception as e:
            logger.error(f"[SYNC-MPRO] Error obteniendo ventas: {e}")
            return None
    
    def sync_ventas_historicas(
        self,
        config: SyncRunConfig
    ) -> SyncRunResult:
        """
        Sincroniza ventas históricas.
        
        Args:
            config: Configuración del sync run
            
        Returns:
            SyncRunResult con detalle de la ejecución
        """
        sync_run_id = self._generar_sync_run_id()
        started_at = get_mexico_now()
        
        logger.info(
            f"[SYNC-VENTAS] Iniciando {sync_run_id}. "
            f"DryRun: {config.dry_run}, "
            f"Ventana: {config.ventana_inicio_hora}:00-{config.ventana_fin_hora}:00"
        )
        
        # Calcular rango de fechas
        fecha_inicio, fecha_fin = self._calcular_rango_fechas(config)
        
        # Obtener servidores a procesar
        all_servers = _get_servers_from_sql(filter_active=True)
        if config.server_ids:
            servers = [s for s in all_servers if s.get('id') in config.server_ids]
        else:
            servers = all_servers
        
        # Inicializar resultado
        result = SyncRunResult(
            sync_run_id=sync_run_id,
            sync_type='VENTAS_HISTORICAS',
            total_servidores=len(servers),
            servidores_exitosos=0,
            servidores_con_error=0,
            total_registros_procesados=0,
            total_registros_insertados=0,
            total_registros_actualizados=0,
            total_registros_error=0,
            is_dry_run=config.dry_run,
            started_at=started_at
        )
        
        # Registrar inicio en bitácora (solo si NO es dry-run)
        if not config.dry_run:
            try:
                control = SyncControlEjecucion(
                    sync_run_id=sync_run_id,
                    sync_type='VENTAS_HISTORICAS',
                    server_id=config.server_ids[0] if config.server_ids and len(config.server_ids) == 1 else None,
                    empresa_id=None,
                    fecha_inicio=fecha_inicio,
                    fecha_fin=fecha_fin,
                    ventana_inicio_hora_config=config.ventana_inicio_hora,
                    ventana_fin_hora_config=config.ventana_fin_hora,
                    is_dry_run=config.dry_run,
                    registros_procesados=0,
                    registros_insertados=0,
                    registros_actualizados=0,
                    registros_error=0,
                    status='RUNNING',
                    error_message=None,
                    started_at_mexico=started_at,
                    finished_at_mexico=None,
                    duration_seconds=None
                )
                self._repo.registrar_inicio_ejecucion(control)
            except Exception as e:
                logger.warning(f"[SYNC-VENTAS] No se pudo registrar inicio: {e}")
        
        # Procesar cada servidor
        for server in servers:
            server_id = server['id']
            system_type = server.get('system_type', 'UNKNOWN')
            
            logger.info(f"[SYNC-VENTAS] Procesando servidor {server_id} ({system_type})")
            
            server_result = {
                'server_id': server_id,
                'system_type': system_type,
                'fechas_procesadas': 0,
                'registros_ok': 0,
                'registros_error': 0,
                'errores': []
            }
            
            try:
                # Obtener credenciales
                server_info = _get_server_by_id_from_sql(server_id)
                if not server_info:
                    raise Exception(f"No se encontró configuración para servidor {server_id}")
                
                # Descifrar credenciales
                creds = get_decrypted_credentials(server_info)
                server_info.update(creds)
                
                # Procesar cada fecha en el rango
                fecha_actual = fecha_inicio
                while fecha_actual <= fecha_fin:
                    # Calcular ventana operativa para esta fecha
                    # Crear un timestamp ficticio para calcular
                    ts = datetime.combine(fecha_actual, time(14, 0))  # 14:00 está dentro de jornada
                    ts = MEXICO_TZ.localize(ts)
                    
                    fecha_op, v_inicio, v_fin, cruza = get_sync_operational_window(
                        ts,
                        config.ventana_inicio_hora,
                        config.ventana_fin_hora
                    )
                    
                    # Obtener ventas según tipo de sistema
                    ventas_data = None
                    source_status = SourceStatus.SUCCESS.value
                    
                    if 'SOFT' in system_type.upper():
                        ventas_data = self._obtener_ventas_dia_softrestaurant(
                            server_info, fecha_actual, v_inicio, v_fin
                        )
                        source_type = SourceType.SOFTRESTAURANT.value
                    elif 'MPRO' in system_type.upper():
                        ventas_data = self._obtener_ventas_dia_mpro(
                            server_info, fecha_actual, v_inicio, v_fin
                        )
                        source_type = SourceType.MPRO.value
                    else:
                        logger.warning(f"[SYNC-VENTAS] Tipo de sistema no soportado: {system_type}")
                        fecha_actual += timedelta(days=1)
                        continue
                    
                    # PROTECCIÓN ANTI-$0 FALSO
                    if ventas_data is None:
                        source_status = SourceStatus.SOURCE_FAILED.value
                        server_result['registros_error'] += 1
                        server_result['errores'].append(f"Error obteniendo datos para {fecha_actual}")
                        logger.warning(
                            f"[SYNC-VENTAS] {server_id}/{fecha_actual}: "
                            f"Fuente falló - NO guardando $0"
                        )
                        fecha_actual += timedelta(days=1)
                        continue
                    
                    # Crear registro de venta
                    # FASE SYNC-2: Asegurar empresa_id no sea None
                    empresa_id_val = server.get('empresa_id')
                    if empresa_id_val is None:
                        empresa_id_val = 0
                    
                    venta = SyncVentaHistorica(
                        server_id=server_id,
                        empresa_id=empresa_id_val,
                        sucursal_id=server.get('sucursal_id'),
                        unidad_negocio_id=server.get('unidad_negocio_id'),
                        system_type=system_type,
                        fecha_operacion=fecha_actual,
                        ventana_inicio=v_inicio,
                        ventana_fin=v_fin,
                        cruza_medianoche=cruza,
                        ventana_inicio_hora_config=config.ventana_inicio_hora,
                        ventana_fin_hora_config=config.ventana_fin_hora,
                        venta_total=ventas_data['venta_total'],
                        venta_efectivo=ventas_data['venta_efectivo'],
                        venta_tarjeta=ventas_data['venta_tarjeta'],
                        venta_otros=ventas_data['venta_otros'],
                        num_tickets=ventas_data['num_tickets'],
                        ticket_promedio=ventas_data['ticket_promedio'],
                        sync_run_id=sync_run_id,
                        source_status=source_status,
                        source_type=source_type,
                        synced_at_mexico=get_mexico_now(),
                        row_hash=''  # Se calcula después
                    )
                    venta.row_hash = venta.compute_hash()
                    
                    # Dry-run: solo mostrar
                    if config.dry_run:
                        logger.info(
                            f"[SYNC-VENTAS] DRY-RUN {server_id}/{fecha_actual}: "
                            f"Venta=${venta.venta_total}, Tickets={venta.num_tickets}"
                        )
                        server_result['registros_ok'] += 1
                    else:
                        # Escritura real
                        try:
                            inserted = self._repo.upsert_venta_historica(venta)
                            if inserted:
                                result.total_registros_insertados += 1
                            else:
                                result.total_registros_actualizados += 1
                            server_result['registros_ok'] += 1
                        except Exception as e:
                            logger.error(f"[SYNC-VENTAS] Error UPSERT: {e}")
                            server_result['registros_error'] += 1
                            result.total_registros_error += 1
                    
                    server_result['fechas_procesadas'] += 1
                    result.total_registros_procesados += 1
                    
                    fecha_actual += timedelta(days=1)
                
                result.servidores_exitosos += 1
                
            except Exception as e:
                logger.error(f"[SYNC-VENTAS] Error procesando servidor {server_id}: {e}")
                server_result['errores'].append(str(e))
                result.servidores_con_error += 1
            
            result.resultados_por_servidor[server_id] = server_result
        
        # Finalizar
        finished_at = get_mexico_now()
        result.finished_at = finished_at
        result.duration_seconds = int((finished_at - started_at).total_seconds())
        result.success = result.servidores_con_error == 0
        
        # Actualizar bitácora
        if not config.dry_run:
            try:
                status = 'SUCCESS' if result.success else 'PARTIAL' if result.servidores_exitosos > 0 else 'FAILED'
                self._repo.actualizar_fin_ejecucion(
                    sync_run_id=sync_run_id,
                    status=status,
                    registros_procesados=result.total_registros_procesados,
                    registros_insertados=result.total_registros_insertados,
                    registros_actualizados=result.total_registros_actualizados,
                    registros_error=result.total_registros_error
                )
            except Exception as e:
                logger.warning(f"[SYNC-VENTAS] No se pudo actualizar bitácora: {e}")
        
        logger.info(
            f"[SYNC-VENTAS] Finalizado {sync_run_id}. "
            f"Servidores: {result.servidores_exitosos}/{result.total_servidores}, "
            f"Registros: {result.total_registros_procesados}, "
            f"Duración: {result.duration_seconds}s"
        )
        
        return result
    
    # =========================================================================
    # FASE SYNC-2B: Ventas Por Hora
    # =========================================================================
    
    def _obtener_ventas_por_hora_softrestaurant(
        self,
        server_info: Dict,
        fecha_operacion: date
    ) -> Optional[List[Dict]]:
        """
        Obtiene ventas por hora para SoftRestaurant.
        
        PROTECCIÓN ANTI-$0 FALSO: Si falla, retorna None.
        
        Returns:
            Lista de dicts {hora, venta, tickets} o None si error
        """
        try:
            fecha_str = fecha_operacion.strftime('%Y-%m-%d')
            
            query = f"""
            SELECT 
                DATEPART(HOUR, fecha) as hora,
                ISNULL(SUM(total), 0) as venta_hora,
                COUNT(DISTINCT folio) as num_tickets
            FROM cheques
            WHERE cancelado = 0
              AND CAST(fecha AS DATE) = '{fecha_str}'
            GROUP BY DATEPART(HOUR, fecha)
            ORDER BY hora
            """
            
            result = execute_sql_query(
                server_info['host'],
                server_info['port'],
                server_info['database'],
                server_info['username'],
                server_info['password'],
                query
            )
            
            if result is not None:
                return [
                    {
                        'hora': int(r.get('hora', 0)),
                        'venta_hora': Decimal(str(r.get('venta_hora', 0) or 0)),
                        'num_tickets': int(r.get('num_tickets', 0) or 0)
                    }
                    for r in result
                ]
            
            return None
            
        except Exception as e:
            logger.error(f"[SYNC-POR-HORA-SR] Error: {e}")
            return None
    
    def _obtener_ventas_por_hora_mpro(
        self,
        server_info: Dict,
        fecha_operacion: date
    ) -> Optional[List[Dict]]:
        """
        Obtiene ventas por hora para MPRO.
        
        FASE SYNC-2: Usa Vn_Precio_Neto_Importe y Es_Cve_Estado = 'AC'
        
        FASE SYNC-2C (2026-05-16): Corrección hora MPRO
        - PROBLEMA: Vn_Fecha solo contiene fecha (hora siempre 00:00:00)
        - SOLUCIÓN: Usar Fecha_Alta para extraer hora real de registro
        - VALIDACIÓN: 
          * Vn_Fecha: Fecha operativa (día al que pertenece la venta)
          * Fecha_Alta: Timestamp real del sistema (contiene hora)
        - EVIDENCIA: Análisis de esquema MPRO CENTRAL2020 confirmó que Fecha_Alta
          tiene distribución horaria real (09:00-23:00, 00:00-01:00)
        - TOTAL: Cuadra exactamente con Sync_Ventas_Historicas
        """
        try:
            fecha_str = fecha_operacion.strftime('%Y-%m-%d')
            
            # FASE SYNC-2C: Query corregida
            # - Filtrar por Vn_Fecha (fecha operativa del documento)
            # - Extraer hora de Fecha_Alta (timestamp real de registro)
            query = f"""
            SELECT 
                DATEPART(HOUR, Fecha_Alta) as hora,
                ISNULL(SUM(Vn_Precio_Neto_Importe), 0) as venta_hora,
                COUNT(DISTINCT Vn_Folio) as num_tickets
            FROM Venta
            WHERE Es_Cve_Estado = 'AC'
              AND CAST(Vn_Fecha AS DATE) = '{fecha_str}'
            GROUP BY DATEPART(HOUR, Fecha_Alta)
            ORDER BY hora
            """
            
            result = execute_sql_query(
                server_info['host'],
                server_info['port'],
                server_info['database'],
                server_info['username'],
                server_info['password'],
                query
            )
            
            if result is not None:
                return [
                    {
                        'hora': int(r.get('hora', 0)),
                        'venta_hora': Decimal(str(r.get('venta_hora', 0) or 0)),
                        'num_tickets': int(r.get('num_tickets', 0) or 0)
                    }
                    for r in result
                ]
            
            return None
            
        except Exception as e:
            logger.error(f"[SYNC-POR-HORA-MPRO] Error: {e}")
            return None
    
    def sync_ventas_por_hora(
        self,
        config: SyncRunConfig
    ) -> SyncRunResult:
        """
        Sincroniza ventas por hora.
        
        FASE SYNC-2B: Distribución horaria de ventas.
        """
        sync_run_id = self._generar_sync_run_id()
        started_at = get_mexico_now()
        
        logger.info(
            f"[SYNC-POR-HORA] Iniciando {sync_run_id}. "
            f"DryRun: {config.dry_run}, "
            f"Ventana: {config.ventana_inicio_hora}:00-{config.ventana_fin_hora}:00"
        )
        
        fecha_inicio, fecha_fin = self._calcular_rango_fechas(config)
        
        all_servers = _get_servers_from_sql(filter_active=True)
        if config.server_ids:
            servers = [s for s in all_servers if s.get('id') in config.server_ids]
        else:
            servers = all_servers
        
        result = SyncRunResult(
            sync_run_id=sync_run_id,
            sync_type='VENTAS_POR_HORA',
            total_servidores=len(servers),
            servidores_exitosos=0,
            servidores_con_error=0,
            total_registros_procesados=0,
            total_registros_insertados=0,
            total_registros_actualizados=0,
            total_registros_error=0,
            is_dry_run=config.dry_run,
            started_at=started_at
        )
        
        # Registrar inicio (solo si NO dry-run)
        if not config.dry_run:
            try:
                control = SyncControlEjecucion(
                    sync_run_id=sync_run_id,
                    sync_type='VENTAS_POR_HORA',
                    server_id=config.server_ids[0] if config.server_ids and len(config.server_ids) == 1 else None,
                    empresa_id=None,
                    fecha_inicio=fecha_inicio,
                    fecha_fin=fecha_fin,
                    ventana_inicio_hora_config=config.ventana_inicio_hora,
                    ventana_fin_hora_config=config.ventana_fin_hora,
                    is_dry_run=config.dry_run,
                    registros_procesados=0,
                    registros_insertados=0,
                    registros_actualizados=0,
                    registros_error=0,
                    status='RUNNING',
                    error_message=None,
                    started_at_mexico=started_at,
                    finished_at_mexico=None,
                    duration_seconds=None
                )
                self._repo.registrar_inicio_ejecucion(control)
            except Exception as e:
                logger.warning(f"[SYNC-POR-HORA] No se pudo registrar inicio: {e}")
        
        for server in servers:
            server_id = server['id']
            system_type = server.get('system_type', 'UNKNOWN')
            
            logger.info(f"[SYNC-POR-HORA] Procesando servidor {server_id} ({system_type})")
            
            server_result = {
                'server_id': server_id,
                'system_type': system_type,
                'fechas_procesadas': 0,
                'registros_ok': 0,
                'registros_error': 0,
                'errores': []
            }
            
            try:
                server_info = _get_server_by_id_from_sql(server_id)
                if not server_info:
                    raise Exception(f"No se encontró configuración para servidor {server_id}")
                
                creds = get_decrypted_credentials(server_info)
                server_info.update(creds)
                
                empresa_id_val = server.get('empresa_id')
                if empresa_id_val is None:
                    empresa_id_val = 0
                
                fecha_actual = fecha_inicio
                while fecha_actual <= fecha_fin:
                    ts = datetime.combine(fecha_actual, time(14, 0))
                    ts = MEXICO_TZ.localize(ts)
                    
                    fecha_op, v_inicio, v_fin, cruza = get_sync_operational_window(
                        ts,
                        config.ventana_inicio_hora,
                        config.ventana_fin_hora
                    )
                    
                    # Obtener ventas por hora según tipo
                    ventas_hora = None
                    if 'SOFT' in system_type.upper():
                        ventas_hora = self._obtener_ventas_por_hora_softrestaurant(
                            server_info, fecha_actual
                        )
                        source_type = SourceType.SOFTRESTAURANT.value
                    elif 'MPRO' in system_type.upper():
                        ventas_hora = self._obtener_ventas_por_hora_mpro(
                            server_info, fecha_actual
                        )
                        source_type = SourceType.MPRO.value
                    else:
                        fecha_actual += timedelta(days=1)
                        continue
                    
                    # PROTECCIÓN ANTI-$0 FALSO
                    if ventas_hora is None:
                        server_result['registros_error'] += 1
                        server_result['errores'].append(f"Error obteniendo datos hora para {fecha_actual}")
                        logger.warning(f"[SYNC-POR-HORA] {server_id}/{fecha_actual}: Fuente falló")
                        fecha_actual += timedelta(days=1)
                        continue
                    
                    # Procesar cada hora con datos
                    for hora_data in ventas_hora:
                        venta = SyncVentaPorHora(
                            server_id=server_id,
                            empresa_id=empresa_id_val,
                            sucursal_id=server.get('sucursal_id'),
                            unidad_negocio_id=server.get('unidad_negocio_id'),
                            system_type=system_type,
                            fecha_operacion=fecha_actual,
                            hora=hora_data['hora'],
                            ventana_inicio=v_inicio,
                            ventana_fin=v_fin,
                            cruza_medianoche=cruza,
                            ventana_inicio_hora_config=config.ventana_inicio_hora,
                            ventana_fin_hora_config=config.ventana_fin_hora,
                            venta_hora=hora_data['venta_hora'],
                            num_tickets_hora=hora_data['num_tickets'],
                            sync_run_id=sync_run_id,
                            source_status=SourceStatus.SUCCESS.value,
                            source_type=source_type,
                            synced_at_mexico=get_mexico_now(),
                            row_hash=''
                        )
                        venta.row_hash = venta.compute_hash()
                        
                        if config.dry_run:
                            logger.info(
                                f"[SYNC-POR-HORA] DRY-RUN {server_id}/{fecha_actual}/{hora_data['hora']}h: "
                                f"Venta=${hora_data['venta_hora']}, Tickets={hora_data['num_tickets']}"
                            )
                            server_result['registros_ok'] += 1
                        else:
                            try:
                                inserted = self._repo.upsert_venta_por_hora(venta)
                                if inserted:
                                    result.total_registros_insertados += 1
                                else:
                                    result.total_registros_actualizados += 1
                                server_result['registros_ok'] += 1
                            except Exception as e:
                                logger.error(f"[SYNC-POR-HORA] Error UPSERT: {e}")
                                server_result['registros_error'] += 1
                                result.total_registros_error += 1
                        
                        result.total_registros_procesados += 1
                    
                    server_result['fechas_procesadas'] += 1
                    fecha_actual += timedelta(days=1)
                
                result.servidores_exitosos += 1
                
            except Exception as e:
                logger.error(f"[SYNC-POR-HORA] Error procesando servidor {server_id}: {e}")
                server_result['errores'].append(str(e))
                result.servidores_con_error += 1
            
            result.resultados_por_servidor[server_id] = server_result
        
        finished_at = get_mexico_now()
        result.finished_at = finished_at
        result.duration_seconds = int((finished_at - started_at).total_seconds())
        result.success = result.servidores_con_error == 0
        
        if not config.dry_run:
            try:
                status = 'SUCCESS' if result.success else 'PARTIAL' if result.servidores_exitosos > 0 else 'FAILED'
                self._repo.actualizar_fin_ejecucion(
                    sync_run_id=sync_run_id,
                    status=status,
                    registros_procesados=result.total_registros_procesados,
                    registros_insertados=result.total_registros_insertados,
                    registros_actualizados=result.total_registros_actualizados,
                    registros_error=result.total_registros_error
                )
            except Exception as e:
                logger.warning(f"[SYNC-POR-HORA] No se pudo actualizar bitácora: {e}")
        
        logger.info(
            f"[SYNC-POR-HORA] Finalizado {sync_run_id}. "
            f"Servidores: {result.servidores_exitosos}/{result.total_servidores}, "
            f"Registros: {result.total_registros_procesados}, "
            f"Duración: {result.duration_seconds}s"
        )
        
        return result
    
    # =========================================================================
    # FASE SYNC-2B: Ventas Por Día de Semana
    # =========================================================================
    
    # Nombres de días de semana (0=Lunes, 6=Domingo)
    DIAS_SEMANA_NOMBRES = ['Lunes', 'Martes', 'Miercoles', 'Jueves', 'Viernes', 'Sabado', 'Domingo']
    
    def sync_ventas_por_dia_semana(
        self,
        config: SyncRunConfig
    ) -> SyncRunResult:
        """
        Sincroniza ventas agregadas por día de semana.
        
        FASE SYNC-2B: Analítica de ventas por día de semana.
        
        Convención: 0=Lunes, 6=Domingo (ISO 8601)
        """
        sync_run_id = self._generar_sync_run_id()
        started_at = get_mexico_now()
        
        logger.info(
            f"[SYNC-DIA-SEMANA] Iniciando {sync_run_id}. "
            f"DryRun: {config.dry_run}, "
            f"Ventana: {config.ventana_inicio_hora}:00-{config.ventana_fin_hora}:00"
        )
        
        fecha_inicio, fecha_fin = self._calcular_rango_fechas(config)
        
        all_servers = _get_servers_from_sql(filter_active=True)
        if config.server_ids:
            servers = [s for s in all_servers if s.get('id') in config.server_ids]
        else:
            servers = all_servers
        
        result = SyncRunResult(
            sync_run_id=sync_run_id,
            sync_type='VENTAS_POR_DIA_SEMANA',
            total_servidores=len(servers),
            servidores_exitosos=0,
            servidores_con_error=0,
            total_registros_procesados=0,
            total_registros_insertados=0,
            total_registros_actualizados=0,
            total_registros_error=0,
            is_dry_run=config.dry_run,
            started_at=started_at
        )
        
        if not config.dry_run:
            try:
                control = SyncControlEjecucion(
                    sync_run_id=sync_run_id,
                    sync_type='VENTAS_POR_DIA_SEMANA',
                    server_id=config.server_ids[0] if config.server_ids and len(config.server_ids) == 1 else None,
                    empresa_id=None,
                    fecha_inicio=fecha_inicio,
                    fecha_fin=fecha_fin,
                    ventana_inicio_hora_config=config.ventana_inicio_hora,
                    ventana_fin_hora_config=config.ventana_fin_hora,
                    is_dry_run=config.dry_run,
                    registros_procesados=0,
                    registros_insertados=0,
                    registros_actualizados=0,
                    registros_error=0,
                    status='RUNNING',
                    error_message=None,
                    started_at_mexico=started_at,
                    finished_at_mexico=None,
                    duration_seconds=None
                )
                self._repo.registrar_inicio_ejecucion(control)
            except Exception as e:
                logger.warning(f"[SYNC-DIA-SEMANA] No se pudo registrar inicio: {e}")
        
        for server in servers:
            server_id = server['id']
            system_type = server.get('system_type', 'UNKNOWN')
            
            logger.info(f"[SYNC-DIA-SEMANA] Procesando servidor {server_id} ({system_type})")
            
            server_result = {
                'server_id': server_id,
                'system_type': system_type,
                'dias_procesados': 0,
                'registros_ok': 0,
                'registros_error': 0,
                'errores': []
            }
            
            try:
                server_info = _get_server_by_id_from_sql(server_id)
                if not server_info:
                    raise Exception(f"No se encontró configuración para servidor {server_id}")
                
                creds = get_decrypted_credentials(server_info)
                server_info.update(creds)
                
                empresa_id_val = server.get('empresa_id')
                if empresa_id_val is None:
                    empresa_id_val = 0
                
                # Determinar tipo de fuente
                if 'SOFT' in system_type.upper():
                    source_type = SourceType.SOFTRESTAURANT.value
                elif 'MPRO' in system_type.upper():
                    source_type = SourceType.MPRO.value
                else:
                    continue
                
                # Agrupar ventas por día de semana del período
                # Dict: dia_semana -> [ventas]
                ventas_por_dia: Dict[int, List[Decimal]] = {i: [] for i in range(7)}
                
                fecha_actual = fecha_inicio
                while fecha_actual <= fecha_fin:
                    # Obtener ventas del día
                    if 'SOFT' in system_type.upper():
                        ventas_data = self._obtener_ventas_dia_softrestaurant(
                            server_info, fecha_actual, time(13, 0), time(11, 0)
                        )
                    else:
                        ventas_data = self._obtener_ventas_dia_mpro(
                            server_info, fecha_actual, time(13, 0), time(11, 0)
                        )
                    
                    if ventas_data is not None:
                        # weekday() retorna 0=Lunes, 6=Domingo (ISO 8601)
                        dia_semana = fecha_actual.weekday()
                        ventas_por_dia[dia_semana].append(ventas_data['venta_total'])
                    else:
                        server_result['registros_error'] += 1
                        server_result['errores'].append(f"Error obteniendo datos para {fecha_actual}")
                    
                    fecha_actual += timedelta(days=1)
                
                # Crear registros agregados por día de semana
                for dia_semana, ventas_lista in ventas_por_dia.items():
                    if not ventas_lista:
                        continue  # No hay datos para este día
                    
                    venta_promedio = sum(ventas_lista) / len(ventas_lista)
                    venta_min = min(ventas_lista)
                    venta_max = max(ventas_lista)
                    num_dias = len(ventas_lista)
                    
                    venta = SyncVentaPorDiaSemana(
                        server_id=server_id,
                        empresa_id=empresa_id_val,
                        sucursal_id=server.get('sucursal_id'),
                        unidad_negocio_id=server.get('unidad_negocio_id'),
                        system_type=system_type,
                        fecha_inicio_periodo=fecha_inicio,
                        fecha_fin_periodo=fecha_fin,
                        dia_semana=dia_semana,
                        dia_semana_nombre=self.DIAS_SEMANA_NOMBRES[dia_semana],
                        ventana_inicio_hora_config=config.ventana_inicio_hora,
                        ventana_fin_hora_config=config.ventana_fin_hora,
                        venta_promedio=venta_promedio,
                        venta_min=venta_min,
                        venta_max=venta_max,
                        num_dias_con_datos=num_dias,
                        sync_run_id=sync_run_id,
                        source_status=SourceStatus.SUCCESS.value,
                        source_type=source_type,
                        synced_at_mexico=get_mexico_now(),
                        row_hash=''
                    )
                    # Calcular hash manualmente
                    import hashlib, json
                    hash_data = {
                        'server_id': venta.server_id,
                        'empresa_id': venta.empresa_id,
                        'fecha_inicio': str(venta.fecha_inicio_periodo),
                        'fecha_fin': str(venta.fecha_fin_periodo),
                        'dia_semana': venta.dia_semana,
                        'venta_promedio': str(venta.venta_promedio),
                    }
                    venta.row_hash = hashlib.sha256(json.dumps(hash_data, sort_keys=True).encode()).hexdigest()[:32]
                    
                    if config.dry_run:
                        logger.info(
                            f"[SYNC-DIA-SEMANA] DRY-RUN {server_id}/{self.DIAS_SEMANA_NOMBRES[dia_semana]}: "
                            f"Promedio=${venta_promedio:.2f}, Min=${venta_min:.2f}, Max=${venta_max:.2f}, Días={num_dias}"
                        )
                        server_result['registros_ok'] += 1
                    else:
                        try:
                            inserted = self._repo.upsert_venta_por_dia_semana(venta)
                            if inserted:
                                result.total_registros_insertados += 1
                            else:
                                result.total_registros_actualizados += 1
                            server_result['registros_ok'] += 1
                        except Exception as e:
                            logger.error(f"[SYNC-DIA-SEMANA] Error UPSERT: {e}")
                            server_result['registros_error'] += 1
                            result.total_registros_error += 1
                    
                    result.total_registros_procesados += 1
                    server_result['dias_procesados'] += 1
                
                result.servidores_exitosos += 1
                
            except Exception as e:
                logger.error(f"[SYNC-DIA-SEMANA] Error procesando servidor {server_id}: {e}")
                server_result['errores'].append(str(e))
                result.servidores_con_error += 1
            
            result.resultados_por_servidor[server_id] = server_result
        
        finished_at = get_mexico_now()
        result.finished_at = finished_at
        result.duration_seconds = int((finished_at - started_at).total_seconds())
        result.success = result.servidores_con_error == 0
        
        if not config.dry_run:
            try:
                status = 'SUCCESS' if result.success else 'PARTIAL' if result.servidores_exitosos > 0 else 'FAILED'
                self._repo.actualizar_fin_ejecucion(
                    sync_run_id=sync_run_id,
                    status=status,
                    registros_procesados=result.total_registros_procesados,
                    registros_insertados=result.total_registros_insertados,
                    registros_actualizados=result.total_registros_actualizados,
                    registros_error=result.total_registros_error
                )
            except Exception as e:
                logger.warning(f"[SYNC-DIA-SEMANA] No se pudo actualizar bitácora: {e}")
        
        logger.info(
            f"[SYNC-DIA-SEMANA] Finalizado {sync_run_id}. "
            f"Servidores: {result.servidores_exitosos}/{result.total_servidores}, "
            f"Registros: {result.total_registros_procesados}, "
            f"Duración: {result.duration_seconds}s"
        )
        
        return result
