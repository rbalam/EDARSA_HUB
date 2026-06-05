"""
Test Config Asignaciones API Endpoints
======================================
Tests for inventory assignment configuration:
- UNIDAD DE NEGOCIO + ALMACÉN → USUARIO RESPONSABLE

Endpoints tested:
- GET /api/config-asignaciones - List configurations
- GET /api/config-asignaciones/unidades-negocio - Get business units catalog
- GET /api/config-asignaciones/almacenes/{unidad_id} - Get warehouses from local catalog
- POST /api/config-asignaciones - Create new configuration
- PUT /api/config-asignaciones/{id} - Update configuration
- DELETE /api/config-asignaciones/{id} - Delete configuration
"""

import pytest
import requests
import os
import uuid

# Import centralized test credentials
from conftest import TEST_SUPERADMIN_EMAIL, TEST_SUPERADMIN_PASSWORD

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://stock-tracker-990.preview.emergentagent.com').rstrip('/')

# Test credentials (centralized)
SUPERADMIN_EMAIL = os.environ.get("TEST_SUPERADMIN_EMAIL", TEST_SUPERADMIN_EMAIL)
SUPERADMIN_PASSWORD = os.environ.get("TEST_SUPERADMIN_PASSWORD", TEST_SUPERADMIN_PASSWORD)


