"""
FASE 11 RBAC Testing: POST Endpoints Protection
================================================
Tests for POST /api/users and POST /api/roles with RBAC permissions.

Test Scenarios:
1. POST /api/users - SuperAdmin (should allow)
2. POST /api/users - Administrador legacy (should allow via fallback)
3. POST /api/users - Usuario (should deny 403)
4. POST /api/users - No auth (should deny 401)
5. POST /api/roles - SuperAdmin (should allow)
6. POST /api/roles - Administrador legacy (should allow via fallback)
7. POST /api/roles - Usuario (should deny 403)
8. POST /auth/register - Public (should work, generates token)
9. POST /auth/login - No regression
10. GET /api/users - FASE 9 no regression
11. GET /api/roles - FASE 9 no regression
"""

import pytest
import requests
import os
import uuid

# Import centralized test credentials
from conftest import (
    TEST_SUPERADMIN_EMAIL, TEST_SUPERADMIN_PASSWORD,
    TEST_ADMIN_EMAIL, TEST_ADMIN_PASSWORD,
    TEST_USER_EMAIL, TEST_USER_PASSWORD
)

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials (centralized via conftest)
SUPERADMIN_CREDS = {
    "email": os.environ.get("TEST_SUPERADMIN_EMAIL", TEST_SUPERADMIN_EMAIL),
    "password": os.environ.get("TEST_SUPERADMIN_PASSWORD", TEST_SUPERADMIN_PASSWORD)
}
ADMIN_CREDS = {
    "email": os.environ.get("TEST_ADMIN_EMAIL", TEST_ADMIN_EMAIL),
    "password": os.environ.get("TEST_ADMIN_PASSWORD", TEST_ADMIN_PASSWORD)
}
USUARIO_CREDS = {
    "email": os.environ.get("TEST_USER_EMAIL", TEST_USER_EMAIL),
    "password": os.environ.get("TEST_USER_PASSWORD", TEST_USER_PASSWORD)
}


