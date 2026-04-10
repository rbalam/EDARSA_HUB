"""
EDARSA HUB - Test Configuration
===============================
Configuración de pytest y fixtures compartidos.

PRIORIDAD 2: Tests básicos de regresión (Abril 2026)
"""

import pytest
import pytest_asyncio
import os
import sys
from typing import Generator, AsyncGenerator

# Añadir el directorio backend al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Variables de entorno para tests
os.environ.setdefault("MONGO_URL", "mongodb://localhost:27017")
os.environ.setdefault("DB_NAME", "test_database")
os.environ.setdefault("JWT_SECRET", "test_secret_key_for_testing_only")


# =============================================================================
# FIXTURES SÍNCRONOS
# =============================================================================

@pytest.fixture(scope="session")
def api_base_url() -> str:
    """URL base para tests de API"""
    return os.environ.get(
        "TEST_API_URL", 
        "https://stock-tracker-990.preview.emergentagent.com"
    )


@pytest.fixture(scope="session")
def test_credentials() -> dict:
    """Credenciales de test"""
    return {
        "email": "admin@inventario.com",
        "password": "admin123"
    }


# =============================================================================
# FIXTURES ASYNC
# =============================================================================

@pytest_asyncio.fixture
async def http_client():
    """Cliente HTTP async para tests"""
    import httpx
    async with httpx.AsyncClient(timeout=30.0) as client:
        yield client


@pytest_asyncio.fixture
async def auth_token(http_client, api_base_url, test_credentials) -> str:
    """Obtiene un token de autenticación válido"""
    response = await http_client.post(
        f"{api_base_url}/api/auth/login",
        json=test_credentials
    )
    assert response.status_code == 200, f"Login failed: {response.text}"
    return response.json()["token"]


@pytest_asyncio.fixture
async def auth_headers(auth_token) -> dict:
    """Headers con autenticación"""
    return {"Authorization": f"Bearer {auth_token}"}


# =============================================================================
# CONFIGURACIÓN DE PYTEST
# =============================================================================

def pytest_configure(config):
    """Configuración inicial de pytest"""
    config.addinivalue_line(
        "markers", "smoke: mark test as smoke test (quick validation)"
    )
    config.addinivalue_line(
        "markers", "regression: mark test as regression test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