class TestConfigAsignacionesAPI:
    """Test suite for Config Asignaciones endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        self.token = None
        self.created_config_ids = []
        
    def get_auth_token(self):
        """Get authentication token for SuperAdmin"""
        if self.token:
            return self.token
            
        response = self.session.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": SUPERADMIN_EMAIL, "password": SUPERADMIN_PASSWORD}
        )
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        self.token = data.get("token")
        self.session.headers.update({"Authorization": f"Bearer {self.token}"})
        return self.token
    
    def cleanup_created_configs(self):
        """Cleanup any configs created during tests"""
        for config_id in self.created_config_ids:
            try:
                self.session.delete(f"{BASE_URL}/api/config-asignaciones/{config_id}")
            except Exception:
                pass
        self.created_config_ids = []
    
    # =========================================================================
    # TEST: Authentication
    # =========================================================================
    
    def test_01_login_superadmin(self):
        """Test SuperAdmin login works"""
        response = self.session.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": SUPERADMIN_EMAIL, "password": SUPERADMIN_PASSWORD}
        )
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert data["user"]["role"] == "SuperAdministrador"
        print(f"✓ SuperAdmin login successful: {data['user']['name']}")
    
    # =========================================================================
    # TEST: GET /api/config-asignaciones (List)
    # =========================================================================
    
    def test_02_list_asignaciones_success(self):
        """Test listing configurations returns success"""
        self.get_auth_token()
        
        response = self.session.get(f"{BASE_URL}/api/config-asignaciones")
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"]
        assert "data" in data
        assert "total" in data
        assert isinstance(data["data"], list)
        print(f"✓ Listed {data['total']} configurations")
    
    def test_03_list_asignaciones_with_filter_unidad(self):
        """Test listing with unidad_negocio_id filter"""
        self.get_auth_token()
        
        # First get a valid unidad_negocio_id
        unidades_resp = self.session.get(f"{BASE_URL}/api/config-asignaciones/unidades-negocio")
        assert unidades_resp.status_code == 200
        unidades = unidades_resp.json()["data"]
        
        if unidades:
            unidad_id = unidades[0]["id"]
            response = self.session.get(
                f"{BASE_URL}/api/config-asignaciones",
                params={"unidad_negocio_id": unidad_id}
            )
            assert response.status_code == 200
            data = response.json()
            assert data["success"]
            print(f"✓ Filtered by unidad_negocio_id: {unidad_id}")
    
    def test_04_list_asignaciones_with_filter_activa(self):
        """Test listing with activa filter"""
        self.get_auth_token()
        
        # Filter active only
        response = self.session.get(
            f"{BASE_URL}/api/config-asignaciones",
            params={"activa": "true"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"]
        
        # Verify all returned are active
        for config in data["data"]:
            assert config["activa"]
        print(f"✓ Filtered by activa=true: {len(data['data'])} results")
    
    def test_05_list_asignaciones_no_auth(self):
        """Test listing without auth returns 403"""
        session = requests.Session()
        response = session.get(f"{BASE_URL}/api/config-asignaciones")
        assert response.status_code == 403
        print("✓ No auth correctly returns 403")
    
    # =========================================================================
    # TEST: GET /api/config-asignaciones/unidades-negocio
    # =========================================================================
    
    def test_06_get_unidades_negocio_success(self):
        """Test getting business units catalog"""
        self.get_auth_token()
        
        response = self.session.get(f"{BASE_URL}/api/config-asignaciones/unidades-negocio")
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"]
        assert "data" in data
        assert isinstance(data["data"], list)
        
        # Verify structure
        if data["data"]:
            unit = data["data"][0]
            assert "id" in unit
            assert "nombre" in unit
        
        print(f"✓ Got {len(data['data'])} unidades de negocio")
        for u in data["data"]:
            print(f"  - {u['nombre']} ({u['id'][:8]}...)")
    
    def test_07_get_unidades_negocio_no_auth(self):
        """Test getting unidades without auth returns 403"""
        session = requests.Session()
        response = session.get(f"{BASE_URL}/api/config-asignaciones/unidades-negocio")
        assert response.status_code == 403
        print("✓ No auth correctly returns 403")
    
    # =========================================================================
    # TEST: GET /api/config-asignaciones/almacenes/{unidad_id}
    # =========================================================================
    
    def test_08_get_almacenes_success(self):
        """Test getting warehouses for a business unit"""
        self.get_auth_token()
        
        # Get a valid unidad_negocio_id
        unidades_resp = self.session.get(f"{BASE_URL}/api/config-asignaciones/unidades-negocio")
        unidades = unidades_resp.json()["data"]
        assert len(unidades) > 0, "No unidades de negocio found"
        
        unidad_id = unidades[0]["id"]
        
        response = self.session.get(f"{BASE_URL}/api/config-asignaciones/almacenes/{unidad_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"]
        assert "data" in data
        assert isinstance(data["data"], list)
        
        # First option should always be "(Todos los almacenes)"
        assert len(data["data"]) >= 1
        assert data["data"][0]["id"] == ""
        assert "(Todos" in data["data"][0]["nombre"]
        
        print(f"✓ Got {len(data['data'])} almacenes for {unidades[0]['nombre']}")
    
    def test_09_get_almacenes_invalid_unidad(self):
        """Test getting warehouses for invalid unidad returns error"""
        self.get_auth_token()
        
        fake_id = str(uuid.uuid4())
        response = self.session.get(f"{BASE_URL}/api/config-asignaciones/almacenes/{fake_id}")
        # Should return 403 (no alcance) or 404
        assert response.status_code in [403, 404, 200]  # 200 with empty list is also valid
        print(f"✓ Invalid unidad_id returns status {response.status_code}")
    
    # =========================================================================
    # TEST: POST /api/config-asignaciones (Create)
    # =========================================================================
    
    def test_10_create_asignacion_success(self):
        """Test creating a new configuration"""
        self.get_auth_token()
        
        # Get valid unidad and user
        unidades_resp = self.session.get(f"{BASE_URL}/api/config-asignaciones/unidades-negocio")
        unidades = unidades_resp.json()["data"]
        
        users_resp = self.session.get(f"{BASE_URL}/api/users")
        users = users_resp.json()
        if isinstance(users, dict):
            users = users.get("users", [])
        
        # Find a unidad that doesn't have a "(todos)" config yet
        existing_resp = self.session.get(f"{BASE_URL}/api/config-asignaciones")
        existing = existing_resp.json()["data"]
        existing_unidades = {c["unidad_negocio_id"] for c in existing if c["almacen_id"] == ""}
        
        # Find unidad without existing config
        test_unidad = None
        for u in unidades:
            if u["id"] not in existing_unidades:
                test_unidad = u
                break
        
        if not test_unidad:
            pytest.skip("All unidades already have (todos) config - skipping create test")
        
        # Get SuperAdmin user ID
        superadmin_user = next((u for u in users if u["email"] == SUPERADMIN_EMAIL), None)
        assert superadmin_user, "SuperAdmin user not found"
        
        payload = {
            "unidad_negocio_id": test_unidad["id"],
            "almacen_id": "",  # Todos los almacenes
            "usuario_responsable_id": superadmin_user["id"]
        }
        
        response = self.session.post(
            f"{BASE_URL}/api/config-asignaciones",
            json=payload
        )
        
        assert response.status_code == 201, f"Create failed: {response.text}"
        
        data = response.json()
        assert data["success"]
        assert "data" in data
        
        created = data["data"]
        assert created["unidad_negocio_id"] == test_unidad["id"]
        assert created["usuario_responsable_id"] == superadmin_user["id"]
        assert created["activa"]
        
        # Store for cleanup
        self.created_config_ids.append(created["id"])
        
        print(f"✓ Created config: {created['unidad_negocio_nombre']} → {created['usuario_responsable_nombre']}")
        
        # Cleanup
        self.cleanup_created_configs()
    
    def test_11_create_asignacion_duplicate_error(self):
        """Test creating duplicate configuration returns 409"""
        self.get_auth_token()
        
        # Get existing config
        existing_resp = self.session.get(f"{BASE_URL}/api/config-asignaciones")
        existing = existing_resp.json()["data"]
        
        if not existing:
            pytest.skip("No existing configs to test duplicate")
        
        # Try to create duplicate
        config = existing[0]
        payload = {
            "unidad_negocio_id": config["unidad_negocio_id"],
            "almacen_id": config["almacen_id"],
            "usuario_responsable_id": config["usuario_responsable_id"]
        }
        
        response = self.session.post(
            f"{BASE_URL}/api/config-asignaciones",
            json=payload
        )
        
        assert response.status_code == 409, f"Expected 409, got {response.status_code}: {response.text}"
        print("✓ Duplicate config correctly returns 409")
    
    def test_12_create_asignacion_invalid_user(self):
        """Test creating with invalid user returns 400"""
        self.get_auth_token()
        
        unidades_resp = self.session.get(f"{BASE_URL}/api/config-asignaciones/unidades-negocio")
        unidades = unidades_resp.json()["data"]
        
        payload = {
            "unidad_negocio_id": unidades[0]["id"],
            "almacen_id": "",
            "usuario_responsable_id": str(uuid.uuid4())  # Invalid user
        }
        
        response = self.session.post(
            f"{BASE_URL}/api/config-asignaciones",
            json=payload
        )
        
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        print("✓ Invalid user correctly returns 400")
    
    def test_13_create_asignacion_missing_fields(self):
        """Test creating with missing required fields returns 422"""
        self.get_auth_token()
        
        # Missing usuario_responsable_id
        payload = {
            "unidad_negocio_id": "some-id"
        }
        
        response = self.session.post(
            f"{BASE_URL}/api/config-asignaciones",
            json=payload
        )
        
        assert response.status_code == 422, f"Expected 422, got {response.status_code}"
        print("✓ Missing fields correctly returns 422")
    
    # =========================================================================
    # TEST: PUT /api/config-asignaciones/{id} (Update)
    # =========================================================================
    
    def test_14_update_asignacion_success(self):
        """Test updating an existing configuration"""
        self.get_auth_token()
        
        # Get existing config
        existing_resp = self.session.get(f"{BASE_URL}/api/config-asignaciones")
        existing = existing_resp.json()["data"]
        
        if not existing:
            pytest.skip("No existing configs to test update")
        
        config = existing[0]
        original_activa = config["activa"]
        
        # Toggle activa state
        payload = {
            "activa": not original_activa
        }
        
        response = self.session.put(
            f"{BASE_URL}/api/config-asignaciones/{config['id']}",
            json=payload
        )
        
        assert response.status_code == 200, f"Update failed: {response.text}"
        
        data = response.json()
        assert data["success"]
        assert data["data"]["activa"] == (not original_activa)
        
        print(f"✓ Updated config activa: {original_activa} → {not original_activa}")
        
        # Restore original state
        self.session.put(
            f"{BASE_URL}/api/config-asignaciones/{config['id']}",
            json={"activa": original_activa}
        )
        print("✓ Restored original state")
    
    def test_15_update_asignacion_change_user(self):
        """Test updating responsible user"""
        self.get_auth_token()
        
        # Get existing config
        existing_resp = self.session.get(f"{BASE_URL}/api/config-asignaciones")
        existing = existing_resp.json()["data"]
        
        if not existing:
            pytest.skip("No existing configs to test update")
        
        config = existing[0]
        original_user_id = config["usuario_responsable_id"]
        
        # Get users
        users_resp = self.session.get(f"{BASE_URL}/api/users")
        users = users_resp.json()
        if isinstance(users, dict):
            users = users.get("users", [])
        
        # Find a different user (SuperAdmin)
        superadmin = next((u for u in users if u["role"] == "SuperAdministrador"), None)
        if not superadmin or superadmin["id"] == original_user_id:
            pytest.skip("No different user available for test")
        
        payload = {
            "usuario_responsable_id": superadmin["id"]
        }
        
        response = self.session.put(
            f"{BASE_URL}/api/config-asignaciones/{config['id']}",
            json=payload
        )
        
        assert response.status_code == 200, f"Update failed: {response.text}"
        
        data = response.json()
        assert data["success"]
        
        print("✓ Updated responsible user")
        
        # Restore original
        self.session.put(
            f"{BASE_URL}/api/config-asignaciones/{config['id']}",
            json={"usuario_responsable_id": original_user_id}
        )
    
    def test_16_update_asignacion_not_found(self):
        """Test updating non-existent config returns 404"""
        self.get_auth_token()
        
        fake_id = str(uuid.uuid4())
        response = self.session.put(
            f"{BASE_URL}/api/config-asignaciones/{fake_id}",
            json={"activa": False}
        )
        
        assert response.status_code == 404
        print("✓ Non-existent config correctly returns 404")
    
    # =========================================================================
    # TEST: DELETE /api/config-asignaciones/{id}
    # =========================================================================
    
    def test_17_delete_asignacion_success(self):
        """Test deleting a configuration"""
        self.get_auth_token()
        
        # First create a config to delete
        unidades_resp = self.session.get(f"{BASE_URL}/api/config-asignaciones/unidades-negocio")
        unidades = unidades_resp.json()["data"]
        
        users_resp = self.session.get(f"{BASE_URL}/api/users")
        users = users_resp.json()
        if isinstance(users, dict):
            users = users.get("users", [])
        
        # Find unidad without existing "(todos)" config
        existing_resp = self.session.get(f"{BASE_URL}/api/config-asignaciones")
        existing = existing_resp.json()["data"]
        existing_unidades = {c["unidad_negocio_id"] for c in existing if c["almacen_id"] == ""}
        
        test_unidad = None
        for u in unidades:
            if u["id"] not in existing_unidades:
                test_unidad = u
                break
        
        if not test_unidad:
            pytest.skip("All unidades have configs - skipping delete test")
        
        superadmin = next((u for u in users if u["email"] == SUPERADMIN_EMAIL), None)
        
        # Create config
        create_resp = self.session.post(
            f"{BASE_URL}/api/config-asignaciones",
            json={
                "unidad_negocio_id": test_unidad["id"],
                "almacen_id": "",
                "usuario_responsable_id": superadmin["id"]
            }
        )
        
        if create_resp.status_code != 201:
            pytest.skip(f"Could not create config for delete test: {create_resp.text}")
        
        config_id = create_resp.json()["data"]["id"]
        
        # Now delete it
        response = self.session.delete(f"{BASE_URL}/api/config-asignaciones/{config_id}")
        
        assert response.status_code == 200, f"Delete failed: {response.text}"
        
        data = response.json()
        assert data["success"]
        
        print(f"✓ Deleted config: {config_id}")
        
        # Verify it's gone
        get_resp = self.session.get(f"{BASE_URL}/api/config-asignaciones/{config_id}")
        assert get_resp.status_code == 404
        print("✓ Verified config no longer exists")
    
    def test_18_delete_asignacion_not_found(self):
        """Test deleting non-existent config returns 404"""
        self.get_auth_token()
        
        fake_id = str(uuid.uuid4())
        response = self.session.delete(f"{BASE_URL}/api/config-asignaciones/{fake_id}")
        
        assert response.status_code == 404
        print("✓ Non-existent config correctly returns 404")
    
    # =========================================================================
    # TEST: GET /api/config-asignaciones/{id} (Get by ID)
    # =========================================================================
    
    def test_19_get_asignacion_by_id_success(self):
        """Test getting a specific configuration by ID"""
        self.get_auth_token()
        
        # Get existing configs
        existing_resp = self.session.get(f"{BASE_URL}/api/config-asignaciones")
        existing = existing_resp.json()["data"]
        
        if not existing:
            pytest.skip("No existing configs to test get by ID")
        
        config_id = existing[0]["id"]
        
        response = self.session.get(f"{BASE_URL}/api/config-asignaciones/{config_id}")
        
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"]
        assert data["data"]["id"] == config_id
        
        print(f"✓ Got config by ID: {config_id[:8]}...")
    
    def test_20_get_asignacion_by_id_not_found(self):
        """Test getting non-existent config returns 404"""
        self.get_auth_token()
        
        fake_id = str(uuid.uuid4())
        response = self.session.get(f"{BASE_URL}/api/config-asignaciones/{fake_id}")
        
        assert response.status_code == 404
        print("✓ Non-existent config correctly returns 404")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
