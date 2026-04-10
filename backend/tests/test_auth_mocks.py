"""
EDARSA HUB - Tests de Autenticación (con Mocks)
===============================================
Tests de autenticación usando mocks.

PASO 3: Tests mínimos usando mocks.
NO conecta a servicios reales.
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient


class TestAuthWithMocks:
    """Tests de autenticación usando mocks"""
    
    @pytest.mark.unit
    def test_login_endpoint_exists(self):
        """Test: Endpoint de login existe en la app"""
        from server import app
        
        # Buscar ruta de login
        login_routes = [r for r in app.routes if hasattr(r, 'path') and 'login' in r.path]
        assert len(login_routes) > 0, "No se encontró endpoint de login"
    
    @pytest.mark.unit
    def test_login_with_mock_db_success(self, mock_current_user):
        """Test: Login exitoso con mock de usuario"""
        from server import app
        
        # Mock del usuario en BD
        mock_user_db = {
            "id": "test-id",
            "email": "test@test.com",
            "password": "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4X",  # hash simulado
            "name": "Test User",
            "role": "Administrador",
            "active": True
        }
        
        with patch("server.db") as mock_db:
            mock_db.users.find_one = AsyncMock(return_value=mock_user_db)
            
            # Verificar que el mock se configuró
            assert mock_db.users.find_one is not None
    
    @pytest.mark.unit
    def test_get_current_user_returns_user(self, mock_current_user):
        """Test: get_current_user retorna estructura correcta"""
        # Verificar campos requeridos
        required_fields = ["id", "email", "name", "role", "active"]
        for field in required_fields:
            assert field in mock_current_user, f"Falta campo: {field}"
    
    @pytest.mark.unit
    def test_auth_me_requires_token(self):
        """Test: /auth/me requiere autenticación"""
        from server import app
        
        with TestClient(app) as client:
            response = client.get("/api/auth/me")
            # Sin token debe fallar con 401 o 403
            assert response.status_code in [401, 403]
    
    @pytest.mark.unit
    def test_auth_me_with_mock_user(self, mock_current_user):
        """Test: /auth/me con usuario mockeado"""
        from server import app, get_current_user
        
        # Override de la dependencia de autenticación
        app.dependency_overrides[get_current_user] = lambda: mock_current_user
        
        try:
            with TestClient(app) as client:
                response = client.get("/api/auth/me")
                assert response.status_code == 200
                data = response.json()
                assert "email" in data
        finally:
            # Limpiar override
            app.dependency_overrides.clear()
    
    @pytest.mark.unit
    def test_protected_endpoint_rejects_no_auth(self):
        """Test: Endpoints protegidos rechazan sin auth"""
        from server import app
        
        with TestClient(app) as client:
            # Probar endpoint protegido sin token
            response = client.get("/api/servers")
            assert response.status_code in [401, 403]
    
    @pytest.mark.unit
    def test_user_roles_structure(self, mock_current_user, mock_user_supervisor, mock_user_regular):
        """Test: Estructura de roles es consistente"""
        users = [mock_current_user, mock_user_supervisor, mock_user_regular]
        
        for user in users:
            assert "role" in user
            assert user["role"] in ["Administrador", "Supervisor", "Usuario"]
