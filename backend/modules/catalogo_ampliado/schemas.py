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
    tipo_entidad: Literal["USUARIO", "CLIENTE", "PROVEEDOR", "CONTACTO_PROVEEDOR", "OTRO_CANONICO"]
    entidad_clave: str = Field(min_length=1, max_length=200)
    es_principal: bool = False


class PersonaEmpresaRolCreate(BaseModel):
    persona_id: int
    rol_corporativo_id: int
    cargo_detalle: Optional[str] = Field(default=None, max_length=200)
    participacion_pct: Optional[float] = Field(default=None, ge=0, le=100)
    facultades: Optional[str] = None
    vigente_desde: Optional[date] = None
    vigente_hasta: Optional[date] = None


class DocumentoCreate(BaseModel):
    tipo_documento_id: int
    propietario_tipo: Literal["PERSONA", "EMPRESA", "RELACION"]
    persona_id: Optional[int] = None
    empresa_id: Optional[int] = None
    persona_empresa_rol_id: Optional[int] = None
    titulo: str = Field(min_length=1, max_length=250)


class AlertaReglaCreate(BaseModel):
    empresa_id: Optional[int] = None
    tipo_documento_id: Optional[int] = None
    usuario_objetivo: Optional[str] = Field(default=None, max_length=320)
    dias_antes: int = Field(ge=0, le=3650)
    canal: Literal["TAREA", "EMAIL", "WHATSAPP", "APP"]
