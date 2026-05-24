"""
Modelos para sincronización de recetas, productos, insumos y costos.
FASE 1C-3B - Costos y Márgenes
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from datetime import datetime
from decimal import Decimal


@dataclass
class SyncRecetasConfig:
    """Configuración para sincronización de recetas"""
    server_ids: List[str]
    sync_familias: bool = True
    sync_productos: bool = True
    sync_insumos: bool = True
    sync_recetas: bool = True
    sync_elaborados: bool = True
    dry_run: bool = True
    

@dataclass
class SyncRecetasResult:
    """Resultado de sincronización de recetas"""
    sync_run_id: str
    success: bool
    is_dry_run: bool
    total_servidores: int = 0
    servidores_exitosos: int = 0
    servidores_con_error: int = 0
    
    # Conteos por tipo
    total_familias: int = 0
    total_subfamilias: int = 0
    total_productos: int = 0
    total_productos_con_receta: int = 0
    total_insumos: int = 0
    total_lineas_receta: int = 0
    total_elaborados: int = 0
    
    # Conteos de operaciones
    registros_insertados: int = 0
    registros_actualizados: int = 0
    registros_error: int = 0
    
    duration_seconds: float = 0.0
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    
    resultados_por_servidor: Dict = field(default_factory=dict)
    errores: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


@dataclass
class FamiliaSync:
    """Familia/Grupo de producto sincronizado"""
    codigo_fuente: str
    nombre: str
    descripcion: Optional[str] = None
    orden: int = 0


@dataclass
class SubFamiliaSync:
    """SubFamilia/SubGrupo de producto sincronizado"""
    codigo_fuente: str
    nombre: str
    familia_codigo_fuente: Optional[str] = None
    descripcion: Optional[str] = None
    orden: int = 0


@dataclass
class ProductoSync:
    """Producto sincronizado"""
    codigo_fuente: str
    nombre: str
    nombre_corto: Optional[str] = None
    familia_codigo_fuente: Optional[str] = None
    subfamilia_codigo_fuente: Optional[str] = None
    familia_nombre: Optional[str] = None
    subfamilia_nombre: Optional[str] = None
    precio_venta: Decimal = Decimal('0')
    precio_sin_impuestos: Decimal = Decimal('0')
    tasa_impuesto: Decimal = Decimal('0')
    tiene_receta: bool = False
    es_compuesto: bool = False
    unidad_venta: Optional[str] = None


@dataclass
class InsumoSync:
    """Insumo sincronizado"""
    codigo_fuente: str
    nombre: str
    unidad_medida: str
    costo: Decimal = Decimal('0')
    costo_promedio: Decimal = Decimal('0')
    ultimo_costo: Decimal = Decimal('0')
    costo_estandar: Decimal = Decimal('0')
    costo_con_impuestos: Decimal = Decimal('0')
    es_elaborado: bool = False
    rendimiento_elaborado: Optional[Decimal] = None
    grupo_codigo_fuente: Optional[str] = None
    grupo_nombre: Optional[str] = None


@dataclass
class RecetaLineaSync:
    """Línea de receta (producto → insumo)"""
    producto_codigo_fuente: str
    insumo_codigo_fuente: str
    insumo_nombre: str
    cantidad: Decimal
    unidad_medida: str
    costo_unitario: Decimal = Decimal('0')
    costo_total: Decimal = Decimal('0')
    es_elaborado: bool = False
    rendimiento_elaborado: Optional[Decimal] = None


@dataclass
class ElaboradoLineaSync:
    """Línea de elaborado (insumo elaborado → sub-insumo)"""
    insumo_elaborado_codigo_fuente: str
    insumo_componente_codigo_fuente: str
    insumo_componente_nombre: str
    cantidad: Decimal
    unidad_medida: str
    costo_unitario: Decimal = Decimal('0')
    costo_total: Decimal = Decimal('0')
