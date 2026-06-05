"""
EDARSA HUB - Sistema de Eventos de Compras
==========================================

ARQUITECTURA:
Este módulo implementa un sistema de eventos desacoplado que permite:
1. ACTUAL (Opción A): Detección por polling incremental con checkpoints
2. FUTURO (Opción C): Migración a SQL Server Service Broker

PATRÓN:
- EventDispatcher: Interfaz abstracta para disparar eventos
- PollingEventDispatcher: Implementación actual (polling)
- ServiceBrokerEventDispatcher: Implementación futura (Service Broker)

EVENTOS SOPORTADOS:
- NUEVO_INVENTARIO: Se detectó un nuevo inventario físico
- NUEVA_REQUISICION: Se detectó una nueva requisición/orden de compra
- INVENTARIO_MODIFICADO: Un inventario existente fue modificado
- REQUISICION_AUTORIZADA: Una requisición cambió a estado autorizado

Autor: E1 Agent
Fecha: 2026-05-23
"""

import os
import json
import logging
import pymssql
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, List, Any, Optional, Callable
from zoneinfo import ZoneInfo
from dataclasses import dataclass, asdict
from enum import Enum
from core.config.edarsahub_config import get_edarsahub_sql_config
_edarsa_cfg = get_edarsahub_sql_config()


logger = logging.getLogger(__name__)

# =============================================================================
# CONFIGURACIÓN
# =============================================================================

EDARSAHUB_CONFIG = {
    'host': _edarsa_cfg.host,
    'port': int(os.environ.get('EDARSAHUB_PORT', '1433')),
    'database': _edarsa_cfg.database,
    'username': _edarsa_cfg.user,
    'password': _edarsa_cfg.password
}

# Intervalo de polling en segundos (2-3 minutos recomendado)
POLLING_INTERVAL_SECONDS = int(os.environ.get('COMPRAS_POLLING_INTERVAL', '120'))


# =============================================================================
# TIPOS DE EVENTOS
# =============================================================================

class EventoTipo(str, Enum):
    NUEVO_INVENTARIO = "NUEVO_INVENTARIO"
    NUEVA_REQUISICION = "NUEVA_REQUISICION"
    INVENTARIO_MODIFICADO = "INVENTARIO_MODIFICADO"
    REQUISICION_AUTORIZADA = "REQUISICION_AUTORIZADA"


class SyncType(str, Enum):
    INVENTARIOS = "INVENTARIOS"
    REQUISICIONES = "REQUISICIONES"


