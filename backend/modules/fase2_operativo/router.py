"""
FASE 2A - Router Principal Módulo Operativo
CAB-003 | EDARSA HUB

Prefijo previsto: /api/v2 (se registrará en server.py en Subfase 2A.7)

NOTA: Este router NO está registrado en server.py todavía.
Solo existe como esqueleto para validar la estructura del módulo.
"""
from fastapi import APIRouter

router_fase2_operativo = APIRouter()


@router_fase2_operativo.get("/health")
async def health_check():
    """
    Health check del módulo operativo.
    Permite verificar que el módulo está correctamente cargado.
    """
    return {
        "status": "ok",
        "module": "fase2_operativo",
        "version": "2A",
        "description": "Módulo Operativo de Automatización de Inventarios"
    }
