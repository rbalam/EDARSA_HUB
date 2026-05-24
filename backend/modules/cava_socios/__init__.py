"""
EDARSA HUB - Módulo Cava de Socios
===================================
Ubicación ERP: 07. Cava de Socios / Socios Cava
Tipo: Módulo principal (Inventario en custodia de terceros)
Fuente de verdad: EDARSAHUB SQL Server
"""

from .service import CavaSociosService, get_cava_socios_service
from .routes import router

__all__ = ['CavaSociosService', 'get_cava_socios_service', 'router']
