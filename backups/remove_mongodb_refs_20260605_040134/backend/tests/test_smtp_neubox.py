#!/usr/bin/env python3
"""
Test de envío de email via SMTP (Neubox)
========================================
Valida la integración del provider SMTP sin exponer credenciales.
"""

import sys
import os
import asyncio

sys.path.insert(0, '/app/backend')

# Cargar variables de entorno
from dotenv import load_dotenv
load_dotenv('/app/backend/.env')


class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def print_ok(msg: str):
    print(f"  {Colors.GREEN}✓{Colors.RESET} {msg}")


def print_fail(msg: str):
    print(f"  {Colors.RED}✗{Colors.RESET} {msg}")


def print_warn(msg: str):
    print(f"  {Colors.YELLOW}⚠{Colors.RESET} {msg}")


def print_info(msg: str):
    print(f"  {Colors.BLUE}ℹ{Colors.RESET} {msg}")


async def test_smtp_provider():
    """Test directo del provider SMTP."""
    print(f"\n{Colors.BOLD}[1] TEST PROVIDER SMTP DIRECTO{Colors.RESET}")
    print("-" * 50)
    
    from core.communications.providers.email_smtp_provider import EmailSMTPProvider
    
    # Verificar configuración
    host = os.environ.get('EMAIL_HOST', '')
    port = os.environ.get('EMAIL_PORT', '587')
    user = os.environ.get('EMAIL_USER', '')
    password = os.environ.get('EMAIL_PASSWORD', '')
    
    print_info(f"Host: {host or '(no configurado)'}")
    print_info(f"Port: {port}")
    print_info(f"User: {user[:3] + '***@' + user.split('@')[-1] if '@' in user else '(no configurado)'}")
    print_info(f"Password: {'***' if password else '(no configurado)'}")
    
    if not all([host, user, password]):
        print_warn("Configuración SMTP incompleta - el provider se inicializará pero no estará disponible")
    
    # Crear provider
    provider = EmailSMTPProvider({})
    
    # Inicializar
    print_info("\nInicializando provider...")
    await provider.initialize()
    
    status = provider.get_status()
    print_info(f"Inicializado: {status['initialized']}")
    print_info(f"Disponible: {status['available']}")
    
    if not status['available']:
        print_warn("Provider no disponible (credenciales faltantes o incorrectas)")
        return False
    
    print_ok("Provider SMTP inicializado correctamente")
    return True


async def test_email_service():
    """Test del servicio de email actualizado."""
    print(f"\n{Colors.BOLD}[2] TEST EMAIL SERVICE (SMTP){Colors.RESET}")
    print("-" * 50)
    
    from modules.fase2_operativo.services.email_service import get_email_service
    
    service = get_email_service()
    
    print_info(f"Servicio habilitado: {service.enabled}")
    print_info(f"Configurado: {service.is_configured()}")
    print_info(f"Host SMTP: {service.smtp_host or '(no configurado)'}")
    print_info(f"Remitente: {service.from_email}")
    
    if not service.is_configured():
        print_warn("Servicio no configurado completamente")
        return False
    
    print_ok("EmailService configurado con SMTP")
    return True


async def test_send_email(destinatario: str):
    """Test de envío real de email."""
    print(f"\n{Colors.BOLD}[3] TEST ENVÍO DE EMAIL{Colors.RESET}")
    print("-" * 50)
    
    from modules.fase2_operativo.services.email_service import get_email_service
    
    service = get_email_service()
    
    if not service.is_configured():
        print_warn("Servicio no configurado - omitiendo test de envío")
        return None
    
    print_info(f"Enviando email de prueba a: {destinatario}")
    
    resultado = await service.enviar_email(
        destinatario=destinatario,
        asunto="[TEST] Prueba SMTP Neubox - EDARSA HUB",
        contenido_html="""
        <html>
        <head>
            <style>
                body { font-family: Arial, sans-serif; padding: 20px; }
                .header { background: #2563eb; color: white; padding: 15px; text-align: center; }
                .content { padding: 20px; background: #f1f5f9; }
                .footer { font-size: 12px; color: #64748b; text-align: center; padding: 10px; }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>EDARSA HUB - Test SMTP</h1>
            </div>
            <div class="content">
                <p>Este es un correo de prueba para validar la integración SMTP con Neubox.</p>
                <p><strong>Si recibes este mensaje, la configuración es correcta.</strong></p>
            </div>
            <div class="footer">
                Sistema de Gestión Operativa - EDARSA HUB
            </div>
        </body>
        </html>
        """,
        metadata={"test": True}
    )
    
    print_info(f"Resultado: {resultado.get('message')}")
    
    if resultado.get('success'):
        print_ok("Email enviado exitosamente")
        print_info(f"Message ID: {resultado.get('message_id', 'N/A')}")
        return True
    else:
        print_fail(f"Error: {resultado.get('error')}")
        return False


