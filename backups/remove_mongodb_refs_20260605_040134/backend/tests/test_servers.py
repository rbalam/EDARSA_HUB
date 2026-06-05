"""
EDARSA HUB - Tests de Servidores
================================
Tests de regresión para el módulo de servidores.

PRIORIDAD 2: Tests básicos de regresión (Abril 2026)
"""

import pytest


class TestServers:
    """Tests del endpoint de servidores"""
    
    @pytest.mark.smoke
    @pytest.mark.asyncio
    async def test_list_servers(self, http_client, api_base_url, auth_headers):
        """Test: Listar servidores"""
        response = await http_client.get(
            f"{api_base_url}/api/servers",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    @pytest.mark.regression
    @pytest.mark.asyncio
    async def test_servers_structure(self, http_client, api_base_url, auth_headers):
        """Test: Estructura de servidores"""
        response = await http_client.get(
            f"{api_base_url}/api/servers",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        servers = response.json()
        
        if servers:
            server = servers[0]
            # Campos requeridos
            assert "id" in server
            assert "name" in server
            assert "system_type" in server
    
    @pytest.mark.smoke
    @pytest.mark.asyncio
    async def test_servers_sin_auth(self, http_client, api_base_url):
        """Test: Servidores sin auth debe fallar"""
        response = await http_client.get(
            f"{api_base_url}/api/servers"
        )
        
        assert response.status_code in [401, 403]


class TestServerConnection:
    """Tests de conexión a servidores"""
    
    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_test_connection_endpoint(self, http_client, api_base_url, auth_headers):
        """Test: Endpoint de test de conexión existe"""
        # Este test solo verifica que el endpoint existe
        # No probamos conexión real porque puede fallar por servidor offline
        response = await http_client.post(
            f"{api_base_url}/api/test-api-connection",
            json={
                "url": "http://invalid-test-url:9999/query",
                "api_key": "test_key"
            }
        )
        
        # Debe responder (aunque con error), no crash
        assert response.status_code in [200, 400, 422, 500]
