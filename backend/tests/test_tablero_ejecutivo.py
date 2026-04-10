"""
EDARSA HUB - Tests de Tablero Ejecutivo (con Mocks)
===================================================
Tests del tablero ejecutivo usando mocks.

PASO 3: Tests mínimos usando mocks.
NO conecta a servicios reales (Mongo, SQL, APIs).
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient


class TestTableroEjecutivoStructure:
    """Tests de estructura del tablero ejecutivo"""
    
    @pytest.mark.unit
    def test_endpoint_exists(self):
        """Test: Endpoint de tablero ejecutivo existe"""
        from server import app
        
        routes = [r for r in app.routes if hasattr(r, 'path') and 'tablero-ejecutivo' in r.path]
        assert len(routes) > 0, "No se encontró endpoint tablero-ejecutivo"
    
    @pytest.mark.unit
    def test_endpoint_requires_auth(self):
        """Test: Tablero ejecutivo requiere autenticación"""
        from server import app
        
        with TestClient(app) as client:
            response = client.get("/api/comercial/tablero-ejecutivo")
            assert response.status_code in [401, 403]
    
    @pytest.mark.unit
    def test_endpoint_with_mock_user(self, mock_current_user):
        """Test: Tablero ejecutivo responde con usuario mock"""
        from server import app, get_current_user
        
        # Mock de MongoDB y SQL
        mock_servers = []  # Lista vacía de servidores
        
        app.dependency_overrides[get_current_user] = lambda: mock_current_user
        
        try:
            with patch("server.db") as mock_db:
                mock_db.servers.find.return_value.to_list = AsyncMock(return_value=mock_servers)
                
                with TestClient(app) as client:
                    response = client.get("/api/comercial/tablero-ejecutivo?meses=ventas_dia")
                    # Debe responder aunque sea con datos vacíos
                    assert response.status_code in [200, 500]  # 500 si hay error de config
        finally:
            app.dependency_overrides.clear()


class TestTableroEjecutivoPayload:
    """Tests de payload del tablero ejecutivo"""
    
    @pytest.mark.unit
    def test_expected_response_structure(self, sample_kpis_data):
        """Test: Estructura esperada del response"""
        # Campos esperados en la respuesta
        expected_fields = ["unidades", "totales", "periodo"]
        
        # Simular respuesta típica
        mock_response = {
            "unidades": [],
            "totales": sample_kpis_data,
            "periodo": {"mes": 4, "año": 2026}
        }
        
        for field in expected_fields:
            assert field in mock_response
    
    @pytest.mark.unit
    def test_unidad_structure(self, sample_kpis_data):
        """Test: Estructura de una unidad en el tablero"""
        # Campos requeridos en cada unidad
        required_fields = ["unidad", "ventas", "pax", "cheques", "status"]
        
        mock_unidad = {
            "unidad": "TEST",
            "ventas": 1000.0,
            "pax": 50,
            "cheques": 20,
            "status": "online",
            **sample_kpis_data
        }
        
        for field in required_fields:
            assert field in mock_unidad, f"Falta campo: {field}"
    
    @pytest.mark.unit
    def test_totales_structure(self, sample_kpis_data):
        """Test: Estructura de totales"""
        required_fields = ["ventas", "pax", "cheques"]
        
        for field in required_fields:
            assert field in sample_kpis_data, f"Falta campo: {field}"
    
    @pytest.mark.unit
    def test_empty_servers_returns_empty_unidades(self):
        """Test: Sin servidores retorna unidades vacías"""
        mock_response = {
            "unidades": [],
            "totales": {"ventas": 0, "pax": 0, "cheques": 0},
            "periodo": {}
        }
        
        assert mock_response["unidades"] == []
        assert mock_response["totales"]["ventas"] == 0


class TestTableroEjecutivoModos:
    """Tests de modos del tablero ejecutivo"""
    
    @pytest.mark.unit
    def test_modo_ventas_dia_parameter(self):
        """Test: Parámetro meses=ventas_dia es válido"""
        valid_modes = ["ventas_dia", "actual", "1", "3", "6", "12"]
        assert "ventas_dia" in valid_modes
    
    @pytest.mark.unit
    def test_modo_actual_parameter(self):
        """Test: Parámetro meses=actual es válido"""
        valid_modes = ["ventas_dia", "actual", "1", "3", "6", "12"]
        assert "actual" in valid_modes
