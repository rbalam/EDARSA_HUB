from core.unidades_service import UnidadesService
from core.corporate_filters.service import CorporateFilterService
"""
SCHEMAS - Comercial V2
======================

Modelos Pydantic para el módulo de sincronización comercial v2.
Define la estructura de datos para KPIs, ventas y logs.
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date, datetime
from decimal import Decimal
from enum import Enum


class SistemaOrigen(str, Enum):
    """Tipos de sistema de origen soportados"""
    SOFTRESTAURANT = "SOFTRESTAURANT"
    MPRO = "MPRO"


class FuenteOriginal(str, Enum):
    """Tipos de fuente de datos"""
    SQL_LIVE = "SQL_LIVE"
    HISTORICAL_LOAD = "HISTORICAL_LOAD"
    API_LOCAL = "API_LOCAL"
    TEMPCHEQUES = "TEMPCHEQUES"
    CHEQUES = "CHEQUES"  # Tabla definitiva de SoftRestaurant (turno cerrado)
    MIXTA = "MIXTA"


class SyncRunType(str, Enum):
    """Tipos de ejecución de sincronización"""
    INCREMENTAL = "INCREMENTAL"
    HISTORICAL = "HISTORICAL"
    VENTAS_DIA = "VENTAS_DIA"
    MANUAL = "MANUAL"


class SyncStatus(str, Enum):
    """Estados posibles de una sincronización"""
    SUCCESS = "SUCCESS"
    PARTIAL = "PARTIAL"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"


class ConnectionStatus(str, Enum):
    """Estados de conexión al origen"""
    ONLINE = "ONLINE"
    OFFLINE = "OFFLINE"
    TIMEOUT = "TIMEOUT"


# =============================================================================
# SCHEMAS DE ENTRADA (desde orígenes)
# =============================================================================

class KPIsDiariosInput(BaseModel):
    """Datos de KPIs diarios desde el origen (SoftRestaurant/MPRO)"""
    
    # Identificadores
    server_id: str
    sucursal_id: str = "DEFAULT"
    fecha: date
    
    # KPIs
    ventas_total: Decimal = Decimal("0")
    ventas_sin_propina: Decimal = Decimal("0")
    propinas_total: Decimal = Decimal("0")
    tickets_total: int = 0
    pax_total: int = 0
    
    # Opcional: desglose
    ventas_cerradas: Decimal = Decimal("0")
    ventas_abiertas: Decimal = Decimal("0")
    
    # Metadata
    es_corte_cerrado: bool = True
    fuente: FuenteOriginal = FuenteOriginal.SQL_LIVE


class VentasDiaAbiertasInput(BaseModel):
    """Snapshot de ventas abiertas (sin corte) del día actual"""
    
    server_id: str
    sucursal_id: str = "DEFAULT"
    fecha: date
    snapshot_timestamp: datetime
    
    ventas_abiertas: Decimal = Decimal("0")
    tickets_abiertos: int = 0
    pax_abiertos: int = 0
    
    fuente: FuenteOriginal = FuenteOriginal.TEMPCHEQUES


# =============================================================================
# SCHEMAS DE SALIDA (hacia EDARSAHUB)
# =============================================================================

class KPIsDiariosV2(BaseModel):
    """Registro completo para vw_Comercial_KPIs_Diarios_v2_Runtime"""
    
    # Identificadores de unidad
    unidad_negocio_pk: str
    unidad_negocio_nombre: str
    server_id: str
    sucursal_id: str = "DEFAULT"
    sucursal_nombre: Optional[str] = None
    sistema_origen: SistemaOrigen
    
    # Período
    fecha_operacion: date
    anio: int
    mes: int
    dia: int
    
    # KPIs principales
    ventas_total: Decimal = Decimal("0")
    ventas_sin_propina: Decimal = Decimal("0")
    propinas_total: Decimal = Decimal("0")
    tickets_total: int = 0
    pax_total: int = 0
    ticket_promedio: Decimal = Decimal("0")
    pax_promedio: Decimal = Decimal("0")
    
    # Desglose ventas
    ventas_cerradas: Decimal = Decimal("0")
    ventas_abiertas: Decimal = Decimal("0")
    total_estimado_dia: Decimal = Decimal("0")
    
    # Flags de estado
    es_venta_abierta: bool = False
    es_corte_cerrado: bool = True
    es_demo: bool = False
    activo: bool = True
    
    # Trazabilidad
    fuente_original: FuenteOriginal
    id_origen: Optional[str] = None
    hash_origen: Optional[str] = None
    
    # Metadata de sync
    sync_run_id: Optional[str] = None

    class Config:
        use_enum_values = True


class VentasDiaAbiertasV2(BaseModel):
    """Registro para Comercial_Ventas_Dia_Abiertas_v2"""
    
    unidad_negocio_pk: str
    unidad_negocio_nombre: str
    server_id: str
    sucursal_id: str = "DEFAULT"
    sucursal_nombre: Optional[str] = None
    sistema_origen: SistemaOrigen
    
    snapshot_timestamp: datetime
    fecha_operacion: date
    
    ventas_abiertas: Decimal = Decimal("0")
    tickets_abiertos: int = 0
    pax_abiertos: int = 0
    
    ventas_cerradas_dia: Decimal = Decimal("0")
    tickets_cerrados_dia: int = 0
    pax_cerrados_dia: int = 0
    
    total_estimado_dia: Decimal = Decimal("0")
    
    fuente_original: FuenteOriginal
    sync_run_id: Optional[str] = None
    
    # Campo para diagnóstico técnico (no visual principal)
    source_status: Optional[str] = "SYNC_OK"

    class Config:
        use_enum_values = True


class SyncLogV2(BaseModel):
    """Registro para Comercial_SyncLog_v2"""
    
    run_id: str
    run_type: SyncRunType
    
    unidad_negocio_pk: Optional[str] = None
    server_id: Optional[str] = None
    sucursal_id: Optional[str] = None
    fecha_inicio: Optional[date] = None
    fecha_fin: Optional[date] = None
    
    status: SyncStatus
    records_processed: int = 0
    records_inserted: int = 0
    records_updated: int = 0
    records_skipped: int = 0
    records_errored: int = 0
    
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    
    duration_seconds: Optional[int] = None
    source_connection_status: Optional[ConnectionStatus] = None

    class Config:
        use_enum_values = True


# =============================================================================
# SCHEMAS DE CONFIGURACIÓN
# =============================================================================

class UnidadNegocioConfig(BaseModel):
    """Configuración de una unidad de negocio para sync"""
    
    unidad_negocio_pk: str
    unidad_negocio_nombre: str
    server_id: str
    sucursal_id: str = "DEFAULT"
    sucursal_nombre: Optional[str] = None
    sistema_origen: SistemaOrigen
    activo: bool = True


class SyncResult(BaseModel):
    """Resultado de una operación de sincronización"""
    
    success: bool
    run_id: str
    unidad_negocio_pk: str
    records_processed: int = 0
    records_inserted: int = 0
    records_updated: int = 0
    records_skipped: int = 0
    records_errored: int = 0
    error_message: Optional[str] = None
    duration_seconds: int = 0
