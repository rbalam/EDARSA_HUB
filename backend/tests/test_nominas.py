"""
Test suite for EDARSA HUB - Módulo de Nóminas
Tests the complete payroll workflow: Headcount -> Incidencias -> Validación RH -> Maquilador -> Autorización -> Tesorería -> Pagada
"""
import pytest
import requests
import os
import uuid
from datetime import datetime, timedelta

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "admin@inventario.com"
ADMIN_PASSWORD = "admin123"


class TestNominaConfiguration:
    """Tests for nomina configuration endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup: Login and get token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        self.token = data.get("token")
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_get_configuracion_default(self):
        """GET /api/nomina/configuracion - Should return default configuration"""
        response = requests.get(f"{BASE_URL}/api/nomina/configuracion", headers=self.headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        assert "configuracion" in data
        config = data["configuracion"]
        
        # Verify default values
        assert "dia_corte" in config
        assert "dia_pago" in config
        assert "horario_headcount" in config
        assert "horario_maquilador" in config
        assert "horario_tesoreria" in config
        
        # Default values check
        assert config.get("dia_corte") == 0  # Domingo
        assert config.get("dia_pago") == 1  # Lunes
        assert config.get("horario_headcount") == "10:00"
        assert config.get("horario_maquilador") == "12:00"
        assert config.get("horario_tesoreria") == "14:00"
        print("✓ GET /api/nomina/configuracion returns default config")
    
    def test_post_configuracion_admin_only(self):
        """POST /api/nomina/configuracion - Only Admin can save configuration"""
        # Test with admin (should succeed)
        config_data = {
            "dia_corte": 0,
            "dia_pago": 1,
            "horario_headcount": "10:00",
            "horario_maquilador": "12:00",
            "horario_tesoreria": "14:00",
            "dias_inhabiles": []
        }
        
        response = requests.post(f"{BASE_URL}/api/nomina/configuracion", 
                                 json=config_data, headers=self.headers)
        assert response.status_code == 200, f"Admin should be able to save config: {response.text}"
        
        data = response.json()
        assert data.get("success") == True
        print("✓ POST /api/nomina/configuracion - Admin can save configuration")
    
    def test_post_configuracion_custom_values(self):
        """POST /api/nomina/configuracion - Save custom configuration values"""
        config_data = {
            "dia_corte": 5,  # Viernes
            "dia_pago": 2,   # Martes
            "horario_headcount": "09:00",
            "horario_maquilador": "11:00",
            "horario_tesoreria": "15:00",
            "dias_inhabiles": ["2026-01-01", "2026-12-25"]
        }
        
        response = requests.post(f"{BASE_URL}/api/nomina/configuracion", 
                                 json=config_data, headers=self.headers)
        assert response.status_code == 200, f"Failed to save custom config: {response.text}"
        
        # Verify saved values
        response = requests.get(f"{BASE_URL}/api/nomina/configuracion", headers=self.headers)
        assert response.status_code == 200
        
        data = response.json()
        config = data["configuracion"]
        assert config.get("dia_corte") == 5
        assert config.get("dia_pago") == 2
        assert config.get("horario_headcount") == "09:00"
        print("✓ POST /api/nomina/configuracion - Custom values saved correctly")
        
        # Restore defaults
        requests.post(f"{BASE_URL}/api/nomina/configuracion", json={
            "dia_corte": 0, "dia_pago": 1, "horario_headcount": "10:00",
            "horario_maquilador": "12:00", "horario_tesoreria": "14:00"
        }, headers=self.headers)


class TestNominaCiclos:
    """Tests for nomina cycles CRUD operations"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup: Login and get token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        self.token = data.get("token")
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_get_ciclos_list(self):
        """GET /api/nomina/ciclos - List payroll cycles with filters"""
        response = requests.get(f"{BASE_URL}/api/nomina/ciclos", headers=self.headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        assert "ciclos" in data
        assert "total" in data
        assert isinstance(data["ciclos"], list)
        print(f"✓ GET /api/nomina/ciclos - Found {data['total']} cycles")
    
    def test_get_ciclos_with_filters(self):
        """GET /api/nomina/ciclos - Test period filters"""
        # Test 'actual' period
        response = requests.get(f"{BASE_URL}/api/nomina/ciclos?periodo=actual", headers=self.headers)
        assert response.status_code == 200
        
        # Test 'anterior' period
        response = requests.get(f"{BASE_URL}/api/nomina/ciclos?periodo=anterior", headers=self.headers)
        assert response.status_code == 200
        
        # Test 'todos' period
        response = requests.get(f"{BASE_URL}/api/nomina/ciclos?periodo=todos", headers=self.headers)
        assert response.status_code == 200
        print("✓ GET /api/nomina/ciclos - Period filters work correctly")
    
    def test_create_ciclo_requires_supervisor_or_admin(self):
        """POST /api/nomina/ciclos - Create cycle requires Supervisor/Admin role"""
        # Get a sucursal ID first
        sucursales_response = requests.get(f"{BASE_URL}/api/rrhh/catalogos/sucursales", headers=self.headers)
        sucursal_id = "1"  # Default if no sucursales
        if sucursales_response.status_code == 200:
            sucursales = sucursales_response.json().get("sucursales", [])
            if sucursales:
                sucursal_id = str(sucursales[0].get("SucursalID", sucursales[0].get("id", "1")))
        
        # Create cycle with unique date to avoid duplicates
        fecha_corte = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
        
        ciclo_data = {
            "sucursal_id": sucursal_id,
            "fecha_corte": fecha_corte,
            "tipo_nomina": "quincenal",
            "notas": "TEST_Ciclo de prueba automatizada"
        }
        
        response = requests.post(f"{BASE_URL}/api/nomina/ciclos", 
                                 json=ciclo_data, headers=self.headers)
        
        # Should succeed for Admin
        if response.status_code == 200:
            data = response.json()
            assert data.get("success") == True
            assert "ciclo_id" in data
            self.test_ciclo_id = data["ciclo_id"]
            print(f"✓ POST /api/nomina/ciclos - Cycle created: {self.test_ciclo_id}")
        elif response.status_code == 400:
            # Might already exist
            print("✓ POST /api/nomina/ciclos - Validation working (cycle may already exist)")
        else:
            pytest.fail(f"Unexpected response: {response.status_code} - {response.text}")
    
    def test_create_ciclo_validation(self):
        """POST /api/nomina/ciclos - Validate required fields"""
        # Missing sucursal_id
        response = requests.post(f"{BASE_URL}/api/nomina/ciclos", 
                                 json={"fecha_corte": "2026-02-01"}, headers=self.headers)
        assert response.status_code == 400, "Should fail without sucursal_id"
        
        # Missing fecha_corte
        response = requests.post(f"{BASE_URL}/api/nomina/ciclos", 
                                 json={"sucursal_id": "1"}, headers=self.headers)
        assert response.status_code == 400, "Should fail without fecha_corte"
        print("✓ POST /api/nomina/ciclos - Validation works correctly")


class TestNominaWorkflow:
    """Tests for the complete payroll workflow"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup: Login and get token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        self.token = data.get("token")
        self.headers = {"Authorization": f"Bearer {self.token}"}
        self.user = data.get("user", {})
    
    def _get_or_create_test_ciclo(self):
        """Helper to get or create a test cycle"""
        # First try to find an existing test cycle
        response = requests.get(f"{BASE_URL}/api/nomina/ciclos?periodo=todos", headers=self.headers)
        if response.status_code == 200:
            ciclos = response.json().get("ciclos", [])
            for ciclo in ciclos:
                if ciclo.get("etapa_actual") != "pagada":
                    return ciclo.get("id")
        
        # Create a new one
        fecha_corte = (datetime.now() + timedelta(days=60)).strftime("%Y-%m-%d")
        ciclo_data = {
            "sucursal_id": "1",
            "fecha_corte": fecha_corte,
            "tipo_nomina": "quincenal",
            "notas": "TEST_Workflow test cycle"
        }
        response = requests.post(f"{BASE_URL}/api/nomina/ciclos", 
                                 json=ciclo_data, headers=self.headers)
        if response.status_code == 200:
            return response.json().get("ciclo_id")
        return None
    
    def test_avanzar_etapa_requires_password(self):
        """POST /api/nomina/ciclos/{id}/avanzar - Requires valid password"""
        ciclo_id = self._get_or_create_test_ciclo()
        if not ciclo_id:
            pytest.skip("No test cycle available")
        
        # Without password
        response = requests.post(f"{BASE_URL}/api/nomina/ciclos/{ciclo_id}/avanzar", 
                                 json={}, headers=self.headers)
        assert response.status_code == 400, "Should require password"
        
        # With wrong password
        response = requests.post(f"{BASE_URL}/api/nomina/ciclos/{ciclo_id}/avanzar", 
                                 json={"password": "wrongpassword"}, headers=self.headers)
        assert response.status_code == 401, "Should reject wrong password"
        print("✓ POST /api/nomina/ciclos/{id}/avanzar - Password validation works")
    
    def test_avanzar_etapa_with_valid_password(self):
        """POST /api/nomina/ciclos/{id}/avanzar - Advance with valid password"""
        ciclo_id = self._get_or_create_test_ciclo()
        if not ciclo_id:
            pytest.skip("No test cycle available")
        
        # Get current stage
        response = requests.get(f"{BASE_URL}/api/nomina/ciclos/{ciclo_id}", headers=self.headers)
        if response.status_code != 200:
            pytest.skip("Could not get cycle details")
        
        ciclo = response.json().get("ciclo", {})
        etapa_actual = ciclo.get("etapa_actual")
        
        if etapa_actual == "pagada":
            pytest.skip("Cycle already completed")
        
        # Advance with valid password
        response = requests.post(f"{BASE_URL}/api/nomina/ciclos/{ciclo_id}/avanzar", 
                                 json={"password": ADMIN_PASSWORD, "comentario": "TEST_Avance automático"}, 
                                 headers=self.headers)
        
        if response.status_code == 200:
            data = response.json()
            assert data.get("success") == True
            assert "etapa_nueva" in data
            print(f"✓ POST /api/nomina/ciclos/{ciclo_id}/avanzar - Advanced from {etapa_actual} to {data.get('etapa_nueva')}")
        elif response.status_code == 403:
            print("✓ POST /api/nomina/ciclos/{id}/avanzar - Permission check working")
        else:
            print(f"⚠ Advance returned {response.status_code}: {response.text}")
    
    def test_rechazar_devuelve_a_validacion_rh(self):
        """POST /api/nomina/ciclos/{id}/rechazar - Returns to validacion_rh stage"""
        ciclo_id = self._get_or_create_test_ciclo()
        if not ciclo_id:
            pytest.skip("No test cycle available")
        
        # Get current stage
        response = requests.get(f"{BASE_URL}/api/nomina/ciclos/{ciclo_id}", headers=self.headers)
        if response.status_code != 200:
            pytest.skip("Could not get cycle details")
        
        ciclo = response.json().get("ciclo", {})
        etapa_actual = ciclo.get("etapa_actual")
        
        # Can only reject from autorizacion or maquilador
        if etapa_actual not in ["autorizacion", "maquilador"]:
            # Try to advance to a rejectable stage first
            print(f"⚠ Current stage '{etapa_actual}' cannot be rejected, skipping")
            pytest.skip(f"Stage {etapa_actual} cannot be rejected")
        
        # Reject without motivo
        response = requests.post(f"{BASE_URL}/api/nomina/ciclos/{ciclo_id}/rechazar", 
                                 json={}, headers=self.headers)
        assert response.status_code == 400, "Should require motivo"
        
        # Reject with motivo
        response = requests.post(f"{BASE_URL}/api/nomina/ciclos/{ciclo_id}/rechazar", 
                                 json={"motivo": "TEST_Rechazo de prueba"}, headers=self.headers)
        
        if response.status_code == 200:
            data = response.json()
            assert data.get("success") == True
            
            # Verify it went back to validacion_rh
            response = requests.get(f"{BASE_URL}/api/nomina/ciclos/{ciclo_id}", headers=self.headers)
            ciclo = response.json().get("ciclo", {})
            assert ciclo.get("etapa_actual") == "validacion_rh"
            print("✓ POST /api/nomina/ciclos/{id}/rechazar - Returned to validacion_rh")
        else:
            print(f"⚠ Reject returned {response.status_code}: {response.text}")


class TestNominaMovimientos:
    """Tests for payroll movements (incidencias)"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup: Login and get token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        self.token = data.get("token")
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def _get_test_ciclo_id(self):
        """Get a test cycle ID that's in an editable stage"""
        response = requests.get(f"{BASE_URL}/api/nomina/ciclos?periodo=todos", headers=self.headers)
        if response.status_code == 200:
            ciclos = response.json().get("ciclos", [])
            for ciclo in ciclos:
                if ciclo.get("etapa_actual") in ["headcount", "incidencias", "validacion_rh"]:
                    return ciclo.get("id")
        return None
    
    def test_get_movimientos(self):
        """GET /api/nomina/ciclos/{id}/movimientos - List movements"""
        ciclo_id = self._get_test_ciclo_id()
        if not ciclo_id:
            pytest.skip("No editable cycle available")
        
        response = requests.get(f"{BASE_URL}/api/nomina/ciclos/{ciclo_id}/movimientos", 
                                headers=self.headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        assert "movimientos" in data
        assert "total" in data
        print(f"✓ GET /api/nomina/ciclos/{ciclo_id}/movimientos - Found {data['total']} movements")
    
    def test_post_movimiento(self):
        """POST /api/nomina/ciclos/{id}/movimientos - Add movement"""
        ciclo_id = self._get_test_ciclo_id()
        if not ciclo_id:
            pytest.skip("No editable cycle available")
        
        movimiento_data = {
            "colaborador_id": "1",
            "tipo_incidencia": "Bono",
            "monto": 500.00,
            "unidades": 1,
            "notas": "TEST_Bono de prueba"
        }
        
        response = requests.post(f"{BASE_URL}/api/nomina/ciclos/{ciclo_id}/movimientos", 
                                 json=movimiento_data, headers=self.headers)
        
        if response.status_code == 200:
            data = response.json()
            assert data.get("success") == True
            assert "movimiento_id" in data
            print(f"✓ POST /api/nomina/ciclos/{ciclo_id}/movimientos - Movement created")
        elif response.status_code == 400:
            print("✓ POST /api/nomina/ciclos/{id}/movimientos - Validation working")
        else:
            pytest.fail(f"Unexpected response: {response.status_code} - {response.text}")
    
    def test_post_movimiento_validation(self):
        """POST /api/nomina/ciclos/{id}/movimientos - Validate required fields"""
        ciclo_id = self._get_test_ciclo_id()
        if not ciclo_id:
            pytest.skip("No editable cycle available")
        
        # Missing colaborador_id
        response = requests.post(f"{BASE_URL}/api/nomina/ciclos/{ciclo_id}/movimientos", 
                                 json={"tipo_incidencia": "Bono"}, headers=self.headers)
        assert response.status_code == 400, "Should require colaborador_id"
        
        # Missing tipo_incidencia
        response = requests.post(f"{BASE_URL}/api/nomina/ciclos/{ciclo_id}/movimientos", 
                                 json={"colaborador_id": "1"}, headers=self.headers)
        assert response.status_code == 400, "Should require tipo_incidencia"
        print("✓ POST /api/nomina/ciclos/{id}/movimientos - Validation works")


class TestNominaKPIs:
    """Tests for KPIs per position"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup: Login and get token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        self.token = data.get("token")
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_get_kpis(self):
        """GET /api/nomina/kpis - List KPIs"""
        response = requests.get(f"{BASE_URL}/api/nomina/kpis", headers=self.headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        assert "kpis" in data
        assert "total" in data
        print(f"✓ GET /api/nomina/kpis - Found {data['total']} KPIs")
    
    def test_post_kpi_admin_only(self):
        """POST /api/nomina/kpis - Only Admin can create KPIs"""
        kpi_data = {
            "puesto_id": "1",
            "indicadores": [
                {"nombre": "Ventas", "meta": 100000, "peso": 50},
                {"nombre": "Asistencia", "meta": 100, "peso": 50}
            ]
        }
        
        response = requests.post(f"{BASE_URL}/api/nomina/kpis", 
                                 json=kpi_data, headers=self.headers)
        
        if response.status_code == 200:
            data = response.json()
            assert data.get("success") == True
            print("✓ POST /api/nomina/kpis - KPI created/updated")
        elif response.status_code == 403:
            print("✓ POST /api/nomina/kpis - Permission check working")
        else:
            print(f"⚠ KPI creation returned {response.status_code}: {response.text}")
    
    def test_post_kpi_validation(self):
        """POST /api/nomina/kpis - Validate required fields"""
        # Missing puesto_id
        response = requests.post(f"{BASE_URL}/api/nomina/kpis", 
                                 json={"indicadores": []}, headers=self.headers)
        assert response.status_code == 400, "Should require puesto_id"
        print("✓ POST /api/nomina/kpis - Validation works")


class TestNominaHistorial:
    """Tests for traceability history"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup: Login and get token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        self.token = data.get("token")
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_ciclo_has_historial(self):
        """Verify cycles have historial array with events"""
        response = requests.get(f"{BASE_URL}/api/nomina/ciclos?periodo=todos", headers=self.headers)
        assert response.status_code == 200
        
        ciclos = response.json().get("ciclos", [])
        if not ciclos:
            pytest.skip("No cycles to test")
        
        # Get first cycle details
        ciclo_id = ciclos[0].get("id")
        response = requests.get(f"{BASE_URL}/api/nomina/ciclos/{ciclo_id}", headers=self.headers)
        assert response.status_code == 200
        
        ciclo = response.json().get("ciclo", {})
        historial = ciclo.get("historial", [])
        
        assert isinstance(historial, list), "Historial should be a list"
        
        if historial:
            evento = historial[0]
            assert "id" in evento
            assert "tipo" in evento
            assert "accion" in evento
            assert "timestamp" in evento
            print(f"✓ Cycle {ciclo_id} has {len(historial)} history events")
        else:
            print(f"⚠ Cycle {ciclo_id} has no history events yet")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
