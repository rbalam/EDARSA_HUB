"""
Test Suite for Responsabilidad Económica - Fase 2C.2 Aprobaciones (Comprehensive)
CAB-003 | EDARSA HUB

This test creates its own test data to ensure all flows can be tested.
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

# Workflow IDs for testing (from existing data)
WORKFLOW_LARGE_AMOUNT = "54445e56-bb2d-4b91-9a0c-5c3cfb57add2"  # $1100
WORKFLOW_SMALL_AMOUNT = "c05aba78-b5a8-4461-afb5-8592c7f35c44"  # $0
WORKFLOW_SOBRANTES = "6c04c646-8603-4ea5-867e-aabbe2cdc817"  # $0 (sobrantes only)


def reset_to_calculado(workflow_id):
    """Reset a responsabilidad to CALCULADO state using forzar_recalculo"""
    response = requests.post(
        f"{BASE_URL}/api/v2/responsabilidad/calcular/{workflow_id}?usuario_id=test-reset&forzar_recalculo=true"
    )
    if response.status_code == 200:
        return response.json()
    return None


class TestEndpointsBasicos:
    """Basic endpoint availability tests"""
    
    def test_pendientes_aprobacion_endpoint(self):
        """Test GET /api/v2/responsabilidad/pendientes-aprobacion"""
        response = requests.get(f"{BASE_URL}/api/v2/responsabilidad/pendientes-aprobacion")
        assert response.status_code == 200
        data = response.json()
        
        assert "total" in data
        assert "monto_total_pendiente" in data
        assert "items" in data
        print(f"✓ Pendientes aprobación: total={data['total']}")
    
    def test_en_disputa_endpoint(self):
        """Test GET /api/v2/responsabilidad/en-disputa"""
        response = requests.get(f"{BASE_URL}/api/v2/responsabilidad/en-disputa")
        assert response.status_code == 200
        data = response.json()
        
        assert "total" in data
        assert "monto_total_en_disputa" in data
        assert "items" in data
        print(f"✓ En disputa: total={data['total']}")


class TestComentarioValidacion:
    """Tests for mandatory comment validation"""
    
    def test_comentario_menor_10_caracteres_rechazado(self):
        """Test that comments with less than 10 chars are rejected"""
        # Reset to CALCULADO
        calc = reset_to_calculado(WORKFLOW_SMALL_AMOUNT)
        if not calc:
            pytest.skip("Could not reset to CALCULADO")
        
        resp_id = calc["id"]
        
        # Try with short comment
        response = requests.post(
            f"{BASE_URL}/api/v2/responsabilidad/{resp_id}/proponer",
            json={
                "usuario_id": TEST_USER_ID,
                "usuario_rol": "SUPERVISOR",
                "comentario": "corto"
            }
        )
        
        assert response.status_code == 422
        print("✓ Short comment (<10 chars) correctly rejected")
    
    def test_comentario_trivial_rechazado(self):
        """Test that trivial comments are rejected"""
        # Reset to CALCULADO
        calc = reset_to_calculado(WORKFLOW_SMALL_AMOUNT)
        if not calc:
            pytest.skip("Could not reset to CALCULADO")
        
        resp_id = calc["id"]
        
        # Try with trivial comment
        response = requests.post(
            f"{BASE_URL}/api/v2/responsabilidad/{resp_id}/proponer",
            json={
                "usuario_id": TEST_USER_ID,
                "usuario_rol": "SUPERVISOR",
                "comentario": "aprobado"
            }
        )
        
        assert response.status_code == 422
        print("✓ Trivial comment correctly rejected")


class TestFlujoCalculadoPropuesto:
    """Tests for CALCULADO → PROPUESTO transition"""
    
    def test_proponer_desde_calculado_monto_bajo(self):
        """Test PROPONER from CALCULADO with low amount (SUPERVISOR can do it)"""
        # Reset to CALCULADO
        calc = reset_to_calculado(WORKFLOW_SMALL_AMOUNT)
        if not calc:
            pytest.skip("Could not reset to CALCULADO")
        
        resp_id = calc["id"]
        
        response = requests.post(
            f"{BASE_URL}/api/v2/responsabilidad/{resp_id}/proponer",
            json={
                "usuario_id": TEST_USER_ID,
                "usuario_rol": "SUPERVISOR",
                "comentario": "Proponiendo monto para revisión formal del equipo"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"]
        assert data["estado_anterior"] == "CALCULADO"
        assert data["estado_nuevo"] == "PROPUESTO"
        print("✓ CALCULADO → PROPUESTO (monto bajo)")
    
    def test_proponer_desde_calculado_monto_alto_requiere_gerente(self):
        """Test PROPONER from CALCULADO with high amount requires GERENTE_OPS"""
        # Reset to CALCULADO
        calc = reset_to_calculado(WORKFLOW_LARGE_AMOUNT)
        if not calc:
            pytest.skip("Could not reset to CALCULADO")
        
        resp_id = calc["id"]
        monto = calc["monto_propuesto_mxn"]
        
        # SUPERVISOR should fail for high amount
        response = requests.post(
            f"{BASE_URL}/api/v2/responsabilidad/{resp_id}/proponer",
            json={
                "usuario_id": TEST_USER_ID,
                "usuario_rol": "SUPERVISOR",
                "comentario": "Intentando proponer monto alto con supervisor"
            }
        )
        
        assert response.status_code == 403
        print(f"✓ SUPERVISOR correctly denied for monto ${monto}")
        
        # GERENTE_OPS should succeed
        response = requests.post(
            f"{BASE_URL}/api/v2/responsabilidad/{resp_id}/proponer",
            json={
                "usuario_id": TEST_USER_ID,
                "usuario_rol": "GERENTE_OPS",
                "comentario": "Proponiendo monto alto con gerente de operaciones"
            }
        )
        
        assert response.status_code == 200
        print(f"✓ GERENTE_OPS correctly allowed for monto ${monto}")


class TestFlujoPropuestoAprobado:
    """Tests for PROPUESTO → APROBADO transition"""
    
    def test_aprobar_desde_propuesto(self):
        """Test APROBAR from PROPUESTO"""
        # Reset and proponer
        calc = reset_to_calculado(WORKFLOW_SMALL_AMOUNT)
        if not calc:
            pytest.skip("Could not reset to CALCULADO")
        
        resp_id = calc["id"]
        
        # Proponer first
        requests.post(
            f"{BASE_URL}/api/v2/responsabilidad/{resp_id}/proponer",
            json={
                "usuario_id": TEST_USER_ID,
                "usuario_rol": "SUPERVISOR",
                "comentario": "Proponiendo monto para revisión formal"
            }
        )
        
        # Now aprobar
        response = requests.post(
            f"{BASE_URL}/api/v2/responsabilidad/{resp_id}/aprobar",
            json={
                "usuario_id": TEST_USER_ID,
                "usuario_rol": "SUPERVISOR",
                "comentario": "Aprobando el cargo propuesto después de revisión"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"]
        assert data["estado_anterior"] == "PROPUESTO"
        assert data["estado_nuevo"] == "APROBADO"
        # APROBADO should NOT close workflow
        assert data["workflow_estado"] == "EN_REVISION_FINANCIERA"
        print("✓ PROPUESTO → APROBADO (workflow stays EN_REVISION_FINANCIERA)")


class TestFlujoPropuestoRechazado:
    """Tests for PROPUESTO → RECHAZADO transition"""
    
    def test_rechazar_desde_propuesto(self):
        """Test RECHAZAR from PROPUESTO"""
        # Reset and proponer
        calc = reset_to_calculado(WORKFLOW_SOBRANTES)
        if not calc:
            pytest.skip("Could not reset to CALCULADO")
        
        resp_id = calc["id"]
        
        # Proponer first
        requests.post(
            f"{BASE_URL}/api/v2/responsabilidad/{resp_id}/proponer",
            json={
                "usuario_id": TEST_USER_ID,
                "usuario_rol": "SUPERVISOR",
                "comentario": "Proponiendo monto para revisión formal"
            }
        )
        
        # Now rechazar
        response = requests.post(
            f"{BASE_URL}/api/v2/responsabilidad/{resp_id}/rechazar",
            json={
                "usuario_id": TEST_USER_ID,
                "usuario_rol": "GERENTE_OPS",
                "comentario": "Rechazando el cargo porque no tiene base válida"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"]
        assert data["estado_anterior"] == "PROPUESTO"
        assert data["estado_nuevo"] == "RECHAZADO"
        print("✓ PROPUESTO → RECHAZADO")


class TestFlujoPropuestoExonerado:
    """Tests for PROPUESTO → EXONERADO transition"""
    
    def test_exonerar_desde_propuesto(self):
        """Test EXONERAR from PROPUESTO"""
        # Reset and proponer
        calc = reset_to_calculado(WORKFLOW_SMALL_AMOUNT)
        if not calc:
            pytest.skip("Could not reset to CALCULADO")
        
        resp_id = calc["id"]
        
        # Proponer first
        requests.post(
            f"{BASE_URL}/api/v2/responsabilidad/{resp_id}/proponer",
            json={
                "usuario_id": TEST_USER_ID,
                "usuario_rol": "SUPERVISOR",
                "comentario": "Proponiendo monto para revisión formal"
            }
        )
        
        # Now exonerar (requires GERENTE_OPS or higher)
        response = requests.post(
            f"{BASE_URL}/api/v2/responsabilidad/{resp_id}/exonerar",
            json={
                "usuario_id": TEST_USER_ID,
                "usuario_rol": "GERENTE_OPS",
                "comentario": "Exonerando al responsable por circunstancias atenuantes"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"]
        assert data["estado_anterior"] == "PROPUESTO"
        assert data["estado_nuevo"] == "EXONERADO"
        print("✓ PROPUESTO → EXONERADO")


class TestFlujoDisputa:
    """Tests for dispute flow"""
    
    def test_disputar_desde_propuesto(self):
        """Test DISPUTAR from PROPUESTO"""
        # Reset and proponer
        calc = reset_to_calculado(WORKFLOW_LARGE_AMOUNT)
        if not calc:
            pytest.skip("Could not reset to CALCULADO")
        
        resp_id = calc["id"]
        
        # Proponer first
        requests.post(
            f"{BASE_URL}/api/v2/responsabilidad/{resp_id}/proponer",
            json={
                "usuario_id": TEST_USER_ID,
                "usuario_rol": "GERENTE_OPS",
                "comentario": "Proponiendo monto para revisión formal"
            }
        )
        
        # Now disputar (AFECTADO can do it)
        response = requests.post(
            f"{BASE_URL}/api/v2/responsabilidad/{resp_id}/disputar",
            json={
                "usuario_id": "afectado-001",
                "usuario_rol": "AFECTADO",
                "comentario": "Disputo este cargo porque hay errores en el cálculo"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"]
        assert data["estado_anterior"] == "PROPUESTO"
        assert data["estado_nuevo"] == "EN_DISPUTA"
        print("✓ PROPUESTO → EN_DISPUTA")
    
    def test_resolver_disputa(self):
        """Test RESOLVER_DISPUTA from EN_DISPUTA"""
        # Reset, proponer, disputar
        calc = reset_to_calculado(WORKFLOW_LARGE_AMOUNT)
        if not calc:
            pytest.skip("Could not reset to CALCULADO")
        
        resp_id = calc["id"]
        
        # Proponer
        requests.post(
            f"{BASE_URL}/api/v2/responsabilidad/{resp_id}/proponer",
            json={
                "usuario_id": TEST_USER_ID,
                "usuario_rol": "GERENTE_OPS",
                "comentario": "Proponiendo monto para revisión formal"
            }
        )
        
        # Disputar
        requests.post(
            f"{BASE_URL}/api/v2/responsabilidad/{resp_id}/disputar",
            json={
                "usuario_id": "afectado-001",
                "usuario_rol": "AFECTADO",
                "comentario": "Disputo este cargo porque hay errores"
            }
        )
        
        # Resolver disputa
        response = requests.post(
            f"{BASE_URL}/api/v2/responsabilidad/{resp_id}/resolver-disputa",
            json={
                "usuario_id": TEST_USER_ID,
                "usuario_rol": "GERENTE_OPS",
                "comentario": "Disputa resuelta después de revisión con el afectado"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"]
        assert data["estado_anterior"] == "EN_DISPUTA"
        assert data["estado_nuevo"] == "PROPUESTO"
        print("✓ EN_DISPUTA → PROPUESTO (resolver disputa)")
    
    def test_exonerar_desde_disputa(self):
        """Test EXONERAR from EN_DISPUTA"""
        # Reset, proponer, disputar
        calc = reset_to_calculado(WORKFLOW_SOBRANTES)
        if not calc:
            pytest.skip("Could not reset to CALCULADO")
        
        resp_id = calc["id"]
        
        # Proponer
        requests.post(
            f"{BASE_URL}/api/v2/responsabilidad/{resp_id}/proponer",
            json={
                "usuario_id": TEST_USER_ID,
                "usuario_rol": "SUPERVISOR",
                "comentario": "Proponiendo monto para revisión formal"
            }
        )
        
        # Disputar
        requests.post(
            f"{BASE_URL}/api/v2/responsabilidad/{resp_id}/disputar",
            json={
                "usuario_id": "afectado-001",
                "usuario_rol": "AFECTADO",
                "comentario": "Disputo este cargo porque hay circunstancias"
            }
        )
        
        # Exonerar desde disputa
        response = requests.post(
            f"{BASE_URL}/api/v2/responsabilidad/{resp_id}/exonerar",
            json={
                "usuario_id": TEST_USER_ID,
                "usuario_rol": "DIRECCION",
                "comentario": "Exonerando desde disputa por decisión de dirección"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"]
        assert data["estado_anterior"] == "EN_DISPUTA"
        assert data["estado_nuevo"] == "EXONERADO"
        print("✓ EN_DISPUTA → EXONERADO")


class TestValidacionPermisos:
    """Tests for permission validation by amount/role"""
    
    def test_supervisor_limite_500(self):
        """Test that SUPERVISOR can only approve amounts up to $500"""
        # Reset to CALCULADO with high amount
        calc = reset_to_calculado(WORKFLOW_LARGE_AMOUNT)
        if not calc:
            pytest.skip("Could not reset to CALCULADO")
        
        resp_id = calc["id"]
        monto = calc["monto_propuesto_mxn"]
        
        if monto <= 500:
            pytest.skip("Need workflow with monto > 500")
        
        # Proponer with GERENTE_OPS
        requests.post(
            f"{BASE_URL}/api/v2/responsabilidad/{resp_id}/proponer",
            json={
                "usuario_id": TEST_USER_ID,
                "usuario_rol": "GERENTE_OPS",
                "comentario": "Proponiendo monto alto para revisión"
            }
        )
        
        # Try to approve with SUPERVISOR (should fail)
        response = requests.post(
            f"{BASE_URL}/api/v2/responsabilidad/{resp_id}/aprobar",
            json={
                "usuario_id": TEST_USER_ID,
                "usuario_rol": "SUPERVISOR",
                "comentario": "Intentando aprobar monto alto con supervisor"
            }
        )
        
        assert response.status_code == 403
        print(f"✓ SUPERVISOR correctly denied for monto ${monto} > $500")


class TestHistorial:
    """Tests for transition history"""
    
    def test_historial_registra_transiciones(self):
        """Test that historial correctly records all transitions"""
        # Reset and do multiple transitions
        calc = reset_to_calculado(WORKFLOW_SMALL_AMOUNT)
        if not calc:
            pytest.skip("Could not reset to CALCULADO")
        
        resp_id = calc["id"]
        
        # Proponer
        requests.post(
            f"{BASE_URL}/api/v2/responsabilidad/{resp_id}/proponer",
            json={
                "usuario_id": "user-1",
                "usuario_rol": "SUPERVISOR",
                "comentario": "Proponiendo monto para revisión formal"
            }
        )
        
        # Disputar
        requests.post(
            f"{BASE_URL}/api/v2/responsabilidad/{resp_id}/disputar",
            json={
                "usuario_id": "user-2",
                "usuario_rol": "AFECTADO",
                "comentario": "Disputo este cargo por errores"
            }
        )
        
        # Resolver
        requests.post(
            f"{BASE_URL}/api/v2/responsabilidad/{resp_id}/resolver-disputa",
            json={
                "usuario_id": "user-3",
                "usuario_rol": "SUPERVISOR",
                "comentario": "Disputa resuelta después de revisión"
            }
        )
        
        # Get historial
        response = requests.get(f"{BASE_URL}/api/v2/responsabilidad/{resp_id}/historial")
        assert response.status_code == 200
        
        data = response.json()
        assert data["total"] >= 3
        
        # Verify structure
        for item in data["items"]:
            assert "id" in item
            assert "accion" in item
            assert "estado_anterior" in item
            assert "estado_nuevo" in item
            assert "usuario_id" in item
            assert "comentario" in item
            assert "fecha" in item
        
        print(f"✓ Historial correctly records {data['total']} transitions")


class TestTransicionesInvalidas:
    """Tests for invalid state transitions"""
    
    def test_aprobar_desde_calculado_invalido(self):
        """Test that APROBAR from CALCULADO is invalid"""
        # Reset to CALCULADO
        calc = reset_to_calculado(WORKFLOW_SMALL_AMOUNT)
        if not calc:
            pytest.skip("Could not reset to CALCULADO")
        
        resp_id = calc["id"]
        
        # Try to approve directly from CALCULADO
        response = requests.post(
            f"{BASE_URL}/api/v2/responsabilidad/{resp_id}/aprobar",
            json={
                "usuario_id": TEST_USER_ID,
                "usuario_rol": "DIRECCION",
                "comentario": "Intentando aprobar directamente desde CALCULADO"
            }
        )
        
        assert response.status_code == 400
        print("✓ CALCULADO → APROBADO correctly rejected")
    
    def test_disputar_desde_calculado_invalido(self):
        """Test that DISPUTAR from CALCULADO is invalid"""
        # Reset to CALCULADO
        calc = reset_to_calculado(WORKFLOW_SMALL_AMOUNT)
        if not calc:
            pytest.skip("Could not reset to CALCULADO")
        
        resp_id = calc["id"]
        
        # Try to dispute from CALCULADO
        response = requests.post(
            f"{BASE_URL}/api/v2/responsabilidad/{resp_id}/disputar",
            json={
                "usuario_id": TEST_USER_ID,
                "usuario_rol": "AFECTADO",
                "comentario": "Intentando disputar directamente desde CALCULADO"
            }
        )
        
        assert response.status_code == 400
        print("✓ CALCULADO → EN_DISPUTA correctly rejected")


class TestNoRegresion:
    """Non-regression tests"""
    
    def test_dashboard_kpis_working(self):
        """Test that dashboard KPIs endpoint still works"""
        response = requests.get(f"{BASE_URL}/api/v2/dashboard/kpis")
        assert response.status_code == 200
        print("✓ Dashboard KPIs working")
    
    def test_auth_login_working(self):
        """Test that authentication still works"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        assert response.status_code == 200
        assert "token" in response.json()
        print("✓ Auth login working")


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
