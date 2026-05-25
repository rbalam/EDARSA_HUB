"""
FASE 1C-3I-B: Services de Pricing y Benchmark

Módulos:
- pricing_schemas.py: Esquemas Pydantic
- perfil_unidad_service.py: Gestión de perfiles digitales
- competidores_service.py: Gestión de competidores y menu items
- benchmark_service.py: Mapeo de productos vs competencia
- pricing_sugerido_service.py: Cálculo de precios sugeridos
- impuestos_service.py: Resolución de tasas de impuesto
- precios_vinos_service.py: Cálculo de precios de vinos (regla de rangos)
"""

from .pricing_schemas import *
from .impuestos_service import *
from .precios_vinos_service import *

# Nuevos servicios FASE 1C-3I-B
from .perfil_unidad_service import *
from .competidores_service import *
from .benchmark_service import *
from .pricing_sugerido_service import *
