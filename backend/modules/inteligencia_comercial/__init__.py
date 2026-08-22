from core.unidades_service import UnidadesService
from core.corporate_filters.service import CorporateFilterService
# Módulo Portal Inteligencia Comercial IA
# EDARSA HUB - Junio 2026

# Registra endpoints adicionales sobre el mismo router /inteligencia.
# La importación carga routes.py y agrega /sync/verificar y
# /sync/sincronizar-pendientes sin crear una segunda ruta paralela.
from . import sync_control as _sync_control  # noqa: F401,E402
