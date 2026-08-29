from core.unidades_service import UnidadesService
from core.corporate_filters.service import CorporateFilterService
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
from typing import List

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


class TestQueryRequest(BaseModel):
    """Request para probar consulta SQL asociada a una conexión."""
    sql_query: str = Field(..., description="Consulta SQL (solo SELECT)")
    tipo_uso: str = Field("Otro", description="Tipo de uso: Ventas del día, Inventario, Cortes, Compras, Otro")
    nombre_consulta: Optional[str] = Field(None, description="Nombre descriptivo de la consulta")
    timeout: int = Field(30, ge=5, le=120, description="Timeout en segundos")


class TestQueryDraftRequest(BaseModel):
    """Request para probar consulta sin conexión guardada (alta nueva)."""
    url: str = Field(..., description="URL del endpoint API")
    api_key: Optional[str] = Field(None, description="API Key")
    sql_query: str = Field(..., description="Consulta SQL (solo SELECT)")
    timeout: int = Field(30, ge=5, le=120, description="Timeout en segundos")


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
        raise HTTPException(status_code=503, detail=f"Error accediendo a base de datos")
    except Exception as e:
        logging.error(f"[API_CONNECTIONS] Error inesperado: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")


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
        raise HTTPException(status_code=503, detail=f"Error accediendo a base de datos")
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error interno del servidor")


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
        raise HTTPException(status_code=400, detail="Error interno del servidor")
    except RuntimeError as e:
        # Error de base de datos
        raise HTTPException(status_code=503, detail=f"Error guardando en EDARSAHUB SQL")
    except Exception as e:
        logging.error(f"[API_CONNECTIONS] Error creando: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")


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
        raise HTTPException(status_code=400, detail="Error interno del servidor")
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=f"Error actualizando en EDARSAHUB SQL")
    except Exception as e:
        logging.error(f"[API_CONNECTIONS] Error actualizando: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")


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
        raise HTTPException(status_code=404, detail="Error interno del servidor")
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=f"Error eliminando en EDARSAHUB SQL")
    except Exception as e:
        logging.error(f"[API_CONNECTIONS] Error eliminando: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")


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
    Mantiene compatibilidad del endpoint de conexiones API.

    EDARSAHUB SQL es la única fuente canónica.
    No existe sincronización secundaria MongoDB.
    """
    get_current_user(credentials)
    try:
        result = await sync_all_to_mongo_cache()
        return {
            "success": True,
            "message": "Conexiones API verificadas en EDARSAHUB SQL",
            **result
        }
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail="Error interno del servidor")
    except Exception as e:
        logging.error(f"[API_CONNECTIONS] Error sincronizando: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")


# ============================================================================
# ENDPOINTS - TEST QUERY (CONSULTAS SQL CONTROLADAS)
# ============================================================================

@router.post("/{api_id}/test-query")
async def test_query_by_connection(
    api_id: str,
    data: TestQueryRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Prueba una consulta SQL contra una conexión API existente.

    SEGURIDAD:
    - Valida SQL (solo SELECT permitido)
    - Usa credenciales cifradas de la conexión
    - No requiere API key en request
    - Registra auditoría

    RESTRICCIONES:
    - Solo usuarios autenticados
    - Solo consultas SELECT
    - Bloquea: DELETE, UPDATE, INSERT, DROP, ALTER, TRUNCATE, EXEC, xp_, sp_
    """
    user = get_current_user(credentials)

    # Importar función de ejecución
    from .repository import execute_test_query

    try:
        result = await execute_test_query(
            api_id=api_id,
            sql_query=data.sql_query,
            timeout=data.timeout,
            executed_by=user.get('email', 'anonymous')
        )

        # Agregar metadata
        result['connection_id'] = api_id
        result['tipo_uso'] = data.tipo_uso
        result['nombre_consulta'] = data.nombre_consulta

        return result

    except Exception as e:
        logging.error(f"[API_CONNECTIONS][TEST-QUERY] Error: {e}")
        raise HTTPException(status_code=500, detail="Error ejecutando consulta")


@router.post("/test-query-draft")
async def test_query_draft(
    data: TestQueryDraftRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Prueba una consulta SQL sin conexión guardada (para alta nueva).

    Requiere URL y opcionalmente API key.

    SEGURIDAD:
    - Valida SQL (solo SELECT permitido)
    - No guarda credenciales
    - Registra auditoría
    """
    import time
    import requests
    from modules.consultas_sql.validator import get_validator

    user = get_current_user(credentials)

    # 1. Validar SQL
    validator = get_validator()
    validation = validator.validate_sql_text(data.sql_query, strict_mode=True)

    if not validation.is_valid:
        errors = [e['message'] for e in validation.errors]
        return {
            "success": False,
            "error": "SQL no válido",
            "validation_errors": errors,
            "sql_blocked": True
        }

    # 2. Ejecutar consulta
    start_time = time.time()

    try:
        headers = {"x-api-key": data.api_key} if data.api_key else {}

        response = requests.get(
            data.url,
            headers=headers,
            params={"sql": data.sql_query},
            timeout=data.timeout
        )

        elapsed_ms = round((time.time() - start_time) * 1000, 2)

        if response.status_code == 200:
            try:
                response_data = response.json()

                rows = []
                columns = []

                if isinstance(response_data, list):
                    rows = response_data[:20]
                    if rows and isinstance(rows[0], dict):
                        columns = list(rows[0].keys())
                elif isinstance(response_data, dict):
                    if 'data' in response_data:
                        rows = response_data['data'][:20] if isinstance(response_data['data'], list) else []
                    elif 'results' in response_data:
                        rows = response_data['results'][:20] if isinstance(response_data['results'], list) else []
                    if rows and isinstance(rows[0], dict):
                        columns = list(rows[0].keys())

                return {
                    "success": True,
                    "status_code": 200,
                    "response_time_ms": elapsed_ms,
                    "rows_count": len(rows),
                    "columns": columns,
                    "preview_data": rows,
                    "message": f"Consulta ejecutada ({len(rows)} filas)"
                }

            except Exception:
                return {
                    "success": True,
                    "status_code": 200,
                    "response_time_ms": elapsed_ms,
                    "message": "Respuesta no es JSON válido"
                }
        else:
            return {
                "success": False,
                "status_code": response.status_code,
                "response_time_ms": elapsed_ms,
                "error": f"HTTP {response.status_code}"
            }

    except requests.exceptions.Timeout:
        return {
            "success": False,
            "error": f"Timeout ({data.timeout}s)"
        }
    except requests.exceptions.ConnectionError:
        return {
            "success": False,
            "error": "Sin conexión a la API"
        }
    except Exception as e:
        logging.error(f"[API_CONNECTIONS][TEST-QUERY-DRAFT] Error: {e}")
        raise HTTPException(status_code=500, detail="Error ejecutando consulta")
