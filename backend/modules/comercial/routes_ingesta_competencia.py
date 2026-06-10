"""
Ingesta de Competencia - Endpoints
==================================
Subida de adjuntos (Excel/CSV/PDF/imagen/Word) o link, extraccion (plantilla o IA
Gemini), staging con validacion humana y confirmacion a tablas canonicas.
RBAC: ver = comercial.competidores.ver ; crear/confirmar = comercial.competidores.crear.
"""
from fastapi import APIRouter, Depends, Query, UploadFile, File, Form, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
from typing import Optional, List

from core.security import get_current_user
from core.rbac.middleware import require_permission
from core.object_storage import get_object
from modules.comercial.services import ingesta_competencia_service as svc

router = APIRouter(prefix="/comercial/ingesta-competencia", tags=["Comercial - Ingesta Competencia"])


class LinkRequest(BaseModel):
    empresa_id: int
    unidades_negocio_ids: Optional[str] = None  # CSV de empresa_ids destino
    url: str


class FilasUpdate(BaseModel):
    filas: List[dict]


@router.get("/plantilla", summary="Descargar plantilla Excel de ingesta")
async def descargar_plantilla(
    current_user: dict = Depends(get_current_user),
    _auth: dict = Depends(require_permission("comercial.competidores.ver")),
):
    data = svc.generar_plantilla_excel()
    return Response(
        content=data,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=plantilla_ingesta_competencia.xlsx"},
    )


@router.get("", summary="Listar ingestas")
async def listar(
    empresa_id: Optional[int] = Query(None),
    estado: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user),
    _auth: dict = Depends(require_permission("comercial.competidores.ver")),
):
    return {"ingestas": svc.listar_ingestas(empresa_id, estado)}


@router.get("/{ingesta_id}", summary="Detalle de ingesta")
async def detalle(
    ingesta_id: str,
    current_user: dict = Depends(get_current_user),
    _auth: dict = Depends(require_permission("comercial.competidores.ver")),
):
    ing = svc.obtener_ingesta(ingesta_id)
    if not ing:
        raise HTTPException(status_code=404, detail="Ingesta no encontrada")
    return ing


@router.get("/{ingesta_id}/archivo", summary="Descargar el adjunto archivado")
async def descargar_archivo(
    ingesta_id: str,
    current_user: dict = Depends(get_current_user),
    _auth: dict = Depends(require_permission("comercial.competidores.ver")),
):
    ing = svc.obtener_ingesta(ingesta_id)
    if not ing or not ing.get("archivo_path"):
        raise HTTPException(status_code=404, detail="Sin archivo archivado")
    data, ctype = get_object(ing["archivo_path"])
    return Response(content=data, media_type=ing.get("archivo_content_type") or ctype,
                    headers={"Content-Disposition": f"attachment; filename={ing.get('archivo_nombre') or 'archivo'}"})


@router.post("/upload", summary="Subir adjunto (Excel/CSV/PDF/imagen/Word)")
async def upload(
    file: UploadFile = File(...),
    empresa_id: int = Form(...),
    unidades_negocio_ids: Optional[str] = Form(None),
    current_user: dict = Depends(get_current_user),
    _auth: dict = Depends(require_permission("comercial.competidores.crear")),
):
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Archivo vacio")
    return await svc.crear_ingesta_archivo(
        empresa_id, unidades_negocio_ids or "", file.filename or "archivo",
        file.content_type or "application/octet-stream", data,
        current_user.get("email", "sistema"),
    )


@router.post("/link", summary="Ingesta desde un link (scraping + IA)")
async def desde_link(
    body: LinkRequest,
    current_user: dict = Depends(get_current_user),
    _auth: dict = Depends(require_permission("comercial.competidores.crear")),
):
    return await svc.crear_ingesta_link(
        body.empresa_id, body.unidades_negocio_ids or "", body.url,
        current_user.get("email", "sistema"),
    )


@router.put("/{ingesta_id}/filas", summary="Editar filas extraidas antes de confirmar")
async def editar_filas(
    ingesta_id: str,
    body: FilasUpdate,
    current_user: dict = Depends(get_current_user),
    _auth: dict = Depends(require_permission("comercial.competidores.crear")),
):
    ing = svc.actualizar_filas(ingesta_id, body.filas)
    if not ing:
        raise HTTPException(status_code=404, detail="Ingesta no encontrada")
    return ing


@router.post("/{ingesta_id}/confirmar", summary="Confirmar e insertar a tablas canonicas")
async def confirmar(
    ingesta_id: str,
    current_user: dict = Depends(get_current_user),
    _auth: dict = Depends(require_permission("comercial.competidores.crear")),
):
    ing = svc.confirmar_ingesta(ingesta_id, current_user.get("email", "sistema"))
    if not ing:
        raise HTTPException(status_code=404, detail="Ingesta no encontrada")
    return ing


@router.post("/{ingesta_id}/rechazar", summary="Rechazar ingesta")
async def rechazar(
    ingesta_id: str,
    current_user: dict = Depends(get_current_user),
    _auth: dict = Depends(require_permission("comercial.competidores.crear")),
):
    ing = svc.rechazar_ingesta(ingesta_id, current_user.get("email", "sistema"))
    if not ing:
        raise HTTPException(status_code=404, detail="Ingesta no encontrada")
    return ing
