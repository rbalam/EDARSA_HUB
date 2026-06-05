"""
EDARSA HUB - Test Configuration
===============================
Infraestructura base para testing del backend.

PASO 2: Configuración mínima y segura para tests automatizados.

CARACTERÍSTICAS:
- Cliente HTTP para tests de integración (httpx)
- Cliente TestClient para tests unitarios (fastapi.testclient)
- Base para mocks de MongoDB, SQL, Auth y APIs externas
- Fixtures reutilizables sin alterar producción
- Credenciales centralizadas via variables de entorno

USO:
    pytest tests/ -m smoke      # Tests rápidos
    pytest tests/ -m unit       # Tests unitarios con mocks
    pytest tests/ -m integration # Tests de integración

SEGURIDAD:
    Las credenciales de test se obtienen de variables de entorno.
    Ver .env.test.example para configuración.
"""

import pytest
import pytest_asyncio
import os
import sys
from typing import Dict, Any
from unittest.mock import MagicMock, AsyncMock

# Añadir el directorio backend al path para imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Variables de entorno para tests (NO modifica producción)
os.environ.setdefault("MONGO_URL", "mongodb://localhost:27017")
os.environ.setdefault("DB_NAME", "test_database")
os.environ.setdefault("JWT_SECRET", "test_secret_key_for_testing_only")

# =============================================================================
# CREDENCIALES DE TEST CENTRALIZADAS (FASE 2 - Code Quality)
# =============================================================================
# Estas credenciales son para entorno de TEST únicamente.
# En producción usar credenciales reales via variables de entorno.

TEST_ADMIN_PASSWORD = os.environ.get("TEST_ADMIN_PASSWORD", "TestPassword123!")
TEST_ADMIN_EMAIL = os.environ.get("TEST_ADMIN_EMAIL", "admin@inventario.com")
TEST_SUPERADMIN_EMAIL = os.environ.get("TEST_SUPERADMIN_EMAIL", "ricardo@edarsa.com.mx")
TEST_SUPERADMIN_PASSWORD = os.environ.get("TEST_SUPERADMIN_PASSWORD", "TestSuperAdmin123!")
TEST_USER_EMAIL = os.environ.get("TEST_USER_EMAIL", "test@inventario.com")
TEST_USER_PASSWORD = os.environ.get("TEST_USER_PASSWORD", "TestUser123!")
TEST_SUPERVISOR_EMAIL = os.environ.get("TEST_SUPERVISOR_EMAIL", "supervisor@inventario.com")
TEST_SUPERVISOR_PASSWORD = os.environ.get("TEST_SUPERVISOR_PASSWORD", "TestSupervisor123!")


# =============================================================================
# CONFIGURACIÓN DE PYTEST
# =============================================================================

def pytest_configure(config):
    """Registra markers personalizados"""
    config.addinivalue_line("markers", "smoke: Tests rápidos de validación")
    config.addinivalue_line("markers", "regression: Tests de regresión completos")
    config.addinivalue_line("markers", "slow: Tests lentos (SQL real, timeouts)")
    config.addinivalue_line("markers", "unit: Tests unitarios con mocks")
    config.addinivalue_line("markers", "integration: Tests de integración (API real)")


# =============================================================================
# FIXTURES: CONFIGURACIÓN BASE
# =============================================================================

@pytest.fixture(scope="session")
def api_base_url() -> str:
    """URL base para tests de integración contra API real"""
    return os.environ.get(
        "TEST_API_URL", 
        "https://stock-tracker-990.preview.emergentagent.com"
    )


@pytest.fixture(scope="session")
def test_credentials() -> Dict[str, str]:
    """Credenciales de test para autenticación (via env vars)"""
    return {
        "email": TEST_ADMIN_EMAIL,
        "password": TEST_ADMIN_PASSWORD
    }


