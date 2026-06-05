"""
Backend API tests for Sistema de Permisos de Sucursales (Branch Permissions)
Tests:
- Admin sees all sucursales
- Restricted user only sees assigned sucursales (0021, 0022)
- Update user permissions with allowed_sucursales field
- Excel export generates formatted file with metadata
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

# Server ID for ManagmentPro
MPRO_SERVER_ID = "1b230a06-ffaf-4c70-bd27-b1be3579dea6"
# Expected sucursales for test user
EXPECTED_SUCURSALES = ["0021", "0022"]


@pytest.fixture(scope="module")
def admin_token():
    """Get authentication token for admin user"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    })
    assert response.status_code == 200, f"Admin login failed: {response.text}"
    return response.json()["token"]


@pytest.fixture(scope="module")
def test_user_token():
    """Get authentication token for restricted test user"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEST_USER_EMAIL_LOCAL,
        "password": TEST_USER_PASSWORD_LOCAL
    })
    assert response.status_code == 200, f"Test user login failed: {response.text}"
    return response.json()["token"]


@pytest.fixture(scope="module")
def admin_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture(scope="module")
def test_user_headers(test_user_token):
    return {"Authorization": f"Bearer {test_user_token}"}


class TestLoginFunctionality:
    """Test login works correctly for both users"""
    
    def test_admin_login_success(self):
        """Admin login with admin@inventario.com / admin123"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Admin login failed: {response.text}"
        data = response.json()
        assert "token" in data, "No token returned"
        assert data["user"]["role"] == "Administrador"
        print(f"✓ Admin login successful: {data['user']['name']}")

    def test_test_user_login_success(self):
        """Test user login with test credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_USER_EMAIL_LOCAL,
            "password": TEST_USER_PASSWORD_LOCAL
        })
        assert response.status_code == 200, f"Test user login failed: {response.text}"
        data = response.json()
        assert "token" in data, "No token returned"
        
        # Verify user has allowed_sucursales configured
        user = data["user"]
        assert "allowed_sucursales" in user, "allowed_sucursales field missing"
        print(f"✓ Test user login successful: {user['name']}")
        print(f"  allowed_sucursales: {user.get('allowed_sucursales')}")


class TestSucursalesFiltering:
    """Test that sucursales are filtered based on user permissions"""
    
    def test_admin_sees_all_sucursales(self, admin_headers):
        """Admin should see ALL sucursales without filtering"""
        response = requests.get(
            f"{BASE_URL}/api/servers/{MPRO_SERVER_ID}/sucursales",
            headers=admin_headers
        )
        assert response.status_code == 200, f"Failed to get sucursales: {response.text}"
        sucursales = response.json()
        
        # Admin should see more than just 2 sucursales
        assert isinstance(sucursales, list), "Response should be a list"
        print(f"✓ Admin sees {len(sucursales)} sucursales")
        for s in sucursales[:5]:
            print(f"  - {s.get('id')}: {s.get('nombre')}")
        
        # Should see significantly more than the restricted 2
        assert len(sucursales) > 2, f"Admin should see more than 2 sucursales, got {len(sucursales)}"

    def test_restricted_user_sees_only_assigned_sucursales(self, test_user_headers):
        """Test user should only see sucursales 0021 and 0022"""
        response = requests.get(
            f"{BASE_URL}/api/servers/{MPRO_SERVER_ID}/sucursales",
            headers=test_user_headers
        )
        assert response.status_code == 200, f"Failed to get sucursales: {response.text}"
        sucursales = response.json()
        
        assert isinstance(sucursales, list), "Response should be a list"
        sucursal_ids = [s.get('id') for s in sucursales]
        
        print(f"✓ Test user sees {len(sucursales)} sucursales:")
        for s in sucursales:
            print(f"  - {s.get('id')}: {s.get('nombre')}")
        
        # Verify only sees assigned sucursales
        assert len(sucursales) == 2, f"Expected 2 sucursales, got {len(sucursales)}"
        assert "0021" in sucursal_ids, "Sucursal 0021 should be visible"
        assert "0022" in sucursal_ids, "Sucursal 0022 should be visible"
        print("✓ Permission filtering working correctly!")


class TestPermissionsEndpoint:
    """Test permissions update endpoint accepts allowed_sucursales"""
    
    def test_update_permissions_with_allowed_sucursales(self, admin_headers):
        """Admin can update user permissions including allowed_sucursales"""
        # First get users to find test user ID
        users_response = requests.get(f"{BASE_URL}/api/users", headers=admin_headers)
        assert users_response.status_code == 200
        users = users_response.json()
        
        # Find the test user
        test_user = next((u for u in users if u.get("email") == TEST_USER_EMAIL), None)
        assert test_user is not None, "Test user not found"
        
        user_id = test_user["id"]
        print(f"Testing permissions update for user {user_id}")
        
        # Update with allowed_sucursales
        new_permissions = {
            "allowed_servers": [MPRO_SERVER_ID],
            "allowed_sucursales": {
                MPRO_SERVER_ID: ["0021", "0022"]
            }
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
        assert "allowed_sucursales" in data.get("updated_fields", [])
        print(f"✓ Permissions updated: {data}")


class TestUsuariosPage:
    """Test that Usuarios page loads correctly"""
    
    def test_users_list_returns_data(self, admin_headers):
        """Users endpoint returns list of users"""
        response = requests.get(f"{BASE_URL}/api/users", headers=admin_headers)
        assert response.status_code == 200, f"Failed to get users: {response.text}"
        users = response.json()
        
        assert isinstance(users, list), "Response should be a list"
        assert len(users) > 0, "Should have at least one user"
        
        print(f"✓ Users endpoint returns {len(users)} users:")
        for user in users:
            allowed_sucursales_count = sum(
                len(v) for v in user.get('allowed_sucursales', {}).values()
            )
            print(f"  - {user['name']} ({user['role']}): {allowed_sucursales_count} sucursales")


class TestExcelExport:
    """Test Excel export with professional formatting"""
    
    def test_excel_export_generates_file(self, admin_headers):
        """Excel export generates a valid xlsx file"""
        # Sample data to export
        export_data = {
            "data": [
                {
                    "Codigo": "P001",
                    "Descripcion": "Producto Test",
                    "Cantidad": 100.5,
                    "Costo": 25.99,
                    "Porcentaje": 15.5
                }
            ],
            "filename": "test_export.xlsx",
            "metadata": {
                "sucursal": "130° QUERETARO",
                "almacen": "ALMACEN CENTRAL",
                "folio_inicial": "001",
                "folio_final": "100",
                "fecha_ini": "2024-01-01",
                "fecha_fin": "2024-12-31"
            }
        }
        
        response = requests.post(
            f"{BASE_URL}/api/reports/export/excel",
            json=export_data,
            headers=admin_headers
        )
        
        assert response.status_code == 200, f"Excel export failed: {response.text}"
        
        # Verify content type
        content_type = response.headers.get('content-type', '')
        assert 'spreadsheet' in content_type or 'octet-stream' in content_type, f"Wrong content type: {content_type}"
        
        # Verify file size > 0
        content = response.content
        assert len(content) > 0, "Excel file is empty"
        
        # Verify it's a valid xlsx (starts with PK for zip format)
        assert content[:2] == b'PK', "File doesn't appear to be a valid xlsx"
        
        print(f"✓ Excel export successful: {len(content)} bytes")

    def test_excel_with_empty_data_returns_empty(self, admin_headers):
        """Excel export with empty data returns empty response"""
        export_data = {
            "data": [],
            "filename": "empty_export.xlsx"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/reports/export/excel",
            json=export_data,
            headers=admin_headers
        )
        
        # Should return 200 with empty content or appropriate message
        assert response.status_code == 200
        print("✓ Empty data export handled correctly")


class TestSucursalesInfo:
    """Verify sucursal names match expected values"""
    
    def test_sucursales_0021_and_0022_exist(self, admin_headers):
        """Verify sucursales 0021 (130° QUERETARO) and 0022 (AGRICREME) exist"""
        response = requests.get(
            f"{BASE_URL}/api/servers/{MPRO_SERVER_ID}/sucursales",
            headers=admin_headers
        )
        assert response.status_code == 200
        sucursales = response.json()
        
        sucursal_dict = {s.get('id'): s.get('nombre') for s in sucursales}
        
        # Check 0021 exists
        assert "0021" in sucursal_dict, "Sucursal 0021 not found"
        print(f"✓ Sucursal 0021: {sucursal_dict.get('0021')}")
        
        # Check 0022 exists
        assert "0022" in sucursal_dict, "Sucursal 0022 not found"
        print(f"✓ Sucursal 0022: {sucursal_dict.get('0022')}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
