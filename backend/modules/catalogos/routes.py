"""
EDARSA HUB - Catálogos Routes
=============================
Endpoints del módulo de catálogos.

ENDPOINTS:
- GET  /catalogos/dominios - Lista todos los dominios y sus catálogos
- GET  /catalogos/tabla/{tabla} - Lista registros de un catálogo
- GET  /catalogos/tabla/{tabla}/{id} - Obtiene un registro específico
- POST /catalogos/tabla/{tabla} - Crea un nuevo registro
- PUT  /catalogos/tabla/{tabla}/{id} - Actualiza un registro
- PUT  /catalogos/tabla/{tabla}/{id}/desactivar - Desactiva un registro
- PUT  /catalogos/tabla/{tabla}/{id}/activar - Reactiva un registro
- GET  /catalogos/estructura/{tabla} - Obtiene estructura de una tabla
- POST /catalogos/admin/crear-tablas - Crea tablas globales nuevas (DDL)
- GET  /catalogos/admin/verificar-tablas - Verifica estado de tablas nuevas
- GET  /catalogos/admin/script-ddl - Obtiene el script DDL

Diciembre 2025
"""

from fastapi import APIRouter, Depends, Query
from typing import Optional, Dict, Any

from core.security import get_current_user
from modules.catalogos.service import get_catalogos_service
from modules.catalogos.schemas import (
    CatalogoRegistroCreate,
    CatalogoRegistroUpdate,
)


router = APIRouter(prefix="/catalogos", tags=["Catálogos"])


# ============================================================================
# ENDPOINTS DE CONSULTA
# ============================================================================

@router.get("/dominios")
async def listar_dominios(current_user: Dict = Depends(get_current_user)):
    """
    Lista todos los dominios de catálogos con sus catálogos y conteos.
    
    Retorna la estructura completa del módulo de catálogos organizada por dominio
    (Generales, RH, Nómina, Compras, etc.) con información de cada catálogo.
    """
    service = get_catalogos_service()
    dominios = await service.obtener_dominios()
    return {"success": True, "dominios": dominios}


@router.get("/tabla/{tabla}")
async def listar_catalogo(
    tabla: str,
    solo_activos: bool = Query(False, description="Filtrar solo registros activos"),
    buscar: Optional[str] = Query(None, description="Texto de búsqueda"),
    limit: int = Query(500, ge=1, le=2000, description="Máximo de registros"),
    current_user: Dict = Depends(get_current_user)
):
    """
    Lista registros de un catálogo específico.
    
    Args:
        tabla: Nombre de la tabla del catálogo
        solo_activos: Si True, solo retorna registros activos
        buscar: Texto para filtrar por nombre/descripción
        limit: Máximo de registros a retornar
    """
    service = get_catalogos_service()
    return await service.listar_catalogo(tabla, solo_activos, buscar, limit)


@router.get("/tabla/{tabla}/{id}")
async def obtener_registro(
    tabla: str,
    id: int,
    current_user: Dict = Depends(get_current_user)
):
    """
    Obtiene un registro específico de un catálogo.
    
    Args:
        tabla: Nombre de la tabla
        id: ID del registro
    """
    service = get_catalogos_service()
    registro = await service.obtener_registro(tabla, id)
    return {"success": True, "data": registro}


@router.get("/estructura/{tabla}")
async def obtener_estructura(
    tabla: str,
    current_user: Dict = Depends(get_current_user)
):
    """
    Obtiene la estructura de una tabla (campos, tipos, etc.).
    
    Útil para generar formularios dinámicos en el frontend.
    """
    service = get_catalogos_service()
    return await service.obtener_estructura_tabla(tabla)


# ============================================================================
# ENDPOINTS DE MODIFICACIÓN
# ============================================================================