class TestAuthBasics:
    """Basic auth tests - no regression from previous phases"""
    
    def test_login_superadmin(self):
        """SuperAdmin login should work"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json=SUPERADMIN_CREDS)
        print(f"SuperAdmin login: {response.status_code}")
        assert response.status_code == 200, f"SuperAdmin login failed: {response.text}"
        data = response.json()
        assert "token" in data, "No token in response"
        assert "user" in data, "No user in response"
        assert data["user"]["role"] == "SuperAdministrador", f"Expected SuperAdministrador, got {data['user']['role']}"
        print(f"SuperAdmin login SUCCESS - role: {data['user']['role']}")
    
    def test_login_admin(self):
        """Administrador login should work"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json=ADMIN_CREDS)
        print(f"Admin login: {response.status_code}")
        if response.status_code != 200:
            print(f"Admin login response: {response.text}")
            pytest.skip("Admin user may not exist - skipping admin tests")
        data = response.json()
        assert "token" in data, "No token in response"
        assert data["user"]["role"] == "Administrador", f"Expected Administrador, got {data['user']['role']}"
        print(f"Admin login SUCCESS - role: {data['user']['role']}")
    
    def test_login_usuario(self):
        """Usuario login should work"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json=USUARIO_CREDS)
        print(f"Usuario login: {response.status_code}")
        if response.status_code != 200:
            print(f"Usuario login response: {response.text}")
            pytest.skip("Usuario may not exist - skipping usuario tests")
        data = response.json()
        assert "token" in data, "No token in response"
        assert data["user"]["role"] == "Usuario", f"Expected Usuario, got {data['user']['role']}"
        print(f"Usuario login SUCCESS - role: {data['user']['role']}")
    
    def test_auth_register_public(self):
        """POST /auth/register should be public and generate token"""
        unique_email = f"test_register_{uuid.uuid4().hex[:8]}@test.com"
        payload = {
            "email": unique_email,
            "name": "Test Register User",
            "password": "TestPass123!",
            "role": "Usuario"  # Required field per schema
        }
        response = requests.post(f"{BASE_URL}/api/auth/register", json=payload)
        print(f"Register public: {response.status_code}")
        
        # Should succeed (200) or fail with duplicate (400) or validation (422) - NOT 401/403
        assert response.status_code in [200, 400, 422], f"Register should be public, got {response.status_code}: {response.text}"
        
        if response.status_code == 200:
            data = response.json()
            assert "token" in data, "Register should return token"
            assert "user" in data, "Register should return user"
            print(f"Register SUCCESS - token generated for {unique_email}")
        else:
            print(f"Register returned {response.status_code}: {response.text}")


class TestPostUsersRBAC:
    """POST /api/users RBAC protection tests"""
    
    @pytest.fixture
    def superadmin_token(self):
        """Get SuperAdmin token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json=SUPERADMIN_CREDS)
        if response.status_code != 200:
            pytest.skip("SuperAdmin login failed")
        return response.json()["token"]
    
    @pytest.fixture
    def admin_token(self):
        """Get Administrador token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json=ADMIN_CREDS)
        if response.status_code != 200:
            pytest.skip("Admin login failed - user may not exist")
        return response.json()["token"]
    
    @pytest.fixture
    def usuario_token(self):
        """Get Usuario token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json=USUARIO_CREDS)
        if response.status_code != 200:
            pytest.skip("Usuario login failed - user may not exist")
        return response.json()["token"]
    
    def test_post_users_superadmin_allowed(self, superadmin_token):
        """POST /api/users with SuperAdmin should be allowed"""
        unique_email = f"test_admin_create_{uuid.uuid4().hex[:8]}@test.com"
        payload = {
            "email": unique_email,
            "name": "Test User Created by SuperAdmin",
            "password": "TestPass123!",
            "role": "Usuario"
        }
        headers = {"Authorization": f"Bearer {superadmin_token}"}
        response = requests.post(f"{BASE_URL}/api/users", json=payload, headers=headers)
        print(f"POST /api/users (SuperAdmin): {response.status_code}")
        
        # Should succeed (200/201) - SuperAdmin has SISTEMA_USUARIOS_CREAR via fallback
        assert response.status_code in [200, 201], f"SuperAdmin should be able to create users: {response.text}"
        
        data = response.json()
        assert "user" in data or "message" in data, f"Unexpected response: {data}"
        print(f"SuperAdmin created user SUCCESS: {unique_email}")
    
    def test_post_users_admin_legacy_fallback(self, admin_token):
        """POST /api/users with Administrador should be allowed via legacy fallback"""
        unique_email = f"test_admin_legacy_{uuid.uuid4().hex[:8]}@test.com"
        payload = {
            "email": unique_email,
            "name": "Test User Created by Admin Legacy",
            "password": "TestPass123!",
            "role": "Usuario"
        }
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.post(f"{BASE_URL}/api/users", json=payload, headers=headers)
        print(f"POST /api/users (Admin legacy): {response.status_code}")
        
        # Should succeed - Administrador has role_level >= 3 (legacy fallback)
        assert response.status_code in [200, 201], f"Admin legacy fallback should allow user creation: {response.text}"
        
        data = response.json()
        assert "user" in data or "message" in data, f"Unexpected response: {data}"
        print(f"Admin legacy created user SUCCESS: {unique_email}")
    
    def test_post_users_usuario_denied(self, usuario_token):
        """POST /api/users with Usuario should be denied (403)"""
        payload = {
            "email": "should_not_create@test.com",
            "name": "Should Not Be Created",
            "password": "TestPass123!",
            "role": "Usuario"
        }
        headers = {"Authorization": f"Bearer {usuario_token}"}
        response = requests.post(f"{BASE_URL}/api/users", json=payload, headers=headers)
        print(f"POST /api/users (Usuario): {response.status_code}")
        
        # Should be denied - Usuario has role_level < 3 and no RBAC permission
        assert response.status_code == 403, f"Usuario should be denied (403), got {response.status_code}: {response.text}"
        print("Usuario correctly denied (403) for POST /api/users")
    
    def test_post_users_no_auth_denied(self):
        """POST /api/users without auth should be denied (401 or 403)"""
        payload = {
            "email": "no_auth_create@test.com",
            "name": "No Auth User",
            "password": "TestPass123!",
            "role": "Usuario"
        }
        response = requests.post(f"{BASE_URL}/api/users", json=payload)
        print(f"POST /api/users (no auth): {response.status_code}")
        
        # Should be denied - no authentication (401 or 403 both acceptable)
        assert response.status_code in [401, 403], f"No auth should be denied (401/403), got {response.status_code}: {response.text}"
        print(f"No auth correctly denied ({response.status_code}) for POST /api/users")


