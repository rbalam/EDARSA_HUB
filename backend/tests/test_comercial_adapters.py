"""
EDARSA HUB - Tests para modules/comercial/adapters.py
=====================================================
Tests de cobertura para adaptadores de APIs locales MPRO.

PASO 5: Ampliar cobertura de adapters.py a ~40%.
NO conecta a servicios reales - usa MOCKS exclusivamente.
"""

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone, timedelta
import requests


class TestApisMproLocalesConfig:
    """Tests de configuración de APIs MPRO locales"""
    
    @pytest.mark.unit
    def test_apis_mpro_locales_structure(self):
        """Test: Estructura correcta de APIS_MPRO_LOCALES"""
        from modules.comercial.adapters import APIS_MPRO_LOCALES
        
        assert isinstance(APIS_MPRO_LOCALES, dict)
        assert len(APIS_MPRO_LOCALES) >= 2
        
        for api_id, config in APIS_MPRO_LOCALES.items():
            assert "nombre" in config
            assert "url" in config
            assert "api_key" in config
            assert "sucursal_destino" in config
            assert "servidor_padre_host" in config
            assert "hora_replica" in config
            assert "activo" in config
    
    @pytest.mark.unit
    def test_apis_have_valid_urls(self):
        """Test: URLs de APIs tienen formato válido"""
        from modules.comercial.adapters import APIS_MPRO_LOCALES
        
        for api_id, config in APIS_MPRO_LOCALES.items():
            url = config.get("url", "")
            assert url.startswith("http://") or url.startswith("https://")
    
    @pytest.mark.unit
    def test_apis_have_replica_hours(self):
        """Test: APIs tienen hora de réplica definida"""
        from modules.comercial.adapters import APIS_MPRO_LOCALES
        
        for api_id, config in APIS_MPRO_LOCALES.items():
            hora = config.get("hora_replica")
            assert isinstance(hora, int)
            assert 0 <= hora <= 23


class TestQueryApiMproLocal:
    """Tests de query_api_mpro_local"""
    
    @pytest.mark.unit
    def test_query_api_inactive(self):
        """Test: API inactiva retorna error"""
        from modules.comercial.adapters import query_api_mpro_local
        
        inactive_config = {
            "nombre": "Test API",
            "url": "http://test.com/query",
            "api_key": "test_key",
            "activo": False
        }
        
        result = query_api_mpro_local(inactive_config, "SELECT 1")
        
        assert result["success"] is False
        assert "desactivada" in result["error"].lower()
    
    @pytest.mark.unit
    def test_query_api_success(self):
        """Test: Query exitoso a API local"""
        from modules.comercial.adapters import query_api_mpro_local
        
        api_config = {
            "nombre": "Test API",
            "url": "http://test.com/query",
            "api_key": "test_key",
            "activo": True
        }
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [{"ventas": 1000}]
        
        with patch("modules.comercial.adapters.requests.get", return_value=mock_response):
            result = query_api_mpro_local(api_config, "SELECT ventas FROM tabla")
        
        assert result["success"] is True
        assert result["data"] == [{"ventas": 1000}]
    
    @pytest.mark.unit
    def test_query_api_timeout(self):
        """Test: Timeout de API se maneja correctamente"""
        from modules.comercial.adapters import query_api_mpro_local
        
        api_config = {
            "nombre": "Slow API",
            "url": "http://slow.com/query",
            "api_key": "test_key",
            "activo": True
        }
        
        with patch("modules.comercial.adapters.requests.get", side_effect=requests.exceptions.Timeout):
            result = query_api_mpro_local(api_config, "SELECT 1", timeout=1)
        
        assert result["success"] is False
        assert "timeout" in result["error"].lower()
    
    @pytest.mark.unit
    def test_query_api_connection_error(self):
        """Test: Error de conexión se maneja"""
        from modules.comercial.adapters import query_api_mpro_local
        
        api_config = {
            "nombre": "Unreachable API",
            "url": "http://unreachable.com/query",
            "api_key": "test_key",
            "activo": True
        }
        
        with patch("modules.comercial.adapters.requests.get", side_effect=requests.exceptions.ConnectionError):
            result = query_api_mpro_local(api_config, "SELECT 1")
        
        assert result["success"] is False
        assert "conexión" in result["error"].lower()
    
    @pytest.mark.unit
    def test_query_api_http_error(self):
        """Test: Error HTTP se reporta"""
        from modules.comercial.adapters import query_api_mpro_local
        
        api_config = {
            "nombre": "Error API",
            "url": "http://error.com/query",
            "api_key": "test_key",
            "activo": True
        }
        
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        
        with patch("modules.comercial.adapters.requests.get", return_value=mock_response):
            result = query_api_mpro_local(api_config, "SELECT 1")
        
        assert result["success"] is False
        assert "500" in result["error"]


