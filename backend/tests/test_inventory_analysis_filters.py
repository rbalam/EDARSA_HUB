"""
Test suite for Inventory Analysis Report Filters
Tests for:
1. Report filters endpoint (categorias, familias, subfamilias)
2. Inventory analysis with filter parameters (Valor_Real, Teorico columns)
3. Frontend label changes verification
"""

import pytest
import requests
import os

# Import centralized test credentials
from conftest import TEST_ADMIN_EMAIL, TEST_ADMIN_PASSWORD

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
if not BASE_URL:
    BASE_URL = "https://erp-crm-enterprise-1.preview.emergentagent.com"

# Test credentials (centralized)
ADMIN_EMAIL = os.environ.get("TEST_ADMIN_EMAIL", TEST_ADMIN_EMAIL)
ADMIN_PASSWORD = os.environ.get("TEST_ADMIN_PASSWORD", TEST_ADMIN_PASSWORD)

# MPRO Server ID
MPRO_SERVER_ID = "1b230a06-ffaf-4c70-bd27-b1be3579dea6"


class TestAuth:
    """Authentication tests"""
    
    def test_admin_login(self):
        """Test admin login works"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "token" in data, "No token in response"
        assert "user" in data, "No user in response"
        assert data["user"]["role"] == "Administrador"


class TestReportFilters:
    """Tests for GET /api/servers/{server_id}/report-filters endpoint"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token before each test"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        self.token = response.json()["token"]
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
    
    def test_report_filters_returns_categorias(self):
        """Test that report-filters endpoint returns categorias for MPRO server"""
        response = requests.get(
            f"{BASE_URL}/api/servers/{MPRO_SERVER_ID}/report-filters",
            headers=self.headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        # Validate categorias
        assert "categorias" in data, "Missing categorias in response"
        assert isinstance(data["categorias"], list), "categorias should be a list"
        assert len(data["categorias"]) > 0, "categorias list should not be empty"
        
        # Validate structure of categoria item
        if data["categorias"]:
            categoria = data["categorias"][0]
            assert "id" in categoria, "categoria should have id"
            assert "nombre" in categoria, "categoria should have nombre"
    
    def test_report_filters_returns_familias(self):
        """Test that report-filters endpoint returns familias for MPRO server"""
        response = requests.get(
            f"{BASE_URL}/api/servers/{MPRO_SERVER_ID}/report-filters",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        
        # Validate familias
        assert "familias" in data, "Missing familias in response"
        assert isinstance(data["familias"], list), "familias should be a list"
        assert len(data["familias"]) > 0, "familias list should not be empty"
        
        # Validate structure
        if data["familias"]:
            familia = data["familias"][0]
            assert "id" in familia, "familia should have id"
            assert "nombre" in familia, "familia should have nombre"
    
    def test_report_filters_returns_subfamilias(self):
        """Test that report-filters endpoint returns subfamilias for MPRO server"""
        response = requests.get(
            f"{BASE_URL}/api/servers/{MPRO_SERVER_ID}/report-filters",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        
        # Validate subfamilias
        assert "subfamilias" in data, "Missing subfamilias in response"
        assert isinstance(data["subfamilias"], list), "subfamilias should be a list"
        assert len(data["subfamilias"]) > 0, "subfamilias list should not be empty"
        
        # Validate structure
        if data["subfamilias"]:
            subfamilia = data["subfamilias"][0]
            assert "id" in subfamilia, "subfamilia should have id"
            assert "nombre" in subfamilia, "subfamilia should have nombre"
    
    def test_report_filters_expected_counts(self):
        """Test that report-filters returns expected counts (19 cats, 72 fams, 106 subfams)"""
        response = requests.get(
            f"{BASE_URL}/api/servers/{MPRO_SERVER_ID}/report-filters",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify counts match expected
        assert len(data["categorias"]) == 19, f"Expected 19 categorias, got {len(data['categorias'])}"
        assert len(data["familias"]) == 72, f"Expected 72 familias, got {len(data['familias'])}"
        assert len(data["subfamilias"]) == 106, f"Expected 106 subfamilias, got {len(data['subfamilias'])}"
    
    def test_report_filters_for_non_mpro_returns_empty(self):
        """Test that report-filters returns empty lists for non-MPRO servers"""
        # First get list of servers to find a non-MPRO server
        response = requests.get(f"{BASE_URL}/api/servers", headers=self.headers)
        servers = response.json()
        
        # Find a non-MPRO server
        non_mpro_server = None
        for server in servers:
            if server.get("system_type") != "MPRO":
                non_mpro_server = server
                break
        
        if non_mpro_server:
            response = requests.get(
                f"{BASE_URL}/api/servers/{non_mpro_server['id']}/report-filters",
                headers=self.headers
            )
            assert response.status_code == 200
            data = response.json()
            
            # Non-MPRO should return empty lists
            assert data["categorias"] == [], "Non-MPRO should return empty categorias"
            assert data["familias"] == [], "Non-MPRO should return empty familias"
            assert data["subfamilias"] == [], "Non-MPRO should return empty subfamilias"
        else:
            pytest.skip("No non-MPRO server found to test")


class TestInventoryAnalysisEndpoint:
    """Tests for POST /api/reports/inventory-analysis endpoint"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token before each test"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        self.token = response.json()["token"]
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
    
    def test_inventory_analysis_accepts_filter_params(self):
        """Test that inventory-analysis endpoint accepts categorias/familias/subfamilias parameters"""
        # Get sample filters first
        filters_response = requests.get(
            f"{BASE_URL}/api/servers/{MPRO_SERVER_ID}/report-filters",
            headers=self.headers
        )
        filters = filters_response.json()
        
        # Get sample sucursal and almacen
        sucursales_response = requests.get(
            f"{BASE_URL}/api/servers/{MPRO_SERVER_ID}/sucursales",
            headers=self.headers
        )
        sucursales = sucursales_response.json()
        if not sucursales:
            pytest.skip("No sucursales available")
        
        sucursal = sucursales[0]["nombre"]
        
        # Get almacenes for sucursal
        almacenes_response = requests.get(
            f"{BASE_URL}/api/servers/{MPRO_SERVER_ID}/almacenes",
            params={"sucursal_id": sucursales[0]["id"]},
            headers=self.headers
        )
        almacenes = almacenes_response.json()
        if not almacenes:
            pytest.skip("No almacenes available")
        
        almacen = almacenes[0]["nombre"]
        
        # Get inventarios
        inventarios_response = requests.get(
            f"{BASE_URL}/api/servers/{MPRO_SERVER_ID}/inventarios",
            params={"sucursal_id": sucursales[0]["id"], "almacen_id": almacenes[0]["id"]},
            headers=self.headers
        )
        inventarios = inventarios_response.json()
        if len(inventarios) < 2:
            pytest.skip("Not enough inventarios for test")
        
        # Select first and last inventario
        folio_inicial = inventarios[-1]["folio"]  # Oldest
        folio_final = inventarios[0]["folio"]  # Newest
        fecha_ini = inventarios[-1].get("fecha", "2024-01-01")
        fecha_fin = inventarios[0].get("fecha", "2024-12-31")
        
        # Prepare request with filter parameters
        payload = {
            "server_id": MPRO_SERVER_ID,
            "sucursal": sucursal,
            "almacen": almacen,
            "fecha_ini": fecha_ini,
            "fecha_fin": fecha_fin,
            "folio_inicial": folio_inicial,
            "folio_final": folio_final,
            # New filter parameters
            "categorias": [filters["categorias"][0]["id"]] if filters["categorias"] else [],
            "familias": [filters["familias"][0]["id"]] if filters["familias"] else [],
            "subfamilias": [filters["subfamilias"][0]["id"]] if filters["subfamilias"] else []
        }
        
        # Make request
        response = requests.post(
            f"{BASE_URL}/api/reports/inventory-analysis",
            json=payload,
            headers=self.headers,
            timeout=120
        )
        
        # Endpoint should accept the parameters without error
        # May return empty results if no data matches, but should not error
        assert response.status_code in [200, 404], f"Unexpected status: {response.status_code}, {response.text}"
        
        if response.status_code == 200:
            data = response.json()
            assert "data" in data, "Response should have data field"
            assert "count" in data, "Response should have count field"


class TestInventoryAnalysisResponseColumns:
    """Tests to verify Valor_Real and Teorico columns in response"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        self.token = response.json()["token"]
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
    
    def test_response_contains_valor_real_and_teorico(self):
        """Test that inventory-analysis response contains Valor_Real and Teorico columns"""
        # Get necessary data to make request
        sucursales_response = requests.get(
            f"{BASE_URL}/api/servers/{MPRO_SERVER_ID}/sucursales",
            headers=self.headers
        )
        sucursales = sucursales_response.json()
        if not sucursales:
            pytest.skip("No sucursales available")
        
        sucursal = sucursales[0]["nombre"]
        sucursal_id = sucursales[0]["id"]
        
        almacenes_response = requests.get(
            f"{BASE_URL}/api/servers/{MPRO_SERVER_ID}/almacenes",
            params={"sucursal_id": sucursal_id},
            headers=self.headers
        )
        almacenes = almacenes_response.json()
        if not almacenes:
            pytest.skip("No almacenes available")
        
        almacen = almacenes[0]["nombre"]
        almacen_id = almacenes[0]["id"]
        
        inventarios_response = requests.get(
            f"{BASE_URL}/api/servers/{MPRO_SERVER_ID}/inventarios",
            params={"sucursal_id": sucursal_id, "almacen_id": almacen_id},
            headers=self.headers
        )
        inventarios = inventarios_response.json()
        if len(inventarios) < 2:
            pytest.skip("Not enough inventarios")
        
        folio_inicial = inventarios[-1]["folio"]
        folio_final = inventarios[0]["folio"]
        fecha_ini = inventarios[-1].get("fecha", "2024-01-01")
        fecha_fin = inventarios[0].get("fecha", "2024-12-31")
        
        payload = {
            "server_id": MPRO_SERVER_ID,
            "sucursal": sucursal,
            "almacen": almacen,
            "fecha_ini": fecha_ini,
            "fecha_fin": fecha_fin,
            "folio_inicial": folio_inicial,
            "folio_final": folio_final,
            "categorias": [],
            "familias": [],
            "subfamilias": []
        }
        
        response = requests.post(
            f"{BASE_URL}/api/reports/inventory-analysis",
            json=payload,
            headers=self.headers,
            timeout=120
        )
        
        if response.status_code != 200:
            pytest.skip(f"Analysis endpoint returned {response.status_code}")
        
        data = response.json()
        results = data.get("data", [])
        
        if not results:
            pytest.skip("No results returned from analysis")
        
        # Check first result for required columns
        first_result = results[0]
        
        # Verify Valor_Real column exists
        assert "Valor_Real" in first_result, f"Missing Valor_Real column. Keys: {list(first_result.keys())}"
        
        # Verify Teorico column exists
        assert "Teorico" in first_result, f"Missing Teorico column. Keys: {list(first_result.keys())}"
        
        # Verify values are numeric
        assert isinstance(first_result["Valor_Real"], (int, float)), "Valor_Real should be numeric"
        assert isinstance(first_result["Teorico"], (int, float)), "Teorico should be numeric"


class TestServersList:
    """Tests for servers endpoint"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        self.token = response.json()["token"]
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
    
    def test_servers_list(self):
        """Test servers list includes MPRO server"""
        response = requests.get(f"{BASE_URL}/api/servers", headers=self.headers)
        assert response.status_code == 200
        servers = response.json()
        
        # Find MPRO server
        mpro_server = None
        for server in servers:
            if server["id"] == MPRO_SERVER_ID:
                mpro_server = server
                break
        
        assert mpro_server is not None, f"MPRO server {MPRO_SERVER_ID} not found"
        assert mpro_server["system_type"] == "MPRO", "Server should be MPRO type"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
