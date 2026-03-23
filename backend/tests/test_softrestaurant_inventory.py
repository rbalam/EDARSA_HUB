"""
Test suite for SoftRestaurant inventory analysis - verifying double prefix fix
Tests the inventory analysis endpoint for LA ESTELAR server with almacen 001 BODEGA
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "admin@inventario.com"
TEST_PASSWORD = "admin123"

# SoftRestaurant server details
SOFTRESTAURANT_SERVER_ID = "a5ff0e25-f029-43db-b634-d4ac814c904f"
TEST_ALMACEN = "001 BODEGA"
TEST_FOLIO_INICIAL = "141"
TEST_FOLIO_FINAL = "149"

@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })
    assert response.status_code == 200, f"Login failed: {response.text}"
    return response.json().get("token")

@pytest.fixture(scope="module")
def auth_headers(auth_token):
    """Get headers with auth token"""
    return {
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json"
    }

class TestSoftRestaurantInventoryAnalysis:
    """Tests for SoftRestaurant inventory analysis - double prefix fix verification"""
    
    def test_login_success(self):
        """Test login works"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert "user" in data
        print(f"✓ Login successful for {TEST_EMAIL}")
    
    def test_server_exists(self, auth_headers):
        """Test that LA ESTELAR server exists"""
        response = requests.get(
            f"{BASE_URL}/api/servers/{SOFTRESTAURANT_SERVER_ID}",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Server not found: {response.text}"
        data = response.json()
        assert data.get("system_type") == "SoftRestaurant"
        print(f"✓ Server found: {data.get('name')} ({data.get('system_type')})")
    
    def test_almacenes_softrestaurant(self, auth_headers):
        """Test that almacenes endpoint returns data"""
        response = requests.get(
            f"{BASE_URL}/api/servers/{SOFTRESTAURANT_SERVER_ID}/almacenes-softrestaurant",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0, "No almacenes found"
        
        # Check for 001 BODEGA
        bodega = next((a for a in data if "001" in str(a.get("id", ""))), None)
        assert bodega is not None, "001 BODEGA not found in almacenes"
        print(f"✓ Found {len(data)} almacenes, including 001 BODEGA")
    
    def test_inventarios_list(self, auth_headers):
        """Test that inventarios endpoint returns data for almacen 001"""
        response = requests.get(
            f"{BASE_URL}/api/servers/{SOFTRESTAURANT_SERVER_ID}/inventarios",
            headers=auth_headers,
            params={"sucursal_id": "default", "almacen_id": "001"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0, "No inventarios found"
        
        # Check for folios 141 and 149
        folios = [str(inv.get("folio")) for inv in data]
        assert TEST_FOLIO_INICIAL in folios, f"Folio {TEST_FOLIO_INICIAL} not found"
        assert TEST_FOLIO_FINAL in folios, f"Folio {TEST_FOLIO_FINAL} not found"
        print(f"✓ Found {len(data)} inventarios, including folios {TEST_FOLIO_INICIAL} and {TEST_FOLIO_FINAL}")
    
    def test_inventory_analysis_generates_report(self, auth_headers):
        """Test that inventory analysis generates a report without errors"""
        # Get inventario dates first
        inv_response = requests.get(
            f"{BASE_URL}/api/servers/{SOFTRESTAURANT_SERVER_ID}/inventarios",
            headers=auth_headers,
            params={"sucursal_id": "default", "almacen_id": "001"}
        )
        inventarios = inv_response.json()
        
        # Find folios 141 and 149
        inv_inicial = next((inv for inv in inventarios if str(inv.get("folio")) == TEST_FOLIO_INICIAL), None)
        inv_final = next((inv for inv in inventarios if str(inv.get("folio")) == TEST_FOLIO_FINAL), None)
        
        assert inv_inicial is not None, f"Inventario inicial {TEST_FOLIO_INICIAL} not found"
        assert inv_final is not None, f"Inventario final {TEST_FOLIO_FINAL} not found"
        
        # Calculate dates (add 1 second to inicial, subtract 1 from final)
        fecha_ini = inv_inicial.get("fecha", "2026-03-01 11:03:41")
        fecha_fin = inv_final.get("fecha", "2026-03-09 13:17:41")
        
        print(f"Using dates: {fecha_ini} to {fecha_fin}")
        
        # Generate report
        response = requests.post(
            f"{BASE_URL}/api/reports/inventory-analysis",
            headers=auth_headers,
            json={
                "server_id": SOFTRESTAURANT_SERVER_ID,
                "sucursal": "SoftRestaurant",
                "almacen": TEST_ALMACEN,
                "fecha_ini": fecha_ini,
                "fecha_fin": fecha_fin,
                "folio_inicial": TEST_FOLIO_INICIAL,
                "folio_final": TEST_FOLIO_FINAL,
                "categorias": [],
                "familias": [],
                "subfamilias": []
            }
        )
        
        assert response.status_code == 200, f"Report generation failed: {response.text}"
        data = response.json()
        assert "data" in data
        assert "count" in data
        assert data["count"] > 0, "Report returned no data"
        print(f"✓ Report generated successfully with {data['count']} products")
        
        return data["data"]
    
    def test_product_codes_no_double_prefix(self, auth_headers):
        """
        CRITICAL TEST: Verify that product codes don't have double prefix
        Example: B130009 should NOT appear as BB130009
        """
        # Get inventario dates first
        inv_response = requests.get(
            f"{BASE_URL}/api/servers/{SOFTRESTAURANT_SERVER_ID}/inventarios",
            headers=auth_headers,
            params={"sucursal_id": "default", "almacen_id": "001"}
        )
        inventarios = inv_response.json()
        
        inv_inicial = next((inv for inv in inventarios if str(inv.get("folio")) == TEST_FOLIO_INICIAL), None)
        inv_final = next((inv for inv in inventarios if str(inv.get("folio")) == TEST_FOLIO_FINAL), None)
        
        fecha_ini = inv_inicial.get("fecha", "2026-03-01 11:03:41")
        fecha_fin = inv_final.get("fecha", "2026-03-09 13:17:41")
        
        # Generate report
        response = requests.post(
            f"{BASE_URL}/api/reports/inventory-analysis",
            headers=auth_headers,
            json={
                "server_id": SOFTRESTAURANT_SERVER_ID,
                "sucursal": "SoftRestaurant",
                "almacen": TEST_ALMACEN,
                "fecha_ini": fecha_ini,
                "fecha_fin": fecha_fin,
                "folio_inicial": TEST_FOLIO_INICIAL,
                "folio_final": TEST_FOLIO_FINAL,
                "categorias": [],
                "familias": [],
                "subfamilias": []
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        products = data.get("data", [])
        
        # Check for double prefix patterns
        double_prefix_products = []
        for product in products:
            codigo = product.get("Codigo", "")
            # Check for patterns like AA, BB, CC at the start (double prefix)
            if len(codigo) >= 2 and codigo[0].isalpha() and codigo[1].isalpha() and codigo[0] == codigo[1]:
                double_prefix_products.append(codigo)
        
        # Specifically check for B130009 (RON BACARDI BLANCO 700 ML)
        b130009_product = next((p for p in products if "130009" in str(p.get("Codigo", ""))), None)
        
        if b130009_product:
            codigo = b130009_product.get("Codigo", "")
            print(f"Found product with 130009: {codigo} - {b130009_product.get('Producto', '')}")
            assert codigo == "B130009", f"Expected B130009 but got {codigo} (double prefix bug!)"
            print(f"✓ Product B130009 has correct code (no double prefix)")
        
        # Assert no double prefix products found
        assert len(double_prefix_products) == 0, f"Found products with double prefix: {double_prefix_products[:10]}"
        print(f"✓ No double prefix products found in {len(products)} products")
    
    def test_products_have_description_and_category(self, auth_headers):
        """Test that products have description, category, and family"""
        inv_response = requests.get(
            f"{BASE_URL}/api/servers/{SOFTRESTAURANT_SERVER_ID}/inventarios",
            headers=auth_headers,
            params={"sucursal_id": "default", "almacen_id": "001"}
        )
        inventarios = inv_response.json()
        
        inv_inicial = next((inv for inv in inventarios if str(inv.get("folio")) == TEST_FOLIO_INICIAL), None)
        inv_final = next((inv for inv in inventarios if str(inv.get("folio")) == TEST_FOLIO_FINAL), None)
        
        fecha_ini = inv_inicial.get("fecha", "2026-03-01 11:03:41")
        fecha_fin = inv_final.get("fecha", "2026-03-09 13:17:41")
        
        response = requests.post(
            f"{BASE_URL}/api/reports/inventory-analysis",
            headers=auth_headers,
            json={
                "server_id": SOFTRESTAURANT_SERVER_ID,
                "sucursal": "SoftRestaurant",
                "almacen": TEST_ALMACEN,
                "fecha_ini": fecha_ini,
                "fecha_fin": fecha_fin,
                "folio_inicial": TEST_FOLIO_INICIAL,
                "folio_final": TEST_FOLIO_FINAL,
                "categorias": [],
                "familias": [],
                "subfamilias": []
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        products = data.get("data", [])
        
        # Check first 10 products for required fields
        products_with_missing_fields = []
        for product in products[:50]:
            missing = []
            if not product.get("Producto"):
                missing.append("Producto")
            if not product.get("Categoria"):
                missing.append("Categoria")
            if not product.get("Familia"):
                missing.append("Familia")
            if missing:
                products_with_missing_fields.append({
                    "codigo": product.get("Codigo"),
                    "missing": missing
                })
        
        # Allow some products to have missing fields (edge cases)
        missing_ratio = len(products_with_missing_fields) / min(50, len(products))
        assert missing_ratio < 0.2, f"Too many products with missing fields: {products_with_missing_fields[:5]}"
        print(f"✓ Products have description, category, and family (missing ratio: {missing_ratio:.1%})")
    
    def test_products_with_movements_have_values(self, auth_headers):
        """Test that products with movements != 0 show correct values"""
        inv_response = requests.get(
            f"{BASE_URL}/api/servers/{SOFTRESTAURANT_SERVER_ID}/inventarios",
            headers=auth_headers,
            params={"sucursal_id": "default", "almacen_id": "001"}
        )
        inventarios = inv_response.json()
        
        inv_inicial = next((inv for inv in inventarios if str(inv.get("folio")) == TEST_FOLIO_INICIAL), None)
        inv_final = next((inv for inv in inventarios if str(inv.get("folio")) == TEST_FOLIO_FINAL), None)
        
        fecha_ini = inv_inicial.get("fecha", "2026-03-01 11:03:41")
        fecha_fin = inv_final.get("fecha", "2026-03-09 13:17:41")
        
        response = requests.post(
            f"{BASE_URL}/api/reports/inventory-analysis",
            headers=auth_headers,
            json={
                "server_id": SOFTRESTAURANT_SERVER_ID,
                "sucursal": "SoftRestaurant",
                "almacen": TEST_ALMACEN,
                "fecha_ini": fecha_ini,
                "fecha_fin": fecha_fin,
                "folio_inicial": TEST_FOLIO_INICIAL,
                "folio_final": TEST_FOLIO_FINAL,
                "categorias": [],
                "familias": [],
                "subfamilias": []
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        products = data.get("data", [])
        
        # Find products with movements != 0
        products_with_movements = [p for p in products if p.get("Movimientos", 0) != 0]
        
        print(f"Found {len(products_with_movements)} products with movements != 0")
        
        # Check B130009 specifically (should have movements = -10)
        b130009 = next((p for p in products if "130009" in str(p.get("Codigo", ""))), None)
        if b130009:
            movimientos = b130009.get("Movimientos", 0)
            print(f"B130009 movements: {movimientos}")
            assert movimientos != 0, f"B130009 should have movements but got {movimientos}"
            print(f"✓ B130009 has movements: {movimientos}")
        
        # Verify at least some products have movements
        assert len(products_with_movements) > 0, "No products with movements found"
        print(f"✓ Found {len(products_with_movements)} products with movements")


class TestMovementDetailsModal:
    """Tests for movement details modal functionality"""
    
    def test_movement_details_endpoint(self, auth_headers):
        """Test that movement details endpoint works"""
        # First get a product with movements
        inv_response = requests.get(
            f"{BASE_URL}/api/servers/{SOFTRESTAURANT_SERVER_ID}/inventarios",
            headers=auth_headers,
            params={"sucursal_id": "default", "almacen_id": "001"}
        )
        inventarios = inv_response.json()
        
        inv_inicial = next((inv for inv in inventarios if str(inv.get("folio")) == TEST_FOLIO_INICIAL), None)
        inv_final = next((inv for inv in inventarios if str(inv.get("folio")) == TEST_FOLIO_FINAL), None)
        
        fecha_ini = inv_inicial.get("fecha", "2026-03-01 11:03:41")
        fecha_fin = inv_final.get("fecha", "2026-03-09 13:17:41")
        
        # Get report to find a product with movements
        report_response = requests.post(
            f"{BASE_URL}/api/reports/inventory-analysis",
            headers=auth_headers,
            json={
                "server_id": SOFTRESTAURANT_SERVER_ID,
                "sucursal": "SoftRestaurant",
                "almacen": TEST_ALMACEN,
                "fecha_ini": fecha_ini,
                "fecha_fin": fecha_fin,
                "folio_inicial": TEST_FOLIO_INICIAL,
                "folio_final": TEST_FOLIO_FINAL,
                "categorias": [],
                "familias": [],
                "subfamilias": []
            }
        )
        
        products = report_response.json().get("data", [])
        product_with_movements = next((p for p in products if p.get("Movimientos", 0) != 0), None)
        
        if product_with_movements:
            codigo = product_with_movements.get("Codigo")
            print(f"Testing movement details for product: {codigo}")
            
            # Call movement details endpoint
            response = requests.post(
                f"{BASE_URL}/api/reports/movement-details",
                headers=auth_headers,
                json={
                    "server_id": SOFTRESTAURANT_SERVER_ID,
                    "producto_codigo": codigo,
                    "sucursal": "SoftRestaurant",
                    "almacen": TEST_ALMACEN,
                    "fecha_ini": fecha_ini,
                    "fecha_fin": fecha_fin
                }
            )
            
            assert response.status_code == 200, f"Movement details failed: {response.text}"
            data = response.json()
            assert "data" in data
            assert "count" in data
            print(f"✓ Movement details returned {data['count']} records for {codigo}")
        else:
            pytest.skip("No products with movements found to test")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
