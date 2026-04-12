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


class ScriptInicializacionResponse(BaseModel):
    """Respuesta para el script de inicialización SQL."""
    script: str
    instrucciones: List[str]
    compatibilidad: dict
