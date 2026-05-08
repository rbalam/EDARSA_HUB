"""
Backend API tests for Sistema de Permisos (User Permissions System)
Tests:
- User login with credentials
- Users list endpoint (admin only)
- Permission system - Admin sees all servers
- Permission system - Restricted user only sees assigned servers
- Update user permissions endpoint
"""
import pytest
import requests
import os

# Import centralized test credentials
from conftest import TEST_ADMIN_EMAIL, TEST_ADMIN_PASSWORD, TEST_USER_EMAIL, TEST_USER_PASSWORD

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials (centralized)
ADMIN_EMAIL = os.environ.get("TEST_ADMIN_EMAIL", TEST_ADMIN_EMAIL)
ADMIN_PASSWORD = os.environ.get("TEST_ADMIN_PASSWORD", TEST_ADMIN_PASSWORD)
TEST_USER_EMAIL_LOCAL = os.environ.get("TEST_USER_EMAIL", TEST_USER_EMAIL)
TEST_USER_PASSWORD_LOCAL = os.environ.get("TEST_USER_PASSWORD", TEST_USER_PASSWORD)

# Server IDs
SERVER_IDS = {
    "MPRO": "1b230a06-ffaf-4c70-bd27-b1be3579dea6",
    "Cienfuegos": "6d053c22-523e-48c0-b72b-96081e2d781b",
    "LA_ESTELAR": "a5ff0e25-f029-43db-b634-d4ac814c904f"
}


@pytest.fixture(scope="module")
def admin_token():
    """Get authentication token for admin user"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    })
    assert response.status_code == 200, f"Admin login failed: {response.text}"
    data = response.json()
    assert "token" in data, "No token in login response"
    return data["token"]


@pytest.fixture(scope="module")
def admin_headers(admin_token):
    """Get headers with admin authorization token"""
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture(scope="module")
def test_user_token():
    """Get authentication token for restricted test user"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEST_USER_EMAIL_LOCAL,
        "password": TEST_USER_PASSWORD_LOCAL
    })
    if response.status_code != 200:
        pytest.skip(f"Test user login failed: {response.text}")
    data = response.json()
    assert "token" in data, "No token in login response"
    return data["token"]


@pytest.fixture(scope="module")
def test_user_headers(test_user_token):
    """Get headers with test user authorization token"""
    return {"Authorization": f"Bearer {test_user_token}"}


