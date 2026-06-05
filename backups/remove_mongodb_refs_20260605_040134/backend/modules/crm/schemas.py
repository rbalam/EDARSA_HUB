"""
EDARSA HUB - CRM Enterprise Schemas
===================================
Modelos Pydantic para validación de datos CRM nativos.
Estas estructuras mapean directamente a las tablas SQL de EDARSAHUB.
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
from uuid import UUID
from enum import Enum


# ============================================================================
# ENUMS
# ============================================================================

class EstatusLead(str, Enum):
    NUEVO = "NUEVO"
    CONTACTADO = "CONTACTADO"
    CALIFICADO = "CALIFICADO"
    DESCALIFICADO = "DESCALIFICADO"
    CONVERTIDO = "CONVERTIDO"


class EstatusOportunidad(str, Enum):
    ABIERTA = "ABIERTA"
    GANADA = "GANADA"
    PERDIDA = "PERDIDA"
    PAUSADA = "PAUSADA"
    CANCELADA = "CANCELADA"


class Prioridad(str, Enum):
    BAJA = "BAJA"
    MEDIA = "MEDIA"
    ALTA = "ALTA"
    CRITICA = "CRITICA"


# ============================================================================
# LEADS
# ============================================================================

class LeadBase(BaseModel):
    """Campos base para Lead"""
    nombre_contacto: str = Field(..., min_length=1, max_length=100)
    apellido_paterno: Optional[str] = Field(None, max_length=100)
    apellido_materno: Optional[str] = Field(None, max_length=100)
    nombre_empresa: Optional[str] = Field(None, max_length=200)
    puesto: Optional[str] = Field(None, max_length=100)
    email: Optional[str] = Field(None, max_length=150)
    telefono: Optional[str] = Field(None, max_length=50)
    telefono_movil: Optional[str] = Field(None, max_length=50)
    descripcion: Optional[str] = None
    presupuesto: Optional[float] = None
    fecha_estimada_cierre: Optional[datetime] = None


class LeadCreate(LeadBase):
    """Crear nuevo Lead"""
    empresa_id: UUID
    sucursal_id: Optional[UUID] = None
    origen_lead_id: Optional[int] = None
    prioridad_id: Optional[int] = None
    ejecutivo_asignado_user_id: Optional[UUID] = None


class LeadUpdate(BaseModel):
    """Actualizar Lead existente"""
    nombre_contacto: Optional[str] = Field(None, max_length=100)
    apellido_paterno: Optional[str] = Field(None, max_length=100)
    apellido_materno: Optional[str] = Field(None, max_length=100)
    nombre_empresa: Optional[str] = Field(None, max_length=200)
    puesto: Optional[str] = Field(None, max_length=100)
    email: Optional[str] = Field(None, max_length=150)
    telefono: Optional[str] = Field(None, max_length=50)
    telefono_movil: Optional[str] = Field(None, max_length=50)
    descripcion: Optional[str] = None
    presupuesto: Optional[float] = None
    fecha_estimada_cierre: Optional[datetime] = None
    origen_lead_id: Optional[int] = None
    estatus_lead_id: Optional[int] = None
    prioridad_id: Optional[int] = None
    ejecutivo_asignado_user_id: Optional[UUID] = None


class LeadResponse(LeadBase):
    """Respuesta de Lead"""
    lead_id: UUID
    empresa_id: UUID
    sucursal_id: Optional[UUID] = None
    folio_lead: Optional[str] = None
    origen_lead_id: Optional[int] = None
    estatus_lead_id: int
    prioridad_id: Optional[int] = None
    calificacion_lead_id: Optional[int] = None
    ejecutivo_asignado_user_id: Optional[UUID] = None
    fecha_asignacion: Optional[datetime] = None
    convertido_a_cuenta: bool = False
    descalificado: bool = False
    activo: bool = True
    created_at: datetime
    updated_at: datetime
    
    # Campos expandidos (joins)
    origen_nombre: Optional[str] = None
    estatus_nombre: Optional[str] = None
    estatus_color: Optional[str] = None
    prioridad_nombre: Optional[str] = None
    ejecutivo_nombre: Optional[str] = None
    
    class Config:
        from_attributes = True


class LeadConvertir(BaseModel):
    """Datos para convertir Lead a Cuenta/Oportunidad"""
    crear_cuenta: bool = True
    crear_contacto: bool = True
    crear_oportunidad: bool = False
    nombre_oportunidad: Optional[str] = None
    monto_estimado: Optional[float] = None
    pipeline_id: Optional[int] = None


class LeadDescalificar(BaseModel):
    """Datos para descalificar un Lead"""
    motivo_descalificacion_id: int
    notas: Optional[str] = Field(None, max_length=500)


# ============================================================================
# OPORTUNIDADES
# ============================================================================

class OportunidadBase(BaseModel):
    """Campos base para Oportunidad"""
    nombre_oportunidad: str = Field(..., min_length=1, max_length=200)
    descripcion_oportunidad: Optional[str] = None
    monto_estimado: Optional[float] = None
    moneda_id: int = 1
    fecha_estimada_cierre: Optional[datetime] = None
    observaciones_internas: Optional[str] = None


class OportunidadCreate(OportunidadBase):
    """Crear nueva Oportunidad"""
    empresa_id: UUID
    sucursal_id: Optional[UUID] = None
    cuenta_id: Optional[UUID] = None
    contacto_principal_id: Optional[UUID] = None
    lead_origen_id: Optional[UUID] = None
    pipeline_id: int = 1
    etapa_actual_id: int = 1
    ejecutivo_responsable_user_id: Optional[UUID] = None
    preventa_responsable_user_id: Optional[UUID] = None


class OportunidadUpdate(BaseModel):
    """Actualizar Oportunidad existente"""
    nombre_oportunidad: Optional[str] = Field(None, max_length=200)
    descripcion_oportunidad: Optional[str] = None
    monto_estimado: Optional[float] = None
    moneda_id: Optional[int] = None
    fecha_estimada_cierre: Optional[datetime] = None
    cuenta_id: Optional[UUID] = None
    contacto_principal_id: Optional[UUID] = None
    ejecutivo_responsable_user_id: Optional[UUID] = None
    preventa_responsable_user_id: Optional[UUID] = None
    observaciones_internas: Optional[str] = None


class OportunidadCambiarEtapa(BaseModel):
    """Cambiar etapa de una oportunidad"""
    etapa_nueva_id: int
    comentario: Optional[str] = Field(None, max_length=500)
    monto_nuevo: Optional[float] = None


class OportunidadCerrar(BaseModel):
    """Cerrar oportunidad (ganada o perdida)"""
    es_ganada: bool
    motivo_id: Optional[int] = None
    razon_texto: Optional[str] = Field(None, max_length=500)
    monto_final: Optional[float] = None
    fecha_real_cierre: Optional[datetime] = None


class OportunidadResponse(OportunidadBase):
    """Respuesta de Oportunidad"""
    oportunidad_id: UUID
    empresa_id: UUID
    sucursal_id: Optional[UUID] = None
    folio_oportunidad: Optional[str] = None
    cuenta_id: Optional[UUID] = None
    contacto_principal_id: Optional[UUID] = None
    lead_origen_id: Optional[UUID] = None
    pipeline_id: int
    etapa_actual_id: int
    probabilidad_actual: int
    dias_en_etapa_actual: int = 0
    fecha_apertura: datetime
    fecha_ultima_actividad: Optional[datetime] = None
    fecha_proxima_actividad: Optional[datetime] = None
    ejecutivo_responsable_user_id: Optional[UUID] = None
    estatus_oportunidad_id: int
    activo: bool = True
    created_at: datetime
    updated_at: datetime
    
    # Campos expandidos (joins)
    cuenta_nombre: Optional[str] = None
    contacto_nombre: Optional[str] = None
    pipeline_nombre: Optional[str] = None
    etapa_nombre: Optional[str] = None
    etapa_color: Optional[str] = None
    estatus_nombre: Optional[str] = None
    estatus_color: Optional[str] = None
    ejecutivo_nombre: Optional[str] = None
    
    class Config:
        from_attributes = True


# ============================================================================
# PIPELINE Y ETAPAS
# ============================================================================

class EtapaResponse(BaseModel):
    """Etapa del pipeline"""
    etapa_id: int
    pipeline_id: int
    codigo: str
    nombre: str
    descripcion: Optional[str] = None
    probabilidad_default: int
    orden: int
    color_hex: str
    es_etapa_inicial: bool
    es_etapa_cierre: bool
    es_cierre_ganado: bool
    es_cierre_perdido: bool
    dias_max_sla: Optional[int] = None
    activo: bool


class PipelineResponse(BaseModel):
    """Pipeline completo con etapas"""
    pipeline_id: int
    empresa_id: Optional[UUID] = None
    codigo: str
    nombre: str
    descripcion: Optional[str] = None
    tipo_pipeline_id: int
    es_default: bool
    activo: bool
    etapas: List[EtapaResponse] = []


class PipelineKanban(BaseModel):
    """Vista Kanban del pipeline con oportunidades por etapa"""
    pipeline: PipelineResponse
    columnas: List[dict]  # [{etapa: EtapaResponse, oportunidades: [...], total_monto: float}]
    totales: dict  # {total_oportunidades: int, total_monto: float, monto_ponderado: float}


# ============================================================================
# CATÁLOGOS
# ============================================================================

class CatalogoItem(BaseModel):
    """Item genérico de catálogo"""
    id: int
    codigo: str
    nombre: str
    descripcion: Optional[str] = None
    orden: int
    color_hex: Optional[str] = None
    activo: bool = True


# ============================================================================
# DASHBOARD / KPIs
# ============================================================================

class CRMDashboardResponse(BaseModel):
    """Resumen del dashboard CRM"""
    leads: dict  # {total, nuevos_mes, por_estatus: [...]}
    oportunidades: dict  # {total, abiertas, monto_pipeline, por_etapa: [...]}
    conversion: dict  # {leads_convertidos, tasa_conversion, tiempo_promedio_conversion}
    actividad_reciente: List[dict]
    pipeline_forecast: dict  # {monto_ponderado, monto_best_case, monto_commit}


# ============================================================================
# LISTADOS CON PAGINACIÓN
# ============================================================================

class PaginatedResponse(BaseModel):
    """Respuesta paginada genérica"""
    items: List
    total: int
    page: int
    page_size: int
    total_pages: int


class LeadListResponse(PaginatedResponse):
    """Lista paginada de Leads"""
    items: List[LeadResponse]


class OportunidadListResponse(PaginatedResponse):
    """Lista paginada de Oportunidades"""
    items: List[OportunidadResponse]
