"""
EDARSA HUB - Sync Agent Receiver (FASE 1 PILOTO)
================================================

Endpoints para recibir datos de Sync Agents externos.

FASE 1 - ALCANCE PILOTO:
- POST /api/sync/kpis - Recibir KPIs de agentes
- POST /api/sync/heartbeat - Registrar heartbeat
- POST /api/admin/agents/generate-token - Generar token para agente
- GET /api/sync/test-auth - Verificar autenticación de agente

SEGURIDAD:
- Tokens JWT separados para agentes (type: "sync_agent")
- No reutiliza autenticación de usuarios
- Validación server_id en token == payload

TRAZABILIDAD:
- source.type = "SYNC_AGENT"
- Registra agent_id, server_id, timestamp

Fecha: 2026-04-23
Versión: 1.1 (Refactorizado)
"""

import os
import logging
from typing import Dict
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, HTTPException, Depends, Header
import jwt

from api.sync_schemas import (
    KPIRecord, SyncKPIsPayload, HeartbeatPayload,
    GenerateTokenRequest, GenerateTokenResponse, SyncResponse
)

# ============================================================================
# CONFIGURACIÓN
# ============================================================================

JWT_SECRET = os.environ.get('JWT_SECRET', '')
JWT_ALGORITHM = 'HS256'
AGENT_TOKEN_EXPIRATION_DAYS = 365

MODULE_NAME = "SYNC_RECEIVER"
logger = logging.getLogger(__name__)

# ============================================================================
# ROUTER & DB
# ============================================================================

router = APIRouter(tags=["Sync Agent"])

_db = None


def init_sync_receiver(database) -> None:
    """Inicializa el módulo con dependencia legacy opcional. SQL canónico es la fuente operativa."""
    global _db
    _db = database
    logger.info(f"[{MODULE_NAME}] Módulo inicializado en modo SQL-first")


def get_db():
    """Obtiene dependencia legacy opcional para compatibilidad."""
    return _db


# ============================================================================
# TOKEN HELPERS
# ============================================================================

def create_agent_token(server_id: str, agent_id: str) -> str:
    """Genera un token JWT para Sync Agents (expira en 1 año)."""
    now = datetime.now(timezone.utc)
    payload = {
        "type": "sync_agent",
        "server_id": server_id,
        "agent_id": agent_id,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(days=AGENT_TOKEN_EXPIRATION_DAYS)).timestamp())
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def verify_agent_token(token: str) -> Dict:
    """Verifica un token de Sync Agent. Raises HTTPException si inválido."""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        if payload.get("type") != "sync_agent":
            raise HTTPException(403, "Token no es de tipo sync_agent")
        return {
            "server_id": payload.get("server_id"),
            "agent_id": payload.get("agent_id"),
            "exp": payload.get("exp")
        }
    except jwt.ExpiredSignatureError:
        raise HTTPException(401, "Token de agente expirado")
    except jwt.InvalidTokenError as e:
        raise HTTPException(401, f"Token inválido: {e}")


def verify_user_admin_token(token: str) -> Dict:
    """Verifica un token de usuario admin. Raises HTTPException si inválido."""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        if payload.get("type") == "sync_agent":
            raise HTTPException(403, "Este endpoint requiere autenticación de usuario")
        user_role = payload.get("role", "").lower()
        if user_role not in ["admin", "superadmin", "supervisor", "administrador", "superadministrador"]:
            raise HTTPException(403, "Solo administradores pueden generar tokens")
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(401, "Token de usuario expirado")
    except jwt.InvalidTokenError:
        raise HTTPException(401, "Token de usuario inválido")


async def get_agent_from_token(authorization: str = Header(...)) -> Dict:
    """Dependency: extrae y valida agente del header Authorization."""
    if not authorization.startswith("Bearer "):
        raise HTTPException(401, "Header debe ser 'Bearer <token>'")
    return verify_agent_token(authorization[7:])


def validate_server_id_match(agent: Dict, payload_server_id: str) -> None:
    """Valida que server_id en token coincida con payload."""
    if agent["server_id"] != payload_server_id:
        raise HTTPException(403, f"server_id mismatch: token={agent['server_id']}, payload={payload_server_id}")


# ============================================================================
# PROCESSING HELPERS
# ============================================================================

async def process_kpi_record(
    record: KPIRecord,
    payload: SyncKPIsPayload,
    empresa_id: str,
    system_type: str,
    received_at: str
) -> Dict:
    """Procesa un registro KPI individual. Retorna {action, error}."""
    from modules.comercial.kpis_repository import upsert_kpi_comercial
    
    source_info = {
        "type": "SYNC_AGENT",
        "agent_id": payload.agent_id,
        "server_id": payload.server_id,
        "received_at": received_at,
        "agent_timestamp": payload.timestamp,
        "system_type": system_type,
        "is_pilot": True
    }
    
    result = await upsert_kpi_comercial(
        server_id=payload.server_id,
        empresa_id=empresa_id,
        sucursal_id=record.sucursal_id,
        fecha=record.fecha,
        kpis=record.kpis,
        source_info=source_info,
        updated_by=f"sync_agent:{payload.agent_id}"
    )
    return {"action": result.get("action", "ERROR"), "error": None}