@dataclass
class EventoCompras:
    """Estructura de un evento de compras."""
    evento_tipo: EventoTipo
    server_id: str
    server_name: str
    unidad_negocio_id: Optional[str]
    unidad_codigo: Optional[str]
    folio: str
    fecha: datetime
    datos: Dict[str, Any]
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now(ZoneInfo("America/Mexico_City"))
    
    def to_dict(self) -> Dict:
        return {
            "evento_tipo": self.evento_tipo.value if isinstance(self.evento_tipo, Enum) else self.evento_tipo,
            "server_id": self.server_id,
            "server_name": self.server_name,
            "unidad_negocio_id": self.unidad_negocio_id,
            "unidad_codigo": self.unidad_codigo,
            "folio": str(self.folio),
            "fecha": self.fecha.isoformat() if self.fecha else None,
            "datos": self.datos,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


# =============================================================================
# INTERFAZ ABSTRACTA DE DISPATCHER (Preparación Service Broker)
# =============================================================================

class EventDispatcher(ABC):
    """
    Interfaz abstracta para el dispatcher de eventos.
    Permite intercambiar implementación (Polling -> Service Broker) sin cambiar código cliente.
    """
    
    @abstractmethod
    def dispatch(self, evento: EventoCompras) -> bool:
        """Dispara un evento al sistema."""
        pass
    
    @abstractmethod
    def get_pending_events(self, limit: int = 100) -> List[EventoCompras]:
        """Obtiene eventos pendientes de procesar."""
        pass
    
    @abstractmethod
    def mark_as_processed(self, evento_id: int, informe_id: str = None) -> bool:
        """Marca un evento como procesado."""
        pass


# =============================================================================
# IMPLEMENTACIÓN POLLING (OPCIÓN A - ACTUAL)
# =============================================================================

class PollingEventDispatcher(EventDispatcher):
    """
    Implementación de eventos basada en polling con checkpoints.
    Los eventos se almacenan en tabla SQL y se procesan periódicamente.
    """
    
    def __init__(self):
        self._handlers: Dict[EventoTipo, List[Callable]] = {}
    
    def _get_connection(self):
        return pymssql.connect(
            server=EDARSAHUB_CONFIG['host'],
            port=EDARSAHUB_CONFIG['port'],
            database=EDARSAHUB_CONFIG['database'],
            user=EDARSAHUB_CONFIG['username'],
            password=EDARSAHUB_CONFIG['password'],
            login_timeout=15
        )
    
    def dispatch(self, evento: EventoCompras) -> bool:
        """
        Guarda el evento en la tabla de eventos pendientes.
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO Compras_Eventos_Pendientes (
                    EventoTipo, ServerID, UnidadNegocioID, Folio, Fecha,
                    DatosJSON, Procesado, CreatedAt
                ) VALUES (%s, %s, %s, %s, %s, %s, 0, %s)
            """, (
                evento.evento_tipo.value if isinstance(evento.evento_tipo, Enum) else evento.evento_tipo,
                evento.server_id,
                evento.unidad_negocio_id,
                str(evento.folio),
                evento.fecha,
                json.dumps(evento.to_dict(), default=str),
                datetime.now(ZoneInfo("America/Mexico_City")).replace(tzinfo=None)
            ))
            conn.commit()
            conn.close()
            
            logger.info(f"[EVENTO] Dispatched: {evento.evento_tipo} - Server={evento.server_name}, Folio={evento.folio}")
            return True
            
        except Exception as e:
            logger.error(f"[EVENTO] Error dispatching evento: {e}")
            return False
    
    def get_pending_events(self, limit: int = 100) -> List[Dict]:
        """Obtiene eventos pendientes de procesar."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor(as_dict=True)
            
            cursor.execute("""
                SELECT TOP %s
                    EventoID, EventoTipo, ServerID, UnidadNegocioID,
                    Folio, Fecha, DatosJSON, CreatedAt
                FROM Compras_Eventos_Pendientes
                WHERE Procesado = 0
                ORDER BY CreatedAt ASC
            """, (limit,))
            
            eventos = cursor.fetchall()
            conn.close()
            
            result = []
            for e in eventos:
                datos = {}
                if e.get('DatosJSON'):
                    try:
                        datos = json.loads(e['DatosJSON'])
                    except Exception:
                        pass
                result.append({
                    "evento_id": e['EventoID'],
                    "evento_tipo": e['EventoTipo'],
                    "server_id": e['ServerID'],
                    "unidad_negocio_id": e['UnidadNegocioID'],
                    "folio": e['Folio'],
                    "fecha": e['Fecha'],
                    "datos": datos,
                    "created_at": e['CreatedAt']
                })
            
            return result
            
        except Exception as e:
            logger.error(f"[EVENTO] Error obteniendo eventos pendientes: {e}")
            return []
    
    def mark_as_processed(self, evento_id: int, informe_id: str = None, error_msg: str = None) -> bool:
        """Marca un evento como procesado."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            now = datetime.now(ZoneInfo("America/Mexico_City")).replace(tzinfo=None)
            
            cursor.execute("""
                UPDATE Compras_Eventos_Pendientes
                SET Procesado = 1,
                    ProcesadoAt = %s,
                    InformeGenerado = %s,
                    InformeID = %s,
                    ErrorMessage = %s
                WHERE EventoID = %s
            """, (
                now,
                1 if informe_id else 0,
                informe_id,
                error_msg[:500] if error_msg else None,
                evento_id
            ))
            conn.commit()
            conn.close()
            
            logger.info(f"[EVENTO] Marcado como procesado: EventoID={evento_id}")
            return True
            
        except Exception as e:
            logger.error(f"[EVENTO] Error marcando evento como procesado: {e}")
            return False
    
    def register_handler(self, evento_tipo: EventoTipo, handler: Callable):
        """Registra un handler para un tipo de evento."""
        if evento_tipo not in self._handlers:
            self._handlers[evento_tipo] = []
        self._handlers[evento_tipo].append(handler)
    
    def process_pending_events(self) -> Dict[str, Any]:
        """Procesa todos los eventos pendientes ejecutando sus handlers."""
        eventos = self.get_pending_events()
        processed = 0
        errors = 0
        
        for evento in eventos:
            evento_tipo = evento.get('evento_tipo')
            handlers = self._handlers.get(EventoTipo(evento_tipo), [])
            
            if not handlers:
                # Sin handlers configurados, marcar como procesado sin informe
                self.mark_as_processed(evento['evento_id'])
                processed += 1
                continue
            
            try:
                for handler in handlers:
                    result = handler(evento)
                    if result and result.get('informe_id'):
                        self.mark_as_processed(evento['evento_id'], result['informe_id'])
                    else:
                        self.mark_as_processed(evento['evento_id'])
                processed += 1
            except Exception as e:
                errors += 1
                self.mark_as_processed(evento['evento_id'], error_msg=str(e)[:500])
                logger.error(f"[EVENTO] Error procesando evento {evento['evento_id']}: {e}")
        
        return {"processed": processed, "errors": errors, "total": len(eventos)}


