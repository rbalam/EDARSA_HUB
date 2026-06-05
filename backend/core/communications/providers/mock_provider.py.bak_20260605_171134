"""
EDARSA HUB - Mock Provider
==========================
Subfase 2B.5 - Proveedor de pruebas para desarrollo y testing.

Simula el envío de mensajes sin conexión real.
Registra todos los "envíos" para verificación.
"""

from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
import logging
import uuid
import re

from .base import BaseProvider, ProviderResponse, ProviderFactory

logger = logging.getLogger(__name__)


class MockProvider(BaseProvider):
    """
    Proveedor mock para pruebas.
    
    NO envía mensajes reales.
    Guarda todo en memoria/log para verificación.
    """
    
    # Almacén en memoria para verificación de tests
    _sent_messages: List[Dict] = []
    
    def _get_provider_name(self) -> str:
        return "mock"
    
    async def initialize(self) -> bool:
        """Mock siempre inicializa correctamente."""
        self._initialized = True
        logger.info("MockProvider inicializado")
        return True
    
    def validate_recipient(self, recipient: str) -> Dict[str, Any]:
        """
        Valida formato de teléfono.
        Acepta formatos:
        - +521234567890 (E.164)
        - 521234567890
        - 1234567890 (asume MX)
        """
        if not recipient:
            return {
                "valid": False,
                "normalized": None,
                "error": "Teléfono vacío"
            }
        
        # Limpiar caracteres no numéricos excepto +
        cleaned = re.sub(r'[^\d+]', '', recipient)
        
        # Normalizar a formato E.164
        if cleaned.startswith('+'):
            normalized = cleaned
        elif cleaned.startswith('52') and len(cleaned) >= 12:
            normalized = '+' + cleaned
        elif len(cleaned) == 10:
            # Asumir México
            normalized = '+52' + cleaned
        else:
            return {
                "valid": False,
                "normalized": None,
                "error": f"Formato de teléfono inválido: {recipient}"
            }
        
        # Validar longitud final
        if len(normalized) < 12 or len(normalized) > 15:
            return {
                "valid": False,
                "normalized": None,
                "error": f"Longitud de teléfono inválida: {len(normalized)} dígitos"
            }
        
        return {
            "valid": True,
            "normalized": normalized,
            "error": None
        }
    
    async def send_message(
        self,
        recipient: str,
        message: str,
        metadata: Optional[Dict] = None
    ) -> ProviderResponse:
        """
        Simula envío de mensaje.
        
        Guarda en memoria para verificación posterior.
        """
        # Validar destinatario
        validation = self.validate_recipient(recipient)
        if not validation["valid"]:
            return ProviderResponse(
                success=False,
                status="failed",
                error_code="INVALID_RECIPIENT",
                error_message=validation["error"]
            )
        
        # Simular envío
        message_id = f"mock_{uuid.uuid4().hex[:12]}"
        timestamp = datetime.now(timezone.utc).isoformat()
        
        # Guardar en memoria
        sent_record = {
            "message_id": message_id,
            "recipient": validation["normalized"],
            "message": message,
            "metadata": metadata or {},
            "timestamp": timestamp,
            "provider": "mock"
        }
        MockProvider._sent_messages.append(sent_record)
        
        logger.info(
            f"[MOCK] Mensaje simulado enviado: "
            f"ID={message_id}, "
            f"destinatario={validation['normalized'][-4:]}****, "
            f"longitud={len(message)}"
        )
        
        return ProviderResponse(
            success=True,
            message_id=message_id,
            status="sent",
            raw_response={"mock": True, "record": sent_record}
        )
    
    async def get_message_status(self, message_id: str) -> Optional[ProviderResponse]:
        """Busca estado de mensaje en memoria."""
        for record in MockProvider._sent_messages:
            if record["message_id"] == message_id:
                return ProviderResponse(
                    success=True,
                    message_id=message_id,
                    status="delivered",  # Mock siempre "entrega"
                    raw_response=record
                )
        return None
    
    # =========================================================================
    # MÉTODOS AUXILIARES PARA TESTING
    # =========================================================================
    
    @classmethod
    def get_sent_messages(cls) -> List[Dict]:
        """Obtiene todos los mensajes enviados (para testing)."""
        return cls._sent_messages.copy()
    
    @classmethod
    def get_messages_to(cls, recipient: str) -> List[Dict]:
        """Obtiene mensajes enviados a un destinatario específico."""
        # Normalizar el recipient para comparación
        cleaned = re.sub(r'[^\d]', '', recipient)
        return [
            msg for msg in cls._sent_messages
            if cleaned in msg["recipient"]
        ]
    
    @classmethod
    def clear_sent_messages(cls):
        """Limpia el historial de mensajes (para testing)."""
        cls._sent_messages = []
        logger.info("[MOCK] Historial de mensajes limpiado")
    
    @classmethod
    def get_message_count(cls) -> int:
        """Obtiene cantidad de mensajes enviados."""
        return len(cls._sent_messages)


# Registrar en factory
ProviderFactory.register("mock", MockProvider)
