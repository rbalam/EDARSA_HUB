from __future__ import annotations

from typing import Any, Dict, Optional
from fastapi import APIRouter, Body, Depends, HTTPException, Query
from core.communications.notifications.repository import NotificationRepository
from core.rbac.middleware import require_permission

router = APIRouter(prefix='/communications', tags=['Centro de Comunicaciones y Conexiones'])

def _meta(action: str) -> Dict[str, Any]:
    return {'gate':'5D','source':'EDARSAHUB_SQL','action':action,'provider_neutral':True,'secrets_exposed':False,'production_touched':False}

def _safe_doc(doc: Any) -> Dict[str, Any]:
    if not isinstance(doc, dict): return {}
    safe={}
    for key,value in doc.items():
        normalized=str(key).lower()
        if str(key).startswith('_sql_') or any(part in normalized for part in ('secret','password','token','api_key')): continue
        safe[key]=value
    return safe

def _repo() -> NotificationRepository: return NotificationRepository(None)

@router.get('/configs')
async def list_configs(modulo:Optional[str]=Query(None),canal:Optional[str]=Query(None),activo:Optional[bool]=Query(None),current_user:Dict=Depends(require_permission('NOTIFICACIONES_VER'))):
    _=current_user; items=await _repo().get_all_configs(modulo=modulo,canal=canal,activo=activo); safe=[_safe_doc(x) for x in items]; return {'status':'SUCCESS','data':safe,'count':len(safe),'meta':_meta('LIST_CONFIGS')}

@router.post('/configs')
async def create_config(payload:Dict[str,Any]=Body(...),current_user:Dict=Depends(require_permission('NOTIFICACIONES_CONFIGURAR'))):
    _=current_user
    if not payload.get('evento') or not payload.get('template_codigo'): raise HTTPException(status_code=422,detail='evento y template_codigo son requeridos')
    created=await _repo().create_config(payload); return {'status':'SUCCESS','data':_safe_doc(created),'meta':_meta('CREATE_CONFIG')}

@router.put('/configs/{config_id}')
async def update_config(config_id:str,payload:Dict[str,Any]=Body(...),current_user:Dict=Depends(require_permission('NOTIFICACIONES_CONFIGURAR'))):
    _=current_user; updated=await _repo().update_config(config_id,payload)
    if not updated: raise HTTPException(status_code=404,detail='Configuracion no encontrada')
    return {'status':'SUCCESS','data':_safe_doc(updated),'meta':_meta('UPDATE_CONFIG')}

@router.delete('/configs/{config_id}')
async def deactivate_config(config_id:str,current_user:Dict=Depends(require_permission('NOTIFICACIONES_CONFIGURAR'))):
    _=current_user; ok=await _repo().delete_config(config_id)
    if not ok: raise HTTPException(status_code=404,detail='Configuracion no encontrada')
    return {'status':'SUCCESS','data':{'id':config_id,'activo':False},'meta':_meta('DEACTIVATE_CONFIG')}

@router.get('/templates')
async def list_templates(canal:Optional[str]=Query(None),activo:Optional[bool]=Query(None),current_user:Dict=Depends(require_permission('NOTIFICACIONES_VER'))):
    _=current_user; items=await _repo().get_all_templates(canal=canal,activo=activo); safe=[_safe_doc(x) for x in items]; return {'status':'SUCCESS','data':safe,'count':len(safe),'meta':_meta('LIST_TEMPLATES')}

@router.post('/templates')
async def create_template(payload:Dict[str,Any]=Body(...),current_user:Dict=Depends(require_permission('NOTIFICACIONES_CONFIGURAR'))):
    _=current_user
    if not payload.get('codigo') or not payload.get('template_texto'): raise HTTPException(status_code=422,detail='codigo y template_texto son requeridos')
    created=await _repo().create_template(payload); return {'status':'SUCCESS','data':_safe_doc(created),'meta':_meta('CREATE_TEMPLATE')}

