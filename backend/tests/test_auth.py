"""
EDARSA HUB - Tests de Autenticación
===================================
Tests de regresión para el módulo de autenticación.

PRIORIDAD 2: Tests básicos de regresión (Abril 2026)

Cobertura:
- Login exitoso
- Login fallido (credenciales incorrectas)
- Validación de token
- Endpoint /auth/me
"""

import pytest
import pytest_asyncio


class TestAuth:
    """Tests del módulo de autenticación"""
    
    @pytest.mark.smoke
    @pytest.mark.asyncio
    async def test_login_success(self, http_client, api_base_url, test_credentials):
        """Test: Login exitoso con credenciales válidas"""
        response = await http_client.post(
            f"{api_base_url}/api/auth/login",
            json=test_credentials
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert len(data["token"]) > 20
    
    @pytest.mark.smoke
    @pytest.mark.asyncio
    async def test_login_wrong_password(self, http_client, api_base_url):
        """Test: Login fallido con contraseña incorrecta"""
        response = await http_client.post(
            f"{api_base_url}/api/auth/login",
            json={"email": "admin@inventario.com", "password": "wrong_password"}
        )
        
        assert response.status_code == 401
    
    @pytest.mark.smoke
    @pytest.mark.asyncio
    async def test_login_nonexistent_user(self, http_client, api_base_url):
        """Test: Login fallido con usuario inexistente"""
        response = await http_client.post(
            f"{api_base_url}/api/auth/login",
            json={"email": "noexiste@test.com", "password": "test123"}
        )
        
        assert response.status_code == 401
    
    @pytest.mark.smoke
    @pytest.mark.asyncio
    async def test_auth_me(self, http_client, api_base_url, auth_headers):
        """Test: Endpoint /auth/me retorna datos del usuario"""
        response = await http_client.get(
            f"{api_base_url}/api/auth/me",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "email" in data
        assert "role" in data
        assert data["email"] == "admin@inventario.com"
    
    @pytest.mark.smoke
    @pytest.mark.asyncio
    async def test_auth_me_no_token(self, http_client, api_base_url):
        """Test: /auth/me sin token debe fallar"""
        response = await http_client.get(
            f"{api_base_url}/api/auth/me"
        )
        
        # Puede ser 401 o 403 dependiendo de la implementación
        assert response.status_code in [401, 403]
    
    @pytest.mark.smoke
    @pytest.mark.asyncio
    async def test_auth_me_invalid_token(self, http_client, api_base_url):
        """Test: /auth/me con token inválido debe fallar"""
        response = await http_client.get(
            f"{api_base_url}/api/auth/me",
            headers={"Authorization": "Bearer invalid_token_12345"}
        )
        
        assert response.status_code in [401, 403]
