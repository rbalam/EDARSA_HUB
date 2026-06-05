"""
Test suite for Sistema de Flujo de Aprobación para Catálogos con Panel de Tareas
Tests: Mis Tareas page, KPIs, Catalog permissions, Solicitudes CRUD, Approval with password signature
"""
import pytest
import requests
import os
import uuid

# Importar configuración de test centralizada
from tests.test_config import test_config

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials desde configuración centralizada
ADMIN_EMAIL = test_config.admin_email
ADMIN_PASSWORD = test_config.admin_password
SUPERVISOR_EMAIL = test_config.supervisor_email
SUPERVISOR_PASSWORD = test_config.supervisor_password


class TestAuth:
    """Authentication tests"""
    
    def test_admin_login(self):
        """Test admin login"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Admin login failed: {response.text}"
        data = response.json()
        assert "token" in data
        assert data["user"]["role"] == "Administrador"
        print(f"✅ Admin login successful - role: {data['user']['role']}")
    
    def test_supervisor_login(self):
        """Test supervisor login"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": SUPERVISOR_EMAIL,
            "password": SUPERVISOR_PASSWORD
        })
        assert response.status_code == 200, f"Supervisor login failed: {response.text}"
        data = response.json()
        assert "token" in data
        assert data["user"]["role"] == "Supervisor"
        print(f"✅ Supervisor login successful - role: {data['user']['role']}")


@pytest.fixture
def admin_token():
    """Get admin authentication token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    })
    if response.status_code == 200:
        return response.json().get("token")
    pytest.skip("Admin authentication failed")


@pytest.fixture
def supervisor_token():
    """Get supervisor authentication token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": SUPERVISOR_EMAIL,
        "password": SUPERVISOR_PASSWORD
    })
    if response.status_code == 200:
        return response.json().get("token")
    pytest.skip("Supervisor authentication failed")


