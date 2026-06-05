"""
Rutas de Notificaciones - API para gestión de notificaciones.
CAB-003 | Fase 2B.1
PROTEGIDO CON RBAC (Fase 3.1)
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone, timedelta
import logging

from ..services.notification_service import get_notification_service
from ..services.email_service import get_email_service

# RBAC - Fase 3.1
from core.security import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/notificaciones", tags=["Notificaciones"])


@router.get("/status")
async def get_notification_status(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Obtiene el estado del servicio de notificaciones.
    """
    email_service = get_email_service()
    
    return {
        "email": {
            "configured": email_service.is_configured(),
            "enabled": email_service.enabled,
            "from_email": email_service.from_email
        },
        "status": "ok"
    }


@router.get("/log")
async def get_notification_log(
    tipo_evento: Optional[str] = None,
    workflow_id: Optional[str] = None,
    estado: Optional[str] = None,
    limit: int = Query(default=50, le=200),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Obtiene el log de notificaciones enviadas.
    """
    from ..db_utils import get_database
    db = get_database()
    
    filtro = {}
    if tipo_evento:
        filtro["tipo_evento"] = tipo_evento
    if workflow_id:
        filtro["workflow_id"] = workflow_id
    if estado:
        filtro["estado"] = estado
    
    # Usar método síncrono para MongoDB síncrono
    items = list(db.notificaciones_log.find(
        filtro,
        {"_id": 0}
    ).sort("fecha_envio", -1).limit(limit))
    
    total = db.notificaciones_log.count_documents(filtro)
    
    return {
        "items": items,
        "total": total
    }


@router.post("/verificar-vencidas")
async def verificar_tareas_vencidas(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Verifica tareas vencidas y envía notificaciones.
    
    Este endpoint puede ser invocado manualmente o por un cron externo cada hora.
    """
    from ..db_utils import get_database
    db = get_database()
    
    notification_service = get_notification_service(db)
    
    ahora = datetime.now(timezone.utc)
    
    # Buscar tareas vencidas que no estén completadas ni canceladas
    # y que no hayan sido notificadas recientemente (últimas 6 horas)
    hace_6_horas = (ahora - timedelta(hours=6)).isoformat()
    
    # Primero actualizar el campo vencida en tareas (síncrono)
    db.tareas_inventario.update_many(
        {
            "fecha_limite": {"$lt": ahora.isoformat()},
            "estado_tarea": {"$nin": ["COMPLETADA", "CANCELADA"]},
            "vencida": {"$ne": True}
        },
        {"$set": {"vencida": True}}
    )
    
    # Buscar tareas vencidas para notificar
    # Excluir las que ya recibieron notificación de vencimiento en las últimas 6 horas
    tareas_notificadas_ids = []
    notificaciones_recientes = db.notificaciones_log.find(
        {
            "tipo_evento": "TAREA_VENCIDA",
            "fecha_envio": {"$gte": hace_6_horas}
        },
        {"tarea_id": 1}
    )
    for n in notificaciones_recientes:
        if n.get("tarea_id"):
            tareas_notificadas_ids.append(n["tarea_id"])
    
    # Buscar tareas vencidas
    filtro_tareas = {
        "vencida": True,
        "estado_tarea": {"$nin": ["COMPLETADA", "CANCELADA"]}
    }
    if tareas_notificadas_ids:
        filtro_tareas["id"] = {"$nin": tareas_notificadas_ids}
    
    tareas_vencidas = list(db.tareas_inventario.find(filtro_tareas, {"_id": 0}).limit(50))
    
    resultados = {
        "tareas_verificadas": len(tareas_vencidas),
        "notificaciones_enviadas": 0,
        "errores": 0,
        "detalles": []
    }
    
    for tarea in tareas_vencidas:
        # Calcular días vencida
        try:
            fecha_limite = datetime.fromisoformat(tarea.get("fecha_limite", "").replace("Z", "+00:00"))
            dias_vencida = (ahora - fecha_limite).days
        except Exception:
            dias_vencida = 1
        
        # Obtener email del usuario asignado
        usuario_id = tarea.get("usuario_asignado_id")
        if not usuario_id:
            continue
        
        usuario = db.users.find_one({"id": usuario_id}, {"_id": 0, "email": 1, "name": 1})
        if not usuario or not usuario.get("email"):
            continue
        
        # Enviar notificación
        resultado = await notification_service.notificar_tarea_vencida(
            tarea_id=tarea.get("id", ""),
            workflow_id=tarea.get("workflow_id", ""),
            tipo_tarea=tarea.get("tipo_tarea", ""),
            titulo=tarea.get("titulo", ""),
            fecha_limite=tarea.get("fecha_limite", ""),
            dias_vencida=dias_vencida,
            destinatario_email=usuario.get("email"),
            destinatario_nombre=usuario.get("name", "Usuario")
        )
        
        if resultado.get("notificado"):
            resultados["notificaciones_enviadas"] += 1
        else:
            resultados["errores"] += 1
        
        resultados["detalles"].append({
            "tarea_id": tarea.get("id"),
            "notificado": resultado.get("notificado"),
            "error": resultado.get("error")
        })
    
    logger.info(f"Verificación de vencidas: {resultados['tareas_verificadas']} tareas, {resultados['notificaciones_enviadas']} notificadas")
    
    return resultados


@router.post("/test-email")
async def test_email(
    destinatario: str = Query(..., description="Email de destino para prueba"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Envía un email de prueba para verificar la configuración.
    """
    email_service = get_email_service()
    
    if not email_service.is_configured():
        return {
            "success": False,
            "message": "Servicio de email no configurado",
            "configured": False,
            "enabled": email_service.enabled,
            "api_key_present": bool(email_service.api_key)
        }
    
    resultado = await email_service.enviar_email(
        destinatario=destinatario,
        asunto="EDARSA HUB - Email de Prueba",
        contenido_html="""
        <html>
        <body style="font-family: Arial, sans-serif; padding: 20px;">
            <h1 style="color: #1e40af;">Email de Prueba</h1>
            <p>Este es un email de prueba del sistema EDARSA HUB.</p>
            <p>Si recibes este mensaje, la configuración de SendGrid está funcionando correctamente.</p>
            <hr>
            <p style="color: #64748b; font-size: 12px;">
                Enviado desde EDARSA HUB - Sistema de Gestión Operativa
            </p>
        </body>
        </html>
        """
    )
    
    return resultado
