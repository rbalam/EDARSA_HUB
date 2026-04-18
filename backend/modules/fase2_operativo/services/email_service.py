"""
Email Service - Servicio de envío de emails.
CAB-003 | Fase 2B.1

Encapsula la integración con SMTP (Neubox).
Mantiene compatibilidad con la interfaz anterior (SendGrid).
"""

import os
import logging
from typing import Optional, List, Dict
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class EmailServiceError(Exception):
    """Error en el servicio de email."""
    pass


class EmailService:
    """
    Servicio encapsulado de envío de emails.
    
    Usa SMTP (Neubox) para envío de emails.
    Mantiene la misma interfaz que la versión anterior (SendGrid).
    """
    
    def __init__(self):
        self.enabled = os.environ.get('EMAIL_ENABLED', 'true').lower() == 'true'
        
        # Configuración SMTP
        self.smtp_host = os.environ.get('EMAIL_HOST', '')
        self.smtp_port = int(os.environ.get('EMAIL_PORT', '587'))
        self.smtp_user = os.environ.get('EMAIL_USER', '')
        self.smtp_password = os.environ.get('EMAIL_PASSWORD', '')
        self.smtp_use_tls = os.environ.get('EMAIL_USE_TLS', 'true').lower() == 'true'
        
        # Remitente
        self.from_email = os.environ.get('EMAIL_FROM') or self.smtp_user
        self.from_name = os.environ.get('EMAIL_FROM_NAME', 'EDARSA HUB')
        
        # Provider (lazy init)
        self._provider = None
    
    def _get_provider(self):
        """Obtiene el provider SMTP (lazy initialization)."""
        if self._provider is None:
            try:
                from core.communications.providers.email_smtp_provider import EmailSMTPProvider
                
                config = {
                    "host": self.smtp_host,
                    "port": self.smtp_port,
                    "user": self.smtp_user,
                    "password": self.smtp_password,
                    "use_tls": self.smtp_use_tls,
                    "from_email": self.from_email,
                    "from_name": self.from_name,
                }
                
                self._provider = EmailSMTPProvider(config)
                
                # Inicializar sincrónicamente (verificar config)
                import asyncio
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        # Ya hay un loop corriendo, crear tarea
                        asyncio.create_task(self._provider.initialize())
                    else:
                        loop.run_until_complete(self._provider.initialize())
                except RuntimeError:
                    # No hay loop, crear uno
                    asyncio.run(self._provider.initialize())
                    
            except Exception as e:
                logger.error(f"Error inicializando EmailSMTPProvider: {e}")
                self._provider = None
        
        return self._provider
    
    def is_configured(self) -> bool:
        """Verifica si el servicio está configurado correctamente."""
        has_smtp = bool(self.smtp_host and self.smtp_user and self.smtp_password)
        return has_smtp and self.enabled
    
    async def enviar_email(
        self,
        destinatario: str,
        asunto: str,
        contenido_html: str,
        destinatarios_cc: Optional[List[str]] = None,
        metadata: Optional[Dict] = None
    ) -> Dict:
        """
        Envía un email.
        
        Args:
            destinatario: Email del destinatario principal
            asunto: Asunto del email
            contenido_html: Contenido HTML del email
            destinatarios_cc: Lista opcional de CC
            metadata: Metadata adicional para logging
        
        Returns:
            Dict con resultado: {success, message, status_code, error}
        """
        resultado = {
            "success": False,
            "message": "",
            "status_code": None,
            "error": None,
            "destinatario": destinatario,
            "asunto": asunto,
            "fecha": datetime.now(timezone.utc).isoformat()
        }
        
        # Verificar si está habilitado
        if not self.enabled:
            resultado["message"] = "Servicio de email deshabilitado (EMAIL_ENABLED=false)"
            logger.info(f"Email NO enviado (deshabilitado): {asunto} -> {destinatario}")
            return resultado
        
        # Verificar configuración SMTP
        if not self.is_configured():
            resultado["error"] = "Configuración SMTP incompleta (EMAIL_HOST, EMAIL_USER, EMAIL_PASSWORD)"
            resultado["message"] = "Email no enviado: configuración incompleta"
            logger.warning(f"Email NO enviado (sin config SMTP): {asunto} -> {destinatario}")
            return resultado
        
        # Validar destinatario
        if not destinatario or '@' not in destinatario:
            resultado["error"] = f"Destinatario inválido: {destinatario}"
            resultado["message"] = "Email no enviado: destinatario inválido"
            logger.warning(f"Email NO enviado (destinatario inválido): {destinatario}")
            return resultado
        
        try:
            provider = self._get_provider()
            
            if not provider or not provider.is_available():
                resultado["error"] = "Provider SMTP no disponible"
                resultado["message"] = "Email no enviado: provider no disponible"
                logger.warning(f"Email NO enviado (provider no disponible): {asunto} -> {destinatario}")
                return resultado
            
            # Enviar usando el provider
            response = await provider.send_email(
                to=destinatario,
                subject=asunto,
                body=contenido_html,
                is_html=True,
                cc=destinatarios_cc
            )
            
            resultado["status_code"] = 200 if response.success else 500
            
            if response.success:
                resultado["success"] = True
                resultado["message"] = f"Email enviado correctamente via SMTP"
                resultado["message_id"] = response.message_id
                logger.info(f"✅ Email enviado (SMTP): {asunto} -> {destinatario}")
            else:
                resultado["error"] = response.error_message
                resultado["message"] = f"Email no enviado: {response.error_message}"
                logger.warning(f"⚠️ Email falló (SMTP): {asunto} -> {destinatario}: {response.error_code}")
            
            return resultado
            
        except Exception as e:
            resultado["error"] = str(e)
            resultado["message"] = f"Error enviando email: {str(e)}"
            logger.error(f"❌ Error enviando email: {asunto} -> {destinatario}: {e}")
            return resultado


# Singleton instance
_email_service_instance = None


def get_email_service() -> EmailService:
    """Factory function para obtener instancia del servicio de email."""
    global _email_service_instance
    if _email_service_instance is None:
        _email_service_instance = EmailService()
    return _email_service_instance
