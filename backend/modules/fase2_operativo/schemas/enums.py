"""
Enumeraciones compartidas para el módulo operativo Fase 2A
CAB-003 | EDARSA HUB

Estas enumeraciones definen los estados y tipos válidos para el flujo
de trabajo de inventarios.
"""
from enum import Enum


class EstadoWorkflow(str, Enum):
    """Estados posibles de un workflow de inventario."""
    PENDIENTE_ASIGNACION = "PENDIENTE_ASIGNACION"
    EN_REVISION = "EN_REVISION"
    PENDIENTE_JUSTIFICACION = "PENDIENTE_JUSTIFICACION"
    JUSTIFICADO = "JUSTIFICADO"
    EN_AUDITORIA = "EN_AUDITORIA"
    CERRADO = "CERRADO"
    ESCALADO = "ESCALADO"


class TipoTarea(str, Enum):
    """Tipos de tarea que pueden asignarse."""
    REVISAR = "REVISAR"
    JUSTIFICAR = "JUSTIFICAR"
    AUDITAR = "AUDITAR"
    ESCALAR = "ESCALAR"


class EstadoTarea(str, Enum):
    """Estados posibles de una tarea."""
    PENDIENTE = "PENDIENTE"
    EN_PROGRESO = "EN_PROGRESO"
    COMPLETADA = "COMPLETADA"
    VENCIDA = "VENCIDA"


class TipoJustificacion(str, Enum):
    """
    Tipos de justificación según regla híbrida.
    - SIMPLE: Solo texto (diferencia <= umbral)
    - COMPLETA: Texto + evidencia obligatoria (diferencia > umbral)
    """
    SIMPLE = "SIMPLE"
    COMPLETA = "COMPLETA"


class DecisionAuditoria(str, Enum):
    """Decisiones posibles del auditor."""
    APROBADO = "APROBADO"
    RECHAZADO = "RECHAZADO"
    DEVUELTO_PARA_CORRECCION = "DEVUELTO_PARA_CORRECCION"
