"""
EDARSA HUB - CRM Integration Framework
======================================
Base abstracta para conectores CRM externos.
Cada conector implementa esta interfaz para sync bidireccional.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class SyncDirection(str, Enum):
    """Dirección de sincronización"""
    ENTRANTE = "ENTRANTE"       # CRM externo -> EDARSA
    SALIENTE = "SALIENTE"       # EDARSA -> CRM externo
    BIDIRECCIONAL = "BIDIRECCIONAL"


class SyncStatus(str, Enum):
    """Estado de sincronización"""
    PENDIENTE = "PENDIENTE"
    EN_PROCESO = "EN_PROCESO"
    SINCRONIZADO = "SINCRONIZADO"
    ERROR = "ERROR"
    CONFLICTO = "CONFLICTO"


class ConnectionStatus(str, Enum):
    """Estado de conexión del conector"""
    CONECTADO = "CONECTADO"
    ERROR = "ERROR"
    PENDIENTE = "PENDIENTE"
    DESCONECTADO = "DESCONECTADO"


@dataclass
class SyncResult:
    """Resultado de una operación de sincronización"""
    success: bool
    registros_procesados: int = 0
    registros_creados: int = 0
    registros_actualizados: int = 0
    registros_error: int = 0
    registros_conflicto: int = 0
    errores: List[str] = None
    duracion_segundos: int = 0
    
    def __post_init__(self):
        if self.errores is None:
            self.errores = []


@dataclass
class LeadExterno:
    """Estructura normalizada de Lead externo"""
    external_id: str
    nombre_contacto: str
    apellido_paterno: Optional[str] = None
    apellido_materno: Optional[str] = None
    nombre_empresa: Optional[str] = None
    email: Optional[str] = None
    telefono: Optional[str] = None
    telefono_movil: Optional[str] = None
    puesto: Optional[str] = None
    descripcion: Optional[str] = None
    origen: Optional[str] = None
    estatus: Optional[str] = None
    fecha_modificacion: Optional[datetime] = None
    datos_adicionales: Optional[Dict] = None


@dataclass
class OportunidadExterna:
    """Estructura normalizada de Oportunidad externa"""
    external_id: str
    nombre: str
    descripcion: Optional[str] = None
    monto_estimado: Optional[float] = None
    moneda: str = "MXN"
    fecha_estimada_cierre: Optional[datetime] = None
    etapa: Optional[str] = None
    probabilidad: Optional[int] = None
    estatus: Optional[str] = None
    external_cuenta_id: Optional[str] = None
    external_contacto_id: Optional[str] = None
    external_lead_id: Optional[str] = None
    fecha_modificacion: Optional[datetime] = None
    datos_adicionales: Optional[Dict] = None


@dataclass
class CuentaExterna:
    """Estructura normalizada de Cuenta/Cliente externo"""
    external_id: str
    razon_social: str
    nombre_comercial: Optional[str] = None
    rfc: Optional[str] = None
    industria: Optional[str] = None
    sitio_web: Optional[str] = None
    email_principal: Optional[str] = None
    telefono_principal: Optional[str] = None
    direccion: Optional[str] = None
    fecha_modificacion: Optional[datetime] = None
    datos_adicionales: Optional[Dict] = None


class BaseCRMConnector(ABC):
    """
    Clase base abstracta para conectores CRM.
    Clase base abstracta para conectores externos (deprecada - CRM opera SQL-First).
    """
    
    def __init__(self, conector_id: int, config: Dict[str, Any]):
        """
        Inicializa el conector
        
        Args:
            conector_id: ID en tabla CRM_Integracion_Conectores
            config: Configuración del conector (URL, credenciales, etc.)
        """
        self.conector_id = conector_id
        self.config = config
        self._connection_status = ConnectionStatus.PENDIENTE
        self._last_error: Optional[str] = None
    
    @property
    @abstractmethod
    def codigo(self) -> str:
        """Código único del conector (VTIGER, SALESFORCE, etc.)"""
        pass
    
    @property
    @abstractmethod
    def nombre(self) -> str:
        """Nombre descriptivo del conector"""
        pass
    
    @property
    def connection_status(self) -> ConnectionStatus:
        return self._connection_status
    
    @property
    def last_error(self) -> Optional[str]:
        return self._last_error
    
    # ==================== CONEXIÓN ====================
    
    @abstractmethod
    def test_connection(self) -> Tuple[bool, Optional[str]]:
        """
        Prueba la conexión con el CRM externo
        
        Returns:
            Tuple de (éxito, mensaje_error)
        """
        pass
    
    @abstractmethod
    def connect(self) -> bool:
        """
        Establece la conexión con el CRM externo
        
        Returns:
            True si la conexión fue exitosa
        """
        pass
    
    def disconnect(self) -> None:
        """Cierra la conexión (si aplica)"""
        self._connection_status = ConnectionStatus.DESCONECTADO
    
    # ==================== LEADS ====================
    
    @abstractmethod
    def pull_leads(self, since: Optional[datetime] = None) -> List[LeadExterno]:
        """
        Obtiene leads del CRM externo
        
        Args:
            since: Solo leads modificados desde esta fecha
            
        Returns:
            Lista de leads normalizados
        """
        pass
    
    @abstractmethod
    def push_lead(self, lead: LeadExterno) -> Tuple[bool, Optional[str]]:
        """
        Envía un lead al CRM externo
        
        Args:
            lead: Lead a enviar
            
        Returns:
            Tuple de (éxito, external_id o mensaje_error)
        """
        pass
    
    @abstractmethod
    def update_lead(self, external_id: str, lead: LeadExterno) -> Tuple[bool, Optional[str]]:
        """
        Actualiza un lead en el CRM externo
        
        Args:
            external_id: ID del lead en el CRM externo
            lead: Datos actualizados
            
        Returns:
            Tuple de (éxito, mensaje_error)
        """
        pass
    
    # ==================== OPORTUNIDADES ====================
    
    @abstractmethod
    def pull_opportunities(self, since: Optional[datetime] = None) -> List[OportunidadExterna]:
        """
        Obtiene oportunidades del CRM externo
        
        Args:
            since: Solo oportunidades modificadas desde esta fecha
            
        Returns:
            Lista de oportunidades normalizadas
        """
        pass
    
    @abstractmethod
    def push_opportunity(self, opp: OportunidadExterna) -> Tuple[bool, Optional[str]]:
        """
        Envía una oportunidad al CRM externo
        
        Args:
            opp: Oportunidad a enviar
            
        Returns:
            Tuple de (éxito, external_id o mensaje_error)
        """
        pass
    
    @abstractmethod
    def update_opportunity(self, external_id: str, opp: OportunidadExterna) -> Tuple[bool, Optional[str]]:
        """
        Actualiza una oportunidad en el CRM externo
        
        Args:
            external_id: ID de la oportunidad en el CRM externo
            opp: Datos actualizados
            
        Returns:
            Tuple de (éxito, mensaje_error)
        """
        pass
    
    # ==================== CUENTAS/CLIENTES ====================
    
    @abstractmethod
    def pull_accounts(self, since: Optional[datetime] = None) -> List[CuentaExterna]:
        """
        Obtiene cuentas/clientes del CRM externo
        
        Args:
            since: Solo cuentas modificadas desde esta fecha
            
        Returns:
            Lista de cuentas normalizadas
        """
        pass
    
    @abstractmethod
    def push_account(self, account: CuentaExterna) -> Tuple[bool, Optional[str]]:
        """
        Envía una cuenta al CRM externo
        
        Args:
            account: Cuenta a enviar
            
        Returns:
            Tuple de (éxito, external_id o mensaje_error)
        """
        pass
    
    # ==================== HELPERS ====================
    
    def map_field(self, field_name: str, value: Any, direction: str = "pull") -> Any:
        """
        Mapea un campo entre sistemas
        
        Args:
            field_name: Nombre del campo
            value: Valor a mapear
            direction: 'pull' (externo->local) o 'push' (local->externo)
            
        Returns:
            Valor mapeado
        """
        # Subclases pueden sobrescribir para mapeos específicos
        return value
    
    def map_stage(self, stage_name: str, direction: str = "pull") -> Optional[str]:
        """
        Mapea una etapa entre sistemas
        
        Args:
            stage_name: Nombre de la etapa
            direction: 'pull' o 'push'
            
        Returns:
            Nombre de etapa mapeada
        """
        # Subclases implementan mapeo específico
        return stage_name
    
    def _set_connected(self) -> None:
        """Marca el conector como conectado"""
        self._connection_status = ConnectionStatus.CONECTADO
        self._last_error = None
    
    def _set_error(self, message: str) -> None:
        """Marca el conector con error"""
        self._connection_status = ConnectionStatus.ERROR
        self._last_error = message
        logger.error(f"[{self.codigo}] Error: {message}")
