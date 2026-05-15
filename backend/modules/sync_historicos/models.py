"""
EDARSA HUB - Sync Históricos: Modelos de Datos
===============================================
FASE SYNC-1: Modelos para tablas Sync_* en EDARSAHUB.

VENTANA OPERATIVA: 13:00 - 11:00 (cruza medianoche)
- Campos de control preparados para futuro módulo de Horarios de Operación

CAMPOS DE CONTROL OBLIGATORIOS:
- server_id, empresa_id, sucursal_id
- system_type
- fecha_operacion
- ventana_inicio, ventana_fin, cruza_medianoche
- ventana_inicio_hora_config, ventana_fin_hora_config
- sync_run_id
- source_status, source_type
- synced_at_mexico
- row_hash
- created_at, updated_at
"""

from dataclasses import dataclass, field
from datetime import date, datetime, time
from typing import Optional, List, Dict, Any
from decimal import Decimal
from enum import Enum
import hashlib
import json


class SourceStatus(Enum):
    """Estado de la fuente de datos."""
    SUCCESS = "SUCCESS"
    ERROR = "ERROR"
    SOURCE_FAILED = "SOURCE_FAILED"
    NO_DATA = "NO_DATA"
    TIMEOUT = "TIMEOUT"
    AUTH_FAILED = "AUTH_FAILED"


class SourceType(Enum):
    """Tipo de fuente de datos."""
    SOFTRESTAURANT = "SOFTRESTAURANT"
    MPRO = "MPRO"


@dataclass
class SyncVentaHistorica:
    """
    Modelo para Sync_Ventas_Historicas.
    Representa ventas diarias consolidadas por unidad.
    """
    # Identificadores
    server_id: str
    empresa_id: int
    sucursal_id: Optional[str]
    unidad_negocio_id: Optional[str]
    system_type: str
    
    # Fecha operativa (NO calendario)
    fecha_operacion: date
    
    # Ventana operativa
    ventana_inicio: time
    ventana_fin: time
    cruza_medianoche: bool
    ventana_inicio_hora_config: int  # 13
    ventana_fin_hora_config: int     # 11
    
    # Métricas de ventas
    venta_total: Decimal
    venta_efectivo: Decimal
    venta_tarjeta: Decimal
    venta_otros: Decimal
    num_tickets: int
    ticket_promedio: Decimal
    
    # Control de sincronización
    sync_run_id: str
    source_status: str  # SUCCESS, ERROR, SOURCE_FAILED, NO_DATA
    source_type: str    # SOFTRESTAURANT, MPRO
    synced_at_mexico: datetime
    
    # Integridad
    row_hash: str
    
    # Auditoría
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def compute_hash(self) -> str:
        """Calcula hash de la fila para UPSERT idempotente."""
        data = {
            'server_id': self.server_id,
            'empresa_id': self.empresa_id,
            'fecha_operacion': str(self.fecha_operacion),
            'venta_total': str(self.venta_total),
            'venta_efectivo': str(self.venta_efectivo),
            'venta_tarjeta': str(self.venta_tarjeta),
            'venta_otros': str(self.venta_otros),
            'num_tickets': self.num_tickets,
        }
        return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()[:32]


@dataclass
class SyncVentaPorHora:
    """
    Modelo para Sync_Ventas_PorHora.
    Distribución de ventas por hora del día.
    """
    # Identificadores
    server_id: str
    empresa_id: int
    sucursal_id: Optional[str]
    unidad_negocio_id: Optional[str]
    system_type: str
    
    # Fecha y hora operativa
    fecha_operacion: date
    hora: int  # 0-23
    
    # Ventana operativa
    ventana_inicio: time
    ventana_fin: time
    cruza_medianoche: bool
    ventana_inicio_hora_config: int
    ventana_fin_hora_config: int
    
    # Métricas
    venta_hora: Decimal
    num_tickets_hora: int
    
    # Control de sincronización
    sync_run_id: str
    source_status: str
    source_type: str
    synced_at_mexico: datetime
    
    # Integridad
    row_hash: str
    
    # Auditoría
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def compute_hash(self) -> str:
        """Calcula hash de la fila."""
        data = {
            'server_id': self.server_id,
            'empresa_id': self.empresa_id,
            'fecha_operacion': str(self.fecha_operacion),
            'hora': self.hora,
            'venta_hora': str(self.venta_hora),
            'num_tickets_hora': self.num_tickets_hora,
        }
        return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()[:32]