@router.post("/tabla/{tabla}")
async def crear_registro(
    tabla: str,
    body: CatalogoRegistroCreate,
    current_user: Dict = Depends(get_current_user)
):
    """
    Crea un nuevo registro en un catálogo.
    
    Args:
        tabla: Nombre de la tabla
        body: Datos del registro a crear
    
    Requiere rol: Administrador o Supervisor
    """
    if current_user.get('role') not in ['Administrador', 'Supervisor']:
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="Sin permisos para crear registros")
    
    service = get_catalogos_service()
    return await service.crear_registro(
        tabla, 
        body.datos, 
        current_user.get('email', '')
    )


@router.put("/tabla/{tabla}/{id}")
async def actualizar_registro(
    tabla: str,
    id: int,
    body: CatalogoRegistroUpdate,
    current_user: Dict = Depends(get_current_user)
):
    """
    Actualiza un registro existente.
    
    Args:
        tabla: Nombre de la tabla
        id: ID del registro
        body: Datos a actualizar
    
    Requiere rol: Administrador o Supervisor
    """
    if current_user.get('role') not in ['Administrador', 'Supervisor']:
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="Sin permisos para editar registros")
    
    service = get_catalogos_service()
    return await service.actualizar_registro(
        tabla, 
        id, 
        body.datos,
        current_user.get('email', '')
    )


@router.put("/tabla/{tabla}/{id}/desactivar")
async def desactivar_registro(
    tabla: str,
    id: int,
    current_user: Dict = Depends(get_current_user)
):
    """
    Desactiva un registro (soft delete).
    
    El registro no se elimina físicamente, solo se marca como inactivo.
    
    Requiere rol: Administrador
    """
    if current_user.get('role') != 'Administrador':
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="Solo administradores pueden desactivar registros")
    
    service = get_catalogos_service()
    return await service.desactivar_registro(tabla, id)


@router.put("/tabla/{tabla}/{id}/activar")
async def activar_registro(
    tabla: str,
    id: int,
    current_user: Dict = Depends(get_current_user)
):
    """
    Reactiva un registro previamente desactivado.
    
    Requiere rol: Administrador
    """
    if current_user.get('role') != 'Administrador':
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="Solo administradores pueden activar registros")
    
    service = get_catalogos_service()
    return await service.activar_registro(tabla, id)


# ============================================================================
# ENDPOINTS DE ADMINISTRACIÓN
# ============================================================================

@router.post("/admin/crear-tablas")
async def crear_tablas_nuevas(current_user: Dict = Depends(get_current_user)):
    """
    Ejecuta el DDL para crear las tablas globales nuevas.
    
    Crea las siguientes tablas si no existen:
    - Global_Cat_Empresas
    - Global_Cat_Bancos
    - Global_Cat_UnidadesMedida
    - Global_Cat_CentrosCosto
    - Global_Cat_FormaPagoSAT
    - Global_Cat_MetodoPagoSAT
    - Global_Cat_UsoCFDI
    - Global_Cat_RegimenFiscal
    - Finanzas_Cat_CuentasBancarias
    
    También inserta datos iniciales (bancos, formas de pago SAT, etc.)
    
    Requiere rol: Administrador
    """
    if current_user.get('role') != 'Administrador':
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="Solo administradores pueden crear tablas")
    
    service = get_catalogos_service()
    return await service.crear_tablas_nuevas()


@router.get("/admin/verificar-tablas")
async def verificar_tablas_nuevas(current_user: Dict = Depends(get_current_user)):
    """
    Verifica qué tablas globales nuevas existen.
    
    Retorna un diccionario con el estado de cada tabla.
    """
    service = get_catalogos_service()
    estado = await service.verificar_tablas_nuevas()
    return {"success": True, "tablas": estado}


@router.get("/admin/script-ddl")
async def obtener_script_ddl(current_user: Dict = Depends(get_current_user)):
    """
    Obtiene el script DDL para revisión antes de ejecutar.
    
    Requiere rol: Administrador
    """
    if current_user.get('role') != 'Administrador':
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="Solo administradores pueden ver el script DDL")
    
    service = get_catalogos_service()
    script = await service.obtener_script_ddl()
    return {"success": True, "script": script}
