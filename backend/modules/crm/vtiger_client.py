"""
VTiger CRM API Client
Maneja la conexión y operaciones con VTiger CRM via REST API
"""

import requests
from requests.auth import HTTPBasicAuth
from typing import Optional, Dict, List, Any
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class VTigerClient:
    """Cliente para interactuar con VTiger CRM REST API"""
    
    def __init__(self, base_url: str, username: str, access_key: str):
        """
        Inicializa el cliente de VTiger
        
        Args:
            base_url: URL base de VTiger (ej: https://saligula.hostw3b.com)
            username: Usuario de VTiger
            access_key: Access Key del usuario
        """
        self.base_url = base_url.rstrip('/')
        self.username = username
        self.access_key = access_key
        self.auth = HTTPBasicAuth(username, access_key)
        self.session = requests.Session()
        self.session.auth = self.auth
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
        
        # Detectar el tipo de API (Cloud vs On-Premise)
        self._api_base = self._detect_api_endpoint()
    
    def _detect_api_endpoint(self) -> str:
        """Detecta el endpoint correcto de la API"""
        # Intentar endpoint de VTiger Cloud
        endpoints = [
            f"{self.base_url}/restapi/v1/vtiger/default",
            f"{self.base_url}/webservice.php",
            f"{self.base_url}/modules/Webservices/api.php"
        ]
        
        for endpoint in endpoints:
            try:
                # Probar con una operación simple
                response = self.session.get(
                    endpoint,
                    params={"operation": "listtypes"},
                    timeout=10
                )
                if response.status_code == 200:
                    logger.info(f"[VTiger] API endpoint detectado: {endpoint}")
                    return endpoint
            except Exception as e:
                logger.debug(f"[VTiger] Endpoint {endpoint} no disponible: {e}")
                continue
        
        # Default al primer endpoint
        return endpoints[0]
    
    def test_connection(self) -> Dict[str, Any]:
        """Prueba la conexión con VTiger"""
        try:
            # Intentar obtener tipos de módulos disponibles
            response = self.session.get(
                self._api_base,
                params={"operation": "listtypes"},
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json() if response.text else {}
                return {
                    "success": True,
                    "message": "Conexión exitosa",
                    "status_code": response.status_code,
                    "modules": data.get("result", {}).get("types", []) if isinstance(data, dict) else []
                }
            else:
                return {
                    "success": False,
                    "message": f"Error HTTP {response.status_code}",
                    "status_code": response.status_code,
                    "detail": response.text[:500]
                }
        except requests.exceptions.Timeout:
            return {"success": False, "message": "Timeout de conexión", "status_code": 0}
        except requests.exceptions.ConnectionError as e:
            return {"success": False, "message": f"Error de conexión: {str(e)[:200]}", "status_code": 0}
        except Exception as e:
            return {"success": False, "message": f"Error: {str(e)[:200]}", "status_code": 0}
    
    def query(self, query: str) -> Dict[str, Any]:
        """
        Ejecuta una query SQL-like en VTiger
        
        Args:
            query: Query en formato VTiger SQL (ej: "SELECT * FROM Contacts LIMIT 10;")
        """
        try:
            response = self.session.get(
                f"{self._api_base}/query",
                params={"query": query},
                timeout=30
            )
            response.raise_for_status()
            return {"success": True, "data": response.json()}
        except requests.exceptions.HTTPError as e:
            logger.error(f"[VTiger] Query error: {e}")
            return {"success": False, "error": str(e), "status_code": e.response.status_code if e.response else 0}
        except Exception as e:
            logger.error(f"[VTiger] Query exception: {e}")
            return {"success": False, "error": str(e)}
    
    def get_records(self, module: str, limit: int = 100, offset: int = 0, 
                    fields: Optional[List[str]] = None, 
                    conditions: Optional[str] = None) -> Dict[str, Any]:
        """
        Obtiene registros de un módulo
        
        Args:
            module: Nombre del módulo (Contacts, Leads, Accounts, etc.)
            limit: Número máximo de registros
            offset: Offset para paginación
            fields: Lista de campos a obtener (None = todos)
            conditions: Condiciones WHERE adicionales
        """
        field_list = ", ".join(fields) if fields else "*"
        query = f"SELECT {field_list} FROM {module}"
        
        if conditions:
            query += f" WHERE {conditions}"
        
        query += f" LIMIT {offset}, {limit};"
        
        return self.query(query)
    
    def get_record_by_id(self, module: str, record_id: str) -> Dict[str, Any]:
        """Obtiene un registro específico por ID"""
        try:
            response = self.session.get(
                f"{self._api_base}/retrieve",
                params={"id": record_id},
                timeout=15
            )
            response.raise_for_status()
            return {"success": True, "data": response.json()}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def create_record(self, module: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crea un nuevo registro en VTiger
        
        Args:
            module: Nombre del módulo
            data: Datos del registro
        """
        try:
            payload = {
                "elementType": module,
                "element": data
            }
            response = self.session.post(
                f"{self._api_base}/create",
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            return {"success": True, "data": response.json()}
        except requests.exceptions.HTTPError as e:
            return {"success": False, "error": str(e), "detail": e.response.text if e.response else ""}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def update_record(self, module: str, record_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Actualiza un registro existente
        
        Args:
            module: Nombre del módulo
            record_id: ID del registro
            data: Datos a actualizar
        """
        try:
            data["id"] = record_id
            payload = {
                "elementType": module,
                "element": data
            }
            response = self.session.post(
                f"{self._api_base}/update",
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            return {"success": True, "data": response.json()}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def delete_record(self, record_id: str) -> Dict[str, Any]:
        """Elimina un registro"""
        try:
            response = self.session.post(
                f"{self._api_base}/delete",
                json={"id": record_id},
                timeout=15
            )
            response.raise_for_status()
            return {"success": True, "message": "Registro eliminado"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_module_fields(self, module: str) -> Dict[str, Any]:
        """Obtiene los campos disponibles de un módulo"""
        try:
            response = self.session.get(
                f"{self._api_base}/describe",
                params={"elementType": module},
                timeout=15
            )
            response.raise_for_status()
            return {"success": True, "data": response.json()}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # Métodos específicos por módulo
    def get_contacts(self, limit: int = 100, offset: int = 0) -> Dict[str, Any]:
        """Obtiene contactos"""
        return self.get_records("Contacts", limit, offset)
    
    def get_leads(self, limit: int = 100, offset: int = 0) -> Dict[str, Any]:
        """Obtiene leads/prospectos"""
        return self.get_records("Leads", limit, offset)
    
    def get_accounts(self, limit: int = 100, offset: int = 0) -> Dict[str, Any]:
        """Obtiene cuentas/empresas"""
        return self.get_records("Accounts", limit, offset)
    
    def get_products(self, limit: int = 100, offset: int = 0) -> Dict[str, Any]:
        """Obtiene productos"""
        return self.get_records("Products", limit, offset)
    
    def get_invoices(self, limit: int = 100, offset: int = 0) -> Dict[str, Any]:
        """Obtiene facturas"""
        return self.get_records("Invoice", limit, offset)
    
    def search(self, module: str, search_term: str, field: str = "name") -> Dict[str, Any]:
        """Busca registros por un campo"""
        query = f"SELECT * FROM {module} WHERE {field} LIKE '%{search_term}%' LIMIT 50;"
        return self.query(query)
