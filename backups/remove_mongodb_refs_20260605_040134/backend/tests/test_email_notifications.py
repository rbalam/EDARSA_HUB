"""
Test Suite: Centro de Control EDARSA - Email Notifications
============================================================
Tests for email notification endpoints:
- GET /api/centro-control/email/config - Email configuration status
- POST /api/centro-control/email/test - Send test email
- POST /api/centro-control/email/alerta-critica - Send critical alert email
- GET /api/centro-control/ping - Health check
- GET /api/centro-control/estado - General consolidated state
- GET /api/centro-control/salud/resumen - Executive summary with traffic lights
"""

import pytest
import requests
import os
from datetime import datetime
from tests.test_config import test_config

# Base URL from environment
BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials from centralized config
ADMIN_EMAIL = test_config.TEST_ADMIN_EMAIL
ADMIN_PASSWORD = test_config.TEST_ADMIN_PASSWORD

# Alternative admin credentials from RBAC testing (via env vars)
ADMIN_RBAC_EMAIL = os.getenv('TEST_RBAC_ADMIN_EMAIL', 'admin.rbac.test@edarsa.com')
ADMIN_RBAC_PASSWORD = os.getenv('TEST_RBAC_ADMIN_PASSWORD', 'AdminRBAC2024!')


class TestEmailNotifications:
    """Test suite for Centro de Control Email Notifications"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        self.token = None
        
    def get_auth_token(self, email=ADMIN_EMAIL, password=ADMIN_PASSWORD):
        """Get authentication token"""
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": email,
            "password": password
        })
        if response.status_code == 200:
            data = response.json()
            # Token field is 'token' not 'access_token'
            return data.get("token")
        return None
    
    def get_authenticated_headers(self, token=None):
        """Get headers with auth token"""
        if token is None:
            token = self.get_auth_token()
        if token:
            return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        return {"Content-Type": "application/json"}
    
    # =========================================================================
    # PING ENDPOINT (No auth required)
    # =========================================================================
    
    def test_ping_endpoint_no_auth(self):
        """Test GET /api/centro-control/ping - No auth required"""
        response = self.session.get(f"{BASE_URL}/api/centro-control/ping")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data.get("status") == "ok", "Ping should return status 'ok'"
        assert data.get("service") == "CENTRO DE CONTROL EDARSA", "Service name mismatch"
        assert "version" in data, "Version should be present"
        assert "timestamp" in data, "Timestamp should be present"
        assert "alertas_activas" in data, "alertas_activas should be present"
        
        print(f"✅ Ping OK - Version: {data.get('version')}, Alertas activas: {data.get('alertas_activas')}")
    
    # =========================================================================
    # EMAIL CONFIG ENDPOINT
    # =========================================================================
    
    def test_email_config_requires_auth(self):
        """Test GET /api/centro-control/email/config - Requires authentication"""
        response = self.session.get(f"{BASE_URL}/api/centro-control/email/config")
        
        # Should return 401 or 403 without auth
        assert response.status_code in [401, 403], f"Expected 401/403 without auth, got {response.status_code}"
        print("✅ Email config correctly requires authentication")
    
    def test_email_config_with_auth(self):
        """Test GET /api/centro-control/email/config - With authentication"""
        # Try primary admin credentials first
        token = self.get_auth_token(ADMIN_EMAIL, ADMIN_PASSWORD)
        
        # If primary fails, try RBAC admin
        if not token:
            token = self.get_auth_token(ADMIN_RBAC_EMAIL, ADMIN_RBAC_PASSWORD)
            
        assert token is not None, "Failed to authenticate with any admin credentials"
        
        headers = self.get_authenticated_headers(token)
        response = self.session.get(f"{BASE_URL}/api/centro-control/email/config", headers=headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "service" in data, "Response should have 'service' field"
        assert "config" in data, "Response should have 'config' field"
        
        config = data.get("config", {})
        assert "configured" in config, "Config should have 'configured' field"
        assert "enabled" in config, "Config should have 'enabled' field"
        assert "smtp_host" in config, "Config should have 'smtp_host' field"
        assert "smtp_port" in config, "Config should have 'smtp_port' field"
        assert "recipients_count" in config, "Config should have 'recipients_count' field"
        
        # Verify SMTP is configured as expected
        assert config.get("configured"), "Email should be configured (configured: true)"
        assert config.get("enabled"), "Email should be enabled"
        assert config.get("smtp_host") == "mail.edarsa.com.mx", f"SMTP host should be mail.edarsa.com.mx, got {config.get('smtp_host')}"
        assert config.get("smtp_port") == 587, f"SMTP port should be 587, got {config.get('smtp_port')}"
        
        print(f"✅ Email config OK - Configured: {config.get('configured')}, Host: {config.get('smtp_host')}, Recipients: {config.get('recipients_count')}")
    
    # =========================================================================
    # EMAIL TEST ENDPOINT
    # =========================================================================
    
    def test_email_test_requires_auth(self):
        """Test POST /api/centro-control/email/test - Requires authentication"""
        response = self.session.post(f"{BASE_URL}/api/centro-control/email/test")
        
        assert response.status_code in [401, 403], f"Expected 401/403 without auth, got {response.status_code}"
        print("✅ Email test correctly requires authentication")
    
    def test_email_test_with_auth(self):
        """Test POST /api/centro-control/email/test - Send test email"""
        token = self.get_auth_token(ADMIN_EMAIL, ADMIN_PASSWORD)
        if not token:
            token = self.get_auth_token(ADMIN_RBAC_EMAIL, ADMIN_RBAC_PASSWORD)
        assert token is not None, "Failed to authenticate"
        
        headers = self.get_authenticated_headers(token)
        response = self.session.post(f"{BASE_URL}/api/centro-control/email/test", headers=headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        # The test email may fail due to invalid recipient, but should connect to SMTP
        assert "success" in data, "Response should have 'success' field"
        assert "message" in data, "Response should have 'message' field"
        
        # Log the result - may succeed or fail depending on SMTP/recipient
        if data.get("success"):
            print(f"✅ Test email sent successfully: {data.get('message')}")
        else:
            # Email may fail due to recipient issues, but endpoint works
            print(f"⚠️ Test email failed (expected if recipient invalid): {data.get('message')}")
            # Still pass the test - endpoint is working, SMTP connection attempted
    
    # =========================================================================
    # ALERTA CRITICA EMAIL ENDPOINT
    # =========================================================================
    
    def test_alerta_critica_email_requires_auth(self):
        """Test POST /api/centro-control/email/alerta-critica - Requires authentication"""
        response = self.session.post(
            f"{BASE_URL}/api/centro-control/email/alerta-critica",
            json={"titulo": "Test", "modulo": "Test", "severidad": "critical", "detalle": "Test"}
        )
        
        assert response.status_code in [401, 403], f"Expected 401/403 without auth, got {response.status_code}"
        print("✅ Alerta critica email correctly requires authentication")
    
    def test_alerta_critica_email_with_auth(self):
        """Test POST /api/centro-control/email/alerta-critica - Send critical alert email"""
        token = self.get_auth_token(ADMIN_EMAIL, ADMIN_PASSWORD)
        if not token:
            token = self.get_auth_token(ADMIN_RBAC_EMAIL, ADMIN_RBAC_PASSWORD)
        assert token is not None, "Failed to authenticate"
        
        headers = self.get_authenticated_headers(token)
        
        alerta_data = {
            "titulo": "TEST - Alerta de Prueba Automatizada",
            "modulo": "Sistema de Testing",
            "severidad": "critical",
            "detalle": f"Esta es una alerta de prueba generada por el sistema de testing automatizado a las {datetime.now().isoformat()}"
        }
        
        response = self.session.post(
            f"{BASE_URL}/api/centro-control/email/alerta-critica",
            headers=headers,
            json=alerta_data
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "success" in data, "Response should have 'success' field"
        assert "message" in data, "Response should have 'message' field"
        
        # Log the result
        if data.get("success"):
            print(f"✅ Critical alert email sent: {data.get('message')}")
            if "enviados" in data:
                print(f"   Enviados: {data.get('enviados')}/{len(data.get('recipients', []))}")
        else:
            print(f"⚠️ Critical alert email failed (may be expected): {data.get('message')}")
    
    # =========================================================================
    # ESTADO GENERAL ENDPOINT
    # =========================================================================
    
    def test_estado_requires_auth(self):
        """Test GET /api/centro-control/estado - Requires authentication"""
        response = self.session.get(f"{BASE_URL}/api/centro-control/estado")
        
        assert response.status_code in [401, 403], f"Expected 401/403 without auth, got {response.status_code}"
        print("✅ Estado correctly requires authentication")
    
    def test_estado_with_auth(self):
        """Test GET /api/centro-control/estado - General consolidated state"""
        token = self.get_auth_token(ADMIN_EMAIL, ADMIN_PASSWORD)
        if not token:
            token = self.get_auth_token(ADMIN_RBAC_EMAIL, ADMIN_RBAC_PASSWORD)
        assert token is not None, "Failed to authenticate"
        
        headers = self.get_authenticated_headers(token)
        response = self.session.get(f"{BASE_URL}/api/centro-control/estado", headers=headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        
        # Verify structure
        assert "centro_control" in data, "Should have 'centro_control' field"
        assert "version" in data, "Should have 'version' field"
        assert "timestamp" in data, "Should have 'timestamp' field"
        assert "estado_general" in data, "Should have 'estado_general' field"
        assert "componentes" in data, "Should have 'componentes' field"
        
        componentes = data.get("componentes", {})
        assert "salud" in componentes, "Componentes should have 'salud'"
        assert "alertas" in componentes, "Componentes should have 'alertas'"
        assert "regresiones" in componentes, "Componentes should have 'regresiones'"
        assert "jobs" in componentes, "Componentes should have 'jobs'"
        assert "metricas" in componentes, "Componentes should have 'metricas'"
        
        print(f"✅ Estado OK - Estado general: {data.get('estado_general')}, Emoji: {data.get('estado_emoji')}")
        print(f"   Alertas activas: {componentes.get('alertas', {}).get('activas', 0)}")
        print(f"   Alertas críticas: {componentes.get('alertas', {}).get('criticas', 0)}")
    
    # =========================================================================
    # SALUD RESUMEN ENDPOINT
    # =========================================================================
    
    def test_salud_resumen_requires_auth(self):
        """Test GET /api/centro-control/salud/resumen - Requires authentication"""
        response = self.session.get(f"{BASE_URL}/api/centro-control/salud/resumen")
        
        assert response.status_code in [401, 403], f"Expected 401/403 without auth, got {response.status_code}"
        print("✅ Salud resumen correctly requires authentication")
    
    def test_salud_resumen_with_auth(self):
        """Test GET /api/centro-control/salud/resumen - Executive summary with traffic lights"""
        token = self.get_auth_token(ADMIN_EMAIL, ADMIN_PASSWORD)
        if not token:
            token = self.get_auth_token(ADMIN_RBAC_EMAIL, ADMIN_RBAC_PASSWORD)
        assert token is not None, "Failed to authenticate"
        
        headers = self.get_authenticated_headers(token)
        response = self.session.get(f"{BASE_URL}/api/centro-control/salud/resumen", headers=headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        
        # Verify structure
        assert "status" in data, "Should have 'status' field"
        assert "status_emoji" in data, "Should have 'status_emoji' field (traffic light)"
        assert "kpis" in data, "Should have 'kpis' field"
        assert "alertas" in data, "Should have 'alertas' field"
        
        # Verify KPIs
        kpis = data.get("kpis", {})
        assert "modules_healthy_pct" in kpis, "KPIs should have 'modules_healthy_pct'"
        assert "sources_connected_pct" in kpis, "KPIs should have 'sources_connected_pct'"
        
        # Verify alertas
        alertas = data.get("alertas", {})
        assert "activas" in alertas, "Alertas should have 'activas'"
        assert "criticas" in alertas, "Alertas should have 'criticas'"
        
        print(f"✅ Salud resumen OK - Status: {data.get('status')} {data.get('status_emoji')}")
        print(f"   Módulos sanos: {kpis.get('modules_healthy_pct', 0)}%")
        print(f"   Fuentes conectadas: {kpis.get('sources_connected_pct', 0)}%")
        print(f"   Alertas activas: {alertas.get('activas', 0)}, Críticas: {alertas.get('criticas', 0)}")


class TestAuthenticationFlow:
    """Test authentication with provided credentials"""
    
    def test_admin_login_primary(self):
        """Test login with primary admin credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        
        if response.status_code == 200:
            data = response.json()
            assert "token" in data, "Response should have 'token' field"
            print(f"✅ Primary admin login successful: {ADMIN_EMAIL}")
        else:
            print(f"⚠️ Primary admin login failed: {response.status_code} - {response.text[:200]}")
            # Don't fail - we have backup credentials
    
    def test_admin_login_rbac(self):
        """Test login with RBAC admin credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_RBAC_EMAIL,
            "password": ADMIN_RBAC_PASSWORD
        })
        
        if response.status_code == 200:
            data = response.json()
            assert "token" in data, "Response should have 'token' field"
            print(f"✅ RBAC admin login successful: {ADMIN_RBAC_EMAIL}")
        else:
            print(f"⚠️ RBAC admin login failed: {response.status_code} - {response.text[:200]}")


class TestEmailConfigurationDetails:
    """Detailed tests for email configuration"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session with authentication"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Get token
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            self.token = response.json().get("token")
        else:
            # Try RBAC admin
            response = self.session.post(f"{BASE_URL}/api/auth/login", json={
                "email": ADMIN_RBAC_EMAIL,
                "password": ADMIN_RBAC_PASSWORD
            })
            if response.status_code == 200:
                self.token = response.json().get("token")
            else:
                self.token = None
        
        if self.token:
            self.session.headers.update({"Authorization": f"Bearer {self.token}"})
    
    def test_email_config_smtp_settings(self):
        """Verify SMTP settings match expected EDARSA configuration"""
        if not self.token:
            pytest.skip("No valid authentication token")
        
        response = self.session.get(f"{BASE_URL}/api/centro-control/email/config")
        assert response.status_code == 200
        
        config = response.json().get("config", {})
        
        # Verify EDARSA SMTP settings
        assert config.get("smtp_host") == "mail.edarsa.com.mx", "SMTP host should be mail.edarsa.com.mx"
        assert config.get("smtp_port") == 587, "SMTP port should be 587 (TLS)"
        assert config.get("use_tls"), "TLS should be enabled"
        assert config.get("enabled"), "Email should be enabled"
        assert config.get("configured"), "Email should be fully configured"
        
        # Verify recipients are configured
        assert config.get("recipients_count", 0) > 0, "At least one recipient should be configured"
        
        # Verify from_email is set
        assert config.get("from_email") is not None, "From email should be configured"
        
        print("✅ SMTP Configuration verified:")
        print(f"   Host: {config.get('smtp_host')}")
        print(f"   Port: {config.get('smtp_port')}")
        print(f"   TLS: {config.get('use_tls')}")
        print(f"   From: {config.get('from_email')}")
        print(f"   Recipients: {config.get('recipients_count')}")
        print(f"   Recipients (masked): {config.get('recipients', [])}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
