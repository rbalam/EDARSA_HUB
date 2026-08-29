from core.unidades_service import UnidadesService
from core.corporate_filters.service import CorporateFilterService
"""
Vtiger CRM Routes - Endpoints para gestión de conexión Vtiger
=============================================================
Endpoints para configurar, probar y sincronizar con Vtiger CRM.
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field
from typing import Optional, List
import logging
import os
from datetime import datetime

from .vtiger_client import create_vtiger_client, VtigerModule

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/vtiger", tags=["CRM - Vtiger"])
security = HTTPBearer()


# ==================== MODELOS ====================

class VtigerConnectionConfig(BaseModel):
    """Configuración de conexión a Vtiger"""
    base_url: str = Field(..., description="URL de la instancia Vtiger", example="https://miempresa.vtiger.com")
    username: str = Field(..., description="Usuario de Vtiger", example="admin")
    access_key: str = Field(..., description="Access Key del usuario")
    name: str = Field(default="Vtiger CRM", description="Nombre descriptivo de la conexión")
    sync_modules: List[str] = Field(
        default=["Leads", "Contacts", "Accounts", "Potentials"],
        description="Módulos a sincronizar"
    )
    sync_direction: str = Field(default="bidirectional", description="Dirección: read_only o bidirectional")
    active: bool = Field(default=True, description="Si la conexión está activa")


class VtigerConnectionResponse(BaseModel):
    """Respuesta de conexión Vtiger"""
    id: str
    name: str
    base_url: str
    username: str
    sync_modules: List[str]
    sync_direction: str
    active: bool
    last_sync: Optional[str] = None
    status: str = "configured"


class VtigerTestResult(BaseModel):
    """Resultado de prueba de conexión"""
    success: bool
    message: str
    user_info: Optional[dict] = None
    response_time_ms: Optional[int] = None


# ==================== ALMACENAMIENTO EN MEMORIA ====================
# NOTA: En producción esto debería ir a la base de datos

_vtiger_connections = {}

def _get_connection_from_env() -> Optional[dict]:
    """Obtiene conexión desde variables de entorno si existe"""
    base_url = os.environ.get('VTIGER_BASE_URL')
    username = os.environ.get('VTIGER_USERNAME')
    access_key = os.environ.get('VTIGER_ACCESS_KEY')
    
    if base_url and username and access_key:
        return {
            "id": "vtiger_env",
            "name": os.environ.get('VTIGER_NAME', 'Vtiger CRM (ENV)'),
            "base_url": base_url,
            "username": username,
            "access_key": access_key,
            "sync_modules": ["Leads", "Contacts", "Accounts", "Potentials"],
            "sync_direction": "bidirectional",
            "active": True,
            "source": "environment"
        }
    return None


# ==================== ENDPOINTS ====================

@router.get("/connections")
async def list_vtiger_connections(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Lista todas las conexiones Vtiger configuradas"""
    connections = []
    
    # Añadir conexión desde ENV si existe
    env_conn = _get_connection_from_env()
    if env_conn:
        connections.append({
            **env_conn,
            "access_key": "***" + env_conn["access_key"][-4:] if len(env_conn["access_key"]) > 4 else "****"
        })
    
    # Añadir conexiones en memoria
    for conn_id, conn in _vtiger_connections.items():
        connections.append({
            **conn,
            "access_key": "***" + conn["access_key"][-4:] if len(conn["access_key"]) > 4 else "****"
        })
    
    return {"connections": connections, "count": len(connections)}


