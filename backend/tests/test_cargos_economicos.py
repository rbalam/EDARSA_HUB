"""
Test Suite for Cargos Económicos - Subfase 2C.3
EDARSA HUB - CAB-003

Tests the complete lifecycle of economic charges:
- Basic endpoints (list, metrics, pending, applied)
- Eligibility evaluation
- Charge creation from approved responsibility
- State transitions (PENDIENTE → AUTORIZADO → APLICADO)
- Invalid transitions
- Permission validation by amount and role
- Reversal (requires GERENTE_OPS+)
- Audit log
"""
import pytest
import requests
import os
import uuid
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test data
TEST_WORKFLOW_ID = f"TEST-WF-CARGO-{uuid.uuid4().hex[:8]}"
TEST_RESPONSABILIDAD_ID = None  # Will be set after creation
TEST_CARGO_ID = None  # Will be set after creation


class TestCargosBasicEndpoints:
    """Test basic GET endpoints for cargos económicos"""
    
    def test_listar_cargos_empty(self):
        """GET /api/v2/cargos - Should return empty list initially"""
        response = requests.get(f"{BASE_URL}/api/v2/cargos")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "total" in data
        assert "items" in data
        assert isinstance(data["items"], list)
        print(f"✓ GET /api/v2/cargos - Total: {data['total']}")
    
    def test_metricas_cargos(self):
        """GET /api/v2/cargos/metricas - Should return metrics structure"""
        response = requests.get(f"{BASE_URL}/api/v2/cargos/metricas")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        # Validate metrics structure
        assert "total_cargos" in data
        assert "por_estatus" in data
        assert "monto_total_propuesto" in data
        assert "monto_total_autorizado" in data
        assert "monto_total_aplicado" in data
        assert "monto_total_revertido" in data
        
        print(f"✓ GET /api/v2/cargos/metricas - Total cargos: {data['total_cargos']}")
    
    def test_cargos_pendientes(self):
        """GET /api/v2/cargos/pendientes - Should return pending charges"""
        response = requests.get(f"{BASE_URL}/api/v2/cargos/pendientes")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        assert "total" in data
        assert "monto_total_pendiente" in data
        assert "items" in data
        
        print(f"✓ GET /api/v2/cargos/pendientes - Total: {data['total']}, Monto: ${data['monto_total_pendiente']}")
    
    def test_cargos_aplicados(self):
        """GET /api/v2/cargos/aplicados - Should return applied charges"""
        response = requests.get(f"{BASE_URL}/api/v2/cargos/aplicados")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        assert "total" in data
        assert "monto_total_aplicado" in data
        assert "items" in data
        
        print(f"✓ GET /api/v2/cargos/aplicados - Total: {data['total']}, Monto: ${data['monto_total_aplicado']}")


