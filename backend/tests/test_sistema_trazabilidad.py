"""
Test Suite for Sistema de Flujo de Aprobación con Log de Trazabilidad y Corrección de Solicitudes
Tests:
- Historial de trazabilidad (GET /api/sistema/solicitudes/{id}/historial)
- Niveles de aprobación configurables (PUT /api/sistema/catalogos/{id}/niveles)
- Corrección y reenvío de solicitudes rechazadas (PUT /api/sistema/solicitudes/{id}/corregir)
- Indicadores de nivel en solicitudes
- Flujo completo: crear -> rechazar -> corregir -> aprobar
"""
import pytest
import requests
import os

# Import centralized test credentials
from conftest import TEST_ADMIN_EMAIL, TEST_ADMIN_PASSWORD

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials (centralized)
ADMIN_EMAIL = os.environ.get("TEST_ADMIN_EMAIL", TEST_ADMIN_EMAIL)
ADMIN_PASSWORD = os.environ.get("TEST_ADMIN_PASSWORD", TEST_ADMIN_PASSWORD)


class TestSistemaTrazabilidad:
    """Tests for the traceability and correction system"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        self.admin_token = None
        self.test_solicitud_id = None
    
    def get_admin_token(self):
        """Get admin authentication token"""
        if self.admin_token:
            return self.admin_token
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Admin login failed: {response.text}"
        self.admin_token = response.json().get("token")
        return self.admin_token
    
    def auth_headers(self):
        """Get authorization headers"""
        return {"Authorization": f"Bearer {self.get_admin_token()}"}
    
    # ============= HISTORIAL DE TRAZABILIDAD =============
    
    def test_01_create_solicitud_with_historial(self):
        """Test creating a solicitud generates initial historial event"""
        response = self.session.post(
            f"{BASE_URL}/api/sistema/solicitudes",
            headers=self.auth_headers(),
            json={
                "catalogo_id": "puestos",
                "datos": {"descripcion": "TEST_Puesto_Trazabilidad", "departamento": "QA"},
                "notas": "Test de trazabilidad"
            }
        )
        assert response.status_code == 200, f"Create solicitud failed: {response.text}"
        data = response.json()
        assert data.get("success")
        assert "solicitud_id" in data
        self.__class__.test_solicitud_id = data["solicitud_id"]
        print(f"Created solicitud: {self.__class__.test_solicitud_id}")
    
    def test_02_get_historial_after_creation(self):
        """Test GET /api/sistema/solicitudes/{id}/historial returns events"""
        solicitud_id = getattr(self.__class__, 'test_solicitud_id', None)
        if not solicitud_id:
            pytest.skip("No solicitud_id from previous test")
        
        response = self.session.get(
            f"{BASE_URL}/api/sistema/solicitudes/{solicitud_id}/historial",
            headers=self.auth_headers()
        )
        assert response.status_code == 200, f"Get historial failed: {response.text}"
        data = response.json()
        
        # Validate historial structure
        assert "historial" in data
        assert "total_eventos" in data
        assert data["total_eventos"] >= 1
        
        # Validate first event is CREACION
        historial = data["historial"]
        assert len(historial) >= 1
        
        # Find CREACION event (historial is sorted by timestamp desc)
        creacion_event = next((e for e in historial if e.get("accion") == "CREACION"), None)
        assert creacion_event is not None, "CREACION event not found"
        assert "timestamp" in creacion_event
        assert "usuario_email" in creacion_event
        assert creacion_event.get("estatus_nuevo") == "Pendiente Nivel 1"
        
        print(f"Historial has {data['total_eventos']} events")
        print(f"CREACION event: {creacion_event.get('descripcion')}")
    
    def test_03_historial_includes_nivel_info(self):
        """Test historial response includes nivel information"""
        solicitud_id = getattr(self.__class__, 'test_solicitud_id', None)
        if not solicitud_id:
            pytest.skip("No solicitud_id from previous test")
        
        response = self.session.get(
            f"{BASE_URL}/api/sistema/solicitudes/{solicitud_id}/historial",
            headers=self.auth_headers()
        )
        assert response.status_code == 200
        data = response.json()
        
        # Validate nivel info
        assert "nivel_actual" in data
        assert "niveles_requeridos" in data
        assert "version_actual" in data
        assert "estatus_actual" in data
        assert "solicitante" in data
        
        print(f"Nivel: {data['nivel_actual']}/{data['niveles_requeridos']}, Version: {data['version_actual']}")
    
    # ============= CONFIGURACIÓN DE NIVELES =============
    
    def test_04_get_catalogos_with_niveles(self):
        """Test GET /api/sistema/catalogos-disponibles returns niveles_aprobacion"""
        response = self.session.get(
            f"{BASE_URL}/api/sistema/catalogos-disponibles",
            headers=self.auth_headers()
        )
        assert response.status_code == 200, f"Get catalogos failed: {response.text}"
        data = response.json()
        
        assert "catalogos" in data
        catalogos = data["catalogos"]
        assert len(catalogos) > 0
        
        # Each catalog should have niveles_aprobacion
        for cat in catalogos:
            assert "niveles_aprobacion" in cat, f"Catalog {cat.get('id')} missing niveles_aprobacion"
            assert cat["niveles_aprobacion"] >= 1 and cat["niveles_aprobacion"] <= 3
        
        print(f"Found {len(catalogos)} catalogs with niveles configured")
    
    def test_05_configure_niveles_aprobacion(self):
        """Test PUT /api/sistema/catalogos/{id}/niveles configures approval levels"""
        # Configure 2 levels for 'puestos' catalog
        response = self.session.put(
            f"{BASE_URL}/api/sistema/catalogos/puestos/niveles",
            headers=self.auth_headers(),
            json={"niveles_aprobacion": 2}
        )
        assert response.status_code == 200, f"Configure niveles failed: {response.text}"
        data = response.json()
        assert data.get("success")
        
        # Verify the change
        response = self.session.get(
            f"{BASE_URL}/api/sistema/catalogos-disponibles",
            headers=self.auth_headers()
        )
        assert response.status_code == 200
        catalogos = response.json().get("catalogos", [])
        puestos = next((c for c in catalogos if c["id"] == "puestos"), None)
        assert puestos is not None
        assert puestos["niveles_aprobacion"] == 2
        
        print("Configured 'puestos' catalog to 2 approval levels")
    
    def test_06_configure_niveles_invalid_value(self):
        """Test configuring invalid niveles (>3 or <1) returns error"""
        # Try to set 4 levels (invalid)
        response = self.session.put(
            f"{BASE_URL}/api/sistema/catalogos/puestos/niveles",
            headers=self.auth_headers(),
            json={"niveles_aprobacion": 4}
        )
        assert response.status_code == 400, "Should reject niveles > 3"
        
        # Try to set 0 levels (invalid)
        response = self.session.put(
            f"{BASE_URL}/api/sistema/catalogos/puestos/niveles",
            headers=self.auth_headers(),
            json={"niveles_aprobacion": 0}
        )
        assert response.status_code == 400, "Should reject niveles < 1"
        
        print("Invalid niveles values correctly rejected")
    
    # ============= RECHAZO Y CORRECCIÓN =============
    
    def test_07_reject_solicitud_creates_historial_event(self):
        """Test rejecting a solicitud adds RECHAZO event to historial"""
        solicitud_id = getattr(self.__class__, 'test_solicitud_id', None)
        if not solicitud_id:
            pytest.skip("No solicitud_id from previous test")
        
        response = self.session.post(
            f"{BASE_URL}/api/sistema/solicitudes/{solicitud_id}/rechazar",
            headers=self.auth_headers(),
            json={"motivo": "Datos incompletos - falta sueldo base"}
        )
        assert response.status_code == 200, f"Reject failed: {response.text}"
        data = response.json()
        assert data.get("success")
        
        # Verify historial has RECHAZO event
        response = self.session.get(
            f"{BASE_URL}/api/sistema/solicitudes/{solicitud_id}/historial",
            headers=self.auth_headers()
        )
        assert response.status_code == 200
        historial_data = response.json()
        
        rechazo_event = next((e for e in historial_data["historial"] if e.get("accion") == "RECHAZO"), None)
        assert rechazo_event is not None, "RECHAZO event not found in historial"
        assert rechazo_event.get("motivo") == "Datos incompletos - falta sueldo base"
        assert rechazo_event.get("estatus_nuevo") == "Rechazada - Pendiente Corrección"
        
        print(f"Solicitud rejected, historial now has {historial_data['total_eventos']} events")
    
    def test_08_solicitud_status_after_rejection(self):
        """Test solicitud status is 'Rechazada - Pendiente Corrección' after rejection"""
        solicitud_id = getattr(self.__class__, 'test_solicitud_id', None)
        if not solicitud_id:
            pytest.skip("No solicitud_id from previous test")
        
        response = self.session.get(
            f"{BASE_URL}/api/sistema/solicitudes/{solicitud_id}",
            headers=self.auth_headers()
        )
        assert response.status_code == 200
        data = response.json()
        
        assert data.get("estatus") == "Rechazada - Pendiente Corrección"
        assert data.get("motivo_rechazo") == "Datos incompletos - falta sueldo base"
        
        print(f"Solicitud status: {data.get('estatus')}")
    
    def test_09_corregir_solicitud(self):
        """Test PUT /api/sistema/solicitudes/{id}/corregir updates data and status"""
        solicitud_id = getattr(self.__class__, 'test_solicitud_id', None)
        if not solicitud_id:
            pytest.skip("No solicitud_id from previous test")
        
        response = self.session.put(
            f"{BASE_URL}/api/sistema/solicitudes/{solicitud_id}/corregir",
            headers=self.auth_headers(),
            json={
                "datos": {
                    "descripcion": "TEST_Puesto_Trazabilidad_Corregido",
                    "departamento": "QA",
                    "sueldo_base": 5000
                },
                "notas": "Corregido con sueldo base"
            }
        )
        assert response.status_code == 200, f"Corregir failed: {response.text}"
        data = response.json()
        assert data.get("success")
        assert "versión" in data.get("message", "").lower() or "version" in data.get("message", "").lower()
        
        print(f"Solicitud corrected: {data.get('message')}")
    
    def test_10_solicitud_status_after_correction(self):
        """Test solicitud status is 'Reenviada' after correction"""
        solicitud_id = getattr(self.__class__, 'test_solicitud_id', None)
        if not solicitud_id:
            pytest.skip("No solicitud_id from previous test")
        
        response = self.session.get(
            f"{BASE_URL}/api/sistema/solicitudes/{solicitud_id}",
            headers=self.auth_headers()
        )
        assert response.status_code == 200
        data = response.json()
        
        assert data.get("estatus") == "Reenviada"
        assert data.get("version") == 2, "Version should be 2 after correction"
        assert data.get("nivel_actual") == 1, "Should reset to nivel 1"
        assert data.get("datos", {}).get("sueldo_base") == 5000
        
        print(f"Solicitud status: {data.get('estatus')}, version: {data.get('version')}")
    
    def test_11_historial_has_correccion_event(self):
        """Test historial includes CORRECCION event after correction"""
        solicitud_id = getattr(self.__class__, 'test_solicitud_id', None)
        if not solicitud_id:
            pytest.skip("No solicitud_id from previous test")
        
        response = self.session.get(
            f"{BASE_URL}/api/sistema/solicitudes/{solicitud_id}/historial",
            headers=self.auth_headers()
        )
        assert response.status_code == 200
        data = response.json()
        
        # Should have at least 3 events: CREACION, RECHAZO, CORRECCION
        assert data["total_eventos"] >= 3
        
        correccion_event = next((e for e in data["historial"] if e.get("accion") == "CORRECCION"), None)
        assert correccion_event is not None, "CORRECCION event not found"
        assert correccion_event.get("estatus_nuevo") == "Reenviada"
        assert "datos_anteriores" in correccion_event
        assert "datos_nuevos" in correccion_event
        
        print(f"Historial has {data['total_eventos']} events including CORRECCION")
    
    # ============= FLUJO COMPLETO CON NIVELES =============
    
    def test_12_create_solicitud_with_2_levels(self):
        """Test creating solicitud for catalog with 2 approval levels"""
        # First ensure puestos has 2 levels
        self.session.put(
            f"{BASE_URL}/api/sistema/catalogos/puestos/niveles",
            headers=self.auth_headers(),
            json={"niveles_aprobacion": 2}
        )
        
        response = self.session.post(
            f"{BASE_URL}/api/sistema/solicitudes",
            headers=self.auth_headers(),
            json={
                "catalogo_id": "puestos",
                "datos": {"descripcion": "TEST_Puesto_2Niveles", "departamento": "IT", "sueldo_base": 8000},
                "notas": "Test con 2 niveles"
            }
        )
        assert response.status_code == 200
        data = response.json()
        self.__class__.test_solicitud_2niveles_id = data["solicitud_id"]
        
        # Verify it has 2 niveles_requeridos
        response = self.session.get(
            f"{BASE_URL}/api/sistema/solicitudes/{data['solicitud_id']}",
            headers=self.auth_headers()
        )
        assert response.status_code == 200
        sol_data = response.json()
        assert sol_data.get("niveles_requeridos") == 2
        assert sol_data.get("nivel_actual") == 1
        
        print(f"Created solicitud with 2 levels: {data['solicitud_id']}")
    
    def test_13_approve_level_1(self):
        """Test approving level 1 moves to level 2"""
        solicitud_id = getattr(self.__class__, 'test_solicitud_2niveles_id', None)
        if not solicitud_id:
            pytest.skip("No solicitud_id from previous test")
        
        response = self.session.post(
            f"{BASE_URL}/api/sistema/solicitudes/{solicitud_id}/aprobar",
            headers=self.auth_headers(),
            json={"password": ADMIN_PASSWORD, "comentario": "Nivel 1 aprobado"}
        )
        assert response.status_code == 200, f"Approve level 1 failed: {response.text}"
        data = response.json()
        assert data.get("success")
        assert "Nivel 2" in data.get("estatus", "") or "nivel 2" in data.get("message", "").lower()
        
        # Verify status
        response = self.session.get(
            f"{BASE_URL}/api/sistema/solicitudes/{solicitud_id}",
            headers=self.auth_headers()
        )
        assert response.status_code == 200
        sol_data = response.json()
        assert sol_data.get("nivel_actual") == 2
        assert "Pendiente Nivel 2" in sol_data.get("estatus", "")
        
        print("Level 1 approved, now at level 2")
    
    def test_14_historial_has_aprobacion_nivel_event(self):
        """Test historial includes APROBACION_NIVEL event"""
        solicitud_id = getattr(self.__class__, 'test_solicitud_2niveles_id', None)
        if not solicitud_id:
            pytest.skip("No solicitud_id from previous test")
        
        response = self.session.get(
            f"{BASE_URL}/api/sistema/solicitudes/{solicitud_id}/historial",
            headers=self.auth_headers()
        )
        assert response.status_code == 200
        data = response.json()
        
        aprobacion_event = next((e for e in data["historial"] if e.get("accion") == "APROBACION_NIVEL"), None)
        assert aprobacion_event is not None, "APROBACION_NIVEL event not found"
        assert "Nivel 1" in aprobacion_event.get("descripcion", "")
        
        print("Found APROBACION_NIVEL event in historial")
    
    def test_15_approve_level_2_final(self):
        """Test approving level 2 completes the solicitud"""
        solicitud_id = getattr(self.__class__, 'test_solicitud_2niveles_id', None)
        if not solicitud_id:
            pytest.skip("No solicitud_id from previous test")
        
        response = self.session.post(
            f"{BASE_URL}/api/sistema/solicitudes/{solicitud_id}/aprobar",
            headers=self.auth_headers(),
            json={"password": ADMIN_PASSWORD, "comentario": "Aprobación final nivel 2"}
        )
        assert response.status_code == 200, f"Approve level 2 failed: {response.text}"
        data = response.json()
        assert data.get("success")
        
        # Verify final status
        response = self.session.get(
            f"{BASE_URL}/api/sistema/solicitudes/{solicitud_id}",
            headers=self.auth_headers()
        )
        assert response.status_code == 200
        sol_data = response.json()
        assert sol_data.get("estatus") == "Aprobada"
        
        print("Solicitud fully approved after 2 levels")
    
    def test_16_historial_has_aprobacion_final_event(self):
        """Test historial includes APROBACION_FINAL event"""
        solicitud_id = getattr(self.__class__, 'test_solicitud_2niveles_id', None)
        if not solicitud_id:
            pytest.skip("No solicitud_id from previous test")
        
        response = self.session.get(
            f"{BASE_URL}/api/sistema/solicitudes/{solicitud_id}/historial",
            headers=self.auth_headers()
        )
        assert response.status_code == 200
        data = response.json()
        
        final_event = next((e for e in data["historial"] if e.get("accion") == "APROBACION_FINAL"), None)
        assert final_event is not None, "APROBACION_FINAL event not found"
        assert final_event.get("estatus_nuevo") == "Aprobada"
        
        # Should have 3 events: CREACION, APROBACION_NIVEL, APROBACION_FINAL
        assert data["total_eventos"] >= 3
        
        print(f"Historial complete with {data['total_eventos']} events")
    
    # ============= SOLICITUDES LIST WITH NIVEL INDICATORS =============
    
    def test_17_solicitudes_list_includes_nivel_info(self):
        """Test GET /api/sistema/solicitudes returns nivel info for each solicitud"""
        response = self.session.get(
            f"{BASE_URL}/api/sistema/solicitudes",
            headers=self.auth_headers()
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "solicitudes" in data
        solicitudes = data["solicitudes"]
        
        # Check that solicitudes have nivel info
        for sol in solicitudes[:5]:  # Check first 5
            assert "nivel_actual" in sol, f"Solicitud {sol.get('id')} missing nivel_actual"
            assert "niveles_requeridos" in sol, f"Solicitud {sol.get('id')} missing niveles_requeridos"
            assert "version" in sol, f"Solicitud {sol.get('id')} missing version"
        
        print(f"Found {len(solicitudes)} solicitudes with nivel info")
    
    # ============= CLEANUP =============
    
    def test_99_cleanup(self):
        """Reset puestos catalog to 1 level"""
        response = self.session.put(
            f"{BASE_URL}/api/sistema/catalogos/puestos/niveles",
            headers=self.auth_headers(),
            json={"niveles_aprobacion": 1}
        )
        assert response.status_code == 200
        print("Cleanup: Reset puestos to 1 approval level")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
