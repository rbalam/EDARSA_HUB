"""
Notification Service - Orquestación de notificaciones.
CAB-003 | Fase 2B.1

Gestiona el envío de notificaciones para eventos del sistema.
"""

import logging
from typing import Optional, Dict, List
from datetime import datetime, timezone
import uuid

from .email_service import get_email_service

logger = logging.getLogger(__name__)


# Tipos de eventos soportados
EVENTO_WORKFLOW_CREADO = "WORKFLOW_CREADO"
EVENTO_TAREA_ASIGNADA = "TAREA_ASIGNADA"
EVENTO_TAREA_VENCIDA = "TAREA_VENCIDA"


class NotificationService:
    """
    Servicio de orquestación de notificaciones.
    
    Recibe eventos y coordina el envío de notificaciones
    por los canales configurados (email, y en futuro WhatsApp).
    """
    
    def __init__(self, db):
        self.db = db
        self.email_service = get_email_service()
        self.collection = db.notificaciones_log
    
    async def notificar_workflow_creado(
        self,
        workflow_id: str,
        sucursal_nombre: str,
        almacen_nombre: str,
        total_productos: int,
        valor_total: float,
        destinatario_email: str,
        destinatario_nombre: str
    ) -> Dict:
        """
        Envía notificación de workflow creado.
        
        IMPORTANTE: Esta función NO debe lanzar excepciones.
        Cualquier error se registra pero no interrumpe el flujo principal.
        """
        resultado = {
            "tipo_evento": EVENTO_WORKFLOW_CREADO,
            "workflow_id": workflow_id,
            "notificado": False,
            "error": None
        }
        
        try:
            # Generar contenido del email
            asunto = f"Nuevo workflow de diferencias - {sucursal_nombre}"
            
            contenido_html = self._generar_html_workflow_creado(
                workflow_id=workflow_id,
                sucursal_nombre=sucursal_nombre,
                almacen_nombre=almacen_nombre,
                total_productos=total_productos,
                valor_total=valor_total,
                destinatario_nombre=destinatario_nombre
            )
            
            # Enviar email
            email_resultado = await self.email_service.enviar_email(
                destinatario=destinatario_email,
                asunto=asunto,
                contenido_html=contenido_html,
                metadata={"workflow_id": workflow_id}
            )
            
            resultado["notificado"] = email_resultado.get("success", False)
            resultado["email_resultado"] = email_resultado
            
            # Registrar en log
            await self._registrar_notificacion(
                tipo_evento=EVENTO_WORKFLOW_CREADO,
                workflow_id=workflow_id,
                tarea_id=None,
                destinatario=destinatario_email,
                canal="email",
                asunto=asunto,
                estado="enviado" if resultado["notificado"] else "fallido",
                error=email_resultado.get("error"),
                metadata={
                    "sucursal": sucursal_nombre,
                    "almacen": almacen_nombre,
                    "total_productos": total_productos,
                    "valor_total": valor_total
                }
            )
            
            if resultado["notificado"]:
                logger.info(f"✅ Notificación WORKFLOW_CREADO enviada: {workflow_id}")
            else:
                logger.warning(f"⚠️ Notificación WORKFLOW_CREADO no enviada: {workflow_id}")
            
        except Exception as e:
            resultado["error"] = str(e)
            logger.error(f"❌ Error en notificación WORKFLOW_CREADO: {e}")
            
            # Registrar error
            try:
                await self._registrar_notificacion(
                    tipo_evento=EVENTO_WORKFLOW_CREADO,
                    workflow_id=workflow_id,
                    tarea_id=None,
                    destinatario=destinatario_email,
                    canal="email",
                    asunto=f"Nuevo workflow de diferencias - {sucursal_nombre}",
                    estado="error",
                    error=str(e),
                    metadata={}
                )
            except Exception:
                pass
        
        return resultado
    
    async def notificar_tarea_asignada(
        self,
        tarea_id: str,
        workflow_id: str,
        tipo_tarea: str,
        titulo: str,
        descripcion: str,
        fecha_limite: str,
        destinatario_email: str,
        destinatario_nombre: str
    ) -> Dict:
        """
        Envía notificación de tarea asignada.
        
        IMPORTANTE: Esta función NO debe lanzar excepciones.
        """
        resultado = {
            "tipo_evento": EVENTO_TAREA_ASIGNADA,
            "tarea_id": tarea_id,
            "notificado": False,
            "error": None
        }
        
        try:
            asunto = f"Nueva tarea asignada - {tipo_tarea}"
            
            contenido_html = self._generar_html_tarea_asignada(
                tarea_id=tarea_id,
                workflow_id=workflow_id,
                tipo_tarea=tipo_tarea,
                titulo=titulo,
                descripcion=descripcion,
                fecha_limite=fecha_limite,
                destinatario_nombre=destinatario_nombre
            )
            
            email_resultado = await self.email_service.enviar_email(
                destinatario=destinatario_email,
                asunto=asunto,
                contenido_html=contenido_html,
                metadata={"tarea_id": tarea_id, "workflow_id": workflow_id}
            )
            
            resultado["notificado"] = email_resultado.get("success", False)
            resultado["email_resultado"] = email_resultado
            
            await self._registrar_notificacion(
                tipo_evento=EVENTO_TAREA_ASIGNADA,
                workflow_id=workflow_id,
                tarea_id=tarea_id,
                destinatario=destinatario_email,
                canal="email",
                asunto=asunto,
                estado="enviado" if resultado["notificado"] else "fallido",
                error=email_resultado.get("error"),
                metadata={"tipo_tarea": tipo_tarea, "titulo": titulo}
            )
            
            if resultado["notificado"]:
                logger.info(f"✅ Notificación TAREA_ASIGNADA enviada: {tarea_id}")
            
        except Exception as e:
            resultado["error"] = str(e)
            logger.error(f"❌ Error en notificación TAREA_ASIGNADA: {e}")
            
            try:
                await self._registrar_notificacion(
                    tipo_evento=EVENTO_TAREA_ASIGNADA,
                    workflow_id=workflow_id,
                    tarea_id=tarea_id,
                    destinatario=destinatario_email,
                    canal="email",
                    asunto=f"Nueva tarea asignada - {tipo_tarea}",
                    estado="error",
                    error=str(e),
                    metadata={}
                )
            except Exception:
                pass
        
        return resultado
    
    async def notificar_tarea_vencida(
        self,
        tarea_id: str,
        workflow_id: str,
        tipo_tarea: str,
        titulo: str,
        fecha_limite: str,
        dias_vencida: int,
        destinatario_email: str,
        destinatario_nombre: str,
        supervisor_email: Optional[str] = None
    ) -> Dict:
        """
        Envía notificación de tarea vencida.
        
        IMPORTANTE: Esta función NO debe lanzar excepciones.
        """
        resultado = {
            "tipo_evento": EVENTO_TAREA_VENCIDA,
            "tarea_id": tarea_id,
            "notificado": False,
            "error": None
        }
        
        try:
            asunto = "⚠️ Tarea vencida - Acción requerida"
            
            contenido_html = self._generar_html_tarea_vencida(
                tarea_id=tarea_id,
                workflow_id=workflow_id,
                tipo_tarea=tipo_tarea,
                titulo=titulo,
                fecha_limite=fecha_limite,
                dias_vencida=dias_vencida,
                destinatario_nombre=destinatario_nombre
            )
            
            # Enviar al asignado
            email_resultado = await self.email_service.enviar_email(
                destinatario=destinatario_email,
                asunto=asunto,
                contenido_html=contenido_html,
                destinatarios_cc=[supervisor_email] if supervisor_email else None,
                metadata={"tarea_id": tarea_id}
            )
            
            resultado["notificado"] = email_resultado.get("success", False)
            resultado["email_resultado"] = email_resultado
            
            await self._registrar_notificacion(
                tipo_evento=EVENTO_TAREA_VENCIDA,
                workflow_id=workflow_id,
                tarea_id=tarea_id,
                destinatario=destinatario_email,
                canal="email",
                asunto=asunto,
                estado="enviado" if resultado["notificado"] else "fallido",
                error=email_resultado.get("error"),
                metadata={"dias_vencida": dias_vencida, "supervisor_notificado": bool(supervisor_email)}
            )
            
            if resultado["notificado"]:
                logger.info(f"✅ Notificación TAREA_VENCIDA enviada: {tarea_id}")
            
        except Exception as e:
            resultado["error"] = str(e)
            logger.error(f"❌ Error en notificación TAREA_VENCIDA: {e}")
            
            try:
                await self._registrar_notificacion(
                    tipo_evento=EVENTO_TAREA_VENCIDA,
                    workflow_id=workflow_id,
                    tarea_id=tarea_id,
                    destinatario=destinatario_email,
                    canal="email",
                    asunto="Tarea vencida - Acción requerida",
                    estado="error",
                    error=str(e),
                    metadata={}
                )
            except Exception:
                pass
        
        return resultado
    
    async def _registrar_notificacion(
        self,
        tipo_evento: str,
        workflow_id: Optional[str],
        tarea_id: Optional[str],
        destinatario: str,
        canal: str,
        asunto: str,
        estado: str,
        error: Optional[str],
        metadata: Dict
    ):
        """Registra una notificación en el log."""
        try:
            doc = {
                "id": str(uuid.uuid4()),
                "tipo_evento": tipo_evento,
                "workflow_id": workflow_id,
                "tarea_id": tarea_id,
                "destinatario": destinatario,
                "canal": canal,
                "asunto": asunto,
                "estado": estado,
                "error": error,
                "metadata": metadata,
                "fecha_envio": datetime.now(timezone.utc).isoformat()
            }
            await self.collection.insert_one(doc)
        except Exception as e:
            logger.error(f"Error registrando notificación en log: {e}")
    
    def _generar_html_workflow_creado(
        self,
        workflow_id: str,
        sucursal_nombre: str,
        almacen_nombre: str,
        total_productos: int,
        valor_total: float,
        destinatario_nombre: str
    ) -> str:
        """Genera HTML para email de workflow creado."""
        return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: #1e40af; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }}
        .content {{ background: #f8fafc; padding: 20px; border: 1px solid #e2e8f0; }}
        .highlight {{ background: #fef3c7; padding: 15px; border-radius: 8px; margin: 15px 0; }}
        .metrics {{ display: flex; gap: 20px; margin: 15px 0; }}
        .metric {{ background: white; padding: 15px; border-radius: 8px; border: 1px solid #e2e8f0; flex: 1; text-align: center; }}
        .metric-value {{ font-size: 24px; font-weight: bold; color: #1e40af; }}
        .metric-label {{ font-size: 12px; color: #64748b; }}
        .footer {{ text-align: center; padding: 15px; font-size: 12px; color: #64748b; }}
        .btn {{ display: inline-block; background: #1e40af; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; margin-top: 15px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Nuevo Workflow de Diferencias</h1>
    </div>
    <div class="content">
        <p>Hola <strong>{destinatario_nombre}</strong>,</p>
        
        <p>Se ha detectado un nuevo análisis de inventario con diferencias que requiere tu atención.</p>
        
        <div class="highlight">
            <strong>📍 Ubicación:</strong> {sucursal_nombre} / {almacen_nombre}
        </div>
        
        <table style="width:100%; margin: 15px 0;">
            <tr>
                <td style="padding: 10px; background: white; border-radius: 8px; text-align: center; border: 1px solid #e2e8f0;">
                    <div style="font-size: 24px; font-weight: bold; color: #1e40af;">{total_productos}</div>
                    <div style="font-size: 12px; color: #64748b;">Productos con diferencia</div>
                </td>
                <td style="width: 10px;"></td>
                <td style="padding: 10px; background: white; border-radius: 8px; text-align: center; border: 1px solid #e2e8f0;">
                    <div style="font-size: 24px; font-weight: bold; color: #dc2626;">${valor_total:,.2f}</div>
                    <div style="font-size: 12px; color: #64748b;">Valor total</div>
                </td>
            </tr>
        </table>
        
        <p>Por favor revisa las diferencias y proporciona las justificaciones correspondientes.</p>
        
        <p style="font-size: 12px; color: #64748b;">
            <strong>ID del workflow:</strong> {workflow_id[:12]}...
        </p>
    </div>
    <div class="footer">
        EDARSA HUB - Sistema de Gestión Operativa<br>
        Este es un mensaje automático, no responder a este correo.
    </div>
</body>
</html>
"""
    
    def _generar_html_tarea_asignada(
        self,
        tarea_id: str,
        workflow_id: str,
        tipo_tarea: str,
        titulo: str,
        descripcion: str,
        fecha_limite: str,
        destinatario_nombre: str
    ) -> str:
        """Genera HTML para email de tarea asignada."""
        # Formatear fecha
        try:
            from datetime import datetime
            fecha_obj = datetime.fromisoformat(fecha_limite.replace('Z', '+00:00'))
            fecha_formateada = fecha_obj.strftime('%d/%m/%Y')
        except Exception:
            fecha_formateada = fecha_limite[:10] if fecha_limite else 'No definida'
        
        return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: #7c3aed; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }}
        .content {{ background: #f8fafc; padding: 20px; border: 1px solid #e2e8f0; }}
        .task-box {{ background: white; padding: 20px; border-radius: 8px; border-left: 4px solid #7c3aed; margin: 15px 0; }}
        .deadline {{ background: #fef3c7; padding: 10px 15px; border-radius: 6px; display: inline-block; }}
        .footer {{ text-align: center; padding: 15px; font-size: 12px; color: #64748b; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Nueva Tarea Asignada</h1>
    </div>
    <div class="content">
        <p>Hola <strong>{destinatario_nombre}</strong>,</p>
        
        <p>Se te ha asignado una nueva tarea que requiere tu atención.</p>
        
        <div class="task-box">
            <p style="margin: 0 0 10px 0;"><strong>Tipo:</strong> {tipo_tarea}</p>
            <p style="margin: 0 0 10px 0;"><strong>Título:</strong> {titulo}</p>
            <p style="margin: 0; color: #64748b; font-size: 14px;">{descripcion}</p>
        </div>
        
        <p>
            <span class="deadline">
                📅 <strong>Fecha límite:</strong> {fecha_formateada}
            </span>
        </p>
        
        <p>Por favor atiende esta tarea antes de la fecha límite para evitar escalamientos.</p>
        
        <p style="font-size: 12px; color: #64748b;">
            <strong>ID de tarea:</strong> {tarea_id[:12]}...<br>
            <strong>Workflow:</strong> {workflow_id[:12]}...
        </p>
    </div>
    <div class="footer">
        EDARSA HUB - Sistema de Gestión Operativa<br>
        Este es un mensaje automático, no responder a este correo.
    </div>
</body>
</html>
"""
    
    def _generar_html_tarea_vencida(
        self,
        tarea_id: str,
        workflow_id: str,
        tipo_tarea: str,
        titulo: str,
        fecha_limite: str,
        dias_vencida: int,
        destinatario_nombre: str
    ) -> str:
        """Genera HTML para email de tarea vencida."""
        return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: #dc2626; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }}
        .content {{ background: #f8fafc; padding: 20px; border: 1px solid #e2e8f0; }}
        .alert-box {{ background: #fef2f2; border: 1px solid #fecaca; padding: 20px; border-radius: 8px; margin: 15px 0; }}
        .task-box {{ background: white; padding: 20px; border-radius: 8px; border-left: 4px solid #dc2626; margin: 15px 0; }}
        .footer {{ text-align: center; padding: 15px; font-size: 12px; color: #64748b; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>⚠️ Tarea Vencida</h1>
    </div>
    <div class="content">
        <p>Hola <strong>{destinatario_nombre}</strong>,</p>
        
        <div class="alert-box">
            <p style="margin: 0; color: #dc2626; font-weight: bold;">
                Esta tarea tiene {dias_vencida} día(s) de vencida y requiere acción inmediata.
            </p>
        </div>
        
        <div class="task-box">
            <p style="margin: 0 0 10px 0;"><strong>Tipo:</strong> {tipo_tarea}</p>
            <p style="margin: 0 0 10px 0;"><strong>Título:</strong> {titulo}</p>
            <p style="margin: 0;"><strong>Fecha límite:</strong> {fecha_limite[:10] if fecha_limite else 'No definida'}</p>
        </div>
        
        <p>Por favor atiende esta tarea de manera urgente para evitar escalamientos adicionales.</p>
        
        <p style="font-size: 12px; color: #64748b;">
            <strong>ID de tarea:</strong> {tarea_id[:12]}...<br>
            <strong>Workflow:</strong> {workflow_id[:12]}...
        </p>
    </div>
    <div class="footer">
        EDARSA HUB - Sistema de Gestión Operativa<br>
        Este es un mensaje automático, no responder a este correo.
    </div>
</body>
</html>
"""


def get_notification_service(db) -> NotificationService:
    """Factory function para obtener instancia del servicio de notificaciones."""
    return NotificationService(db)
