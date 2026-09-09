from fastapi import APIRouter, Depends, HTTPException, Query

from core.rbac_helper_sql import has_full_access
from core.security import get_current_user
from . import repository as repo
from .schemas import AlertaReglaCreate,DocumentoCreate,DocumentoVersionCreate,EmpresaConfiguracionUpdate,PersonaCreate,PersonaEmpresaRolCreate,PersonaVinculoCreate

router=APIRouter(prefix='/catalogo-ampliado',tags=['Catalogo Ampliado'])


def _usuario_id(user: dict) -> int:
    value=user.get('_sql_usuario_id') or user.get('UsuarioID')
    if value is None:
        raise HTTPException(status_code=403,detail='Usuario SQL canonico no resuelto')
    return int(value)


def _gobierno_admin(current_user: dict=Depends(get_current_user)) -> dict:
    if not has_full_access(current_user):
        raise HTTPException(status_code=403,detail='Sin permisos de gobierno corporativo')
    _usuario_id(current_user)
    return current_user


def _assert_empresa(empresa_id: int, require_active: bool=True) -> None:
    if not repo.empresa_existe(empresa_id):
        raise HTTPException(status_code=404,detail='Empresa no encontrada')
    if require_active:
        cfg=repo.get_empresa_configuracion(empresa_id)
        if not cfg or not cfg.get('CatalogoLegalAmpliadoActivo') or not cfg.get('Activo'):
            raise HTTPException(status_code=409,detail='Catalogo legal ampliado no activo para esta empresa')


@router.get('/empresas/{empresa_id}/configuracion')
def empresa_configuracion(empresa_id:int,current_user:dict=Depends(_gobierno_admin)):
    _assert_empresa(empresa_id,False); return {'success':True,'data':repo.get_empresa_configuracion(empresa_id)}

@router.put('/empresas/{empresa_id}/configuracion')
def actualizar_configuracion(empresa_id:int,body:EmpresaConfiguracionUpdate,current_user:dict=Depends(_gobierno_admin)):
    _assert_empresa(empresa_id,False); return {'success':True,'data':repo.upsert_empresa_configuracion(empresa_id,body.catalogo_legal_ampliado_activo,body.dias_alerta_default,_usuario_id(current_user))}

@router.get('/personas')
def personas(empresa_id:int|None=Query(default=None),current_user:dict=Depends(_gobierno_admin)):
    if empresa_id is not None: _assert_empresa(empresa_id)
    return {'success':True,'data':repo.list_personas(empresa_id)}

@router.post('/personas',status_code=201)
def crear_persona(body:PersonaCreate,current_user:dict=Depends(_gobierno_admin)):
    return {'success':True,'data':repo.create_persona(body.model_dump(),_usuario_id(current_user))}

@router.post('/personas/{persona_id}/vinculos',status_code=201)
def crear_vinculo(persona_id:int,body:PersonaVinculoCreate,current_user:dict=Depends(_gobierno_admin)):
    data=body.model_dump(); targets=[data.get(k) for k in ('usuario_id','cliente_id','proveedor_id','contacto_cliente_id','contacto_proveedor_id')]
    if sum(v is not None for v in targets)!=1: raise HTTPException(status_code=422,detail='Debe indicarse exactamente un destino canonico')
    return {'success':True,'data':repo.create_vinculo(persona_id,data,_usuario_id(current_user))}

@router.get('/roles-corporativos')
def roles(current_user:dict=Depends(_gobierno_admin)):
    return {'success':True,'data':repo.list_roles_catalogo()}

@router.post('/empresas/{empresa_id}/roles',status_code=201)
def asignar_rol(empresa_id:int,body:PersonaEmpresaRolCreate,current_user:dict=Depends(_gobierno_admin)):
    _assert_empresa(empresa_id)
    if body.vigente_desde and body.vigente_hasta and body.vigente_hasta<body.vigente_desde: raise HTTPException(status_code=422,detail='vigente_hasta no puede ser anterior a vigente_desde')
    return {'success':True,'data':repo.create_empresa_rol(empresa_id,body.model_dump(),_usuario_id(current_user))}

@router.get('/tipos-documento')
def tipos_documento(current_user:dict=Depends(_gobierno_admin)):
    return {'success':True,'data':repo.list_tipos_documento()}

@router.get('/empresas/{empresa_id}/documentos')
def documentos(empresa_id:int,current_user:dict=Depends(_gobierno_admin)):
    _assert_empresa(empresa_id); return {'success':True,'data':repo.list_documentos(empresa_id)}

@router.post('/empresas/{empresa_id}/documentos',status_code=201)
def crear_documento(empresa_id:int,body:DocumentoCreate,current_user:dict=Depends(_gobierno_admin)):
    _assert_empresa(empresa_id); data=body.model_dump(); tipo=data['propietario_tipo']
    if tipo=='EMPRESA': data.update(empresa_id=empresa_id,persona_id=None,persona_empresa_rol_id=None)
    elif tipo=='PERSONA':
        if not data.get('persona_id'): raise HTTPException(status_code=422,detail='persona_id requerido')
        data.update(empresa_id=None,persona_empresa_rol_id=None)
    else:
        if not data.get('persona_empresa_rol_id'): raise HTTPException(status_code=422,detail='persona_empresa_rol_id requerido')
        data.update(empresa_id=None,persona_id=None)
    return {'success':True,'data':repo.create_documento(data,_usuario_id(current_user))}

@router.post('/documentos/{documento_id}/versiones',status_code=201)
def crear_version(documento_id:int,body:DocumentoVersionCreate,current_user:dict=Depends(_gobierno_admin)):
    if body.fecha_emision and body.fecha_vencimiento and body.fecha_vencimiento<body.fecha_emision: raise HTTPException(status_code=422,detail='fecha_vencimiento invalida')
    return {'success':True,'data':repo.create_documento_version(documento_id,body.model_dump(),_usuario_id(current_user))}

@router.get('/documentos/{documento_id}/kardex')
def kardex(documento_id:int,current_user:dict=Depends(_gobierno_admin)):
    return {'success':True,'data':repo.get_kardex(documento_id)}

@router.get('/empresas/{empresa_id}/vencimientos')
def vencimientos(empresa_id:int,dias:int=Query(default=30,ge=0,le=3650),current_user:dict=Depends(_gobierno_admin)):
    _assert_empresa(empresa_id); return {'success':True,'en_dias':dias,'data':repo.list_vencimientos(empresa_id,dias)}

@router.get('/empresas/{empresa_id}/alertas/reglas')
def reglas_alerta(empresa_id:int,current_user:dict=Depends(_gobierno_admin)):
    _assert_empresa(empresa_id); return {'success':True,'data':repo.list_alerta_reglas(empresa_id)}

@router.post('/empresas/{empresa_id}/alertas/reglas',status_code=201)
def crear_regla_alerta(empresa_id:int,body:AlertaReglaCreate,current_user:dict=Depends(_gobierno_admin)):
    _assert_empresa(empresa_id); return {'success':True,'data':repo.create_alerta_regla(empresa_id,body.model_dump(),_usuario_id(current_user))}

@router.get('/empresas/{empresa_id}/alertas/eventos')
def eventos_alerta(empresa_id:int,limit:int=Query(default=200,ge=1,le=500),current_user:dict=Depends(_gobierno_admin)):
    _assert_empresa(empresa_id); return {'success':True,'data':repo.list_alerta_eventos(empresa_id,limit)}
