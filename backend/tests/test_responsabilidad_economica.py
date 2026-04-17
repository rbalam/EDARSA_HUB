"""
Test Suite for Responsabilidad Económica Module (Fase 2C.1)
CAB-003 | EDARSA HUB

Tests the economic responsibility calculation for inventory differences:
- Calculation of faltantes (shortages) and sobrantes (surpluses)
- Tolerance application (units and percentage)
- Minimum charge threshold
- Configuration management
- Workflow state transitions
"""
import pytest
import requests
import os
import uuid
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "admin@inventario.com"
ADMIN_PASSWORD = "admin123"


class TestAuthAndHealth:
    """Basic authentication and health check tests"""
    
    def test_health_check(self):
        """Test that the API health endpoint is working"""
        response = requests.get(f"{BASE_URL}/api/v2/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["module"] == "fase2_operativo"
        print("✓ Health check passed")
    
    def test_auth_login(self):
        """Test authentication with admin credentials"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert "user" in data
        assert data["user"]["email"] == ADMIN_EMAIL
        print("✓ Auth login passed")


class TestResponsabilidadConfiguracion:
    """Tests for configuration endpoints"""
    
    def test_get_configuracion(self):
        """Test GET /api/v2/responsabilidad/configuracion returns current config"""
        response = requests.get(f"{BASE_URL}/api/v2/responsabilidad/configuracion")
        assert response.status_code == 200
        data = response.json()
        
        # Verify all expected fields are present
        assert "cargo_minimo_mxn" in data
        assert "tolerancia_unidades" in data
        assert "tolerancia_porcentaje_diferencia" in data
        assert "precio_faltante_default" in data
        assert "modulo_responsabilidad_activo" in data
        assert "permitir_compensacion_faltantes_sobrantes" in data
        
        # Verify types
        assert isinstance(data["cargo_minimo_mxn"], (int, float))
        assert isinstance(data["tolerancia_unidades"], int)
        assert isinstance(data["tolerancia_porcentaje_diferencia"], (int, float))
        assert isinstance(data["modulo_responsabilidad_activo"], bool)
        assert isinstance(data["permitir_compensacion_faltantes_sobrantes"], bool)
        
        # Verify default: compensacion should be false
        assert data["permitir_compensacion_faltantes_sobrantes"] == False
        
        print(f"✓ GET configuracion passed - cargo_minimo: {data['cargo_minimo_mxn']}, tolerancia_unidades: {data['tolerancia_unidades']}")
    
    def test_put_configuracion_update_and_persist(self):
        """Test PUT /api/v2/responsabilidad/configuracion updates and persists"""
        # Get current config
        response = requests.get(f"{BASE_URL}/api/v2/responsabilidad/configuracion")
        original_config = response.json()
        
        # Update with new values
        new_cargo_minimo = 75.0
        update_response = requests.put(
            f"{BASE_URL}/api/v2/responsabilidad/configuracion",
            json={"cargo_minimo_mxn": new_cargo_minimo}
        )
        assert update_response.status_code == 200
        updated_data = update_response.json()
        assert updated_data["cargo_minimo_mxn"] == new_cargo_minimo
        
        # Verify persistence by fetching again
        verify_response = requests.get(f"{BASE_URL}/api/v2/responsabilidad/configuracion")
        verify_data = verify_response.json()
        assert verify_data["cargo_minimo_mxn"] == new_cargo_minimo
        
        # Restore original value
        restore_response = requests.put(
            f"{BASE_URL}/api/v2/responsabilidad/configuracion",
            json={"cargo_minimo_mxn": original_config["cargo_minimo_mxn"]}
        )
        assert restore_response.status_code == 200
        
        print(f"✓ PUT configuracion passed - updated cargo_minimo to {new_cargo_minimo} and restored")
    
    def test_put_configuracion_tolerancia(self):
        """Test updating tolerance configuration"""
        # Get current config
        response = requests.get(f"{BASE_URL}/api/v2/responsabilidad/configuracion")
        original_config = response.json()
        
        # Update tolerancia
        new_tolerancia = 5
        update_response = requests.put(
            f"{BASE_URL}/api/v2/responsabilidad/configuracion",
            json={"tolerancia_unidades": new_tolerancia}
        )
        assert update_response.status_code == 200
        assert update_response.json()["tolerancia_unidades"] == new_tolerancia
        
        # Restore
        requests.put(
            f"{BASE_URL}/api/v2/responsabilidad/configuracion",
            json={"tolerancia_unidades": original_config["tolerancia_unidades"]}
        )
        
        print(f"✓ PUT configuracion tolerancia passed")


class TestResponsabilidadListar:
    """Tests for listing responsabilidad records"""
    
    def test_get_responsabilidad_list(self):
        """Test GET /api/v2/responsabilidad returns list of calculations"""
        response = requests.get(f"{BASE_URL}/api/v2/responsabilidad")
        assert response.status_code == 200
        data = response.json()
        
        assert "items" in data
        assert "total" in data
        assert isinstance(data["items"], list)
        assert isinstance(data["total"], int)
        
        print(f"✓ GET responsabilidad list passed - total: {data['total']}")
    
    def test_get_responsabilidad_list_with_filters(self):
        """Test GET /api/v2/responsabilidad with filters"""
        # Test with excede_minimo filter
        response = requests.get(f"{BASE_URL}/api/v2/responsabilidad?excede_minimo=true")
        assert response.status_code == 200
        data = response.json()
        
        # All items should have excede_minimo=true
        for item in data["items"]:
            assert item["excede_minimo"] == True
        
        print(f"✓ GET responsabilidad with filters passed - found {len(data['items'])} items with excede_minimo=true")
    
    def test_get_responsabilidad_pagination(self):
        """Test pagination parameters"""
        response = requests.get(f"{BASE_URL}/api/v2/responsabilidad?skip=0&limit=2")
        assert response.status_code == 200
        data = response.json()
        
        assert len(data["items"]) <= 2
        print(f"✓ GET responsabilidad pagination passed")


class TestResponsabilidadPorWorkflow:
    """Tests for getting responsabilidad by workflow"""
    
    def test_get_responsabilidad_by_workflow_existing(self):
        """Test GET /api/v2/responsabilidad/workflow/{workflow_id} for existing calculation"""
        # First get a workflow that has a calculation
        list_response = requests.get(f"{BASE_URL}/api/v2/responsabilidad")
        items = list_response.json()["items"]
        
        if len(items) > 0:
            workflow_id = items[0]["workflow_id"]
            
            response = requests.get(f"{BASE_URL}/api/v2/responsabilidad/workflow/{workflow_id}")
            assert response.status_code == 200
            data = response.json()
            
            # Verify structure
            assert data["workflow_id"] == workflow_id
            assert "faltantes" in data
            assert "sobrantes" in data
            assert "tolerancia" in data
            assert "monto_propuesto_mxn" in data
            assert "excede_minimo" in data
            assert "estado" in data
            assert data["estado"] == "CALCULADO"
            
            print(f"✓ GET responsabilidad by workflow passed - workflow: {workflow_id}")
        else:
            pytest.skip("No existing calculations to test")
    
    def test_get_responsabilidad_by_workflow_not_found(self):
        """Test GET /api/v2/responsabilidad/workflow/{workflow_id} for non-existing"""
        fake_workflow_id = str(uuid.uuid4())
        response = requests.get(f"{BASE_URL}/api/v2/responsabilidad/workflow/{fake_workflow_id}")
        assert response.status_code == 404
        print(f"✓ GET responsabilidad by non-existing workflow returns 404")


class TestResponsabilidadCalculo:
    """Tests for calculation endpoint"""
    
    def test_calcular_workflow_con_faltantes_grandes(self):
        """Test calculation for workflow with large faltantes (excede_minimo=true)"""
        # Get existing calculation with excede_minimo=true
        list_response = requests.get(f"{BASE_URL}/api/v2/responsabilidad?excede_minimo=true")
        items = list_response.json()["items"]
        
        if len(items) > 0:
            item = items[0]
            
            # Verify the calculation has correct structure
            assert item["excede_minimo"] == True
            assert item["monto_propuesto_mxn"] > 0
            assert item["faltantes"]["valor_mxn"] > 0
            assert item["estado"] == "CALCULADO"
            
            # Verify workflow state
            workflow_response = requests.get(f"{BASE_URL}/api/v2/workflows/{item['workflow_id']}")
            if workflow_response.status_code == 200:
                workflow = workflow_response.json()
                assert workflow["estado_workflow"] == "EN_REVISION_FINANCIERA"
            
            print(f"✓ Workflow con faltantes grandes: monto_propuesto={item['monto_propuesto_mxn']}, excede_minimo=True")
        else:
            pytest.skip("No workflow with large faltantes found")
    
    def test_calcular_workflow_con_faltantes_menores_minimo(self):
        """Test calculation for workflow with faltantes below minimum (excede_minimo=false)"""
        # Get existing calculation with excede_minimo=false
        list_response = requests.get(f"{BASE_URL}/api/v2/responsabilidad?excede_minimo=false")
        items = list_response.json()["items"]
        
        if len(items) > 0:
            item = items[0]
            
            # Verify the calculation
            assert item["excede_minimo"] == False
            # monto_propuesto could be 0 or below cargo_minimo
            assert item["monto_propuesto_mxn"] < item["cargo_minimo_configurado_mxn"]
            assert item["estado"] == "CALCULADO"
            
            print(f"✓ Workflow con faltantes menores: monto_propuesto={item['monto_propuesto_mxn']}, cargo_minimo={item['cargo_minimo_configurado_mxn']}")
        else:
            pytest.skip("No workflow with small faltantes found")
    
    def test_calcular_workflow_solo_sobrantes(self):
        """Test calculation for workflow with only sobrantes (monto_propuesto=0)"""
        # Find a calculation with only sobrantes
        list_response = requests.get(f"{BASE_URL}/api/v2/responsabilidad")
        items = list_response.json()["items"]
        
        sobrantes_only = [i for i in items if i["faltantes"]["cantidad_items"] == 0 and i["sobrantes"]["cantidad_items"] > 0]
        
        if len(sobrantes_only) > 0:
            item = sobrantes_only[0]
            
            # Verify: sobrantes registered but monto_propuesto=0
            assert item["sobrantes"]["cantidad_items"] > 0
            assert item["sobrantes"]["valor_mxn"] > 0
            assert item["faltantes"]["cantidad_items"] == 0
            assert item["monto_propuesto_mxn"] == 0.0
            
            print(f"✓ Workflow solo sobrantes: sobrantes_valor={item['sobrantes']['valor_mxn']}, monto_propuesto=0")
        else:
            pytest.skip("No workflow with only sobrantes found")
    
    def test_sobrantes_no_compensan_faltantes(self):
        """Test that sobrantes do NOT compensate faltantes by default"""
        # Find a calculation with both faltantes and sobrantes
        list_response = requests.get(f"{BASE_URL}/api/v2/responsabilidad")
        items = list_response.json()["items"]
        
        mixed = [i for i in items if i["faltantes"]["cantidad_items"] > 0 and i["sobrantes"]["cantidad_items"] > 0]
        
        if len(mixed) > 0:
            item = mixed[0]
            
            # monto_propuesto should be based on faltantes only, not reduced by sobrantes
            # monto_propuesto = faltantes_valor - valor_excluido_por_tolerancia
            expected_monto = item["faltantes"]["valor_mxn"] - item["tolerancia"]["valor_excluido_por_tolerancia_mxn"]
            expected_monto = max(0, expected_monto)
            
            # Allow small floating point differences
            assert abs(item["monto_propuesto_mxn"] - expected_monto) < 0.01, \
                f"monto_propuesto ({item['monto_propuesto_mxn']}) should equal faltantes - tolerancia ({expected_monto}), not reduced by sobrantes"
            
            print(f"✓ Sobrantes NO compensan faltantes: faltantes={item['faltantes']['valor_mxn']}, sobrantes={item['sobrantes']['valor_mxn']}, monto_propuesto={item['monto_propuesto_mxn']}")
        else:
            pytest.skip("No workflow with both faltantes and sobrantes found")
    
    def test_tolerancia_aplicada(self):
        """Test that tolerance is correctly applied"""
        # Find a calculation with items within tolerance
        list_response = requests.get(f"{BASE_URL}/api/v2/responsabilidad")
        items = list_response.json()["items"]
        
        with_tolerance = [i for i in items if i["tolerancia"]["diferencias_dentro_tolerancia"] > 0]
        
        if len(with_tolerance) > 0:
            item = with_tolerance[0]
            
            # Verify tolerance structure
            assert item["tolerancia"]["tolerancia_unidades"] >= 0
            assert item["tolerancia"]["tolerancia_porcentaje"] >= 0
            assert item["tolerancia"]["diferencias_dentro_tolerancia"] > 0
            
            # If there's excluded value, it should reduce monto_propuesto
            if item["tolerancia"]["valor_excluido_por_tolerancia_mxn"] > 0:
                assert item["monto_propuesto_mxn"] < item["faltantes"]["valor_mxn"]
            
            print(f"✓ Tolerancia aplicada: dentro={item['tolerancia']['diferencias_dentro_tolerancia']}, fuera={item['tolerancia']['diferencias_fuera_tolerancia']}, excluido={item['tolerancia']['valor_excluido_por_tolerancia_mxn']}")
        else:
            pytest.skip("No calculation with items within tolerance found")


class TestResponsabilidadCalcularEndpoint:
    """Tests for POST /api/v2/responsabilidad/calcular/{workflow_id}"""
    
    def test_calcular_requires_usuario_id(self):
        """Test that calcular endpoint requires usuario_id query param"""
        fake_workflow_id = str(uuid.uuid4())
        
        # Without usuario_id should fail
        response = requests.post(f"{BASE_URL}/api/v2/responsabilidad/calcular/{fake_workflow_id}")
        assert response.status_code == 422  # Validation error
        
        print("✓ Calcular requires usuario_id parameter")
    
    def test_calcular_workflow_not_found(self):
        """Test calcular with non-existing workflow returns 404"""
        fake_workflow_id = str(uuid.uuid4())
        
        response = requests.post(
            f"{BASE_URL}/api/v2/responsabilidad/calcular/{fake_workflow_id}?usuario_id=test-user"
        )
        assert response.status_code == 404
        
        print("✓ Calcular with non-existing workflow returns 404")
    
    def test_calcular_already_exists_returns_409(self):
        """Test calcular for workflow that already has calculation returns 409"""
        # Get an existing calculation
        list_response = requests.get(f"{BASE_URL}/api/v2/responsabilidad")
        items = list_response.json()["items"]
        
        if len(items) > 0:
            workflow_id = items[0]["workflow_id"]
            
            # Try to calculate again without forzar_recalculo
            response = requests.post(
                f"{BASE_URL}/api/v2/responsabilidad/calcular/{workflow_id}?usuario_id=test-user"
            )
            assert response.status_code == 409  # Conflict - already exists
            
            print("✓ Calcular for existing calculation returns 409")
        else:
            pytest.skip("No existing calculations to test")
    
    def test_calcular_forzar_recalculo(self):
        """Test calcular with forzar_recalculo=true recalculates"""
        # Get an existing calculation
        list_response = requests.get(f"{BASE_URL}/api/v2/responsabilidad")
        items = list_response.json()["items"]
        
        if len(items) > 0:
            workflow_id = items[0]["workflow_id"]
            original_fecha = items[0]["fecha_calculo"]
            
            # Recalculate with forzar_recalculo
            response = requests.post(
                f"{BASE_URL}/api/v2/responsabilidad/calcular/{workflow_id}?usuario_id=test-recalculo&forzar_recalculo=true"
            )
            assert response.status_code == 200
            data = response.json()
            
            # Verify response structure
            assert data["workflow_id"] == workflow_id
            assert data["estado"] == "CALCULADO"
            assert "monto_propuesto_mxn" in data
            assert "excede_minimo" in data
            assert data["workflow_estado_nuevo"] == "EN_REVISION_FINANCIERA"
            
            print(f"✓ Calcular with forzar_recalculo passed - workflow: {workflow_id}")
        else:
            pytest.skip("No existing calculations to test recalculation")


class TestWorkflowStateTransition:
    """Tests for workflow state transition after calculation"""
    
    def test_workflow_estado_en_revision_financiera(self):
        """Test that workflow transitions to EN_REVISION_FINANCIERA after calculation"""
        # Get workflows
        workflows_response = requests.get(f"{BASE_URL}/api/v2/workflows")
        workflows = workflows_response.json()["items"]
        
        # Get responsabilidades
        resp_response = requests.get(f"{BASE_URL}/api/v2/responsabilidad")
        responsabilidades = resp_response.json()["items"]
        
        # For each responsabilidad, verify the workflow is in EN_REVISION_FINANCIERA
        for resp in responsabilidades:
            workflow = next((w for w in workflows if w.get("id") == resp["workflow_id"]), None)
            if workflow:
                assert workflow["estado_workflow"] == "EN_REVISION_FINANCIERA", \
                    f"Workflow {resp['workflow_id']} should be EN_REVISION_FINANCIERA but is {workflow['estado_workflow']}"
        
        print(f"✓ All calculated workflows are in EN_REVISION_FINANCIERA state")


class TestNoRegression:
    """Non-regression tests for existing functionality"""
    
    def test_dashboard_kpis_working(self):
        """Test that dashboard KPIs endpoint still works"""
        response = requests.get(f"{BASE_URL}/api/v2/dashboard/kpis")
        assert response.status_code == 200
        data = response.json()
        
        # Verify expected fields
        assert "total_workflows" in data
        assert "workflows_activos" in data
        assert "tareas_pendientes" in data
        
        print(f"✓ Dashboard KPIs working - total_workflows: {data['total_workflows']}")
    
    def test_auth_login_working(self):
        """Test that authentication still works"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        assert response.status_code == 200
        assert "token" in response.json()
        
        print("✓ Auth login still working")
    
    def test_workflows_list_working(self):
        """Test that workflows list endpoint still works"""
        response = requests.get(f"{BASE_URL}/api/v2/workflows")
        assert response.status_code == 200
        data = response.json()
        
        assert "items" in data
        assert "total" in data
        
        print(f"✓ Workflows list working - total: {data['total']}")


# Fixtures
@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token for tests that need it"""
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
    )
    if response.status_code == 200:
        return response.json().get("token")
    return None


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