@dataclass
class SyncVentaPorDiaSemana:
    """
    Modelo para Sync_Ventas_PorDiaSemana.
    Análisis de ventas por día de la semana.
    """
    # Identificadores
    server_id: str
    empresa_id: int
    sucursal_id: Optional[str]
    unidad_negocio_id: Optional[str]
    system_type: str
    
    # Período y día
    fecha_inicio_periodo: date
    fecha_fin_periodo: date
    dia_semana: int  # 0=Lunes, 6=Domingo
    dia_semana_nombre: str  # "Lunes", "Martes", etc.
    
    # Ventana operativa
    ventana_inicio_hora_config: int
    ventana_fin_hora_config: int
    
    # Métricas agregadas
    venta_promedio: Decimal
    venta_min: Decimal
    venta_max: Decimal
    num_dias_con_datos: int
    
    # Control de sincronización
    sync_run_id: str
    source_status: str
    source_type: str
    synced_at_mexico: datetime
    
    # Integridad
    row_hash: str
    
    # Auditoría
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class SyncControlEjecucion:
    """
    Modelo para Sync_Control_Ejecuciones.
    Bitácora de ejecuciones de sincronización.
    """
    # Identificación del run
    sync_run_id: str
    sync_type: str  # VENTAS_HISTORICAS, VENTAS_POR_HORA, VENTAS_POR_DIA_SEMANA
    
    # Scope
    server_id: Optional[str]  # None si es todos
    empresa_id: Optional[int]
    
    # Rango procesado
    fecha_inicio: date
    fecha_fin: date
    
    # Ventana operativa usada
    ventana_inicio_hora_config: int
    ventana_fin_hora_config: int
    
    # Modo
    is_dry_run: bool
    
    # Resultados
    registros_procesados: int
    registros_insertados: int
    registros_actualizados: int
    registros_error: int
    
    # Estado
    status: str  # RUNNING, SUCCESS, PARTIAL, FAILED
    error_message: Optional[str]
    
    # Timestamps
    started_at_mexico: datetime
    finished_at_mexico: Optional[datetime]
    duration_seconds: Optional[int]
    
    # Auditoría
    created_at: Optional[datetime] = None


@dataclass
class SyncRunConfig:
    """Configuración para una ejecución de sincronización."""
    # Scope
    server_ids: Optional[List[str]] = None  # None = todos
    empresa_ids: Optional[List[int]] = None
    
    # Rango de fechas
    fecha_inicio: Optional[date] = None
    fecha_fin: Optional[date] = None
    dias_atras: int = 7  # Default últimos 7 días
    
    # Ventana operativa (preparación para módulo futuro)
    ventana_inicio_hora: int = 13
    ventana_fin_hora: int = 11
    
    # Modo
    dry_run: bool = True  # Obligatorio empezar en dry-run
    
    # Límites
    max_registros_por_servidor: int = 10000


@dataclass
class SyncRunResult:
    """Resultado de una ejecución de sincronización."""
    sync_run_id: str
    sync_type: str
    
    # Resultados globales
    total_servidores: int
    servidores_exitosos: int
    servidores_con_error: int
    
    total_registros_procesados: int
    total_registros_insertados: int
    total_registros_actualizados: int
    total_registros_error: int
    
    # Detalle por servidor
    resultados_por_servidor: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    
    # Estado
    success: bool = False
    is_dry_run: bool = True
    error_message: Optional[str] = None
    
    # Timestamps
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    duration_seconds: int = 0
