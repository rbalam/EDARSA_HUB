"""
Test suite for RH Module - Cobertura completa de endpoints migrados
=====================================================================

FASE RH-POST-1: Estabilización y cobertura básica

SUITES DEFINIDAS:
================

1. SUITE OBLIGATORIA (siempre debe pasar, no requiere SQL Server):
   - TestRHAuth: Autenticación básica
   - TestRHEndpointsRequireAuth: Validación 403 sin token
   - TestRHValidacionPydantic: Validación de schemas (errores 422)
   - TestRHScriptsEstaticos: Scripts SQL estáticos

2. SUITE DE INTEGRACIÓN (requiere EDARSA HUB SQL Server):
   - TestRHIntegracionColaboradores
   - TestRHIntegracionIncidencias
   - TestRHIntegracionAsistencia
   - TestRHIntegracionFlujoNomina
   - TestRHIntegracionAuditoria
   - TestRHIntegracionReclutamiento
   
   Estos tests usan pytest.skip() si EDARSA HUB no está configurado.

EJECUCIÓN:
=========
# Suite completa RH:
python -m pytest tests/test_rh_modular.py -v

# Suite obligatoria solamente (siempre pasa):
python -m pytest tests/test_rh_modular.py -v -k "Auth or RequireAuth or Pydantic or Estaticos"

# Suite de integración (requiere SQL Server):
python -m pytest tests/test_rh_modular.py -v -k "Integracion"
"""
import pytest
import requests
import os

# Import centralized test credentials
from conftest import TEST_ADMIN_EMAIL, TEST_ADMIN_PASSWORD

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://stock-tracker-990.preview.emergentagent.com').rstrip('/')

# Test credentials (centralized)
ADMIN_EMAIL = os.environ.get("TEST_ADMIN_EMAIL", TEST_ADMIN_EMAIL)
ADMIN_PASSWORD = os.environ.get("TEST_ADMIN_PASSWORD", TEST_ADMIN_PASSWORD)


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture(scope="module")
def admin_token():
    """Get admin authentication token (cached per module)"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    })
    if response.status_code != 200:
        pytest.skip("Admin login failed - cannot run tests")
    return response.json()["token"]


@pytest.fixture
def auth_headers(admin_token):
    """Get authorization headers"""
    return {"Authorization": f"Bearer {admin_token}"}


def check_edarsa_hub_available(response):
    """Check if EDARSA HUB is available based on response"""
    if response.status_code == 404:
        data = response.json()
        if "EDARSA HUB no configurado" in data.get("detail", ""):
            pytest.skip("EDARSA HUB no configurado - test de integración omitido")


# =============================================================================
# SUITE OBLIGATORIA: AUTENTICACIÓN
# =============================================================================

class TestRHAuth:
    """Tests de autenticación básica para módulo RH"""
    
    def test_admin_login_exitoso(self):
        """Test: Login admin retorna token válido"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "token" in data
        assert len(data["token"]) > 20  # JWT tiene más de 20 chars


# =============================================================================
# SUITE OBLIGATORIA: ENDPOINTS REQUIEREN AUTENTICACIÓN
# =============================================================================

