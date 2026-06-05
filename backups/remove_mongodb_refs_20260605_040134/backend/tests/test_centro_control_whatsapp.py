"""
EDARSA HUB - Test Suite for Centro de Control WhatsApp Notifications (Twilio)
==============================================================================

Tests for Centro de Control WhatsApp notification endpoints:
- GET /api/centro-control/whatsapp/config - WhatsApp/Twilio configuration status
- POST /api/centro-control/whatsapp/test - Send test WhatsApp message
- GET /api/centro-control/notificaciones/config - All notification services status

Expected behavior:
- twilio_configured: true (TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_WHATSAPP_FROM are set)
- configured: false (ALERT_WHATSAPP_TO is empty - no recipients)
- Test message will fail without recipients configured
"""

import pytest
import requests
import os
from tests.test_config import test_config

# Base URL from environment
BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials from centralized config
ADMIN_EMAIL = test_config.TEST_ADMIN_EMAIL
ADMIN_PASSWORD = test_config.TEST_ADMIN_PASSWORD


class TestCentroControlAuth:
    """Authentication helper for Centro de Control endpoints"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token for admin user"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        # Token field is 'token' not 'access_token'
        token = data.get("token")
        assert token, f"No token in response: {data}"
        return token
    
    @pytest.fixture(scope="class")
    def auth_headers(self, auth_token):
        """Get headers with auth token"""
        return {"Authorization": f"Bearer {auth_token}"}


class TestCentroControlPing:
    """Test Centro de Control ping endpoint (no auth required)"""
    
    def test_ping_endpoint_accessible(self):
        """GET /api/centro-control/ping - should return status ok without auth"""
        response = requests.get(f"{BASE_URL}/api/centro-control/ping")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data["status"] == "ok", f"Expected status=ok, got {data.get('status')}"
        assert data["service"] == "CENTRO DE CONTROL EDARSA"
        assert "version" in data
        assert "timestamp" in data
        print(f"✅ Ping successful: {data['service']} v{data['version']}")


class TestWhatsAppConfig(TestCentroControlAuth):
    """Tests for WhatsApp configuration endpoint"""
    
    def test_whatsapp_config_requires_auth(self):
        """GET /api/centro-control/whatsapp/config - should require authentication"""
        response = requests.get(f"{BASE_URL}/api/centro-control/whatsapp/config")
        assert response.status_code in [401, 403], f"Expected 401/403 without auth, got {response.status_code}"
        print("✅ WhatsApp config endpoint correctly requires authentication")
    
    def test_whatsapp_config_returns_status(self, auth_headers):
        """GET /api/centro-control/whatsapp/config - should return Twilio config status"""
        response = requests.get(
            f"{BASE_URL}/api/centro-control/whatsapp/config",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "service" in data, "Response should have 'service' key"
        assert "config" in data, "Response should have 'config' key"
        
        config = data["config"]
        print(f"WhatsApp Config: {config}")
        
        # Verify expected fields
        assert "configured" in config, "Config should have 'configured' field"
        assert "enabled" in config, "Config should have 'enabled' field"
        assert "twilio_configured" in config, "Config should have 'twilio_configured' field"
        assert "from_number" in config, "Config should have 'from_number' field"
        assert "recipients_count" in config, "Config should have 'recipients_count' field"
        
        print("✅ WhatsApp config retrieved successfully")
        print(f"   - Service: {data['service']}")
        print(f"   - Twilio Configured: {config['twilio_configured']}")
        print(f"   - Enabled: {config['enabled']}")
        print(f"   - Configured (with recipients): {config['configured']}")
        print(f"   - From Number: {config['from_number']}")
        print(f"   - Recipients Count: {config['recipients_count']}")
    
    def test_twilio_credentials_configured(self, auth_headers):
        """Verify Twilio credentials are properly configured (twilio_configured: true)"""
        response = requests.get(
            f"{BASE_URL}/api/centro-control/whatsapp/config",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        config = response.json()["config"]
        
        # Twilio should be configured (SID, TOKEN, FROM are set in .env)
        assert config["twilio_configured"], \
            f"Expected twilio_configured=True, got {config['twilio_configured']}. Check TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN in .env"
        
        # WhatsApp should be enabled
        assert config["enabled"], \
            f"Expected enabled=True, got {config['enabled']}. Check WHATSAPP_ENABLED in .env"
        
        # From number should be set
        assert config["from_number"] is not None, \
            "Expected from_number to be set, got None. Check TWILIO_WHATSAPP_FROM in .env"
        
        print("✅ Twilio credentials are properly configured")
        print(f"   - twilio_configured: {config['twilio_configured']}")
        print(f"   - enabled: {config['enabled']}")
        print(f"   - from_number: {config['from_number']}")
    
    def test_no_recipients_configured(self, auth_headers):
        """Verify ALERT_WHATSAPP_TO is empty (configured: false)"""
        response = requests.get(
            f"{BASE_URL}/api/centro-control/whatsapp/config",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        config = response.json()["config"]
        
        # configured should be false because ALERT_WHATSAPP_TO is empty
        assert not config["configured"], \
            f"Expected configured=False (no recipients), got {config['configured']}"
        
        assert config["recipients_count"] == 0, \
            f"Expected recipients_count=0, got {config['recipients_count']}"
        
        print("✅ Correctly reports no recipients configured")
        print(f"   - configured: {config['configured']}")
        print(f"   - recipients_count: {config['recipients_count']}")


class TestWhatsAppTestMessage(TestCentroControlAuth):
    """Tests for WhatsApp test message endpoint"""
    
    def test_whatsapp_test_requires_auth(self):
        """POST /api/centro-control/whatsapp/test - should require authentication"""
        response = requests.post(f"{BASE_URL}/api/centro-control/whatsapp/test")
        assert response.status_code in [401, 403], f"Expected 401/403 without auth, got {response.status_code}"
        print("✅ WhatsApp test endpoint correctly requires authentication")
    
    def test_whatsapp_test_fails_without_recipients(self, auth_headers):
        """POST /api/centro-control/whatsapp/test - should fail when no recipients configured"""
        response = requests.post(
            f"{BASE_URL}/api/centro-control/whatsapp/test",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        print(f"WhatsApp Test Response: {data}")
        
        # Should return success=False because no recipients configured
        assert not data["success"], \
            f"Expected success=False (no recipients), got {data.get('success')}"
        
        # Should have a message explaining why
        assert "message" in data, "Response should have 'message' field"
        assert "no" in data["message"].lower() or "configurado" in data["message"].lower() or "destinatario" in data["message"].lower(), \
            f"Message should indicate no recipients: {data['message']}"
        
        print("✅ WhatsApp test correctly fails without recipients")
        print(f"   - success: {data['success']}")
        print(f"   - message: {data['message']}")


class TestNotificacionesConfig(TestCentroControlAuth):
    """Tests for all notification services configuration endpoint"""
    
    def test_notificaciones_config_requires_auth(self):
        """GET /api/centro-control/notificaciones/config - should require authentication"""
        response = requests.get(f"{BASE_URL}/api/centro-control/notificaciones/config")
        assert response.status_code in [401, 403], f"Expected 401/403 without auth, got {response.status_code}"
        print("✅ Notificaciones config endpoint correctly requires authentication")
    
    def test_notificaciones_config_returns_all_services(self, auth_headers):
        """GET /api/centro-control/notificaciones/config - should return all 3 notification channels"""
        response = requests.get(
            f"{BASE_URL}/api/centro-control/notificaciones/config",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        print(f"Notificaciones Config: {data}")
        
        # Verify structure
        assert "timestamp" in data, "Response should have 'timestamp'"
        assert "servicios" in data, "Response should have 'servicios'"
        assert "flujo_alertas_criticas" in data, "Response should have 'flujo_alertas_criticas'"
        
        servicios = data["servicios"]
        
        # Verify all 3 channels are present
        assert "email" in servicios, "Should have 'email' service"
        assert "whatsapp" in servicios, "Should have 'whatsapp' service"
        assert "websocket" in servicios, "Should have 'websocket' service"
        
        print("✅ All 3 notification channels present")
        print(f"   - Email: {servicios['email']['nombre']}")
        print(f"   - WhatsApp: {servicios['whatsapp']['nombre']}")
        print(f"   - WebSocket: {servicios['websocket']['nombre']}")
    
    def test_email_service_config(self, auth_headers):
        """Verify email service configuration in notificaciones/config"""
        response = requests.get(
            f"{BASE_URL}/api/centro-control/notificaciones/config",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        email_config = response.json()["servicios"]["email"]
        
        assert "nombre" in email_config, "Email should have 'nombre'"
        assert "config" in email_config, "Email should have 'config'"
        
        config = email_config["config"]
        assert "configured" in config, "Email config should have 'configured'"
        assert "enabled" in config, "Email config should have 'enabled'"
        
        print("✅ Email service config verified")
        print(f"   - Nombre: {email_config['nombre']}")
        print(f"   - Configured: {config.get('configured')}")
        print(f"   - Enabled: {config.get('enabled')}")
    
    def test_whatsapp_service_config(self, auth_headers):
        """Verify WhatsApp service configuration in notificaciones/config"""
        response = requests.get(
            f"{BASE_URL}/api/centro-control/notificaciones/config",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        whatsapp_config = response.json()["servicios"]["whatsapp"]
        
        assert "nombre" in whatsapp_config, "WhatsApp should have 'nombre'"
        assert "config" in whatsapp_config, "WhatsApp should have 'config'"
        
        config = whatsapp_config["config"]
        assert "configured" in config, "WhatsApp config should have 'configured'"
        assert "enabled" in config, "WhatsApp config should have 'enabled'"
        assert "twilio_configured" in config, "WhatsApp config should have 'twilio_configured'"
        
        # Verify Twilio is configured
        assert config["twilio_configured"], \
            f"Expected twilio_configured=True, got {config['twilio_configured']}"
        
        print("✅ WhatsApp service config verified")
        print(f"   - Nombre: {whatsapp_config['nombre']}")
        print(f"   - Twilio Configured: {config['twilio_configured']}")
        print(f"   - Enabled: {config['enabled']}")
        print(f"   - Configured (with recipients): {config['configured']}")
    
    def test_websocket_service_config(self, auth_headers):
        """Verify WebSocket service configuration in notificaciones/config"""
        response = requests.get(
            f"{BASE_URL}/api/centro-control/notificaciones/config",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        ws_config = response.json()["servicios"]["websocket"]
        
        assert "nombre" in ws_config, "WebSocket should have 'nombre'"
        assert "config" in ws_config, "WebSocket should have 'config'"
        
        config = ws_config["config"]
        assert "enabled" in config, "WebSocket config should have 'enabled'"
        assert config["enabled"], "WebSocket should be enabled"
        
        print("✅ WebSocket service config verified")
        print(f"   - Nombre: {ws_config['nombre']}")
        print(f"   - Enabled: {config['enabled']}")
        print(f"   - Connections: {config.get('connections', 'N/A')}")
    
    def test_flujo_alertas_criticas(self, auth_headers):
        """Verify critical alerts flow documentation"""
        response = requests.get(
            f"{BASE_URL}/api/centro-control/notificaciones/config",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        flujo = response.json()["flujo_alertas_criticas"]
        
        assert "descripcion" in flujo, "Flujo should have 'descripcion'"
        assert "canales" in flujo, "Flujo should have 'canales'"
        
        canales = flujo["canales"]
        assert len(canales) == 3, f"Expected 3 channels, got {len(canales)}"
        
        print("✅ Critical alerts flow documented")
        print(f"   - Descripcion: {flujo['descripcion']}")
        print(f"   - Canales: {canales}")


class TestWhatsAppAlertaCritica(TestCentroControlAuth):
    """Tests for WhatsApp critical alert endpoint"""
    
    def test_alerta_critica_requires_auth(self):
        """POST /api/centro-control/whatsapp/alerta-critica - should require authentication"""
        response = requests.post(
            f"{BASE_URL}/api/centro-control/whatsapp/alerta-critica",
            json={"titulo": "Test", "modulo": "Test", "detalle": "Test"}
        )
        assert response.status_code in [401, 403], f"Expected 401/403 without auth, got {response.status_code}"
        print("✅ WhatsApp alerta-critica endpoint correctly requires authentication")
    
    def test_alerta_critica_fails_without_recipients(self, auth_headers):
        """POST /api/centro-control/whatsapp/alerta-critica - should fail when no recipients"""
        alerta = {
            "titulo": "Test Alert",
            "modulo": "Centro de Control",
            "severidad": "critical",
            "detalle": "This is a test critical alert"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/centro-control/whatsapp/alerta-critica",
            headers=auth_headers,
            json=alerta
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        print(f"Alerta Critica Response: {data}")
        
        # Should return success=False because no recipients configured
        assert not data["success"], \
            f"Expected success=False (no recipients), got {data.get('success')}"
        
        print("✅ WhatsApp alerta-critica correctly fails without recipients")
        print(f"   - success: {data['success']}")
        print(f"   - message: {data.get('message', 'N/A')}")


class TestIntegrationSummary(TestCentroControlAuth):
    """Summary test to verify overall WhatsApp integration status"""
    
    def test_whatsapp_integration_summary(self, auth_headers):
        """Comprehensive test of WhatsApp integration status"""
        print("\n" + "="*60)
        print("WHATSAPP INTEGRATION SUMMARY")
        print("="*60)
        
        # 1. Check WhatsApp config
        config_response = requests.get(
            f"{BASE_URL}/api/centro-control/whatsapp/config",
            headers=auth_headers
        )
        assert config_response.status_code == 200
        config = config_response.json()["config"]
        
        print("\n📱 WhatsApp Configuration:")
        print(f"   - Twilio Configured: {'✅' if config['twilio_configured'] else '❌'} {config['twilio_configured']}")
        print(f"   - WhatsApp Enabled: {'✅' if config['enabled'] else '❌'} {config['enabled']}")
        print(f"   - From Number: {config['from_number']}")
        print(f"   - Recipients Configured: {'✅' if config['configured'] else '⚠️'} {config['configured']}")
        print(f"   - Recipients Count: {config['recipients_count']}")
        
        # 2. Check all notification services
        notif_response = requests.get(
            f"{BASE_URL}/api/centro-control/notificaciones/config",
            headers=auth_headers
        )
        assert notif_response.status_code == 200
        servicios = notif_response.json()["servicios"]
        
        print("\n📢 All Notification Services:")
        for service_name, service_data in servicios.items():
            service_config = service_data.get("config", {})
            enabled = service_config.get("enabled", False)
            configured = service_config.get("configured", service_config.get("twilio_configured", False))
            print(f"   - {service_data['nombre']}: {'✅' if enabled else '❌'} Enabled, {'✅' if configured else '⚠️'} Configured")
        
        # 3. Verify expected state
        print("\n✅ VERIFICATION:")
        print(f"   - Twilio credentials are configured: {config['twilio_configured']}")
        print(f"   - WhatsApp is enabled: {config['enabled']}")
        print(f"   - No recipients configured (expected): {not config['configured']}")
        
        # Assertions
        assert config["twilio_configured"], "Twilio should be configured"
        assert config["enabled"], "WhatsApp should be enabled"
        assert not config["configured"], "Should report not configured (no recipients)"
        
        print(f"\n{'='*60}")
        print("ALL WHATSAPP INTEGRATION TESTS PASSED ✅")
        print("="*60)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
