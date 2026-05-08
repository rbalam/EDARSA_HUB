"""
Schemas Pydantic para Cargos Económicos
CAB-003 | EDARSA HUB - Fase 2C.3

Define los modelos de datos para la aplicación formal de cargos económicos
derivados de diferencias de inventario dictaminadas.
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime
from enum import Enum


class EstatusCargo(str, Enum):
    """
    Estados del ciclo de vida de un cargo económico.
    
    Flujo normal: PENDIENTE → AUTORIZADO → APLICADO
    Flujo rechazo: PENDIENTE → RECHAZADO
    Flujo cancelación: PENDIENTE/AUTORIZADO → CANCELADO
    Flujo reversa: APLICADO → REVERTIDO
    """
    PENDIENTE = "PENDIENTE"          # Propuesta creada, pendiente autorización
    AUTORIZADO = "AUTORIZADO"        # Autorizado, pendiente aplicación
    APLICADO = "APLICADO"            # Cargo aplicado formalmente
    RECHAZADO = "RECHAZADO"          # Cargo rechazado (no procedía)
    REVERTIDO = "REVERTIDO"          # Cargo revertido post-aplicación
    CANCELADO = "CANCELADO"          # Cargo cancelado antes de aplicar


class AccionCargo(str, Enum):
    """Acciones posibles sobre un cargo económico."""
    CREAR = "CREAR"
    AUTORIZAR = "AUTORIZAR"
    APLICAR = "APLICAR"
    RECHAZAR = "RECHAZAR"
    REVERTIR = "REVERTIR"
    CANCELAR = "CANCELAR"


# Transiciones válidas entre estados de cargo
TRANSICIONES_CARGO_VALIDAS = {
    EstatusCargo.PENDIENTE: [
        EstatusCargo.AUTORIZADO,
        EstatusCargo.RECHAZADO,
        EstatusCargo.CANCELADO
    ],
    EstatusCargo.AUTORIZADO: [
        EstatusCargo.APLICADO,
        EstatusCargo.CANCELADO
    ],
    EstatusCargo.APLICADO: [
        EstatusCargo.REVERTIDO
    ],
    EstatusCargo.RECHAZADO: [],      # Estado final
    EstatusCargo.REVERTIDO: [],      # Estado final
    EstatusCargo.CANCELADO: [],      # Estado final
}


class OrigenCargo(str, Enum):
    """Origen que genera el cargo económico."""
    RESPONSABILIDAD_ECONOMICA = "RESPONSABILIDAD_ECONOMICA"  # Desde 2C.1/2C.2
    MANUAL = "MANUAL"                                         # Creación manual (futuro)


# ==================== SCHEMAS DE CREACIÓN ====================

class CargoEconomicoCreate(BaseModel):
    """Schema para crear una propuesta de cargo económico."""
    responsabilidad_id: str = Field(..., description="ID del registro de responsabilidad económica origen")
    comentario: str = Field(..., min_length=10, max_length=2000, description="Justificación para crear el cargo")
    usuario_id: str = Field(..., description="Usuario que crea la propuesta")
    usuario_rol: str = Field(..., description="Rol del usuario")
    
    @field_validator('comentario')
    @classmethod
    def validar_comentario(cls, v):
        if not v or len(v.strip()) < 10:
            raise ValueError('El comentario debe tener al menos 10 caracteres significativos')
        triviales = ['ok', 'crear', 'cargo', 'test', 'prueba', 'pendiente']
        if v.strip().lower() in triviales:
            raise ValueError('El comentario debe ser descriptivo')
        return v.strip()


class CargoAccionRequest(BaseModel):
    """Request genérico para ejecutar una acción sobre un cargo."""
    usuario_id: str = Field(..., description="ID del usuario que ejecuta la acción")
    usuario_rol: str = Field(..., description="Rol del usuario")
    comentario: str = Field(..., min_length=10, max_length=2000, description="Comentario obligatorio")
    motivo_codigo: Optional[str] = Field(None, description="Código de motivo predefinido")
    
    @field_validator('comentario')
    @classmethod
    def validar_comentario(cls, v):
        if not v or len(v.strip()) < 10:
            raise ValueError('El comentario debe tener al menos 10 caracteres significativos')
        triviales = ['ok', 'sí', 'no', 'test', 'prueba']
        if v.strip().lower() in triviales:
            raise ValueError('El comentario debe ser descriptivo')
        return v.strip()


class CargoReversaRequest(BaseModel):
    """Request para revertir un cargo aplicado."""
    usuario_id: str = Field(..., description="ID del usuario que ejecuta la reversa")
    usuario_rol: str = Field(..., description="Rol del usuario")
    motivo_reversa: str = Field(..., min_length=20, max_length=2000, description="Motivo detallado de la reversa")
    motivo_codigo: Optional[str] = Field(None, description="Código de motivo predefinido")
    
    @field_validator('motivo_reversa')
    @classmethod
    def validar_motivo(cls, v):
        if not v or len(v.strip()) < 20:
            raise ValueError('El motivo de reversa debe tener al menos 20 caracteres detallados')
        return v.strip()


# ==================== SCHEMAS DE RESPUESTA ====================

class CargoEconomicoResponse(BaseModel):
    """Schema de respuesta para un cargo económico."""
    id: str
    
    # Referencias
    responsabilidad_id: str
    workflow_id: str
    procesado_id: str
    sucursal_id: str
    
    # Responsable
    responsable_id: Optional[str] = None
    responsable_nombre: Optional[str] = None
    
    # Montos
    monto_responsabilidad: float = Field(..., description="Monto original de la responsabilidad")
    monto_aplicado: float = Field(default=0.0, description="Monto efectivamente aplicado")
    monto_revertido: float = Field(default=0.0, description="Monto revertido (si aplica)")
    
    # Estado
    estatus_cargo: EstatusCargo
    origen: OrigenCargo
    
    # Fechas de ciclo de vida
    fecha_propuesta: datetime
    fecha_autorizacion: Optional[datetime] = None
    fecha_aplicacion: Optional[datetime] = None
    fecha_reversa: Optional[datetime] = None
    
    # Usuarios responsables
    propuesto_por: str
    autorizado_por: Optional[str] = None
    aplicado_por: Optional[str] = None
    revertido_por: Optional[str] = None
    
    # Auditoría
    fecha_creacion: datetime
    fecha_actualizacion: datetime
    
    class Config:
        from_attributes = True


class CargoEconomicoListResponse(BaseModel):
    """Schema de respuesta para lista de cargos."""
    total: int
    items: List[CargoEconomicoResponse]


class CargoAccionResponse(BaseModel):
    """Response después de ejecutar una acción sobre un cargo."""
    success: bool
    cargo_id: str
    accion: AccionCargo
    estatus_anterior: EstatusCargo
    estatus_nuevo: EstatusCargo
    mensaje: str
    log_id: str = Field(..., description="ID del registro de auditoría")


# ==================== SCHEMAS DE LOG/AUDITORÍA ====================

class CargoLogResponse(BaseModel):
    """Registro de log de un cargo económico."""
    id: str
    cargo_id: str
    accion: str
    estatus_anterior: str
    estatus_nuevo: str
    usuario_id: str
    usuario_rol: Optional[str] = None
    comentario: str
    motivo_codigo: Optional[str] = None
    monto_al_momento: float
    fecha: datetime
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


class CargoLogListResponse(BaseModel):
    """Lista de logs de un cargo."""
    cargo_id: str
    total: int
    items: List[CargoLogResponse]


# ==================== SCHEMAS DE MÉTRICAS ====================

class CargosPendientesResponse(BaseModel):
    """Lista de cargos pendientes de autorización."""
    total: int
    monto_total_pendiente: float
    items: List[CargoEconomicoResponse]


class CargosAplicadosResponse(BaseModel):
    """Lista de cargos aplicados."""
    total: int
    monto_total_aplicado: float
    items: List[CargoEconomicoResponse]


class CargosMetricasResponse(BaseModel):
    """Métricas agregadas de cargos económicos."""
    total_cargos: int
    por_estatus: dict
    monto_total_propuesto: float
    monto_total_autorizado: float
    monto_total_aplicado: float
    monto_total_revertido: float
    promedio_tiempo_autorizacion_horas: Optional[float] = None
    promedio_tiempo_aplicacion_horas: Optional[float] = None


# ==================== SCHEMAS DE ELEGIBILIDAD ====================

class ElegibilidadCargoResponse(BaseModel):
    """
    Response de evaluación de elegibilidad para crear cargo.
    
    Un cargo es elegible si:
    1. La responsabilidad está en estado APROBADO
    2. NO existe controversia activa
    3. NO existe exoneración
    4. NO existe cargo previo activo para la misma responsabilidad
    """
    responsabilidad_id: str
    es_elegible: bool
    motivo: str
    monto_disponible: float = Field(default=0.0, description="Monto disponible para cargo")
    workflow_id: Optional[str] = None
    estado_responsabilidad: Optional[str] = None
    tiene_controversia_activa: bool = False
    tiene_exoneracion: bool = False
    tiene_cargo_previo: bool = False
    cargo_previo_id: Optional[str] = None
