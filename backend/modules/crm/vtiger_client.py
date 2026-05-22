"""
VTiger CRM API Client
Maneja la conexión y operaciones con VTiger CRM via REST API
Soporta tanto VTiger Cloud (Basic Auth) como VTiger Open Source (Challenge-Response)
"""

import requests
import hashlib
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
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/x-www-form-urlencoded',
            'Accept': 'application/json'
        })
        
        # Token de sesión para API webservice
        self._session_token = None
        self._user_id = None
        self._api_type = None  # 'webservice' o 'rest'
        
    def _get_webservice_url(self) -> str:
        """Retorna la URL del webservice"""
        return f"{self.base_url}/webservice.php"
    
    def _login_webservice(self) -> bool:
        """
        Autenticación challenge-response para VTiger Open Source
        
        1. GET /webservice.php?operation=getchallenge&username=xxx
        2. Calcular: md5(challenge_token + access_key)
        3. POST /webservice.php con operation=login, username, accessKey
        """
        try:
            # Paso 1: Obtener challenge
            challenge_url = f"{self._get_webservice_url()}?operation=getchallenge&username={self.username}"
            response = self.session.get(challenge_url, timeout=15)
            
            if response.status_code != 200:
                logger.error(f"[VTiger] Challenge failed: HTTP {response.status_code}")
                return False
            
            data = response.json()
            if not data.get('success'):
                logger.error(f"[VTiger] Challenge error: {data.get('error', {}).get('message', 'Unknown')}")
                return False
            
            challenge_token = data['result']['token']
            logger.info(f"[VTiger] Challenge obtenido: {challenge_token[:20]}...")
            
            # Paso 2: Calcular accessKey = md5(challenge + access_key)
            access_key_hash = hashlib.md5((challenge_token + self.access_key).encode()).hexdigest()
            
            # Paso 3: Login
            login_data = {
                'operation': 'login',
                'username': self.username,
                'accessKey': access_key_hash
            }
            
            login_response = self.session.post(self._get_webservice_url(), data=login_data, timeout=15)
            login_result = login_response.json()
            
            if login_result.get('success'):
                self._session_token = login_result['result']['sessionName']
                self._user_id = login_result['result']['userId']
                self._api_type = 'webservice'
                logger.info(f"[VTiger] Login exitoso. User ID: {self._user_id}")
                return True
            else:
                error_msg = login_result.get('error', {}).get('message', 'Unknown error')
                logger.error(f"[VTiger] Login failed: {error_msg}")
                return False
                
        except Exception as e:
            logger.error(f"[VTiger] Login exception: {e}")
            return False
    
    def _ensure_authenticated(self) -> bool:
        """Asegura que hay una sesión activa"""
        if self._session_token:
            return True
        return self._login_webservice()
    
    def test_connection(self) -> Dict[str, Any]:
        """Prueba la conexión con VTiger"""
        try:
            if self._login_webservice():
                # Obtener tipos de módulos disponibles
                modules = self._list_types()
                return {
                    "success": True,
                    "message": "Conexión exitosa",
                    "status_code": 200,
                    "api_type": self._api_type,
                    "user_id": self._user_id,
                    "modules": modules
                }
            else:
                return {
                    "success": False,
                    "message": "Error de autenticación",
                    "status_code": 401,
                    "detail": "Verifique usuario y access key"
                }
        except requests.exceptions.Timeout:
            return {"success": False, "message": "Timeout de conexión", "status_code": 0}
        except requests.exceptions.ConnectionError as e:
            return {"success": False, "message": f"Error de conexión: {str(e)[:200]}", "status_code": 0}
        except Exception as e:
            return {"success": False, "message": f"Error: {str(e)[:200]}", "status_code": 0}
    
    def _list_types(self) -> List[str]:
        """Obtiene la lista de módulos disponibles"""
        if not self._ensure_authenticated():
            return []
        
        try:
            params = {
                'operation': 'listtypes',
                'sessionName': self._session_token
            }
            response = self.session.get(self._get_webservice_url(), params=params, timeout=15)
            data = response.json()
            
            if data.get('success'):
                types_info = data.get('result', {}).get('types', [])
                return types_info if isinstance(types_info, list) else list(types_info)
            return []
        except Exception as e:
            logger.error(f"[VTiger] listtypes error: {e}")
            return []
    
    def query(self, query: str) -> Dict[str, Any]:
        """
        Ejecuta una query SQL-like en VTiger
        
        Args:
            query: Query en formato VTiger SQL (ej: "SELECT * FROM Contacts LIMIT 10;")
        """
        if not self._ensure_authenticated():
            return {"success": False, "error": "No autenticado"}
        
        try:
            params = {
                'operation': 'query',
                'sessionName': self._session_token,
                'query': query
            }
            response = self.session.get(self._get_webservice_url(), params=params, timeout=30)
            data = response.json()
            
            if data.get('success'):
                return {"success": True, "data": data.get('result', [])}
            else:
                error = data.get('error', {})
                return {"success": False, "error": error.get('message', 'Query failed')}
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
        if not self._ensure_authenticated():
            return {"success": False, "error": "No autenticado"}
        
        try:
            params = {
                'operation': 'retrieve',
                'sessionName': self._session_token,
                'id': record_id
            }
            response = self.session.get(self._get_webservice_url(), params=params, timeout=15)
            data = response.json()
            
            if data.get('success'):
                return {"success": True, "data": data.get('result', {})}
            else:
                error = data.get('error', {})
                return {"success": False, "error": error.get('message', 'Retrieve failed')}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def create_record(self, module: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crea un nuevo registro en VTiger
        
        Args:
            module: Nombre del módulo
            data: Datos del registro
        """
        if not self._ensure_authenticated():
            return {"success": False, "error": "No autenticado"}
        
        try:
            import json
            payload = {
                'operation': 'create',
                'sessionName': self._session_token,
                'elementType': module,
                'element': json.dumps(data)
            }
            response = self.session.post(self._get_webservice_url(), data=payload, timeout=30)
            result = response.json()
            
            if result.get('success'):
                return {"success": True, "data": result.get('result', {})}
            else:
                error = result.get('error', {})
                return {"success": False, "error": error.get('message', 'Create failed')}
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
        if not self._ensure_authenticated():
            return {"success": False, "error": "No autenticado"}
        
        try:
            import json
            data["id"] = record_id
            payload = {
                'operation': 'update',
                'sessionName': self._session_token,
                'element': json.dumps(data)
            }
            response = self.session.post(self._get_webservice_url(), data=payload, timeout=30)
            result = response.json()
            
            if result.get('success'):
                return {"success": True, "data": result.get('result', {})}
            else:
                error = result.get('error', {})
                return {"success": False, "error": error.get('message', 'Update failed')}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def delete_record(self, record_id: str) -> Dict[str, Any]:
        """Elimina un registro"""
        if not self._ensure_authenticated():
            return {"success": False, "error": "No autenticado"}
        
        try:
            payload = {
                'operation': 'delete',
                'sessionName': self._session_token,
                'id': record_id
            }
            response = self.session.post(self._get_webservice_url(), data=payload, timeout=15)
            result = response.json()
            
            if result.get('success'):
                return {"success": True, "message": "Registro eliminado"}
            else:
                error = result.get('error', {})
                return {"success": False, "error": error.get('message', 'Delete failed')}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_module_fields(self, module: str) -> Dict[str, Any]:
        """Obtiene los campos disponibles de un módulo"""
        if not self._ensure_authenticated():
            return {"success": False, "error": "No autenticado"}
        
        try:
            params = {
                'operation': 'describe',
                'sessionName': self._session_token,
                'elementType': module
            }
            response = self.session.get(self._get_webservice_url(), params=params, timeout=15)
            data = response.json()
            
            if data.get('success'):
                return {"success": True, "data": data.get('result', {})}
            else:
                error = data.get('error', {})
                return {"success": False, "error": error.get('message', 'Describe failed')}
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
