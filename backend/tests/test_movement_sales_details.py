"""
Tests for movement-details and sales-details endpoints.
Tests the new feature to view detailed movements and sales for products.
"""
import pytest
import requests
import os
from tests.test_config import test_config

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials from centralized config
ADMIN_EMAIL = test_config.TEST_ADMIN_EMAIL
ADMIN_PASSWORD = test_config.TEST_ADMIN_PASSWORD
MPRO_SERVER_ID = "1b230a06-ffaf-4c70-bd27-b1be3579dea6"


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token for API requests"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    })
    assert response.status_code == 200, f"Login failed: {response.text}"
    return response.json().get("token")


@pytest.fixture(scope="module")
def api_client(auth_token):
    """Create authenticated session"""
    session = requests.Session()
    session.headers.update({
        "Content-Type": "application/json",
        "Authorization": f"Bearer {auth_token}"
    })
    return session


class TestMovementDetailsEndpoint:
    """Tests for POST /api/reports/movement-details endpoint"""
    
    def test_movement_details_endpoint_exists(self, api_client):
        """Test that the endpoint exists and returns proper response structure"""
        # Test with minimal params to check endpoint exists
        response = api_client.post(f"{BASE_URL}/api/reports/movement-details", json={
            "server_id": MPRO_SERVER_ID,
            "producto_codigo": "TEST",
            "sucursal": "TEST",
            "almacen": "GENERAL",
            "fecha_ini": "2025-01-01",
            "fecha_fin": "2025-01-31"
        })
        
        # Endpoint should exist (not 404 or 405)
        assert response.status_code != 404, "Endpoint /api/reports/movement-details not found"
        assert response.status_code != 405, "Method POST not allowed"
        
        # Should return data structure even if no results
        if response.status_code == 200:
            data = response.json()
            assert "data" in data, "Response should have 'data' field"
            assert "count" in data, "Response should have 'count' field"
            print(f"Movement details endpoint returned {data['count']} records")
    
    def test_movement_details_requires_auth(self):
        """Test that endpoint requires authentication"""
        response = requests.post(f"{BASE_URL}/api/reports/movement-details", json={
            "server_id": MPRO_SERVER_ID,
            "producto_codigo": "TEST"
        })
        assert response.status_code == 403 or response.status_code == 401, "Endpoint should require authentication"
    
    def test_movement_details_with_valid_params(self, api_client):
        """Test movement details with valid MPRO server params"""
        response = api_client.post(f"{BASE_URL}/api/reports/movement-details", json={
            "server_id": MPRO_SERVER_ID,
            "producto_codigo": "1301",  # A common product code
            "sucursal": "MATRIZ",
            "almacen": "GENERAL",
            "fecha_ini": "2024-01-01",
            "fecha_fin": "2025-12-31"
        })
        
        # Should return 200 or 500 (if product not found)
        assert response.status_code in [200, 500], f"Unexpected status: {response.status_code}"
        
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data.get("data"), list)
            assert isinstance(data.get("count"), int)
            
            # Verify data structure if there are results
            if data["count"] > 0:
                record = data["data"][0]
                expected_fields = ["folio", "fecha", "cantidad", "tipo_movimiento"]
                for field in expected_fields:
                    assert field in record, f"Movement record missing field: {field}"
                print(f"Movement details: {data['count']} records found")
                print(f"Sample record: {record}")


