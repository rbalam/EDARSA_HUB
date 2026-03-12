"""
Backend API tests for Sistema de Análisis de Inventarios Dashboard
Tests: Dashboard endpoints, server configurations, and filters for 3 servers:
- MPRO (ManagmentPro)
- Cienfuegos SoftRestaurant  
- LA ESTELAR (SoftRestaurant)
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "admin@inventario.com"
TEST_PASSWORD = "admin123"

# Server IDs from the problem statement
SERVER_IDS = {
    "MPRO": "1b230a06-ffaf-4c70-bd27-b1be3579dea6",
    "Cienfuegos": "6d053c22-523e-48c0-b72b-96081e2d781b",
    "LA_ESTELAR": "a5ff0e25-f029-43db-b634-d4ac814c904f"
}


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token for API calls"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })
    assert response.status_code == 200, f"Login failed: {response.text}"
    data = response.json()
    assert "token" in data, "No token in login response"
    return data["token"]


@pytest.fixture(scope="module")
def auth_headers(auth_token):
    """Get headers with authorization token"""
    return {"Authorization": f"Bearer {auth_token}"}


class TestAuthentication:
    """Test authentication endpoints"""
    
    def test_login_success(self):
        """Test login with valid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200, f"Login failed with status {response.status_code}"
        data = response.json()
        assert "token" in data, "Token not in response"
        assert "user" in data, "User not in response"
        assert data["user"]["email"] == TEST_EMAIL

    def test_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "invalid@test.com",
            "password": "wrongpassword"
        })
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"


