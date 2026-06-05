"""
EDARSA HUB - Base Provider Interface
====================================
Subfase 2B.5 - Interfaz abstracta para proveedores de mensajería.

Todos los proveedores (WhatsApp, SMS, etc.) deben implementar esta interfaz.
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)


@dataclass
class ProviderResponse:
    """
    Respuesta estandarizada de un proveedor.
    """
    success: bool
    message_id: Optional[str] = None  # ID asignado por el proveedor
    status: str = "unknown"  # sent, delivered, failed, queued
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    raw_response: Optional[Dict] = None
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    
    def to_dict(self) -> Dict:
        return {
            "success": self.success,
            "message_id": self.message_id,
            "status": self.status,
            "error_code": self.error_code,
            "error_message": self.error_message,
            "timestamp": self.timestamp
        }


class BaseProvider(ABC):
    """
    Interfaz base para proveedores de mensajería.
    
    Todos los proveedores deben implementar:
    - send_message: Envío de mensaje
    - validate_recipient: Validación de destinatario
    - get_status: Consulta de estado (opcional)
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Inicializa el proveedor con su configuración.
        
        Args:
            config: Diccionario con configuración del proveedor
        """
        self.config = config
        self.provider_name = self._get_provider_name()
        self._initialized = False
    
    @abstractmethod
    def _get_provider_name(self) -> str:
        """Retorna el nombre del proveedor."""
        pass
    
    @abstractmethod
    async def initialize(self) -> bool:
        """
        Inicializa la conexión con el proveedor.
        
        Returns:
            True si la inicialización fue exitosa
        """
        pass
    
    @abstractmethod
    async def send_message(
        self,
        recipient: str,
        message: str,
        metadata: Optional[Dict] = None
    ) -> ProviderResponse:
        """
        Envía un mensaje al destinatario.
        
        Args:
            recipient: Teléfono/identificador del destinatario
            message: Contenido del mensaje
            metadata: Datos adicionales opcionales
            
        Returns:
            ProviderResponse con resultado del envío
        """
        pass
    
    @abstractmethod
    def validate_recipient(self, recipient: str) -> Dict[str, Any]:
        """
        Valida formato del destinatario.
        
        Args:
            recipient: Teléfono/identificador a validar
            
        Returns:
            Dict con:
            - valid: bool
            - normalized: str (formato normalizado)
            - error: Optional[str]
        """
        pass
    
    async def get_message_status(self, message_id: str) -> Optional[ProviderResponse]:
        """
        Consulta el estado de un mensaje enviado.
        
        Args:
            message_id: ID del mensaje
            
        Returns:
            ProviderResponse con estado actual o None si no soportado
        """
        logger.warning(f"get_message_status no implementado para {self.provider_name}")
        return None
    
    async def send_bulk(
        self,
        recipients: List[str],
        message: str,
        metadata: Optional[Dict] = None
    ) -> List[ProviderResponse]:
        """
        Envía mensaje a múltiples destinatarios.
        Implementación por defecto: envío secuencial.
        
        Args:
            recipients: Lista de destinatarios
            message: Contenido del mensaje
            metadata: Datos adicionales
            
        Returns:
            Lista de ProviderResponse
        """
        responses = []
        for recipient in recipients:
            response = await self.send_message(recipient, message, metadata)
            responses.append(response)
        return responses
    
    def is_initialized(self) -> bool:
        """Verifica si el proveedor está inicializado."""
        return self._initialized
    
    def get_config_value(self, key: str, default: Any = None) -> Any:
        """Obtiene un valor de configuración."""
        return self.config.get(key, default)


class ProviderFactory:
    """
    Factory para crear instancias de proveedores.
    """
    
    _providers: Dict[str, type] = {}
    
    @classmethod
    def register(cls, name: str, provider_class: type):
        """Registra un proveedor."""
        cls._providers[name] = provider_class
        logger.info(f"Provider registrado: {name}")
    
    @classmethod
    def create(cls, name: str, config: Dict[str, Any]) -> Optional[BaseProvider]:
        """
        Crea una instancia de proveedor.
        
        Args:
            name: Nombre del proveedor
            config: Configuración
            
        Returns:
            Instancia del proveedor o None si no existe
        """
        provider_class = cls._providers.get(name)
        if provider_class is None:
            logger.error(f"Provider no registrado: {name}")
            return None
        return provider_class(config)
    
    @classmethod
    def list_providers(cls) -> List[str]:
        """Lista proveedores registrados."""
        return list(cls._providers.keys())