# =============================================================================
# CHECKPOINT MANAGER (Detección de Nuevos Registros)
# =============================================================================

class CheckpointManager:
    """
    Gestiona los checkpoints para detección incremental de nuevos registros.
    """
    
    def __init__(self):
        pass
    
    def _get_connection(self):
        return pymssql.connect(
            server=EDARSAHUB_CONFIG['host'],
            port=EDARSAHUB_CONFIG['port'],
            database=EDARSAHUB_CONFIG['database'],
            user=EDARSAHUB_CONFIG['username'],
            password=EDARSAHUB_CONFIG['password'],
            login_timeout=15
        )
    
    def get_checkpoint(self, server_id: str, sync_type: SyncType) -> Dict:
        """Obtiene el último checkpoint para un servidor y tipo de sync."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor(as_dict=True)
            
            cursor.execute("""
                SELECT LastFolio, LastFecha, LastSyncAt, RecordsFoundLastSync
                FROM Compras_Sync_Checkpoint
                WHERE ServerID = %s AND SyncType = %s
            """, (server_id, sync_type.value))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return {
                    "last_folio": row['LastFolio'],
                    "last_fecha": row['LastFecha'],
                    "last_sync_at": row['LastSyncAt'],
                    "records_found": row['RecordsFoundLastSync']
                }
            return {
                "last_folio": None,
                "last_fecha": None,
                "last_sync_at": None,
                "records_found": 0
            }
            
        except Exception as e:
            logger.error(f"[CHECKPOINT] Error obteniendo checkpoint: {e}")
            return {"last_folio": None, "last_fecha": None, "last_sync_at": None, "records_found": 0}
    
    def update_checkpoint(
        self, 
        server_id: str, 
        server_name: str,
        sync_type: SyncType, 
        last_folio: str, 
        last_fecha: datetime,
        records_found: int
    ) -> bool:
        """Actualiza o crea el checkpoint para un servidor."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            now = datetime.now(ZoneInfo("America/Mexico_City")).replace(tzinfo=None)
            
            # Upsert usando MERGE
            cursor.execute("""
                MERGE Compras_Sync_Checkpoint AS target
                USING (SELECT %s AS ServerID, %s AS SyncType) AS source
                ON target.ServerID = source.ServerID AND target.SyncType = source.SyncType
                WHEN MATCHED THEN
                    UPDATE SET 
                        LastFolio = %s,
                        LastFecha = %s,
                        LastSyncAt = %s,
                        RecordsFoundLastSync = %s,
                        UpdatedAt = %s
                WHEN NOT MATCHED THEN
                    INSERT (ServerID, ServerName, SyncType, LastFolio, LastFecha, LastSyncAt, RecordsFoundLastSync, CreatedAt, UpdatedAt)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);
            """, (
                server_id, sync_type.value,  # Source
                last_folio, last_fecha, now, records_found, now,  # Update
                server_id, server_name, sync_type.value, last_folio, last_fecha, now, records_found, now, now  # Insert
            ))
            conn.commit()
            conn.close()
            
            logger.debug(f"[CHECKPOINT] Actualizado: {server_name}/{sync_type.value} -> Folio={last_folio}")
            return True
            
        except Exception as e:
            logger.error(f"[CHECKPOINT] Error actualizando checkpoint: {e}")
            return False
    
    def get_all_checkpoints(self) -> List[Dict]:
        """Obtiene todos los checkpoints activos."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor(as_dict=True)
            
            cursor.execute("""
                SELECT ServerID, ServerName, SyncType, LastFolio, LastFecha, 
                       LastSyncAt, RecordsFoundLastSync, UpdatedAt
                FROM Compras_Sync_Checkpoint
                ORDER BY ServerName, SyncType
            """)
            
            rows = cursor.fetchall()
            conn.close()
            return rows
            
        except Exception as e:
            logger.error(f"[CHECKPOINT] Error obteniendo checkpoints: {e}")
            return []


# =============================================================================
# DETECTOR DE NUEVOS REGISTROS
# =============================================================================

class NuevosRegistrosDetector:
    """
    Detecta nuevos registros comparando con checkpoints.
    Genera eventos cuando encuentra registros nuevos.
    """
    
    def __init__(self, dispatcher: EventDispatcher, checkpoint_mgr: CheckpointManager):
        self.dispatcher = dispatcher
        self.checkpoint_mgr = checkpoint_mgr
    
    def detectar_nuevos_inventarios(
        self,
        server_info: Dict,
        unidad_info: Dict,
        execute_query_func: Callable
    ) -> Dict[str, Any]:
        """
        Detecta inventarios nuevos desde el último checkpoint.
        
        Returns:
            Dict con nuevos_encontrados, eventos_generados, error
        """
        server_id = server_info.get('id', '')
        server_name = server_info.get('name', '')
        system_type = server_info.get('system_type', '').upper()
        
        # Obtener checkpoint actual
        checkpoint = self.checkpoint_mgr.get_checkpoint(server_id, SyncType.INVENTARIOS)
        last_folio = checkpoint.get('last_folio')
        
        try:
            # Construir query según tipo de sistema
            if 'MPRO' in system_type or 'MANAGEMENT' in system_type:
                if last_folio:
                    query = f"""
                        SELECT TOP 100 Fi_Folio as folio, Fi_Fecha as fecha,
                               Al_Cve_Almacen as almacen_id, Sc_Cve_Sucursal as sucursal_id
                        FROM Fisico
                        WHERE Fi_Folio > '{last_folio}'
                        ORDER BY Fi_Folio ASC
                    """
                else:
                    # Primera vez: obtener últimos 10 para establecer baseline
                    query = """
                        SELECT TOP 10 Fi_Folio as folio, Fi_Fecha as fecha,
                               Al_Cve_Almacen as almacen_id, Sc_Cve_Sucursal as sucursal_id
                        FROM Fisico
                        ORDER BY Fi_Folio DESC
                    """
            elif 'SOFTRESTAURANT' in system_type:
                if last_folio:
                    query = f"""
                        SELECT TOP 100 folio, fecha, idalmacen1 as almacen_id
                        FROM invfisico
                        WHERE folio > {last_folio}
                        ORDER BY folio ASC
                    """
                else:
                    query = """
                        SELECT TOP 10 folio, fecha, idalmacen1 as almacen_id
                        FROM invfisico
                        ORDER BY folio DESC
                    """
            else:
                return {"nuevos_encontrados": 0, "eventos_generados": 0, "error": f"Sistema no soportado: {system_type}"}
            
            # Ejecutar query
            result = execute_query_func(
                server_info['host'],
                server_info['port'],
                server_info['database'],
                server_info['username'],
                server_info['password'],
                query
            )
            
            if result is None:
                return {"nuevos_encontrados": 0, "eventos_generados": 0, "error": "Timeout o conexión fallida"}
            
            nuevos = len(result)
            eventos_generados = 0
            max_folio = last_folio
            max_fecha = None
            
            # Generar eventos para cada nuevo registro
            for row in result:
                folio = str(row.get('folio', ''))
                fecha = row.get('fecha')
                
                # Solo generar evento si es realmente nuevo (no en primera carga)
                if last_folio is not None:
                    evento = EventoCompras(
                        evento_tipo=EventoTipo.NUEVO_INVENTARIO,
                        server_id=server_id,
                        server_name=server_name,
                        unidad_negocio_id=unidad_info.get('id'),
                        unidad_codigo=unidad_info.get('codigo'),
                        folio=folio,
                        fecha=fecha,
                        datos={
                            "almacen_id": row.get('almacen_id'),
                            "sucursal_id": row.get('sucursal_id'),
                            "system_type": system_type
                        }
                    )
                    if self.dispatcher.dispatch(evento):
                        eventos_generados += 1
                
                # Actualizar max_folio
                if folio and (max_folio is None or folio > max_folio):
                    max_folio = folio
                    max_fecha = fecha
            
            # Actualizar checkpoint
            if max_folio:
                self.checkpoint_mgr.update_checkpoint(
                    server_id, server_name, SyncType.INVENTARIOS,
                    max_folio, max_fecha, nuevos
                )
            
            logger.info(f"[DETECTOR] Inventarios {server_name}: {nuevos} nuevos, {eventos_generados} eventos")
            return {"nuevos_encontrados": nuevos, "eventos_generados": eventos_generados, "error": None}
            
        except Exception as e:
            logger.error(f"[DETECTOR] Error detectando inventarios en {server_name}: {e}")
            return {"nuevos_encontrados": 0, "eventos_generados": 0, "error": str(e)[:200]}
    
    def detectar_nuevas_requisiciones(
        self,
        server_info: Dict,
        unidad_info: Dict,
        execute_query_func: Callable
    ) -> Dict[str, Any]:
        """
        Detecta requisiciones nuevas desde el último checkpoint.
        """
        server_id = server_info.get('id', '')
        server_name = server_info.get('name', '')
        system_type = server_info.get('system_type', '').upper()
        
        checkpoint = self.checkpoint_mgr.get_checkpoint(server_id, SyncType.REQUISICIONES)
        last_folio = checkpoint.get('last_folio')
        
        try:
            if 'MPRO' in system_type or 'MANAGEMENT' in system_type:
                if last_folio:
                    query = f"""
                        SELECT TOP 100 Oc_Folio as folio, Oc_Fecha as fecha,
                               Es_Cve_Estado as estado, Pv_Cve_Proveedor as proveedor_id
                        FROM Orden_Compra
                        WHERE Oc_Folio > '{last_folio}'
                        ORDER BY Oc_Folio ASC
                    """
                else:
                    query = """
                        SELECT TOP 10 Oc_Folio as folio, Oc_Fecha as fecha,
                               Es_Cve_Estado as estado, Pv_Cve_Proveedor as proveedor_id
                        FROM Orden_Compra
                        ORDER BY Oc_Folio DESC
                    """
            elif 'SOFTRESTAURANT' in system_type:
                if last_folio:
                    query = f"""
                        SELECT TOP 100 folio, fechacaptura as fecha,
                               aplicada as estado, idproveedor as proveedor_id
                        FROM ordenescompra
                        WHERE folio > {last_folio}
                        ORDER BY folio ASC
                    """
                else:
                    query = """
                        SELECT TOP 10 folio, fechacaptura as fecha,
                               aplicada as estado, idproveedor as proveedor_id
                        FROM ordenescompra
                        ORDER BY folio DESC
                    """
            else:
                return {"nuevos_encontrados": 0, "eventos_generados": 0, "error": f"Sistema no soportado: {system_type}"}
            
            result = execute_query_func(
                server_info['host'],
                server_info['port'],
                server_info['database'],
                server_info['username'],
                server_info['password'],
                query
            )
            
            if result is None:
                return {"nuevos_encontrados": 0, "eventos_generados": 0, "error": "Timeout o conexión fallida"}
            
            nuevos = len(result)
            eventos_generados = 0
            max_folio = last_folio
            max_fecha = None
            
            for row in result:
                folio = str(row.get('folio', ''))
                fecha = row.get('fecha')
                
                if last_folio is not None:
                    evento = EventoCompras(
                        evento_tipo=EventoTipo.NUEVA_REQUISICION,
                        server_id=server_id,
                        server_name=server_name,
                        unidad_negocio_id=unidad_info.get('id'),
                        unidad_codigo=unidad_info.get('codigo'),
                        folio=folio,
                        fecha=fecha,
                        datos={
                            "estado": row.get('estado'),
                            "proveedor_id": row.get('proveedor_id'),
                            "system_type": system_type
                        }
                    )
                    if self.dispatcher.dispatch(evento):
                        eventos_generados += 1
                
                if folio and (max_folio is None or folio > max_folio):
                    max_folio = folio
                    max_fecha = fecha
            
            if max_folio:
                self.checkpoint_mgr.update_checkpoint(
                    server_id, server_name, SyncType.REQUISICIONES,
                    max_folio, max_fecha, nuevos
                )
            
            logger.info(f"[DETECTOR] Requisiciones {server_name}: {nuevos} nuevos, {eventos_generados} eventos")
            return {"nuevos_encontrados": nuevos, "eventos_generados": eventos_generados, "error": None}
            
        except Exception as e:
            logger.error(f"[DETECTOR] Error detectando requisiciones en {server_name}: {e}")
            return {"nuevos_encontrados": 0, "eventos_generados": 0, "error": str(e)[:200]}


# =============================================================================
# SINGLETON INSTANCES
# =============================================================================

# Instancias globales (singleton pattern)
_event_dispatcher: Optional[PollingEventDispatcher] = None
_checkpoint_manager: Optional[CheckpointManager] = None
_detector: Optional[NuevosRegistrosDetector] = None


def get_event_dispatcher() -> PollingEventDispatcher:
    """Obtiene la instancia singleton del dispatcher."""
    global _event_dispatcher
    if _event_dispatcher is None:
        _event_dispatcher = PollingEventDispatcher()
    return _event_dispatcher


def get_checkpoint_manager() -> CheckpointManager:
    """Obtiene la instancia singleton del checkpoint manager."""
    global _checkpoint_manager
    if _checkpoint_manager is None:
        _checkpoint_manager = CheckpointManager()
    return _checkpoint_manager


def get_detector() -> NuevosRegistrosDetector:
    """Obtiene la instancia singleton del detector."""
    global _detector
    if _detector is None:
        _detector = NuevosRegistrosDetector(
            get_event_dispatcher(),
            get_checkpoint_manager()
        )
    return _detector


# =============================================================================
# PREPARACIÓN PARA SERVICE BROKER (FUTURO)
# =============================================================================

class ServiceBrokerEventDispatcher(EventDispatcher):
    """
    STUB: Implementación futura para SQL Server Service Broker.
    
    Service Broker permite mensajería asíncrona nativa en SQL Server.
    Cuando esté configurado:
    1. Los triggers en origen envían mensajes a una cola
    2. Este dispatcher escucha la cola y procesa mensajes
    3. Latencia de milisegundos en lugar de minutos
    
    Requisitos para migrar:
    - Habilitar Service Broker en servidores origen
    - Crear contratos y colas
    - Configurar rutas entre servidores
    - Permisos de SEND/RECEIVE
    """
    
    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        raise NotImplementedError(
            "ServiceBrokerEventDispatcher no implementado. "
            "Usar PollingEventDispatcher mientras tanto."
        )
    
    def dispatch(self, evento: EventoCompras) -> bool:
        # Enviar mensaje a cola Service Broker
        pass
    
    def get_pending_events(self, limit: int = 100) -> List[EventoCompras]:
        # RECEIVE de la cola Service Broker
        pass
    
    def mark_as_processed(self, evento_id: int, informe_id: str = None) -> bool:
        # END CONVERSATION en Service Broker
        pass
