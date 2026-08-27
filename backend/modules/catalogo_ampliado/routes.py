from fastapi import APIRouter, Depends, HTTPException, Query

from core.security import get_current_user
from . import repository as repo
from .schemas import (
    AlertaReglaCreate,
    DocumentoCreate,
    EmpresaConfiguracionUpdate,
    PersonaCreate,
    PersonaEmpresaRolCreate,
    PersonaVinculoCreate,
)

router = APIRouter(prefix="/catalogo-ampliado", tags=["Catalogo Ampliado"])


def _email(user: dict) -> str:
    return str(user.get("email") or user.get("correo") or "unknown")


def _assert_empresa_activa(empresa_id: int) -> None:
    cfg = repo.get_empresa_configuracion(empresa_id)
    if not cfg or not cfg.get("CatalogoLegalAmpliadoActivo"):
        raise HTTPException(status_code=409, detail="Catalogo legal ampliado no activo para esta empresa")


@router.get("/empresas/{empresa_id}/configuracion")
def empresa_configuracion(empresa_id: int, current_user: dict = Depends(get_current_user)):
    return {"success": True, "data": repo.get_empresa_configuracion(empresa_id)}


@router.put("/empresas/{empresa_id}/configuracion")
def actualizar_empresa_configuracion(
    empresa_id: int,
    body: EmpresaConfiguracionUpdate,
    current_user: dict = Depends(get_current_user),
):
    data = repo.upsert_empresa_configuracion(
        empresa_id,
        body.catalogo_legal_ampliado_activo,
        body.dias_alerta_default,
        _email(current_user),
    )
    return {"success": True, "data": data}


@router.get("/personas")
def personas(empresa_id: int | None = Query(default=None), current_user: dict = Depends(get_current_user)):
    return {"success": True, "data": repo.list_personas(empresa_id)}


@router.post("/personas", status_code=201)
def crear_persona(body: PersonaCreate, current_user: dict = Depends(get_current_user)):
    return {"success": True, "data": repo.create_persona(body.model_dump(), _email(current_user))}


@router.post("/personas/{persona_id}/vinculos", status_code=201)
def crear_vinculo(persona_id: int, body: PersonaVinculoCreate, current_user: dict = Depends(get_current_user)):
    return {"success": True, "data": repo.create_vinculo(persona_id, body.model_dump(), _email(current_user))}


@router.get("/roles-corporativos")
def roles_corporativos(current_user: dict = Depends(get_current_user)):
    return {"success": True, "data": repo.list_roles_catalogo()}


@router.post("/empresas/{empresa_id}/roles", status_code=201)
def asignar_rol(
    empresa_id: int,
    body: PersonaEmpresaRolCreate,
    current_user: dict = Depends(get_current_user),
):
    _assert_empresa_activa(empresa_id)
    if body.vigente_desde and body.vigente_hasta and body.vigente_hasta < body.vigente_desde:
        raise HTTPException(status_code=422, detail="vigente_hasta no puede ser anterior a vigente_desde")
    return {"success": True, "data": repo.create_empresa_rol(empresa_id, body.model_dump(), _email(current_user))}


@router.get("/empresas/{empresa_id}/documentos")
def documentos(empresa_id: int, current_user: dict = Depends(get_current_user)):
    _assert_empresa_activa(empresa_id)
    return {"success": True, "data": repo.list_documentos(empresa_id)}


@router.post("/empresas/{empresa_id}/documentos", status_code=201)
def crear_documento(
    empresa_id: int,
    body: DocumentoCreate,
    current_user: dict = Depends(get_current_user),
):
    _assert_empresa_activa(empresa_id)
    data = body.model_dump()
    if data["propietario_tipo"] == "EMPRESA":
        data["empresa_id"] = empresa_id
        data["persona_id"] = None
        data["persona_empresa_rol_id"] = None
    elif data["propietario_tipo"] == "PERSONA":
        data["empresa_id"] = None
        data["persona_empresa_rol_id"] = None
        if not data.get("persona_id"):
            raise HTTPException(status_code=422, detail="persona_id requerido")
    else:
        data["empresa_id"] = None
        data["persona_id"] = None
        if not data.get("persona_empresa_rol_id"):
            raise HTTPException(status_code=422, detail="persona_empresa_rol_id requerido")
    return {"success": True, "data": repo.create_documento(data, _email(current_user))}


@router.get("/documentos/{documento_id}/kardex")
def kardex(documento_id: int, current_user: dict = Depends(get_current_user)):
    return {"success": True, "data": repo.get_kardex(documento_id)}


@router.get("/empresas/{empresa_id}/vencimientos")
def vencimientos(
    empresa_id: int,
    dias: int = Query(default=30, ge=0, le=3650),
    current_user: dict = Depends(get_current_user),
):
    _assert_empresa_activa(empresa_id)
    return {"success": True, "en_dias": dias, "data": repo.list_vencimientos(empresa_id, dias)}
