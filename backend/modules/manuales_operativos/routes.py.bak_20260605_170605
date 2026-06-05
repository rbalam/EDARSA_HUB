"""
Rutas de Manuales Operativos - EDARSA HUB

Endpoints para consultar y exportar manuales operativos
generados automáticamente al cerrar procesos.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from typing import Optional, Dict
import logging

from core.security import get_current_user

from .service import ManualOperativoService
from .schemas import (
    ManualOperativoResponse,
    ManualOperativoListResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/manuales-operativos", tags=["Manuales Operativos"])

# Referencia a la DB (se inicializa desde server.py)
_db = None


def init_manuales_module(db):
    """Inicializa el módulo con la conexión a MongoDB."""
    global _db
    _db = db
    logger.info("Módulo de Manuales Operativos inicializado")


async def get_service() -> ManualOperativoService:
    """Obtiene instancia del servicio."""
    if _db is None:
        raise HTTPException(status_code=500, detail="Módulo no inicializado")
    return ManualOperativoService(_db)


@router.get("", response_model=ManualOperativoListResponse)
async def listar_manuales(
    modulo: Optional[str] = Query(None, description="Filtrar por módulo (compras, operaciones, etc.)"),
    empresa_id: Optional[str] = Query(None, description="Filtrar por empresa"),
    limite: int = Query(50, ge=1, le=100),
    skip: int = Query(0, ge=0),
    current_user: Dict = Depends(get_current_user)
):
    """
    Lista los manuales operativos disponibles.
    
    Filtros opcionales:
    - modulo: compras, operaciones, finanzas, etc.
    - empresa_id: ID de la empresa
    """
    service = await get_service()
    return await service.listar_manuales(
        modulo=modulo,
        empresa_id=empresa_id,
        limite=limite,
        skip=skip
    )


@router.get("/{manual_id}", response_model=ManualOperativoResponse)
async def obtener_manual(
    manual_id: str,
    current_user: Dict = Depends(get_current_user)
):
    """Obtiene un manual operativo por su ID."""
    service = await get_service()
    manual = await service.obtener_manual(manual_id)
    
    if not manual:
        raise HTTPException(status_code=404, detail="Manual no encontrado")
    
    return manual


@router.get("/proceso/{proceso_id}", response_model=ManualOperativoResponse)
async def obtener_manual_por_proceso(
    proceso_id: str,
    current_user: Dict = Depends(get_current_user)
):
    """Obtiene el manual asociado a un proceso específico."""
    service = await get_service()
    manual = await service.obtener_manual_por_proceso(proceso_id)
    
    if not manual:
        raise HTTPException(status_code=404, detail="No existe manual para este proceso")
    
    return manual


@router.get("/{manual_id}/exportar")
async def exportar_manual_texto(
    manual_id: str,
    current_user: Dict = Depends(get_current_user)
):
    """
    Exporta un manual en formato texto plano.
    
    Útil para:
    - Imprimir
    - Enviar por email
    - Archivar
    """
    service = await get_service()
    texto = await service.generar_texto_plano(manual_id)
    
    if not texto:
        raise HTTPException(status_code=404, detail="Manual no encontrado")
    
    return Response(
        content=texto,
        media_type="text/plain; charset=utf-8",
        headers={
            "Content-Disposition": f"attachment; filename=manual_{manual_id}.txt"
        }
    )


@router.post("/generar/{proceso_id}")
async def generar_manual_manual(
    proceso_id: str,
    modulo: str = Query(..., description="Módulo del proceso (compras, operaciones, etc.)"),
    current_user: Dict = Depends(get_current_user)
):
    """
    Genera manualmente un manual para un proceso.
    
    Normalmente los manuales se generan automáticamente al cerrar procesos,
    pero este endpoint permite regenerar o generar bajo demanda.
    """
    if _db is None:
        raise HTTPException(status_code=500, detail="Módulo no inicializado")
    
    service = ManualOperativoService(_db)
    
    if modulo == "compras":
        # Obtener proceso y bitácora
        proceso = await _db.automatizaciones_operativas_compras.find_one({"id": proceso_id})
        if not proceso:
            raise HTTPException(status_code=404, detail="Proceso no encontrado")
        
        bitacora = await _db.automatizaciones_bitacora.find(
            {"automatizacion_id": proceso_id}
        ).sort("fecha", 1).to_list(100)
        
        manual = await service.generar_manual_auditoria_compras(proceso, bitacora)
        
        if manual:
            return {"status": "success", "manual_id": manual.id, "mensaje": "Manual generado exitosamente"}
        else:
            raise HTTPException(status_code=500, detail="Error generando manual")
    else:
        raise HTTPException(status_code=400, detail=f"Módulo '{modulo}' no soportado aún")


__all__ = ['router', 'init_manuales_module']