class TestRHEndpointsRequireAuth:
    """Tests: Todos los endpoints RH requieren autenticación"""
    
    # Colaboradores
    def test_colaboradores_require_auth(self):
        """GET /rrhh/colaboradores requiere token"""
        response = requests.get(f"{BASE_URL}/api/rrhh/colaboradores")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
    
    # Incidencias
    def test_incidencias_require_auth(self):
        """GET /rrhh/incidencias requiere token"""
        response = requests.get(f"{BASE_URL}/api/rrhh/incidencias")
        assert response.status_code in [401, 403]
    
    # Asistencia
    def test_asistencia_require_auth(self):
        """GET /rrhh/asistencia requiere token"""
        response = requests.get(f"{BASE_URL}/api/rrhh/asistencia")
        assert response.status_code in [401, 403]
    
    # Flujo Nómina
    def test_flujo_nomina_require_auth(self):
        """GET /rrhh/nominas/flujo requiere token"""
        response = requests.get(f"{BASE_URL}/api/rrhh/nominas/flujo")
        assert response.status_code in [401, 403]
    
    # Auditoría
    def test_auditoria_require_auth(self):
        """GET /rrhh/auditoria-fiscal requiere token"""
        response = requests.get(f"{BASE_URL}/api/rrhh/auditoria-fiscal")
        assert response.status_code in [401, 403]
    
    # Dashboard
    def test_dashboard_require_auth(self):
        """GET /rrhh/dashboard requiere token"""
        response = requests.get(f"{BASE_URL}/api/rrhh/dashboard")
        assert response.status_code in [401, 403]
    
    # Vacantes
    def test_vacantes_require_auth(self):
        """GET /rrhh/vacantes requiere token"""
        response = requests.get(f"{BASE_URL}/api/rrhh/vacantes")
        assert response.status_code in [401, 403]
    
    # Candidatos
    def test_candidatos_require_auth(self):
        """GET /rrhh/candidatos requiere token"""
        response = requests.get(f"{BASE_URL}/api/rrhh/candidatos")
        assert response.status_code in [401, 403]
    
    # Dashboard Reclutamiento
    def test_reclutamiento_dashboard_require_auth(self):
        """GET /rrhh/reclutamiento/dashboard requiere token"""
        response = requests.get(f"{BASE_URL}/api/rrhh/reclutamiento/dashboard")
        assert response.status_code in [401, 403]


# =============================================================================
# SUITE OBLIGATORIA: VALIDACIÓN PYDANTIC (no requiere SQL)
# =============================================================================

class TestRHValidacionPydantic:
    """Tests de validación Pydantic - siempre pasan (422 esperado)"""
    
    # --- Asistencia ---
    def test_asistencia_tipo_registro_invalido(self, auth_headers):
        """POST /rrhh/asistencia rechaza tipo_registro inválido"""
        response = requests.post(
            f"{BASE_URL}/api/rrhh/asistencia",
            headers=auth_headers,
            json={"colaborador_id": 1, "tipo_registro": "TipoInvalido"}
        )
        assert response.status_code == 422, f"Expected 422, got {response.status_code}"
        assert "tipo_registro" in response.text.lower()
    
    def test_asistencia_colaborador_id_negativo(self, auth_headers):
        """POST /rrhh/asistencia rechaza colaborador_id <= 0"""
        response = requests.post(
            f"{BASE_URL}/api/rrhh/asistencia",
            headers=auth_headers,
            json={"colaborador_id": -1, "tipo_registro": "Entrada"}
        )
        assert response.status_code == 422
    
    # --- Flujo Nómina ---
    def test_flujo_nomina_semana_invalida(self, auth_headers):
        """POST /rrhh/nominas/flujo rechaza semana > 53"""
        response = requests.post(
            f"{BASE_URL}/api/rrhh/nominas/flujo",
            headers=auth_headers,
            json={"sucursal_id": 1, "semana_anio": 202699}  # Semana 99 inválida
        )
        assert response.status_code == 422
        assert "semana" in response.text.lower()
    
    def test_flujo_nomina_validar_gerente_sin_motivo(self, auth_headers):
        """PUT validar-gerente rechaza rechazo sin motivo"""
        response = requests.put(
            f"{BASE_URL}/api/rrhh/nominas/flujo/1/validar-gerente",
            headers=auth_headers,
            json={"aprobado": False}  # Falta motivo_rechazo
        )
        assert response.status_code == 422
        assert "motivo" in response.text.lower()
    
    # --- Vacantes ---
    def test_vacante_tipo_contrato_invalido(self, auth_headers):
        """POST /rrhh/vacantes rechaza tipo_contrato inválido"""
        response = requests.post(
            f"{BASE_URL}/api/rrhh/vacantes",
            headers=auth_headers,
            json={
                "sucursal_id": 1,
                "puesto_id": 1,
                "titulo": "Test",
                "tipo_contrato": "ContratoInvalido"
            }
        )
        assert response.status_code == 422
        assert "tipo_contrato" in response.text.lower()
    
    def test_vacante_titulo_vacio(self, auth_headers):
        """POST /rrhh/vacantes rechaza título vacío"""
        response = requests.post(
            f"{BASE_URL}/api/rrhh/vacantes",
            headers=auth_headers,
            json={
                "sucursal_id": 1,
                "puesto_id": 1,
                "titulo": "",
                "tipo_contrato": "Tiempo Completo"
            }
        )
        assert response.status_code == 422
    
    # --- Candidatos ---
    def test_candidato_email_invalido(self, auth_headers):
        """POST /rrhh/candidatos rechaza email inválido"""
        response = requests.post(
            f"{BASE_URL}/api/rrhh/candidatos",
            headers=auth_headers,
            json={
                "vacante_id": 1,
                "nombre": "Juan Perez",
                "email": "correo-sin-arroba"
            }
        )
        assert response.status_code == 422
        assert "email" in response.text.lower()
    
    def test_candidato_puntuacion_fuera_rango(self, auth_headers):
        """PUT /rrhh/candidatos rechaza puntuación > 100"""
        response = requests.put(
            f"{BASE_URL}/api/rrhh/candidatos/1",
            headers=auth_headers,
            json={"puntuacion": 150}  # Max es 100
        )
        assert response.status_code == 422