@pytest.fixture(scope="session")
def superadmin_credentials() -> Dict[str, str]:
    """Credenciales de superadmin para tests de permisos elevados"""
    return {
        "email": TEST_SUPERADMIN_EMAIL,
        "password": TEST_SUPERADMIN_PASSWORD
    }


@pytest.fixture(scope="session")
def supervisor_credentials() -> Dict[str, str]:
    """Credenciales de supervisor para tests de permisos medios"""
    return {
        "email": TEST_SUPERVISOR_EMAIL,
        "password": TEST_SUPERVISOR_PASSWORD
    }


@pytest.fixture(scope="session")
def user_credentials() -> Dict[str, str]:
    """Credenciales de usuario regular para tests de permisos básicos"""
    return {
        "email": TEST_USER_EMAIL,
        "password": TEST_USER_PASSWORD
    }


# Exponer constantes para imports directos en tests legacy
def get_test_password() -> str:
    """Obtiene password de admin para tests legacy."""
    return TEST_ADMIN_PASSWORD


def get_test_admin_email() -> str:
    """Obtiene email de admin para tests legacy."""
    return TEST_ADMIN_EMAIL


# =============================================================================
# FIXTURES: CLIENTE HTTP ASYNC (para tests de integración)
# =============================================================================

@pytest_asyncio.fixture
async def http_client():
    """Cliente HTTP async para tests de integración"""
    import httpx
    async with httpx.AsyncClient(timeout=30.0) as client:
        yield client


@pytest_asyncio.fixture
async def auth_token(http_client, api_base_url, test_credentials) -> str:
    """Obtiene token de autenticación válido desde API real"""
    response = await http_client.post(
        f"{api_base_url}/api/auth/login",
        json=test_credentials
    )
    assert response.status_code == 200, f"Login failed: {response.text}"
    return response.json()["token"]


@pytest_asyncio.fixture
async def auth_headers(auth_token) -> Dict[str, str]:
    """Headers con Bearer token para requests autenticados"""
    return {"Authorization": f"Bearer {auth_token}"}


# =============================================================================
# FIXTURES: TEST CLIENT (para tests unitarios sin servidor)
# =============================================================================

@pytest.fixture(scope="module")
def test_client():
    """
    TestClient de FastAPI para tests unitarios.
    NO requiere servidor corriendo - importa la app directamente.
    
    Uso:
        def test_endpoint(test_client):
            response = test_client.get("/api/health")
            assert response.status_code == 200
    """
    from fastapi.testclient import TestClient
    # Import lazy para evitar efectos secundarios en producción
    from server import app
    
    with TestClient(app) as client:
        yield client


# =============================================================================
# FIXTURES: MOCKS BASE PARA MONGODB
# =============================================================================

@pytest.fixture
def mock_mongo_db():
    """
    Mock básico de la base de datos MongoDB.
    
    Uso:
        def test_con_mongo(mock_mongo_db):
            mock_mongo_db.users.find_one.return_value = {"email": "test@test.com"}
    """
    mock_db = MagicMock()
    
    # Colecciones comunes pre-configuradas
    mock_db.users = MagicMock()
    mock_db.servers = MagicMock()
    mock_db.roles = MagicMock()
    mock_db.kpis_cache = MagicMock()
    mock_db.server_status = MagicMock()
    
    return mock_db


@pytest.fixture
def mock_mongo_collection():
    """Mock de una colección MongoDB individual"""
    collection = MagicMock()
    collection.find_one = AsyncMock(return_value=None)
    collection.find = MagicMock(return_value=MagicMock())
    collection.insert_one = AsyncMock(return_value=MagicMock(inserted_id="test_id"))
    collection.update_one = AsyncMock(return_value=MagicMock(modified_count=1))
    collection.delete_one = AsyncMock(return_value=MagicMock(deleted_count=1))
    return collection


# =============================================================================
# FIXTURES: MOCKS BASE PARA SQL SERVER
# =============================================================================

