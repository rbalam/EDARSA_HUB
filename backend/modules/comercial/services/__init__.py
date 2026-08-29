from core.unidades_service import UnidadesService
from core.corporate_filters.service import CorporateFilterService
"""
FASE 1C-3I-B/C: Services de Pricing y Benchmark

Módulos:
- pricing_schemas.py: Esquemas Pydantic
- perfil_unidad_service.py: Gestión de perfiles digitales
- competidores_service.py: Gestión de competidores y menu items
- benchmark_service.py: Mapeo de productos vs competencia
- pricing_sugerido_service.py: Cálculo de precios sugeridos (sin IA)
- pricing_ai_service.py: Integración GPT-5.2 para análisis IA
- impuestos_service.py: Resolución de tasas de impuesto
- precios_vinos_service.py: Cálculo de precios de vinos (regla de rangos)
"""

from .pricing_schemas import *  # noqa: F403
from .impuestos_service import *  # noqa: F403
from .precios_vinos_service import *  # noqa: F403

# Nuevos servicios FASE 1C-3I-B
from .perfil_unidad_service import *  # noqa: F403
from .competidores_service import *  # noqa: F403
from .benchmark_service import *  # noqa: F403
from .pricing_sugerido_service import *  # noqa: F403

# Servicio IA FASE 1C-3I-C
from .pricing_ai_service import *  # noqa: F403
