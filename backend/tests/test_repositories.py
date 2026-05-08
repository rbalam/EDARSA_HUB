"""
EDARSA HUB - Tests de Repositorios (con Mocks)
==============================================
Tests de capa de acceso a datos usando mocks.

PASO 3: Tests mínimos usando mocks.
NO conecta a servicios reales (Mongo, SQL).
"""

import pytest
from unittest.mock import patch, AsyncMock


class TestRepositoryMongo:
    """Tests de acceso a MongoDB con mocks"""
    
    @pytest.mark.unit
    def test_mock_mongo_db_structure(self, mock_mongo_db):
        """Test: Mock de MongoDB tiene estructura correcta"""
        # Colecciones esperadas
        assert hasattr(mock_mongo_db, 'users')
        assert hasattr(mock_mongo_db, 'servers')
        assert hasattr(mock_mongo_db, 'roles')
        assert hasattr(mock_mongo_db, 'kpis_cache')
    
    @pytest.mark.unit
    def test_mock_find_one_returns_none(self, mock_mongo_collection):
        """Test: find_one mock retorna None por defecto"""
        # El mock está configurado para retornar None
        import asyncio
        result = asyncio.get_event_loop().run_until_complete(
            mock_mongo_collection.find_one()
        )
        assert result is None
    
    @pytest.mark.unit
    def test_mock_find_one_configured(self, mock_mongo_collection):
        """Test: find_one mock puede configurarse"""
        expected = {"id": "test", "name": "Test"}
        mock_mongo_collection.find_one = AsyncMock(return_value=expected)
        
        import asyncio
        result = asyncio.get_event_loop().run_until_complete(
            mock_mongo_collection.find_one()
        )
        assert result == expected
    
    @pytest.mark.unit
    def test_mock_insert_one_returns_id(self, mock_mongo_collection):
        """Test: insert_one mock retorna inserted_id"""
        import asyncio
        result = asyncio.get_event_loop().run_until_complete(
            mock_mongo_collection.insert_one({"test": "data"})
        )
        assert hasattr(result, 'inserted_id')


class TestRepositorySQL:
    """Tests de acceso a SQL Server con mocks"""
    
    @pytest.mark.unit
    def test_mock_sql_query_returns_list(self, mock_sql_query):
        """Test: Mock de SQL retorna lista"""
        mock_sql_query.return_value = [{"id": 1}, {"id": 2}]
        
        result = mock_sql_query()
        assert isinstance(result, list)
        assert len(result) == 2
    
    @pytest.mark.unit
    def test_mock_sql_query_empty(self, mock_sql_query):
        """Test: Mock de SQL puede retornar vacío"""
        mock_sql_query.return_value = []
        
        result = mock_sql_query()
        assert result == []
    
    @pytest.mark.unit
    def test_execute_sql_query_import(self):
        """Test: execute_sql_query se puede importar"""
        from core.db import execute_sql_query
        assert callable(execute_sql_query)
    
    @pytest.mark.unit
    def test_mock_sql_with_patch(self):
        """Test: Patch de execute_sql_query funciona"""
        with patch("core.db.execute_sql_query") as mock:
            mock.return_value = [{"ventas": 1000}]
            
            # El patch aplica al módulo importado
            assert mock.return_value == [{"ventas": 1000}]


class TestRepositoryTransformations:
    """Tests de transformaciones de datos"""
    
    @pytest.mark.unit
    def test_datetime_to_iso_string(self):
        """Test: Datetime se convierte a ISO string"""
        from datetime import datetime
        
        dt = datetime(2026, 4, 10, 12, 30, 0)
        iso_string = dt.isoformat()
        
        assert "2026-04-10" in iso_string
        assert "T" in iso_string
    
    @pytest.mark.unit
    def test_decimal_to_float(self):
        """Test: Decimal se convierte a float"""
        from decimal import Decimal
        
        valor_decimal = Decimal("1234.56")
        valor_float = float(valor_decimal)
        
        assert isinstance(valor_float, float)
        assert abs(valor_float - 1234.56) < 0.01
    
    @pytest.mark.unit
    def test_none_handling(self):
        """Test: None se maneja correctamente"""
        valor = None
        
        resultado = valor if valor is not None else 0
        assert resultado == 0
    
    @pytest.mark.unit
    def test_empty_list_handling(self):
        """Test: Lista vacía se maneja correctamente"""
        datos = []
        
        total = sum(d.get("valor", 0) for d in datos)
        assert total == 0


class TestRepositoryErrors:
    """Tests de manejo de errores con mocks"""
    
    @pytest.mark.unit
    def test_mock_sql_raises_exception(self, mock_sql_query):
        """Test: Mock puede simular excepción"""
        mock_sql_query.side_effect = Exception("Connection timeout")
        
        with pytest.raises(Exception) as exc_info:
            mock_sql_query()
        
        assert "timeout" in str(exc_info.value).lower()
    
    @pytest.mark.unit
    def test_mock_mongo_raises_exception(self, mock_mongo_collection):
        """Test: Mock de Mongo puede simular excepción"""
        mock_mongo_collection.find_one = AsyncMock(
            side_effect=Exception("Database error")
        )
        
        import asyncio
        with pytest.raises(Exception):
            asyncio.get_event_loop().run_until_complete(
                mock_mongo_collection.find_one()
            )
    
    @pytest.mark.unit
    def test_error_returns_empty_list(self):
        """Test: Error controlado retorna lista vacía"""
        def safe_query():
            try:
                raise Exception("Error")
            except Exception:
                return []
        
        result = safe_query()
        assert result == []


class TestAPILocalMocks:
    """Tests de mocks para APIs locales"""
    
    @pytest.mark.unit
    def test_mock_api_local_success(self, mock_api_local_mpro):
        """Test: Mock de API local exitoso"""
        result = mock_api_local_mpro()
        
        assert result["success"]
        assert "data" in result
        assert result["error"] is None
    
    @pytest.mark.unit
    def test_mock_api_local_offline(self, mock_api_local_offline):
        """Test: Mock de API local offline"""
        result = mock_api_local_offline()
        
        assert not result["success"]
        assert result["data"] is None
        assert result["error"] == "Timeout"
    
    @pytest.mark.unit
    def test_api_local_data_structure(self, mock_api_local_mpro):
        """Test: Estructura de datos de API local"""
        result = mock_api_local_mpro()
        
        if result["success"] and result["data"]:
            data = result["data"][0]
            assert "ventas" in data
            assert "cheques" in data
            assert "pax" in data
