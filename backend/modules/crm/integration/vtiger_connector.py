"""
EDARSA HUB - CRM Integration: VTiger Connector
===============================================
Implementación del conector para VTiger CRM.
"""

import hashlib
import requests
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import logging
import json

from .base_connector import (
    BaseCRMConnector, LeadExterno, OportunidadExterna, CuentaExterna,
    ConnectionStatus, SyncResult
)

logger = logging.getLogger(__name__)


class VTigerConnector(BaseCRMConnector):
    """
    Conector para VTiger CRM.
    Soporta VTiger Open Source (challenge-response auth) y VTiger Cloud (basic auth).
    """
    
    @property
    def codigo(self) -> str:
        return "VTIGER"
    
    @property
    def nombre(self) -> str:
        return "VTiger CRM"
    
    def __init__(self, conector_id: int, config: Dict[str, Any]):
        super().__init__(conector_id, config)
        
        self.base_url = config.get('base_url', '').rstrip('/')
        self.username = config.get('username', '')
        self.access_key = config.get('access_key', '')
        
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/x-www-form-urlencoded',
            'Accept': 'application/json'
        })
        
        self._session_token = None
        self._user_id = None
    
    def _get_webservice_url(self) -> str:
        return f"{self.base_url}/webservice.php"
    
    # ==================== CONEXIÓN ====================
    
    def test_connection(self) -> Tuple[bool, Optional[str]]:
        """Prueba la conexión con VTiger"""
        try:
            # Intenta obtener challenge
            url = f"{self._get_webservice_url()}?operation=getchallenge&username={self.username}"
            response = self.session.get(url, timeout=15)
            
            if response.status_code != 200:
                return False, f"HTTP {response.status_code}"
            
            data = response.json()
            if not data.get('success'):
                return False, data.get('error', {}).get('message', 'Challenge failed')
            
            return True, None
            
        except requests.Timeout:
            return False, "Timeout de conexión"
        except Exception as e:
            return False, str(e)
    
    def connect(self) -> bool:
        """Establece conexión con VTiger usando challenge-response"""
        try:
            # Paso 1: Obtener challenge
            url = f"{self._get_webservice_url()}?operation=getchallenge&username={self.username}"
            response = self.session.get(url, timeout=15)
            
            if response.status_code != 200:
                self._set_error(f"HTTP {response.status_code}")
                return False
            
            data = response.json()
            if not data.get('success'):
                self._set_error(data.get('error', {}).get('message', 'Challenge failed'))
                return False
            
            challenge_token = data['result']['token']
            
            # Paso 2: Calcular accessKey
            access_key_hash = hashlib.md5(
                (challenge_token + self.access_key).encode()
            ).hexdigest()
            
            # Paso 3: Login
            login_data = {
                'operation': 'login',
                'username': self.username,
                'accessKey': access_key_hash
            }
            
            response = self.session.post(self._get_webservice_url(), data=login_data, timeout=15)
            
            if response.status_code != 200:
                self._set_error(f"Login HTTP {response.status_code}")
                return False
            
            data = response.json()
            if not data.get('success'):
                self._set_error(data.get('error', {}).get('message', 'Login failed'))
                return False
            
            self._session_token = data['result']['sessionName']
            self._user_id = data['result']['userId']
            self._set_connected()
            
            logger.info(f"[VTIGER] Conectado como {self.username}")
            return True
            
        except Exception as e:
            self._set_error(str(e))
            return False
    
    def _ensure_connected(self) -> bool:
        """Asegura que haya conexión activa"""
        if self._session_token:
            return True
        return self.connect()
    
    def _api_call(self, operation: str, params: Dict = None, method: str = 'GET') -> Optional[Dict]:
        """Realiza una llamada al webservice de VTiger"""
        if not self._ensure_connected():
            return None
        
        try:
            url = self._get_webservice_url()
            data = {'operation': operation, 'sessionName': self._session_token}
            
            if params:
                data.update(params)
            
            if method == 'GET':
                response = self.session.get(url, params=data, timeout=30)
            else:
                response = self.session.post(url, data=data, timeout=30)
            
            if response.status_code != 200:
                logger.error(f"[VTIGER] HTTP {response.status_code}")
                return None
            
            result = response.json()
            if not result.get('success'):
                error = result.get('error', {}).get('message', 'Unknown error')
                logger.error(f"[VTIGER] API Error: {error}")
                return None
            
            return result.get('result')
            
        except Exception as e:
            logger.error(f"[VTIGER] API call error: {e}")
            return None
    
    # ==================== LEADS ====================
    
    def pull_leads(self, since: Optional[datetime] = None) -> List[LeadExterno]:
        """Obtiene leads de VTiger"""
        leads = []
        
        # Query para leads
        query = "SELECT * FROM Leads"
        if since:
            query += f" WHERE modifiedtime >= '{since.strftime('%Y-%m-%d %H:%M:%S')}'"
        query += " LIMIT 100;"
        
        result = self._api_call('query', {'query': query})
        
        if not result:
            return leads
        
        for record in result:
            try:
                lead = LeadExterno(
                    external_id=record.get('id', ''),
                    nombre_contacto=record.get('firstname', ''),
                    apellido_paterno=record.get('lastname', ''),
                    nombre_empresa=record.get('company', ''),
                    email=record.get('email', ''),
                    telefono=record.get('phone', ''),
                    telefono_movil=record.get('mobile', ''),
                    puesto=record.get('designation', ''),
                    descripcion=record.get('description', ''),
                    origen=record.get('leadsource', ''),
                    estatus=record.get('leadstatus', ''),
                    fecha_modificacion=self._parse_datetime(record.get('modifiedtime')),
                    datos_adicionales=record
                )
                leads.append(lead)
            except Exception as e:
                logger.warning(f"[VTIGER] Error parsing lead: {e}")
        
        logger.info(f"[VTIGER] Obtenidos {len(leads)} leads")
        return leads
    
    def push_lead(self, lead: LeadExterno) -> Tuple[bool, Optional[str]]:
        """Crea un lead en VTiger"""
        element = {
            'firstname': lead.nombre_contacto or '',
            'lastname': lead.apellido_paterno or 'N/A',
            'company': lead.nombre_empresa or 'Sin Empresa',
            'email': lead.email or '',
            'phone': lead.telefono or '',
            'mobile': lead.telefono_movil or '',
            'designation': lead.puesto or '',
            'description': lead.descripcion or '',
            'leadsource': lead.origen or 'Web',
            'leadstatus': lead.estatus or 'New',
            'assigned_user_id': self._user_id
        }
        
        result = self._api_call('create', {
            'elementType': 'Leads',
            'element': json.dumps(element)
        }, method='POST')
        
        if result:
            external_id = result.get('id')
            logger.info(f"[VTIGER] Lead creado: {external_id}")
            return True, external_id
        
        return False, "Error creando lead"
    
    def update_lead(self, external_id: str, lead: LeadExterno) -> Tuple[bool, Optional[str]]:
        """Actualiza un lead en VTiger"""
        element = {
            'id': external_id,
            'firstname': lead.nombre_contacto or '',
            'lastname': lead.apellido_paterno or '',
            'company': lead.nombre_empresa or '',
            'email': lead.email or '',
            'phone': lead.telefono or '',
            'mobile': lead.telefono_movil or '',
            'designation': lead.puesto or '',
            'description': lead.descripcion or '',
        }
        
        result = self._api_call('update', {
            'element': json.dumps(element)
        }, method='POST')
        
        if result:
            logger.info(f"[VTIGER] Lead actualizado: {external_id}")
            return True, None
        
        return False, "Error actualizando lead"
    
    # ==================== OPORTUNIDADES ====================
    
    def pull_opportunities(self, since: Optional[datetime] = None) -> List[OportunidadExterna]:
        """Obtiene oportunidades de VTiger (Potentials)"""
        opps = []
        
        query = "SELECT * FROM Potentials"
        if since:
            query += f" WHERE modifiedtime >= '{since.strftime('%Y-%m-%d %H:%M:%S')}'"
        query += " LIMIT 100;"
        
        result = self._api_call('query', {'query': query})
        
        if not result:
            return opps
        
        for record in result:
            try:
                opp = OportunidadExterna(
                    external_id=record.get('id', ''),
                    nombre=record.get('potentialname', ''),
                    descripcion=record.get('description', ''),
                    monto_estimado=self._parse_float(record.get('amount')),
                    fecha_estimada_cierre=self._parse_date(record.get('closingdate')),
                    etapa=record.get('sales_stage', ''),
                    probabilidad=self._parse_int(record.get('probability')),
                    estatus=record.get('potentialtype', ''),
                    external_cuenta_id=record.get('related_to', ''),
                    fecha_modificacion=self._parse_datetime(record.get('modifiedtime')),
                    datos_adicionales=record
                )
                opps.append(opp)
            except Exception as e:
                logger.warning(f"[VTIGER] Error parsing opportunity: {e}")
        
        logger.info(f"[VTIGER] Obtenidas {len(opps)} oportunidades")
        return opps
    
    def push_opportunity(self, opp: OportunidadExterna) -> Tuple[bool, Optional[str]]:
        """Crea una oportunidad en VTiger"""
        element = {
            'potentialname': opp.nombre,
            'description': opp.descripcion or '',
            'amount': opp.monto_estimado or 0,
            'closingdate': opp.fecha_estimada_cierre.strftime('%Y-%m-%d') if opp.fecha_estimada_cierre else '',
            'sales_stage': self.map_stage(opp.etapa, 'push') or 'Prospecting',
            'probability': opp.probabilidad or 10,
            'assigned_user_id': self._user_id
        }
        
        if opp.external_cuenta_id:
            element['related_to'] = opp.external_cuenta_id
        
        result = self._api_call('create', {
            'elementType': 'Potentials',
            'element': json.dumps(element)
        }, method='POST')
        
        if result:
            external_id = result.get('id')
            logger.info(f"[VTIGER] Oportunidad creada: {external_id}")
            return True, external_id
        
        return False, "Error creando oportunidad"
    
    def update_opportunity(self, external_id: str, opp: OportunidadExterna) -> Tuple[bool, Optional[str]]:
        """Actualiza una oportunidad en VTiger"""
        element = {
            'id': external_id,
            'potentialname': opp.nombre,
            'description': opp.descripcion or '',
            'amount': opp.monto_estimado or 0,
            'sales_stage': self.map_stage(opp.etapa, 'push') or '',
            'probability': opp.probabilidad or 0,
        }
        
        if opp.fecha_estimada_cierre:
            element['closingdate'] = opp.fecha_estimada_cierre.strftime('%Y-%m-%d')
        
        result = self._api_call('update', {
            'element': json.dumps(element)
        }, method='POST')
        
        if result:
            logger.info(f"[VTIGER] Oportunidad actualizada: {external_id}")
            return True, None
        
        return False, "Error actualizando oportunidad"
    
    # ==================== CUENTAS ====================
    
    def pull_accounts(self, since: Optional[datetime] = None) -> List[CuentaExterna]:
        """Obtiene cuentas de VTiger (Accounts)"""
        accounts = []
        
        query = "SELECT * FROM Accounts"
        if since:
            query += f" WHERE modifiedtime >= '{since.strftime('%Y-%m-%d %H:%M:%S')}'"
        query += " LIMIT 100;"
        
        result = self._api_call('query', {'query': query})
        
        if not result:
            return accounts
        
        for record in result:
            try:
                account = CuentaExterna(
                    external_id=record.get('id', ''),
                    razon_social=record.get('accountname', ''),
                    industria=record.get('industry', ''),
                    sitio_web=record.get('website', ''),
                    email_principal=record.get('email1', ''),
                    telefono_principal=record.get('phone', ''),
                    direccion=f"{record.get('bill_street', '')} {record.get('bill_city', '')}".strip(),
                    fecha_modificacion=self._parse_datetime(record.get('modifiedtime')),
                    datos_adicionales=record
                )
                accounts.append(account)
            except Exception as e:
                logger.warning(f"[VTIGER] Error parsing account: {e}")
        
        logger.info(f"[VTIGER] Obtenidas {len(accounts)} cuentas")
        return accounts
    
    def push_account(self, account: CuentaExterna) -> Tuple[bool, Optional[str]]:
        """Crea una cuenta en VTiger"""
        element = {
            'accountname': account.razon_social,
            'industry': account.industria or '',
            'website': account.sitio_web or '',
            'email1': account.email_principal or '',
            'phone': account.telefono_principal or '',
            'assigned_user_id': self._user_id
        }
        
        result = self._api_call('create', {
            'elementType': 'Accounts',
            'element': json.dumps(element)
        }, method='POST')
        
        if result:
            external_id = result.get('id')
            logger.info(f"[VTIGER] Cuenta creada: {external_id}")
            return True, external_id
        
        return False, "Error creando cuenta"
    
    # ==================== MAPEO DE ETAPAS ====================
    
    def map_stage(self, stage_name: str, direction: str = "pull") -> Optional[str]:
        """Mapea etapas entre VTiger y CRM nativo"""
        # Mapeo VTiger -> Local
        pull_map = {
            'Prospecting': 'Nuevo',
            'Qualification': 'Calificado',
            'Needs Analysis': 'Diagnóstico',
            'Value Proposition': 'Propuesta',
            'Id. Decision Makers': 'Propuesta',
            'Perception Analysis': 'Negociación',
            'Proposal/Price Quote': 'Negociación',
            'Negotiation/Review': 'Negociación',
            'Closed Won': 'Cierre Ganado',
            'Closed Lost': 'Cierre Perdido',
        }
        
        # Mapeo Local -> VTiger
        push_map = {v: k for k, v in pull_map.items()}
        
        mapping = pull_map if direction == 'pull' else push_map
        return mapping.get(stage_name, stage_name)
    
    # ==================== HELPERS ====================
    
    def _parse_datetime(self, value: str) -> Optional[datetime]:
        """Parsea datetime de VTiger"""
        if not value:
            return None
        try:
            return datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
        except:
            return None
    
    def _parse_date(self, value: str) -> Optional[datetime]:
        """Parsea date de VTiger"""
        if not value:
            return None
        try:
            return datetime.strptime(value, '%Y-%m-%d')
        except:
            return None
    
    def _parse_float(self, value) -> Optional[float]:
        """Parsea float"""
        if value is None:
            return None
        try:
            return float(value)
        except:
            return None
    
    def _parse_int(self, value) -> Optional[int]:
        """Parsea int"""
        if value is None:
            return None
        try:
            return int(value)
        except:
            return None
