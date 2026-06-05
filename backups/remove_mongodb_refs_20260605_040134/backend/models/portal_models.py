"""
Modelos Pydantic para el Portal de Proveedores
NO modifica nada de EDARSA HUB - Solo define modelos nuevos
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class SupplierStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    SUSPENDED = "suspended"


class SupplierRegister(BaseModel):
    """Registro de nuevo proveedor"""
    rfc: str = Field(..., min_length=12, max_length=13)
    razon_social: str
    nombre_contacto: str
    email: str
    telefono: Optional[str] = None
    password: str = Field(..., min_length=6)
    # Datos bancarios
    banco: Optional[str] = None
    clabe: Optional[str] = None
    cuenta: Optional[str] = None


class SupplierLogin(BaseModel):
    """Login de proveedor"""
    rfc: str
    password: str


class SupplierProfile(BaseModel):
    """Perfil del proveedor"""
    id: str
    rfc: str
    razon_social: str
    nombre_contacto: str
    email: str
    telefono: Optional[str] = None
    banco: Optional[str] = None
    clabe: Optional[str] = None
    cuenta: Optional[str] = None
    status: SupplierStatus = SupplierStatus.PENDING
    sucursales_asignadas: List[str] = []
    created_at: datetime
    approved_at: Optional[datetime] = None
    approved_by: Optional[str] = None


class InvoiceUpload(BaseModel):
    """Datos de factura subida"""
    uuid: Optional[str] = None
    serie: Optional[str] = None
    folio: Optional[str] = None
    fecha_emision: Optional[str] = None
    fecha_timbrado: Optional[str] = None
    subtotal: float = 0
    iva: float = 0
    total: float = 0
    moneda: str = "MXN"
    tipo_comprobante: str = "I"
    receptor_rfc: Optional[str] = None
    receptor_nombre: Optional[str] = None


class InvoiceStatus(str, Enum):
    UPLOADED = "uploaded"
    VALIDATED = "validated"
    MATCHED = "matched"
    REJECTED = "rejected"
    PAID = "paid"


class Invoice(BaseModel):
    """Factura del proveedor"""
    id: str
    supplier_id: str
    supplier_rfc: str
    uuid: str
    serie: Optional[str] = None
    folio: Optional[str] = None
    fecha_emision: datetime
    subtotal: float
    iva: float
    total: float
    moneda: str = "MXN"
    receptor_rfc: str
    receptor_nombre: Optional[str] = None
    status: InvoiceStatus = InvoiceStatus.UPLOADED
    xml_file: Optional[str] = None
    pdf_file: Optional[str] = None
    orden_compra: Optional[str] = None
    sucursal: Optional[str] = None
    created_at: datetime
    validated_at: Optional[datetime] = None
    matched_at: Optional[datetime] = None


class PurchaseOrder(BaseModel):
    """Orden de compra"""
    folio: str
    fecha: datetime
    proveedor_codigo: str
    proveedor_nombre: str
    sucursal: str
    total: float
    status: str
    items: List[dict] = []


class SupplierApproval(BaseModel):
    """Aprobación/Rechazo de proveedor"""
    supplier_id: str
    action: str  # "approve" o "reject"
    sucursales: List[str] = []  # Sucursales asignadas si se aprueba
    notes: Optional[str] = None
