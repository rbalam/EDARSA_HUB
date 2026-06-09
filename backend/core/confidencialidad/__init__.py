"""
Capa central de Confidencialidad / Anonimización (regla de centralización).
============================================================================
Un único punto de enmascaramiento para TODO el Portal de Inteligencia Comercial:
el backend decide qué nombres reales puede ver el usuario y enmascara el resto
ANTES de responder. El frontend NUNCA recibe nombres reales sin permiso.

NO-LIVE, sin hardcode de identidades (los nombres vienen de SQL canónico).
"""
from core.confidencialidad.anonymizer import (
    ConfidentialityContext,
    AnonymizerService,
    NivelConfidencialidad,
)

__all__ = [
    "ConfidentialityContext",
    "AnonymizerService",
    "NivelConfidencialidad",
]