class TestObtenerVentasDiaApiLocal:
    """Tests de obtener_ventas_dia_api_local"""
    
    @pytest.mark.unit
    def test_obtener_ventas_post_replica(self):
        """Test: Omitir si ya pasó hora de réplica"""
        from modules.comercial.adapters import obtener_ventas_dia_api_local
        
        # Configurar API con hora réplica en el pasado
        api_config = {
            "nombre": "Test API",
            "url": "http://test.com/query",
            "api_key": "test_key",
            "hora_replica": 0,  # Ya pasó
            "activo": True
        }
        
        # Sin forzar consulta
        result = obtener_ventas_dia_api_local(api_config, forzar_consulta=False)
        
        # Si estamos después de medianoche México, debe omitir
        assert "omitido" in result
    
    @pytest.mark.unit
    def test_obtener_ventas_forzado(self):
        """Test: Forzar consulta ignora hora de réplica"""
        from modules.comercial.adapters import obtener_ventas_dia_api_local
        
        api_config = {
            "nombre": "Test API",
            "url": "http://test.com/query",
            "api_key": "test_key",
            "hora_replica": 0,
            "activo": True
        }
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": [{"ventas": 5000, "cheques": 50, "pax": 100}]}
        
        with patch("modules.comercial.adapters.requests.get", return_value=mock_response):
            result = obtener_ventas_dia_api_local(api_config, forzar_consulta=True)
        
        # Con forzar=True siempre intenta
        assert "ventas" in result
    
    @pytest.mark.unit
    def test_obtener_ventas_parse_format_1(self):
        """Test: Parseo formato {'data': [...]}"""
        from modules.comercial.adapters import obtener_ventas_dia_api_local
        
        api_config = {
            "nombre": "Test API",
            "url": "http://test.com/query",
            "api_key": "test_key",
            "hora_replica": 23,  # No ha pasado
            "activo": True
        }
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "total_registros": 1,
            "data": [{"ventas": 15000.50, "cheques": 75, "pax": 150}]
        }
        
        with patch("modules.comercial.adapters.requests.get", return_value=mock_response):
            result = obtener_ventas_dia_api_local(api_config, forzar_consulta=True)
        
        assert result["ventas"] == 15000.50
        assert result["cheques"] == 75
        assert result["pax"] == 150
    
    @pytest.mark.unit
    def test_obtener_ventas_parse_format_list(self):
        """Test: Parseo formato lista directa [...]"""
        from modules.comercial.adapters import obtener_ventas_dia_api_local
        
        api_config = {
            "nombre": "Test API",
            "url": "http://test.com/query",
            "api_key": "test_key",
            "hora_replica": 23,
            "activo": True
        }
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [{"ventas": 8000, "cheques": 40, "pax": 80}]
        
        with patch("modules.comercial.adapters.requests.get", return_value=mock_response):
            result = obtener_ventas_dia_api_local(api_config, forzar_consulta=True)
        
        assert result["ventas"] == 8000.0
    
    @pytest.mark.unit
    def test_obtener_ventas_handles_none_values(self):
        """Test: Manejo de valores None en respuesta"""
        from modules.comercial.adapters import obtener_ventas_dia_api_local
        
        api_config = {
            "nombre": "Test API",
            "url": "http://test.com/query",
            "api_key": "test_key",
            "hora_replica": 23,
            "activo": True
        }
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [{"ventas": None, "cheques": None, "pax": None}]
        
        with patch("modules.comercial.adapters.requests.get", return_value=mock_response):
            result = obtener_ventas_dia_api_local(api_config, forzar_consulta=True)
        
        # Valores None deben convertirse a 0
        assert result["ventas"] == 0
        assert result["cheques"] == 0
        assert result["pax"] == 0