def determine_agent_status(payload_status: str) -> str:
    """Mapea status del payload a status interno."""
    status_map = {"OK": "ONLINE", "SQL_LOCAL_ERROR": "SQL_ERROR"}
    return status_map.get(payload_status, "UNKNOWN")


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.post("/sync/kpis", response_model=SyncResponse)
async def sync_kpis(payload: SyncKPIsPayload, agent: Dict = Depends(get_agent_from_token)):
    """Recibe KPIs de un Sync Agent y los almacena usando UPSERT idempotente."""
    validate_server_id_match(agent, payload.server_id)
    
    from core.server_registry import get_server_connection_info
    server = get_server_connection_info(payload.server_id)
    if not server:
        raise HTTPException(404, f"Servidor {payload.server_id} no encontrado")
    
    empresa_id = server.get("empresa_id") or server.get("EmpresaID") or "default"
    system_type = server.get("system_type") or server.get("SystemType") or "UNKNOWN"
    now = datetime.now(timezone.utc)
    received_at = now.isoformat()
    
    actions = {"INSERT": 0, "UPDATE": 0, "SKIP": 0, "REJECTED": 0}
    errors = []
    
    for record in payload.records:
        try:
            result = await process_kpi_record(record, payload, empresa_id, system_type, received_at)
            action = result["action"]
            actions[action] = actions.get(action, 0) + 1
        except Exception as e:
            errors.append(f"Error {record.sucursal_id}/{record.fecha}: {e}")
            logger.error(f"[{MODULE_NAME}] UPSERT error: {e}")
    
    total = sum(actions.values())
    status = "OK" if not errors else ("PARTIAL" if total > 0 else "ERROR")
    
    logger.info(f"[{MODULE_NAME}] KPIs from {payload.agent_id}: received={len(payload.records)}, processed={total}")
    
    return SyncResponse(
        status=status,
        received=len(payload.records),
        processed=total,
        actions=actions,
        errors=errors,
        batch_id=f"batch-{payload.agent_id}-{now.strftime('%Y%m%d-%H%M%S')}",
        server_time=received_at
    )


@router.post("/sync/heartbeat")
async def sync_heartbeat(payload: HeartbeatPayload, agent: Dict = Depends(get_agent_from_token)):
    """Registra heartbeat de un Sync Agent."""
    validate_server_id_match(agent, payload.server_id)
    
    now = datetime.now(timezone.utc)
    
    logger.info(
        f"[{MODULE_NAME}] Heartbeat recibido SQL-first "
        f"agent={payload.agent_id} server={payload.server_id} status={payload.status}"
    )
    return {"status": "OK", "message": "Heartbeat registrado", "server_time": now.isoformat()}


@router.get("/sync/test-auth")
async def test_agent_auth(agent: Dict = Depends(get_agent_from_token)):
    """Verifica que el token del agente es válido."""
    return {
        "status": "OK",
        "message": "Autenticación válida",
        "agent_id": agent["agent_id"],
        "server_id": agent["server_id"],
        "token_expires": datetime.fromtimestamp(agent["exp"], tz=timezone.utc).isoformat()
    }


@router.post("/admin/agents/generate-token", response_model=GenerateTokenResponse)
async def generate_agent_token_endpoint(request: GenerateTokenRequest, authorization: str = Header(...)):
    """Genera un token JWT para un Sync Agent. Requiere autenticación de admin."""
    if not authorization.startswith("Bearer "):
        raise HTTPException(401, "Authorization requerida")
    
    verify_user_admin_token(authorization[7:])
    
    from core.server_registry import get_server_connection_info
    server = get_server_connection_info(request.server_id)
    if not server:
        raise HTTPException(404, f"Servidor {request.server_id} no encontrado")
    
    server_name = server.get("name") or server.get("Name") or request.server_id
    agent_id = request.agent_id or f"agent-{str(server_name).lower().replace(' ', '-')}-001"
    agent_token = create_agent_token(request.server_id, agent_id)
    
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(days=AGENT_TOKEN_EXPIRATION_DAYS)
    
    logger.info(
        f"[{MODULE_NAME}] Token generado SQL-first agent={agent_id} server={request.server_id}"
    )
    
    logger.info(f"[{MODULE_NAME}] Token generated for {agent_id} server {request.server_id}")
    
    return GenerateTokenResponse(
        token=agent_token,
        agent_id=agent_id,
        server_id=request.server_id,
        expires_at=expires_at.isoformat()
    )


# ============================================================================
# ÍNDICES
# ============================================================================

async def setup_sync_agent_indexes(db):
    """Compatibilidad legacy: no crea índices documentales en modo SQL-first."""
    logger.info(f"[{MODULE_NAME}] setup_sync_agent_indexes omitido: SQL-first")
