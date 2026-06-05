"""
Test Suite for Responsabilidad Económica - Fase 2C.2 Aprobaciones
CAB-003 | EDARSA HUB

Tests the approval workflow for economic responsibility:
- State transitions: CALCULADO → PROPUESTO → APROBADO/RECHAZADO/EXONERADO/EN_DISPUTA
- Permission validation by role/amount
- Mandatory comments (min 10 chars)
- Transition history
- Workflow closure rules
"""
import pytest
import requests
import os
import uuid
from tests.test_config import test_config

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials from centralized config
ADMIN_EMAIL = test_config.TEST_ADMIN_EMAIL
ADMIN_PASSWORD = test_config.TEST_ADMIN_PASSWORD

# Test user IDs
TEST_USER_ID = "test-aprobaciones-user"

# Roles for testing
ROLES = {
    "AFECTADO": "AFECTADO",
    "SUPERVISOR": "SUPERVISOR",
    "GERENTE_OPS": "GERENTE_OPS",
    "DIRECCION": "DIRECCION"
}


class TestAprobacionesEndpointsBasicos:
    """Basic tests for approval endpoints availability"""
    
    def test_pendientes_aprobacion_endpoint(self):
        """Test GET /api/v2/responsabilidad/pendientes-aprobacion"""
        response = requests.get(f"{BASE_URL}/api/v2/responsabilidad/pendientes-aprobacion")
        assert response.status_code == 200
        data = response.json()
        
        assert "total" in data
        assert "monto_total_pendiente" in data
        assert "items" in data
        assert isinstance(data["items"], list)
        
        print(f"✓ Pendientes aprobación: total={data['total']}, monto_total={data['monto_total_pendiente']}")
    
    def test_en_disputa_endpoint(self):
        """Test GET /api/v2/responsabilidad/en-disputa"""
        response = requests.get(f"{BASE_URL}/api/v2/responsabilidad/en-disputa")
        assert response.status_code == 200
        data = response.json()
        
        assert "total" in data
        assert "monto_total_en_disputa" in data
        assert "items" in data
        assert isinstance(data["items"], list)
        
        print(f"✓ En disputa: total={data['total']}, monto_total={data['monto_total_en_disputa']}")


class TestComentarioObligatorio:
    """Tests for mandatory comment validation (min 10 chars)"""
    
    def test_comentario_menor_10_caracteres_rechazado(self):
        """Test that comments with less than 10 chars are rejected"""
        # Get a CALCULADO record
        response = requests.get(f"{BASE_URL}/api/v2/responsabilidad?estado=CALCULADO")
        items = response.json().get("items", [])
        
        if not items:
            pytest.skip("No CALCULADO records available for testing")
        
        responsabilidad_id = items[0]["id"]
        
        # Try with short comment
        response = requests.post(
            f"{BASE_URL}/api/v2/responsabilidad/{responsabilidad_id}/proponer",
            json={
                "usuario_id": TEST_USER_ID,
                "usuario_rol": "SUPERVISOR",
                "comentario": "corto"  # Less than 10 chars
            }
        )
        
        assert response.status_code == 422, f"Expected 422 for short comment, got {response.status_code}"
        print("✓ Short comment (<10 chars) correctly rejected with 422")
    
    def test_comentario_trivial_rechazado(self):
        """Test that trivial comments are rejected"""
        response = requests.get(f"{BASE_URL}/api/v2/responsabilidad?estado=CALCULADO")
        items = response.json().get("items", [])
        
        if not items:
            pytest.skip("No CALCULADO records available for testing")
        
        responsabilidad_id = items[0]["id"]
        
        # Try with trivial comment
        response = requests.post(
            f"{BASE_URL}/api/v2/responsabilidad/{responsabilidad_id}/proponer",
            json={
                "usuario_id": TEST_USER_ID,
                "usuario_rol": "SUPERVISOR",
                "comentario": "aprobado"  # Trivial comment
            }
        )
        
        assert response.status_code == 422, f"Expected 422 for trivial comment, got {response.status_code}"
        print("✓ Trivial comment correctly rejected with 422")


