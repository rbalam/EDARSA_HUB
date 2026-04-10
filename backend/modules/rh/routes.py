"""
EDARSA HUB - RH Routes
======================
Endpoints del módulo de recursos humanos.

Funcionalidades planeadas:
- Catálogos RH (Colaboradores, Incidencias, Períodos)
- Integración con NomiPAQ
- Integración con Excel
- Flujo Kanban de nóminas
"""

from fastapi import APIRouter

router = APIRouter(prefix="/rh", tags=["Recursos Humanos"])
