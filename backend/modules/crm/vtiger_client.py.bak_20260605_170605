"""
Vtiger CRM Client - REST API con Challenge-Token Auth
======================================================
Cliente para integración con Vtiger CRM usando su API webservice.

Flujo de autenticación:
1. GET /webservice.php?operation=getchallenge&username=<USER>
2. Calcular: md5(challenge_token + access_key)
3. POST /webservice.php con operation=login, username, accessKey=md5hash
4. Usar sessionName para las siguientes operaciones

Documentación: https://community.vtiger.com/help/vtigercrm/developers/third-party-app-integration.html
"""

import httpx
import hashlib
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass
from enum import Enum
import json

logger = logging.getLogger(__name__)


class VtigerModule(str, Enum):
    """Módulos disponibles en Vtiger CRM"""
    LEADS = "Leads"
    CONTACTS = "Contacts"
    ACCOUNTS = "Accounts"
    POTENTIALS = "Potentials"  # Oportunidades
    PRODUCTS = "Products"
    SERVICES = "Services"
    QUOTES = "Quotes"
    INVOICES = "Invoice"
    SALESORDERS = "SalesOrder"


@dataclass
class VtigerConfig:
    """Configuración de conexión a Vtiger"""
    base_url: str
    username: str
    access_key: str
    timeout: int = 30


