"""
CRM Routes - Endpoints básicos del CRM Enterprise
NOTA: Las rutas principales del CRM están en native_routes.py y comercial_routes.py
Este archivo mantiene solo endpoints de estado/configuración.
"""

from fastapi import APIRouter, Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import logging

from .service import CRMService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/crm", tags=["CRM - Estado"])
security = HTTPBearer()


# ==================== ESTADO ====================

@router.get("/status")
async def get_crm_status(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Obtiene el estado del CRM Enterprise"""
    return CRMService.get_connection_status()

@router.get("/test-connection")
async def test_crm_connection(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verifica conexión del CRM con EDARSAHUB SQL"""
    return CRMService.test_connection()

@router.get("/stats")
async def get_crm_stats(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Obtiene estadísticas del CRM"""
    return CRMService.get_sync_stats()

@router.get("/modules")
async def get_available_modules(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Lista los módulos CRM disponibles"""
    return {"modules": CRMService.get_available_modules()}
