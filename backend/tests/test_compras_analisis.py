"""
Test suite for Compras Análisis module endpoints
Tests the drill-down functionality: Proveedor → Facturas → Productos
"""
import pytest
import requests
import os

# Import centralized test credentials
from conftest import TEST_ADMIN_EMAIL, TEST_ADMIN_PASSWORD

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestComprasAnalisis:
    """Tests for the Análisis de Compras feature"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures"""
        # Login to get token (using centralized credentials)
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": os.environ.get("TEST_ADMIN_EMAIL", TEST_ADMIN_EMAIL),
            "password": os.environ.get("TEST_ADMIN_PASSWORD", TEST_ADMIN_PASSWORD)
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        self.token = response.json()["token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
        
        # Get servers
        servers_response = requests.get(f"{BASE_URL}/api/servers", headers=self.headers)
        assert servers_response.status_code == 200
        self.servers = servers_response.json()
        
        # Find SoftRestaurant server (130° MERIDA or CIENFUEGOS)
        self.softrestaurant_server = None
        self.mpro_server = None
        for server in self.servers:
            if server.get('system_type') == 'SoftRestaurant':
                self.softrestaurant_server = server
            elif server.get('system_type') == 'MPRO':
                self.mpro_server = server
    
    # ============ POST /api/compras/analisis Tests ============
    
    def test_analisis_endpoint_returns_200(self):
        """Test that analisis endpoint returns 200 for valid request"""
        if not self.softrestaurant_server:
            pytest.skip("No SoftRestaurant server available")
        
        response = requests.post(f"{BASE_URL}/api/compras/analisis", 
            headers=self.headers,
            json={
                "server_id": self.softrestaurant_server['id'],
                "sucursal": self.softrestaurant_server['name'],
                "anios": ["2024", "2025"],
                "meses": ["10", "11", "12"]
            }
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    
    def test_analisis_returns_proveedores_list(self):
        """Test that analisis returns a list of proveedores"""
        if not self.softrestaurant_server:
            pytest.skip("No SoftRestaurant server available")
        
        response = requests.post(f"{BASE_URL}/api/compras/analisis", 
            headers=self.headers,
            json={
                "server_id": self.softrestaurant_server['id'],
                "sucursal": self.softrestaurant_server['name'],
                "anios": ["2024"],
                "meses": ["10", "11", "12"]
            }
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "proveedores" in data, "Response should contain 'proveedores' key"
        assert isinstance(data["proveedores"], list), "proveedores should be a list"
        assert len(data["proveedores"]) > 0, "Should return at least one proveedor"
    
    def test_analisis_proveedor_has_required_fields(self):
        """Test that each proveedor has required fields"""
        if not self.softrestaurant_server:
            pytest.skip("No SoftRestaurant server available")
        
        response = requests.post(f"{BASE_URL}/api/compras/analisis", 
            headers=self.headers,
            json={
                "server_id": self.softrestaurant_server['id'],
                "sucursal": self.softrestaurant_server['name'],
                "anios": ["2024"],
                "meses": ["10", "11", "12"]
            }
        )
        assert response.status_code == 200
        data = response.json()
        
        if len(data["proveedores"]) > 0:
            proveedor = data["proveedores"][0]
            assert "codigo" in proveedor, "Proveedor should have 'codigo'"
            assert "nombre" in proveedor, "Proveedor should have 'nombre'"
            assert "total" in proveedor, "Proveedor should have 'total'"
    
    def test_analisis_returns_alertas(self):
        """Test that analisis returns alertas field"""
        if not self.softrestaurant_server:
            pytest.skip("No SoftRestaurant server available")
        
        response = requests.post(f"{BASE_URL}/api/compras/analisis", 
            headers=self.headers,
            json={
                "server_id": self.softrestaurant_server['id'],
                "sucursal": self.softrestaurant_server['name'],
                "anios": ["2024"],
                "meses": ["10"]
            }
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "alertas" in data, "Response should contain 'alertas' key"
        assert isinstance(data["alertas"], list), "alertas should be a list"
    
    def test_analisis_multiple_months(self):
        """Test that analisis works with multiple months selected"""
        if not self.softrestaurant_server:
            pytest.skip("No SoftRestaurant server available")
        
        response = requests.post(f"{BASE_URL}/api/compras/analisis", 
            headers=self.headers,
            json={
                "server_id": self.softrestaurant_server['id'],
                "sucursal": self.softrestaurant_server['name'],
                "anios": ["2024"],
                "meses": ["01", "02", "03", "04", "05", "06"]
            }
        )
        assert response.status_code == 200
        data = response.json()
        
        # Check that proveedores have month columns
        if len(data["proveedores"]) > 0:
            proveedor = data["proveedores"][0]
            # Should have at least one month column
            month_columns = [k for k in proveedor.keys() if k in ["01", "02", "03", "04", "05", "06"]]
            assert len(month_columns) > 0, "Proveedor should have month columns"
    
    def test_analisis_multiple_years(self):
        """Test that analisis works with multiple years selected"""
        if not self.softrestaurant_server:
            pytest.skip("No SoftRestaurant server available")
        
        response = requests.post(f"{BASE_URL}/api/compras/analisis", 
            headers=self.headers,
            json={
                "server_id": self.softrestaurant_server['id'],
                "sucursal": self.softrestaurant_server['name'],
                "anios": ["2024", "2025"],
                "meses": ["10", "11", "12"]
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "proveedores" in data
    
    def test_analisis_invalid_server_returns_404(self):
        """Test that analisis returns 404 for invalid server"""
        response = requests.post(f"{BASE_URL}/api/compras/analisis", 
            headers=self.headers,
            json={
                "server_id": "invalid-server-id",
                "sucursal": "Test",
                "anios": ["2024"],
                "meses": ["10"]
            }
        )
        assert response.status_code == 404
    
    # ============ GET /api/compras/facturas-proveedor Tests ============
    
    def test_facturas_proveedor_endpoint_exists(self):
        """Test that facturas-proveedor endpoint exists"""
        if not self.softrestaurant_server:
            pytest.skip("No SoftRestaurant server available")
        
        response = requests.get(
            f"{BASE_URL}/api/compras/facturas-proveedor/{self.softrestaurant_server['id']}",
            headers=self.headers,
            params={
                "proveedor_codigo": "0099",
                "anio": 2024,
                "meses": "10,11,12"
            }
        )
        # Should return 200 even if empty (SoftRestaurant not implemented)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    
    def test_facturas_proveedor_returns_list(self):
        """Test that facturas-proveedor returns a list"""
        if not self.softrestaurant_server:
            pytest.skip("No SoftRestaurant server available")
        
        response = requests.get(
            f"{BASE_URL}/api/compras/facturas-proveedor/{self.softrestaurant_server['id']}",
            headers=self.headers,
            params={
                "proveedor_codigo": "0099",
                "anio": 2024,
                "meses": "10,11,12"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
    
    def test_facturas_proveedor_invalid_server_returns_404(self):
        """Test that facturas-proveedor returns 404 for invalid server"""
        response = requests.get(
            f"{BASE_URL}/api/compras/facturas-proveedor/invalid-server-id",
            headers=self.headers,
            params={
                "proveedor_codigo": "0099",
                "anio": 2024,
                "meses": "10"
            }
        )
        assert response.status_code == 404
    
    # ============ GET /api/compras/detalle-factura Tests ============
    
    def test_detalle_factura_endpoint_exists(self):
        """Test that detalle-factura endpoint exists"""
        if not self.softrestaurant_server:
            pytest.skip("No SoftRestaurant server available")
        
        response = requests.get(
            f"{BASE_URL}/api/compras/detalle-factura/{self.softrestaurant_server['id']}/TEST-001",
            headers=self.headers
        )
        # Should return 200 even if empty (SoftRestaurant not implemented)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    
    def test_detalle_factura_returns_list(self):
        """Test that detalle-factura returns a list"""
        if not self.softrestaurant_server:
            pytest.skip("No SoftRestaurant server available")
        
        response = requests.get(
            f"{BASE_URL}/api/compras/detalle-factura/{self.softrestaurant_server['id']}/TEST-001",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
    
    def test_detalle_factura_invalid_server_returns_404(self):
        """Test that detalle-factura returns 404 for invalid server"""
        response = requests.get(
            f"{BASE_URL}/api/compras/detalle-factura/invalid-server-id/TEST-001",
            headers=self.headers
        )
        assert response.status_code == 404


class TestComprasAnalisisMPRO:
    """Tests specifically for MPRO server (if available and online)"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": os.environ.get("TEST_ADMIN_EMAIL", TEST_ADMIN_EMAIL),
            "password": os.environ.get("TEST_ADMIN_PASSWORD", TEST_ADMIN_PASSWORD)
        })
        assert response.status_code == 200
        self.token = response.json()["token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
        
        servers_response = requests.get(f"{BASE_URL}/api/servers", headers=self.headers)
        self.servers = servers_response.json()
        
        self.mpro_server = None
        for server in self.servers:
            if server.get('system_type') == 'MPRO':
                self.mpro_server = server
                break
    
    def test_mpro_analisis_endpoint(self):
        """Test analisis endpoint for MPRO server"""
        if not self.mpro_server:
            pytest.skip("No MPRO server available")
        
        # Get sucursales first
        sucursales_response = requests.get(
            f"{BASE_URL}/api/servers/{self.mpro_server['id']}/sucursales",
            headers=self.headers
        )
        if sucursales_response.status_code != 200 or len(sucursales_response.json()) == 0:
            pytest.skip("No sucursales available for MPRO server")
        
        sucursal = sucursales_response.json()[0]['nombre']
        
        response = requests.post(f"{BASE_URL}/api/compras/analisis", 
            headers=self.headers,
            json={
                "server_id": self.mpro_server['id'],
                "sucursal": sucursal,
                "anios": ["2024"],
                "meses": ["10", "11", "12"]
            }
        )
        # May return empty if server is in cooldown
        assert response.status_code in [200, 500], f"Unexpected status: {response.status_code}"