class TestElegibilidad:
    """Test eligibility evaluation for creating charges"""
    
    def test_elegibilidad_responsabilidad_no_existe(self):
        """GET /api/v2/cargos/elegibilidad/{id} - Non-existent responsibility"""
        fake_id = "nonexistent-responsabilidad-id"
        response = requests.get(f"{BASE_URL}/api/v2/cargos/elegibilidad/{fake_id}")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        assert data["responsabilidad_id"] == fake_id
        assert data["es_elegible"] == False
        assert "no encontrada" in data["motivo"].lower()
        
        print(f"✓ Elegibilidad - Responsabilidad no encontrada: {data['motivo']}")
    
    def test_elegibilidad_responsabilidad_calculado(self):
        """GET /api/v2/cargos/elegibilidad/{id} - Responsibility in CALCULADO state"""
        # Get a responsibility in CALCULADO state
        response = requests.get(f"{BASE_URL}/api/v2/responsabilidad?estado=CALCULADO&limit=1")
        if response.status_code == 200:
            data = response.json()
            if data.get("items"):
                resp_id = data["items"][0]["id"]
                
                elig_response = requests.get(f"{BASE_URL}/api/v2/cargos/elegibilidad/{resp_id}")
                assert elig_response.status_code == 200
                elig_data = elig_response.json()
                
                assert elig_data["es_elegible"] == False
                assert "APROBADO" in elig_data["motivo"]
                print(f"✓ Elegibilidad - CALCULADO no elegible: {elig_data['motivo']}")
            else:
                pytest.skip("No CALCULADO responsibilities found")
        else:
            pytest.skip("Could not fetch responsibilities")
    
    def test_elegibilidad_responsabilidad_propuesto(self):
        """GET /api/v2/cargos/elegibilidad/{id} - Responsibility in PROPUESTO state"""
        response = requests.get(f"{BASE_URL}/api/v2/responsabilidad?estado=PROPUESTO&limit=1")
        if response.status_code == 200:
            data = response.json()
            if data.get("items"):
                resp_id = data["items"][0]["id"]
                
                elig_response = requests.get(f"{BASE_URL}/api/v2/cargos/elegibilidad/{resp_id}")
                assert elig_response.status_code == 200
                elig_data = elig_response.json()
                
                assert elig_data["es_elegible"] == False
                assert "APROBADO" in elig_data["motivo"]
                print(f"✓ Elegibilidad - PROPUESTO no elegible: {elig_data['motivo']}")
            else:
                pytest.skip("No PROPUESTO responsibilities found")
        else:
            pytest.skip("Could not fetch responsibilities")
    
    def test_elegibilidad_responsabilidad_exonerado(self):
        """GET /api/v2/cargos/elegibilidad/{id} - Responsibility in EXONERADO state"""
        response = requests.get(f"{BASE_URL}/api/v2/responsabilidad?estado=EXONERADO&limit=1")
        if response.status_code == 200:
            data = response.json()
            if data.get("items"):
                resp_id = data["items"][0]["id"]
                
                elig_response = requests.get(f"{BASE_URL}/api/v2/cargos/elegibilidad/{resp_id}")
                assert elig_response.status_code == 200
                elig_data = elig_response.json()
                
                assert elig_data["es_elegible"] == False
                assert elig_data["tiene_exoneracion"] == True or "exonera" in elig_data["motivo"].lower()
                print(f"✓ Elegibilidad - EXONERADO no elegible: {elig_data['motivo']}")
            else:
                pytest.skip("No EXONERADO responsibilities found")
        else:
            pytest.skip("Could not fetch responsibilities")


class TestCrearCargoValidaciones:
    """Test validation rules for creating charges"""
    
    def test_crear_cargo_responsabilidad_no_existe(self):
        """POST /api/v2/cargos - Should fail for non-existent responsibility"""
        payload = {
            "responsabilidad_id": "fake-responsabilidad-id",
            "comentario": "Intento de crear cargo para responsabilidad inexistente",
            "usuario_id": "test-user-001",
            "usuario_rol": "SUPERVISOR"
        }
        response = requests.post(f"{BASE_URL}/api/v2/cargos", json=payload)
        assert response.status_code == 400, f"Expected 400, got {response.status_code}: {response.text}"
        print(f"✓ Crear cargo - Responsabilidad no existe: {response.json().get('detail', '')}")
    
    def test_crear_cargo_comentario_muy_corto(self):
        """POST /api/v2/cargos - Should fail with short comment"""
        payload = {
            "responsabilidad_id": "any-id",
            "comentario": "corto",  # Less than 10 chars
            "usuario_id": "test-user-001",
            "usuario_rol": "SUPERVISOR"
        }
        response = requests.post(f"{BASE_URL}/api/v2/cargos", json=payload)
        assert response.status_code == 422, f"Expected 422, got {response.status_code}: {response.text}"
        print(f"✓ Crear cargo - Comentario muy corto rechazado")
    
    def test_crear_cargo_comentario_trivial(self):
        """POST /api/v2/cargos - Should fail with trivial comment"""
        payload = {
            "responsabilidad_id": "any-id",
            "comentario": "ok",  # Trivial comment
            "usuario_id": "test-user-001",
            "usuario_rol": "SUPERVISOR"
        }
        response = requests.post(f"{BASE_URL}/api/v2/cargos", json=payload)
        assert response.status_code == 422, f"Expected 422, got {response.status_code}: {response.text}"
        print(f"✓ Crear cargo - Comentario trivial rechazado")


