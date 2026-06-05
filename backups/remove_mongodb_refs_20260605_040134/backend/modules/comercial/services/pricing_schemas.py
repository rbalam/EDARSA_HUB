"""
FASE 1C-3I-B: Esquemas Pydantic para Motor de Precios Sugeridos y Benchmark

Este módulo define los modelos de datos para:
- Perfil Digital de Unidad de Negocio
- Competidores
- Menú Items de Competidores
- Benchmark Producto
- Precios Sugeridos (cálculo base sin IA)

REGLAS:
- NO se ejecuta IA en esta fase
- Los esquemas están preparados para futuras extensiones IA
- Validaciones estrictas de tipos y rangos
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from decimal import Decimal
from enum import Enum


# =============================================================================
# ENUMS
# =============================================================================

class TipoRestaurante(str, Enum):
    """Tipos de restaurante soportados."""
    FINE_DINING = "fine_dining"
    CASUAL_DINING = "casual_dining"
    FAST_CASUAL = "fast_casual"
    QUICK_SERVICE = "quick_service"
    BAR_RESTAURANT = "bar_restaurant"
    CAFE = "cafe"
    STEAKHOUSE = "steakhouse"
    SEAFOOD = "seafood"
    MEXICAN = "mexican"
    INTERNATIONAL = "international"
    FUSION = "fusion"
    OTRO = "otro"


class SegmentoPrecio(str, Enum):
    """Segmentos de precio."""
    ECONOMICO = "ECONOMICO"
    MEDIO = "MEDIO"
    MEDIO_ALTO = "MEDIO_ALTO"
    PREMIUM = "PREMIUM"
    LUJO = "LUJO"


class MetodoObtencion(str, Enum):
    """Métodos de obtención de datos de competencia."""
    MANUAL = "MANUAL"
    IA_WEB_PUBLICO = "IA_WEB_PUBLICO"
    IMPORTACION_EXCEL = "IMPORTACION_EXCEL"
    API_PUBLICA = "API_PUBLICA"
    OTRO = "OTRO"


class ConfianzaDato(str, Enum):
    """Niveles de confianza de datos."""
    ALTA = "ALTA"
    MEDIA = "MEDIA"
    BAJA = "BAJA"


class TipoComparacion(str, Enum):
    """Tipos de comparación para benchmark."""
    MISMO_PRODUCTO = "MISMO_PRODUCTO"
    PRODUCTO_SIMILAR = "PRODUCTO_SIMILAR"
    MISMA_CATEGORIA = "MISMA_CATEGORIA"
    BENCHMARK_ASPIRACIONAL = "BENCHMARK_ASPIRACIONAL"
    NO_COMPARABLE = "NO_COMPARABLE"


class TipoMotorPrecio(str, Enum):
    """Tipos de motor de cálculo de precio."""
    VINOS_RANGOS = "VINOS_RANGOS"
    COSTO_MARGEN = "COSTO_MARGEN"
    BENCHMARK_COMPETENCIA = "BENCHMARK_COMPETENCIA"
    MIXTO_COSTO_COMPETENCIA = "MIXTO_COSTO_COMPETENCIA"
    MANUAL_AUTORIZADO = "MANUAL_AUTORIZADO"


class PosicionVsCompetencia(str, Enum):
    """Posición relativa vs competencia."""
    MUY_POR_DEBAJO = "MUY_POR_DEBAJO"
    POR_DEBAJO = "POR_DEBAJO"
    ALINEADO = "ALINEADO"
    POR_ENCIMA = "POR_ENCIMA"
    MUY_POR_ENCIMA = "MUY_POR_ENCIMA"
    SIN_DATOS_COMPETENCIA = "SIN_DATOS_COMPETENCIA"


class EstadoCalculo(str, Enum):
    """Estados del cálculo de precio."""
    CALCULADO = "CALCULADO"
    COSTO_NO_CONFIGURADO = "COSTO_NO_CONFIGURADO"
    IMPUESTO_NO_CONFIGURADO = "IMPUESTO_NO_CONFIGURADO"
    MARGEN_INVALIDO = "MARGEN_INVALIDO"
    RANGO_NO_CONFIGURADO = "RANGO_NO_CONFIGURADO"
    ERROR_CALCULO = "ERROR_CALCULO"
    # Estados especiales para vinos (heredados de precios_vinos_service.py)
    COSTO_BASE_NO_CONFIGURADO = "COSTO_BASE_NO_CONFIGURADO"
    NO_APLICA_RANGO_SERVICIO = "NO_APLICA_RANGO_SERVICIO"
    NO_APLICA_RANGO_PRESENTACION = "NO_APLICA_RANGO_PRESENTACION"
    NO_APLICA_RANGO_OPERATIVO = "NO_APLICA_RANGO_OPERATIVO"


# =============================================================================
# PERFIL DIGITAL DE UNIDAD DE NEGOCIO
# =============================================================================

class PerfilDigitalBase(BaseModel):
    """Campos comunes del perfil digital."""
    nombre_comercial: str = Field(..., max_length=200, description="Nombre comercial público")
    concepto_restaurante: Optional[str] = Field(None, max_length=500, description="Descripción del concepto")
    tipo_restaurante: Optional[TipoRestaurante] = Field(None, description="Tipo de restaurante")
    segmento_precio: Optional[SegmentoPrecio] = Field(None, description="Segmento de precio")
    ciudad: Optional[str] = Field(None, max_length=100)
    estado: Optional[str] = Field(None, max_length=100)
    pais: str = Field(default="México", max_length=50)
    zona_comercial: Optional[str] = Field(None, max_length=200)
    
    # URLs
    sitio_web_oficial: Optional[str] = Field(None, max_length=500)
    url_menu_digital: Optional[str] = Field(None, max_length=500)
    url_reservaciones: Optional[str] = Field(None, max_length=500)
    url_google_maps: Optional[str] = Field(None, max_length=500)
    url_instagram: Optional[str] = Field(None, max_length=500)
    url_facebook: Optional[str] = Field(None, max_length=500)
    url_tripadvisor: Optional[str] = Field(None, max_length=500)
    url_opentable: Optional[str] = Field(None, max_length=500)
    url_delivery: Optional[str] = Field(None, max_length=500)
    
    # Comercial
    ticket_promedio_objetivo: Optional[float] = Field(None, gt=0, description="Ticket promedio objetivo")
    rango_precio_objetivo: Optional[str] = Field(None, max_length=30)
    moneda: str = Field(default="MXN", max_length=10)
    
    # Contexto IA (preparado para futuro)
    descripcion_concepto: Optional[str] = Field(None, description="Descripción extendida para IA")
    palabras_clave: Optional[str] = Field(None, max_length=1000, description="Keywords para IA")


class PerfilDigitalCreate(PerfilDigitalBase):
    """Request para crear perfil digital."""
    empresa_id: int = Field(..., gt=0, description="ID de la empresa")
    unidad_negocio_id: int = Field(..., gt=0, description="ID de la unidad de negocio")
    server_id: Optional[str] = Field(None, description="UUID del servidor")


class PerfilDigitalUpdate(BaseModel):
    """Request para actualizar perfil digital."""
    nombre_comercial: Optional[str] = Field(None, max_length=200)
    concepto_restaurante: Optional[str] = Field(None, max_length=500)
    tipo_restaurante: Optional[TipoRestaurante] = None
    segmento_precio: Optional[SegmentoPrecio] = None
    ciudad: Optional[str] = Field(None, max_length=100)
    estado: Optional[str] = Field(None, max_length=100)
    pais: Optional[str] = Field(None, max_length=50)
    zona_comercial: Optional[str] = Field(None, max_length=200)
    
    sitio_web_oficial: Optional[str] = Field(None, max_length=500)
    url_menu_digital: Optional[str] = Field(None, max_length=500)
    url_reservaciones: Optional[str] = Field(None, max_length=500)
    url_google_maps: Optional[str] = Field(None, max_length=500)
    url_instagram: Optional[str] = Field(None, max_length=500)
    url_facebook: Optional[str] = Field(None, max_length=500)
    url_tripadvisor: Optional[str] = Field(None, max_length=500)
    url_opentable: Optional[str] = Field(None, max_length=500)
    url_delivery: Optional[str] = Field(None, max_length=500)
    
    ticket_promedio_objetivo: Optional[float] = Field(None, gt=0)
    rango_precio_objetivo: Optional[str] = Field(None, max_length=30)
    moneda: Optional[str] = Field(None, max_length=10)
    descripcion_concepto: Optional[str] = None
    palabras_clave: Optional[str] = Field(None, max_length=1000)


class PerfilDigitalResponse(PerfilDigitalBase):
    """Respuesta de perfil digital."""
    perfil_digital_id: str
    empresa_id: int
    unidad_negocio_id: int
    server_id: Optional[str] = None
    activo: bool = True
    fecha_creacion: datetime
    usuario_creacion: Optional[str] = None
    fecha_modificacion: Optional[datetime] = None
    usuario_modificacion: Optional[str] = None
    
    class Config:
        from_attributes = True


# =============================================================================
# COMPETIDORES
# =============================================================================

class CompetidorBase(BaseModel):
    """Campos comunes del competidor."""
    nombre_competidor: str = Field(..., max_length=200, description="Nombre del competidor")
    tipo_restaurante: Optional[TipoRestaurante] = None
    segmento_precio: Optional[SegmentoPrecio] = None
    ciudad: Optional[str] = Field(None, max_length=100)
    estado: Optional[str] = Field(None, max_length=100)
    pais: str = Field(default="México", max_length=50)
    zona_comercial: Optional[str] = Field(None, max_length=200)
    
    # URLs
    sitio_web: Optional[str] = Field(None, max_length=500)
    url_menu: Optional[str] = Field(None, max_length=500)
    url_google_maps: Optional[str] = Field(None, max_length=500)
    url_instagram: Optional[str] = Field(None, max_length=500)
    url_facebook: Optional[str] = Field(None, max_length=500)
    url_tripadvisor: Optional[str] = Field(None, max_length=500)
    url_opentable: Optional[str] = Field(None, max_length=500)
    
    # Notas
    notas: Optional[str] = Field(None, max_length=1000, description="Observaciones adicionales")
    
    # Clasificación
    es_competencia_directa: bool = Field(default=True, description="Es competencia directa")
    es_benchmark_aspiracional: bool = Field(default=False, description="Benchmark aspiracional")
    distancia_km: Optional[float] = Field(None, ge=0, description="Distancia en km")
    prioridad: int = Field(default=0, ge=0, description="Prioridad (0 = normal)")


class CompetidorCreate(CompetidorBase):
    """Request para crear competidor."""
    empresa_id: int = Field(..., gt=0, description="ID de la empresa")
    unidad_negocio_id: int = Field(..., gt=0, description="ID de la unidad de negocio")


class CompetidorUpdate(BaseModel):
    """Request para actualizar competidor."""
    nombre_competidor: Optional[str] = Field(None, max_length=200)
    tipo_restaurante: Optional[TipoRestaurante] = None
    segmento_precio: Optional[SegmentoPrecio] = None
    ciudad: Optional[str] = Field(None, max_length=100)
    estado: Optional[str] = Field(None, max_length=100)
    pais: Optional[str] = Field(None, max_length=50)
    zona_comercial: Optional[str] = Field(None, max_length=200)
    
    sitio_web: Optional[str] = Field(None, max_length=500)
    url_menu: Optional[str] = Field(None, max_length=500)
    url_google_maps: Optional[str] = Field(None, max_length=500)
    url_instagram: Optional[str] = Field(None, max_length=500)
    url_facebook: Optional[str] = Field(None, max_length=500)
    url_tripadvisor: Optional[str] = Field(None, max_length=500)
    url_opentable: Optional[str] = Field(None, max_length=500)
    
    notas: Optional[str] = Field(None, max_length=1000)
    
    es_competencia_directa: Optional[bool] = None
    es_benchmark_aspiracional: Optional[bool] = None
    distancia_km: Optional[float] = Field(None, ge=0)
    prioridad: Optional[int] = Field(None, ge=0)


class CompetidorResponse(CompetidorBase):
    """Respuesta de competidor."""
    competidor_id: str
    empresa_id: int
    unidad_negocio_id: int
    activo: bool = True
    fecha_creacion: datetime
    usuario_creacion: Optional[str] = None
    fecha_modificacion: Optional[datetime] = None
    usuario_modificacion: Optional[str] = None
    
    # Contador de items (agregado en queries)
    total_menu_items: int = 0
    
    class Config:
        from_attributes = True


# =============================================================================
# MENU ITEMS DE COMPETIDORES
# =============================================================================

class CompetidorMenuItemBase(BaseModel):
    """Campos comunes del item de menú de competidor."""
    nombre_producto_competidor: str = Field(..., max_length=300, description="Nombre del producto")
    categoria_competidor: Optional[str] = Field(None, max_length=100, description="Categoría en menú")
    descripcion: Optional[str] = Field(None, max_length=1000)
    precio: float = Field(..., gt=0, description="Precio observado")
    moneda: str = Field(default="MXN", max_length=10)
    
    # Trazabilidad de datos
    fuente_url: Optional[str] = Field(None, max_length=500, description="URL de donde se obtuvo")
    fecha_consulta: Optional[date] = Field(None, description="Fecha de consulta")
    metodo_obtencion: MetodoObtencion = Field(default=MetodoObtencion.MANUAL)
    confianza_dato: ConfianzaDato = Field(default=ConfianzaDato.MEDIA)
    es_dato_manual: bool = Field(default=True)
    es_dato_ia: bool = Field(default=False)
    
    # Datos adicionales
    payload_json: Optional[Dict[str, Any]] = Field(None, description="Datos adicionales JSON")


class CompetidorMenuItemCreate(CompetidorMenuItemBase):
    """Request para crear item de menú de competidor."""
    competidor_id: str = Field(..., description="UUID del competidor")


class CompetidorMenuItemUpdate(BaseModel):
    """Request para actualizar item de menú."""
    nombre_producto_competidor: Optional[str] = Field(None, max_length=300)
    categoria_competidor: Optional[str] = Field(None, max_length=100)
    descripcion: Optional[str] = Field(None, max_length=1000)
    precio: Optional[float] = Field(None, gt=0)
    moneda: Optional[str] = Field(None, max_length=10)
    
    fuente_url: Optional[str] = Field(None, max_length=500)
    fecha_consulta: Optional[date] = None
    metodo_obtencion: Optional[MetodoObtencion] = None
    confianza_dato: Optional[ConfianzaDato] = None
    es_dato_manual: Optional[bool] = None
    es_dato_ia: Optional[bool] = None
    payload_json: Optional[Dict[str, Any]] = None


class CompetidorMenuItemResponse(CompetidorMenuItemBase):
    """Respuesta de item de menú de competidor."""
    competidor_menu_item_id: str
    competidor_id: str
    activo: bool = True
    fecha_creacion: datetime
    usuario_creacion: Optional[str] = None
    
    # Info del competidor (agregada en queries)
    nombre_competidor: Optional[str] = None
    
    class Config:
        from_attributes = True


# =============================================================================
# BENCHMARK PRODUCTO
# =============================================================================

class PricingBenchmarkProductoBase(BaseModel):
    """Campos comunes del benchmark de producto."""
    producto_id: Optional[str] = Field(None, description="UUID del producto propio")
    codigo_producto: str = Field(..., max_length=100, description="Código del producto")
    server_id: str = Field(..., description="UUID del servidor")
    competidor_menu_item_id: str = Field(..., description="UUID del item de competidor")
    
    # Comparación
    similitud: float = Field(..., ge=0, le=100, description="Similitud 0-100%")
    tipo_comparacion: TipoComparacion = Field(default=TipoComparacion.PRODUCTO_SIMILAR)
    comentario_ia: Optional[str] = Field(None, description="Comentario generado por IA")
    
    # Validación
    validado_por_usuario: bool = Field(default=False)
    usuario_validacion: Optional[str] = Field(None, max_length=100)
    fecha_validacion: Optional[datetime] = None


class PricingBenchmarkProductoCreate(PricingBenchmarkProductoBase):
    """Request para crear benchmark de producto."""
    empresa_id: int = Field(..., gt=0)
    unidad_negocio_id: int = Field(..., gt=0)
    competidor_id: str = Field(..., description="UUID del competidor")


class PricingBenchmarkProductoUpdate(BaseModel):
    """Request para actualizar benchmark de producto."""
    similitud: Optional[float] = Field(None, ge=0, le=100)
    tipo_comparacion: Optional[TipoComparacion] = None
    comentario_ia: Optional[str] = None
    validado_por_usuario: Optional[bool] = None
    usuario_validacion: Optional[str] = Field(None, max_length=100)


class PricingBenchmarkProductoResponse(PricingBenchmarkProductoBase):
    """Respuesta de benchmark de producto."""
    benchmark_producto_id: str
    empresa_id: int
    unidad_negocio_id: int
    competidor_id: str
    activo: bool = True
    fecha_creacion: datetime
    usuario_creacion: Optional[str] = None
    fecha_modificacion: Optional[datetime] = None
    usuario_modificacion: Optional[str] = None
    
    # Info del competidor (agregada en queries)
    nombre_competidor: Optional[str] = None
    nombre_producto_competidor: Optional[str] = None
    precio_competidor: Optional[float] = None
    
    class Config:
        from_attributes = True


# =============================================================================
# PRECIOS SUGERIDOS - CÁLCULO BASE
# =============================================================================

class PrecioSugeridoCalcularRequest(BaseModel):
    """Request para calcular precio sugerido base (SIN IA)."""
    producto_id: Optional[str] = Field(None, description="UUID del producto")
    codigo_producto: str = Field(..., max_length=100, description="Código del producto")
    server_id: str = Field(..., description="UUID del servidor")
    
    # Motor a usar
    tipo_motor: TipoMotorPrecio = Field(
        default=TipoMotorPrecio.COSTO_MARGEN,
        description="Tipo de motor de cálculo"
    )
    
    # Parámetros para COSTO_MARGEN
    margen_objetivo: Optional[float] = Field(
        None,
        gt=0,
        lt=1,
        description="Margen objetivo (0.30 = 30%)"
    )
    
    # Parámetros para redondeo
    multiplo_redondeo: int = Field(default=5, ge=1, description="Múltiplo de redondeo")
    metodo_redondeo: str = Field(default="MAS_CERCANO", description="MAS_CERCANO, HACIA_ARRIBA, HACIA_ABAJO")
    
    @validator('margen_objetivo')
    def validar_margen(cls, v, values):
        tipo = values.get('tipo_motor')
        if tipo == TipoMotorPrecio.COSTO_MARGEN and v is None:
            raise ValueError("margen_objetivo es requerido para tipo COSTO_MARGEN")
        return v


class PrecioSugeridoCalcularResponse(BaseModel):
    """Respuesta del cálculo de precio sugerido base."""
    # Producto
    producto_id: Optional[str] = None
    codigo_producto: str
    nombre_producto: Optional[str] = None
    server_id: str
    
    # Motor utilizado
    tipo_motor: TipoMotorPrecio
    
    # Costo
    costo_producto: Optional[float] = None
    fuente_costo: Optional[str] = None
    
    # Impuesto
    tasa_impuesto: Optional[float] = None
    estado_fiscal: Optional[str] = None
    fuente_impuesto: Optional[str] = None
    
    # Cálculo
    margen_objetivo: Optional[float] = None
    precio_minimo_rentable: Optional[float] = None
    precio_con_impuesto: Optional[float] = None
    precio_sugerido: Optional[float] = None
    
    # Para vinos (regla existente)
    costo_base_vino: Optional[float] = None
    rango_aplicado: Optional[str] = None
    margen_multiplicador: Optional[float] = None
    
    # Redondeo
    multiplo_redondeo: int = 5
    metodo_redondeo: str = "MAS_CERCANO"
    
    # Estado
    estado: EstadoCalculo
    mensaje: Optional[str] = None
    permite_solicitud_cambio: bool = False
    
    # Trazabilidad
    fecha_calculo: datetime
    
    class Config:
        from_attributes = True


# =============================================================================
# BENCHMARK RESUMEN Y ESTADO DE PREPARACIÓN
# =============================================================================

class BenchmarkResumenResponse(BaseModel):
    """Resumen de benchmark para una unidad de negocio."""
    unidad_negocio_id: int
    empresa_id: int
    nombre_unidad: Optional[str] = None
    
    # Estadísticas de configuración
    competidores_configurados: int = 0
    competidores_directos: int = 0
    competidores_aspiracionales: int = 0
    
    # Estadísticas de datos
    items_competencia_capturados: int = 0
    items_alta_confianza: int = 0
    items_media_confianza: int = 0
    items_baja_confianza: int = 0
    
    # Productos mapeados
    productos_propios_total: int = 0
    productos_con_benchmark: int = 0
    productos_sin_benchmark: int = 0
    cobertura_benchmark: float = 0.0  # Porcentaje
    
    # Última actividad
    fecha_ultima_actualizacion: Optional[datetime] = None
    
    # Estado general
    estado: str = "SIN_CONFIGURAR"  # SIN_CONFIGURAR, PARCIAL, COMPLETO
    
    class Config:
        from_attributes = True


class BenchmarkEstadoPreparacionResponse(BaseModel):
    """Estado de preparación para ejecutar IA."""
    unidad_negocio_id: int
    empresa_id: int
    
    # Perfil digital
    perfil_digital_completo: bool = False
    urls_disponibles: List[str] = []
    urls_faltantes: List[str] = []
    
    # Competidores
    competidores_configurados: int = 0
    minimo_competidores_recomendado: int = 3
    competidores_con_menu: int = 0
    
    # Items de competencia
    items_capturados: int = 0
    minimo_items_recomendado: int = 10
    
    # Productos mapeados
    productos_mapeados: int = 0
    productos_validados: int = 0
    
    # Datos faltantes
    faltantes: List[str] = []
    
    # Veredicto
    listo_para_ia: bool = False
    razones_no_listo: List[str] = []
    
    # Recomendaciones
    recomendaciones: List[str] = []
    
    class Config:
        from_attributes = True


# =============================================================================
# LISTAS Y PAGINACIÓN
# =============================================================================

class PaginacionResponse(BaseModel):
    """Respuesta con paginación."""
    total: int
    page: int
    page_size: int
    total_pages: int


class PerfilesDigitalesListResponse(PaginacionResponse):
    """Lista paginada de perfiles digitales."""
    perfiles: List[PerfilDigitalResponse]


class CompetidoresListResponse(PaginacionResponse):
    """Lista paginada de competidores."""
    competidores: List[CompetidorResponse]


class MenuItemsListResponse(PaginacionResponse):
    """Lista paginada de menu items."""
    menu_items: List[CompetidorMenuItemResponse]


class BenchmarksListResponse(PaginacionResponse):
    """Lista paginada de benchmarks."""
    benchmarks: List[PricingBenchmarkProductoResponse]


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Enums
    'TipoRestaurante',
    'SegmentoPrecio',
    'MetodoObtencion',
    'ConfianzaDato',
    'TipoComparacion',
    'TipoMotorPrecio',
    'PosicionVsCompetencia',
    'EstadoCalculo',
    
    # Perfil Digital
    'PerfilDigitalCreate',
    'PerfilDigitalUpdate',
    'PerfilDigitalResponse',
    
    # Competidores
    'CompetidorCreate',
    'CompetidorUpdate',
    'CompetidorResponse',
    
    # Menu Items
    'CompetidorMenuItemCreate',
    'CompetidorMenuItemUpdate',
    'CompetidorMenuItemResponse',
    
    # Benchmark
    'PricingBenchmarkProductoCreate',
    'PricingBenchmarkProductoUpdate',
    'PricingBenchmarkProductoResponse',
    
    # Precios Sugeridos
    'PrecioSugeridoCalcularRequest',
    'PrecioSugeridoCalcularResponse',
    
    # Resumen y Estado
    'BenchmarkResumenResponse',
    'BenchmarkEstadoPreparacionResponse',
    
    # Listas
    'PerfilesDigitalesListResponse',
    'CompetidoresListResponse',
    'MenuItemsListResponse',
    'BenchmarksListResponse',
]
