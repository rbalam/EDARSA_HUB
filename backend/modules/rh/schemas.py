"""
EDARSA HUB - RH Schemas (Catálogos)
===================================
Modelos Pydantic para validación de datos del módulo de Recursos Humanos.

FASE 6B DEL REFACTOR MODULAR (Diciembre 2025):
- Modelos para Catálogo de Puestos (CRUD)
- Modelos para Catálogo de Tipos de Incidencias (CRUD)
- Modelos de respuesta estandarizados

CONTRATOS DE API:
- Los modelos de respuesta mantienen compatibilidad exacta con los endpoints
  originales en server.py para no romper el frontend existente.
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Any
from decimal import Decimal


# ============================================================================
# CATÁLOGO DE PUESTOS
# ============================================================================

class PuestoBase(BaseModel):
    """Campos base compartidos para Puesto."""
    descripcion: str = Field(..., min_length=1, max_length=200, description="Descripción del puesto")
    departamento: str = Field(default="", max_length=100, description="Departamento")
    sueldo_base: Decimal = Field(default=Decimal("0"), ge=0, description="Sueldo base semanal SBC")
    nomipaq_id: str = Field(default="", max_length=50, description="ID de mapeo con NomiPAQ")
    mpro_id: str = Field(default="", max_length=50, description="ID de mapeo con MPRO")


class PuestoCreate(PuestoBase):
    """Modelo para crear un nuevo puesto."""
    
    @field_validator('descripcion')
    @classmethod
    def descripcion_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError('La descripción del puesto es requerida')
        return v.strip()


class PuestoUpdate(BaseModel):
    """Modelo para actualizar un puesto existente (campos opcionales)."""
    descripcion: Optional[str] = Field(None, min_length=1, max_length=200)
    departamento: Optional[str] = Field(None, max_length=100)
    sueldo_base: Optional[Decimal] = Field(None, ge=0)
    nomipaq_id: Optional[str] = Field(None, max_length=50)
    mpro_id: Optional[str] = Field(None, max_length=50)
    
    @field_validator('descripcion')
    @classmethod
    def descripcion_not_empty(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not v.strip():
            raise ValueError('La descripción no puede estar vacía')
        return v.strip() if v else v


class PuestoResponse(BaseModel):
    """Modelo de respuesta para un puesto individual (desde BD)."""
    PuestoID: int
    Descripcion: str
    Departamento: Optional[str] = None
    Sueldo_Base_Seman_SBC: Optional[Decimal] = None
    
    class Config:
        from_attributes = True


class PuestosListResponse(BaseModel):
    """Modelo de respuesta para lista de puestos."""
    puestos: List[PuestoResponse]
    total: int


# ============================================================================
# CATÁLOGO DE SUCURSALES (Solo lectura en FASE 6B)
# ============================================================================

class SucursalResponse(BaseModel):
    """Modelo de respuesta para una sucursal."""
    SucursalID: int
    Nombre_Sucursal: str
    Ciudad: Optional[str] = None
    Activa: Optional[bool] = None
    RFC: Optional[str] = None
    RazonSocial: Optional[str] = None
    
    class Config:
        from_attributes = True


class SucursalesListResponse(BaseModel):
    """Modelo de respuesta para lista de sucursales."""
    sucursales: List[SucursalResponse]
    total: int


# ============================================================================
# CATÁLOGO DE TIPOS DE INCIDENCIAS
# ============================================================================

class TipoIncidenciaBase(BaseModel):
    """Campos base para Tipo de Incidencia."""
    codigo: str = Field(..., min_length=1, max_length=10, description="Código único (ej: BON, HEX)")
    descripcion: str = Field(..., min_length=1, max_length=100, description="Descripción del tipo")
    categoria: str = Field(default="Descuento", description="Ingreso o Descuento")
    calculo_monto: str = Field(default="Manual", max_length=20, description="Manual, Porcentaje, Formula")
    nomipaq_id: str = Field(default="", max_length=50, description="ID de mapeo con NomiPAQ")
    mpro_id: str = Field(default="", max_length=50, description="ID de mapeo con MPRO")
    
    @field_validator('codigo')
    @classmethod
    def codigo_uppercase(cls, v: str) -> str:
        if not v.strip():
            raise ValueError('El código es requerido')
        return v.strip().upper()
    
    @field_validator('descripcion')
    @classmethod
    def descripcion_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError('La descripción es requerida')
        return v.strip()
    
    @field_validator('categoria')
    @classmethod
    def categoria_valida(cls, v: str) -> str:
        if v not in ('Ingreso', 'Descuento'):
            raise ValueError('Categoría debe ser Ingreso o Descuento')
        return v


class TipoIncidenciaCreate(TipoIncidenciaBase):
    """Modelo para crear un tipo de incidencia."""
    pass


class TipoIncidenciaUpdate(BaseModel):
    """Modelo para actualizar un tipo de incidencia (campos opcionales)."""
    codigo: Optional[str] = Field(None, min_length=1, max_length=10)
    descripcion: Optional[str] = Field(None, min_length=1, max_length=100)
    categoria: Optional[str] = None
    calculo_monto: Optional[str] = Field(None, max_length=20)
    activo: Optional[bool] = None
    nomipaq_id: Optional[str] = Field(None, max_length=50)
    mpro_id: Optional[str] = Field(None, max_length=50)
    
    @field_validator('codigo')
    @classmethod
    def codigo_uppercase(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            if not v.strip():
                raise ValueError('El código no puede estar vacío')
            return v.strip().upper()
        return v
    
    @field_validator('categoria')
    @classmethod
    def categoria_valida(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in ('Ingreso', 'Descuento'):
            raise ValueError('Categoría debe ser Ingreso o Descuento')
        return v


class TipoIncidenciaResponse(BaseModel):
    """Modelo de respuesta para un tipo de incidencia individual (desde BD)."""
    TipoIncidenciaID: int
    Codigo: str
    Descripcion: str
    Categoria: str
    Afectacion: int
    Calculo_Monto: Optional[str] = None
    Activo: Optional[bool] = None
    NomiPAQ_ID: Optional[str] = None
    MPRO_ID: Optional[str] = None
    
    class Config:
        from_attributes = True


class TiposIncidenciasListResponse(BaseModel):
    """Modelo de respuesta para lista de tipos de incidencias."""
    tipos_incidencias: List[TipoIncidenciaResponse]
    total: int
    nota: Optional[str] = None  # Para indicar si se usan tipos por defecto


# ============================================================================
# RESPUESTAS GENÉRICAS
# ============================================================================

class SuccessResponse(BaseModel):
    """Respuesta genérica de éxito para operaciones CRUD."""
    success: bool = True
    message: str


class SuccessWithIdResponse(BaseModel):
    """Respuesta de éxito con ID del registro creado."""
    success: bool = True
    message: str
    colaborador_id: Optional[int] = None


class ScriptInicializacionResponse(BaseModel):
    """Respuesta para el script de inicialización SQL."""
    script: str
    instrucciones: List[str]
    compatibilidad: dict


# ============================================================================
# COLABORADORES (FASE 6C-B)
# ============================================================================

# Valores permitidos para estatus laboral
ESTATUS_LABORAL_VALIDOS = ["Activo", "Baja", "Vacaciones", "Incapacidad", "Permiso", "Suspendido"]


class ColaboradorBase(BaseModel):
    """Campos base compartidos para Colaborador."""
    nombre_completo: str = Field(..., min_length=2, max_length=200, description="Nombre completo del colaborador")
    curp: Optional[str] = Field(None, min_length=18, max_length=18, description="CURP (18 caracteres)")
    rfc: Optional[str] = Field(None, min_length=12, max_length=13, description="RFC (12-13 caracteres)")
    clabe_bancaria: Optional[str] = Field(None, min_length=18, max_length=18, description="CLABE interbancaria (18 dígitos)")
    sucursal_id: int = Field(..., gt=0, description="ID de sucursal")
    puesto_id: int = Field(..., gt=0, description="ID de puesto")
    estatus_laboral: str = Field(default="Activo", description="Estatus laboral del colaborador")
    
    @field_validator('nombre_completo')
    @classmethod
    def nombre_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError('El nombre completo es requerido')
        return v.strip()
    
    @field_validator('curp')
    @classmethod
    def curp_format(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v = v.strip().upper()
        if len(v) != 18:
            raise ValueError('CURP debe tener exactamente 18 caracteres')
        # Patrón básico: 4 letras + 6 dígitos + 1 letra (H/M) + 5 letras + 1 alfanumérico + 1 dígito
        import re
        pattern = r'^[A-Z]{4}\d{6}[HM][A-Z]{5}[A-Z0-9]\d$'
        if not re.match(pattern, v):
            raise ValueError('Formato de CURP inválido')
        return v
    
    @field_validator('rfc')
    @classmethod
    def rfc_format(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v = v.strip().upper()
        if len(v) not in (12, 13):
            raise ValueError('RFC debe tener 12 o 13 caracteres')
        # Patrón básico RFC
        import re
        pattern = r'^[A-ZÑ&]{3,4}\d{6}[A-Z0-9]{3}$'
        if not re.match(pattern, v):
            raise ValueError('Formato de RFC inválido')
        return v
    
    @field_validator('clabe_bancaria')
    @classmethod
    def clabe_format(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v = v.strip()
        if len(v) != 18:
            raise ValueError('CLABE debe tener exactamente 18 dígitos')
        if not v.isdigit():
            raise ValueError('CLABE debe contener solo dígitos')
        return v
    
    @field_validator('estatus_laboral')
    @classmethod
    def estatus_valido(cls, v: str) -> str:
        if v not in ESTATUS_LABORAL_VALIDOS:
            raise ValueError(f'Estatus laboral debe ser uno de: {", ".join(ESTATUS_LABORAL_VALIDOS)}')
        return v


class ColaboradorCreate(ColaboradorBase):
    """Modelo para crear un nuevo colaborador."""
    pass


class ColaboradorUpdate(BaseModel):
    """Modelo para actualizar un colaborador existente (campos opcionales)."""
    nombre_completo: Optional[str] = Field(None, min_length=2, max_length=200)
    curp: Optional[str] = Field(None, min_length=18, max_length=18)
    rfc: Optional[str] = Field(None, min_length=12, max_length=13)
    clabe_bancaria: Optional[str] = Field(None, min_length=18, max_length=18)
    sucursal_id: Optional[int] = Field(None, gt=0)
    puesto_id: Optional[int] = Field(None, gt=0)
    estatus_laboral: Optional[str] = None
    
    @field_validator('nombre_completo')
    @classmethod
    def nombre_not_empty(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not v.strip():
            raise ValueError('El nombre no puede estar vacío')
        return v.strip() if v else v
    
    @field_validator('curp')
    @classmethod
    def curp_format(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v = v.strip().upper()
        if len(v) != 18:
            raise ValueError('CURP debe tener exactamente 18 caracteres')
        import re
        pattern = r'^[A-Z]{4}\d{6}[HM][A-Z]{5}[A-Z0-9]\d$'
        if not re.match(pattern, v):
            raise ValueError('Formato de CURP inválido')
        return v
    
    @field_validator('rfc')
    @classmethod
    def rfc_format(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v = v.strip().upper()
        if len(v) not in (12, 13):
            raise ValueError('RFC debe tener 12 o 13 caracteres')
        import re
        pattern = r'^[A-ZÑ&]{3,4}\d{6}[A-Z0-9]{3}$'
        if not re.match(pattern, v):
            raise ValueError('Formato de RFC inválido')
        return v
    
    @field_validator('clabe_bancaria')
    @classmethod
    def clabe_format(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v = v.strip()
        if len(v) != 18:
            raise ValueError('CLABE debe tener exactamente 18 dígitos')
        if not v.isdigit():
            raise ValueError('CLABE debe contener solo dígitos')
        return v
    
    @field_validator('estatus_laboral')
    @classmethod
    def estatus_valido(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in ESTATUS_LABORAL_VALIDOS:
            raise ValueError(f'Estatus laboral debe ser uno de: {", ".join(ESTATUS_LABORAL_VALIDOS)}')
        return v


class ColaboradorResponse(BaseModel):
    """Modelo de respuesta para un colaborador (vista lista)."""
    ColaboradorID: int
    Nombre_Completo: str
    CURP: Optional[str] = None
    RFC: Optional[str] = None
    CLABE_Bancaria: Optional[str] = None
    SucursalID: Optional[int] = None
    Nombre_Sucursal: Optional[str] = None
    PuestoID: Optional[int] = None
    Puesto: Optional[str] = None
    Departamento: Optional[str] = None
    Colaborador_Activo: Optional[bool] = None
    Fecha_Alta: Optional[str] = None
    Estatus_Laboral: Optional[str] = None
    Validacion_IA_RFC: Optional[str] = None
    Validacion_IA_CURP: Optional[str] = None
    Validacion_IA_EdoCta: Optional[str] = None
    Validacion_IA_Contrato: Optional[str] = None
    
    class Config:
        from_attributes = True


class ColaboradorDetalleResponse(BaseModel):
    """Modelo de respuesta para detalle de colaborador (incluye relacionados)."""
    colaborador: ColaboradorResponse
    incidencias: List[Any] = []  # Tipado flexible hasta FASE 6D
    asistencias: List[Any] = []  # Tipado flexible hasta FASE 6E
    auditoria_fiscal: List[Any] = []  # Tipado flexible hasta FASE 6G


class ColaboradoresListResponse(BaseModel):
    """Modelo de respuesta para lista paginada de colaboradores."""
    colaboradores: List[ColaboradorResponse]
    total: int
    page: int
    limit: int
    pages: int


class ColaboradorFiltros(BaseModel):
    """Filtros para búsqueda de colaboradores."""
    sucursal_id: Optional[int] = None
    puesto_id: Optional[int] = None
    estatus: Optional[str] = None
    buscar: Optional[str] = None