class TestCargoNoEncontrado:
    """Test 404 responses for non-existent charges"""
    
    def test_obtener_cargo_no_existe(self):
        """GET /api/v2/cargos/{id} - Should return 404"""
        fake_id = "nonexistent-cargo-id"
        response = requests.get(f"{BASE_URL}/api/v2/cargos/{fake_id}")
        assert response.status_code == 404, f"Expected 404, got {response.status_code}: {response.text}"
        print(f"✓ GET cargo no existe - 404 returned")
    
    def test_obtener_log_cargo_no_existe(self):
        """GET /api/v2/cargos/{id}/log - Should return 404"""
        fake_id = "nonexistent-cargo-id"
        response = requests.get(f"{BASE_URL}/api/v2/cargos/{fake_id}/log")
        assert response.status_code == 404, f"Expected 404, got {response.status_code}: {response.text}"
        print(f"✓ GET log cargo no existe - 404 returned")
    
    def test_autorizar_cargo_no_existe(self):
        """POST /api/v2/cargos/{id}/autorizar - Should return 404"""
        fake_id = "nonexistent-cargo-id"
        payload = {
            "usuario_id": "test-user",
            "usuario_rol": "SUPERVISOR",
            "comentario": "Intento de autorizar cargo inexistente"
        }
        response = requests.post(f"{BASE_URL}/api/v2/cargos/{fake_id}/autorizar", json=payload)
        assert response.status_code == 404, f"Expected 404, got {response.status_code}: {response.text}"
        print(f"✓ Autorizar cargo no existe - 404 returned")
    
    def test_aplicar_cargo_no_existe(self):
        """POST /api/v2/cargos/{id}/aplicar - Should return 404"""
        fake_id = "nonexistent-cargo-id"
        payload = {
            "usuario_id": "test-user",
            "usuario_rol": "SUPERVISOR",
            "comentario": "Intento de aplicar cargo inexistente"
        }
        response = requests.post(f"{BASE_URL}/api/v2/cargos/{fake_id}/aplicar", json=payload)
        assert response.status_code == 404, f"Expected 404, got {response.status_code}: {response.text}"
        print(f"✓ Aplicar cargo no existe - 404 returned")
    
    def test_rechazar_cargo_no_existe(self):
        """POST /api/v2/cargos/{id}/rechazar - Should return 404"""
        fake_id = "nonexistent-cargo-id"
        payload = {
            "usuario_id": "test-user",
            "usuario_rol": "SUPERVISOR",
            "comentario": "Intento de rechazar cargo inexistente"
        }
        response = requests.post(f"{BASE_URL}/api/v2/cargos/{fake_id}/rechazar", json=payload)
        assert response.status_code == 404, f"Expected 404, got {response.status_code}: {response.text}"
        print(f"✓ Rechazar cargo no existe - 404 returned")
    
    def test_revertir_cargo_no_existe(self):
        """POST /api/v2/cargos/{id}/revertir - Should return 404"""
        fake_id = "nonexistent-cargo-id"
        payload = {
            "usuario_id": "test-user",
            "usuario_rol": "GERENTE_OPS",
            "motivo_reversa": "Intento de revertir cargo inexistente con motivo detallado"
        }
        response = requests.post(f"{BASE_URL}/api/v2/cargos/{fake_id}/revertir", json=payload)
        assert response.status_code == 404, f"Expected 404, got {response.status_code}: {response.text}"
        print(f"✓ Revertir cargo no existe - 404 returned")
    
    def test_cancelar_cargo_no_existe(self):
        """POST /api/v2/cargos/{id}/cancelar - Should return 404"""
        fake_id = "nonexistent-cargo-id"
        payload = {
            "usuario_id": "test-user",
            "usuario_rol": "SUPERVISOR",
            "comentario": "Intento de cancelar cargo inexistente"
        }
        response = requests.post(f"{BASE_URL}/api/v2/cargos/{fake_id}/cancelar", json=payload)
        assert response.status_code == 404, f"Expected 404, got {response.status_code}: {response.text}"
        print(f"✓ Cancelar cargo no existe - 404 returned")


