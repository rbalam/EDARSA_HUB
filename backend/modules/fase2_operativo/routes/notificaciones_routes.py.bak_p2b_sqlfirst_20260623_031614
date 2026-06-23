from core.unidades_service import UnidadesService
from core.corporate_filters.service import CorporateFilterService
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
    SQL-First: fuente canónica EDARSAHUB.Operativo_Notificaciones_Log (sin MongoDB).
    """
    import asyncio
    from core.sql_first.db import get_sql_connection

    where = ["1=1"]
    params: list = []
    if tipo_evento:
        where.append("TipoEvento = %s"); params.append(tipo_evento)
    if workflow_id:
        where.append("WorkflowID = %s"); params.append(workflow_id)
    if estado:
        where.append("Estado = %s"); params.append(estado)
    where_sql = " AND ".join(where)

    def _run():
        conn = get_sql_connection()
        cur = conn.cursor(as_dict=True)
        cur.execute(f"SELECT COUNT(*) AS total FROM Operativo_Notificaciones_Log WHERE {where_sql}", tuple(params))
        total = cur.fetchone()["total"]
        cur.execute(f"""
            SELECT NotificacionID AS id, TipoEvento AS tipo_evento, WorkflowID AS workflow_id,
                   TareaID AS tarea_id, Destinatario AS destinatario, DestinatarioEmail AS destinatario_email,
                   Titulo AS titulo, Mensaje AS mensaje, Estado AS estado, Canal AS canal,
                   FechaEnvio AS fecha_envio, ErrorMensaje AS error
            FROM Operativo_Notificaciones_Log
            WHERE {where_sql}
            ORDER BY FechaEnvio DESC
            OFFSET 0 ROWS FETCH NEXT %s ROWS ONLY
        """, tuple(params) + (limit,))
        rows = list(cur.fetchall())
        cur.close(); conn.close()
        return total, rows

    try:
        total, items = await asyncio.get_event_loop().run_in_executor(None, _run)
    except Exception as e:
        logger.error(f"[NOTIF_LOG] Error SQL: {e}")
        total, items = 0, []

    return {"items": items, "total": total}


@router.post("/verificar-vencidas")
async def verificar_tareas_vencidas(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Verifica tareas vencidas y envía notificaciones.
    
    Este endpoint puede ser invocado manualmente o por un cron externo cada hora.
    NOTA: La detección de tareas vencidas se realiza ahora vía el módulo SLA
    (SQL-First). El almacén MongoDB fue deprecado; si no hay backend de datos
    disponible, retorna un resultado vacío en lugar de fallar.
    """
    from ..db_utils import get_database
    db = get_database()
    
    if db is None:
        logger.info("[NOTIF] verificar-vencidas: almacén operativo deprecado (NO-MONGO). Use el módulo SLA.")
        return {
            "tareas_verificadas": 0,
            "notificaciones_enviadas": 0,
            "errores": 0,
            "detalles": [],
            "mensaje": "Detección de vencidas migrada al módulo SLA (SQL-First)."
        }
    
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
