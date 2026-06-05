"""
EDARSA HUB - Email SMTP Provider (Neubox)
=========================================
Provider de email vía SMTP para integración con Neubox.

Reemplaza SendGrid manteniendo compatibilidad con el sistema de notificaciones.

Variables de entorno requeridas:
- EMAIL_HOST: Servidor SMTP (ej: mail.tudominio.com)
- EMAIL_PORT: Puerto SMTP (ej: 587)
- EMAIL_USER: Usuario de autenticación
- EMAIL_PASSWORD: Contraseña (nunca en logs)
- EMAIL_USE_TLS: true/false (default: true)
- EMAIL_FROM: Dirección remitente (opcional, usa EMAIL_USER si no está)
- EMAIL_FROM_NAME: Nombre visible del remitente (opcional)
"""

import os
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone

from .base import BaseProvider, ProviderResponse, ProviderFactory

logger = logging.getLogger(__name__)


class EmailSMTPProvider(BaseProvider):
    """
    Provider de email usando SMTP (compatible con Neubox).
    
    Características:
    - Conexión SMTP con TLS
    - Autenticación segura
    - Soporte para HTML y texto plano
    - Manejo de errores sin exponer credenciales
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        
        # Configuración desde config o variables de entorno
        self.host = config.get("host") or os.environ.get("EMAIL_HOST", "")
        self.port = int(config.get("port") or os.environ.get("EMAIL_PORT", "587"))
        self.user = config.get("user") or os.environ.get("EMAIL_USER", "")
        self.password = config.get("password") or os.environ.get("EMAIL_PASSWORD", "")
        self.use_tls = str(config.get("use_tls") or os.environ.get("EMAIL_USE_TLS", "true")).lower() == "true"
        
        # Remitente
        self.from_email = config.get("from_email") or os.environ.get("EMAIL_FROM") or self.user
        self.from_name = config.get("from_name") or os.environ.get("EMAIL_FROM_NAME", "EDARSA HUB")
        
        # Estado
        self._available = False
    
    def _get_provider_name(self) -> str:
        return "email_smtp"
    
    async def initialize(self) -> bool:
        """
        Verifica la configuración del provider SMTP.
        No abre conexión permanente (SMTP es por envío).
        """
        # Verificar configuración mínima
        missing = []
        if not self.host:
            missing.append("EMAIL_HOST")
        if not self.user:
            missing.append("EMAIL_USER")
        if not self.password:
            missing.append("EMAIL_PASSWORD")
        
        if missing:
            logger.warning(f"EmailSMTPProvider: Variables faltantes: {', '.join(missing)}")
            self._initialized = True
            self._available = False
            return True
        
        # Verificar conectividad (opcional, se puede omitir en producción)
        try:
            # Test rápido de conexión
            with smtplib.SMTP(self.host, self.port, timeout=10) as server:
                if self.use_tls:
                    server.starttls()
                server.login(self.user, self.password)
            
            self._initialized = True
            self._available = True
            
            # Log seguro
            masked_host = self.host
            masked_user = f"{self.user[:3]}***@{self.user.split('@')[-1]}" if '@' in self.user else f"{self.user[:3]}***"
            logger.info(f"EmailSMTPProvider inicializado: Host={masked_host}, User={masked_user}, TLS={self.use_tls}")
            
            return True
            
        except smtplib.SMTPAuthenticationError:
            logger.error("EmailSMTPProvider: Error de autenticación SMTP (credenciales incorrectas)")
            self._initialized = True
            self._available = False
            return True
        except smtplib.SMTPConnectError:
            logger.error("EmailSMTPProvider: No se pudo conectar al servidor SMTP")
            self._initialized = True
            self._available = False
            return True
        except Exception as e:
            # Log genérico sin exponer detalles sensibles
            logger.error(f"EmailSMTPProvider: Error de inicialización: {type(e).__name__}")
            self._initialized = True
            self._available = False
            return True
    
    def validate_recipient(self, recipient: str) -> Dict[str, Any]:
        """
        Valida formato de email.
        """
        if not recipient:
            return {
                "valid": False,
                "normalized": None,
                "error": "Email vacío"
            }
        
        # Validación básica
        recipient = recipient.strip().lower()
        
        if '@' not in recipient:
            return {
                "valid": False,
                "normalized": None,
                "error": "Email sin @"
            }
        
        parts = recipient.split('@')
        if len(parts) != 2 or not parts[0] or not parts[1]:
            return {
                "valid": False,
                "normalized": None,
                "error": "Formato de email inválido"
            }
        
        if '.' not in parts[1]:
            return {
                "valid": False,
                "normalized": None,
                "error": "Dominio de email inválido"
            }
        
        return {
            "valid": True,
            "normalized": recipient,
            "error": None
        }
    
    async def send_message(
        self,
        recipient: str,
        message: str,
        metadata: Optional[Dict] = None
    ) -> ProviderResponse:
        """
        Envía email vía SMTP.
        
        Para email, 'message' es el contenido y metadata puede incluir:
        - subject: Asunto del email
        - html: True si message es HTML (default: True)
        - cc: Lista de CC
        """
        metadata = metadata or {}
        subject = metadata.get("subject", "Notificación EDARSA HUB")
        is_html = metadata.get("html", True)
        cc_list = metadata.get("cc", [])
        
        return await self.send_email(
            to=recipient,
            subject=subject,
            body=message,
            is_html=is_html,
            cc=cc_list
        )
    
    async def send_email(
        self,
        to: str,
        subject: str,
        body: str,
        is_html: bool = True,
        cc: Optional[List[str]] = None
    ) -> ProviderResponse:
        """
        Envía email con parámetros específicos.
        
        Args:
            to: Destinatario principal
            subject: Asunto
            body: Contenido (HTML o texto)
            is_html: True si body es HTML
            cc: Lista opcional de CC
            
        Returns:
            ProviderResponse con resultado
        """
        # Verificar disponibilidad
        if not self._available:
            return ProviderResponse(
                success=False,
                status="failed",
                error_code="PROVIDER_NOT_AVAILABLE",
                error_message="SMTP provider no disponible (verificar configuración)"
            )
        
        # Validar destinatario
        validation = self.validate_recipient(to)
        if not validation["valid"]:
            return ProviderResponse(
                success=False,
                status="failed",
                error_code="INVALID_RECIPIENT",
                error_message=validation["error"]
            )
        
        to_email = validation["normalized"]
        
        try:
            # Construir mensaje
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"{self.from_name} <{self.from_email}>"
            msg["To"] = to_email
            
            # CC
            valid_cc = []
            if cc:
                for cc_email in cc:
                    cc_validation = self.validate_recipient(cc_email)
                    if cc_validation["valid"]:
                        valid_cc.append(cc_validation["normalized"])
                if valid_cc:
                    msg["Cc"] = ", ".join(valid_cc)
            
            # Contenido
            if is_html:
                # Agregar versión texto plano como fallback
                text_content = self._html_to_text(body)
                msg.attach(MIMEText(text_content, "plain", "utf-8"))
                msg.attach(MIMEText(body, "html", "utf-8"))
            else:
                msg.attach(MIMEText(body, "plain", "utf-8"))
            
            # Lista completa de destinatarios
            all_recipients = [to_email] + valid_cc
            
            # Enviar
            with smtplib.SMTP(self.host, self.port, timeout=30) as server:
                if self.use_tls:
                    server.starttls()
                server.login(self.user, self.password)
                server.sendmail(self.from_email, all_recipients, msg.as_string())
            
            # Log seguro
            masked_to = f"***@{to_email.split('@')[-1]}"
            logger.info(f"[SMTP] Email enviado: To={masked_to}, Subject={subject[:30]}...")
            
            # Generar ID único para tracking
            message_id = f"smtp_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')}"
            
            return ProviderResponse(
                success=True,
                message_id=message_id,
                status="sent",
                raw_response={
                    "to": to_email,
                    "cc_count": len(valid_cc),
                    "subject": subject,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            )
            
        except smtplib.SMTPAuthenticationError:
            logger.error("[SMTP] Error de autenticación al enviar email")
            return ProviderResponse(
                success=False,
                status="failed",
                error_code="AUTH_ERROR",
                error_message="Error de autenticación SMTP"
            )
        except smtplib.SMTPRecipientsRefused:
            logger.error(f"[SMTP] Destinatario rechazado")
            return ProviderResponse(
                success=False,
                status="failed",
                error_code="RECIPIENT_REFUSED",
                error_message="El servidor rechazó el destinatario"
            )
        except smtplib.SMTPServerDisconnected:
            logger.error("[SMTP] Servidor SMTP desconectado")
            return ProviderResponse(
                success=False,
                status="failed",
                error_code="SERVER_DISCONNECTED",
                error_message="Conexión con servidor SMTP perdida"
            )
        except smtplib.SMTPConnectError:
            logger.error("[SMTP] No se pudo conectar al servidor SMTP")
            return ProviderResponse(
                success=False,
                status="failed",
                error_code="CONNECTION_ERROR",
                error_message="No se pudo conectar al servidor SMTP"
            )
        except TimeoutError:
            logger.error("[SMTP] Timeout al enviar email")
            return ProviderResponse(
                success=False,
                status="failed",
                error_code="TIMEOUT",
                error_message="Timeout en conexión SMTP"
            )
        except Exception as e:
            # Log genérico sin exponer detalles sensibles
            logger.error(f"[SMTP] Error enviando email: {type(e).__name__}")
            return ProviderResponse(
                success=False,
                status="failed",
                error_code="SMTP_ERROR",
                error_message="Error al enviar email"
            )
    
    def _html_to_text(self, html: str) -> str:
        """Convierte HTML básico a texto plano."""
        import re
        # Remover tags HTML
        text = re.sub(r'<br\s*/?>', '\n', html, flags=re.IGNORECASE)
        text = re.sub(r'</p>', '\n\n', text, flags=re.IGNORECASE)
        text = re.sub(r'<[^>]+>', '', text)
        # Decodificar entidades comunes
        text = text.replace('&nbsp;', ' ')
        text = text.replace('&amp;', '&')
        text = text.replace('&lt;', '<')
        text = text.replace('&gt;', '>')
        # Limpiar espacios múltiples
        text = re.sub(r' +', ' ', text)
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text.strip()
    
    def is_available(self) -> bool:
        """Verifica si el provider está disponible."""
        return self._available
    
    def get_status(self) -> Dict[str, Any]:
        """Obtiene información de estado del provider."""
        masked_host = self.host or "N/A"
        masked_user = None
        if self.user:
            if '@' in self.user:
                masked_user = f"{self.user[:3]}***@{self.user.split('@')[-1]}"
            else:
                masked_user = f"{self.user[:3]}***"
        
        return {
            "provider": "email_smtp",
            "initialized": self._initialized,
            "available": self._available,
            "host": masked_host,
            "port": self.port,
            "user_masked": masked_user,
            "use_tls": self.use_tls,
            "from_email": self.from_email,
            "has_credentials": bool(self.host and self.user and self.password)
        }


# Registrar en factory
ProviderFactory.register("email_smtp", EmailSMTPProvider)
ProviderFactory.register("smtp", EmailSMTPProvider)
ProviderFactory.register("neubox", EmailSMTPProvider)