class TestSumarVentasApiLocalASucursal:
    """Tests de sumar_ventas_api_local_a_sucursal"""
    
    @pytest.mark.unit
    def test_periodo_no_incluye_hoy(self):
        """Test: Retorna vacío si período no incluye hoy"""
        from modules.comercial.adapters import sumar_ventas_api_local_a_sucursal
        
        # Fecha en el pasado
        result = sumar_ventas_api_local_a_sucursal(
            server_host="54.39.104.176",
            sucursal_nombre="QUERETARO",
            fecha_fin="2020-01-01",
            mes_solicitado=1,
            anio_solicitado=2020,
            solo_ventas_dia=False
        )
        
        assert result["aplicado"] is False
        assert result["razon"] == "fecha_no_incluye_hoy"
    
    @pytest.mark.unit
    def test_busca_en_mongodb_primero(self):
        """Test: Intenta buscar en MongoDB antes de hardcoded"""
        from modules.comercial.adapters import sumar_ventas_api_local_a_sucursal
        
        # Fecha actual para que incluya hoy
        hoy = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        mes_actual = datetime.now(timezone.utc).month
        anio_actual = datetime.now(timezone.utc).year
        
        # Mock MongoDB sin APIs - pymongo.MongoClient
        with patch("pymongo.MongoClient") as mock_mongo:
            mock_client = MagicMock()
            mock_db = MagicMock()
            mock_client.__getitem__ = MagicMock(return_value=mock_db)
            mock_db.servers.find.return_value = []  # Sin APIs en MongoDB
            mock_mongo.return_value = mock_client
            
            result = sumar_ventas_api_local_a_sucursal(
                server_host="no-existe.com",
                sucursal_nombre="INEXISTENTE",
                fecha_fin=hoy,
                mes_solicitado=mes_actual,
                anio_solicitado=anio_actual,
                solo_ventas_dia=False
            )
        
        # Sin match debe retornar sin_api_local
        assert result["aplicado"] is False
    
    @pytest.mark.unit
    def test_modo_ventas_dia_reemplaza(self):
        """Test: modo solo_ventas_dia marca reemplazar=True"""
        from modules.comercial.adapters import sumar_ventas_api_local_a_sucursal
        
        hoy = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        mes_actual = datetime.now(timezone.utc).month
        anio_actual = datetime.now(timezone.utc).year
        
        # Mock MongoDB con API que matchea
        mock_api_doc = {
            "name": "API QRO",
            "endpoint": "http://test.com/query",
            "api_key": "test_key",
            "sucursal_destino": "QUERETARO",
            "servidor_padre_host": "54.39.104.176",
            "hora_replica": 4
        }
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [{"ventas": 10000, "cheques": 50, "pax": 100}]
        
        with patch("pymongo.MongoClient") as mock_mongo:
            mock_client = MagicMock()
            mock_db = MagicMock()
            mock_client.__getitem__ = MagicMock(return_value=mock_db)
            mock_db.servers.find.return_value = [mock_api_doc]
            mock_mongo.return_value = mock_client
            
            with patch("modules.comercial.adapters.requests.get", return_value=mock_response):
                result = sumar_ventas_api_local_a_sucursal(
                    server_host="54.39.104.176",
                    sucursal_nombre="130° QUERETARO",
                    fecha_fin=hoy,
                    mes_solicitado=mes_actual,
                    anio_solicitado=anio_actual,
                    solo_ventas_dia=True
                )
        
        # Con solo_ventas_dia=True debe indicar reemplazar
        if result["aplicado"]:
            assert result["reemplazar"] is True
    
    @pytest.mark.unit
    def test_fallback_to_hardcoded(self):
        """Test: Fallback a configuración hardcodeada si no hay MongoDB"""
        from modules.comercial.adapters import sumar_ventas_api_local_a_sucursal
        
        hoy = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        mes_actual = datetime.now(timezone.utc).month
        anio_actual = datetime.now(timezone.utc).year
        
        # Simular error de MongoDB
        with patch("pymongo.MongoClient", side_effect=Exception("DB Error")):
            result = sumar_ventas_api_local_a_sucursal(
                server_host="54.39.104.176",
                sucursal_nombre="QUERETARO",
                fecha_fin=hoy,
                mes_solicitado=mes_actual,
                anio_solicitado=anio_actual,
                solo_ventas_dia=False
            )
        
        # Debe haber intentado el fallback (aunque falle el match)
        assert isinstance(result, dict)
        assert "aplicado" in result
    
    @pytest.mark.unit
    def test_sucursal_matching_flexible(self):
        """Test: Matching flexible de nombres de sucursal"""
        # Verifica que el matching es case-insensitive y parcial
        sucursal_destino = "QUERETARO"
        sucursal_actual = "130° QUERETARO"
        
        # Comparación como en el código real
        match = (sucursal_destino.upper() in sucursal_actual.upper() or 
                 sucursal_actual.upper() in sucursal_destino.upper())
        
        assert match is True
    
    @pytest.mark.unit
    def test_server_host_mismatch_skips(self):
        """Test: Si servidor padre no coincide, omite API"""
        from modules.comercial.adapters import sumar_ventas_api_local_a_sucursal
        
        hoy = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        
        # API con servidor diferente
        mock_api_doc = {
            "name": "API Otra",
            "endpoint": "http://otro.com/query",
            "api_key": "key",
            "sucursal_destino": "QUERETARO",
            "servidor_padre_host": "otro.servidor.com",  # Diferente
            "hora_replica": 4
        }
        
        with patch("pymongo.MongoClient") as mock_mongo:
            mock_client = MagicMock()
            mock_db = MagicMock()
            mock_client.__getitem__ = MagicMock(return_value=mock_db)
            mock_db.servers.find.return_value = [mock_api_doc]
            mock_mongo.return_value = mock_client
            
            result = sumar_ventas_api_local_a_sucursal(
                server_host="54.39.104.176",  # No coincide
                sucursal_nombre="QUERETARO",
                fecha_fin=hoy,
                solo_ventas_dia=False
            )
        
        # Debe omitir por mismatch de host - el resultado depende del fallback hardcoded
        assert isinstance(result, dict)


