"""
EDARSA HUB - Sync Agent Schemas
===============================
Modelos Pydantic para el módulo Sync Receiver.
"""

from typing import Dict, Optional, List
from pydantic import BaseModel


class KPIRecord(BaseModel):
    """Registro individual de KPIs por sucursal/día."""
    sucursal_id: str
    sucursal_nombre: Optional[str] = None
    fecha: str  # YYYY-MM-DD
    kpis: Dict  # {ventas, pax, cheques, ...}


class SyncKPIsPayload(BaseModel):
    """Payload de sincronización de KPIs."""
    version: str = "1.0"
    agent_id: str
    server_id: str
    timestamp: str  # ISO format
    payload_type: str = "KPIS_DIARIOS"
    records: List[KPIRecord]


class HeartbeatPayload(BaseModel):
    """Payload de heartbeat del agente."""
    agent_id: str
    server_id: str
    timestamp: str
    status: str = "OK"  # OK | SQL_LOCAL_ERROR | CONFIG_ERROR
    last_sync: Optional[str] = None
    sql_local_status: str = "CONNECTED"  # CONNECTED | DISCONNECTED | ERROR
    queue_depth: int = 0


class GenerateTokenRequest(BaseModel):
    """Request para generar token de agente."""
    server_id: str
    agent_id: Optional[str] = None  # Si no se provee, se genera


class GenerateTokenResponse(BaseModel):
    """Response con token generado."""
    token: str
    agent_id: str
    server_id: str
    expires_at: str


class SyncResponse(BaseModel):
    """Respuesta estándar de sync."""
    status: str  # OK | PARTIAL | ERROR
    received: int
    processed: int
    actions: Dict  # {INSERT: n, UPDATE: n, SKIP: n, REJECTED: n}
    errors: List[str]
    batch_id: Optional[str] = None
    server_time: str