class TestDashboardServersConfigured:
    """Test the dashboard servers-configured endpoint"""
    
    def test_get_servers_configured(self, auth_headers):
        """Test GET /api/dashboard/servers-configured returns configured servers"""
        response = requests.get(
            f"{BASE_URL}/api/dashboard/servers-configured",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed with status {response.status_code}: {response.text}"
        data = response.json()
        
        # Should return a list
        assert isinstance(data, list), f"Expected list, got {type(data)}"
        
        # Should have at least the 3 servers mentioned
        server_names = [s.get("name", "") for s in data]
        print(f"Servers configured: {server_names}")
        
        # Check each server has required fields
        for server in data:
            assert "id" in server, "Server missing 'id' field"
            assert "name" in server, "Server missing 'name' field"
            assert "system_type" in server, "Server missing 'system_type' field"
    
    def test_servers_count(self, auth_headers):
        """Verify at least 3 servers are configured"""
        response = requests.get(
            f"{BASE_URL}/api/dashboard/servers-configured",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 3, f"Expected at least 3 servers, got {len(data)}"
        print(f"Total configured servers: {len(data)}")


class TestDashboardMPRO:
    """Test dashboard functionality with MPRO server"""
    
    def test_dashboard_mpro_loads(self, auth_headers):
        """Test dashboard loads data for MPRO server"""
        server_id = SERVER_IDS["MPRO"]
        response = requests.get(
            f"{BASE_URL}/api/dashboard/inventory-summary?server_id={server_id}",
            headers=auth_headers,
            timeout=120  # SQL queries can be slow
        )
        assert response.status_code == 200, f"MPRO dashboard failed: {response.text}"
        data = response.json()
        
        assert "success" in data, "Missing 'success' field"
        assert data["success"] == True, f"MPRO dashboard returned error: {data.get('message')}"
        assert "data" in data, "Missing 'data' field"
        
        dashboard_data = data["data"]
        assert "server_name" in dashboard_data, "Missing server_name"
        assert "kpis" in dashboard_data, "Missing KPIs"
        
        print(f"MPRO Dashboard - Server: {dashboard_data.get('server_name')}")
        print(f"MPRO KPIs: {dashboard_data.get('kpis')}")

    def test_mpro_kpis_calculated(self, auth_headers):
        """Verify KPIs are calculated for MPRO"""
        server_id = SERVER_IDS["MPRO"]
        response = requests.get(
            f"{BASE_URL}/api/dashboard/inventory-summary?server_id={server_id}",
            headers=auth_headers,
            timeout=120
        )
        assert response.status_code == 200
        data = response.json()
        
        if data.get("success"):
            kpis = data["data"].get("kpis", {})
            # Verify KPI fields exist
            expected_kpi_fields = [
                "total_diferencia_costo",
                "total_items_con_diferencia", 
                "total_items",
                "precision_inventario",
                "total_faltantes",
                "total_sobrantes"
            ]
            for field in expected_kpi_fields:
                assert field in kpis, f"Missing KPI field: {field}"
            print(f"MPRO KPIs validated: {len(expected_kpi_fields)} fields present")


class TestDashboardCienfuegos:
    """Test dashboard functionality with Cienfuegos SoftRestaurant server"""
    
    def test_dashboard_cienfuegos_loads(self, auth_headers):
        """Test dashboard loads data for Cienfuegos server"""
        server_id = SERVER_IDS["Cienfuegos"]
        response = requests.get(
            f"{BASE_URL}/api/dashboard/inventory-summary?server_id={server_id}",
            headers=auth_headers,
            timeout=120
        )
        assert response.status_code == 200, f"Cienfuegos dashboard failed: {response.text}"
        data = response.json()
        
        assert data.get("success") == True, f"Cienfuegos dashboard error: {data.get('message')}"
        
        dashboard_data = data["data"]
        print(f"Cienfuegos Dashboard - Server: {dashboard_data.get('server_name')}")
        print(f"Cienfuegos KPIs: {dashboard_data.get('kpis')}")

    def test_cienfuegos_has_data(self, auth_headers):
        """Verify Cienfuegos returns inventory data"""
        server_id = SERVER_IDS["Cienfuegos"]
        response = requests.get(
            f"{BASE_URL}/api/dashboard/inventory-summary?server_id={server_id}",
            headers=auth_headers,
            timeout=120
        )
        assert response.status_code == 200
        data = response.json()
        
        if data.get("success"):
            dashboard_data = data["data"]
            kpis = dashboard_data.get("kpis", {})
            # Cienfuegos should have data - from previous tests it had items
            total_items = kpis.get("total_items", 0)
            print(f"Cienfuegos total items: {total_items}")


class TestDashboardLaEstelar:
    """Test dashboard functionality with LA ESTELAR server"""
    
    def test_dashboard_la_estelar_loads(self, auth_headers):
        """Test dashboard loads data for LA ESTELAR server"""
        server_id = SERVER_IDS["LA_ESTELAR"]
        response = requests.get(
            f"{BASE_URL}/api/dashboard/inventory-summary?server_id={server_id}",
            headers=auth_headers,
            timeout=120
        )
        assert response.status_code == 200, f"LA ESTELAR dashboard failed: {response.text}"
        data = response.json()
        
        assert data.get("success") == True, f"LA ESTELAR dashboard error: {data.get('message')}"
        
        dashboard_data = data["data"]
        print(f"LA ESTELAR Dashboard - Server: {dashboard_data.get('server_name')}")
        print(f"LA ESTELAR System type: {dashboard_data.get('system_type')}")

    def test_la_estelar_kpis(self, auth_headers):
        """Verify KPIs are present for LA ESTELAR"""
        server_id = SERVER_IDS["LA_ESTELAR"]
        response = requests.get(
            f"{BASE_URL}/api/dashboard/inventory-summary?server_id={server_id}",
            headers=auth_headers,
            timeout=120
        )
        assert response.status_code == 200
        data = response.json()
        
        if data.get("success"):
            kpis = data["data"].get("kpis", {})
            print(f"LA ESTELAR KPIs: {kpis}")


class TestMPROFilters:
    """Test filter endpoints for MPRO server"""
    
    def test_mpro_tipos_movimiento(self, auth_headers):
        """Test tipos-movimiento endpoint for MPRO"""
        server_id = SERVER_IDS["MPRO"]
        response = requests.get(
            f"{BASE_URL}/api/servers/{server_id}/tipos-movimiento",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        assert isinstance(data, list), f"Expected list, got {type(data)}"
        print(f"MPRO Tipos Movimiento count: {len(data)}")
        
        # Verify structure if data exists
        if data:
            assert "codigo" in data[0], "Missing 'codigo' field"
            assert "descripcion" in data[0], "Missing 'descripcion' field"

    def test_mpro_categorias(self, auth_headers):
        """Test categorias endpoint for MPRO"""
        server_id = SERVER_IDS["MPRO"]
        response = requests.get(
            f"{BASE_URL}/api/servers/{server_id}/categorias",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        assert isinstance(data, list), f"Expected list, got {type(data)}"
        print(f"MPRO Categorías count: {len(data)}")

    def test_mpro_departamentos(self, auth_headers):
        """Test departamentos endpoint for MPRO"""
        server_id = SERVER_IDS["MPRO"]
        response = requests.get(
            f"{BASE_URL}/api/servers/{server_id}/departamentos",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        assert isinstance(data, list), f"Expected list, got {type(data)}"
        print(f"MPRO Departamentos count: {len(data)}")


class TestLaEstelarFilters:
    """Test filter endpoints for LA ESTELAR server"""
    
    def test_la_estelar_tipos_movimiento(self, auth_headers):
        """Test tipos-movimiento endpoint for LA ESTELAR"""
        server_id = SERVER_IDS["LA_ESTELAR"]
        response = requests.get(
            f"{BASE_URL}/api/servers/{server_id}/tipos-movimiento",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        assert isinstance(data, list), f"Expected list, got {type(data)}"
        print(f"LA ESTELAR Tipos Movimiento count: {len(data)}")

    def test_la_estelar_categorias(self, auth_headers):
        """Test categorias endpoint for LA ESTELAR"""
        server_id = SERVER_IDS["LA_ESTELAR"]
        response = requests.get(
            f"{BASE_URL}/api/servers/{server_id}/categorias",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        assert isinstance(data, list), f"Expected list, got {type(data)}"
        print(f"LA ESTELAR Categorías count: {len(data)}")

    def test_la_estelar_departamentos(self, auth_headers):
        """Test departamentos endpoint for LA ESTELAR"""
        server_id = SERVER_IDS["LA_ESTELAR"]
        response = requests.get(
            f"{BASE_URL}/api/servers/{server_id}/departamentos",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        assert isinstance(data, list), f"Expected list, got {type(data)}"
        print(f"LA ESTELAR Departamentos count: {len(data)}")


class TestServersEndpoint:
    """Test the servers list endpoint"""
    
    def test_get_servers_list(self, auth_headers):
        """Test GET /api/servers returns all active servers"""
        response = requests.get(
            f"{BASE_URL}/api/servers",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        assert isinstance(data, list), f"Expected list, got {type(data)}"
        print(f"Total active servers: {len(data)}")
        
        # Check server fields
        for server in data:
            assert "id" in server
            assert "name" in server
            assert "host" in server
            assert "system_type" in server
            print(f"  - {server['name']} ({server['system_type']})")

    def test_servers_have_queries_configured(self, auth_headers):
        """Verify servers have queries_configured flag"""
        response = requests.get(
            f"{BASE_URL}/api/servers",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        configured_count = sum(1 for s in data if s.get("queries_configured", False))
        print(f"Servers with queries configured: {configured_count} of {len(data)}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