@pytest.fixture
def mock_sql_query():
    """
    Mock para execute_sql_query.
    
    Uso:
        def test_con_sql(mock_sql_query):
            mock_sql_query.return_value = [{"ventas": 1000}]
            with patch("core.db.execute_sql_query", mock_sql_query):
                result = mi_funcion()
    """
    return MagicMock(return_value=[])


@pytest.fixture
def mock_sql_connection():
    """Mock de conexión SQL Server"""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_cursor.fetchall.return_value = []
    mock_cursor.description = []
    mock_conn.cursor.return_value = mock_cursor
    return mock_conn


# =============================================================================
# FIXTURES: MOCKS BASE PARA AUTENTICACIÓN
# =============================================================================

@pytest.fixture
def mock_current_user():
    """
    Mock de usuario autenticado para bypass de auth.
    
    Uso:
        def test_con_auth(mock_current_user):
            with patch("server.get_current_user", return_value=mock_current_user):
                response = client.get("/api/protected")
    """
    return {
        "id": "test-user-id",
        "email": "test@test.com",
        "name": "Test User",
        "role": "Administrador",
        "active": True,
        "allowed_servers": [],
        "sucursales": []
    }


@pytest.fixture
def mock_user_supervisor():
    """Mock de usuario con rol Supervisor"""
    return {
        "id": "supervisor-id",
        "email": "supervisor@test.com",
        "name": "Supervisor Test",
        "role": "Supervisor",
        "active": True,
        "allowed_servers": ["server-1"],
        "sucursales": ["SUC001"]
    }


@pytest.fixture
def mock_user_regular():
    """Mock de usuario con rol Usuario (restringido)"""
    return {
        "id": "user-id",
        "email": "user@test.com",
        "name": "Regular User",
        "role": "Usuario",
        "active": True,
        "allowed_servers": ["server-1"],
        "sucursales": ["SUC001"]
    }


# =============================================================================
# FIXTURES: MOCKS BASE PARA APIs EXTERNAS
# =============================================================================

@pytest.fixture
def mock_api_local_mpro():
    """
    Mock para APIs locales MPRO.
    
    Uso:
        def test_api_local(mock_api_local_mpro):
            with patch("modules.comercial.adapters.query_api_mpro_local", mock_api_local_mpro):
                result = obtener_ventas()
    """
    mock = MagicMock()
    mock.return_value = {
        "success": True,
        "data": [{"ventas": 50000, "cheques": 100, "pax": 200}],
        "error": None
    }
    return mock


@pytest.fixture
def mock_api_local_offline():
    """Mock de API local que está offline/timeout"""
    mock = MagicMock()
    mock.return_value = {
        "success": False,
        "data": None,
        "error": "Timeout"
    }
    return mock


# =============================================================================
# FIXTURES: DATOS DE PRUEBA COMUNES
# =============================================================================

@pytest.fixture
def sample_server_config() -> Dict[str, Any]:
    """Configuración de servidor de prueba"""
    return {
        "id": "test-server-id",
        "name": "Test Server",
        "host": "localhost",
        "port": 1433,
        "database": "TestDB",
        "username": "test_user",
        "password": "test_pass",
        "system_type": "MPRO",
        "active": True
    }


@pytest.fixture
def sample_kpis_data() -> Dict[str, Any]:
    """Datos de KPIs de prueba"""
    return {
        "ventas": 150000.50,
        "ventas_ant": 140000.00,
        "var_vs_mes_ant": 7.14,
        "pax": 500,
        "cheques": 200,
        "ticket_prom": 300.00,
        "status": "online"
    }


# =============================================================================
# HELPERS PARA TESTS
# =============================================================================

def assert_valid_response(response, expected_status: int = 200):
    """Helper para validar respuesta HTTP"""
    assert response.status_code == expected_status, \
        f"Expected {expected_status}, got {response.status_code}: {response.text}"


def assert_json_structure(data: dict, required_keys: list):
    """Helper para validar estructura JSON"""
    for key in required_keys:
        assert key in data, f"Missing key: {key}"