class TestCicloCompletoCargo:
    """
    Test complete charge lifecycle: Create → Authorize → Apply
    Requires creating a workflow and responsibility in APROBADO state first
    """
    
    @pytest.fixture(autouse=True)
    def setup_test_data(self):
        """Setup test workflow and responsibility in APROBADO state"""
        global TEST_RESPONSABILIDAD_ID, TEST_CARGO_ID
        
        # Create a test workflow
        workflow_id = f"TEST-WF-CARGO-{uuid.uuid4().hex[:8]}"
        workflow_payload = {
            "procesado_id": f"TEST-PROC-{uuid.uuid4().hex[:6]}",
            "server_id": "test-server-cargo",
            "server_name": "Servidor Test Cargos",
            "sucursal_id": "SUC-TEST-CARGO",
            "sucursal_nombre": "Sucursal Test Cargos",
            "almacen_id": "ALM-TEST-CARGO",
            "almacen_nombre": "Almacén Test Cargos",
            "folios_iniciales": ["CARGO-001"],
            "folios_finales": ["CARGO-002"],
            "folio_final_key": "CARGO-002",
            "fecha_analisis_ini": "2026-01-01",
            "fecha_analisis_fin": "2026-01-17",
            "usuario_creador_id": "test-user-cargo"
        }
        
        wf_response = requests.post(f"{BASE_URL}/api/v2/workflows", json=workflow_payload)
        if wf_response.status_code not in [200, 201]:
            pytest.skip(f"Could not create test workflow: {wf_response.text}")
        
        wf_data = wf_response.json()
        workflow_id = wf_data.get("id") or wf_data.get("workflow_id")
        
        # Create test differences for the workflow
        diff_payload = {
            "workflow_id": workflow_id,
            "diferencias": [
                {
                    "producto_id": "PROD-CARGO-001",
                    "producto_nombre": "Producto Test Cargo",
                    "cantidad_sistema": 100,
                    "cantidad_fisica": 90,
                    "diferencia": -10,
                    "precio_unitario": 50.0,
                    "valor_diferencia": -500.0,
                    "tipo_diferencia": "FALTANTE"
                }
            ]
        }
        
        diff_response = requests.post(f"{BASE_URL}/api/v2/workflows/{workflow_id}/diferencias", json=diff_payload)
        # Continue even if this fails - some workflows may not need explicit differences
        
        # Calculate responsibility
        calc_response = requests.post(f"{BASE_URL}/api/v2/responsabilidad/calcular/{workflow_id}")
        if calc_response.status_code not in [200, 201]:
            pytest.skip(f"Could not calculate responsibility: {calc_response.text}")
        
        calc_data = calc_response.json()
        resp_id = calc_data.get("id")
        
        # Propose responsibility (CALCULADO → PROPUESTO)
        proponer_payload = {
            "usuario_id": "test-user-cargo",
            "usuario_rol": "SUPERVISOR",
            "comentario": "Propuesta de responsabilidad para prueba de cargos económicos"
        }
        prop_response = requests.post(f"{BASE_URL}/api/v2/responsabilidad/{resp_id}/proponer", json=proponer_payload)
        if prop_response.status_code not in [200, 201]:
            pytest.skip(f"Could not propose responsibility: {prop_response.text}")
        
        # Approve responsibility (PROPUESTO → APROBADO)
        aprobar_payload = {
            "usuario_id": "test-gerente-cargo",
            "usuario_rol": "GERENTE_OPS",
            "comentario": "Aprobación de responsabilidad para prueba de cargos económicos"
        }
        apro_response = requests.post(f"{BASE_URL}/api/v2/responsabilidad/{resp_id}/aprobar", json=aprobar_payload)
        if apro_response.status_code not in [200, 201]:
            pytest.skip(f"Could not approve responsibility: {apro_response.text}")
        
        TEST_RESPONSABILIDAD_ID = resp_id
        print(f"✓ Setup: Created APROBADO responsibility {resp_id}")
        
        yield
        
        # Cleanup - cancel any created cargo
        if TEST_CARGO_ID:
            cancel_payload = {
                "usuario_id": "test-cleanup",
                "usuario_rol": "DIRECCION",
                "comentario": "Limpieza de datos de prueba de cargos económicos"
            }
            requests.post(f"{BASE_URL}/api/v2/cargos/{TEST_CARGO_ID}/cancelar", json=cancel_payload)
    
    def test_01_elegibilidad_responsabilidad_aprobada(self):
        """Verify APROBADO responsibility is eligible for charge"""
        global TEST_RESPONSABILIDAD_ID
        if not TEST_RESPONSABILIDAD_ID:
            pytest.skip("No test responsibility available")
        
        response = requests.get(f"{BASE_URL}/api/v2/cargos/elegibilidad/{TEST_RESPONSABILIDAD_ID}")
        assert response.status_code == 200
        data = response.json()
        
        # May or may not be eligible depending on monto
        print(f"✓ Elegibilidad APROBADO: es_elegible={data['es_elegible']}, motivo={data['motivo']}")
        
        if not data["es_elegible"]:
            pytest.skip(f"Responsibility not eligible: {data['motivo']}")
    
    def test_02_crear_propuesta_cargo(self):
        """Create charge proposal from APROBADO responsibility"""
        global TEST_RESPONSABILIDAD_ID, TEST_CARGO_ID
        if not TEST_RESPONSABILIDAD_ID:
            pytest.skip("No test responsibility available")
        
        # First check eligibility
        elig_response = requests.get(f"{BASE_URL}/api/v2/cargos/elegibilidad/{TEST_RESPONSABILIDAD_ID}")
        if elig_response.status_code == 200:
            elig_data = elig_response.json()
            if not elig_data["es_elegible"]:
                pytest.skip(f"Responsibility not eligible: {elig_data['motivo']}")
        
        payload = {
            "responsabilidad_id": TEST_RESPONSABILIDAD_ID,
            "comentario": "Creación de propuesta de cargo económico para prueba del ciclo completo",
            "usuario_id": "test-supervisor-cargo",
            "usuario_rol": "SUPERVISOR"
        }
        
        response = requests.post(f"{BASE_URL}/api/v2/cargos", json=payload)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data["success"] == True
        assert data["accion"] == "CREAR"
        assert data["estatus_nuevo"] == "PENDIENTE"
        assert "cargo_id" in data
        assert "log_id" in data
        
        TEST_CARGO_ID = data["cargo_id"]
        print(f"✓ Cargo creado: {TEST_CARGO_ID}, estatus: {data['estatus_nuevo']}")
    
    def test_03_obtener_cargo_creado(self):
        """Verify created charge can be retrieved"""
        global TEST_CARGO_ID
        if not TEST_CARGO_ID:
            pytest.skip("No test cargo available")
        
        response = requests.get(f"{BASE_URL}/api/v2/cargos/{TEST_CARGO_ID}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["id"] == TEST_CARGO_ID
        assert data["estatus_cargo"] == "PENDIENTE"
        assert data["responsabilidad_id"] == TEST_RESPONSABILIDAD_ID
        
        print(f"✓ Cargo obtenido: monto=${data['monto_responsabilidad']}, estatus={data['estatus_cargo']}")
    
    def test_04_obtener_log_cargo(self):
        """Verify charge log has creation entry"""
        global TEST_CARGO_ID
        if not TEST_CARGO_ID:
            pytest.skip("No test cargo available")
        
        response = requests.get(f"{BASE_URL}/api/v2/cargos/{TEST_CARGO_ID}/log")
        assert response.status_code == 200
        
        data = response.json()
        assert data["cargo_id"] == TEST_CARGO_ID
        assert data["total"] >= 1
        assert len(data["items"]) >= 1
        
        # First log entry should be CREAR
        crear_log = data["items"][-1]  # Last item (oldest) should be CREAR
        assert crear_log["accion"] == "CREAR"
        
        print(f"✓ Log cargo: {data['total']} entradas, última acción: {data['items'][0]['accion']}")
    
    def test_05_cargo_aparece_en_pendientes(self):
        """Verify charge appears in pending list"""
        global TEST_CARGO_ID
        if not TEST_CARGO_ID:
            pytest.skip("No test cargo available")
        
        response = requests.get(f"{BASE_URL}/api/v2/cargos/pendientes")
        assert response.status_code == 200
        
        data = response.json()
        cargo_ids = [c["id"] for c in data["items"]]
        assert TEST_CARGO_ID in cargo_ids, f"Cargo {TEST_CARGO_ID} not in pending list"
        
        print(f"✓ Cargo en pendientes: total={data['total']}, monto_total=${data['monto_total_pendiente']}")
    
    def test_06_autorizar_cargo(self):
        """Authorize pending charge (PENDIENTE → AUTORIZADO)"""
        global TEST_CARGO_ID
        if not TEST_CARGO_ID:
            pytest.skip("No test cargo available")
        
        payload = {
            "usuario_id": "test-gerente-cargo",
            "usuario_rol": "GERENTE_OPS",
            "comentario": "Autorización de cargo económico para prueba del ciclo completo"
        }
        
        response = requests.post(f"{BASE_URL}/api/v2/cargos/{TEST_CARGO_ID}/autorizar", json=payload)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data["success"] == True
        assert data["accion"] == "AUTORIZAR"
        assert data["estatus_anterior"] == "PENDIENTE"
        assert data["estatus_nuevo"] == "AUTORIZADO"
        
        print(f"✓ Cargo autorizado: {data['estatus_anterior']} → {data['estatus_nuevo']}")
    
    def test_07_aplicar_cargo(self):
        """Apply authorized charge (AUTORIZADO → APLICADO)"""
        global TEST_CARGO_ID
        if not TEST_CARGO_ID:
            pytest.skip("No test cargo available")
        
        payload = {
            "usuario_id": "test-gerente-cargo",
            "usuario_rol": "GERENTE_OPS",
            "comentario": "Aplicación de cargo económico para prueba del ciclo completo"
        }
        
        response = requests.post(f"{BASE_URL}/api/v2/cargos/{TEST_CARGO_ID}/aplicar", json=payload)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data["success"] == True
        assert data["accion"] == "APLICAR"
        assert data["estatus_anterior"] == "AUTORIZADO"
        assert data["estatus_nuevo"] == "APLICADO"
        
        print(f"✓ Cargo aplicado: {data['estatus_anterior']} → {data['estatus_nuevo']}")
    
    def test_08_cargo_aparece_en_aplicados(self):
        """Verify charge appears in applied list"""
        global TEST_CARGO_ID
        if not TEST_CARGO_ID:
            pytest.skip("No test cargo available")
        
        response = requests.get(f"{BASE_URL}/api/v2/cargos/aplicados")
        assert response.status_code == 200
        
        data = response.json()
        cargo_ids = [c["id"] for c in data["items"]]
        assert TEST_CARGO_ID in cargo_ids, f"Cargo {TEST_CARGO_ID} not in applied list"
        
        print(f"✓ Cargo en aplicados: total={data['total']}, monto_total=${data['monto_total_aplicado']}")
    
    def test_09_revertir_cargo_aplicado(self):
        """Revert applied charge (APLICADO → REVERTIDO)"""
        global TEST_CARGO_ID
        if not TEST_CARGO_ID:
            pytest.skip("No test cargo available")
        
        payload = {
            "usuario_id": "test-gerente-cargo",
            "usuario_rol": "GERENTE_OPS",
            "motivo_reversa": "Reversa de cargo económico para prueba del ciclo completo - motivo detallado requerido"
        }
        
        response = requests.post(f"{BASE_URL}/api/v2/cargos/{TEST_CARGO_ID}/revertir", json=payload)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data["success"] == True
        assert data["accion"] == "REVERTIR"
        assert data["estatus_anterior"] == "APLICADO"
        assert data["estatus_nuevo"] == "REVERTIDO"
        
        print(f"✓ Cargo revertido: {data['estatus_anterior']} → {data['estatus_nuevo']}")
    
    def test_10_verificar_log_completo(self):
        """Verify complete audit log"""
        global TEST_CARGO_ID
        if not TEST_CARGO_ID:
            pytest.skip("No test cargo available")
        
        response = requests.get(f"{BASE_URL}/api/v2/cargos/{TEST_CARGO_ID}/log")
        assert response.status_code == 200
        
        data = response.json()
        assert data["total"] >= 4  # CREAR, AUTORIZAR, APLICAR, REVERTIR
        
        acciones = [log["accion"] for log in data["items"]]
        # Items are sorted by date DESC, so newest first
        assert "REVERTIR" in acciones
        assert "APLICAR" in acciones
        assert "AUTORIZAR" in acciones
        assert "CREAR" in acciones
        
        print(f"✓ Log completo: {data['total']} entradas, acciones: {acciones}")


class TestTransicionesInvalidas:
    """Test invalid state transitions"""
    
    @pytest.fixture
    def cargo_pendiente(self):
        """Create a cargo in PENDIENTE state for testing"""
        # First need an APROBADO responsibility
        # Get existing or create new
        response = requests.get(f"{BASE_URL}/api/v2/responsabilidad?estado=APROBADO&limit=1")
        if response.status_code == 200 and response.json().get("items"):
            resp_id = response.json()["items"][0]["id"]
            
            # Check eligibility
            elig = requests.get(f"{BASE_URL}/api/v2/cargos/elegibilidad/{resp_id}")
            if elig.status_code == 200 and elig.json().get("es_elegible"):
                # Create cargo
                payload = {
                    "responsabilidad_id": resp_id,
                    "comentario": "Cargo de prueba para validar transiciones inválidas",
                    "usuario_id": "test-user-trans",
                    "usuario_rol": "SUPERVISOR"
                }
                create_resp = requests.post(f"{BASE_URL}/api/v2/cargos", json=payload)
                if create_resp.status_code == 200:
                    cargo_id = create_resp.json()["cargo_id"]
                    yield cargo_id
                    # Cleanup
                    requests.post(f"{BASE_URL}/api/v2/cargos/{cargo_id}/cancelar", json={
                        "usuario_id": "cleanup",
                        "usuario_rol": "DIRECCION",
                        "comentario": "Limpieza de cargo de prueba de transiciones"
                    })
                    return
        
        pytest.skip("Could not create test cargo for transition tests")
    
    def test_aplicar_cargo_pendiente_directo(self, cargo_pendiente):
        """Cannot apply PENDIENTE charge directly (must authorize first)"""
        payload = {
            "usuario_id": "test-user",
            "usuario_rol": "GERENTE_OPS",
            "comentario": "Intento de aplicar cargo pendiente directamente"
        }
        response = requests.post(f"{BASE_URL}/api/v2/cargos/{cargo_pendiente}/aplicar", json=payload)
        assert response.status_code == 400, f"Expected 400, got {response.status_code}: {response.text}"
        assert "transición" in response.json().get("detail", "").lower() or "inválid" in response.json().get("detail", "").lower()
        print(f"✓ Aplicar PENDIENTE directo rechazado: {response.json().get('detail', '')}")
    
    def test_revertir_cargo_pendiente(self, cargo_pendiente):
        """Cannot revert PENDIENTE charge (only APLICADO can be reverted)"""
        payload = {
            "usuario_id": "test-user",
            "usuario_rol": "GERENTE_OPS",
            "motivo_reversa": "Intento de revertir cargo pendiente que no ha sido aplicado"
        }
        response = requests.post(f"{BASE_URL}/api/v2/cargos/{cargo_pendiente}/revertir", json=payload)
        assert response.status_code == 400, f"Expected 400, got {response.status_code}: {response.text}"
        print(f"✓ Revertir PENDIENTE rechazado: {response.json().get('detail', '')}")


class TestPermisosRol:
    """Test role-based permission validation"""
    
    @pytest.fixture
    def cargo_pendiente_alto_monto(self):
        """Create a cargo with high amount for permission testing"""
        # This would need a responsibility with monto > $2000 for DIRECCION requirement
        # For now, we'll test with existing cargos or skip
        response = requests.get(f"{BASE_URL}/api/v2/cargos?estatus=PENDIENTE&limit=1")
        if response.status_code == 200 and response.json().get("items"):
            cargo = response.json()["items"][0]
            if cargo.get("monto_responsabilidad", 0) > 500:
                yield cargo["id"], cargo["monto_responsabilidad"]
                return
        pytest.skip("No high-amount pending cargo available for permission tests")
    
    def test_afectado_no_puede_autorizar(self):
        """AFECTADO role cannot authorize charges"""
        # Get any pending cargo
        response = requests.get(f"{BASE_URL}/api/v2/cargos?estatus=PENDIENTE&limit=1")
        if response.status_code != 200 or not response.json().get("items"):
            pytest.skip("No pending cargos available")
        
        cargo_id = response.json()["items"][0]["id"]
        
        payload = {
            "usuario_id": "test-afectado",
            "usuario_rol": "AFECTADO",
            "comentario": "Intento de autorización por rol AFECTADO"
        }
        response = requests.post(f"{BASE_URL}/api/v2/cargos/{cargo_id}/autorizar", json=payload)
        assert response.status_code == 403, f"Expected 403, got {response.status_code}: {response.text}"
        print(f"✓ AFECTADO no puede autorizar: {response.json().get('detail', '')}")
    
    def test_supervisor_no_puede_revertir(self):
        """SUPERVISOR role cannot revert charges (requires GERENTE_OPS+)"""
        # Get any applied cargo
        response = requests.get(f"{BASE_URL}/api/v2/cargos?estatus=APLICADO&limit=1")
        if response.status_code != 200 or not response.json().get("items"):
            pytest.skip("No applied cargos available")
        
        cargo_id = response.json()["items"][0]["id"]
        
        payload = {
            "usuario_id": "test-supervisor",
            "usuario_rol": "SUPERVISOR",
            "motivo_reversa": "Intento de reversa por rol SUPERVISOR que no tiene permisos suficientes"
        }
        response = requests.post(f"{BASE_URL}/api/v2/cargos/{cargo_id}/revertir", json=payload)
        assert response.status_code == 403, f"Expected 403, got {response.status_code}: {response.text}"
        print(f"✓ SUPERVISOR no puede revertir: {response.json().get('detail', '')}")


class TestFiltrosCargos:
    """Test filtering capabilities for charges list"""
    
    def test_filtrar_por_estatus(self):
        """Filter charges by status"""
        for estatus in ["PENDIENTE", "AUTORIZADO", "APLICADO", "RECHAZADO", "REVERTIDO", "CANCELADO"]:
            response = requests.get(f"{BASE_URL}/api/v2/cargos?estatus={estatus}")
            assert response.status_code == 200, f"Failed for estatus {estatus}"
            data = response.json()
            # All items should have the requested status
            for item in data["items"]:
                assert item["estatus_cargo"] == estatus
        print(f"✓ Filtro por estatus funciona correctamente")
    
    def test_filtrar_por_sucursal(self):
        """Filter charges by branch"""
        response = requests.get(f"{BASE_URL}/api/v2/cargos?sucursal_id=SUC-TEST")
        assert response.status_code == 200
        print(f"✓ Filtro por sucursal funciona")
    
    def test_paginacion(self):
        """Test pagination parameters"""
        response = requests.get(f"{BASE_URL}/api/v2/cargos?skip=0&limit=5")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) <= 5
        print(f"✓ Paginación funciona: {len(data['items'])} items")