@router.put('/templates/{template_id}')
async def update_template(template_id:str,payload:Dict[str,Any]=Body(...),current_user:Dict=Depends(require_permission('NOTIFICACIONES_CONFIGURAR'))):
    _=current_user; updated=await _repo().update_template(template_id,payload)
    if not updated: raise HTTPException(status_code=404,detail='Template no encontrado')
    return {'status':'SUCCESS','data':_safe_doc(updated),'meta':_meta('UPDATE_TEMPLATE')}

@router.delete('/templates/{template_id}')
async def deactivate_template(template_id:str,current_user:Dict=Depends(require_permission('NOTIFICACIONES_CONFIGURAR'))):
    _=current_user; ok=await _repo().delete_template(template_id)
    if not ok: raise HTTPException(status_code=404,detail='Template no encontrado')
    return {'status':'SUCCESS','data':{'id':template_id,'activo':False},'meta':_meta('DEACTIVATE_TEMPLATE')}

@router.get('/providers')
async def list_providers(canal:Optional[str]=Query(None),activo:Optional[bool]=Query(None),current_user:Dict=Depends(require_permission('NOTIFICACIONES_VER'))):
    _=current_user; items=await _repo().get_all_provider_configs(canal=canal,activo=activo); safe=[_safe_doc(x) for x in items]; return {'status':'SUCCESS','data':safe,'count':len(safe),'meta':_meta('LIST_PROVIDERS')}

def _reject_secret_fields(payload:Dict[str,Any]):
    forbidden=[k for k in payload if any(part in str(k).lower() for part in ('secret','password','token','api_key'))]
    if forbidden: raise HTTPException(status_code=422,detail='Los secretos no se almacenan en la configuracion de provider')

@router.post('/providers')
async def create_provider(payload:Dict[str,Any]=Body(...),current_user:Dict=Depends(require_permission('NOTIFICACIONES_CONFIGURAR'))):
    _=current_user; _reject_secret_fields(payload)
    if not payload.get('canal') or not payload.get('provider'): raise HTTPException(status_code=422,detail='canal y provider son requeridos')
    created=await _repo().create_provider_config(payload); return {'status':'SUCCESS','data':_safe_doc(created),'meta':_meta('CREATE_PROVIDER')}

@router.put('/providers/{provider_id}')
async def update_provider(provider_id:str,payload:Dict[str,Any]=Body(...),current_user:Dict=Depends(require_permission('NOTIFICACIONES_CONFIGURAR'))):
    _=current_user; _reject_secret_fields(payload); updated=await _repo().update_provider_config(provider_id,payload)
    if not updated: raise HTTPException(status_code=404,detail='Provider no encontrado')
    return {'status':'SUCCESS','data':_safe_doc(updated),'meta':_meta('UPDATE_PROVIDER')}

@router.get('/queue')
async def queue_status(limit:int=Query(50,ge=1,le=200),current_user:Dict=Depends(require_permission('NOTIFICACIONES_VER'))):
    _=current_user; repo=_repo(); items=await repo.get_pending_items(limit=limit); stats=await repo.get_queue_stats(); return {'status':'SUCCESS','data':{'stats':stats,'pending':[_safe_doc(x) for x in items]},'meta':_meta('QUEUE_STATUS')}

@router.get('/logs')
async def logs(workflow_id:Optional[str]=Query(None),evento:Optional[str]=Query(None),estado:Optional[str]=Query(None),limit:int=Query(100,ge=1,le=500),current_user:Dict=Depends(require_permission('NOTIFICACIONES_VER'))):
    _=current_user; repo=_repo(); items=await repo.get_logs(workflow_id=workflow_id,evento_negocio=evento,estado_envio=estado,limit=limit); return {'status':'SUCCESS','data':[_safe_doc(x) for x in items],'count':len(items),'meta':_meta('LIST_LOGS')}
