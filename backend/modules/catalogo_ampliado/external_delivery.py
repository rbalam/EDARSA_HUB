"""Adapter de Catalogo Ampliado hacia Communications canonico SQL-first."""
from __future__ import annotations
import asyncio
import uuid
from core.sql_first.db import fetch_one_dict, sql_connection
from core.communications.notifications.repository import NotificationRepository
TEMPLATE_CODE='catalogo_ampliado_documento_vencimiento'
EVENT_CODE='DOCUMENTO_VENCIMIENTO'
MODULE='catalogo_ampliado'
def _queue_id(evento_id:int,canal:str,usuario_id:int)->str:
    return str(uuid.uuid5(uuid.NAMESPACE_URL,f'edarsahub:{MODULE}:{evento_id}:{canal.lower()}:{usuario_id}'))
def _target(usuario_id:int):
    return fetch_one_dict("""SELECT TOP 1 u.UsuarioID,u.Email,u.Celular,u.Activo,COALESCE(pc.RecibeEmailNotificaciones,1) RecibeEmailNotificaciones,COALESCE(pc.RecibeWhatsAppNotificaciones,0) RecibeWhatsAppNotificaciones FROM dbo.Usuario_Catalogo u LEFT JOIN dbo.Usuario_PortalConfiguracion pc ON pc.UsuarioID=u.UsuarioID WHERE u.UsuarioID=%s""",[usuario_id])
def _queue_exists(queue_id:str)->bool:
    return fetch_one_dict("SELECT ID FROM dbo.Operativo_Notificaciones_Queue WHERE ID=%s",[queue_id]) is not None
def _mark_generated(evento_id:int,queue_id:str)->None:
    with sql_connection() as conn:
        cur=conn.cursor(); cur.execute("UPDATE dbo.Gobierno_AlertaEvento SET NotificacionReferencia=%s,Estado='GENERADA',ErrorMensaje=NULL WHERE AlertaEventoID=%s AND Estado IN('PENDIENTE','GENERADA')",[queue_id,evento_id]); conn.commit()
def dispatch_external_alert(evento:dict)->dict:
    canal=str(evento.get('Canal') or '').upper(); evento_id=int(evento['AlertaEventoID'])
    if canal=='APP': return {'alerta_evento_id':evento_id,'canal':canal,'status':'BLOCKED_NO_CANONICAL_PUSH_PROVIDER'}
    if canal not in {'EMAIL','WHATSAPP'}: return {'alerta_evento_id':evento_id,'canal':canal,'status':'BLOCKED_UNSUPPORTED_CHANNEL'}
    usuario_id=evento.get('UsuarioObjetivoID')
    if not usuario_id: return {'alerta_evento_id':evento_id,'canal':canal,'status':'BLOCKED_NO_TARGET_USER'}
    target=_target(int(usuario_id))
    if not target or not bool(target.get('Activo')): return {'alerta_evento_id':evento_id,'canal':canal,'status':'BLOCKED_TARGET_INACTIVE_OR_MISSING'}
    if canal=='EMAIL':
        if not bool(target.get('RecibeEmailNotificaciones')): return {'alerta_evento_id':evento_id,'canal':canal,'status':'BLOCKED_USER_PREFERENCE'}
        recipient=(target.get('Email') or '').strip(); dest={'user_id':str(usuario_id),'email':recipient,'tipo':'usuario_objetivo'}
    else:
        if not bool(target.get('RecibeWhatsAppNotificaciones')): return {'alerta_evento_id':evento_id,'canal':canal,'status':'BLOCKED_USER_PREFERENCE'}
        recipient=(target.get('Celular') or '').strip(); dest={'user_id':str(usuario_id),'telefono':recipient,'tipo':'usuario_objetivo'}
    if not recipient: return {'alerta_evento_id':evento_id,'canal':canal,'status':'BLOCKED_MISSING_CONTACT'}
    qid=_queue_id(evento_id,canal,int(usuario_id))
    if not _queue_exists(qid):
        item={'id':qid,'canal':canal.lower(),'modulo':MODULE,'evento_negocio':EVENT_CODE,'referencia_id':str(evento_id),'prioridad':3,'destinatarios':[dest],'template_codigo':TEMPLATE_CODE,'payload':{'titulo':str(evento.get('Titulo') or 'Documento'),'fecha_objetivo':str(evento.get('FechaObjetivo') or '')},'estado':'pendiente','intentos':0}
        asyncio.run(NotificationRepository(None).enqueue(item))
    _mark_generated(evento_id,qid)
    return {'alerta_evento_id':evento_id,'canal':canal,'status':'GENERADA','reference':qid}