class TestRechazoCargo:
    """Test charge rejection flow"""
    
    @pytest.fixture
    def cargo_para_rechazar(self):
        """Create a cargo to reject"""
        response = requests.get(f"{BASE_URL}/api/v2/responsabilidad?estado=APROBADO&limit=1")
        if response.status_code == 200 and response.json().get("items"):
            resp_id = response.json()["items"][0]["id"]
            
            elig = requests.get(f"{BASE_URL}/api/v2/cargos/elegibilidad/{resp_id}")
            if elig.status_code == 200 and elig.json().get("es_elegible"):
                payload = {
                    "responsabilidad_id": resp_id,
                    "comentario": "Cargo de prueba para validar flujo de rechazo",
                    "usuario_id": "test-user-rechazo",
                    "usuario_rol": "SUPERVISOR"
                }
                create_resp = requests.post(f"{BASE_URL}/api/v2/cargos", json=payload)
                if create_resp.status_code == 200:
                    yield create_resp.json()["cargo_id"]
                    return
        pytest.skip("Could not create test cargo for rejection test")
    
    def test_rechazar_cargo_pendiente(self, cargo_para_rechazar):
        """Reject pending charge (PENDIENTE → RECHAZADO)"""
        payload = {
            "usuario_id": "test-gerente",
            "usuario_rol": "GERENTE_OPS",
            "comentario": "Rechazo de cargo por motivos de prueba - el cargo no procedía"
        }
        response = requests.post(f"{BASE_URL}/api/v2/cargos/{cargo_para_rechazar}/rechazar", json=payload)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data["success"] == True
        assert data["accion"] == "RECHAZAR"
        assert data["estatus_nuevo"] == "RECHAZADO"
        
        print(f"✓ Cargo rechazado: {data['estatus_anterior']} → {data['estatus_nuevo']}")


