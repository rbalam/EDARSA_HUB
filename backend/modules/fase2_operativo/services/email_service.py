"""
Email Service - Servicio de envío de emails.
CAB-003 | Fase 2B.1

Encapsula la integración con SendGrid.
Preparado para cambiar de proveedor en el futuro.
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
    
    Actualmente usa SendGrid, pero está diseñado para
    poder cambiar de proveedor sin afectar el resto del sistema.
    """
    
    def __init__(self):
        self.api_key = os.environ.get('SENDGRID_API_KEY', '')
        self.from_email = os.environ.get('EMAIL_FROM', 'noreply@edarsa.com')
        self.from_name = os.environ.get('EMAIL_FROM_NAME', 'EDARSA HUB')
        self.enabled = os.environ.get('EMAIL_ENABLED', 'true').lower() == 'true'
        self._client = None
    
    def _get_client(self):
        """Obtiene el cliente de SendGrid (lazy initialization)."""
        if self._client is None and self.api_key:
            try:
                from sendgrid import SendGridAPIClient
                self._client = SendGridAPIClient(api_key=self.api_key)
            except Exception as e:
                logger.error(f"Error inicializando SendGrid client: {e}")
                self._client = None
        return self._client
    
    def is_configured(self) -> bool:
        """Verifica si el servicio está configurado correctamente."""
        return bool(self.api_key) and self.enabled
    
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
        
        # Verificar configuración
        if not self.api_key:
            resultado["error"] = "SENDGRID_API_KEY no configurada"
            resultado["message"] = "Email no enviado: API key no configurada"
            logger.warning(f"Email NO enviado (sin API key): {asunto} -> {destinatario}")
            return resultado
        
        # Validar destinatario
        if not destinatario or '@' not in destinatario:
            resultado["error"] = f"Destinatario inválido: {destinatario}"
            resultado["message"] = "Email no enviado: destinatario inválido"
            logger.warning(f"Email NO enviado (destinatario inválido): {destinatario}")
            return resultado
        
        try:
            from sendgrid.helpers.mail import Mail, Email, To, Content
            
            # Construir mensaje
            message = Mail(
                from_email=Email(self.from_email, self.from_name),
                to_emails=To(destinatario),
                subject=asunto,
                html_content=Content("text/html", contenido_html)
            )
            
            # Agregar CC si hay
            if destinatarios_cc:
                for cc in destinatarios_cc:
                    if cc and '@' in cc:
                        message.add_cc(Email(cc))
            
            # Enviar
            client = self._get_client()
            if not client:
                resultado["error"] = "No se pudo inicializar el cliente de SendGrid"
                resultado["message"] = "Email no enviado: error de cliente"
                return resultado
            
            response = client.send(message)
            
            resultado["status_code"] = response.status_code
            
            if response.status_code in [200, 201, 202]:
                resultado["success"] = True
                resultado["message"] = f"Email enviado correctamente (status: {response.status_code})"
                logger.info(f"✅ Email enviado: {asunto} -> {destinatario}")
            else:
                resultado["error"] = f"SendGrid respondió con status {response.status_code}"
                resultado["message"] = f"Email posiblemente no enviado (status: {response.status_code})"
                logger.warning(f"⚠️ Email status inesperado: {asunto} -> {destinatario} (status: {response.status_code})")
            
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
