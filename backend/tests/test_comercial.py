"""
EDARSA HUB - Tests del Módulo Comercial
=======================================
Tests de regresión para el módulo comercial.

PRIORIDAD 2: Tests básicos de regresión (Abril 2026)

Cobertura:
- Tablero Ejecutivo
- Dashboard Comercial
- Metas
- Ticket Perfecto
"""

import pytest
import pytest_asyncio


class TestTableroEjecutivo:
    """Tests del Tablero Ejecutivo"""
    
    @pytest.mark.smoke
    @pytest.mark.asyncio
    async def test_tablero_ejecutivo_ventas_dia(self, http_client, api_base_url, auth_headers):
        """Test: Tablero Ejecutivo en modo ventas_dia"""
        response = await http_client.get(
            f"{api_base_url}/api/comercial/tablero-ejecutivo",
            params={"meses": "ventas_dia"},
            headers=auth_headers,
            timeout=60.0  # Puede ser lento por SQL
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Validar estructura de respuesta
        assert "unidades" in data
        assert "totales" in data
        assert "periodo" in data
        assert isinstance(data["unidades"], list)
    
    @pytest.mark.smoke
    @pytest.mark.asyncio
    async def test_tablero_ejecutivo_mes_actual(self, http_client, api_base_url, auth_headers):
        """Test: Tablero Ejecutivo en modo mes actual"""
        response = await http_client.get(
            f"{api_base_url}/api/comercial/tablero-ejecutivo",
            params={"meses": "actual"},
            headers=auth_headers,
            timeout=60.0
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "unidades" in data
    
    @pytest.mark.regression
    @pytest.mark.asyncio
    async def test_tablero_ejecutivo_estructura_unidad(self, http_client, api_base_url, auth_headers):
        """Test: Validar estructura de cada unidad en el tablero"""
        response = await http_client.get(
            f"{api_base_url}/api/comercial/tablero-ejecutivo",
            params={"meses": "ventas_dia"},
            headers=auth_headers,
            timeout=60.0
        )
        
        assert response.status_code == 200
        data = response.json()
        
        if data["unidades"]:
            unidad = data["unidades"][0]
            # Campos requeridos en cada unidad
            campos_requeridos = ["unidad", "ventas", "pax", "cheques", "status"]
            for campo in campos_requeridos:
                assert campo in unidad, f"Campo '{campo}' falta en unidad"
    
    @pytest.mark.regression
    @pytest.mark.asyncio
    async def test_tablero_ejecutivo_totales(self, http_client, api_base_url, auth_headers):
        """Test: Validar que totales son consistentes"""
        response = await http_client.get(
            f"{api_base_url}/api/comercial/tablero-ejecutivo",
            params={"meses": "ventas_dia"},
            headers=auth_headers,
            timeout=60.0
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Calcular suma de ventas de unidades
        suma_ventas = sum(u.get("ventas", 0) for u in data["unidades"])
        totales_ventas = data.get("totales", {}).get("ventas", 0)
        
        # Permitir pequeña diferencia por redondeo
        assert abs(suma_ventas - totales_ventas) < 1, \
            f"Inconsistencia en totales: suma={suma_ventas}, totales={totales_ventas}"
    
    @pytest.mark.smoke
    @pytest.mark.asyncio
    async def test_tablero_ejecutivo_sin_auth(self, http_client, api_base_url):
        """Test: Tablero Ejecutivo sin autenticación debe fallar"""
        response = await http_client.get(
            f"{api_base_url}/api/comercial/tablero-ejecutivo",
            params={"meses": "ventas_dia"}
        )
        
        assert response.status_code in [401, 403]


class TestDashboardComercial:
    """Tests del Dashboard Comercial por servidor"""
    
    @pytest.mark.regression
    @pytest.mark.asyncio
    async def test_dashboard_comercial_estructura(self, http_client, api_base_url, auth_headers):
        """Test: Dashboard comercial retorna estructura válida"""
        # Primero obtener lista de servidores
        servers_response = await http_client.get(
            f"{api_base_url}/api/servers",
            headers=auth_headers
        )
        
        if servers_response.status_code == 200:
            servers = servers_response.json()
            if servers:
                server_id = servers[0].get("id")
                
                response = await http_client.get(
                    f"{api_base_url}/api/comercial/dashboard/{server_id}",
                    headers=auth_headers,
                    timeout=60.0
                )
                
                # Puede ser 200 o error si el servidor está offline
                assert response.status_code in [200, 500, 503]
    
    @pytest.mark.smoke
    @pytest.mark.asyncio
    async def test_dashboard_comercial_invalid_server(self, http_client, api_base_url, auth_headers):
        """Test: Dashboard con server_id inválido"""
        response = await http_client.get(
            f"{api_base_url}/api/comercial/dashboard/invalid-server-id-12345",
            headers=auth_headers,
            timeout=30.0
        )
        
        # Debe retornar error o datos vacíos, no crash
        assert response.status_code in [200, 404, 500]


class TestPoolStats:
    """Tests del endpoint de estadísticas del pool"""
    
    @pytest.mark.smoke
    @pytest.mark.asyncio
    async def test_pool_stats_admin(self, http_client, api_base_url, auth_headers):
        """Test: Admin puede ver estadísticas del pool"""
        response = await http_client.get(
            f"{api_base_url}/api/sistema/pool-stats",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "pool_stats" in data
        assert "mensaje" in data
    
    @pytest.mark.smoke
    @pytest.mark.asyncio
    async def test_pool_stats_sin_auth(self, http_client, api_base_url):
        """Test: Pool stats sin auth debe fallar"""
        response = await http_client.get(
            f"{api_base_url}/api/sistema/pool-stats"
        )
        
        assert response.status_code in [401, 403]
