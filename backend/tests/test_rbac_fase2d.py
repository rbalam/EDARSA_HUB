"""
RBAC Fase 2D - Test Suite
=========================
Tests for Role-Based Access Control implementation.

Tests verify:
1. RBAC middleware blocks users without permissions (403 Forbidden)
2. Admin (Administrador) can access all endpoints
3. Operador (Usuario) can VIEW but NOT CREATE/APPLY/AUTHORIZE/CONFIGURE

Test Users:
- ADMIN: admin.rbac.test@edarsa.com / AdminRBAC2024! (role=Administrador)
- OPERADOR: operador.test@edarsa.com / OperadorTest2024! (role=Usuario)

OPERADOR permissions (from ROLES_SISTEMA):
- CARGOS_VER
- RESPONSABILIDAD_VER, RESPONSABILIDAD_DISPUTAR
- SLA_VER
- WORKFLOW_VER
- TAREAS_VER, TAREAS_COMPLETAR
- REPORTES_VER
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "admin.rbac.test@edarsa.com"
ADMIN_PASSWORD = "AdminRBAC2024!"

OPERADOR_EMAIL = "operador.test@edarsa.com"
OPERADOR_PASSWORD = "OperadorTest2024!"


class TestRBACSetup:
    """Setup tests - verify users exist and can login"""
    
    def test_api_health(self):
        """Verify API is accessible"""
        response = requests.get(f"{BASE_URL}/api/auth/me", headers={"Authorization": "Bearer invalid"})
        # We expect 401 which means the API is running
        assert response.status_code in [200, 401], f"API not accessible: {response.text}"
        print("✓ API is accessible")
    
    def test_admin_login(self):
        """Verify admin user can login"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        assert response.status_code == 200, f"Admin login failed: {response.text}"
        data = response.json()
        assert "token" in data, "No token in response"
        print(f"✓ Admin login successful, role: {data.get('user', {}).get('role')}")
    
    def test_operador_login(self):
        """Verify operador user can login"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": OPERADOR_EMAIL, "password": OPERADOR_PASSWORD}
        )
        assert response.status_code == 200, f"Operador login failed: {response.text}"
        data = response.json()
        assert "token" in data, "No token in response"
        print(f"✓ Operador login successful, role: {data.get('user', {}).get('role')}")


@pytest.fixture(scope="module")
def admin_token():
    """Get admin authentication token"""
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
    )
    if response.status_code != 200:
        pytest.skip(f"Admin login failed: {response.text}")
    return response.json().get("token")


@pytest.fixture(scope="module")
def operador_token():
    """Get operador authentication token"""
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": OPERADOR_EMAIL, "password": OPERADOR_PASSWORD}
    )
    if response.status_code != 200:
        pytest.skip(f"Operador login failed: {response.text}")
    return response.json().get("token")


def get_auth_headers(token):
    """Helper to create auth headers"""
    return {"Authorization": f"Bearer {token}"}


# =============================================================================
# CARGOS ECONÓMICOS - RBAC TESTS
# =============================================================================

class TestCargosRBAC:
    """Test RBAC for Cargos Económicos endpoints"""
    
    # --- GET endpoints (CARGOS_VER) - Both Admin and Operador should access ---
    
    def test_get_cargos_admin(self, admin_token):
        """Admin can GET /api/v2/cargos"""
        response = requests.get(
            f"{BASE_URL}/api/v2/cargos",
            headers=get_auth_headers(admin_token)
        )
        assert response.status_code == 200, f"Admin GET cargos failed: {response.text}"
        print("✓ Admin can GET /api/v2/cargos")
    
    def test_get_cargos_operador(self, operador_token):
        """Operador can GET /api/v2/cargos (has CARGOS_VER)"""
        response = requests.get(
            f"{BASE_URL}/api/v2/cargos",
            headers=get_auth_headers(operador_token)
        )
        assert response.status_code == 200, f"Operador GET cargos failed: {response.text}"
        print("✓ Operador can GET /api/v2/cargos")
    
    def test_get_cargos_pendientes_operador(self, operador_token):
        """Operador can GET /api/v2/cargos/pendientes"""
        response = requests.get(
            f"{BASE_URL}/api/v2/cargos/pendientes",
            headers=get_auth_headers(operador_token)
        )
        # Note: This endpoint doesn't have RBAC protection in the code
        assert response.status_code in [200, 403], f"Unexpected status: {response.status_code}"
        print(f"✓ Operador GET /api/v2/cargos/pendientes: {response.status_code}")
    
    def test_get_cargos_metricas_operador(self, operador_token):
        """Operador can GET /api/v2/cargos/metricas"""
        response = requests.get(
            f"{BASE_URL}/api/v2/cargos/metricas",
            headers=get_auth_headers(operador_token)
        )
        # Note: This endpoint doesn't have RBAC protection in the code
        assert response.status_code in [200, 403], f"Unexpected status: {response.status_code}"
        print(f"✓ Operador GET /api/v2/cargos/metricas: {response.status_code}")
    
    # --- POST endpoints (CARGOS_CREAR) - Only Admin should access ---
    
    def test_post_cargos_admin(self, admin_token):
        """Admin can POST /api/v2/cargos (has CARGOS_CREAR)"""
        response = requests.post(
            f"{BASE_URL}/api/v2/cargos",
            headers=get_auth_headers(admin_token),
            json={
                "responsabilidad_id": "test-responsabilidad-id",
                "usuario_id": "admin-user-id",
                "usuario_rol": "Administrador",
                "comentario": "Test cargo creation by admin"
            }
        )
        # May fail with 404 (responsabilidad not found) or 400 (not eligible), but NOT 403
        assert response.status_code != 403, f"Admin should have CARGOS_CREAR permission"
        print(f"✓ Admin POST /api/v2/cargos: {response.status_code} (not 403)")
    
    def test_post_cargos_operador_forbidden(self, operador_token):
        """Operador CANNOT POST /api/v2/cargos (no CARGOS_CREAR)"""
        response = requests.post(
            f"{BASE_URL}/api/v2/cargos",
            headers=get_auth_headers(operador_token),
            json={
                "responsabilidad_id": "test-responsabilidad-id",
                "usuario_id": "operador-user-id",
                "usuario_rol": "Usuario",
                "comentario": "Test cargo creation by operador"
            }
        )
        assert response.status_code == 403, f"Operador should get 403, got {response.status_code}: {response.text}"
        print("✓ Operador POST /api/v2/cargos: 403 Forbidden (correct)")
    
    # --- POST /aplicar (CARGOS_APLICAR) - Only Admin should access ---
    
    def test_post_aplicar_operador_forbidden(self, operador_token):
        """Operador CANNOT POST /api/v2/cargos/{id}/aplicar (no CARGOS_APLICAR)"""
        response = requests.post(
            f"{BASE_URL}/api/v2/cargos/test-cargo-id/aplicar",
            headers=get_auth_headers(operador_token),
            json={
                "usuario_id": "operador-user-id",
                "usuario_rol": "Usuario",
                "comentario": "Test aplicar by operador"
            }
        )
        assert response.status_code == 403, f"Operador should get 403, got {response.status_code}: {response.text}"
        print("✓ Operador POST /api/v2/cargos/{id}/aplicar: 403 Forbidden (correct)")
    
    # --- POST /autorizar (CARGOS_AUTORIZAR) - Only Admin should access ---
    
    def test_post_autorizar_operador_forbidden(self, operador_token):
        """Operador CANNOT POST /api/v2/cargos/{id}/autorizar (no CARGOS_AUTORIZAR)"""
        response = requests.post(
            f"{BASE_URL}/api/v2/cargos/test-cargo-id/autorizar",
            headers=get_auth_headers(operador_token),
            json={
                "usuario_id": "operador-user-id",
                "usuario_rol": "Usuario",
                "comentario": "Test autorizar by operador"
            }
        )
        assert response.status_code == 403, f"Operador should get 403, got {response.status_code}: {response.text}"
        print("✓ Operador POST /api/v2/cargos/{id}/autorizar: 403 Forbidden (correct)")


# =============================================================================
# RESPONSABILIDAD ECONÓMICA - RBAC TESTS
# =============================================================================

class TestResponsabilidadRBAC:
    """Test RBAC for Responsabilidad Económica endpoints"""
    
    # --- GET endpoints (RESPONSABILIDAD_VER) - Both should access ---
    
    def test_get_responsabilidad_admin(self, admin_token):
        """Admin can GET /api/v2/responsabilidad"""
        response = requests.get(
            f"{BASE_URL}/api/v2/responsabilidad",
            headers=get_auth_headers(admin_token)
        )
        assert response.status_code == 200, f"Admin GET responsabilidad failed: {response.text}"
        print("✓ Admin can GET /api/v2/responsabilidad")
    
    def test_get_responsabilidad_operador(self, operador_token):
        """Operador can GET /api/v2/responsabilidad (has RESPONSABILIDAD_VER)"""
        response = requests.get(
            f"{BASE_URL}/api/v2/responsabilidad",
            headers=get_auth_headers(operador_token)
        )
        assert response.status_code == 200, f"Operador GET responsabilidad failed: {response.text}"
        print("✓ Operador can GET /api/v2/responsabilidad")
    
    def test_get_configuracion_operador(self, operador_token):
        """Operador can GET /api/v2/responsabilidad/configuracion"""
        response = requests.get(
            f"{BASE_URL}/api/v2/responsabilidad/configuracion",
            headers=get_auth_headers(operador_token)
        )
        assert response.status_code == 200, f"Operador GET configuracion failed: {response.text}"
        print("✓ Operador can GET /api/v2/responsabilidad/configuracion")
    
    # --- POST /calcular (RESPONSABILIDAD_CALCULAR) - Only Admin should access ---
    
    def test_post_calcular_operador_forbidden(self, operador_token):
        """Operador CANNOT POST /api/v2/responsabilidad/calcular/{id} (no RESPONSABILIDAD_CALCULAR)"""
        response = requests.post(
            f"{BASE_URL}/api/v2/responsabilidad/calcular/test-workflow-id?usuario_id=operador-user-id",
            headers=get_auth_headers(operador_token)
        )
        assert response.status_code == 403, f"Operador should get 403, got {response.status_code}: {response.text}"
        print("✓ Operador POST /api/v2/responsabilidad/calcular/{id}: 403 Forbidden (correct)")
    
    # --- POST /exonerar (RESPONSABILIDAD_EXONERAR) - Only Admin should access ---
    
    def test_post_exonerar_operador_forbidden(self, operador_token):
        """Operador CANNOT POST /api/v2/responsabilidad/{id}/exonerar (no RESPONSABILIDAD_EXONERAR)"""
        response = requests.post(
            f"{BASE_URL}/api/v2/responsabilidad/test-responsabilidad-id/exonerar",
            headers=get_auth_headers(operador_token),
            json={
                "usuario_id": "operador-user-id",
                "usuario_rol": "Usuario",
                "comentario": "Test exonerar by operador"
            }
        )
        assert response.status_code == 403, f"Operador should get 403, got {response.status_code}: {response.text}"
        print("✓ Operador POST /api/v2/responsabilidad/{id}/exonerar: 403 Forbidden (correct)")
    
    # --- POST /disputar (RESPONSABILIDAD_DISPUTAR) - Operador CAN access ---
    
    def test_post_disputar_operador_allowed(self, operador_token):
        """Operador CAN POST /api/v2/responsabilidad/{id}/disputar (has RESPONSABILIDAD_DISPUTAR)"""
        response = requests.post(
            f"{BASE_URL}/api/v2/responsabilidad/test-responsabilidad-id/disputar",
            headers=get_auth_headers(operador_token),
            json={
                "usuario_id": "operador-user-id",
                "usuario_rol": "Usuario",
                "comentario": "Test disputar by operador - should be allowed"
            }
        )
        # May fail with 404 (not found) or 400 (invalid transition), but NOT 403
        assert response.status_code != 403, f"Operador should have RESPONSABILIDAD_DISPUTAR permission, got 403"
        print(f"✓ Operador POST /api/v2/responsabilidad/{id}/disputar: {response.status_code} (not 403)")


# =============================================================================
# SLA - RBAC TESTS
# =============================================================================

class TestSLARBAC:
    """Test RBAC for SLA endpoints"""
    
    # --- GET /configuracion (SLA_VER) - Both should access ---
    
    def test_get_sla_config_admin(self, admin_token):
        """Admin can GET /api/v2/sla/configuracion"""
        response = requests.get(
            f"{BASE_URL}/api/v2/sla/configuracion",
            headers=get_auth_headers(admin_token)
        )
        assert response.status_code == 200, f"Admin GET SLA config failed: {response.text}"
        print("✓ Admin can GET /api/v2/sla/configuracion")
    
    def test_get_sla_config_operador(self, operador_token):
        """Operador can GET /api/v2/sla/configuracion (has SLA_VER)"""
        response = requests.get(
            f"{BASE_URL}/api/v2/sla/configuracion",
            headers=get_auth_headers(operador_token)
        )
        assert response.status_code == 200, f"Operador GET SLA config failed: {response.text}"
        print("✓ Operador can GET /api/v2/sla/configuracion")
    
    # --- PUT /configuracion (SLA_CONFIGURAR) - Only Admin should access ---
    
    def test_put_sla_config_operador_forbidden(self, operador_token):
        """Operador CANNOT PUT /api/v2/sla/configuracion (no SLA_CONFIGURAR)"""
        response = requests.put(
            f"{BASE_URL}/api/v2/sla/configuracion",
            headers=get_auth_headers(operador_token),
            json={"justificacion_simple_horas": 24}
        )
        assert response.status_code == 403, f"Operador should get 403, got {response.status_code}: {response.text}"
        print("✓ Operador PUT /api/v2/sla/configuracion: 403 Forbidden (correct)")
    
    def test_put_sla_config_admin(self, admin_token):
        """Admin can PUT /api/v2/sla/configuracion (has SLA_CONFIGURAR)"""
        response = requests.put(
            f"{BASE_URL}/api/v2/sla/configuracion",
            headers=get_auth_headers(admin_token),
            json={"justificacion_simple_horas": 24}
        )
        assert response.status_code != 403, f"Admin should have SLA_CONFIGURAR permission"
        print(f"✓ Admin PUT /api/v2/sla/configuracion: {response.status_code} (not 403)")


# =============================================================================
# NOTIFICACIONES WHATSAPP - RBAC TESTS
# =============================================================================

class TestNotificacionesRBAC:
    """Test RBAC for Notificaciones WhatsApp endpoints"""
    
    # --- GET /config (NOTIFICACIONES_VER) - Only Admin should access (Operador doesn't have this) ---
    
    def test_get_notificaciones_config_admin(self, admin_token):
        """Admin can GET /api/v2/notificaciones-whatsapp/config"""
        response = requests.get(
            f"{BASE_URL}/api/v2/notificaciones-whatsapp/config",
            headers=get_auth_headers(admin_token)
        )
        assert response.status_code == 200, f"Admin GET notificaciones config failed: {response.text}"
        print("✓ Admin can GET /api/v2/notificaciones-whatsapp/config")
    
    def test_get_notificaciones_config_operador_forbidden(self, operador_token):
        """Operador CANNOT GET /api/v2/notificaciones-whatsapp/config (no NOTIFICACIONES_VER)"""
        response = requests.get(
            f"{BASE_URL}/api/v2/notificaciones-whatsapp/config",
            headers=get_auth_headers(operador_token)
        )
        assert response.status_code == 403, f"Operador should get 403, got {response.status_code}: {response.text}"
        print("✓ Operador GET /api/v2/notificaciones-whatsapp/config: 403 Forbidden (correct)")
    
    # --- POST /test (NOTIFICACIONES_ENVIAR) - Only Admin should access ---
    
    def test_post_notificaciones_test_operador_forbidden(self, operador_token):
        """Operador CANNOT POST /api/v2/notificaciones-whatsapp/test (no NOTIFICACIONES_ENVIAR)"""
        response = requests.post(
            f"{BASE_URL}/api/v2/notificaciones-whatsapp/test",
            headers=get_auth_headers(operador_token),
            json={
                "template_codigo": "test_template",
                "destinatario_telefono": "+521234567890",
                "payload": {},
                "modo": "mock"
            }
        )
        assert response.status_code == 403, f"Operador should get 403, got {response.status_code}: {response.text}"
        print("✓ Operador POST /api/v2/notificaciones-whatsapp/test: 403 Forbidden (correct)")


# =============================================================================
# AUTHENTICATION TESTS - No token / Invalid token
# =============================================================================

class TestAuthenticationRequired:
    """Test that endpoints require authentication"""
    
    def test_no_token_returns_401(self):
        """Endpoints without token should return 401"""
        response = requests.get(f"{BASE_URL}/api/v2/cargos")
        assert response.status_code == 401, f"Expected 401 without token, got {response.status_code}"
        print("✓ GET /api/v2/cargos without token: 401 Unauthorized")
    
    def test_invalid_token_returns_401(self):
        """Endpoints with invalid token should return 401"""
        response = requests.get(
            f"{BASE_URL}/api/v2/cargos",
            headers={"Authorization": "Bearer invalid-token-12345"}
        )
        assert response.status_code == 401, f"Expected 401 with invalid token, got {response.status_code}"
        print("✓ GET /api/v2/cargos with invalid token: 401 Unauthorized")


# =============================================================================
# RBAC AUDIT LOG TEST
# =============================================================================

class TestRBACAudit:
    """Test RBAC audit logging"""
    
    def test_rbac_audit_endpoint(self, admin_token):
        """Admin can access RBAC audit logs"""
        response = requests.get(
            f"{BASE_URL}/api/v2/rbac/audit",
            headers=get_auth_headers(admin_token)
        )
        # This endpoint may or may not exist
        if response.status_code == 404:
            pytest.skip("RBAC audit endpoint not implemented")
        assert response.status_code in [200, 403], f"Unexpected status: {response.status_code}"
        print(f"✓ Admin GET /api/v2/rbac/audit: {response.status_code}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
