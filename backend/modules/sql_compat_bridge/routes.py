"""
SQL Compat Bridge Routes
Endpoints compatibles con frontend legacy, usando SQL Server
"""
from fastapi import APIRouter, Depends, HTTPException
from typing import Dict
from core.security import get_current_user
from .repository import get_sql_compat_bridge_repo

router = APIRouter(prefix="/api", tags=["SQL Compat Bridge"])


# =========================================================
# COMPATIBILIDAD CATALOGO CONSULTAS
# Mantiene frontend actual, pero ya usa SQL
# =========================================================

@router.get("/catalogo/consultas-custom")
async def compat_listar_consultas_custom(current_user: Dict = Depends(get_current_user)):
    """Lista consultas custom desde SQL (compatibilidad con frontend legacy)."""
    repo = get_sql_compat_bridge_repo()
    consultas = repo.listar_consultas_custom()
    return {
        "consultas": consultas,
        "total": len(consultas),
        "source": "SQL_COMPAT_BRIDGE"
    }


@router.post("/catalogo/consultas-custom")
async def compat_crear_consulta_custom(body: Dict, current_user: Dict = Depends(get_current_user)):
    """Crea consulta custom en SQL (compatibilidad con frontend legacy)."""
    repo = get_sql_compat_bridge_repo()
    repo.crear_consulta_custom(body, current_user)
    return {"ok": True, "message": "Consulta custom creada en SQL (compat)"}


@router.put("/catalogo/consultas-custom/{consulta_id}")
async def compat_actualizar_consulta_custom(consulta_id: int, body: Dict, current_user: Dict = Depends(get_current_user)):
    """Actualiza consulta custom en SQL (compatibilidad con frontend legacy)."""
    repo = get_sql_compat_bridge_repo()
    updated = repo.actualizar_consulta_custom(consulta_id, body, current_user)
    if not updated:
        raise HTTPException(status_code=404, detail="Consulta no encontrada")
    return {"ok": True, "message": "Consulta custom actualizada en SQL (compat)"}


@router.delete("/catalogo/consultas-custom/{consulta_id}")
async def compat_eliminar_consulta_custom(consulta_id: int, current_user: Dict = Depends(get_current_user)):
    """Elimina (soft) consulta custom en SQL (compatibilidad con frontend legacy)."""
    repo = get_sql_compat_bridge_repo()
    updated = repo.eliminar_consulta_custom(consulta_id, current_user)
    if not updated:
        raise HTTPException(status_code=404, detail="Consulta no encontrada")
    return {"ok": True, "message": "Consulta custom desactivada en SQL (compat)"}


# =========================================================
# COMPATIBILIDAD EXPLORADOR / SCRIPTS PENDIENTES
# Mantiene frontend actual, pero ya usa SQL
# =========================================================

@router.get("/explorador/scripts-pendientes/{server_id}")
async def compat_listar_scripts_pendientes(server_id: str, current_user: Dict = Depends(get_current_user)):
    """Lista scripts pendientes por servidor desde SQL (compatibilidad)."""
    repo = get_sql_compat_bridge_repo()
    scripts = repo.listar_scripts_pendientes_por_server(server_id)
    return {
        "scripts": scripts,
        "total": len(scripts),
        "source": "SQL_COMPAT_BRIDGE"
    }


@router.post("/explorador/guardar-script/{server_id}")
async def compat_guardar_script(server_id: str, body: Dict, current_user: Dict = Depends(get_current_user)):
    """Guarda script pendiente en SQL (compatibilidad con frontend legacy)."""
    repo = get_sql_compat_bridge_repo()
    repo.guardar_script_pendiente(server_id, body, current_user)
    return {"ok": True, "message": "Script guardado en SQL (compat)"}
