"""
Schemas Pydantic para Responsabilidad Económica
CAB-003 | EDARSA HUB - Fase 2C.1 y 2C.2

Define los modelos de datos para el cálculo de impacto económico
de diferencias de inventario y flujo de aprobaciones.
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime
from enum import Enum


class EstadoResponsabilidad(str, Enum):
    """Estados del registro de responsabilidad económica."""
    # Fase 2C.1
    CALCULADO = "CALCULADO"
    # Fase 2C.2
    PROPUESTO = "PROPUESTO"
    EN_DISPUTA = "EN_DISPUTA"
    APROBADO = "APROBADO"
    RECHAZADO = "RECHAZADO"
    EXONERADO = "EXONERADO"
    # Fase 2C.3 (NO implementar todavía)
    # APLICADO = "APLICADO"


class AccionResponsabilidad(str, Enum):
    """Acciones posibles sobre un registro de responsabilidad."""
    CALCULAR = "CALCULAR"
    PROPONER = "PROPONER"
    APROBAR = "APROBAR"
    RECHAZAR = "RECHAZAR"
    EXONERAR = "EXONERAR"
    DISPUTAR = "DISPUTAR"
    RESOLVER_DISPUTA = "RESOLVER_DISPUTA"


class RolAutorizacion(str, Enum):
    """Roles funcionales para autorización (sin RBAC completo)."""
    AFECTADO = "AFECTADO"
    SUPERVISOR = "SUPERVISOR"
    GERENTE_OPS = "GERENTE_OPS"
    DIRECCION = "DIRECCION"


class ToleranciaAplicada(BaseModel):
    """Detalle de tolerancia aplicada en el cálculo."""
    tolerancia_unidades: int = Field(default=0, description="Tolerancia absoluta en unidades")
    tolerancia_porcentaje: float = Field(default=0.0, description="Tolerancia relativa (%)")
    diferencias_dentro_tolerancia: int = Field(default=0, description="Diferencias dentro de tolerancia")
    diferencias_fuera_tolerancia: int = Field(default=0, description="Diferencias fuera de tolerancia")
    valor_excluido_por_tolerancia_mxn: float = Field(default=0.0, description="Valor monetario excluido por tolerancia")


class ResumenFaltantes(BaseModel):
    """Resumen de faltantes calculados."""
    unidades: int = Field(default=0, description="Total unidades faltantes")
    valor_mxn: float = Field(default=0.0, description="Valor monetario de faltantes")
    cantidad_items: int = Field(default=0, description="Número de items con faltantes")


class ResumenSobrantes(BaseModel):
    """Resumen de sobrantes calculados (solo registro, no compensan)."""
    unidades: int = Field(default=0, description="Total unidades sobrantes")
    valor_mxn: float = Field(default=0.0, description="Valor monetario de sobrantes")
    cantidad_items: int = Field(default=0, description="Número de items con sobrantes")


class ResponsabilidadBase(BaseModel):
    """Campos base de responsabilidad económica."""
    workflow_id: str = Field(..., description="FK al workflow operativo")
    tarea_id: Optional[str] = Field(None, description="FK a la tarea que generó el cálculo")
    procesado_id: str = Field(..., description="FK al folio procesado original")
    sucursal_id: str = Field(..., description="ID de la sucursal")


class ResponsabilidadCreate(BaseModel):
    """Schema para crear un cálculo de responsabilidad."""
    workflow_id: str = Field(..., description="ID del workflow a calcular")


class ResponsabilidadInDB(ResponsabilidadBase):
    """Schema de responsabilidad como está almacenada en BD."""
    id: str = Field(..., description="ID único del registro")
    
    # Totales de diferencias
    total_diferencias: int = Field(default=0, description="Total de diferencias evaluadas")
    
    # Faltantes
    faltantes_unidades: int = Field(default=0)
    faltantes_valor_mxn: float = Field(default=0.0)
    faltantes_cantidad_items: int = Field(default=0)
    
    # Sobrantes (solo registro, NO compensan)
    sobrantes_unidades: int = Field(default=0)
    sobrantes_valor_mxn: float = Field(default=0.0)
    sobrantes_cantidad_items: int = Field(default=0)
    
    # Tolerancia aplicada
    tolerancia_aplicada_unidades: int = Field(default=0)
    tolerancia_aplicada_porcentaje: float = Field(default=0.0)
    diferencias_dentro_tolerancia: int = Field(default=0)
    diferencias_fuera_tolerancia: int = Field(default=0)
    valor_excluido_por_tolerancia_mxn: float = Field(default=0.0)
    
    # Monto propuesto (solo sobre faltantes fuera de tolerancia)
    monto_propuesto_mxn: float = Field(default=0.0, description="Monto a proponer como cargo")
    excede_minimo: bool = Field(default=False, description="¿Excede CARGO_MINIMO_MXN?")
    cargo_minimo_configurado_mxn: float = Field(default=0.0, description="Valor del cargo mínimo al momento del cálculo")
    
    # Estado (2C.1 solo CALCULADO)
    estado: EstadoResponsabilidad = Field(default=EstadoResponsabilidad.CALCULADO)
    
    # Auditoría
    fecha_calculo: datetime
    calculado_por: str = Field(..., description="Usuario que ejecutó el cálculo")
    
    # Metadatos
    fecha_creacion: datetime
    fecha_actualizacion: datetime

    class Config:
        from_attributes = True


class ResponsabilidadResponse(BaseModel):
    """Schema de respuesta para responsabilidad económica."""
    id: str
    workflow_id: str
    tarea_id: Optional[str] = None
    procesado_id: str
    sucursal_id: str
    
    # Totales
    total_diferencias: int
    
    # Faltantes
    faltantes: ResumenFaltantes
    
    # Sobrantes
    sobrantes: ResumenSobrantes
    
    # Tolerancia
    tolerancia: ToleranciaAplicada
    
    # Monto propuesto
    monto_propuesto_mxn: float
    excede_minimo: bool
    cargo_minimo_configurado_mxn: float
    
    # Estado
    estado: EstadoResponsabilidad
    
    # Auditoría
    fecha_calculo: datetime
    calculado_por: str
    
    # Metadatos
    fecha_creacion: datetime
    fecha_actualizacion: datetime

    class Config:
        from_attributes = True


class ResponsabilidadListResponse(BaseModel):
    """Schema de respuesta para lista de responsabilidades."""
    total: int = Field(..., description="Total de registros")
    items: List[ResponsabilidadResponse] = Field(default_factory=list)


class ResponsabilidadResumenCalculo(BaseModel):
    """Resumen devuelto después del cálculo."""
    id: str = Field(..., description="ID del registro creado")
    workflow_id: str
    estado: EstadoResponsabilidad
    
    # Resumen ejecutivo
    total_diferencias: int
    faltantes_valor_mxn: float
    sobrantes_valor_mxn: float
    valor_excluido_por_tolerancia_mxn: float
    monto_propuesto_mxn: float
    excede_minimo: bool
    
    # Workflow actualizado
    workflow_estado_nuevo: str = Field(..., description="Nuevo estado del workflow")
    
    mensaje: str = Field(..., description="Mensaje descriptivo del resultado")


class ConfiguracionResponsabilidadResponse(BaseModel):
    """Configuración de responsabilidad económica."""
    cargo_minimo_mxn: float = Field(default=50.0, description="Monto mínimo para generar cargo")
    tolerancia_unidades: int = Field(default=2, description="Tolerancia absoluta en unidades")
    tolerancia_porcentaje_diferencia: float = Field(default=1.5, description="Tolerancia relativa (%)")
    precio_faltante_default: float = Field(default=0.0, description="Precio unitario si no viene del análisis")
    modulo_responsabilidad_activo: bool = Field(default=True, description="¿Módulo habilitado?")
    permitir_compensacion_faltantes_sobrantes: bool = Field(default=False, description="¿Permitir compensación?")


class ConfiguracionResponsabilidadUpdate(BaseModel):
    """Schema para actualizar configuración de responsabilidad."""
    cargo_minimo_mxn: Optional[float] = Field(None, ge=0)
    tolerancia_unidades: Optional[int] = Field(None, ge=0)
    tolerancia_porcentaje_diferencia: Optional[float] = Field(None, ge=0, le=100)
    precio_faltante_default: Optional[float] = Field(None, ge=0)
    modulo_responsabilidad_activo: Optional[bool] = None
    permitir_compensacion_faltantes_sobrantes: Optional[bool] = None


# ==================== FASE 2C.2: APROBACIONES ====================

class AccionResponsabilidadRequest(BaseModel):
    """Request para ejecutar una acción sobre responsabilidad."""
    usuario_id: str = Field(..., description="ID del usuario que ejecuta la acción")
    usuario_rol: str = Field(..., description="Rol del usuario (AFECTADO, SUPERVISOR, GERENTE_OPS, DIRECCION)")
    comentario: str = Field(..., min_length=10, max_length=1000, description="Comentario obligatorio (mínimo 10 caracteres)")
    motivo_codigo: Optional[str] = Field(None, description="Código de motivo predefinido (opcional)")
    
    @field_validator('comentario')
    @classmethod
    def validar_comentario(cls, v):
        if not v or len(v.strip()) < 10:
            raise ValueError('El comentario debe tener al menos 10 caracteres significativos')
        # Rechazar comentarios triviales
        triviales = ['ok', 'aprobado', 'rechazado', 'exonerado', 'sí', 'no', 'test', 'prueba']
        if v.strip().lower() in triviales:
            raise ValueError('El comentario debe ser descriptivo, no trivial')
        return v.strip()


class AccionResponsabilidadResponse(BaseModel):
    """Response después de ejecutar una acción."""
    success: bool
    responsabilidad_id: str
    accion: AccionResponsabilidad
    estado_anterior: EstadoResponsabilidad
    estado_nuevo: EstadoResponsabilidad
    mensaje: str
    transicion_id: str = Field(..., description="ID del registro de historial")
    workflow_estado: str = Field(..., description="Estado actual del workflow")


class HistorialTransicionResponse(BaseModel):
    """Registro de historial de una transición."""
    id: str
    responsabilidad_id: str
    accion: str
    estado_anterior: str
    estado_nuevo: str
    usuario_id: str
    usuario_rol: Optional[str] = None
    comentario: str
    motivo_codigo: Optional[str] = None
    monto_al_momento: float
    fecha: datetime


class HistorialListResponse(BaseModel):
    """Lista de historial de transiciones."""
    responsabilidad_id: str
    total: int
    items: List[HistorialTransicionResponse]


class ResponsabilidadPendienteResponse(BaseModel):
    """Responsabilidad pendiente de aprobación."""
    id: str
    workflow_id: str
    sucursal_id: str
    monto_propuesto_mxn: float
    excede_minimo: bool
    estado: EstadoResponsabilidad
    fecha_calculo: datetime
    dias_pendiente: int = Field(default=0, description="Días desde el cálculo")


class PendientesAprobacionResponse(BaseModel):
    """Lista de responsabilidades pendientes de aprobación."""
    total: int
    monto_total_pendiente: float
    items: List[ResponsabilidadPendienteResponse]


class EnDisputaResponse(BaseModel):
    """Lista de responsabilidades en disputa."""
    total: int
    monto_total_en_disputa: float
    items: List[ResponsabilidadPendienteResponse]


# Transiciones válidas entre estados
TRANSICIONES_VALIDAS = {
    EstadoResponsabilidad.CALCULADO: [EstadoResponsabilidad.PROPUESTO],
    EstadoResponsabilidad.PROPUESTO: [
        EstadoResponsabilidad.APROBADO,
        EstadoResponsabilidad.RECHAZADO,
        EstadoResponsabilidad.EXONERADO,
        EstadoResponsabilidad.EN_DISPUTA
    ],
    EstadoResponsabilidad.EN_DISPUTA: [
        EstadoResponsabilidad.PROPUESTO,  # Resolver disputa
        EstadoResponsabilidad.EXONERADO,
        EstadoResponsabilidad.RECHAZADO
    ],
    EstadoResponsabilidad.APROBADO: [],  # Estado final en 2C.2 (APLICADO será en 2C.3)
    EstadoResponsabilidad.RECHAZADO: [],  # Estado final
    EstadoResponsabilidad.EXONERADO: [],  # Estado final
}