# =============================================================================
# SUITE OBLIGATORIA: SCRIPTS ESTÁTICOS (no requiere SQL)
# =============================================================================

class TestRHScriptsEstaticos:
    """Tests de scripts SQL estáticos - no requieren BD"""
    
    def test_script_catalogos_retorna_sql(self, auth_headers):
        """GET /rrhh/catalogos/script-inicializacion retorna SQL válido"""
        response = requests.get(
            f"{BASE_URL}/api/rrhh/catalogos/script-inicializacion",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "script" in data
        assert "CREATE TABLE" in data["script"]
        assert "RH_Cat_Puestos" in data["script"]
    
    def test_script_reclutamiento_retorna_sql(self, auth_headers):
        """GET /rrhh/reclutamiento/script-inicializacion retorna SQL válido"""
        response = requests.get(
            f"{BASE_URL}/api/rrhh/reclutamiento/script-inicializacion",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "script" in data
        assert "CREATE TABLE" in data["script"]
        assert "RH_Vacantes" in data["script"]
        assert "RH_Candidatos" in data["script"]
    
    def test_plantilla_incidencias_descarga(self, auth_headers):
        """GET /rrhh/incidencias/plantilla-excel descarga archivo"""
        response = requests.get(
            f"{BASE_URL}/api/rrhh/incidencias/plantilla-excel",
            headers=auth_headers
        )
        assert response.status_code == 200
        # Verificar que es un archivo Excel
        content_type = response.headers.get("content-type", "")
        assert "spreadsheet" in content_type or "octet-stream" in content_type
        # Verificar que tiene contenido
        assert len(response.content) > 100


# =============================================================================
# SUITE DE INTEGRACIÓN: COLABORADORES (requiere EDARSA HUB)
# =============================================================================

class TestRHIntegracionColaboradores:
    """Tests de integración para Colaboradores - requiere EDARSA HUB"""
    
    def test_listar_colaboradores(self, auth_headers):
        """GET /rrhh/colaboradores retorna lista"""
        response = requests.get(
            f"{BASE_URL}/api/rrhh/colaboradores",
            headers=auth_headers
        )
        check_edarsa_hub_available(response)
        assert response.status_code == 200
        data = response.json()
        assert "colaboradores" in data
        assert "total" in data


# =============================================================================
# SUITE DE INTEGRACIÓN: INCIDENCIAS (requiere EDARSA HUB)
# =============================================================================

class TestRHIntegracionIncidencias:
    """Tests de integración para Incidencias - requiere EDARSA HUB"""
    
    def test_listar_incidencias(self, auth_headers):
        """GET /rrhh/incidencias retorna lista"""
        response = requests.get(
            f"{BASE_URL}/api/rrhh/incidencias",
            headers=auth_headers
        )
        check_edarsa_hub_available(response)
        assert response.status_code == 200
        data = response.json()
        assert "incidencias" in data


# =============================================================================
# SUITE DE INTEGRACIÓN: ASISTENCIA (requiere EDARSA HUB)
# =============================================================================

class TestRHIntegracionAsistencia:
    """Tests de integración para Asistencia - requiere EDARSA HUB"""
    
    def test_listar_asistencias(self, auth_headers):
        """GET /rrhh/asistencia retorna lista"""
        response = requests.get(
            f"{BASE_URL}/api/rrhh/asistencia",
            headers=auth_headers
        )
        check_edarsa_hub_available(response)
        assert response.status_code == 200
        data = response.json()
        assert "asistencias" in data


# =============================================================================
# SUITE DE INTEGRACIÓN: FLUJO NÓMINA (requiere EDARSA HUB)
# =============================================================================

class TestRHIntegracionFlujoNomina:
    """Tests de integración para Flujo Nómina - requiere EDARSA HUB"""
    
    def test_listar_flujos(self, auth_headers):
        """GET /rrhh/nominas/flujo retorna lista"""
        response = requests.get(
            f"{BASE_URL}/api/rrhh/nominas/flujo",
            headers=auth_headers
        )
        check_edarsa_hub_available(response)
        assert response.status_code == 200
        data = response.json()
        assert "flujos" in data


# =============================================================================
# SUITE DE INTEGRACIÓN: AUDITORÍA (requiere EDARSA HUB)
# =============================================================================

class TestRHIntegracionAuditoria:
    """Tests de integración para Auditoría - requiere EDARSA HUB"""
    
    def test_listar_auditoria(self, auth_headers):
        """GET /rrhh/auditoria-fiscal retorna lista"""
        response = requests.get(
            f"{BASE_URL}/api/rrhh/auditoria-fiscal",
            headers=auth_headers
        )
        check_edarsa_hub_available(response)
        assert response.status_code == 200
        data = response.json()
        assert "auditoria" in data
    
    def test_dashboard_rh(self, auth_headers):
        """GET /rrhh/dashboard retorna métricas"""
        response = requests.get(
            f"{BASE_URL}/api/rrhh/dashboard",
            headers=auth_headers
        )
        check_edarsa_hub_available(response)
        assert response.status_code == 200
        data = response.json()
        assert "resumen" in data or "por_departamento" in data


# =============================================================================
# SUITE DE INTEGRACIÓN: RECLUTAMIENTO (requiere EDARSA HUB)
# =============================================================================

class TestRHIntegracionReclutamiento:
    """Tests de integración para Reclutamiento - requiere EDARSA HUB"""
    
    def test_listar_vacantes(self, auth_headers):
        """GET /rrhh/vacantes retorna lista"""
        response = requests.get(
            f"{BASE_URL}/api/rrhh/vacantes",
            headers=auth_headers
        )
        check_edarsa_hub_available(response)
        assert response.status_code == 200
        data = response.json()
        assert "vacantes" in data
    
    def test_listar_candidatos(self, auth_headers):
        """GET /rrhh/candidatos retorna lista"""
        response = requests.get(
            f"{BASE_URL}/api/rrhh/candidatos",
            headers=auth_headers
        )
        check_edarsa_hub_available(response)
        assert response.status_code == 200
        data = response.json()
        assert "candidatos" in data
    
    def test_dashboard_reclutamiento(self, auth_headers):
        """GET /rrhh/reclutamiento/dashboard retorna métricas"""
        response = requests.get(
            f"{BASE_URL}/api/rrhh/reclutamiento/dashboard",
            headers=auth_headers
        )
        check_edarsa_hub_available(response)
        assert response.status_code == 200
        data = response.json()
        assert "vacantes_por_estatus" in data or "nota" in data