@router.post("/connections")
async def create_vtiger_connection(
    config: VtigerConnectionConfig,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Crea una nueva conexión Vtiger"""
    import uuid
    
    conn_id = f"vtiger_{uuid.uuid4().hex[:8]}"
    
    connection = {
        "id": conn_id,
        "name": config.name,
        "base_url": config.base_url.rstrip('/'),
        "username": config.username,
        "access_key": config.access_key,
        "sync_modules": config.sync_modules,
        "sync_direction": config.sync_direction,
        "active": config.active,
        "created_at": datetime.utcnow().isoformat(),
        "last_sync": None,
        "source": "manual"
    }
    
    _vtiger_connections[conn_id] = connection
    
    logger.info(f"[VTIGER] Conexión creada: {conn_id} -> {config.base_url}")
    
    return {
        "success": True,
        "connection": {
            **connection,
            "access_key": "***" + config.access_key[-4:] if len(config.access_key) > 4 else "****"
        },
        "message": "Conexión creada. Use /test para verificar conectividad."
    }


@router.put("/connections/{connection_id}")
async def update_vtiger_connection(
    connection_id: str,
    config: VtigerConnectionConfig,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Actualiza una conexión Vtiger existente"""
    if connection_id not in _vtiger_connections:
        raise HTTPException(status_code=404, detail="Conexión no encontrada")
    
    _vtiger_connections[connection_id].update({
        "name": config.name,
        "base_url": config.base_url.rstrip('/'),
        "username": config.username,
        "access_key": config.access_key,
        "sync_modules": config.sync_modules,
        "sync_direction": config.sync_direction,
        "active": config.active,
        "updated_at": datetime.utcnow().isoformat()
    })
    
    return {
        "success": True,
        "message": "Conexión actualizada"
    }


@router.delete("/connections/{connection_id}")
async def delete_vtiger_connection(
    connection_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Elimina una conexión Vtiger"""
    if connection_id == "vtiger_env":
        raise HTTPException(status_code=400, detail="No se puede eliminar conexión de entorno")
    
    if connection_id not in _vtiger_connections:
        raise HTTPException(status_code=404, detail="Conexión no encontrada")
    
    del _vtiger_connections[connection_id]
    
    return {"success": True, "message": "Conexión eliminada"}


@router.post("/connections/{connection_id}/test")
async def test_vtiger_connection(
    connection_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Prueba la conexión con Vtiger"""
    import time
    
    # Buscar conexión
    if connection_id == "vtiger_env":
        conn = _get_connection_from_env()
    else:
        conn = _vtiger_connections.get(connection_id)
    
    if not conn:
        raise HTTPException(status_code=404, detail="Conexión no encontrada")
    
    # Crear cliente y probar
    client = create_vtiger_client(
        base_url=conn["base_url"],
        username=conn["username"],
        access_key=conn["access_key"]
    )
    
    start = time.time()
    result = await client.test_connection()
    elapsed_ms = int((time.time() - start) * 1000)
    
    await client.close()
    
    return {
        "success": result["success"],
        "message": result["message"],
        "user_info": result.get("user"),
        "response_time_ms": elapsed_ms,
        "status_code": result.get("status_code")
    }


@router.post("/test")
async def test_vtiger_direct(
    config: VtigerConnectionConfig,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Prueba una conexión Vtiger sin guardarla"""
    import time
    
    client = create_vtiger_client(
        base_url=config.base_url,
        username=config.username,
        access_key=config.access_key
    )
    
    start = time.time()
    result = await client.test_connection()
    elapsed_ms = int((time.time() - start) * 1000)
    
    await client.close()
    
    return {
        "success": result["success"],
        "message": result["message"],
        "user_info": result.get("user"),
        "response_time_ms": elapsed_ms
    }


# ==================== SINCRONIZACIÓN ====================

@router.get("/connections/{connection_id}/leads")
async def get_vtiger_leads(
    connection_id: str,
    limit: int = 100,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Obtiene leads desde Vtiger"""
    conn = _vtiger_connections.get(connection_id) or (
        _get_connection_from_env() if connection_id == "vtiger_env" else None
    )
    
    if not conn:
        raise HTTPException(status_code=404, detail="Conexión no encontrada")
    
    client = create_vtiger_client(
        base_url=conn["base_url"],
        username=conn["username"],
        access_key=conn["access_key"]
    )
    
    result = await client.get_leads(limit=limit)
    await client.close()
    
    return result


@router.get("/connections/{connection_id}/contacts")
async def get_vtiger_contacts(
    connection_id: str,
    limit: int = 100,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Obtiene contactos desde Vtiger"""
    conn = _vtiger_connections.get(connection_id) or (
        _get_connection_from_env() if connection_id == "vtiger_env" else None
    )
    
    if not conn:
        raise HTTPException(status_code=404, detail="Conexión no encontrada")
    
    client = create_vtiger_client(
        base_url=conn["base_url"],
        username=conn["username"],
        access_key=conn["access_key"]
    )
    
    result = await client.get_contacts(limit=limit)
    await client.close()
    
    return result


@router.get("/connections/{connection_id}/accounts")
async def get_vtiger_accounts(
    connection_id: str,
    limit: int = 100,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Obtiene cuentas/organizaciones desde Vtiger"""
    conn = _vtiger_connections.get(connection_id) or (
        _get_connection_from_env() if connection_id == "vtiger_env" else None
    )
    
    if not conn:
        raise HTTPException(status_code=404, detail="Conexión no encontrada")
    
    client = create_vtiger_client(
        base_url=conn["base_url"],
        username=conn["username"],
        access_key=conn["access_key"]
    )
    
    result = await client.get_accounts(limit=limit)
    await client.close()
    
    return result


@router.get("/connections/{connection_id}/opportunities")
async def get_vtiger_opportunities(
    connection_id: str,
    limit: int = 100,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Obtiene oportunidades desde Vtiger"""
    conn = _vtiger_connections.get(connection_id) or (
        _get_connection_from_env() if connection_id == "vtiger_env" else None
    )
    
    if not conn:
        raise HTTPException(status_code=404, detail="Conexión no encontrada")
    
    client = create_vtiger_client(
        base_url=conn["base_url"],
        username=conn["username"],
        access_key=conn["access_key"]
    )
    
    result = await client.get_opportunities(limit=limit)
    await client.close()
    
    return result


@router.get("/modules")
async def list_vtiger_modules(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Lista los módulos disponibles para sincronización"""
    return {
        "modules": [
            {"code": "Leads", "name": "Leads", "description": "Prospectos de ventas"},
            {"code": "Contacts", "name": "Contactos", "description": "Contactos de clientes"},
            {"code": "Accounts", "name": "Cuentas", "description": "Organizaciones/Empresas"},
            {"code": "Potentials", "name": "Oportunidades", "description": "Oportunidades de negocio"},
            {"code": "Products", "name": "Productos", "description": "Catálogo de productos"},
            {"code": "Quotes", "name": "Cotizaciones", "description": "Cotizaciones"},
            {"code": "SalesOrder", "name": "Pedidos", "description": "Órdenes de venta"},
            {"code": "Invoice", "name": "Facturas", "description": "Facturas"}
        ]
    }


# ==================== SINCRONIZACIÓN ====================

@router.post("/sync/execute")
async def execute_vtiger_sync_manual(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Ejecuta sincronización manual con Vtiger CRM.
    Sincroniza todos los módulos configurados (Leads, Contactos, Cuentas, Oportunidades).
    """
    from core.scheduler.jobs.vtiger_sync_job import execute_vtiger_sync
    
    try:
        result = await execute_vtiger_sync(None)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@router.get("/sync/status")
async def get_vtiger_sync_status(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Obtiene el estado de la última sincronización"""
    from core.scheduler.jobs.vtiger_sync_job import get_vtiger_sync_status
    
    try:
        return await get_vtiger_sync_status()
    except Exception as e:
        return {"error": str(e), "last_sync": None}


@router.get("/sync/config")
async def get_vtiger_sync_config(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Obtiene la configuración de sincronización automática"""
    return {
        "interval_minutes": int(os.environ.get("SCHEDULER_VTIGER_SYNC_INTERVAL_SECONDS", "900")) // 60,
        "enabled": os.environ.get("SCHEDULER_VTIGER_SYNC_ENABLED", "true").lower() == "true",
        "modules": ["Leads", "Contacts", "Accounts", "Potentials"],
        "direction": "bidirectional"
    }
