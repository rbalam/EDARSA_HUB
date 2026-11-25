"""Contratos de incidencias de caja; sin SQL ni efectos secundarios."""
from __future__ import annotations
from decimal import Decimal
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field

class TipoIncidenciaCaja(str, Enum):
    CANCELACION = "CANCELACION"
    REAPERTURA = "REAPERTURA"
    BONIFICACION = "BONIFICACION"
    DESCUENTO = "DESCUENTO"
    DIFERENCIA = "DIFERENCIA"
    ERROR_TPV = "ERROR_TPV"
    OTRO = "OTRO"

class IncidenciaCajaCreate(BaseModel):
    tipo: TipoIncidenciaCaja
    cuenta_folio: Optional[str] = Field(default=None, max_length=100)
    corte_caja_id: Optional[int] = Field(default=None, ge=1)
    importe_involucrado: Optional[Decimal] = Field(default=None, ge=0, max_digits=18, decimal_places=2)
    motivo_codigo: str = Field(min_length=1, max_length=100)
    descripcion: str = Field(min_length=1, max_length=2000)
    solicitud_idempotencia: str = Field(min_length=8, max_length=128)

class IncidenciaCajaRead(BaseModel):
    folio: str
    tipo: TipoIncidenciaCaja
    estado: str
    conciliacion_estado: str
    unidad_negocio_id: str
    solicitante_usuario_id: int
