"""
CRM Service - Lógica de negocio para integración con VTiger
"""

import os
import logging
from typing import Optional, Dict, List, Any
from datetime import datetime
from .vtiger_client import VTigerClient

logger = logging.getLogger(__name__)

# Configuración por defecto desde variables de entorno
VTIGER_URL = os.environ.get('VTIGER_URL', 'https://saligula.hostw3b.com')
VTIGER_USERNAME = os.environ.get('VTIGER_USERNAME', 'admin')
VTIGER_ACCESS_KEY = os.environ.get('VTIGER_ACCESS_KEY', 'v7Wex2c3Mf9jVlJB')


class CRMService:
    """Servicio para operaciones CRM con VTiger"""
    
    _instance: Optional['CRMService'] = None
    _client: Optional[VTigerClient] = None
    
    @classmethod
    def get_instance(cls) -> 'CRMService':
        """Singleton pattern para el servicio"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    @classmethod
    def get_client(cls) -> VTigerClient:
        """Obtiene el cliente VTiger configurado"""
        if cls._client is None:
            cls._client = VTigerClient(
                base_url=VTIGER_URL,
                username=VTIGER_USERNAME,
                access_key=VTIGER_ACCESS_KEY
            )
        return cls._client
    
    @classmethod
    def reconfigure(cls, url: str, username: str, access_key: str):
        """Reconfigura el cliente con nuevas credenciales"""
        cls._client = VTigerClient(
            base_url=url,
            username=username,
            access_key=access_key
        )
        logger.info(f"[CRM] Cliente reconfigurado para {url}")
    
    # ==================== CONEXIÓN ====================
    
    @staticmethod
    def test_connection() -> Dict[str, Any]:
        """Prueba la conexión con VTiger"""
        client = CRMService.get_client()
        result = client.test_connection()
        
        if result["success"]:
            logger.info("[CRM] Conexión a VTiger exitosa")
        else:
            logger.error(f"[CRM] Error de conexión: {result.get('message')}")
        
        return result
    
    @staticmethod
    def get_connection_status() -> Dict[str, Any]:
        """Obtiene el estado de la conexión"""
        return {
            "url": VTIGER_URL,
            "username": VTIGER_USERNAME,
            "configured": bool(VTIGER_ACCESS_KEY),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    # ==================== CONTACTS ====================
    
    @staticmethod
    def get_contacts(limit: int = 100, offset: int = 0, search: Optional[str] = None) -> Dict[str, Any]:
        """Obtiene lista de contactos"""
        client = CRMService.get_client()
        
        if search:
            return client.search("Contacts", search, "lastname")
        
        return client.get_contacts(limit, offset)
    
    @staticmethod
    def get_contact(contact_id: str) -> Dict[str, Any]:
        """Obtiene un contacto por ID"""
        client = CRMService.get_client()
        return client.get_record_by_id("Contacts", contact_id)
    
    @staticmethod
    def create_contact(data: Dict[str, Any]) -> Dict[str, Any]:
        """Crea un nuevo contacto"""
        client = CRMService.get_client()
        
        # Campos requeridos para Contacts
        required = ["lastname"]
        for field in required:
            if field not in data:
                return {"success": False, "error": f"Campo requerido: {field}"}
        
        return client.create_record("Contacts", data)
    
    @staticmethod
    def update_contact(contact_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Actualiza un contacto"""
        client = CRMService.get_client()
        return client.update_record("Contacts", contact_id, data)
    
    # ==================== LEADS ====================
    
    @staticmethod
    def get_leads(limit: int = 100, offset: int = 0, search: Optional[str] = None) -> Dict[str, Any]:
        """Obtiene lista de leads"""
        client = CRMService.get_client()
        
        if search:
            return client.search("Leads", search, "lastname")
        
        return client.get_leads(limit, offset)
    
    @staticmethod
    def get_lead(lead_id: str) -> Dict[str, Any]:
        """Obtiene un lead por ID"""
        client = CRMService.get_client()
        return client.get_record_by_id("Leads", lead_id)
    
    @staticmethod
    def create_lead(data: Dict[str, Any]) -> Dict[str, Any]:
        """Crea un nuevo lead"""
        client = CRMService.get_client()
        
        required = ["lastname", "company"]
        for field in required:
            if field not in data:
                return {"success": False, "error": f"Campo requerido: {field}"}
        
        return client.create_record("Leads", data)
    
    @staticmethod
    def update_lead(lead_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Actualiza un lead"""
        client = CRMService.get_client()
        return client.update_record("Leads", lead_id, data)
    
    @staticmethod
    def convert_lead_to_contact(lead_id: str) -> Dict[str, Any]:
        """Convierte un lead en contacto"""
        client = CRMService.get_client()
        
        # Obtener datos del lead
        lead_result = client.get_record_by_id("Leads", lead_id)
        if not lead_result.get("success"):
            return lead_result
        
        lead_data = lead_result.get("data", {}).get("result", {})
        
        # Mapear campos de Lead a Contact
        contact_data = {
            "firstname": lead_data.get("firstname", ""),
            "lastname": lead_data.get("lastname", ""),
            "email": lead_data.get("email", ""),
            "phone": lead_data.get("phone", ""),
            "mobile": lead_data.get("mobile", ""),
            "description": f"Convertido desde Lead: {lead_data.get('lastname')}"
        }
        
        # Crear contacto
        return client.create_record("Contacts", contact_data)
    
    # ==================== ACCOUNTS ====================
    
    @staticmethod
    def get_accounts(limit: int = 100, offset: int = 0, search: Optional[str] = None) -> Dict[str, Any]:
        """Obtiene lista de cuentas/empresas"""
        client = CRMService.get_client()
        
        if search:
            return client.search("Accounts", search, "accountname")
        
        return client.get_accounts(limit, offset)
    
    @staticmethod
    def get_account(account_id: str) -> Dict[str, Any]:
        """Obtiene una cuenta por ID"""
        client = CRMService.get_client()
        return client.get_record_by_id("Accounts", account_id)
    
    @staticmethod
    def create_account(data: Dict[str, Any]) -> Dict[str, Any]:
        """Crea una nueva cuenta"""
        client = CRMService.get_client()
        
        if "accountname" not in data:
            return {"success": False, "error": "Campo requerido: accountname"}
        
        return client.create_record("Accounts", data)
    
    @staticmethod
    def update_account(account_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Actualiza una cuenta"""
        client = CRMService.get_client()
        return client.update_record("Accounts", account_id, data)
    
    # ==================== PRODUCTS ====================
    
    @staticmethod
    def get_products(limit: int = 100, offset: int = 0, search: Optional[str] = None) -> Dict[str, Any]:
        """Obtiene lista de productos"""
        client = CRMService.get_client()
        
        if search:
            return client.search("Products", search, "productname")
        
        return client.get_products(limit, offset)
    
    @staticmethod
    def get_product(product_id: str) -> Dict[str, Any]:
        """Obtiene un producto por ID"""
        client = CRMService.get_client()
        return client.get_record_by_id("Products", product_id)
    
    @staticmethod
    def create_product(data: Dict[str, Any]) -> Dict[str, Any]:
        """Crea un nuevo producto"""
        client = CRMService.get_client()
        
        if "productname" not in data:
            return {"success": False, "error": "Campo requerido: productname"}
        
        return client.create_record("Products", data)
    
    # ==================== INVOICES ====================
    
    @staticmethod
    def get_invoices(limit: int = 100, offset: int = 0, search: Optional[str] = None) -> Dict[str, Any]:
        """Obtiene lista de facturas"""
        client = CRMService.get_client()
        
        if search:
            return client.search("Invoice", search, "subject")
        
        return client.get_invoices(limit, offset)
    
    @staticmethod
    def get_invoice(invoice_id: str) -> Dict[str, Any]:
        """Obtiene una factura por ID"""
        client = CRMService.get_client()
        return client.get_record_by_id("Invoice", invoice_id)
    
    # ==================== METADATA ====================
    
    @staticmethod
    def get_module_fields(module: str) -> Dict[str, Any]:
        """Obtiene los campos de un módulo"""
        client = CRMService.get_client()
        return client.get_module_fields(module)
    
    @staticmethod
    def get_available_modules() -> List[str]:
        """Lista de módulos disponibles"""
        return ["Contacts", "Leads", "Accounts", "Products", "Invoice"]
    
    # ==================== SINCRONIZACIÓN ====================
    
    @staticmethod
    def get_sync_stats() -> Dict[str, Any]:
        """Obtiene estadísticas de sincronización"""
        client = CRMService.get_client()
        stats = {
            "timestamp": datetime.utcnow().isoformat(),
            "modules": {}
        }
        
        for module in ["Contacts", "Leads", "Accounts", "Products", "Invoice"]:
            try:
                result = client.query(f"SELECT COUNT(*) FROM {module};")
                if result.get("success"):
                    data = result.get("data", {})
                    # Intentar extraer el count
                    count = 0
                    if isinstance(data, dict):
                        records = data.get("result", [])
                        if records and isinstance(records, list) and len(records) > 0:
                            count = list(records[0].values())[0] if records[0] else 0
                    stats["modules"][module] = {"count": count, "status": "ok"}
                else:
                    stats["modules"][module] = {"count": 0, "status": "error", "error": result.get("error")}
            except Exception as e:
                stats["modules"][module] = {"count": 0, "status": "error", "error": str(e)}
        
        return stats
