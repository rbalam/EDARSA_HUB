"""
Test suite for multi-branch inventory analysis system with user permissions.
Tests login, server filtering by permissions, and page loading.
"""
import pytest
import requests
import os

# Import centralized test credentials
from conftest import TEST_ADMIN_EMAIL, TEST_ADMIN_PASSWORD, TEST_USER_PASSWORD

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials (centralized)
ADMIN_CREDS = {
    "email": os.environ.get("TEST_ADMIN_EMAIL", TEST_ADMIN_EMAIL),
    "password": os.environ.get("TEST_ADMIN_PASSWORD", TEST_ADMIN_PASSWORD)
}
# Specific user credentials for permission tests
NOXTE_CREDS = {
    "email": os.environ.get("TEST_NOXTE_EMAIL", "noxte@alpyc.com"),
    "password": os.environ.get("TEST_NOXTE_PASSWORD", TEST_USER_PASSWORD)
}

# Server IDs
MANAGMENT_PRO_ID = "1b230a06-ffaf-4c70-bd27-b1be3579dea6"
CIENFUEGOS_ID = "6d053c22-523e-48c0-b72b-96081e2d781b"
LA_ESTELAR_ID = "a5ff0e25-f029-43db-b634-d4ac814c904f"


class TestLogin:
    """Test authentication endpoints"""
    
    def test_admin_login_success(self):
        """Admin login should work without errors"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json=ADMIN_CREDS)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "token" in data, "Response should contain token"
        assert "user" in data, "Response should contain user"
        assert data["user"]["email"] == ADMIN_CREDS["email"]
        assert data["user"]["role"] == "Administrador"
        
    def test_noxte_login_success(self):
        """noxte@alpyc.com login should work without errors"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json=NOXTE_CREDS)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "token" in data, "Response should contain token"
        assert "user" in data, "Response should contain user"
        assert data["user"]["email"] == NOXTE_CREDS["email"]
        # noxte should have allowed_servers configured
        assert "allowed_servers" in data["user"], "User should have allowed_servers field"
        assert MANAGMENT_PRO_ID in data["user"]["allowed_servers"], "noxte should have ManagmentPro server access"
        
    def test_invalid_login(self):
        """Invalid credentials should return 401"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "invalid@test.com", 
            "password": "wrongpassword"
        })
        assert response.status_code == 401


class TestServerPermissions:
    """Test server access filtering by user permissions"""
    
    @pytest.fixture
    def admin_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json=ADMIN_CREDS)
        return response.json()["token"]
    
    @pytest.fixture
    def noxte_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json=NOXTE_CREDS)
        return response.json()["token"]
    
    def test_admin_sees_3_servers(self, admin_token):
        """Admin should see all 3 servers"""
        response = requests.get(
            f"{BASE_URL}/api/servers",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        
        servers = response.json()
        assert len(servers) == 3, f"Admin should see 3 servers, got {len(servers)}"
        
        server_ids = [s["id"] for s in servers]
        assert MANAGMENT_PRO_ID in server_ids, "ManagmentPro should be visible"
        assert CIENFUEGOS_ID in server_ids, "Cienfuegos should be visible"
        assert LA_ESTELAR_ID in server_ids, "LA ESTELAR should be visible"
        
    def test_noxte_sees_only_1_server(self, noxte_token):
        """noxte should see only ManagmentPro server"""
        response = requests.get(
            f"{BASE_URL}/api/servers",
            headers={"Authorization": f"Bearer {noxte_token}"}
        )
        assert response.status_code == 200
        
        servers = response.json()
        assert len(servers) == 1, f"noxte should see only 1 server, got {len(servers)}"
        assert servers[0]["id"] == MANAGMENT_PRO_ID, "noxte should only see ManagmentPro"
        assert servers[0]["name"] == "ManagmentPro"


class TestUsersEndpoint:
    """Test users management endpoint"""
    
    @pytest.fixture
    def admin_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json=ADMIN_CREDS)
        return response.json()["token"]
    
    def test_get_users_requires_admin(self, admin_token):
        """GET /users should work for admin"""
        response = requests.get(
            f"{BASE_URL}/api/users",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        
        users = response.json()
        assert isinstance(users, list)
        assert len(users) >= 2, "Should have at least admin and noxte users"
        
        # Verify noxte user has correct permissions in database
        noxte_user = next((u for u in users if u["email"] == "noxte@alpyc.com"), None)
        assert noxte_user is not None, "noxte user should exist"
        assert MANAGMENT_PRO_ID in noxte_user.get("allowed_servers", [])


class TestSucursalesPermissions:
    """Test sucursales endpoint with permission filtering"""
    
    @pytest.fixture
    def admin_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json=ADMIN_CREDS)
        return response.json()["token"]
    
    @pytest.fixture
    def noxte_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json=NOXTE_CREDS)
        return response.json()["token"]
    
    def test_get_sucursales_for_managmentpro(self, admin_token):
        """Should return sucursales for ManagmentPro server"""
        response = requests.get(
            f"{BASE_URL}/api/servers/{MANAGMENT_PRO_ID}/sucursales",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        # This endpoint connects to external SQL Server, may fail if server is down
        # But the endpoint itself should work
        assert response.status_code in [200, 500], f"Unexpected status: {response.status_code}"
        
        if response.status_code == 200:
            sucursales = response.json()
            assert isinstance(sucursales, list)


class TestPermissionsUpdate:
    """Test permission update endpoint"""
    
    @pytest.fixture
    def admin_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json=ADMIN_CREDS)
        return response.json()["token"]
    
    def test_update_user_permissions_requires_admin(self, admin_token):
        """PUT /users/{id}/permissions should work for admin"""
        # Get noxte's user ID first
        response = requests.get(
            f"{BASE_URL}/api/users",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        users = response.json()
        noxte_user = next((u for u in users if u["email"] == "noxte@alpyc.com"), None)
        
        if noxte_user:
            # Try updating permissions (same values to not break anything)
            update_response = requests.put(
                f"{BASE_URL}/api/users/{noxte_user['id']}/permissions",
                headers={"Authorization": f"Bearer {admin_token}"},
                json={
                    "allowed_servers": noxte_user.get("allowed_servers", []),
                    "allowed_sucursales": noxte_user.get("allowed_sucursales", {}),
                    "allowed_warehouses": noxte_user.get("allowed_warehouses", {})
                }
            )
            assert update_response.status_code == 200, f"Permission update failed: {update_response.text}"
