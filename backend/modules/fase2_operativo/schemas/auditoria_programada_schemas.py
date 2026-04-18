"""
Schemas para Auditorías Programadas
EDARSA HUB - Módulo Auditorías Programadas

Colecciones:
- auditorias_programadas: Configuración de programaciones
- auditorias_programadas_log: Bitácora de ejecuciones
"""
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from enum import Enum
from pydantic import BaseModel, Field
import uuid


class FrecuenciaAuditoria(str, Enum):
    """Frecuencia de ejecución de auditoría."""
    DIARIA = "DIARIA"
    SEMANAL = "SEMANAL"
    QUINCENAL = "QUINCENAL"
    MENSUAL = "MENSUAL"
    MANUAL = "MANUAL"  # Solo ejecución manual


class TipoAuditoria(str, Enum):
    """Tipo de auditoría a ejecutar."""
    INVENTARIO_COMPLETO = "INVENTARIO_COMPLETO"
    INVENTARIO_SELECTIVO = "INVENTARIO_SELECTIVO"
    CONTEO_CICLICO = "CONTEO_CICLICO"
    AUDITORIA_SORPRESA = "AUDITORIA_SORPRESA"


class EstadoEjecucion(str, Enum):
    """Estado de una ejecución de auditoría programada."""
    PENDIENTE = "PENDIENTE"
    EN_PROGRESO = "EN_PROGRESO"
    COMPLETADA = "COMPLETADA"
    FALLIDA = "FALLIDA"
    OMITIDA = "OMITIDA"


# =============================================================================
# AUDITORÍA PROGRAMADA
# =============================================================================

class AuditoriaProgramada(BaseModel):
    """Modelo de auditoría programada."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    
    # Identificación
    nombre: str = Field(..., min_length=3, max_length=100)
    descripcion: Optional[str] = None
    
    # Sucursal/Alcance
    sucursal_id: str
    sucursal_nombre: str
    almacenes: List[str] = Field(default=[], description="IDs de almacenes específicos, vacío = todos")
    
    # Tipo y frecuencia
    tipo_auditoria: TipoAuditoria
    frecuencia: FrecuenciaAuditoria
    
    # Programación temporal
    dia_semana: Optional[int] = Field(None, ge=0, le=6, description="0=Lunes, 6=Domingo")
    dia_mes: Optional[int] = Field(None, ge=1, le=31)
    hora_ejecucion: str = Field(default="08:00", pattern=r"^\d{2}:\d{2}$")
    timezone: str = Field(default="America/Mexico_City")
    
    # Estado
    activo: bool = True
    ultima_ejecucion: Optional[datetime] = None
    ultima_ejecucion_status: Optional[EstadoEjecucion] = None
    proxima_ejecucion: Optional[datetime] = None
    
    # Responsable
    usuario_responsable_id: Optional[str] = None
    rol_responsable: Optional[str] = None
    
    # Metadata
    observaciones: Optional[str] = None
    created_by: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    class Config:
        extra = "allow"


class AuditoriaProgramadaCreate(BaseModel):
    """Request para crear auditoría programada."""
    nombre: str = Field(..., min_length=3, max_length=100)
    descripcion: Optional[str] = None
    sucursal_id: str
    sucursal_nombre: str
    almacenes: List[str] = []
    tipo_auditoria: TipoAuditoria
    frecuencia: FrecuenciaAuditoria
    dia_semana: Optional[int] = Field(None, ge=0, le=6)
    dia_mes: Optional[int] = Field(None, ge=1, le=31)
    hora_ejecucion: str = "08:00"
    timezone: str = "America/Mexico_City"
    usuario_responsable_id: Optional[str] = None
    rol_responsable: Optional[str] = None
    observaciones: Optional[str] = None
    created_by: str


class AuditoriaProgramadaUpdate(BaseModel):
    """Request para actualizar auditoría programada."""
    nombre: Optional[str] = Field(None, min_length=3, max_length=100)
    descripcion: Optional[str] = None
    almacenes: Optional[List[str]] = None
    tipo_auditoria: Optional[TipoAuditoria] = None
    frecuencia: Optional[FrecuenciaAuditoria] = None
    dia_semana: Optional[int] = Field(None, ge=0, le=6)
    dia_mes: Optional[int] = Field(None, ge=1, le=31)
    hora_ejecucion: Optional[str] = None
    timezone: Optional[str] = None
    usuario_responsable_id: Optional[str] = None
    rol_responsable: Optional[str] = None
    observaciones: Optional[str] = None


class AuditoriaProgramadaResponse(BaseModel):
    """Response de auditoría programada."""
    id: str
    nombre: str
    descripcion: Optional[str]
    sucursal_id: str
    sucursal_nombre: str
    almacenes: List[str]
    tipo_auditoria: str
    frecuencia: str
    dia_semana: Optional[int]
    dia_mes: Optional[int]
    hora_ejecucion: str
    timezone: str
    activo: bool
    ultima_ejecucion: Optional[str]
    ultima_ejecucion_status: Optional[str]
    proxima_ejecucion: Optional[str]
    usuario_responsable_id: Optional[str]
    rol_responsable: Optional[str]
    observaciones: Optional[str]
    created_by: str
    created_at: str
    updated_at: str


# =============================================================================
# LOG DE EJECUCIONES
# =============================================================================

class AuditoriaProgramadaLog(BaseModel):
    """Registro de ejecución de auditoría programada."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    
    # Referencias
    auditoria_programada_id: str
    workflow_id: Optional[str] = None  # Si se creó workflow
    
    # Ejecución
    fecha_programada: datetime
    fecha_ejecucion: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    estado: EstadoEjecucion
    
    # Detalles
    disparado_por: str  # "SCHEDULER" | "MANUAL" | user_id
    mensaje: Optional[str] = None
    error_detalle: Optional[str] = None
    
    # Métricas
    duracion_ms: Optional[int] = None
    items_procesados: int = 0
    
    class Config:
        extra = "allow"


class AuditoriaProgramadaLogResponse(BaseModel):
    """Response de log de ejecución."""
    id: str
    auditoria_programada_id: str
    workflow_id: Optional[str]
    fecha_programada: str
    fecha_ejecucion: str
    estado: str
    disparado_por: str
    mensaje: Optional[str]
    error_detalle: Optional[str]
    duracion_ms: Optional[int]
    items_procesados: int


# =============================================================================
# RESPONSES AGREGADOS
# =============================================================================

class AuditoriasProgramadasListResponse(BaseModel):
    """Lista de auditorías programadas."""
    items: List[AuditoriaProgramadaResponse]
    total: int
    activas: int
    inactivas: int


class AuditoriasKPIsResponse(BaseModel):
    """KPIs de auditorías."""
    total_programadas: int
    activas: int
    inactivas: int
    pendientes_hoy: int
    en_curso: int
    completadas_mes: int
    fallidas_mes: int
    tasa_cumplimiento: float  # % ejecutadas vs programadas
    proximas_24h: List[Dict[str, Any]]


class CalendarioAuditoriasResponse(BaseModel):
    """Vista calendario de auditorías."""
    eventos: List[Dict[str, Any]]  # {fecha, auditorias: [...]}
    mes: int
    anio: int
