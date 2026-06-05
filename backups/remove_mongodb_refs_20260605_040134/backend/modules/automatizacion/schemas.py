# -*- coding: utf-8 -*-
"""
Schemas Pydantic - Automatización de Análisis de Inventarios
CAB-003 - Fase 0

Propósito: Contratos internos de validación.
Estado: Definidos pero no usados activamente en Fase 0.
Uso: Se activarán cuando se implementen endpoints en Fase 1A.

NOTA: Estos schemas corresponden a las 6 tablas definidas en el DDL.
      El DDL es la fuente maestra de verdad para la estructura.
"""

from datetime import datetime, date, time
from typing import Optional, Literal
from pydantic import BaseModel, Field, EmailStr
from uuid import UUID


# =============================================================================
# ENUMS / LITERALS
# =============================================================================

SistemaOrigen = Literal["SOFTRESTAURANT", "MPRO"]
NivelOrigen = Literal["SERVER", "SUCURSAL", "ALMACEN"]
CanalEnvio = Literal["EMAIL", "WHATSAPP", "AMBOS"]
TipoDestinatario = Literal["TO", "CC", "BCC"]
EstadoProcesado = Literal["EN_PROCESO", "EXITOSO", "ERROR"]
EstadoEjecucion = Literal["INICIADO", "COMPLETADO", "ERROR"]
EstadoEnvio = Literal["PENDIENTE", "ENVIADO", "ERROR"]


# =============================================================================
# SCHEMA: automatizacion_inventarios_config
# =============================================================================

class AutomatizacionConfigBase(BaseModel):
    """Schema base para configuración de automatización."""
    server_id: str = Field(..., max_length=50)
    sucursal_id: Optional[str] = Field(None, max_length=20)
    almacen_id: Optional[str] = Field(None, max_length=20)
    intervalo_minutos: int = Field(default=15, ge=5, le=1440)
    hora_inicio: Optional[time] = None
    hora_fin: Optional[time] = None
    activo: bool = Field(default=False)


class AutomatizacionConfigCreate(AutomatizacionConfigBase):
    """Schema para crear configuración."""
    created_by: Optional[str] = Field(None, max_length=100)


class AutomatizacionConfigResponse(AutomatizacionConfigBase):
    """Schema de respuesta para configuración."""
    config_id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: Optional[str] = None
    updated_by: Optional[str] = None

    class Config:
        from_attributes = True


# =============================================================================
# SCHEMA: automatizacion_inventarios_destinatarios
# =============================================================================

class DestinatarioBase(BaseModel):
    """Schema base para destinatarios."""
    server_id: str = Field(..., max_length=50)
    sucursal_id: Optional[str] = Field(None, max_length=20)
    almacen_id: Optional[str] = Field(None, max_length=20)
    nivel_origen: NivelOrigen
    canal: CanalEnvio = Field(default="EMAIL")
    tipo_destinatario: TipoDestinatario = Field(default="TO")
    email: Optional[EmailStr] = None
    telefono: Optional[str] = Field(None, max_length=20)
    nombre_contacto: Optional[str] = Field(None, max_length=100)
    activo: bool = Field(default=True)


class DestinatarioCreate(DestinatarioBase):
    """Schema para crear destinatario."""
    created_by: Optional[str] = Field(None, max_length=100)


class DestinatarioResponse(DestinatarioBase):
    """Schema de respuesta para destinatario."""
    destinatario_id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: Optional[str] = None
    updated_by: Optional[str] = None

    class Config:
        from_attributes = True


# =============================================================================
# SCHEMA: automatizacion_inventarios_folios_procesados
# =============================================================================

class FolioProcesadoBase(BaseModel):
    """
    Schema base para folios procesados.
    
    NOTA: La clave única de 6 componentes está definida en el DDL:
    (sistema_origen, server_id, sucursal_id, almacen_id, folio_inventario, fecha_inventario)
    """
    sistema_origen: SistemaOrigen
    server_id: str = Field(..., max_length=50)
    sucursal_id: str = Field(..., max_length=20)
    almacen_id: str = Field(..., max_length=20)
    folio_inventario: str = Field(..., max_length=50)
    fecha_inventario: date
    hash_verificacion: str = Field(..., max_length=64)
    estado: EstadoProcesado = Field(default="EN_PROCESO")


class FolioProcesadoCreate(FolioProcesadoBase):
    """Schema para crear registro de folio procesado."""
    created_by: Optional[str] = Field(None, max_length=100)


class FolioProcesadoResponse(FolioProcesadoBase):
    """Schema de respuesta para folio procesado."""
    procesado_id: UUID
    heartbeat_at: Optional[datetime] = None
    fecha_procesado: Optional[datetime] = None
    error_detalle: Optional[str] = None
    ruta_archivo_excel: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: Optional[str] = None
    updated_by: Optional[str] = None

    class Config:
        from_attributes = True


# =============================================================================
# SCHEMA: automatizacion_inventarios_ejecuciones
# =============================================================================

class EjecucionBase(BaseModel):
    """Schema base para ejecuciones del scheduler."""
    estado: EstadoEjecucion = Field(default="INICIADO")
    servidores_escaneados: Optional[int] = None
    folios_detectados: Optional[int] = None
    folios_procesados: Optional[int] = None
    folios_error: Optional[int] = None
    detalle_errores: Optional[str] = None


class EjecucionCreate(EjecucionBase):
    """Schema para crear registro de ejecución."""
    fecha_inicio: datetime


class EjecucionResponse(EjecucionBase):
    """Schema de respuesta para ejecución."""
    ejecucion_id: UUID
    fecha_inicio: datetime
    fecha_fin: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# =============================================================================
# SCHEMA: automatizacion_inventarios_envios
# =============================================================================

class EnvioBase(BaseModel):
    """Schema base para envíos."""
    procesado_id: UUID
    destinatario_email: EmailStr
    canal: CanalEnvio = Field(default="EMAIL")
    tipo_destinatario: TipoDestinatario
    estado: EstadoEnvio = Field(default="PENDIENTE")
    intentos: int = Field(default=0, ge=0)


class EnvioCreate(EnvioBase):
    """Schema para crear registro de envío."""
    pass


class EnvioResponse(EnvioBase):
    """Schema de respuesta para envío."""
    envio_id: UUID
    fecha_envio: Optional[datetime] = None
    error_detalle: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# =============================================================================
# SCHEMA: automatizacion_inventarios_ultimo_folio_conocido
# =============================================================================

class UltimoFolioBase(BaseModel):
    """
    Schema base para marca de agua de último folio conocido.
    
    NOTA: La clave única está definida en el DDL:
    (sistema_origen, server_id, sucursal_id, almacen_id)
    """
    sistema_origen: SistemaOrigen
    server_id: str = Field(..., max_length=50)
    sucursal_id: str = Field(..., max_length=20)
    almacen_id: str = Field(..., max_length=20)
    ultimo_folio: str = Field(..., max_length=50)
    fecha_ultimo_folio: date


class UltimoFolioCreate(UltimoFolioBase):
    """Schema para crear registro de último folio."""
    created_by: Optional[str] = Field(None, max_length=100)


class UltimoFolioResponse(UltimoFolioBase):
    """Schema de respuesta para último folio."""
    id: UUID
    fecha_actualizacion: datetime
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: Optional[str] = None
    updated_by: Optional[str] = None

    class Config:
        from_attributes = True