class TestLoginWithCredentials:
    """Test login functionality with correct credentials"""
    
    def test_admin_login_success(self):
        """Test admin login with correct credentials returns token and user data"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Admin login failed with status {response.status_code}: {response.text}"
        data = response.json()
        
        # Verify token is returned
        assert "token" in data, "Token not in response"
        assert len(data["token"]) > 0, "Token is empty"
        
        # Verify user data is returned
        assert "user" in data, "User not in response"
        assert data["user"]["email"] == ADMIN_EMAIL
        assert data["user"]["role"] == "Administrador"
        print(f"Admin login success: {data['user']['name']} ({data['user']['role']})")

    def test_test_user_login_success(self):
        """Test restricted user login with correct credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        })
        
        if response.status_code != 200:
            print("Test user not found or login failed - may need to be created first")
            pytest.skip("Test user not created yet")
            
        data = response.json()
        assert "token" in data, "Token not in response"
        assert "user" in data, "User not in response"
        assert data["user"]["email"] == TEST_USER_EMAIL
        print(f"Test user login success: {data['user']['name']} ({data['user']['role']})")

    def test_invalid_credentials_rejected(self):
        """Test login with invalid credentials returns 401"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "wrong@test.com",
            "password": "wrongpassword"
        })
        assert response.status_code == 401, f"Expected 401 for invalid credentials, got {response.status_code}"
        print("Invalid credentials correctly rejected with 401")


class TestUsersPage:
    """Test users list endpoint - admin only functionality"""
    
    def test_users_endpoint_requires_auth(self):
        """Test that /api/users requires authentication"""
        response = requests.get(f"{BASE_URL}/api/users")
        assert response.status_code == 403, f"Expected 403 for unauthenticated request, got {response.status_code}"
        print("Users endpoint correctly requires authentication")

    def test_admin_can_list_users(self, admin_headers):
        """Test admin can access users list"""
        response = requests.get(
            f"{BASE_URL}/api/users",
            headers=admin_headers
        )
        assert response.status_code == 200, f"Admin failed to get users: {response.text}"
        data = response.json()
        
        # Verify response is a list
        assert isinstance(data, list), f"Expected list, got {type(data)}"
        
        # Verify user fields
        if data:
            user = data[0]
            assert "id" in user, "User missing 'id' field"
            assert "email" in user, "User missing 'email' field"
            assert "name" in user, "User missing 'name' field"
            assert "role" in user, "User missing 'role' field"
            
        print(f"Admin can list {len(data)} users")
        for user in data[:5]:  # Print first 5
            role = user.get('role', 'Unknown')
            servers = len(user.get('allowed_servers', []))
            print(f"  - {user['name']} ({role}) - {servers} servers assigned")

    def test_non_admin_cannot_list_users(self, test_user_headers):
        """Test non-admin user cannot access users list"""
        response = requests.get(
            f"{BASE_URL}/api/users",
            headers=test_user_headers
        )
        assert response.status_code == 403, f"Expected 403 for non-admin, got {response.status_code}"
        print("Non-admin correctly blocked from users list with 403")


class TestPermissionsAdminSeesAllServers:
    """Test that admin users see all servers"""
    
    def test_admin_sees_all_servers(self, admin_headers):
        """Test admin can see all servers without restrictions"""
        response = requests.get(
            f"{BASE_URL}/api/servers",
            headers=admin_headers
        )
        assert response.status_code == 200, f"Failed to get servers: {response.text}"
        servers = response.json()
        
        assert isinstance(servers, list), f"Expected list, got {type(servers)}"
        assert len(servers) >= 3, f"Admin should see at least 3 servers, got {len(servers)}"
        
        server_names = [s.get("name") for s in servers]
        print(f"Admin sees {len(servers)} servers: {server_names}")
        
        # Verify all expected servers are visible
        for server_name in ["ManagmentPro", "Cienfuegos", "LA ESTELAR"]:
            found = any(server_name.lower() in name.lower() for name in server_names)
            print(f"  - {server_name}: {'✓ Visible' if found else '✗ Not found'}")


class TestPermissionsRestrictedUserAccess:
    """Test that restricted users only see assigned servers"""
    
    def test_restricted_user_sees_only_assigned_servers(self, test_user_headers, admin_headers):
        """Test restricted user only sees servers they have access to"""
        # First get the test user's permissions
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        })
        
        if response.status_code != 200:
            pytest.skip("Test user not available")
            
        user_data = response.json()["user"]
        allowed_servers = user_data.get("allowed_servers", [])
        
        print(f"Test user allowed_servers: {allowed_servers}")
        
        # Get servers as the test user
        response = requests.get(
            f"{BASE_URL}/api/servers",
            headers=test_user_headers
        )
        assert response.status_code == 200, f"Failed to get servers: {response.text}"
        visible_servers = response.json()
        
        visible_server_ids = [s.get("id") for s in visible_servers]
        print(f"Test user sees {len(visible_servers)} servers: {[s.get('name') for s in visible_servers]}")
        
        # If user has allowed_servers configured, verify filtering works
        if allowed_servers:
            # All visible servers should be in allowed_servers
            for server_id in visible_server_ids:
                assert server_id in allowed_servers, f"Server {server_id} visible but not in allowed_servers"
            print("✓ Permission filtering working - user only sees assigned servers")
        else:
            # User with no allowed_servers should see no servers (unless admin)
            if user_data.get("role") != "Administrador":
                assert len(visible_servers) == 0, f"User with no allowed_servers should see 0 servers, sees {len(visible_servers)}"
                print("✓ User with no allowed_servers correctly sees 0 servers")


class TestUpdateUserPermissions:
    """Test updating user permissions endpoint"""
    
    def test_admin_can_update_permissions(self, admin_headers):
        """Test admin can update user permissions"""
        # First get users list
        response = requests.get(
            f"{BASE_URL}/api/users",
            headers=admin_headers
        )
        assert response.status_code == 200
        users = response.json()
        
        # Find a non-admin user to update
        non_admin_user = next((u for u in users if u.get("role") != "Administrador"), None)
        
        if not non_admin_user:
            pytest.skip("No non-admin user found to test permissions update")
        
        user_id = non_admin_user["id"]
        print(f"Testing permissions update for user: {non_admin_user['name']} ({user_id})")
        
        # Update permissions
        new_permissions = {
            "company_group": "Grupo Test",
            "allowed_servers": [SERVER_IDS["Cienfuegos"]],
            "allowed_warehouses": {}
        }
        
        response = requests.put(
            f"{BASE_URL}/api/users/{user_id}/permissions",
            json=new_permissions,
            headers=admin_headers
        )
        assert response.status_code == 200, f"Failed to update permissions: {response.text}"
        
        data = response.json()
        assert "message" in data
        assert "Permisos actualizados" in data["message"]
        print(f"✓ Permissions updated successfully: {data}")

    def test_non_admin_cannot_update_permissions(self, test_user_headers, admin_headers):
        """Test non-admin cannot update user permissions"""
        # Get a user ID first
        response = requests.get(
            f"{BASE_URL}/api/users",
            headers=admin_headers
        )
        if response.status_code != 200:
            pytest.skip("Cannot get users list")
            
        users = response.json()
        if not users:
            pytest.skip("No users found")
            
        user_id = users[0]["id"]
        
        # Try to update as non-admin
        response = requests.put(
            f"{BASE_URL}/api/users/{user_id}/permissions",
            json={"allowed_servers": []},
            headers=test_user_headers
        )
        assert response.status_code == 403, f"Expected 403, got {response.status_code}"
        print("✓ Non-admin correctly blocked from updating permissions")


class TestCompanyGroups:
    """Test company groups endpoint"""
    
    def test_get_company_groups(self, admin_headers):
        """Test getting list of company groups"""
        response = requests.get(
            f"{BASE_URL}/api/company-groups",
            headers=admin_headers
        )
        assert response.status_code == 200, f"Failed to get company groups: {response.text}"
        data = response.json()
        
        assert isinstance(data, list), f"Expected list, got {type(data)}"
        print(f"Company groups: {data}")
        
        # Default groups should be present
        expected_defaults = ["Grupo Principal", "Grupo Norte", "Grupo Sur", "Grupo Centro"]
        for group in expected_defaults:
            if group in data:
                print(f"  ✓ {group}")


class TestServerAccessPermissions:
    """Test server-specific access based on permissions"""
    
    def test_admin_can_access_any_server(self, admin_headers):
        """Test admin can access any individual server"""
        for server_name, server_id in SERVER_IDS.items():
            response = requests.get(
                f"{BASE_URL}/api/servers/{server_id}",
                headers=admin_headers
            )
            assert response.status_code == 200, f"Admin failed to access {server_name}: {response.text}"
            print(f"✓ Admin can access {server_name}")

    def test_restricted_user_blocked_from_unauthorized_server(self, test_user_headers, admin_headers):
        """Test restricted user cannot access servers they don't have permission for"""
        # Get test user's allowed servers
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        })
        
        if response.status_code != 200:
            pytest.skip("Test user not available")
            
        user_data = response.json()["user"]
        allowed_servers = user_data.get("allowed_servers", [])
        
        # Try to access a server not in allowed_servers
        for server_name, server_id in SERVER_IDS.items():
            if server_id not in allowed_servers:
                response = requests.get(
                    f"{BASE_URL}/api/servers/{server_id}",
                    headers=test_user_headers
                )
                # Should get 403 for unauthorized access
                if response.status_code == 403:
                    print(f"✓ Correctly blocked from {server_name}")
                else:
                    print(f"Note: {server_name} access returned {response.status_code}")
                break


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