class TestTransicionCalculadoPropuesto:
    """Tests for CALCULADO → PROPUESTO transition"""
    
    def test_proponer_desde_calculado(self):
        """Test POST /api/v2/responsabilidad/{id}/proponer from CALCULADO state"""
        # Get a CALCULADO record
        response = requests.get(f"{BASE_URL}/api/v2/responsabilidad?estado=CALCULADO")
        items = response.json().get("items", [])
        
        if not items:
            pytest.skip("No CALCULADO records available for testing")
        
        responsabilidad_id = items[0]["id"]
        monto = items[0]["monto_propuesto_mxn"]
        
        # Proponer
        response = requests.post(
            f"{BASE_URL}/api/v2/responsabilidad/{responsabilidad_id}/proponer",
            json={
                "usuario_id": TEST_USER_ID,
                "usuario_rol": "SUPERVISOR",
                "comentario": "Proponiendo monto para revisión formal del equipo de finanzas"
            }
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        assert data["success"]
        assert data["estado_anterior"] == "CALCULADO"
        assert data["estado_nuevo"] == "PROPUESTO"
        assert data["accion"] == "PROPONER"
        assert "transicion_id" in data
        
        print(f"✓ CALCULADO → PROPUESTO: responsabilidad_id={responsabilidad_id}, monto={monto}")
        
        return responsabilidad_id


class TestTransicionPropuestoAprobado:
    """Tests for PROPUESTO → APROBADO transition"""
    
    def test_aprobar_desde_propuesto(self):
        """Test POST /api/v2/responsabilidad/{id}/aprobar from PROPUESTO state"""
        # Get a PROPUESTO record
        response = requests.get(f"{BASE_URL}/api/v2/responsabilidad")
        items = response.json().get("items", [])
        propuestos = [i for i in items if i["estado"] == "PROPUESTO"]
        
        if not propuestos:
            pytest.skip("No PROPUESTO records available for testing")
        
        responsabilidad_id = propuestos[0]["id"]
        monto = propuestos[0]["monto_propuesto_mxn"]
        
        # Determine required role based on amount
        if monto <= 500:
            rol = "SUPERVISOR"
        elif monto <= 2000:
            rol = "GERENTE_OPS"
        else:
            rol = "DIRECCION"
        
        # Aprobar
        response = requests.post(
            f"{BASE_URL}/api/v2/responsabilidad/{responsabilidad_id}/aprobar",
            json={
                "usuario_id": TEST_USER_ID,
                "usuario_rol": rol,
                "comentario": "Aprobando el cargo propuesto después de revisión detallada"
            }
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        assert data["success"]
        assert data["estado_anterior"] == "PROPUESTO"
        assert data["estado_nuevo"] == "APROBADO"
        assert data["accion"] == "APROBAR"
        # APROBADO should NOT close workflow
        assert data["workflow_estado"] == "EN_REVISION_FINANCIERA"
        
        print(f"✓ PROPUESTO → APROBADO: responsabilidad_id={responsabilidad_id}, rol={rol}")


class TestTransicionPropuestoRechazado:
    """Tests for PROPUESTO → RECHAZADO transition"""
    
    def test_rechazar_desde_propuesto(self):
        """Test POST /api/v2/responsabilidad/{id}/rechazar from PROPUESTO state"""
        # Get a PROPUESTO record
        response = requests.get(f"{BASE_URL}/api/v2/responsabilidad")
        items = response.json().get("items", [])
        propuestos = [i for i in items if i["estado"] == "PROPUESTO"]
        
        if not propuestos:
            pytest.skip("No PROPUESTO records available for testing")
        
        responsabilidad_id = propuestos[0]["id"]
        
        # Rechazar
        response = requests.post(
            f"{BASE_URL}/api/v2/responsabilidad/{responsabilidad_id}/rechazar",
            json={
                "usuario_id": TEST_USER_ID,
                "usuario_rol": "GERENTE_OPS",
                "comentario": "Rechazando el cargo porque no tiene base válida según revisión"
            }
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        assert data["success"]
        assert data["estado_anterior"] == "PROPUESTO"
        assert data["estado_nuevo"] == "RECHAZADO"
        assert data["accion"] == "RECHAZAR"
        
        print(f"✓ PROPUESTO → RECHAZADO: responsabilidad_id={responsabilidad_id}")


class TestTransicionPropuestoExonerado:
    """Tests for PROPUESTO → EXONERADO transition"""
    
    def test_exonerar_desde_propuesto(self):
        """Test POST /api/v2/responsabilidad/{id}/exonerar from PROPUESTO state"""
        # Get a PROPUESTO record
        response = requests.get(f"{BASE_URL}/api/v2/responsabilidad")
        items = response.json().get("items", [])
        propuestos = [i for i in items if i["estado"] == "PROPUESTO"]
        
        if not propuestos:
            pytest.skip("No PROPUESTO records available for testing")
        
        responsabilidad_id = propuestos[0]["id"]
        
        # Exonerar requires GERENTE_OPS or higher
        response = requests.post(
            f"{BASE_URL}/api/v2/responsabilidad/{responsabilidad_id}/exonerar",
            json={
                "usuario_id": TEST_USER_ID,
                "usuario_rol": "GERENTE_OPS",
                "comentario": "Exonerando al responsable por circunstancias atenuantes documentadas"
            }
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        assert data["success"]
        assert data["estado_anterior"] == "PROPUESTO"
        assert data["estado_nuevo"] == "EXONERADO"
        assert data["accion"] == "EXONERAR"
        
        print(f"✓ PROPUESTO → EXONERADO: responsabilidad_id={responsabilidad_id}")


class TestTransicionPropuestoEnDisputa:
    """Tests for PROPUESTO → EN_DISPUTA transition"""
    
    def test_disputar_desde_propuesto(self):
        """Test POST /api/v2/responsabilidad/{id}/disputar from PROPUESTO state"""
        # Get a PROPUESTO record
        response = requests.get(f"{BASE_URL}/api/v2/responsabilidad")
        items = response.json().get("items", [])
        propuestos = [i for i in items if i["estado"] == "PROPUESTO"]
        
        if not propuestos:
            pytest.skip("No PROPUESTO records available for testing")
        
        responsabilidad_id = propuestos[0]["id"]
        
        # Disputar can be done by AFECTADO or higher
        response = requests.post(
            f"{BASE_URL}/api/v2/responsabilidad/{responsabilidad_id}/disputar",
            json={
                "usuario_id": TEST_USER_ID,
                "usuario_rol": "AFECTADO",
                "comentario": "Disputo este cargo porque considero que hay errores en el cálculo"
            }
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        assert data["success"]
        assert data["estado_anterior"] == "PROPUESTO"
        assert data["estado_nuevo"] == "EN_DISPUTA"
        assert data["accion"] == "DISPUTAR"
        
        print(f"✓ PROPUESTO → EN_DISPUTA: responsabilidad_id={responsabilidad_id}")


class TestTransicionEnDisputaPropuesto:
    """Tests for EN_DISPUTA → PROPUESTO transition (resolver disputa)"""
    
    def test_resolver_disputa(self):
        """Test POST /api/v2/responsabilidad/{id}/resolver-disputa from EN_DISPUTA state"""
        # Get an EN_DISPUTA record
        response = requests.get(f"{BASE_URL}/api/v2/responsabilidad/en-disputa")
        items = response.json().get("items", [])
        
        if not items:
            pytest.skip("No EN_DISPUTA records available for testing")
        
        responsabilidad_id = items[0]["id"]
        
        # Resolver disputa
        response = requests.post(
            f"{BASE_URL}/api/v2/responsabilidad/{responsabilidad_id}/resolver-disputa",
            json={
                "usuario_id": TEST_USER_ID,
                "usuario_rol": "SUPERVISOR",
                "comentario": "Disputa resuelta después de revisión con el afectado y documentación"
            }
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        assert data["success"]
        assert data["estado_anterior"] == "EN_DISPUTA"
        assert data["estado_nuevo"] == "PROPUESTO"
        assert data["accion"] == "RESOLVER_DISPUTA"
        
        print(f"✓ EN_DISPUTA → PROPUESTO: responsabilidad_id={responsabilidad_id}")


class TestTransicionEnDisputaExonerado:
    """Tests for EN_DISPUTA → EXONERADO transition"""
    
    def test_exonerar_desde_disputa(self):
        """Test POST /api/v2/responsabilidad/{id}/exonerar from EN_DISPUTA state"""
        # Get an EN_DISPUTA record
        response = requests.get(f"{BASE_URL}/api/v2/responsabilidad/en-disputa")
        items = response.json().get("items", [])
        
        if not items:
            pytest.skip("No EN_DISPUTA records available for testing")
        
        responsabilidad_id = items[0]["id"]
        
        # Exonerar desde disputa
        response = requests.post(
            f"{BASE_URL}/api/v2/responsabilidad/{responsabilidad_id}/exonerar",
            json={
                "usuario_id": TEST_USER_ID,
                "usuario_rol": "DIRECCION",
                "comentario": "Exonerando desde disputa por decisión de dirección general"
            }
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        assert data["success"]
        assert data["estado_anterior"] == "EN_DISPUTA"
        assert data["estado_nuevo"] == "EXONERADO"
        assert data["accion"] == "EXONERAR"
        
        print(f"✓ EN_DISPUTA → EXONERADO: responsabilidad_id={responsabilidad_id}")


class TestValidacionPermisosPorMonto:
    """Tests for permission validation by amount/role"""
    
    def test_supervisor_limite_500(self):
        """Test that SUPERVISOR can only approve amounts up to $500"""
        # Get a PROPUESTO record with monto > 500
        response = requests.get(f"{BASE_URL}/api/v2/responsabilidad")
        items = response.json().get("items", [])
        propuestos = [i for i in items if i["estado"] == "PROPUESTO" and i["monto_propuesto_mxn"] > 500]
        
        if not propuestos:
            pytest.skip("No PROPUESTO records with monto > 500 available")
        
        responsabilidad_id = propuestos[0]["id"]
        monto = propuestos[0]["monto_propuesto_mxn"]
        
        # Try to approve with SUPERVISOR (should fail for monto > 500)
        response = requests.post(
            f"{BASE_URL}/api/v2/responsabilidad/{responsabilidad_id}/aprobar",
            json={
                "usuario_id": TEST_USER_ID,
                "usuario_rol": "SUPERVISOR",
                "comentario": "Intentando aprobar monto alto con rol supervisor"
            }
        )
        
        assert response.status_code == 403, f"Expected 403 for SUPERVISOR approving >${monto}, got {response.status_code}"
        print(f"✓ SUPERVISOR correctly denied for monto ${monto} > $500")
    
    def test_gerente_ops_limite_2000(self):
        """Test that GERENTE_OPS can approve amounts up to $2000"""
        # Get a PROPUESTO record with monto between 500 and 2000
        response = requests.get(f"{BASE_URL}/api/v2/responsabilidad")
        items = response.json().get("items", [])
        propuestos = [i for i in items if i["estado"] == "PROPUESTO" and 500 < i["monto_propuesto_mxn"] <= 2000]
        
        if not propuestos:
            pytest.skip("No PROPUESTO records with 500 < monto <= 2000 available")
        
        responsabilidad_id = propuestos[0]["id"]
        monto = propuestos[0]["monto_propuesto_mxn"]
        
        # GERENTE_OPS should be able to approve
        response = requests.post(
            f"{BASE_URL}/api/v2/responsabilidad/{responsabilidad_id}/aprobar",
            json={
                "usuario_id": TEST_USER_ID,
                "usuario_rol": "GERENTE_OPS",
                "comentario": "Aprobando monto dentro de mi límite de autorización"
            }
        )
        
        assert response.status_code == 200, f"Expected 200 for GERENTE_OPS approving ${monto}, got {response.status_code}"
        print(f"✓ GERENTE_OPS correctly approved monto ${monto}")
    
    def test_direccion_sin_limite(self):
        """Test that DIRECCION can approve any amount"""
        # Get any PROPUESTO record
        response = requests.get(f"{BASE_URL}/api/v2/responsabilidad")
        items = response.json().get("items", [])
        propuestos = [i for i in items if i["estado"] == "PROPUESTO"]
        
        if not propuestos:
            pytest.skip("No PROPUESTO records available")
        
        responsabilidad_id = propuestos[0]["id"]
        monto = propuestos[0]["monto_propuesto_mxn"]
        
        # DIRECCION should be able to approve any amount
        response = requests.post(
            f"{BASE_URL}/api/v2/responsabilidad/{responsabilidad_id}/aprobar",
            json={
                "usuario_id": TEST_USER_ID,
                "usuario_rol": "DIRECCION",
                "comentario": "Aprobación de dirección general sin límite de monto"
            }
        )
        
        assert response.status_code == 200, f"Expected 200 for DIRECCION, got {response.status_code}"
        print(f"✓ DIRECCION correctly approved monto ${monto}")


class TestHistorialTransiciones:
    """Tests for transition history"""
    
    def test_historial_endpoint(self):
        """Test GET /api/v2/responsabilidad/{id}/historial"""
        # Get any responsabilidad
        response = requests.get(f"{BASE_URL}/api/v2/responsabilidad")
        items = response.json().get("items", [])
        
        if not items:
            pytest.skip("No responsabilidad records available")
        
        responsabilidad_id = items[0]["id"]
        
        # Get historial
        response = requests.get(f"{BASE_URL}/api/v2/responsabilidad/{responsabilidad_id}/historial")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "responsabilidad_id" in data
        assert "total" in data
        assert "items" in data
        assert data["responsabilidad_id"] == responsabilidad_id
        
        print(f"✓ Historial endpoint working: {data['total']} transiciones")
    
    def test_historial_contiene_transiciones(self):
        """Test that historial contains transition records with correct structure"""
        # Get a responsabilidad that has been through transitions
        response = requests.get(f"{BASE_URL}/api/v2/responsabilidad")
        items = response.json().get("items", [])
        
        # Find one that's not in CALCULADO (has been transitioned)
        transitioned = [i for i in items if i["estado"] != "CALCULADO"]
        
        if not transitioned:
            pytest.skip("No transitioned records available")
        
        responsabilidad_id = transitioned[0]["id"]
        
        # Get historial
        response = requests.get(f"{BASE_URL}/api/v2/responsabilidad/{responsabilidad_id}/historial")
        data = response.json()
        
        if data["total"] > 0:
            transicion = data["items"][0]
            
            # Verify structure
            assert "id" in transicion
            assert "responsabilidad_id" in transicion
            assert "accion" in transicion
            assert "estado_anterior" in transicion
            assert "estado_nuevo" in transicion
            assert "usuario_id" in transicion
            assert "comentario" in transicion
            assert "fecha" in transicion
            
            print(f"✓ Historial structure correct: {transicion['accion']} ({transicion['estado_anterior']} → {transicion['estado_nuevo']})")
        else:
            pytest.skip("No transitions in historial")


class TestTransicionesInvalidas:
    """Tests for invalid state transitions"""
    
    def test_aprobar_desde_calculado_invalido(self):
        """Test that APROBAR from CALCULADO is invalid (must go through PROPUESTO)"""
        # Get a CALCULADO record
        response = requests.get(f"{BASE_URL}/api/v2/responsabilidad?estado=CALCULADO")
        items = response.json().get("items", [])
        
        if not items:
            pytest.skip("No CALCULADO records available")
        
        responsabilidad_id = items[0]["id"]
        
        # Try to approve directly from CALCULADO
        response = requests.post(
            f"{BASE_URL}/api/v2/responsabilidad/{responsabilidad_id}/aprobar",
            json={
                "usuario_id": TEST_USER_ID,
                "usuario_rol": "DIRECCION",
                "comentario": "Intentando aprobar directamente desde CALCULADO"
            }
        )
        
        assert response.status_code == 400, f"Expected 400 for invalid transition, got {response.status_code}"
        print("✓ CALCULADO → APROBADO correctly rejected as invalid transition")
    
    def test_disputar_desde_calculado_invalido(self):
        """Test that DISPUTAR from CALCULADO is invalid"""
        # Get a CALCULADO record
        response = requests.get(f"{BASE_URL}/api/v2/responsabilidad?estado=CALCULADO")
        items = response.json().get("items", [])
        
        if not items:
            pytest.skip("No CALCULADO records available")
        
        responsabilidad_id = items[0]["id"]
        
        # Try to dispute from CALCULADO
        response = requests.post(
            f"{BASE_URL}/api/v2/responsabilidad/{responsabilidad_id}/disputar",
            json={
                "usuario_id": TEST_USER_ID,
                "usuario_rol": "AFECTADO",
                "comentario": "Intentando disputar directamente desde CALCULADO"
            }
        )
        
        assert response.status_code == 400, f"Expected 400 for invalid transition, got {response.status_code}"
        print("✓ CALCULADO → EN_DISPUTA correctly rejected as invalid transition")
    
    def test_proponer_desde_aprobado_invalido(self):
        """Test that PROPONER from APROBADO is invalid (final state)"""
        # Get an APROBADO record
        response = requests.get(f"{BASE_URL}/api/v2/responsabilidad")
        items = response.json().get("items", [])
        aprobados = [i for i in items if i["estado"] == "APROBADO"]
        
        if not aprobados:
            pytest.skip("No APROBADO records available")
        
        responsabilidad_id = aprobados[0]["id"]
        
        # Try to proponer from APROBADO
        response = requests.post(
            f"{BASE_URL}/api/v2/responsabilidad/{responsabilidad_id}/proponer",
            json={
                "usuario_id": TEST_USER_ID,
                "usuario_rol": "SUPERVISOR",
                "comentario": "Intentando proponer desde estado APROBADO"
            }
        )
        
        assert response.status_code == 400, f"Expected 400 for invalid transition, got {response.status_code}"
        print("✓ APROBADO → PROPUESTO correctly rejected as invalid transition")


class TestAprobadoNoCierraWorkflow:
    """Tests that APROBADO does NOT close the workflow"""
    
    def test_aprobado_mantiene_workflow_en_revision(self):
        """Test that APROBADO keeps workflow in EN_REVISION_FINANCIERA"""
        # Get an APROBADO record
        response = requests.get(f"{BASE_URL}/api/v2/responsabilidad")
        items = response.json().get("items", [])
        aprobados = [i for i in items if i["estado"] == "APROBADO"]
        
        if not aprobados:
            pytest.skip("No APROBADO records available")
        
        workflow_id = aprobados[0]["workflow_id"]
        
        # Check workflow state
        response = requests.get(f"{BASE_URL}/api/v2/workflows/{workflow_id}")
        
        if response.status_code == 200:
            workflow = response.json()
            # APROBADO should NOT close workflow - it stays in EN_REVISION_FINANCIERA
            assert workflow["estado_workflow"] == "EN_REVISION_FINANCIERA", \
                f"Expected EN_REVISION_FINANCIERA, got {workflow['estado_workflow']}"
            print("✓ APROBADO correctly keeps workflow in EN_REVISION_FINANCIERA")
        else:
            pytest.skip("Could not fetch workflow")


class TestNoRegresion:
    """Non-regression tests"""
    
    def test_dashboard_kpis_working(self):
        """Test that dashboard KPIs endpoint still works"""
        response = requests.get(f"{BASE_URL}/api/v2/dashboard/kpis")
        assert response.status_code == 200
        data = response.json()
        
        assert "total_workflows" in data
        print("✓ Dashboard KPIs working")
    
    def test_auth_login_working(self):
        """Test that authentication still works"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        assert response.status_code == 200
        assert "token" in response.json()
        print("✓ Auth login still working")
    
    def test_responsabilidad_list_working(self):
        """Test that responsabilidad list endpoint still works"""
        response = requests.get(f"{BASE_URL}/api/v2/responsabilidad")
        assert response.status_code == 200
        data = response.json()
        
        assert "items" in data
        assert "total" in data
        print(f"✓ Responsabilidad list working - total: {data['total']}")


class TestResponsabilidadNoEncontrada:
    """Tests for non-existing responsabilidad"""
    
    def test_proponer_no_encontrada(self):
        """Test proponer with non-existing ID returns 404"""
        fake_id = str(uuid.uuid4())
        
        response = requests.post(
            f"{BASE_URL}/api/v2/responsabilidad/{fake_id}/proponer",
            json={
                "usuario_id": TEST_USER_ID,
                "usuario_rol": "SUPERVISOR",
                "comentario": "Intentando proponer responsabilidad inexistente"
            }
        )
        
        assert response.status_code == 404
        print("✓ Proponer non-existing returns 404")
    
    def test_historial_no_encontrada(self):
        """Test historial with non-existing ID returns 404"""
        fake_id = str(uuid.uuid4())
        
        response = requests.get(f"{BASE_URL}/api/v2/responsabilidad/{fake_id}/historial")
        
        assert response.status_code == 404
        print("✓ Historial non-existing returns 404")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
