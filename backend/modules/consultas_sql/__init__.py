"""
EDARSA HUB - Módulo Consultas SQL (SQL-First)
=============================================
FASE 3: Repository SQL-First para lectura del catálogo de consultas
desde las tablas ConsultasSQL_* de EDARSAHUB.

PROPÓSITO:
- Leer consultas desde EDARSAHUB SQL (no desde código/MongoDB)
- Validar seguridad de consultas SQL antes de ejecución
- Preparar contexto de ejecución para endpoints futuros
- Mantener legacy funcionando sin cambios

COMPONENTES:
- models.py: Modelos Pydantic para consultas y parámetros
- validator.py: Validador estricto de SQL (solo SELECT/WITH)
- repository.py: Acceso a datos desde ConsultasSQL_*
- service.py: Lógica de negocio para consultas

CREADO: FASE 3 - Mayo 2026
AUTOR: E1 Agent
"""

from .models import (
    ConsultaSQLCatalogo,
    ConsultaSQLParametro,
    ConsultaSQLVersion,
    ConsultaSQLServidor,
    ConsultaSQLFilter,
    ConsultaSQLValidationResult,
)
from .validator import SQLValidator
from .repository import ConsultasSQLRepository
from .service import ConsultasSQLService

__all__ = [
    # Modelos
    'ConsultaSQLCatalogo',
    'ConsultaSQLParametro',
    'ConsultaSQLVersion',
    'ConsultaSQLServidor',
    'ConsultaSQLFilter',
    'ConsultaSQLValidationResult',
    # Validador
    'SQLValidator',
    # Repository
    'ConsultasSQLRepository',
    # Service
    'ConsultasSQLService',
]