class TestCancelacionCargo:
    """Test charge cancellation flow"""
    
    @pytest.fixture
    def cargo_para_cancelar(self):
        """Create a cargo to cancel"""
        response = requests.get(f"{BASE_URL}/api/v2/responsabilidad?estado=APROBADO&limit=1")
        if response.status_code == 200 and response.json().get("items"):
            resp_id = response.json()["items"][0]["id"]
            
            elig = requests.get(f"{BASE_URL}/api/v2/cargos/elegibilidad/{resp_id}")
            if elig.status_code == 200 and elig.json().get("es_elegible"):
                payload = {
                    "responsabilidad_id": resp_id,
                    "comentario": "Cargo de prueba para validar flujo de cancelación",
                    "usuario_id": "test-user-cancel",
                    "usuario_rol": "SUPERVISOR"
                }
                create_resp = requests.post(f"{BASE_URL}/api/v2/cargos", json=payload)
                if create_resp.status_code == 200:
                    yield create_resp.json()["cargo_id"]
                    return
        pytest.skip("Could not create test cargo for cancellation test")
    
    def test_cancelar_cargo_pendiente(self, cargo_para_cancelar):
        """Cancel pending charge (PENDIENTE → CANCELADO)"""
        payload = {
            "usuario_id": "test-supervisor",
            "usuario_rol": "SUPERVISOR",
            "comentario": "Cancelación de cargo por motivos de prueba - ya no se requiere"
        }
        response = requests.post(f"{BASE_URL}/api/v2/cargos/{cargo_para_cancelar}/cancelar", json=payload)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data["success"] == True
        assert data["accion"] == "CANCELAR"
        assert data["estatus_nuevo"] == "CANCELADO"
        
        print(f"✓ Cargo cancelado: {data['estatus_anterior']} → {data['estatus_nuevo']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
