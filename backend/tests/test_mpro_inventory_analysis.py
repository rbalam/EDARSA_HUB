"""
Test MPRO Inventory Analysis Report
====================================
Tests the corrected MPRO inventory analysis logic:
- INSUMOS (dept 0007) with presentations appear in report
- COMPRAS without presentation appear in report
- Presentations of INSUMOS do NOT appear in report
- Sales are calculated using Producto_Kit (recipes)
"""

import pytest
import requests
import os

# Import centralized test credentials
from conftest import TEST_ADMIN_EMAIL, TEST_ADMIN_PASSWORD

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test data for MPRO server
MPRO_SERVER_ID = "1b230a06-ffaf-4c70-bd27-b1be3579dea6"
TEST_SUCURSAL = "QUERETARO"
TEST_ALMACEN = "ALMACEN GENERAL"
TEST_FOLIO_INICIAL = "QR-0000900"
TEST_FOLIO_FINAL = "QR-0000939"
TEST_FECHA_INI = "2026-01-01"
TEST_FECHA_FIN = "2026-03-22"

# Specific products to verify
INSUMO_RON_BACARDI = "0000000185"  # Ron Bacardí Blanco - SHOULD appear
PRESENTACION_1 = "0000007586"  # Presentation of Ron Bacardí - should NOT appear
PRESENTACION_2 = "0000009049"  # Presentation of Ron Bacardí - should NOT appear


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token"""
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={
            "email": os.environ.get("TEST_ADMIN_EMAIL", TEST_ADMIN_EMAIL),
            "password": os.environ.get("TEST_ADMIN_PASSWORD", TEST_ADMIN_PASSWORD)
        }
    )
    assert response.status_code == 200, f"Login failed: {response.text}"
    return response.json()["token"]


@pytest.fixture(scope="module")
def auth_headers(auth_token):
    """Get headers with auth token"""
    return {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}


class TestMPROServerAccess:
    """Test MPRO server access and configuration"""
    
    def test_mpro_server_exists(self, auth_headers):
        """Verify MPRO server is accessible"""
        response = requests.get(
            f"{BASE_URL}/api/servers/{MPRO_SERVER_ID}",
            headers=auth_headers
        )
        assert response.status_code == 200
        server = response.json()
        assert server["system_type"] == "MPRO"
        assert server["name"] == "ManagmentPro"
        print(f"✅ MPRO server found: {server['name']}")
    
    def test_mpro_sucursales_available(self, auth_headers):
        """Verify QUERETARO sucursal is available"""
        response = requests.get(
            f"{BASE_URL}/api/servers/{MPRO_SERVER_ID}/sucursales",
            headers=auth_headers
        )
        assert response.status_code == 200
        sucursales = response.json()
        queretaro = [s for s in sucursales if "QUERETARO" in s["nombre"]]
        assert len(queretaro) > 0, "QUERETARO sucursal not found"
        print(f"✅ Found {len(sucursales)} sucursales, including QUERETARO")
    
    def test_mpro_almacenes_available(self, auth_headers):
        """Verify ALMACEN GENERAL is available for QUERETARO"""
        response = requests.get(
            f"{BASE_URL}/api/servers/{MPRO_SERVER_ID}/almacenes",
            headers=auth_headers,
            params={"sucursal_id": "0021"}  # QUERETARO
        )
        assert response.status_code == 200
        almacenes = response.json()
        almacen_general = [a for a in almacenes if "ALMACEN GENERAL" in a["nombre"]]
        assert len(almacen_general) > 0, "ALMACEN GENERAL not found"
        print(f"✅ Found {len(almacenes)} almacenes, including ALMACEN GENERAL")


class TestMPROInventoryAnalysis:
    """Test MPRO inventory analysis report generation"""
    
    @pytest.fixture(scope="class")
    def report_data(self, auth_headers):
        """Generate inventory analysis report"""
        response = requests.post(
            f"{BASE_URL}/api/reports/inventory-analysis",
            headers=auth_headers,
            json={
                "server_id": MPRO_SERVER_ID,
                "sucursal": TEST_SUCURSAL,
                "almacen": TEST_ALMACEN,
                "fecha_ini": TEST_FECHA_INI,
                "fecha_fin": TEST_FECHA_FIN,
                "folio_inicial": TEST_FOLIO_INICIAL,
                "folio_final": TEST_FOLIO_FINAL
            },
            timeout=120
        )
        assert response.status_code == 200, f"Report generation failed: {response.text}"
        return response.json()
    
    def test_report_generates_successfully(self, report_data):
        """Verify report generates with data"""
        assert "data" in report_data
        assert "count" in report_data
        assert report_data["count"] > 0, "Report should have products"
        print(f"✅ Report generated with {report_data['count']} products")
    
    def test_report_has_correct_structure(self, report_data):
        """Verify report data has correct columns"""
        assert len(report_data["data"]) > 0
        first_product = report_data["data"][0]
        
        required_columns = [
            "Tipo", "Categoria", "Familia", "SubFamilia", "Codigo", "Producto",
            "Unidad", "Costo_Unitario", "Inv_Inicial_Cantidad", "Movimientos",
            "Ventas", "Inv_Teorico_Cantidad", "Inv_Final_Cantidad", 
            "Diferencia_Cantidad", "Diferencia_Costo"
        ]
        
        for col in required_columns:
            assert col in first_product, f"Missing column: {col}"
        print("✅ Report has all required columns")
    
    def test_insumo_ron_bacardi_appears_in_report(self, report_data):
        """CRITICAL: INSUMO 0000000185 (Ron Bacardí) MUST appear in report"""
        products = report_data["data"]
        ron_bacardi = [p for p in products if p["Codigo"] == INSUMO_RON_BACARDI]
        
        assert len(ron_bacardi) == 1, f"INSUMO {INSUMO_RON_BACARDI} (Ron Bacardí) should appear exactly once in report"
        
        product = ron_bacardi[0]
        assert product["Tipo"] == "INSUMO", "Ron Bacardí should be marked as INSUMO"
        assert "Ron Bacardi" in product["Producto"] or "Ron Bacardí" in product["Producto"], "Product name should contain 'Ron Bacardi'"
        
        print(f"✅ INSUMO {INSUMO_RON_BACARDI} (Ron Bacardí) found in report")
        print(f"   - Tipo: {product['Tipo']}")
        print(f"   - Producto: {product['Producto']}")
        print(f"   - Ventas: {product['Ventas']}")
    
    def test_ron_bacardi_has_sales(self, report_data):
        """CRITICAL: Ron Bacardí should have sales calculated from Producto_Kit"""
        products = report_data["data"]
        ron_bacardi = [p for p in products if p["Codigo"] == INSUMO_RON_BACARDI]
        
        assert len(ron_bacardi) == 1
        product = ron_bacardi[0]
        
        # Ron Bacardí is a popular product, should have sales
        assert product["Ventas"] > 0, f"Ron Bacardí should have sales (got {product['Ventas']})"
        print(f"✅ Ron Bacardí has {product['Ventas']} units in sales (calculated from Producto_Kit)")
    
    def test_presentation_7586_not_in_report(self, report_data):
        """CRITICAL: Presentation 0000007586 should NOT appear in report"""
        products = report_data["data"]
        presentation = [p for p in products if p["Codigo"] == PRESENTACION_1]
        
        assert len(presentation) == 0, f"Presentation {PRESENTACION_1} should NOT appear in report (it's a presentation of an INSUMO)"
        print(f"✅ Presentation {PRESENTACION_1} correctly excluded from report")
    
    def test_presentation_9049_not_in_report(self, report_data):
        """CRITICAL: Presentation 0000009049 should NOT appear in report"""
        products = report_data["data"]
        presentation = [p for p in products if p["Codigo"] == PRESENTACION_2]
        
        assert len(presentation) == 0, f"Presentation {PRESENTACION_2} should NOT appear in report (it's a presentation of an INSUMO)"
        print(f"✅ Presentation {PRESENTACION_2} correctly excluded from report")
    
    def test_report_has_insumos_and_compras(self, report_data):
        """Verify report contains both INSUMO and COMPRA type products"""
        products = report_data["data"]
        
        insumos = [p for p in products if p["Tipo"] == "INSUMO"]
        compras = [p for p in products if p["Tipo"] == "COMPRA"]
        
        assert len(insumos) > 0, "Report should have INSUMO products"
        assert len(compras) > 0, "Report should have COMPRA products"
        
        print(f"✅ Report has {len(insumos)} INSUMOS and {len(compras)} COMPRAS")
    
    def test_no_capture_errors_for_valid_data(self, report_data):
        """Verify errores_captura is returned (may be empty)"""
        assert "errores_captura" in report_data
        errores = report_data.get("errores_captura", [])
        print(f"✅ Report returned {len(errores)} capture errors")


class TestSoftRestaurantNoRegression:
    """Verify SoftRestaurant report still works (no regression)"""
    
    SOFTRESTAURANT_SERVER_ID = "a5ff0e25-f029-43db-b634-d4ac814c904f"
    
    def test_softrestaurant_server_exists(self, auth_headers):
        """Verify SoftRestaurant server is accessible"""
        response = requests.get(
            f"{BASE_URL}/api/servers/{self.SOFTRESTAURANT_SERVER_ID}",
            headers=auth_headers
        )
        assert response.status_code == 200
        server = response.json()
        assert server["system_type"] == "SoftRestaurant"
        print(f"✅ SoftRestaurant server found: {server['name']}")
    
    def test_softrestaurant_almacenes_available(self, auth_headers):
        """Verify SoftRestaurant almacenes are available"""
        response = requests.get(
            f"{BASE_URL}/api/servers/{self.SOFTRESTAURANT_SERVER_ID}/almacenes-softrestaurant",
            headers=auth_headers
        )
        assert response.status_code == 200
        almacenes = response.json()
        assert len(almacenes) > 0, "SoftRestaurant should have almacenes"
        print(f"✅ SoftRestaurant has {len(almacenes)} almacenes")
    
    def test_softrestaurant_inventarios_available(self, auth_headers):
        """Verify SoftRestaurant inventarios are available"""
        response = requests.get(
            f"{BASE_URL}/api/servers/{self.SOFTRESTAURANT_SERVER_ID}/inventarios",
            headers=auth_headers,
            params={"almacen_id": "001"}  # 001 BODEGA
        )
        assert response.status_code == 200
        inventarios = response.json()
        assert len(inventarios) > 0, "SoftRestaurant should have inventarios"
        print(f"✅ SoftRestaurant has {len(inventarios)} inventarios")
    
    def test_softrestaurant_report_generates(self, auth_headers):
        """Verify SoftRestaurant inventory analysis still works"""
        response = requests.post(
            f"{BASE_URL}/api/reports/inventory-analysis",
            headers=auth_headers,
            json={
                "server_id": self.SOFTRESTAURANT_SERVER_ID,
                "sucursal": "SoftRestaurant",
                "almacen": "001 BODEGA",
                "fecha_ini": "2025-01-01 00:00:01",
                "fecha_fin": "2025-12-31 23:59:59",
                "folio_inicial": "141",
                "folio_final": "149"
            },
            timeout=120
        )
        assert response.status_code == 200, f"SoftRestaurant report failed: {response.text}"
        data = response.json()
        assert data["count"] > 0, "SoftRestaurant report should have products"
        print(f"✅ SoftRestaurant report generated with {data['count']} products")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