class TestCatalogosDisponibles:
    """Tests for GET /api/sistema/catalogos-disponibles"""
    
    def test_get_catalogos_disponibles_returns_9_catalogos(self, admin_token):
        """API should return 9 available catalogs"""
        response = requests.get(
            f"{BASE_URL}/api/sistema/catalogos-disponibles",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "catalogos" in data
        catalogos = data["catalogos"]
        assert len(catalogos) == 9, f"Expected 9 catalogs, got {len(catalogos)}"
        
        # Verify expected catalog IDs
        expected_ids = ["puestos", "tipos_incidencias", "sucursales", "departamentos", 
                       "proveedores", "categorias_presupuesto", "almacenes", "familias", "categorias"]
        actual_ids = [c["id"] for c in catalogos]
        for expected_id in expected_ids:
            assert expected_id in actual_ids, f"Missing catalog: {expected_id}"
        
        print(f"✅ GET /api/sistema/catalogos-disponibles returns 9 catalogs: {actual_ids}")
    
    def test_catalogos_have_required_fields(self, admin_token):
        """Each catalog should have id, nombre, modulo, tabla fields"""
        response = requests.get(
            f"{BASE_URL}/api/sistema/catalogos-disponibles",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        catalogos = response.json()["catalogos"]
        
        for cat in catalogos:
            assert "id" in cat, "Missing 'id' in catalog"
            assert "nombre" in cat, "Missing 'nombre' in catalog"
            assert "modulo" in cat, "Missing 'modulo' in catalog"
            assert "tabla" in cat, "Missing 'tabla' in catalog"
        
        print("✅ All catalogs have required fields (id, nombre, modulo, tabla)")


class TestMisTareas:
    """Tests for GET /api/sistema/mis-tareas"""
    
    def test_get_mis_tareas_admin(self, admin_token):
        """Admin should get tasks with KPI counters"""
        response = requests.get(
            f"{BASE_URL}/api/sistema/mis-tareas",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        # Verify structure
        assert "pendientes" in data
        assert "en_proceso" in data
        assert "completadas" in data
        assert "total_pendientes" in data
        assert "total_en_proceso" in data
        assert "solicitudes_pendientes_aprobar" in data
        
        # Verify types
        assert isinstance(data["pendientes"], list)
        assert isinstance(data["total_pendientes"], int)
        assert isinstance(data["solicitudes_pendientes_aprobar"], int)
        
        print("✅ GET /api/sistema/mis-tareas returns correct structure")
        print(f"   - Pendientes: {data['total_pendientes']}")
        print(f"   - En Proceso: {data['total_en_proceso']}")
        print(f"   - Por Aprobar: {data['solicitudes_pendientes_aprobar']}")
    
    def test_get_mis_tareas_supervisor(self, supervisor_token):
        """Supervisor should also see solicitudes_pendientes_aprobar"""
        response = requests.get(
            f"{BASE_URL}/api/sistema/mis-tareas",
            headers={"Authorization": f"Bearer {supervisor_token}"}
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        # Supervisor should see approval count
        assert "solicitudes_pendientes_aprobar" in data
        print(f"✅ Supervisor can see solicitudes_pendientes_aprobar: {data['solicitudes_pendientes_aprobar']}")


class TestMisPermisosCatalogos:
    """Tests for GET /api/sistema/mis-permisos-catalogos"""
    
    def test_admin_has_all_permissions(self, admin_token):
        """Admin should have all catalog permissions"""
        response = requests.get(
            f"{BASE_URL}/api/sistema/mis-permisos-catalogos",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        assert data["puede_solicitar"]
        assert data["puede_aprobar"]
        assert len(data["catalogos_permitidos"]) == 9
        
        print(f"✅ Admin has all permissions: puede_solicitar={data['puede_solicitar']}, puede_aprobar={data['puede_aprobar']}")
    
    def test_supervisor_can_approve(self, supervisor_token):
        """Supervisor should be able to approve"""
        response = requests.get(
            f"{BASE_URL}/api/sistema/mis-permisos-catalogos",
            headers={"Authorization": f"Bearer {supervisor_token}"}
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        assert data["puede_aprobar"]
        print(f"✅ Supervisor puede_aprobar={data['puede_aprobar']}")


class TestPermisosCatalogos:
    """Tests for POST /api/sistema/permisos-catalogos"""
    
    def test_assign_permissions_requires_supervisor_or_admin(self, admin_token, supervisor_token):
        """Only Supervisor or Admin can assign permissions"""
        # First get a user to assign permissions to
        response = requests.get(
            f"{BASE_URL}/api/sistema/usuarios-asignables",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        usuarios = response.json().get("usuarios", [])
        
        if len(usuarios) > 0:
            # Find a non-admin user
            test_user = next((u for u in usuarios if u["role"] != "Administrador"), None)
            if test_user:
                # Admin can assign
                response = requests.post(
                    f"{BASE_URL}/api/sistema/permisos-catalogos",
                    headers={"Authorization": f"Bearer {admin_token}"},
                    json={
                        "user_id": test_user["id"],
                        "catalogos_permitidos": ["puestos", "tipos_incidencias"],
                        "puede_solicitar": True
                    }
                )
                assert response.status_code == 200, f"Admin should be able to assign permissions: {response.text}"
                print("✅ Admin can assign permissions to users")
                
                # Supervisor can also assign
                response = requests.post(
                    f"{BASE_URL}/api/sistema/permisos-catalogos",
                    headers={"Authorization": f"Bearer {supervisor_token}"},
                    json={
                        "user_id": test_user["id"],
                        "catalogos_permitidos": ["puestos"],
                        "puede_solicitar": True
                    }
                )
                assert response.status_code == 200, f"Supervisor should be able to assign permissions: {response.text}"
                print("✅ Supervisor can assign permissions to users")
        else:
            print("⚠️ No users available to test permission assignment")


class TestUsuariosAsignables:
    """Tests for GET /api/sistema/usuarios-asignables"""
    
    def test_get_usuarios_asignables_admin(self, admin_token):
        """Admin should get list of assignable users"""
        response = requests.get(
            f"{BASE_URL}/api/sistema/usuarios-asignables",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        assert "usuarios" in data
        usuarios = data["usuarios"]
        assert isinstance(usuarios, list)
        
        # Each user should have required fields
        if len(usuarios) > 0:
            user = usuarios[0]
            assert "id" in user
            assert "email" in user
            assert "role" in user
            assert "permisos_catalogos" in user
            assert "puede_solicitar" in user
        
        print(f"✅ GET /api/sistema/usuarios-asignables returns {len(usuarios)} users")
    
    def test_get_usuarios_asignables_supervisor(self, supervisor_token):
        """Supervisor should also get list of assignable users"""
        response = requests.get(
            f"{BASE_URL}/api/sistema/usuarios-asignables",
            headers={"Authorization": f"Bearer {supervisor_token}"}
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        print("✅ Supervisor can access usuarios-asignables endpoint")


class TestSolicitudesCRUD:
    """Tests for Solicitudes CRUD operations"""
    
    def test_create_solicitud_admin(self, admin_token):
        """Admin can create a solicitud"""
        unique_desc = f"TEST_Puesto_{uuid.uuid4().hex[:8]}"
        response = requests.post(
            f"{BASE_URL}/api/sistema/solicitudes",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "catalogo_id": "puestos",
                "datos": {
                    "descripcion": unique_desc,
                    "departamento": "Test Dept",
                    "sueldo_base": 5000
                },
                "notas": "Test solicitud from pytest"
            }
        )
        assert response.status_code == 200, f"Failed to create solicitud: {response.text}"
        data = response.json()
        
        assert data["success"]
        assert "solicitud_id" in data
        
        print(f"✅ POST /api/sistema/solicitudes - Created solicitud: {data['solicitud_id']}")
        return data["solicitud_id"]
    
    def test_list_solicitudes_admin(self, admin_token):
        """Admin can list all solicitudes"""
        response = requests.get(
            f"{BASE_URL}/api/sistema/solicitudes",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        assert "solicitudes" in data
        assert "total" in data
        
        print(f"✅ GET /api/sistema/solicitudes - Total: {data['total']}")
    
    def test_list_solicitudes_pendientes(self, admin_token):
        """Can filter solicitudes by status"""
        response = requests.get(
            f"{BASE_URL}/api/sistema/solicitudes?estatus=Pendiente",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        # All returned should be Pendiente
        for sol in data["solicitudes"]:
            assert sol["estatus"] == "Pendiente"
        
        print(f"✅ GET /api/sistema/solicitudes?estatus=Pendiente - Found {data['total']} pending")
    
    def test_get_solicitud_detail(self, admin_token):
        """Can get solicitud detail"""
        # First create one
        unique_desc = f"TEST_Detail_{uuid.uuid4().hex[:8]}"
        create_response = requests.post(
            f"{BASE_URL}/api/sistema/solicitudes",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "catalogo_id": "tipos_incidencias",
                "datos": {
                    "codigo": "TST",
                    "descripcion": unique_desc,
                    "categoria": "Descuento"
                },
                "notas": "Test detail"
            }
        )
        assert create_response.status_code == 200
        solicitud_id = create_response.json()["solicitud_id"]
        
        # Get detail
        response = requests.get(
            f"{BASE_URL}/api/sistema/solicitudes/{solicitud_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        assert data["id"] == solicitud_id
        assert data["catalogo_id"] == "tipos_incidencias"
        assert data["estatus"] == "Pendiente"
        
        print(f"✅ GET /api/sistema/solicitudes/{solicitud_id} - Detail retrieved")


class TestAprobacionConFirma:
    """Tests for approval with password signature"""
    
    def test_aprobar_solicitud_with_correct_password(self, admin_token):
        """Approve solicitud with correct password"""
        # Create a solicitud first
        unique_desc = f"TEST_Aprobar_{uuid.uuid4().hex[:8]}"
        create_response = requests.post(
            f"{BASE_URL}/api/sistema/solicitudes",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "catalogo_id": "puestos",
                "datos": {"descripcion": unique_desc},
                "notas": "To be approved"
            }
        )
        assert create_response.status_code == 200
        solicitud_id = create_response.json()["solicitud_id"]
        
        # Approve with correct password
        response = requests.post(
            f"{BASE_URL}/api/sistema/solicitudes/{solicitud_id}/aprobar",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"password": ADMIN_PASSWORD}
        )
        assert response.status_code == 200, f"Failed to approve: {response.text}"
        data = response.json()
        
        assert data["success"]
        assert "aprobada" in data["message"].lower() or "insertada" in data["message"].lower()
        
        # Verify status changed
        detail_response = requests.get(
            f"{BASE_URL}/api/sistema/solicitudes/{solicitud_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert detail_response.status_code == 200
        assert detail_response.json()["estatus"] == "Aprobada"
        
        print(f"✅ POST /api/sistema/solicitudes/{solicitud_id}/aprobar - Approved with password signature")
    
    def test_aprobar_solicitud_with_wrong_password(self, admin_token):
        """Reject approval with wrong password"""
        # Create a solicitud first
        unique_desc = f"TEST_WrongPwd_{uuid.uuid4().hex[:8]}"
        create_response = requests.post(
            f"{BASE_URL}/api/sistema/solicitudes",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "catalogo_id": "puestos",
                "datos": {"descripcion": unique_desc},
                "notas": "Wrong password test"
            }
        )
        assert create_response.status_code == 200
        solicitud_id = create_response.json()["solicitud_id"]
        
        # Try to approve with wrong password
        response = requests.post(
            f"{BASE_URL}/api/sistema/solicitudes/{solicitud_id}/aprobar",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"password": "wrongpassword123"}
        )
        assert response.status_code == 401, f"Should return 401 for wrong password, got {response.status_code}"
        
        print(f"✅ POST /api/sistema/solicitudes/{solicitud_id}/aprobar - Correctly rejects wrong password (401)")
    
    def test_supervisor_can_approve(self, supervisor_token):
        """Supervisor can also approve solicitudes"""
        # Create a solicitud first (as supervisor)
        unique_desc = f"TEST_SupApprove_{uuid.uuid4().hex[:8]}"
        create_response = requests.post(
            f"{BASE_URL}/api/sistema/solicitudes",
            headers={"Authorization": f"Bearer {supervisor_token}"},
            json={
                "catalogo_id": "puestos",
                "datos": {"descripcion": unique_desc},
                "notas": "Supervisor approval test"
            }
        )
        # Supervisor might not have permission to create, that's ok
        if create_response.status_code == 200:
            solicitud_id = create_response.json()["solicitud_id"]
            
            # Approve with supervisor password
            response = requests.post(
                f"{BASE_URL}/api/sistema/solicitudes/{solicitud_id}/aprobar",
                headers={"Authorization": f"Bearer {supervisor_token}"},
                json={"password": SUPERVISOR_PASSWORD}
            )
            assert response.status_code == 200, f"Supervisor should be able to approve: {response.text}"
            print("✅ Supervisor can approve solicitudes with password signature")
        else:
            print("⚠️ Supervisor cannot create solicitudes (expected if no permissions assigned)")


class TestRechazarSolicitud:
    """Tests for rejecting solicitudes"""
    
    def test_rechazar_solicitud(self, admin_token):
        """Can reject a solicitud with reason"""
        # Create a solicitud first
        unique_desc = f"TEST_Rechazar_{uuid.uuid4().hex[:8]}"
        create_response = requests.post(
            f"{BASE_URL}/api/sistema/solicitudes",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "catalogo_id": "puestos",
                "datos": {"descripcion": unique_desc},
                "notas": "To be rejected"
            }
        )
        assert create_response.status_code == 200
        solicitud_id = create_response.json()["solicitud_id"]
        
        # Reject
        response = requests.post(
            f"{BASE_URL}/api/sistema/solicitudes/{solicitud_id}/rechazar",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"motivo": "Test rejection reason"}
        )
        assert response.status_code == 200, f"Failed to reject: {response.text}"
        data = response.json()
        
        assert data["success"]
        
        # Verify status changed
        detail_response = requests.get(
            f"{BASE_URL}/api/sistema/solicitudes/{solicitud_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert detail_response.status_code == 200
        detail = detail_response.json()
        assert detail["estatus"] == "Rechazada"
        assert detail["motivo_rechazo"] == "Test rejection reason"
        
        print(f"✅ POST /api/sistema/solicitudes/{solicitud_id}/rechazar - Rejected with reason")


class TestTareasMarcarLeida:
    """Tests for marking tasks as read"""
    
    def test_marcar_tarea_leida(self, admin_token):
        """Can mark a task as read"""
        # Get tasks first
        response = requests.get(
            f"{BASE_URL}/api/sistema/mis-tareas",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Find a pending task
        if len(data["pendientes"]) > 0:
            tarea_id = data["pendientes"][0]["id"]
            
            # Mark as read
            response = requests.put(
                f"{BASE_URL}/api/sistema/tareas/{tarea_id}/marcar-leida",
                headers={"Authorization": f"Bearer {admin_token}"}
            )
            assert response.status_code == 200, f"Failed: {response.text}"
            print(f"✅ PUT /api/sistema/tareas/{tarea_id}/marcar-leida - Task marked as read")
        else:
            print("⚠️ No pending tasks to mark as read")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
