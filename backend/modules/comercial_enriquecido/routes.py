"""
Rutas SQL-first del Catálogo Comercial Enriquecido de Productos (Bloque C).
===========================================================================
8 endpoints + RBAC canónico (NO hardcode):
  - SUPERADMIN/ADMIN (vía es_admin canónico) y scope por unidades permitidas
    (resolve_unidad_scope: lista vacía => sin restricción).
  - Escritura: es_admin o es_aprobador (canónico). Lectura: cualquier usuario,
    acotado por sus server_ids permitidos.
NO-LIVE, conexión central, parametrizado.
"""
import logging
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from pydantic import BaseModel

from core.security import get_current_user
from core.rbac_helper_sql import es_admin, es_aprobador
from core.corporate_filters.request_resolver import resolve_unidad_scope, canonical_server_id
from modules.comercial_enriquecido.repository import ComercialEnriquecidoRepository as Repo

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/comercial/productos-enriquecidos", tags=["Comercial - Catálogo Enriquecido"])


async def _allowed_servers(current_user) -> List[str]:
    """server_ids permitidos del usuario (lista vacía => sin restricción / admin)."""
    scope = await resolve_unidad_scope(current_user)
    return scope.allowed_server_ids or []


def _puede_editar(current_user) -> bool:
    return es_admin(current_user) or es_aprobador(current_user)


class ProductoEnriquecidoCreate(BaseModel):
    producto_id: Optional[str] = None
    server_id: Optional[str] = None
    system_type: Optional[str] = None
    unidad_codigo: Optional[str] = None
    codigo_producto_origen: Optional[str] = None
    nombre_producto: Optional[str] = None
    familia_origen: Optional[str] = None
    grupo_comercial: Optional[str] = None
    casa_comercial: Optional[str] = None
    marca: Optional[str] = None
    categoria: Optional[str] = None
    subcategoria: Optional[str] = None
    tipo_alcohol: Optional[str] = None
    es_alcoholico: Optional[bool] = False
    grado_alcohol: Optional[float] = None
    presentacion_ml: Optional[float] = None
    presentacion_texto: Optional[str] = None
    ean: Optional[str] = None
    imagen_url: Optional[str] = None
    proveedor_id: Optional[str] = None
    representante_id: Optional[str] = None
    precio_venta: Optional[float] = None
    confianza: Optional[float] = None
    requiere_validacion: Optional[bool] = False
    regla_usada: Optional[str] = None
    observaciones: Optional[str] = None
    activo: Optional[bool] = True


class ProductoEnriquecidoUpdate(BaseModel):
    grupo_comercial: Optional[str] = None
    casa_comercial: Optional[str] = None
    marca: Optional[str] = None
    categoria: Optional[str] = None
    subcategoria: Optional[str] = None
    tipo_alcohol: Optional[str] = None
    es_alcoholico: Optional[bool] = None
    grado_alcohol: Optional[float] = None
    presentacion_ml: Optional[float] = None
    presentacion_texto: Optional[str] = None
    ean: Optional[str] = None
    imagen_url: Optional[str] = None
    proveedor_id: Optional[str] = None
    representante_id: Optional[str] = None
    precio_venta: Optional[float] = None
    confianza: Optional[float] = None
    requiere_validacion: Optional[bool] = None
    regla_usada: Optional[str] = None
    observaciones: Optional[str] = None