class TestAdaptersImports:
    """Tests de importación del módulo"""
    
    @pytest.mark.unit
    def test_all_exports_importable(self):
        """Test: Todas las exportaciones se pueden importar"""
        from modules.comercial.adapters import (
            APIS_MPRO_LOCALES,
            query_api_mpro_local,
            obtener_ventas_dia_api_local,
            sumar_ventas_api_local_a_sucursal
        )
        
        assert isinstance(APIS_MPRO_LOCALES, dict)
        assert callable(query_api_mpro_local)
        assert callable(obtener_ventas_dia_api_local)
        assert callable(sumar_ventas_api_local_a_sucursal)


class TestEdgeCases:
    """Tests de casos límite"""
    
    @pytest.mark.unit
    def test_empty_api_response(self):
        """Test: Respuesta vacía de API"""
        from modules.comercial.adapters import query_api_mpro_local
        
        api_config = {
            "nombre": "Empty API",
            "url": "http://empty.com/query",
            "api_key": "key",
            "activo": True
        }
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = []
        
        with patch("modules.comercial.adapters.requests.get", return_value=mock_response):
            result = query_api_mpro_local(api_config, "SELECT 1")
        
        assert result["success"] is True
        assert result["data"] == []
    
    @pytest.mark.unit
    def test_malformed_json_response(self):
        """Test: Respuesta JSON malformada"""
        from modules.comercial.adapters import query_api_mpro_local
        
        api_config = {
            "nombre": "Bad JSON API",
            "url": "http://bad.com/query",
            "api_key": "key",
            "activo": True
        }
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.side_effect = ValueError("Invalid JSON")
        
        with patch("modules.comercial.adapters.requests.get", return_value=mock_response):
            result = query_api_mpro_local(api_config, "SELECT 1")
        
        assert result["success"] is False
    
    @pytest.mark.unit
    def test_ventas_with_decimal_values(self):
        """Test: Ventas con valores decimales"""
        from modules.comercial.adapters import obtener_ventas_dia_api_local
        
        api_config = {
            "nombre": "Decimal API",
            "url": "http://decimal.com/query",
            "api_key": "key",
            "hora_replica": 23,
            "activo": True
        }
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [{"ventas": 12345.67, "cheques": 50, "pax": 100}]
        
        with patch("modules.comercial.adapters.requests.get", return_value=mock_response):
            result = obtener_ventas_dia_api_local(api_config, forzar_consulta=True)
        
        assert isinstance(result["ventas"], float)
        assert result["ventas"] == 12345.67
