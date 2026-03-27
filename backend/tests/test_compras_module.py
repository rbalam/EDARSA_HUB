"""
Test module for Autorización de Compras (Purchase Authorization) - Phase 1
Tests the /api/compras/calculo-pedido endpoint and related functionality

Features tested:
- Login and authentication
- Server selection (MPRO)
- Sucursales loading
- Almacenes loading
- Calculo-pedido endpoint with correct data structure
- KPIs calculation (total products, products to order, total cost, low stock, no physical inventory)
- Physical inventory info (folio and date)
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials from review request
ADMIN_EMAIL = "admin@inventario.com"
ADMIN_PASSWORD = "admin123"
MPRO_SERVER_ID = "1b230a06-ffaf-4c70-bd27-b1be3579dea6"
TEST_SUCURSAL = "ORIGEN"
TEST_ALMACEN = "BODEGA"


class TestComprasModuleAuth:
    """Authentication tests for Compras module"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        return response.json().get("token")
    
    def test_login_success(self):
        """Test admin login returns 200 with token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert "user" in data
        assert data["user"]["email"] == ADMIN_EMAIL
        print(f"✓ Login successful for {ADMIN_EMAIL}")


class TestComprasServerSelection:
    """Tests for server selection in Compras module"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        return response.json().get("token")
    
    def test_get_servers_returns_mpro(self, auth_token):
        """Test that servers list includes MPRO server"""
        response = requests.get(
            f"{BASE_URL}/api/servers",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        servers = response.json()
        assert len(servers) > 0, "No servers found"
        
        # Find MPRO server
        mpro_server = next((s for s in servers if s['id'] == MPRO_SERVER_ID), None)
        assert mpro_server is not None, f"MPRO server {MPRO_SERVER_ID} not found"
        assert mpro_server['system_type'] == 'MPRO'
        print(f"✓ MPRO server found: {mpro_server['name']}")
    
    def test_get_sucursales_for_mpro(self, auth_token):
        """Test loading sucursales for MPRO server"""
        response = requests.get(
            f"{BASE_URL}/api/servers/{MPRO_SERVER_ID}/sucursales",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        sucursales = response.json()
        assert len(sucursales) > 0, "No sucursales found"
        
        # Check structure
        first_suc = sucursales[0]
        assert 'id' in first_suc or 'nombre' in first_suc
        print(f"✓ Found {len(sucursales)} sucursales")
        
        # Check if ORIGEN exists
        origen = next((s for s in sucursales if 'ORIGEN' in str(s.get('nombre', '')).upper()), None)
        if origen:
            print(f"✓ ORIGEN sucursal found")
        else:
            print(f"⚠ ORIGEN not found, available: {[s.get('nombre') for s in sucursales[:5]]}")
    
    def test_get_almacenes_for_sucursal(self, auth_token):
        """Test loading almacenes for a sucursal"""
        # First get sucursales to find ORIGEN
        suc_response = requests.get(
            f"{BASE_URL}/api/servers/{MPRO_SERVER_ID}/sucursales",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        sucursales = suc_response.json()
        
        # Find ORIGEN or use first sucursal
        origen = next((s for s in sucursales if 'ORIGEN' in str(s.get('nombre', '')).upper()), None)
        sucursal_nombre = origen['nombre'] if origen else sucursales[0]['nombre']
        
        response = requests.get(
            f"{BASE_URL}/api/servers/{MPRO_SERVER_ID}/almacenes?sucursal={sucursal_nombre}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        almacenes = response.json()
        assert len(almacenes) > 0, f"No almacenes found for sucursal {sucursal_nombre}"
        
        # Check structure
        first_alm = almacenes[0]
        assert 'id' in first_alm or 'nombre' in first_alm
        print(f"✓ Found {len(almacenes)} almacenes for {sucursal_nombre}")
        
        # Check if BODEGA exists
        bodega = next((a for a in almacenes if 'BODEGA' in str(a.get('nombre', '')).upper()), None)
        if bodega:
            print(f"✓ BODEGA almacen found")
        else:
            print(f"⚠ BODEGA not found, available: {[a.get('nombre') for a in almacenes[:5]]}")


class TestCalculoPedidoEndpoint:
    """Tests for /api/compras/calculo-pedido endpoint"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        return response.json().get("token")
    
    @pytest.fixture(scope="class")
    def valid_sucursal_almacen(self, auth_token):
        """Get valid sucursal and almacen names from the server"""
        # Get sucursales
        suc_response = requests.get(
            f"{BASE_URL}/api/servers/{MPRO_SERVER_ID}/sucursales",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        sucursales = suc_response.json()
        
        # Find ORIGEN or use first
        origen = next((s for s in sucursales if 'ORIGEN' in str(s.get('nombre', '')).upper()), None)
        sucursal_nombre = origen['nombre'] if origen else sucursales[0]['nombre']
        
        # Get almacenes
        alm_response = requests.get(
            f"{BASE_URL}/api/servers/{MPRO_SERVER_ID}/almacenes?sucursal={sucursal_nombre}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        almacenes = alm_response.json()
        
        # Find BODEGA or use first
        bodega = next((a for a in almacenes if 'BODEGA' in str(a.get('nombre', '')).upper()), None)
        almacen_nombre = bodega['nombre'] if bodega else almacenes[0]['nombre']
        
        return {"sucursal": sucursal_nombre, "almacen": almacen_nombre}
    
    def test_calculo_pedido_returns_200(self, auth_token, valid_sucursal_almacen):
        """Test that calculo-pedido endpoint returns 200 with valid params"""
        response = requests.post(
            f"{BASE_URL}/api/compras/calculo-pedido",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "server_id": MPRO_SERVER_ID,
                "sucursal": valid_sucursal_almacen["sucursal"],
                "almacen": valid_sucursal_almacen["almacen"],
                "fecha_calculo": "2025-01-15",
                "dias_historial_ventas": 30,
                "dias_inventario": 10
            }
        )
        assert response.status_code == 200, f"Calculo pedido failed: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "data" in data, "Response missing 'data' field"
        assert "count" in data, "Response missing 'count' field"
        assert "tiene_inventario_fisico" in data, "Response missing 'tiene_inventario_fisico' field"
        assert "parametros" in data, "Response missing 'parametros' field"
        
        print(f"✓ Calculo pedido returned {data['count']} products")
        print(f"✓ Tiene inventario físico: {data['tiene_inventario_fisico']}")
    
    def test_calculo_pedido_data_structure(self, auth_token, valid_sucursal_almacen):
        """Test that each product in response has required columns"""
        response = requests.post(
            f"{BASE_URL}/api/compras/calculo-pedido",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "server_id": MPRO_SERVER_ID,
                "sucursal": valid_sucursal_almacen["sucursal"],
                "almacen": valid_sucursal_almacen["almacen"],
                "fecha_calculo": "2025-01-15",
                "dias_historial_ventas": 30,
                "dias_inventario": 10
            }
        )
        assert response.status_code == 200
        data = response.json()
        
        if data['count'] > 0:
            product = data['data'][0]
            
            # Required columns for the table
            required_columns = [
                'Codigo', 'Producto', 'Familia',
                'Inventario_Fisico', 'Compras_Periodo', 'Consumos_Periodo',
                'Inventario_Teorico', 'Promedio_Diario', 'Dias_Inventario',
                'Consumo_Esperado', 'Cantidad_Pedir', 'Costo_Pedido',
                'Sin_Inventario_Fisico'
            ]
            
            for col in required_columns:
                assert col in product, f"Missing column: {col}"
            
            print(f"✓ All required columns present in response")
            print(f"  Sample product: {product['Codigo']} - {product['Producto'][:30]}...")
        else:
            print("⚠ No products returned - cannot verify column structure")
    
    def test_calculo_pedido_inventory_info(self, auth_token, valid_sucursal_almacen):
        """Test that inventory info (folio and date) is returned"""
        response = requests.post(
            f"{BASE_URL}/api/compras/calculo-pedido",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "server_id": MPRO_SERVER_ID,
                "sucursal": valid_sucursal_almacen["sucursal"],
                "almacen": valid_sucursal_almacen["almacen"],
                "fecha_calculo": "2025-01-15",
                "dias_historial_ventas": 30,
                "dias_inventario": 10
            }
        )
        assert response.status_code == 200
        data = response.json()
        
        # Check inventory info fields
        assert "tiene_inventario_fisico" in data
        assert "folio_inventario_fisico" in data
        assert "fecha_inventario_fisico" in data
        assert "productos_sin_inventario" in data
        assert "es_bodega" in data
        
        if data['tiene_inventario_fisico']:
            print(f"✓ Inventario físico: Folio {data['folio_inventario_fisico']}, Fecha {data['fecha_inventario_fisico']}")
        else:
            print(f"⚠ No hay inventario físico capturado")
        
        print(f"✓ Productos sin inventario: {data['productos_sin_inventario']}")
        print(f"✓ Es bodega: {data['es_bodega']}")
    
    def test_calculo_pedido_kpi_calculation(self, auth_token, valid_sucursal_almacen):
        """Test that KPIs can be calculated from response data"""
        response = requests.post(
            f"{BASE_URL}/api/compras/calculo-pedido",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "server_id": MPRO_SERVER_ID,
                "sucursal": valid_sucursal_almacen["sucursal"],
                "almacen": valid_sucursal_almacen["almacen"],
                "fecha_calculo": "2025-01-15",
                "dias_historial_ventas": 30,
                "dias_inventario": 10
            }
        )
        assert response.status_code == 200
        data = response.json()
        products = data['data']
        
        # Calculate KPIs
        total_productos = len(products)
        productos_a_pedir = len([p for p in products if p['Cantidad_Pedir'] > 0])
        costo_total_pedido = sum(p['Costo_Pedido'] for p in products)
        productos_stock_bajo = len([p for p in products if p['Dias_Inventario'] < 3])
        productos_sin_inv_fisico = len([p for p in products if p['Sin_Inventario_Fisico']])
        
        print(f"✓ KPIs calculados:")
        print(f"  - Total productos: {total_productos}")
        print(f"  - Productos a pedir: {productos_a_pedir}")
        print(f"  - Costo total pedido: ${costo_total_pedido:,.2f}")
        print(f"  - Stock bajo (<3 días): {productos_stock_bajo}")
        print(f"  - Sin inv. físico: {productos_sin_inv_fisico}")
        
        # Verify KPIs are reasonable
        assert total_productos >= 0
        assert productos_a_pedir >= 0
        assert costo_total_pedido >= 0
    
    def test_calculo_pedido_invalid_server(self, auth_token):
        """Test that invalid server returns 404"""
        response = requests.post(
            f"{BASE_URL}/api/compras/calculo-pedido",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "server_id": "invalid-server-id",
                "sucursal": "TEST",
                "almacen": "TEST",
                "fecha_calculo": "2025-01-15",
                "dias_historial_ventas": 30,
                "dias_inventario": 10
            }
        )
        assert response.status_code == 404
        print("✓ Invalid server returns 404")
    
    def test_calculo_pedido_without_auth(self):
        """Test that endpoint requires authentication"""
        response = requests.post(
            f"{BASE_URL}/api/compras/calculo-pedido",
            json={
                "server_id": MPRO_SERVER_ID,
                "sucursal": "TEST",
                "almacen": "TEST",
                "fecha_calculo": "2025-01-15",
                "dias_historial_ventas": 30,
                "dias_inventario": 10
            }
        )
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("✓ Endpoint requires authentication")


class TestComprasParametros:
    """Tests for compras parameters endpoints"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        return response.json().get("token")
    
    def test_get_parametros_returns_defaults(self, auth_token):
        """Test that parametros endpoint returns default values"""
        response = requests.get(
            f"{BASE_URL}/api/compras/parametros/{MPRO_SERVER_ID}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Check default fields
        assert "server_id" in data
        assert "dias_inventario" in data
        print(f"✓ Parametros returned: dias_inventario={data.get('dias_inventario')}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
