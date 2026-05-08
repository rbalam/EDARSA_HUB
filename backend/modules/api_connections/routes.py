"""
Rutas de Conexiones API Locales
===============================
Endpoints REST para gestionar conexiones a APIs locales.

ARQUITECTURA:
- Todas las operaciones CRUD van a EDARSAHUB SQL (fuente primaria)
- MongoDB solo se usa como caché/log (no autoritativo)
- Errores de EDARSAHUB SQL se propagan al cliente
- Errores de MongoDB se registran pero no bloquean la operación
"""

import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field
from typing import Optional, List

from .repository import (
    list_api_connections,
    get_api_connection,
    create_api_connection,
    update_api_connection,
    delete_api_connection,
    sync_all_to_mongo_cache,
    test_api_connection_health,
    check_duplicate_api
)

router = APIRouter(prefix="/api-connections", tags=["API Connections"])
security = HTTPBearer()


# ============================================================================
# SCHEMAS
# ============================================================================

class ApiConnectionCreate(BaseModel):
    name: str = Field(..., description="Nombre de la conexión (único)")
    url: str = Field(..., description="URL del endpoint API (único)")
    api_key: Optional[str] = Field(None, description="API Key para autenticación")
    tipo: str = Field("MPRO", description="Tipo de sistema (MPRO, SoftRestaurant)")
    servidor_padre: Optional[str] = Field(None, description="Host del servidor padre en nube")
    servidor_padre_id: Optional[str] = Field(None, description="ID del servidor padre")
    sucursal_destino: Optional[str] = Field(None, description="Nombre de la sucursal destino")
    hora_replica: str = Field("04:00", description="Hora de réplica diaria (HH:MM)")
    solo_ventas_dia: bool = Field(True, description="Solo obtener ventas del día actual")
    activo: bool = Field(True, description="Si la conexión está activa")
    visible_en_operaciones: bool = Field(False, description="Visible en módulo Operaciones")


class ApiConnectionUpdate(BaseModel):
    name: Optional[str] = None
    url: Optional[str] = None
    api_key: Optional[str] = None
    tipo: Optional[str] = None
    servidor_padre: Optional[str] = None
    servidor_padre_id: Optional[str] = None
    sucursal_destino: Optional[str] = None
    hora_replica: Optional[str] = None
    solo_ventas_dia: Optional[bool] = None
    activo: Optional[bool] = None
    visible_en_operaciones: Optional[bool] = None


class TestConnectionRequest(BaseModel):
    url: str
    api_key: Optional[str] = None


# ============================================================================
# DEPENDENCIAS
# ============================================================================

_verify_token = None

def set_verify_token(func):
    global _verify_token
    _verify_token = func

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if _verify_token is None:
        raise HTTPException(status_code=500, detail="Auth not configured")
    return _verify_token(credentials.credentials)


# ============================================================================
# ENDPOINTS - LECTURA (DESDE EDARSAHUB SQL)
# ============================================================================

