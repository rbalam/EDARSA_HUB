"""
Schemas Pydantic para Auditoría
CAB-003 | EDARSA HUB - Fase 2A

Define los modelos de datos para las decisiones de auditoría.
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from .enums import DecisionAuditoria


class DecisionAuditoriaBase(BaseModel):
    """Campos base de una decisión de auditoría."""
    workflow_id: str = Field(..., description="FK al workflow")
    decision: DecisionAuditoria = Field(..., description="Decisión del auditor")
    comentarios_auditor: str = Field(
        ..., 
        min_length=10, 
        description="Comentarios del auditor (mínimo 10 caracteres)"
    )
    requiere_accion_adicional: bool = Field(
        default=False, 
        description="Indica si requiere seguimiento"
    )


class DecisionAuditoriaCreate(BaseModel):
    """Schema para crear una decisión de auditoría."""
    workflow_id: str
    decision: DecisionAuditoria
    comentarios_auditor: str = Field(..., min_length=10)
    usuario_auditor_id: str = Field(..., description="ID del auditor")
    requiere_accion_adicional: bool = False


class DecisionAuditoriaInDB(DecisionAuditoriaBase):
    """Schema de decisión como está almacenada en BD."""
    id: str = Field(..., alias="_id")
    usuario_auditor_id: str
    fecha_decision: datetime

    class Config:
        populate_by_name = True
        from_attributes = True


class DecisionAuditoriaResponse(BaseModel):
    """Schema de respuesta para una decisión de auditoría."""
    id: str = Field(..., alias="_id")
    workflow_id: str
    decision: DecisionAuditoria
    comentarios_auditor: str
    usuario_auditor_id: str
    fecha_decision: datetime
    requiere_accion_adicional: bool

    class Config:
        populate_by_name = True
        from_attributes = True


class DecisionAuditoriaListResponse(BaseModel):
    """Schema de respuesta para lista de decisiones."""
    total: int
    items: List[DecisionAuditoriaResponse] = Field(default_factory=list)