class TestPostRolesRBAC:
    """POST /api/roles RBAC protection tests"""
    
    @pytest.fixture
    def superadmin_token(self):
        """Get SuperAdmin token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json=SUPERADMIN_CREDS)
        if response.status_code != 200:
            pytest.skip("SuperAdmin login failed")
        return response.json()["token"]
    
    @pytest.fixture
    def admin_token(self):
        """Get Administrador token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json=ADMIN_CREDS)
        if response.status_code != 200:
            pytest.skip("Admin login failed - user may not exist")
        return response.json()["token"]
    
    @pytest.fixture
    def usuario_token(self):
        """Get Usuario token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json=USUARIO_CREDS)
        if response.status_code != 200:
            pytest.skip("Usuario login failed - user may not exist")
        return response.json()["token"]
    
    def test_post_roles_superadmin_allowed(self, superadmin_token):
        """POST /api/roles with SuperAdmin should be allowed"""
        unique_name = f"TEST_ROLE_{uuid.uuid4().hex[:8]}"
        payload = {
            "nombre": unique_name,
            "descripcion": "Test role created by SuperAdmin",
            "permisos": []
        }
        headers = {"Authorization": f"Bearer {superadmin_token}"}
        response = requests.post(f"{BASE_URL}/api/roles", json=payload, headers=headers)
        print(f"POST /api/roles (SuperAdmin): {response.status_code}")
        
        # Should succeed - SuperAdmin has SISTEMA_ROLES_CREAR via fallback
        assert response.status_code in [200, 201], f"SuperAdmin should be able to create roles: {response.text}"
        
        data = response.json()
        print(f"SuperAdmin created role SUCCESS: {unique_name}")
        
        # Cleanup: delete the test role
        if "id" in data:
            requests.delete(f"{BASE_URL}/api/roles/{data['id']}", headers=headers)
    
    def test_post_roles_admin_legacy_fallback(self, admin_token):
        """POST /api/roles with Administrador should be allowed via legacy fallback"""
        unique_name = f"TEST_ROLE_ADMIN_{uuid.uuid4().hex[:8]}"
        payload = {
            "nombre": unique_name,
            "descripcion": "Test role created by Admin legacy",
            "permisos": []
        }
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.post(f"{BASE_URL}/api/roles", json=payload, headers=headers)
        print(f"POST /api/roles (Admin legacy): {response.status_code}")
        
        # Should succeed - Administrador has role_level >= 3 (legacy fallback)
        assert response.status_code in [200, 201], f"Admin legacy fallback should allow role creation: {response.text}"
        
        data = response.json()
        print(f"Admin legacy created role SUCCESS: {unique_name}")
        
        # Cleanup: delete the test role
        if "id" in data:
            requests.delete(f"{BASE_URL}/api/roles/{data['id']}", headers=headers)
    
    def test_post_roles_usuario_denied(self, usuario_token):
        """POST /api/roles with Usuario should be denied (403)"""
        payload = {
            "nombre": "SHOULD_NOT_CREATE",
            "descripcion": "Should not be created",
            "permisos": []
        }
        headers = {"Authorization": f"Bearer {usuario_token}"}
        response = requests.post(f"{BASE_URL}/api/roles", json=payload, headers=headers)
        print(f"POST /api/roles (Usuario): {response.status_code}")
        
        # Should be denied - Usuario has role_level < 3 and no RBAC permission
        assert response.status_code == 403, f"Usuario should be denied (403), got {response.status_code}: {response.text}"
        print("Usuario correctly denied (403) for POST /api/roles")


class TestGetEndpointsNoRegression:
    """GET endpoints - FASE 9 no regression tests"""
    
    @pytest.fixture
    def superadmin_token(self):
        """Get SuperAdmin token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json=SUPERADMIN_CREDS)
        if response.status_code != 200:
            pytest.skip("SuperAdmin login failed")
        return response.json()["token"]
    
    @pytest.fixture
    def admin_token(self):
        """Get Administrador token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json=ADMIN_CREDS)
        if response.status_code != 200:
            pytest.skip("Admin login failed - user may not exist")
        return response.json()["token"]
    
    def test_get_users_superadmin(self, superadmin_token):
        """GET /api/users with SuperAdmin should work (FASE 9 no regression)"""
        headers = {"Authorization": f"Bearer {superadmin_token}"}
        response = requests.get(f"{BASE_URL}/api/users", headers=headers)
        print(f"GET /api/users (SuperAdmin): {response.status_code}")
        
        assert response.status_code == 200, f"GET /api/users should work for SuperAdmin: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list of users"
        print(f"GET /api/users SUCCESS - {len(data)} users returned")
    
    def test_get_users_admin(self, admin_token):
        """GET /api/users with Administrador should work (FASE 9 no regression)"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/users", headers=headers)
        print(f"GET /api/users (Admin): {response.status_code}")
        
        assert response.status_code == 200, f"GET /api/users should work for Admin: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list of users"
        print(f"GET /api/users (Admin) SUCCESS - {len(data)} users returned")
    
    def test_get_roles_superadmin(self, superadmin_token):
        """GET /api/roles with SuperAdmin should work (FASE 9 no regression)"""
        headers = {"Authorization": f"Bearer {superadmin_token}"}
        response = requests.get(f"{BASE_URL}/api/roles", headers=headers)
        print(f"GET /api/roles (SuperAdmin): {response.status_code}")
        
        assert response.status_code == 200, f"GET /api/roles should work for SuperAdmin: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list of roles"
        print(f"GET /api/roles SUCCESS - {len(data)} roles returned")
    
    def test_get_roles_admin(self, admin_token):
        """GET /api/roles with Administrador should work (FASE 9 no regression)"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/roles", headers=headers)
        print(f"GET /api/roles (Admin): {response.status_code}")
        
        assert response.status_code == 200, f"GET /api/roles should work for Admin: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list of roles"
        print(f"GET /api/roles (Admin) SUCCESS - {len(data)} roles returned")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