@router.get("")
async def list_apis(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Lista todas las conexiones API activas.
    FUENTE: EDARSAHUB SQL (autoritativa).
    """
    get_current_user(credentials)
    try:
        apis = await list_api_connections()
        return {
            "success": True, 
            "data": apis, 
            "count": len(apis),
            "source": "EDARSAHUB_SQL"
        }
    except RuntimeError as e:
        logging.error(f"[API_CONNECTIONS] Error listando: {e}")
        raise HTTPException(status_code=503, detail=f"Error accediendo a base de datos: {e}")
    except Exception as e:
        logging.error(f"[API_CONNECTIONS] Error inesperado: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{api_id}")
async def get_api(api_id: str, credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Obtiene una conexión API por ID.
    FUENTE: EDARSAHUB SQL (autoritativa).
    """
    get_current_user(credentials)
    try:
        api = await get_api_connection(api_id)
        if not api:
            raise HTTPException(status_code=404, detail="Conexión API no encontrada en EDARSAHUB SQL")
        return {"success": True, "data": api, "source": "EDARSAHUB_SQL"}
    except HTTPException:
        raise
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=f"Error accediendo a base de datos: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# ENDPOINTS - ESCRITURA (PRIMERO EDARSAHUB SQL, LUEGO CACHÉ)
# ============================================================================

@router.post("")
async def create_api(
    data: ApiConnectionCreate,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Crea una nueva conexión API.
    DESTINO: EDARSAHUB SQL (autoritativo), luego caché MongoDB.
    """
    user = get_current_user(credentials)
    try:
        api = await create_api_connection(
            data.model_dump(),
            created_by=user.get('email', 'system')
        )
        return {
            "success": True, 
            "data": api, 
            "message": "Conexión API creada en EDARSAHUB SQL",
            "source": "EDARSAHUB_SQL"
        }
    except ValueError as e:
        # Duplicado u otro error de validación
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        # Error de base de datos
        raise HTTPException(status_code=503, detail=f"Error guardando en EDARSAHUB SQL: {e}")
    except Exception as e:
        logging.error(f"[API_CONNECTIONS] Error creando: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{api_id}")
async def update_api(
    api_id: str,
    data: ApiConnectionUpdate,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Actualiza una conexión API existente.
    DESTINO: EDARSAHUB SQL (autoritativo), luego caché MongoDB.
    """
    user = get_current_user(credentials)
    
    try:
        # Filtrar solo campos proporcionados
        update_data = {k: v for k, v in data.model_dump().items() if v is not None}
        if not update_data:
            raise HTTPException(status_code=400, detail="No se proporcionaron campos para actualizar")
        
        api = await update_api_connection(
            api_id,
            update_data,
            updated_by=user.get('email', 'system')
        )
        return {
            "success": True, 
            "data": api, 
            "message": "Conexión API actualizada en EDARSAHUB SQL",
            "source": "EDARSAHUB_SQL"
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=f"Error actualizando en EDARSAHUB SQL: {e}")
    except Exception as e:
        logging.error(f"[API_CONNECTIONS] Error actualizando: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{api_id}")
async def delete_api(api_id: str, credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Elimina (soft delete) una conexión API.
    DESTINO: EDARSAHUB SQL (autoritativo).
    """
    user = get_current_user(credentials)
    
    try:
        await delete_api_connection(api_id, deleted_by=user.get('email', 'system'))
        return {
            "success": True, 
            "message": "Conexión API eliminada de EDARSAHUB SQL",
            "source": "EDARSAHUB_SQL"
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=f"Error eliminando en EDARSAHUB SQL: {e}")
    except Exception as e:
        logging.error(f"[API_CONNECTIONS] Error eliminando: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# ENDPOINTS - UTILIDADES
# ============================================================================

@router.post("/test")
async def test_connection(
    data: TestConnectionRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Prueba la conexión a una URL de API."""
    get_current_user(credentials)
    result = await test_api_connection_health(url=data.url, api_key=data.api_key)
    return result


@router.post("/{api_id}/test")
async def test_connection_by_id(
    api_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Prueba la conexión de una API existente por ID.
    Lee configuración de EDARSAHUB SQL.
    """
    get_current_user(credentials)
    result = await test_api_connection_health(api_id=api_id)
    return result


@router.post("/sync-cache")
async def sync_to_mongo(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Sincroniza conexiones API de EDARSAHUB SQL a MongoDB caché.
    FLUJO: EDARSAHUB SQL → MongoDB (caché).
    """
    get_current_user(credentials)
    try:
        result = await sync_all_to_mongo_cache()
        return {
            "success": True, 
            "message": "Sincronización EDARSAHUB SQL → MongoDB completada", 
            **result
        }
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logging.error(f"[API_CONNECTIONS] Error sincronizando: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/check-duplicate")
async def check_dup(
    name: str = None,
    url: str = None,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Verifica si existe una conexión con el mismo nombre o URL."""
    get_current_user(credentials)
    if not name and not url:
        raise HTTPException(status_code=400, detail="Proporciona name o url")
    
    duplicate = check_duplicate_api(name or '', url or '')
    return {
        "exists": duplicate is not None,
        "duplicate": duplicate
    }
