"""
P3-02 Sync Monitor Routes - SQL-First
Endpoint GET /api/admin/sync-monitor
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any
import logging

from .service import get_sync_monitor_data

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["Admin - Sync Monitor"])


@router.get("/sync-monitor")
async def get_sync_monitor() -> Dict[str, Any]:
    """
    Monitor de Sincronización SQL-First.
    
    Retorna estado consolidado de todas las sincronizaciones
    usando SOLO tablas existentes en EDARSAHUB SQL.
    
    NO usa MongoDB.
    NO usa conexiones LIVE.
    
    Returns:
        {
            "servidores": [...],
            "procesos": [...],
            "errores": [...],
            "ultimos_syncs": [],
            "kpis": {...}
        }
    """
    try:
        data = get_sync_monitor_data()
        return data
    except Exception as e:
        logger.error(f"[SYNC_MONITOR] Error en endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sync-monitor/kpis")
async def get_sync_monitor_kpis() -> Dict[str, Any]:
    """
    Solo KPIs del monitor de sincronización.
    Versión ligera para dashboards.
    """
    try:
        data = get_sync_monitor_data()
        return {
            "success": data.get("success", False),
            "source": data.get("source"),
            "generated_at": data.get("generated_at"),
            "kpis": data.get("kpis", {}),
        }
    except Exception as e:
        logger.error(f"[SYNC_MONITOR] Error en kpis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sync-monitor/servidor/{server_id}")
async def get_sync_monitor_servidor(server_id: str) -> Dict[str, Any]:
    """
    Detalle de sincronización para un servidor específico.
    """
    try:
        data = get_sync_monitor_data()
        
        # Filtrar por servidor
        servidor = next((s for s in data.get("servidores", []) if s["server_id"] == server_id), None)
        procesos = [p for p in data.get("procesos", []) if p["server_id"] == server_id]
        errores = [e for e in data.get("errores", []) if e["server_id"] == server_id]
        ultimos = [u for u in data.get("ultimos_syncs", []) if u["server_id"] == server_id]
        
        if not servidor:
            raise HTTPException(status_code=404, detail="Servidor no encontrado")
        
        return {
            "success": True,
            "source": data.get("source"),
            "servidor": servidor,
            "procesos": procesos,
            "errores": errores,
            "ultimos_syncs": ultimos,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[SYNC_MONITOR] Error detalle servidor: {e}")
        raise HTTPException(status_code=500, detail=str(e))