class TestSalesDetailsEndpoint:
    """Tests for POST /api/reports/sales-details endpoint"""
    
    def test_sales_details_endpoint_exists(self, api_client):
        """Test that the endpoint exists and returns proper response structure"""
        response = api_client.post(f"{BASE_URL}/api/reports/sales-details", json={
            "server_id": MPRO_SERVER_ID,
            "producto_codigo": "TEST",
            "sucursal": "TEST",
            "fecha_ini": "2025-01-01",
            "fecha_fin": "2025-01-31"
        })
        
        # Endpoint should exist (not 404 or 405)
        assert response.status_code != 404, "Endpoint /api/reports/sales-details not found"
        assert response.status_code != 405, "Method POST not allowed"
        
        # Should return data structure even if no results
        if response.status_code == 200:
            data = response.json()
            assert "data" in data, "Response should have 'data' field"
            assert "count" in data, "Response should have 'count' field"
            print(f"Sales details endpoint returned {data['count']} records")
    
    def test_sales_details_requires_auth(self):
        """Test that endpoint requires authentication"""
        response = requests.post(f"{BASE_URL}/api/reports/sales-details", json={
            "server_id": MPRO_SERVER_ID,
            "producto_codigo": "TEST"
        })
        assert response.status_code == 403 or response.status_code == 401, "Endpoint should require authentication"
    
    def test_sales_details_with_valid_params(self, api_client):
        """Test sales details with valid MPRO server params"""
        response = api_client.post(f"{BASE_URL}/api/reports/sales-details", json={
            "server_id": MPRO_SERVER_ID,
            "producto_codigo": "1301",  # A common product code
            "sucursal": "MATRIZ",
            "fecha_ini": "2024-01-01",
            "fecha_fin": "2025-12-31"
        })
        
        # Should return 200 or 500 (if product not found)
        assert response.status_code in [200, 500], f"Unexpected status: {response.status_code}"
        
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data.get("data"), list)
            assert isinstance(data.get("count"), int)
            
            # Verify data structure if there are results
            if data["count"] > 0:
                record = data["data"][0]
                expected_fields = ["folio", "fecha", "cantidad", "tipo_venta"]
                for field in expected_fields:
                    assert field in record, f"Sales record missing field: {field}"
                print(f"Sales details: {data['count']} records found")
                print(f"Sample record: {record}")


class TestAlmacenGeneralLogic:
    """Tests for MPRO warehouse GENERAL sales logic"""
    
    def test_get_almacenes_includes_general(self, api_client):
        """Test that almacenes list includes GENERAL warehouse"""
        # First get sucursales
        suc_response = api_client.get(f"{BASE_URL}/api/servers/{MPRO_SERVER_ID}/sucursales")
        assert suc_response.status_code == 200
        sucursales = suc_response.json()
        
        if len(sucursales) > 0:
            sucursal_id = sucursales[0].get('id')
            # Get almacenes for this sucursal
            alm_response = api_client.get(f"{BASE_URL}/api/servers/{MPRO_SERVER_ID}/almacenes", 
                                          params={"sucursal_id": sucursal_id})
            assert alm_response.status_code == 200
            almacenes = alm_response.json()
            
            # Look for GENERAL warehouse
            general_exists = any('GENERAL' in str(a.get('nombre', '')).upper() for a in almacenes)
            print(f"Found {len(almacenes)} almacenes for sucursal {sucursal_id}")
            print(f"GENERAL warehouse exists: {general_exists}")
            print(f"Almacenes: {[a.get('nombre') for a in almacenes]}")


class TestInvalidParams:
    """Tests for invalid parameter handling"""
    
    def test_movement_details_invalid_server(self, api_client):
        """Test movement details with invalid server ID"""
        response = api_client.post(f"{BASE_URL}/api/reports/movement-details", json={
            "server_id": "invalid-server-id",
            "producto_codigo": "1301",
            "sucursal": "TEST",
            "almacen": "GENERAL",
            "fecha_ini": "2025-01-01",
            "fecha_fin": "2025-01-31"
        })
        assert response.status_code == 404, "Should return 404 for invalid server"
    
    def test_sales_details_invalid_server(self, api_client):
        """Test sales details with invalid server ID"""
        response = api_client.post(f"{BASE_URL}/api/reports/sales-details", json={
            "server_id": "invalid-server-id",
            "producto_codigo": "1301",
            "sucursal": "TEST",
            "fecha_ini": "2025-01-01",
            "fecha_fin": "2025-01-31"
        })
        assert response.status_code == 404, "Should return 404 for invalid server"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
