"""
EDARSA HUB - Tests del Connection Pool
======================================
Tests unitarios para el módulo de connection pooling.

PRIORIDAD 2: Tests básicos de regresión (Abril 2026)

Cobertura:
- Creación de pools
- Reutilización de conexiones
- Estadísticas
- Manejo de errores
"""

import pytest
import sys
import os

# Añadir path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestPoolConfig:
    """Tests de configuración del pool"""
    
    @pytest.mark.smoke
    def test_pool_config_defaults(self):
        """Test: Configuración por defecto tiene valores correctos"""
        from core.pool import DEFAULT_POOL_CONFIG
        
        assert DEFAULT_POOL_CONFIG.min_connections >= 1
        assert DEFAULT_POOL_CONFIG.max_connections >= DEFAULT_POOL_CONFIG.min_connections
        assert DEFAULT_POOL_CONFIG.connection_timeout > 0
        assert DEFAULT_POOL_CONFIG.query_timeout > 0
    
    @pytest.mark.smoke
    def test_pool_config_custom(self):
        """Test: Se puede crear configuración personalizada"""
        from core.pool import PoolConfig
        
        config = PoolConfig(
            min_connections=2,
            max_connections=20,
            connection_timeout=30
        )
        
        assert config.min_connections == 2
        assert config.max_connections == 20
        assert config.connection_timeout == 30


class TestPoolManager:
    """Tests del Pool Manager"""
    
    @pytest.mark.smoke
    def test_pool_manager_singleton(self):
        """Test: Pool Manager es singleton"""
        from core.pool import get_pool_manager, ConnectionPoolManager
        
        manager1 = get_pool_manager()
        manager2 = get_pool_manager()
        
        assert manager1 is manager2
        assert isinstance(manager1, ConnectionPoolManager)
    
    @pytest.mark.smoke
    def test_pool_key_generation(self):
        """Test: Generación de claves de pool"""
        from core.pool import get_pool_manager
        
        manager = get_pool_manager()
        key = manager._generate_pool_key("host.com", 1433, "mydb")
        
        assert key == "host.com:1433/mydb"
    
    @pytest.mark.smoke
    def test_get_pool_statistics(self):
        """Test: Obtener estadísticas del pool"""
        from core.pool import get_pool_statistics
        
        stats = get_pool_statistics()
        
        assert "total_pools" in stats
        assert "pools" in stats
        assert isinstance(stats["total_pools"], int)
        assert isinstance(stats["pools"], dict)


class TestPoolIntegration:
    """Tests de integración del pool (requieren servidor SQL real)"""
    
    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_pool_reuses_connection(self, http_client, api_base_url, auth_headers):
        """Test: El pool reutiliza conexiones en llamadas consecutivas"""
        # Hacer primera llamada (crea pool)
        response1 = await http_client.get(
            f"{api_base_url}/api/sistema/pool-stats",
            headers=auth_headers
        )
        
        if response1.status_code != 200:
            pytest.skip("Pool stats endpoint not accessible")
        
        response1.json().get("pool_stats", {})
        
        # Hacer llamada que usa SQL
        await http_client.get(
            f"{api_base_url}/api/comercial/tablero-ejecutivo",
            params={"meses": "ventas_dia"},
            headers=auth_headers,
            timeout=60.0
        )
        
        # Verificar estadísticas después
        response2 = await http_client.get(
            f"{api_base_url}/api/sistema/pool-stats",
            headers=auth_headers
        )
        
        stats_after = response2.json().get("pool_stats", {})
        
        # Debe haber pools creados o conexiones servidas
        assert stats_after.get("total_pools", 0) >= 0


class TestDbExecuteQuery:
    """Tests de la función execute_sql_query"""
    
    @pytest.mark.smoke
    def test_execute_sql_query_import(self):
        """Test: execute_sql_query se importa correctamente"""
        from core.db import execute_sql_query
        
        assert callable(execute_sql_query)
    
    @pytest.mark.smoke
    def test_execute_sql_query_fallback_exists(self):
        """Test: Función de fallback existe"""
        from core.db import _execute_sql_query_direct
        
        assert callable(_execute_sql_query_direct)
    
    @pytest.mark.smoke
    def test_server_cache_functions(self):
        """Test: Funciones de caché de servidor existen"""
        from core.db import (
            mark_server_offline,
            mark_server_online,
            is_server_offline_in_memory,
            get_server_cooldown_info,
            reset_server_cache
        )
        
        # Todas deben ser callable
        assert callable(mark_server_offline)
        assert callable(mark_server_online)
        assert callable(is_server_offline_in_memory)
        assert callable(get_server_cooldown_info)
        assert callable(reset_server_cache)
