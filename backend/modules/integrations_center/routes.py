"""Gate 5B - Fachada administrativa unificada de Conexiones y Comunicaciones.

Solo lectura. Los writers existentes permanecen en sus contratos legacy hasta Gate 5C/5D.
"""

from __future__ import annotations

import logging
from typing import Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from core.rbac.middleware import require_permission
from core.security import get_current_user

from . import service
from .communications_routes import router as communications_router

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/integrations-center", tags=["Centro de Comunicaciones y Conexiones"])
router.include_router(communications_router)


def _meta() -> Dict:
    return {
        "gate": "5B",
        "source": "EDARSAHUB_SQL_COMPOSED",
        "read_only": True,
        "secrets_exposed": False,
        "production_touched": False,
        "legacy_write_endpoints_preserved": True,
    }


@router.get("/overview")
async def overview(current_user: Dict = Depends(get_current_user)):
    """Resumen administrativo unico para la futura UI del Centro."""
    try:
        return {"status": "SUCCESS", "data": await service.get_overview(current_user), "meta": _meta()}
    except Exception as exc:
        logger.error("[INTEGRATIONS_CENTER][OVERVIEW] %s", type(exc).__name__)
        raise HTTPException(status_code=500, detail="Error obteniendo resumen de integraciones")


@router.get("/connections")
async def connections(
    include_inactive: bool = Query(True),
    connection_type: Optional[str] = Query(None),
    system_type: Optional[str] = Query(None),
    health_status: Optional[str] = Query(None),
    current_user: Dict = Depends(get_current_user),
):
    """Lista normalizada y RBAC-aware de DATA_SOURCE, API_LOCAL y CORE autorizado."""
    try:
        items = await service.list_connections(
            current_user,
            include_inactive=include_inactive,
            connection_type=connection_type,
            system_type=system_type,
            health_status=health_status,
        )
        return {"status": "SUCCESS", "data": items, "count": len(items), "meta": _meta()}
    except Exception as exc:
        logger.error("[INTEGRATIONS_CENTER][CONNECTIONS] %s", type(exc).__name__)
        raise HTTPException(status_code=500, detail="Error obteniendo conexiones")


@router.get("/connections/{connection_id}")
async def connection_detail(
    connection_id: str,
    current_user: Dict = Depends(get_current_user),
):
    """Detalle administrativo seguro; no descifra ni devuelve secretos."""
    try:
        item = await service.get_connection_detail(current_user, connection_id)
        if not item:
            raise HTTPException(status_code=404, detail="Conexión no encontrada o fuera de alcance")
        return {"status": "SUCCESS", "data": item, "meta": _meta()}
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("[INTEGRATIONS_CENTER][DETAIL] %s", type(exc).__name__)
        raise HTTPException(status_code=500, detail="Error obteniendo detalle de conexión")


@router.get("/catalogs")
async def catalogs(current_user: Dict = Depends(get_current_user)):
    """Catálogos universales ya existentes: capacidades, sync y su relación."""
    _ = current_user
    try:
        return {"status": "SUCCESS", "data": service.get_catalogs(), "meta": _meta()}
    except Exception as exc:
        logger.error("[INTEGRATIONS_CENTER][CATALOGS] %s", type(exc).__name__)
        raise HTTPException(status_code=500, detail="Error obteniendo catálogos de integraciones")


@router.get("/communications")
async def communications(
    current_user: Dict = Depends(require_permission("NOTIFICACIONES_VER")),
):
    """Resumen de Communications respetando el permiso RBAC ya existente."""
    _ = current_user
    try:
        data = service.get_communications_summary()
        data["legacy_route"] = "/api/v2/notificaciones-whatsapp"
        data["governance_status"] = "COMPATIBILITY_UNTIL_GATE_5D"
        return {"status": "SUCCESS", "data": data, "meta": _meta()}
    except Exception as exc:
        logger.error("[INTEGRATIONS_CENTER][COMMUNICATIONS] %s", type(exc).__name__)
        raise HTTPException(status_code=500, detail="Error obteniendo resumen de comunicaciones")
