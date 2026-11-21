from datetime import date
from typing import Literal, Optional

from pydantic import BaseModel, Field


class EmpresaConfiguracionUpdate(BaseModel):
    catalogo_legal_ampliado_activo: bool
    dias_alerta_default: Optional[int] = Field(default=None, ge=0, le=3650)


class PersonaCreate(BaseModel):
    nombre: str = Field(min_length=1, max_length=150)
    apellido_paterno: Optional[str] = Field(default=None, max_length=100)
    apellido_materno: Optional[str] = Field(default=None, max_length=100)
    rfc: Optional[str] = Field(default=None, max_length=13)
    curp: Optional[str] = Field(default=None, max_length=18)
    fecha_nacimiento: Optional[date] = None
    nacionalidad: Optional[str] = Field(default=None, max_length=80)


class PersonaVinculoCreate(BaseModel):
    usuario_id: Optional[int] = None
    cliente_id: Optional[int] = None
    proveedor_id: Optional[int] = None
    contacto_cliente_id: Optional[int] = None
    contacto_proveedor_id: Optional[int] = None
    es_principal: bool = False


class PersonaEmpresaRolCreate(BaseModel):
    persona_id: int = Field(gt=0)
    rol_corporativo_id: int = Field(gt=0)
    cargo_detalle: Optional[str] = Field(default=None, max_length=200)
    participacion_pct: Optional[float] = Field(default=None, ge=0, le=100)
    facultades: Optional[str] = None
    vigente_desde: Optional[date] = None
    vigente_hasta: Optional[date] = None


class DocumentoCreate(BaseModel):
    tipo_documento_id: int = Field(gt=0)
    propietario_tipo: Literal['PERSONA','EMPRESA','RELACION']
    persona_id: Optional[int] = None
    persona_empresa_rol_id: Optional[int] = None
    titulo: str = Field(min_length=1, max_length=250)


class DocumentoVersionCreate(BaseModel):
    nombre_archivo: str = Field(min_length=1, max_length=260)
    storage_key: str = Field(min_length=1, max_length=900)
    mime_type: Optional[str] = Field(default=None, max_length=120)
    tamanio_bytes: Optional[int] = Field(default=None, ge=0)
    sha256: str = Field(min_length=64, max_length=64)
    fecha_emision: Optional[date] = None
    fecha_vencimiento: Optional[date] = None
    fecha_vencimiento_fuente: Optional[Literal['CAPTURA','OCR','SISTEMA']] = None
    ocr_texto: Optional[str] = None
    ocr_metadata_json: Optional[str] = None
    ocr_confianza: Optional[float] = Field(default=None, ge=0, le=1)


class AlertaReglaCreate(BaseModel):
    tipo_documento_id: Optional[int] = None
    usuario_objetivo_id: Optional[int] = None
    dias_antes: int = Field(ge=0, le=3650)
    canal: Literal['TAREA','EMAIL','WHATSAPP','APP']
