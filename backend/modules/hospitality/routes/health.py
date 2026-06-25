"""
EDARSAHUB Hospitality - Health Stub
Fase 1: stub seguro, sin lógica operativa, sin tablas nuevas, sin conexión externa.
"""

from fastapi import APIRouter

router = APIRouter(prefix="/api/hospitality", tags=["Hospitality"])

@router.get("/health")
async def hospitality_health():
    return {
        "module": "hospitality",
        "status": "stub_ready",
        "phase": "fase_1_preparacion",
        "sql_first": True,
        "mongo": False,
        "live_operativo": False
    }
