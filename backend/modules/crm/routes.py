"""
CRM Routes - Endpoints para integración con VTiger CRM
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from typing import Optional, Dict, Any, List
from pydantic import BaseModel
import logging

from .service import CRMService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/crm", tags=["CRM - VTiger"])
security = HTTPBearer()


# ==================== SCHEMAS ====================

class ConnectionConfig(BaseModel):
    url: str
    username: str
    access_key: str

class ContactCreate(BaseModel):
    firstname: Optional[str] = None
    lastname: str
    email: Optional[str] = None
    phone: Optional[str] = None
    mobile: Optional[str] = None
    title: Optional[str] = None
    department: Optional[str] = None
    description: Optional[str] = None

class LeadCreate(BaseModel):
    firstname: Optional[str] = None
    lastname: str
    company: str
    email: Optional[str] = None
    phone: Optional[str] = None
    mobile: Optional[str] = None
    leadsource: Optional[str] = None
    leadstatus: Optional[str] = None
    description: Optional[str] = None

class AccountCreate(BaseModel):
    accountname: str
    phone: Optional[str] = None
    email1: Optional[str] = None
    website: Optional[str] = None
    industry: Optional[str] = None
    description: Optional[str] = None

class ProductCreate(BaseModel):
    productname: str
    product_no: Optional[str] = None
    unit_price: Optional[float] = None
    qty_per_unit: Optional[int] = None
    description: Optional[str] = None


# ==================== CONEXIÓN ====================

@router.get("/status")
async def get_crm_status(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Obtiene el estado de la conexión CRM"""
    return CRMService.get_connection_status()

@router.get("/test-connection")
async def test_crm_connection(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Prueba la conexión con VTiger"""
    result = CRMService.test_connection()
    if not result.get("success"):
        raise HTTPException(status_code=503, detail=result.get("message", "Error de conexión"))
    return result

@router.post("/configure")
async def configure_crm(config: ConnectionConfig, credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Configura las credenciales de VTiger"""
    try:
        CRMService.reconfigure(config.url, config.username, config.access_key)
        result = CRMService.test_connection()
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=f"No se pudo conectar: {result.get('message')}")
        return {"success": True, "message": "Configuración actualizada", "connection": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats")
async def get_crm_stats(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Obtiene estadísticas del CRM"""
    return CRMService.get_sync_stats()

@router.get("/modules")
async def get_available_modules(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Lista los módulos disponibles"""
    return {"modules": CRMService.get_available_modules()}

@router.get("/modules/{module}/fields")
async def get_module_fields(module: str, credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Obtiene los campos de un módulo"""
    result = CRMService.get_module_fields(module)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Error obteniendo campos"))
    return result


# ==================== CONTACTS ====================

@router.get("/contacts")
async def get_contacts(
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    search: Optional[str] = None,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Obtiene lista de contactos"""
    result = CRMService.get_contacts(limit, offset, search)
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error", "Error obteniendo contactos"))
    return result

@router.get("/contacts/{contact_id}")
async def get_contact(contact_id: str, credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Obtiene un contacto por ID"""
    result = CRMService.get_contact(contact_id)
    if not result.get("success"):
        raise HTTPException(status_code=404, detail=result.get("error", "Contacto no encontrado"))
    return result

@router.post("/contacts")
async def create_contact(contact: ContactCreate, credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Crea un nuevo contacto"""
    result = CRMService.create_contact(contact.dict(exclude_none=True))
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Error creando contacto"))
    return result

@router.put("/contacts/{contact_id}")
async def update_contact(contact_id: str, contact: ContactCreate, credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Actualiza un contacto"""
    result = CRMService.update_contact(contact_id, contact.dict(exclude_none=True))
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Error actualizando contacto"))
    return result


# ==================== LEADS ====================

@router.get("/leads")
async def get_leads(
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    search: Optional[str] = None,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Obtiene lista de leads/prospectos"""
    result = CRMService.get_leads(limit, offset, search)
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error", "Error obteniendo leads"))
    return result

@router.get("/leads/{lead_id}")
async def get_lead(lead_id: str, credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Obtiene un lead por ID"""
    result = CRMService.get_lead(lead_id)
    if not result.get("success"):
        raise HTTPException(status_code=404, detail=result.get("error", "Lead no encontrado"))
    return result

@router.post("/leads")
async def create_lead(lead: LeadCreate, credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Crea un nuevo lead"""
    result = CRMService.create_lead(lead.dict(exclude_none=True))
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Error creando lead"))
    return result

@router.put("/leads/{lead_id}")
async def update_lead(lead_id: str, lead: LeadCreate, credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Actualiza un lead"""
    result = CRMService.update_lead(lead_id, lead.dict(exclude_none=True))
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Error actualizando lead"))
    return result

@router.post("/leads/{lead_id}/convert")
async def convert_lead(lead_id: str, credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Convierte un lead en contacto"""
    result = CRMService.convert_lead_to_contact(lead_id)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Error convirtiendo lead"))
    return result


# ==================== ACCOUNTS ====================

@router.get("/accounts")
async def get_accounts(
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    search: Optional[str] = None,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Obtiene lista de cuentas/empresas"""
    result = CRMService.get_accounts(limit, offset, search)
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error", "Error obteniendo cuentas"))
    return result

@router.get("/accounts/{account_id}")
async def get_account(account_id: str, credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Obtiene una cuenta por ID"""
    result = CRMService.get_account(account_id)
    if not result.get("success"):
        raise HTTPException(status_code=404, detail=result.get("error", "Cuenta no encontrada"))
    return result

@router.post("/accounts")
async def create_account(account: AccountCreate, credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Crea una nueva cuenta"""
    result = CRMService.create_account(account.dict(exclude_none=True))
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Error creando cuenta"))
    return result

@router.put("/accounts/{account_id}")
async def update_account(account_id: str, account: AccountCreate, credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Actualiza una cuenta"""
    result = CRMService.update_account(account_id, account.dict(exclude_none=True))
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Error actualizando cuenta"))
    return result


# ==================== PRODUCTS ====================

@router.get("/products")
async def get_products(
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    search: Optional[str] = None,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Obtiene lista de productos"""
    result = CRMService.get_products(limit, offset, search)
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error", "Error obteniendo productos"))
    return result

@router.get("/products/{product_id}")
async def get_product(product_id: str, credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Obtiene un producto por ID"""
    result = CRMService.get_product(product_id)
    if not result.get("success"):
        raise HTTPException(status_code=404, detail=result.get("error", "Producto no encontrado"))
    return result

@router.post("/products")
async def create_product(product: ProductCreate, credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Crea un nuevo producto"""
    result = CRMService.create_product(product.dict(exclude_none=True))
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Error creando producto"))
    return result


# ==================== INVOICES ====================

@router.get("/invoices")
async def get_invoices(
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    search: Optional[str] = None,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Obtiene lista de facturas"""
    result = CRMService.get_invoices(limit, offset, search)
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error", "Error obteniendo facturas"))
    return result

@router.get("/invoices/{invoice_id}")
async def get_invoice(invoice_id: str, credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Obtiene una factura por ID"""
    result = CRMService.get_invoice(invoice_id)
    if not result.get("success"):
        raise HTTPException(status_code=404, detail=result.get("error", "Factura no encontrada"))
    return result