@router.get("")
async def listar_productos_enriquecidos(
    unidad: Optional[str] = Query(None, description="Unidad canónica (codigo/pk) o server_id legacy"),
    grupo_comercial: Optional[str] = None,
    casa_comercial: Optional[str] = None,
    marca: Optional[str] = None,
    categoria: Optional[str] = None,
    subcategoria: Optional[str] = None,
    tipo_alcohol: Optional[str] = None,
    es_alcoholico: Optional[bool] = None,
    grado_alcohol_min: Optional[float] = None,
    grado_alcohol_max: Optional[float] = None,
    requiere_validacion: Optional[bool] = None,
    activo: Optional[bool] = None,
    texto_busqueda: Optional[str] = None,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(get_current_user),
):
    allowed = await _allowed_servers(current_user)
    filtros = {
        "server_id": canonical_server_id(unidad) if unidad else None,
        "grupo_comercial": grupo_comercial, "casa_comercial": casa_comercial, "marca": marca,
        "categoria": categoria, "subcategoria": subcategoria, "tipo_alcohol": tipo_alcohol,
        "es_alcoholico": es_alcoholico, "grado_alcohol_min": grado_alcohol_min,
        "grado_alcohol_max": grado_alcohol_max, "requiere_validacion": requiere_validacion,
        "activo": activo, "texto_busqueda": texto_busqueda,
    }
    return Repo.listar(filtros, allowed, limit=limit, offset=offset)


@router.get("/catalogos/filtros")
async def catalogos_filtros(current_user: dict = Depends(get_current_user)):
    allowed = await _allowed_servers(current_user)
    return Repo.catalogos_filtros(allowed)


@router.get("/{id}")
async def obtener_producto_enriquecido(id: str, current_user: dict = Depends(get_current_user)):
    allowed = await _allowed_servers(current_user)
    item = Repo.get_by_id(id, allowed)
    if not item:
        raise HTTPException(status_code=404, detail="Producto enriquecido no encontrado o fuera de su alcance")
    return item


@router.post("")
async def crear_producto_enriquecido(
    body: ProductoEnriquecidoCreate, current_user: dict = Depends(get_current_user)
):
    if not _puede_editar(current_user):
        raise HTTPException(status_code=403, detail="No autorizado para editar el catálogo enriquecido")
    new_id = Repo.crear(body.dict(), current_user.get("email"))
    return {"id": new_id, "creado": True}


@router.put("/{id}")
async def actualizar_producto_enriquecido(
    id: str, body: ProductoEnriquecidoUpdate, current_user: dict = Depends(get_current_user)
):
    if not _puede_editar(current_user):
        raise HTTPException(status_code=403, detail="No autorizado para editar el catálogo enriquecido")
    allowed = await _allowed_servers(current_user)
    if not Repo.get_by_id(id, allowed):
        raise HTTPException(status_code=404, detail="Producto enriquecido no encontrado o fuera de su alcance")
    ok = Repo.actualizar(id, body.dict(exclude_unset=True), current_user.get("email"))
    return {"id": id, "actualizado": ok}


@router.patch("/{id}/activar")
async def activar_producto(id: str, current_user: dict = Depends(get_current_user)):
    if not _puede_editar(current_user):
        raise HTTPException(status_code=403, detail="No autorizado")
    allowed = await _allowed_servers(current_user)
    if not Repo.get_by_id(id, allowed):
        raise HTTPException(status_code=404, detail="No encontrado o fuera de su alcance")
    ok = Repo.set_activo(id, True, current_user.get("email"))
    return {"id": id, "activo": True, "ok": ok}


@router.patch("/{id}/desactivar")
async def desactivar_producto(id: str, current_user: dict = Depends(get_current_user)):
    if not _puede_editar(current_user):
        raise HTTPException(status_code=403, detail="No autorizado")
    allowed = await _allowed_servers(current_user)
    if not Repo.get_by_id(id, allowed):
        raise HTTPException(status_code=404, detail="No encontrado o fuera de su alcance")
    ok = Repo.set_activo(id, False, current_user.get("email"))
    return {"id": id, "activo": False, "ok": ok}


@router.post("/importar")
async def importar_productos(
    rows: List[dict] = Body(..., description="Lista de filas de enriquecimiento (UPSERT por producto_id)"),
    current_user: dict = Depends(get_current_user),
):
    if not _puede_editar(current_user):
        raise HTTPException(status_code=403, detail="No autorizado para importar")
    if not isinstance(rows, list) or not rows:
        raise HTTPException(status_code=400, detail="Se requiere una lista de filas no vacía")
    resultado = Repo.importar(rows, current_user.get("email"))
    return {"ok": True, **resultado}
