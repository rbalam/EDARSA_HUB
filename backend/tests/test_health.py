"""
EDARSA HUB - Tests de Health/Smoke
==================================
Tests básicos de disponibilidad del sistema.

PASO 3: Tests mínimos usando mocks.
NO conecta a servicios reales.
"""

import pytest


class TestHealthSmoke:
    """Tests smoke básicos del sistema"""
    
    @pytest.mark.unit
    def test_app_imports_correctly(self):
        """Test: La app FastAPI se importa sin errores"""
        from server import app
        assert app is not None
        assert hasattr(app, 'routes')
    
    @pytest.mark.unit
    def test_api_router_exists(self):
        """Test: El router principal existe"""
        from server import api_router
        assert api_router is not None
    
    @pytest.mark.unit
    def test_core_db_imports(self):
        """Test: Módulo core.db se importa correctamente"""
        from core.db import execute_sql_query
        assert callable(execute_sql_query)
    
    @pytest.mark.unit
    def test_core_security_imports(self):
        """Test: Módulo core.security se importa correctamente"""
        from core.security import get_current_user
        assert callable(get_current_user)
    
    @pytest.mark.unit
    def test_core_pool_imports(self):
        """Test: Módulo core.pool se importa correctamente"""
        from core.pool import get_pool_manager, PoolConfig
        assert callable(get_pool_manager)
        assert PoolConfig is not None


class TestAppStructure:
    """Tests de estructura de la aplicación"""
    
    @pytest.mark.unit
    def test_fastapi_app_has_routes(self):
        """Test: La app tiene rutas registradas"""
        from server import app
        # FastAPI registra rutas en app.routes
        assert len(app.routes) > 0
    
    @pytest.mark.unit
    def test_modules_comercial_imports(self):
        """Test: Módulo comercial se importa correctamente"""
        from modules.comercial import get_router
        router = get_router()
        assert router is not None
    
    @pytest.mark.unit
    def test_modules_auth_imports(self):
        """Test: Módulo auth se importa correctamente"""
        from modules.auth import get_router
        router = get_router()
        assert router is not None