class VtigerClient:
    """
    Cliente para Vtiger CRM REST API (webservice.php)
    
    Uso:
        config = VtigerConfig(
            base_url="https://micrm.hostw3b.com",
            username="admin",
            access_key="abc123xyz"
        )
        client = VtigerClient(config)
        
        # Verificar conexión (login automático)
        result = await client.test_connection()
        
        # Obtener leads
        leads = await client.query("SELECT * FROM Leads LIMIT 10")
    """
    
    def __init__(self, config: VtigerConfig):
        self.config = config
        self.base_url = config.base_url.rstrip('/')
        self._client: Optional[httpx.AsyncClient] = None
        self._session_name: Optional[str] = None
        self._user_id: Optional[str] = None
    
    @property
    def webservice_url(self) -> str:
        """URL del webservice"""
        return f"{self.base_url}/webservice.php"
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Obtiene o crea el cliente HTTP"""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=self.config.timeout,
                headers={
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Accept": "application/json"
                }
            )
        return self._client
    
    async def close(self):
        """Cierra el cliente HTTP"""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None
        self._session_name = None
    
    # ==================== AUTENTICACIÓN ====================
    
    async def _get_challenge(self) -> Dict[str, Any]:
        """
        Paso 1: Obtener el challenge token
        GET /webservice.php?operation=getchallenge&username=<USER>
        """
        try:
            client = await self._get_client()
            params = {
                "operation": "getchallenge",
                "username": self.config.username
            }
            
            response = await client.get(self.webservice_url, params=params)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    return {
                        "success": True,
                        "token": data["result"]["token"],
                        "serverTime": data["result"].get("serverTime"),
                        "expireTime": data["result"].get("expireTime")
                    }
                else:
                    return {
                        "success": False,
                        "error": data.get("error", {}).get("message", "Error desconocido")
                    }
            else:
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}: {response.text}"
                }
        except Exception as e:
            logger.error(f"[VTIGER] Error en getchallenge: {e}")
            return {"success": False, "error": str(e)}
    
    async def login(self) -> Dict[str, Any]:
        """
        Autenticación completa con Vtiger.
        Paso 1: getchallenge
        Paso 2: login con md5(token + accessKey)
        """
        try:
            # Paso 1: Obtener challenge
            challenge = await self._get_challenge()
            if not challenge["success"]:
                return {
                    "success": False,
                    "error": f"Challenge falló: {challenge.get('error')}"
                }
            
            token = challenge["token"]
            
            # Paso 2: Calcular accessKey = md5(token + access_key)
            access_key_hash = hashlib.md5(
                (token + self.config.access_key).encode()
            ).hexdigest()
            
            # Paso 3: Login
            client = await self._get_client()
            data = {
                "operation": "login",
                "username": self.config.username,
                "accessKey": access_key_hash
            }
            
            response = await client.post(self.webservice_url, data=data)
            
            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    self._session_name = result["result"]["sessionName"]
                    self._user_id = result["result"]["userId"]
                    
                    return {
                        "success": True,
                        "sessionName": self._session_name,
                        "userId": self._user_id,
                        "user": result["result"],
                        "message": "Login exitoso"
                    }
                else:
                    error_msg = result.get("error", {}).get("message", "Error de login")
                    return {
                        "success": False,
                        "error": error_msg,
                        "message": f"Login falló: {error_msg}"
                    }
            else:
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}",
                    "message": response.text
                }
        except Exception as e:
            logger.error(f"[VTIGER] Error en login: {e}")
            return {"success": False, "error": str(e), "message": "Error de conexión"}
    
    async def _ensure_session(self) -> bool:
        """Asegura que hay una sesión activa"""
        if not self._session_name:
            result = await self.login()
            return result["success"]
        return True
    
    async def test_connection(self) -> Dict[str, Any]:
        """
        Prueba la conexión con Vtiger realizando login.
        
        Returns:
            Dict con información del usuario autenticado o error
        """
        result = await self.login()
        
        if result["success"]:
            return {
                "success": True,
                "status_code": 200,
                "user": result.get("user"),
                "message": "Conexión exitosa",
                "sessionName": result.get("sessionName")
            }
        else:
            return {
                "success": False,
                "status_code": 401 if "Invalid" in str(result.get("error", "")) else 0,
                "error": result.get("error"),
                "message": result.get("message", "Error de conexión")
            }
    
    # ==================== OPERACIONES ====================
    
    async def query(self, query_string: str) -> Dict[str, Any]:
        """
        Ejecuta una consulta VQL (Vtiger Query Language).
        
        Ejemplo: "SELECT * FROM Leads LIMIT 10"
        
        Args:
            query_string: Consulta en formato VQL
        
        Returns:
            Dict con registros o error
        """
        try:
            if not await self._ensure_session():
                return {"success": False, "error": "No se pudo establecer sesión"}
            
            client = await self._get_client()
            params = {
                "operation": "query",
                "sessionName": self._session_name,
                "query": query_string
            }
            
            response = await client.get(self.webservice_url, params=params)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    records = data.get("result", [])
                    return {
                        "success": True,
                        "count": len(records),
                        "records": records
                    }
                else:
                    return {
                        "success": False,
                        "error": data.get("error", {}).get("message", "Error en query")
                    }
            else:
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}"
                }
        except Exception as e:
            logger.error(f"[VTIGER] Error en query: {e}")
            return {"success": False, "error": str(e)}
    
    async def retrieve(self, record_id: str) -> Dict[str, Any]:
        """
        Obtiene un registro específico por ID.
        
        Args:
            record_id: ID del registro (formato: 12x345)
        """
        try:
            if not await self._ensure_session():
                return {"success": False, "error": "No se pudo establecer sesión"}
            
            client = await self._get_client()
            params = {
                "operation": "retrieve",
                "sessionName": self._session_name,
                "id": record_id
            }
            
            response = await client.get(self.webservice_url, params=params)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    return {
                        "success": True,
                        "record": data.get("result")
                    }
                else:
                    return {
                        "success": False,
                        "error": data.get("error", {}).get("message")
                    }
            else:
                return {"success": False, "error": f"HTTP {response.status_code}"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def create(self, module: VtigerModule, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crea un nuevo registro.
        
        Args:
            module: Módulo destino (Leads, Contacts, etc.)
            data: Datos del registro
        """
        try:
            if not await self._ensure_session():
                return {"success": False, "error": "No se pudo establecer sesión"}
            
            client = await self._get_client()
            
            # Preparar elemento
            element = {**data, "assigned_user_id": self._user_id}
            
            form_data = {
                "operation": "create",
                "sessionName": self._session_name,
                "element": json.dumps(element),
                "elementType": module.value
            }
            
            response = await client.post(self.webservice_url, data=form_data)
            
            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    return {
                        "success": True,
                        "record": result.get("result"),
                        "message": "Registro creado exitosamente"
                    }
                else:
                    return {
                        "success": False,
                        "error": result.get("error", {}).get("message")
                    }
            else:
                return {"success": False, "error": f"HTTP {response.status_code}"}
        except Exception as e:
            logger.error(f"[VTIGER] Error en create: {e}")
            return {"success": False, "error": str(e)}
    
    async def update(self, record_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Actualiza un registro existente.
        
        Args:
            record_id: ID del registro
            data: Datos a actualizar (debe incluir todos los campos obligatorios)
        """
        try:
            if not await self._ensure_session():
                return {"success": False, "error": "No se pudo establecer sesión"}
            
            client = await self._get_client()
            
            # Incluir ID en el elemento
            element = {**data, "id": record_id}
            
            form_data = {
                "operation": "update",
                "sessionName": self._session_name,
                "element": json.dumps(element)
            }
            
            response = await client.post(self.webservice_url, data=form_data)
            
            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    return {
                        "success": True,
                        "record": result.get("result"),
                        "message": "Registro actualizado"
                    }
                else:
                    return {
                        "success": False,
                        "error": result.get("error", {}).get("message")
                    }
            else:
                return {"success": False, "error": f"HTTP {response.status_code}"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def delete(self, record_id: str) -> Dict[str, Any]:
        """Elimina un registro"""
        try:
            if not await self._ensure_session():
                return {"success": False, "error": "No se pudo establecer sesión"}
            
            client = await self._get_client()
            
            form_data = {
                "operation": "delete",
                "sessionName": self._session_name,
                "id": record_id
            }
            
            response = await client.post(self.webservice_url, data=form_data)
            
            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    return {"success": True, "message": "Registro eliminado"}
                else:
                    return {
                        "success": False,
                        "error": result.get("error", {}).get("message")
                    }
            else:
                return {"success": False, "error": f"HTTP {response.status_code}"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # ==================== MÓDULOS ESPECÍFICOS ====================
    
    async def get_leads(self, limit: int = 100) -> Dict[str, Any]:
        """Obtiene leads"""
        return await self.query(f"SELECT * FROM Leads LIMIT {limit};")
    
    async def get_contacts(self, limit: int = 100) -> Dict[str, Any]:
        """Obtiene contactos"""
        return await self.query(f"SELECT * FROM Contacts LIMIT {limit};")
    
    async def get_accounts(self, limit: int = 100) -> Dict[str, Any]:
        """Obtiene cuentas/organizaciones"""
        return await self.query(f"SELECT * FROM Accounts LIMIT {limit};")
    
    async def get_opportunities(self, limit: int = 100) -> Dict[str, Any]:
        """Obtiene oportunidades (Potentials)"""
        return await self.query(f"SELECT * FROM Potentials LIMIT {limit};")
    
    # ==================== UTILIDADES ====================
    
    async def describe(self, module: VtigerModule) -> Dict[str, Any]:
        """Obtiene el esquema/descripción de un módulo"""
        try:
            if not await self._ensure_session():
                return {"success": False, "error": "No se pudo establecer sesión"}
            
            client = await self._get_client()
            params = {
                "operation": "describe",
                "sessionName": self._session_name,
                "elementType": module.value
            }
            
            response = await client.get(self.webservice_url, params=params)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    return {
                        "success": True,
                        "module": module.value,
                        "schema": data.get("result")
                    }
                else:
                    return {"success": False, "error": data.get("error", {}).get("message")}
            else:
                return {"success": False, "error": f"HTTP {response.status_code}"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def list_types(self) -> Dict[str, Any]:
        """Lista todos los módulos disponibles"""
        try:
            if not await self._ensure_session():
                return {"success": False, "error": "No se pudo establecer sesión"}
            
            client = await self._get_client()
            params = {
                "operation": "listtypes",
                "sessionName": self._session_name
            }
            
            response = await client.get(self.webservice_url, params=params)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    return {
                        "success": True,
                        "types": data.get("result", {}).get("types", [])
                    }
                else:
                    return {"success": False, "error": data.get("error", {}).get("message")}
            else:
                return {"success": False, "error": f"HTTP {response.status_code}"}
        except Exception as e:
            return {"success": False, "error": str(e)}


# ==================== FACTORY ====================

def create_vtiger_client(
    base_url: str,
    username: str,
    access_key: str,
    timeout: int = 30
) -> VtigerClient:
    """
    Factory para crear un cliente Vtiger.
    
    Args:
        base_url: URL de la instancia (ej: https://micrm.hostw3b.com)
        username: Usuario de Vtiger
        access_key: Access Key del usuario
        timeout: Timeout en segundos
    
    Returns:
        VtigerClient configurado
    """
    config = VtigerConfig(
        base_url=base_url,
        username=username,
        access_key=access_key,
        timeout=timeout
    )
    return VtigerClient(config)