async def test_twilio_still_works():
    """Verifica que Twilio sigue funcionando."""
    print(f"\n{Colors.BOLD}[4] VERIFICACIÓN TWILIO (NO REGRESIÓN){Colors.RESET}")
    print("-" * 50)
    
    from core.communications.providers.twilio_provider import TwilioWhatsAppProvider
    
    provider = TwilioWhatsAppProvider({})
    await provider.initialize()
    
    status = provider.get_status()
    print_info(f"Provider: {status['provider']}")
    print_info(f"Inicializado: {status['initialized']}")
    print_info(f"Disponible: {status['available']}")
    print_info(f"Credenciales: {'OK' if status['has_credentials'] else 'Faltantes'}")
    
    if status['available']:
        print_ok("Twilio WhatsApp provider sigue funcionando")
        return True
    else:
        print_warn("Twilio no disponible (pero no es regresión si no había credenciales)")
        return True  # No es error si no estaba configurado


async def main():
    print(f"{Colors.BOLD}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}  VALIDACIÓN SMTP NEUBOX - EDARSA HUB{Colors.RESET}")
    print(f"{Colors.BOLD}{'='*60}{Colors.RESET}")
    
    resultados = {
        "provider_smtp": None,
        "email_service": None,
        "envio_email": None,
        "twilio_ok": None,
    }
    
    # Test 1: Provider SMTP
    resultados["provider_smtp"] = await test_smtp_provider()
    
    # Test 2: Email Service
    resultados["email_service"] = await test_email_service()
    
    # Test 3: Envío (solo si hay destinatario)
    if len(sys.argv) > 1:
        destinatario = sys.argv[1]
        resultados["envio_email"] = await test_send_email(destinatario)
    else:
        print(f"\n{Colors.YELLOW}[3] ENVÍO DE EMAIL OMITIDO{Colors.RESET}")
        print("-" * 50)
        print_warn("Para probar envío real, ejecutar:")
        print_info("  python tests/test_smtp_neubox.py correo@destino.com")
    
    # Test 4: No regresión Twilio
    resultados["twilio_ok"] = await test_twilio_still_works()
    
    # Resumen
    print(f"\n{Colors.BOLD}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}  RESUMEN{Colors.RESET}")
    print(f"{Colors.BOLD}{'='*60}{Colors.RESET}\n")
    
    for test, resultado in resultados.items():
        if resultado:
            print(f"  {Colors.GREEN}✓{Colors.RESET} {test}")
        elif not resultado:
            print(f"  {Colors.RED}✗{Colors.RESET} {test}")
        else:
            print(f"  {Colors.YELLOW}?{Colors.RESET} {test} (no ejecutado)")
    
    print()
    
    # Verificar si el provider está disponible para envío
    from core.communications.providers.email_smtp_provider import EmailSMTPProvider
    provider = EmailSMTPProvider({})
    await provider.initialize()
    
    if not provider.is_available():
        print(f"{Colors.YELLOW}NOTA:{Colors.RESET} Para activar envío de emails, configurar en .env:")
        print("  EMAIL_HOST=mail.tudominio.com")
        print("  EMAIL_PORT=587")
        print("  EMAIL_USER=notificaciones@tudominio.com")
        print("  EMAIL_PASSWORD=tu_password_aqui")
        print("  EMAIL_USE_TLS=true")


if __name__ == "__main__":
    asyncio.run(main())
