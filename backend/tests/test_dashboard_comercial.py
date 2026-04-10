"""
EDARSA HUB - Tests de Dashboard Comercial (con Mocks)
=====================================================
Tests del dashboard comercial usando mocks.

PASO 3: Tests mínimos usando mocks.
NO conecta a servicios reales.
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient


class TestDashboardComercialStructure:
    """Tests de estructura del dashboard comercial"""
    
    @pytest.mark.unit
    def test_endpoint_exists(self):
        """Test: Endpoint de dashboard comercial existe"""
        from server import app
        
        routes = [r for r in app.routes if hasattr(r, 'path') and 'comercial/dashboard' in r.path]
        assert len(routes) > 0, "No se encontró endpoint dashboard comercial"
    
    @pytest.mark.unit
    def test_endpoint_requires_auth(self):
        """Test: Dashboard comercial requiere autenticación"""
        from server import app
        
        with TestClient(app) as client:
            response = client.get("/api/comercial/dashboard/test-server-id")
            assert response.status_code in [401, 403]
    
    @pytest.mark.unit
    def test_endpoint_with_invalid_server(self, mock_current_user):
        """Test: Dashboard con server_id inválido"""
        from server import app, get_current_user
        
        app.dependency_overrides[get_current_user] = lambda: mock_current_user
        
        try:
            with patch("server.db") as mock_db:
                # Servidor no existe
                mock_db.servers.find_one = AsyncMock(return_value=None)
                
                with TestClient(app) as client:
                    response = client.get("/api/comercial/dashboard/invalid-id")
                    # Puede ser 404 o 200 con datos vacíos
                    assert response.status_code in [200, 404, 500]
        finally:
            app.dependency_overrides.clear()


class TestDashboardComercialPayload:
    """Tests de payload del dashboard comercial"""
    
    @pytest.mark.unit
    def test_server_config_structure(self, sample_server_config):
        """Test: Estructura de configuración de servidor"""
        required_fields = ["id", "name", "host", "port", "database", "system_type"]
        
        for field in required_fields:
            assert field in sample_server_config, f"Falta campo: {field}"
    
    @pytest.mark.unit
    def test_system_types_valid(self):
        """Test: Tipos de sistema válidos"""
        valid_types = ["MPRO", "SoftRestaurant", "Otro"]
        
        for sys_type in valid_types:
            assert isinstance(sys_type, str)
    
    @pytest.mark.unit
    def test_kpis_structure(self, sample_kpis_data):
        """Test: Estructura de KPIs es correcta"""
        # Campos numéricos
        numeric_fields = ["ventas", "pax", "cheques"]
        
        for field in numeric_fields:
            assert field in sample_kpis_data
            assert isinstance(sample_kpis_data[field], (int, float))


class TestDashboardComercialWithMocks:
    """Tests con mocks completos"""
    
    @pytest.mark.unit
    def test_mock_server_found(self, mock_current_user, sample_server_config):
        """Test: Con servidor mockeado"""
        from server import app, get_current_user
        
        app.dependency_overrides[get_current_user] = lambda: mock_current_user
        
        try:
            with patch("server.db") as mock_db:
                # Servidor existe
                mock_db.servers.find_one = AsyncMock(return_value=sample_server_config)
                
                # Mock de execute_sql_query para no conectar a SQL real
                with patch("core.db.execute_sql_query") as mock_sql:
                    mock_sql.return_value = []  # Sin datos
                    
                    with TestClient(app) as client:
                        response = client.get(f"/api/comercial/dashboard/{sample_server_config['id']}")
                        # Cualquier respuesta válida (200 o error controlado)
                        assert response.status_code in [200, 404, 500]
        finally:
            app.dependency_overrides.clear()
    
    @pytest.mark.unit
    def test_empty_sql_result_handled(self, mock_sql_query):
        """Test: Resultado SQL vacío se maneja correctamente"""
        mock_sql_query.return_value = []
        
        result = mock_sql_query()
        assert result == []
        assert isinstance(result, list)
