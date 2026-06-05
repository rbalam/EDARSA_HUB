"""
EDARSA HUB - CRM Trigger Routes
================================
Endpoints para gestión de triggers y automatizaciones avanzadas del CRM.
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
import logging

from core.security import get_current_user
from .trigger_service import (
    get_crm_trigger_service, 
    TriggerEvent, 
    TriggerAction
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/crm/triggers", tags=["CRM Triggers"])


# ==================== SCHEMAS ====================

class AccionTrigger(BaseModel):
    """Definición de una acción de trigger."""
    tipo: str = Field(..., description="Tipo de acción: CREAR_ACTIVIDAD, ENVIAR_EMAIL, etc.")
    titulo: Optional[str] = None
    descripcion: Optional[str] = None
    mensaje: Optional[str] = None
    dias_programar: Optional[int] = 1
    destinatario_email: Optional[str] = None
    telefono: Optional[str] = None
    usuario_destino_id: Optional[str] = None
    url: Optional[str] = None  # Para webhooks
    campo: Optional[str] = None  # Para actualizar campo
    valor: Optional[Any] = None


class CrearTriggerRequest(BaseModel):
    """Request para crear un trigger."""
    nombre: str = Field(..., min_length=3, max_length=200)
    tipo_evento: str = Field(..., description="Tipo de evento que dispara el trigger")
    condiciones: Optional[Dict[str, Any]] = Field(default={}, description="Condiciones JSON")
    acciones: List[AccionTrigger] = Field(..., min_items=1)
    prioridad: int = Field(default=100, ge=1, le=1000)


class DispatchEventRequest(BaseModel):
    """Request para despachar un evento manualmente."""
    tipo_evento: str
    entidad_id: str
    datos_evento: Dict[str, Any] = {}


# ==================== ENDPOINTS ====================

@router.get("/", summary="Listar Triggers")
async def listar_triggers(
    empresa_id: str = Query(...),
    activos_solo: bool = Query(default=True),
    current_user: Dict = Depends(get_current_user)
):
    """
    Lista todos los triggers de una empresa.
    
    Permisos: CRM_VER
    """
    service = get_crm_trigger_service()
    triggers = service.listar_triggers(empresa_id, activos_solo)
    
    return {
        "triggers": triggers,
        "total": len(triggers)
    }


@router.post("/", summary="Crear Trigger")
async def crear_trigger(
    empresa_id: str = Query(...),
    data: CrearTriggerRequest = ...,
    current_user: Dict = Depends(get_current_user)
):
    """
    Crea un nuevo trigger de automatización.
    
    Tipos de evento disponibles:
    - OPORTUNIDAD_CREADA
    - OPORTUNIDAD_ACTUALIZADA
    - ETAPA_CAMBIADA
    - OPORTUNIDAD_GANADA
    - OPORTUNIDAD_PERDIDA
    - ACTIVIDAD_VENCIDA
    - SLA_VENCIDO
    - MONTO_ACTUALIZADO
    - RESPONSABLE_CAMBIADO
    
    Tipos de acción disponibles:
    - CREAR_ACTIVIDAD
    - ENVIAR_EMAIL
    - ENVIAR_WHATSAPP
    - CREAR_NOTIFICACION
    - ACTUALIZAR_CAMPO
    - WEBHOOK
    - CREAR_TAREA_SEGUIMIENTO
    
    Permisos: CRM_ADMIN
    """
    try:
        # Validar tipo de evento
        try:
            evento = TriggerEvent(data.tipo_evento)
        except ValueError:
            raise HTTPException(
                status_code=400, 
                detail=f"Tipo de evento inválido: {data.tipo_evento}. "
                       f"Valores válidos: {[e.value for e in TriggerEvent]}"
            )
        
        # Validar tipos de acción
        for accion in data.acciones:
            try:
                TriggerAction(accion.tipo)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Tipo de acción inválido: {accion.tipo}. "
                           f"Valores válidos: {[a.value for a in TriggerAction]}"
                )
        
        service = get_crm_trigger_service()
        resultado = service.crear_trigger(
            empresa_id=empresa_id,
            nombre=data.nombre,
            tipo_evento=evento,
            acciones=[a.dict() for a in data.acciones],
            condiciones=data.condiciones,
            prioridad=data.prioridad,
            usuario_id=current_user.get('user_id')
        )
        
        if not resultado.get('success'):
            raise HTTPException(status_code=400, detail=resultado.get('error'))
        
        return resultado
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[CRM-Triggers] Error creando trigger: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{trigger_id}/toggle", summary="Activar/Desactivar Trigger")
async def toggle_trigger(
    trigger_id: str,
    activo: bool = Query(...),
    current_user: Dict = Depends(get_current_user)
):
    """
    Activa o desactiva un trigger.
    
    Permisos: CRM_ADMIN
    """
    service = get_crm_trigger_service()
    resultado = service.activar_desactivar_trigger(trigger_id, activo)
    
    if not resultado.get('success'):
        raise HTTPException(status_code=400, detail=resultado.get('error'))
    
    return resultado


@router.post("/dispatch", summary="Despachar Evento Manual")
async def dispatch_event(
    empresa_id: str = Query(...),
    data: DispatchEventRequest = ...,
    current_user: Dict = Depends(get_current_user)
):
    """
    Despacha un evento manualmente para probar triggers.
    
    Útil para:
    - Testing de triggers
    - Disparar acciones manualmente
    - Debugging
    
    Permisos: CRM_ADMIN
    """
    try:
        evento = TriggerEvent(data.tipo_evento)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Tipo de evento inválido: {data.tipo_evento}"
        )
    
    service = get_crm_trigger_service()
    resultados = service.dispatch_event(
        evento=evento,
        empresa_id=empresa_id,
        entidad_id=data.entidad_id,
        datos_evento=data.datos_evento,
        usuario_id=current_user.get('user_id')
    )
    
    return {
        "evento": data.tipo_evento,
        "entidad_id": data.entidad_id,
        "triggers_ejecutados": len(resultados),
        "resultados": resultados
    }


@router.get("/eventos", summary="Listar Tipos de Evento")
async def listar_tipos_evento():
    """Lista todos los tipos de evento disponibles para triggers."""
    return {
        "eventos": [
            {
                "valor": e.value,
                "descripcion": _get_descripcion_evento(e)
            }
            for e in TriggerEvent
        ]
    }


@router.get("/acciones", summary="Listar Tipos de Acción")
async def listar_tipos_accion():
    """Lista todos los tipos de acción disponibles para triggers."""
    return {
        "acciones": [
            {
                "valor": a.value,
                "descripcion": _get_descripcion_accion(a),
                "parametros": _get_parametros_accion(a)
            }
            for a in TriggerAction
        ]
    }


def _get_descripcion_evento(evento: TriggerEvent) -> str:
    """Obtiene descripción de un tipo de evento."""
    descripciones = {
        TriggerEvent.OPORTUNIDAD_CREADA: "Se dispara cuando se crea una nueva oportunidad",
        TriggerEvent.OPORTUNIDAD_ACTUALIZADA: "Se dispara cuando se actualiza cualquier campo de una oportunidad",
        TriggerEvent.ETAPA_CAMBIADA: "Se dispara cuando una oportunidad cambia de etapa en el pipeline",
        TriggerEvent.OPORTUNIDAD_GANADA: "Se dispara cuando una oportunidad se marca como ganada",
        TriggerEvent.OPORTUNIDAD_PERDIDA: "Se dispara cuando una oportunidad se marca como perdida",
        TriggerEvent.ACTIVIDAD_VENCIDA: "Se dispara cuando una actividad de seguimiento ha vencido",
        TriggerEvent.SLA_VENCIDO: "Se dispara cuando una oportunidad supera el tiempo máximo en una etapa",
        TriggerEvent.MONTO_ACTUALIZADO: "Se dispara cuando se modifica el monto estimado de una oportunidad",
        TriggerEvent.RESPONSABLE_CAMBIADO: "Se dispara cuando se cambia el responsable de una oportunidad"
    }
    return descripciones.get(evento, "Sin descripción")


def _get_descripcion_accion(accion: TriggerAction) -> str:
    """Obtiene descripción de un tipo de acción."""
    descripciones = {
        TriggerAction.CREAR_ACTIVIDAD: "Crea una actividad de seguimiento automática",
        TriggerAction.ENVIAR_EMAIL: "Envía un correo electrónico al contacto o responsable",
        TriggerAction.ENVIAR_WHATSAPP: "Envía un mensaje de WhatsApp",
        TriggerAction.CREAR_NOTIFICACION: "Crea una notificación interna en el sistema",
        TriggerAction.ACTUALIZAR_CAMPO: "Actualiza un campo de la oportunidad",
        TriggerAction.WEBHOOK: "Envía datos a una URL externa (webhook)",
        TriggerAction.CREAR_TAREA_SEGUIMIENTO: "Crea una tarea de seguimiento con recordatorio"
    }
    return descripciones.get(accion, "Sin descripción")


def _get_parametros_accion(accion: TriggerAction) -> List[Dict]:
    """Obtiene parámetros requeridos para un tipo de acción."""
    parametros = {
        TriggerAction.CREAR_ACTIVIDAD: [
            {"nombre": "titulo", "tipo": "string", "requerido": False},
            {"nombre": "descripcion", "tipo": "string", "requerido": False},
            {"nombre": "dias_programar", "tipo": "int", "requerido": False, "default": 1},
            {"nombre": "tipo_actividad_id", "tipo": "int", "requerido": False, "default": 1}
        ],
        TriggerAction.ENVIAR_EMAIL: [
            {"nombre": "destinatario_email", "tipo": "string", "requerido": False},
            {"nombre": "asunto", "tipo": "string", "requerido": True},
            {"nombre": "cuerpo_html", "tipo": "string", "requerido": True}
        ],
        TriggerAction.ENVIAR_WHATSAPP: [
            {"nombre": "telefono", "tipo": "string", "requerido": False},
            {"nombre": "mensaje", "tipo": "string", "requerido": True}
        ],
        TriggerAction.CREAR_NOTIFICACION: [
            {"nombre": "titulo", "tipo": "string", "requerido": True},
            {"nombre": "mensaje", "tipo": "string", "requerido": True},
            {"nombre": "usuario_destino_id", "tipo": "string", "requerido": False}
        ],
        TriggerAction.ACTUALIZAR_CAMPO: [
            {"nombre": "campo", "tipo": "string", "requerido": True},
            {"nombre": "valor", "tipo": "any", "requerido": True}
        ],
        TriggerAction.WEBHOOK: [
            {"nombre": "url", "tipo": "string", "requerido": True},
            {"nombre": "headers", "tipo": "object", "requerido": False}
        ],
        TriggerAction.CREAR_TAREA_SEGUIMIENTO: [
            {"nombre": "titulo", "tipo": "string", "requerido": False},
            {"nombre": "descripcion", "tipo": "string", "requerido": False},
            {"nombre": "dias_programar", "tipo": "int", "requerido": False, "default": 3},
            {"nombre": "prioridad", "tipo": "string", "requerido": False, "default": "MEDIA"}
        ]
    }
    return parametros.get(accion, [])
