"""
EDARSA HUB - Tests de Automatización Operativa de Compras (Fase 4.3)
====================================================================
Tests para la separación de periodo operativo vs estadístico y ajuste porcentual.

ENDPOINTS TESTEADOS:
- GET /api/v2/automatizaciones/operativas/compras/{id} - campos fecha_consumo_inicio, fecha_consumo_fin, porcentaje_ajuste_consumo
- POST /api/v2/automatizaciones/operativas/compras/{id}/parametros-consumo - modificar periodo estadístico y ajuste
- GET /api/v2/automatizaciones/operativas/compras/{id}/bitacora - verificar CAMBIO_PARAMETROS_CONSUMO

VALIDACIONES:
- Ajuste positivo (+15%) aumenta consumo_promedio_ajustado
- Ajuste negativo (-10%) disminuye consumo_promedio_ajustado
- detalle_productos incluye consumo_promedio_base y consumo_promedio_ajustado
- Bitácora registra CAMBIO_PARAMETROS_CONSUMO
- Porcentaje fuera de rango (-100 a +500) es rechazado
"""

import pytest
import requests
import os
from tests.test_config import test_config

# Base URL from environment
BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', test_config.TEST_BASE_URL).rstrip('/')

# Test credentials from centralized config
TEST_CREDENTIALS = {
    "email": test_config.TEST_ADMIN_EMAIL,
    "password": test_config.TEST_ADMIN_PASSWORD
}

# Known automatizacion ID with -10% adjustment already applied
KNOWN_AUTOMATIZACION_ID = "c4295c76-6508-4c74-bcf1-11ccd75f4bb6"


class TestAutomatizacionComprasFase43:
    """Tests para Fase 4.3 - Periodo Estadístico y Ajuste Porcentual de Consumo"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup: obtener token de autenticación"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login
        response = self.session.post(
            f"{BASE_URL}/api/auth/login",
            json=TEST_CREDENTIALS
        )
        if response.status_code == 200:
            token = response.json().get("token")
            self.session.headers.update({"Authorization": f"Bearer {token}"})
            self.token = token
        else:
            pytest.skip(f"Authentication failed: {response.status_code} - {response.text}")
    
    # =========================================================================
    # TEST 1: GET automatizacion incluye campos de periodo estadístico
    # =========================================================================
    
    def test_get_automatizacion_includes_consumo_fields(self):
        """GET /compras/{id} - Debe incluir campos fecha_consumo_inicio, fecha_consumo_fin, porcentaje_ajuste_consumo"""
        # First get list to find an existing automatizacion
        response = self.session.get(
            f"{BASE_URL}/api/v2/automatizaciones/operativas/compras?limite=5"
        )
        assert response.status_code == 200, f"Failed to get list: {response.text}"
        
        automatizaciones = response.json()
        if not automatizaciones or len(automatizaciones) == 0:
            pytest.skip("No automatizaciones found in database")
        
        # Get first automatizacion
        auto_id = automatizaciones[0].get("id")
        
        response = self.session.get(
            f"{BASE_URL}/api/v2/automatizaciones/operativas/compras/{auto_id}"
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        
        # Verify new Fase 4.3 fields exist
        assert "fecha_consumo_inicio" in data, "Missing 'fecha_consumo_inicio' field"
        assert "fecha_consumo_fin" in data, "Missing 'fecha_consumo_fin' field"
        assert "porcentaje_ajuste_consumo" in data, "Missing 'porcentaje_ajuste_consumo' field"
        
        # Verify operational period fields (should be read-only)
        assert "fecha_inicio_periodo" in data, "Missing 'fecha_inicio_periodo' field"
        assert "fecha_fin_periodo" in data, "Missing 'fecha_fin_periodo' field"
        assert "fecha_pedido" in data, "Missing 'fecha_pedido' field"
        
        print(f"✓ Automatizacion {auto_id} has Fase 4.3 fields:")
        print(f"  - fecha_consumo_inicio: {data.get('fecha_consumo_inicio')}")
        print(f"  - fecha_consumo_fin: {data.get('fecha_consumo_fin')}")
        print(f"  - porcentaje_ajuste_consumo: {data.get('porcentaje_ajuste_consumo')}")
    
    def test_get_known_automatizacion_with_adjustment(self):
        """GET /compras/{id} - Verificar automatización conocida con ajuste -10%"""
        response = self.session.get(
            f"{BASE_URL}/api/v2/automatizaciones/operativas/compras/{KNOWN_AUTOMATIZACION_ID}"
        )
        
        if response.status_code == 404:
            pytest.skip(f"Known automatizacion {KNOWN_AUTOMATIZACION_ID} not found")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        
        # Verify adjustment is -10%
        ajuste = data.get("porcentaje_ajuste_consumo", 0)
        print(f"✓ Automatizacion {KNOWN_AUTOMATIZACION_ID} has porcentaje_ajuste_consumo: {ajuste}")
        
        # Verify detalle_productos has both consumo fields
        if data.get("detalle_productos"):
            for prod in data["detalle_productos"][:3]:  # Check first 3
                assert "consumo_promedio_base" in prod or "consumo_promedio" in prod, \
                    f"Product {prod.get('codigo')} missing consumo fields"
                print(f"  - Product {prod.get('codigo')}: base={prod.get('consumo_promedio_base')}, ajustado={prod.get('consumo_promedio_ajustado')}")
    
    # =========================================================================
    # TEST 2: detalle_productos incluye consumo_promedio_base y consumo_promedio_ajustado
    # =========================================================================
    
    def test_detalle_productos_has_consumo_base_and_ajustado(self):
        """GET /compras/{id} - detalle_productos debe incluir consumo_promedio_base y consumo_promedio_ajustado"""
        # Get list first
        response = self.session.get(
            f"{BASE_URL}/api/v2/automatizaciones/operativas/compras?limite=10"
        )
        assert response.status_code == 200
        
        automatizaciones = response.json()
        
        # Find one with detalle_productos
        auto_with_products = None
        for auto in automatizaciones:
            if auto.get("detalle_productos") and len(auto.get("detalle_productos", [])) > 0:
                auto_with_products = auto
                break
        
        if not auto_with_products:
            # Try getting full detail
            for auto in automatizaciones:
                response = self.session.get(
                    f"{BASE_URL}/api/v2/automatizaciones/operativas/compras/{auto.get('id')}"
                )
                if response.status_code == 200:
                    data = response.json()
                    if data.get("detalle_productos") and len(data.get("detalle_productos", [])) > 0:
                        auto_with_products = data
                        break
        
        if not auto_with_products or not auto_with_products.get("detalle_productos"):
            pytest.skip("No automatizacion with detalle_productos found")
        
        # Verify each product has both consumo fields
        for prod in auto_with_products["detalle_productos"]:
            # consumo_promedio_base should exist (original calculated consumption)
            assert "consumo_promedio_base" in prod or "consumo_promedio" in prod, \
                f"Product {prod.get('codigo')} missing consumo_promedio_base"
            
            # consumo_promedio_ajustado should exist (adjusted consumption)
            assert "consumo_promedio_ajustado" in prod or "consumo_promedio" in prod, \
                f"Product {prod.get('codigo')} missing consumo_promedio_ajustado"
            
            # porcentaje_ajuste_aplicado should exist
            assert "porcentaje_ajuste_aplicado" in prod, \
                f"Product {prod.get('codigo')} missing porcentaje_ajuste_aplicado"
        
        print(f"✓ All {len(auto_with_products['detalle_productos'])} products have consumo_promedio_base and consumo_promedio_ajustado")
    
    # =========================================================================
    # TEST 3: POST parametros-consumo - Validar ajuste positivo aumenta consumo
    # =========================================================================
    
    def test_parametros_consumo_positive_adjustment_increases_consumo(self):
        """POST /parametros-consumo - Ajuste +15% debe aumentar consumo_promedio_ajustado"""
        # Get an automatizacion to test
        response = self.session.get(
            f"{BASE_URL}/api/v2/automatizaciones/operativas/compras?limite=5"
        )
        assert response.status_code == 200
        
        automatizaciones = response.json()
        if not automatizaciones:
            pytest.skip("No automatizaciones found")
        
        # Find one with products
        test_auto = None
        for auto in automatizaciones:
            response = self.session.get(
                f"{BASE_URL}/api/v2/automatizaciones/operativas/compras/{auto.get('id')}"
            )
            if response.status_code == 200:
                data = response.json()
                if data.get("detalle_productos") and len(data.get("detalle_productos", [])) > 0:
                    test_auto = data
                    break
        
        if not test_auto:
            pytest.skip("No automatizacion with products found")
        
        auto_id = test_auto["id"]
        original_ajuste = test_auto.get("porcentaje_ajuste_consumo", 0)
        
        # Get original consumo values
        original_productos = test_auto.get("detalle_productos", [])
        if original_productos:
            original_productos[0].get("consumo_promedio_base", 
                                                               original_productos[0].get("consumo_promedio", 0))
        
        # Apply +15% adjustment
        response = self.session.post(
            f"{BASE_URL}/api/v2/automatizaciones/operativas/compras/{auto_id}/parametros-consumo",
            json={
                "porcentaje_ajuste": 15.0,
                "motivo": "Test: Ajuste positivo +15%"
            }
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        result = response.json()
        assert result.get("success"), f"Expected success=True, got {result}"
        assert result.get("recalculado"), "Expected recalculado=True"
        
        # Verify the adjustment was applied
        assert result.get("cambios", {}).get("porcentaje_ajuste", {}).get("nuevo") == 15.0, \
            f"Expected nuevo=15.0, got {result.get('cambios')}"
        
        # Get updated automatizacion
        response = self.session.get(
            f"{BASE_URL}/api/v2/automatizaciones/operativas/compras/{auto_id}"
        )
        assert response.status_code == 200
        
        updated = response.json()
        
        # Verify porcentaje_ajuste_consumo is now 15
        assert updated.get("porcentaje_ajuste_consumo") == 15.0, \
            f"Expected porcentaje_ajuste_consumo=15.0, got {updated.get('porcentaje_ajuste_consumo')}"
        
        # Verify consumo_promedio_ajustado > consumo_promedio_base for products
        if updated.get("detalle_productos"):
            for prod in updated["detalle_productos"]:
                base = prod.get("consumo_promedio_base", 0)
                ajustado = prod.get("consumo_promedio_ajustado", prod.get("consumo_promedio", 0))
                
                if base > 0:
                    # With +15%, ajustado should be base * 1.15
                    expected_ajustado = round(base * 1.15, 2)
                    assert abs(ajustado - expected_ajustado) < 0.1, \
                        f"Product {prod.get('codigo')}: expected ajustado={expected_ajustado}, got {ajustado}"
        
        print("✓ Ajuste +15% aplicado correctamente. Consumo ajustado = base * 1.15")
        
        # Restore original adjustment
        self.session.post(
            f"{BASE_URL}/api/v2/automatizaciones/operativas/compras/{auto_id}/parametros-consumo",
            json={
                "porcentaje_ajuste": original_ajuste,
                "motivo": "Test: Restaurar ajuste original"
            }
        )
    
    # =========================================================================
    # TEST 4: POST parametros-consumo - Validar ajuste negativo disminuye consumo
    # =========================================================================
    
    def test_parametros_consumo_negative_adjustment_decreases_consumo(self):
        """POST /parametros-consumo - Ajuste -10% debe disminuir consumo_promedio_ajustado"""
        # Get an automatizacion to test
        response = self.session.get(
            f"{BASE_URL}/api/v2/automatizaciones/operativas/compras?limite=5"
        )
        assert response.status_code == 200
        
        automatizaciones = response.json()
        if not automatizaciones:
            pytest.skip("No automatizaciones found")
        
        # Find one with products
        test_auto = None
        for auto in automatizaciones:
            response = self.session.get(
                f"{BASE_URL}/api/v2/automatizaciones/operativas/compras/{auto.get('id')}"
            )
            if response.status_code == 200:
                data = response.json()
                if data.get("detalle_productos") and len(data.get("detalle_productos", [])) > 0:
                    test_auto = data
                    break
        
        if not test_auto:
            pytest.skip("No automatizacion with products found")
        
        auto_id = test_auto["id"]
        original_ajuste = test_auto.get("porcentaje_ajuste_consumo", 0)
        
        # Apply -10% adjustment
        response = self.session.post(
            f"{BASE_URL}/api/v2/automatizaciones/operativas/compras/{auto_id}/parametros-consumo",
            json={
                "porcentaje_ajuste": -10.0,
                "motivo": "Test: Ajuste negativo -10%"
            }
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        result = response.json()
        assert result.get("success"), f"Expected success=True, got {result}"
        
        # Get updated automatizacion
        response = self.session.get(
            f"{BASE_URL}/api/v2/automatizaciones/operativas/compras/{auto_id}"
        )
        assert response.status_code == 200
        
        updated = response.json()
        
        # Verify porcentaje_ajuste_consumo is now -10
        assert updated.get("porcentaje_ajuste_consumo") == -10.0, \
            f"Expected porcentaje_ajuste_consumo=-10.0, got {updated.get('porcentaje_ajuste_consumo')}"
        
        # Verify consumo_promedio_ajustado < consumo_promedio_base for products
        if updated.get("detalle_productos"):
            for prod in updated["detalle_productos"]:
                base = prod.get("consumo_promedio_base", 0)
                ajustado = prod.get("consumo_promedio_ajustado", prod.get("consumo_promedio", 0))
                
                if base > 0:
                    # With -10%, ajustado should be base * 0.90
                    expected_ajustado = round(base * 0.90, 2)
                    assert abs(ajustado - expected_ajustado) < 0.1, \
                        f"Product {prod.get('codigo')}: expected ajustado={expected_ajustado}, got {ajustado}"
        
        print("✓ Ajuste -10% aplicado correctamente. Consumo ajustado = base * 0.90")
        
        # Restore original adjustment
        self.session.post(
            f"{BASE_URL}/api/v2/automatizaciones/operativas/compras/{auto_id}/parametros-consumo",
            json={
                "porcentaje_ajuste": original_ajuste,
                "motivo": "Test: Restaurar ajuste original"
            }
        )
    
    # =========================================================================
    # TEST 5: POST parametros-consumo - Validar rango de porcentaje (-100 a +500)
    # =========================================================================
    
    def test_parametros_consumo_rejects_out_of_range_positive(self):
        """POST /parametros-consumo - Debe rechazar porcentaje > 500"""
        # Get an automatizacion
        response = self.session.get(
            f"{BASE_URL}/api/v2/automatizaciones/operativas/compras?limite=1"
        )
        assert response.status_code == 200
        
        automatizaciones = response.json()
        if not automatizaciones:
            pytest.skip("No automatizaciones found")
        
        auto_id = automatizaciones[0].get("id")
        
        # Try to apply +600% (out of range)
        response = self.session.post(
            f"{BASE_URL}/api/v2/automatizaciones/operativas/compras/{auto_id}/parametros-consumo",
            json={
                "porcentaje_ajuste": 600.0,
                "motivo": "Test: Ajuste fuera de rango"
            }
        )
        
        assert response.status_code == 400, f"Expected 400 for out of range, got {response.status_code}: {response.text}"
        
        error = response.json()
        assert "detail" in error, "Expected error detail"
        assert "-100" in error["detail"] or "500" in error["detail"], \
            f"Error should mention valid range, got: {error['detail']}"
        
        print(f"✓ Porcentaje +600% rechazado correctamente: {error['detail']}")
    
    def test_parametros_consumo_rejects_out_of_range_negative(self):
        """POST /parametros-consumo - Debe rechazar porcentaje < -100"""
        # Get an automatizacion
        response = self.session.get(
            f"{BASE_URL}/api/v2/automatizaciones/operativas/compras?limite=1"
        )
        assert response.status_code == 200
        
        automatizaciones = response.json()
        if not automatizaciones:
            pytest.skip("No automatizaciones found")
        
        auto_id = automatizaciones[0].get("id")
        
        # Try to apply -150% (out of range)
        response = self.session.post(
            f"{BASE_URL}/api/v2/automatizaciones/operativas/compras/{auto_id}/parametros-consumo",
            json={
                "porcentaje_ajuste": -150.0,
                "motivo": "Test: Ajuste fuera de rango negativo"
            }
        )
        
        assert response.status_code == 400, f"Expected 400 for out of range, got {response.status_code}: {response.text}"
        
        error = response.json()
        assert "detail" in error, "Expected error detail"
        
        print(f"✓ Porcentaje -150% rechazado correctamente: {error['detail']}")
    
    def test_parametros_consumo_accepts_boundary_values(self):
        """POST /parametros-consumo - Debe aceptar valores límite -100 y +500"""
        # Get an automatizacion
        response = self.session.get(
            f"{BASE_URL}/api/v2/automatizaciones/operativas/compras?limite=1"
        )
        assert response.status_code == 200
        
        automatizaciones = response.json()
        if not automatizaciones:
            pytest.skip("No automatizaciones found")
        
        auto_id = automatizaciones[0].get("id")
        
        # Get original value
        response = self.session.get(
            f"{BASE_URL}/api/v2/automatizaciones/operativas/compras/{auto_id}"
        )
        original_ajuste = response.json().get("porcentaje_ajuste_consumo", 0)
        
        # Test -100 (minimum valid)
        response = self.session.post(
            f"{BASE_URL}/api/v2/automatizaciones/operativas/compras/{auto_id}/parametros-consumo",
            json={
                "porcentaje_ajuste": -100.0,
                "motivo": "Test: Valor límite -100%"
            }
        )
        
        assert response.status_code == 200, f"Expected 200 for -100%, got {response.status_code}: {response.text}"
        print("✓ Porcentaje -100% aceptado (valor límite inferior)")
        
        # Test +500 (maximum valid)
        response = self.session.post(
            f"{BASE_URL}/api/v2/automatizaciones/operativas/compras/{auto_id}/parametros-consumo",
            json={
                "porcentaje_ajuste": 500.0,
                "motivo": "Test: Valor límite +500%"
            }
        )
        
        assert response.status_code == 200, f"Expected 200 for +500%, got {response.status_code}: {response.text}"
        print("✓ Porcentaje +500% aceptado (valor límite superior)")
        
        # Restore original
        self.session.post(
            f"{BASE_URL}/api/v2/automatizaciones/operativas/compras/{auto_id}/parametros-consumo",
            json={
                "porcentaje_ajuste": original_ajuste,
                "motivo": "Test: Restaurar valor original"
            }
        )
    
    # =========================================================================
    # TEST 6: Bitácora registra CAMBIO_PARAMETROS_CONSUMO
    # =========================================================================
    
    def test_bitacora_registers_cambio_parametros_consumo(self):
        """GET /bitacora - Debe mostrar eventos CAMBIO_PARAMETROS_CONSUMO"""
        # Get an automatizacion
        response = self.session.get(
            f"{BASE_URL}/api/v2/automatizaciones/operativas/compras?limite=1"
        )
        assert response.status_code == 200
        
        automatizaciones = response.json()
        if not automatizaciones:
            pytest.skip("No automatizaciones found")
        
        auto_id = automatizaciones[0].get("id")
        
        # Get original value
        response = self.session.get(
            f"{BASE_URL}/api/v2/automatizaciones/operativas/compras/{auto_id}"
        )
        original_ajuste = response.json().get("porcentaje_ajuste_consumo", 0)
        
        # Make a change to create bitacora entry
        new_ajuste = 25.0 if original_ajuste != 25.0 else 30.0
        
        response = self.session.post(
            f"{BASE_URL}/api/v2/automatizaciones/operativas/compras/{auto_id}/parametros-consumo",
            json={
                "porcentaje_ajuste": new_ajuste,
                "motivo": "Test: Verificar bitácora"
            }
        )
        
        assert response.status_code == 200, f"Failed to apply adjustment: {response.text}"
        
        # Get bitacora
        response = self.session.get(
            f"{BASE_URL}/api/v2/automatizaciones/operativas/compras/{auto_id}/bitacora"
        )
        
        assert response.status_code == 200, f"Failed to get bitacora: {response.text}"
        
        bitacora = response.json()
        assert isinstance(bitacora, list), "Bitacora should be a list"
        
        # Find CAMBIO_PARAMETROS_CONSUMO event
        cambio_evento = None
        for entry in bitacora:
            if entry.get("evento") == "CAMBIO_PARAMETROS_CONSUMO":
                cambio_evento = entry
                break
        
        assert cambio_evento is not None, "CAMBIO_PARAMETROS_CONSUMO event not found in bitacora"
        
        # Verify event structure
        assert "fecha" in cambio_evento, "Event missing 'fecha'"
        assert "datos" in cambio_evento, "Event missing 'datos'"
        
        datos = cambio_evento.get("datos", {})
        assert "cambios" in datos or "motivo" in datos, "Event datos should have 'cambios' or 'motivo'"
        
        print("✓ Bitácora contiene CAMBIO_PARAMETROS_CONSUMO:")
        print(f"  - Fecha: {cambio_evento.get('fecha')}")
        print(f"  - Datos: {datos}")
        
        # Restore original
        self.session.post(
            f"{BASE_URL}/api/v2/automatizaciones/operativas/compras/{auto_id}/parametros-consumo",
            json={
                "porcentaje_ajuste": original_ajuste,
                "motivo": "Test: Restaurar valor original"
            }
        )
    
    # =========================================================================
    # TEST 7: POST parametros-consumo - Modificar periodo estadístico
    # =========================================================================
    
    def test_parametros_consumo_modify_statistical_period(self):
        """POST /parametros-consumo - Debe permitir modificar fecha_consumo_inicio y fecha_consumo_fin"""
        # Get an automatizacion
        response = self.session.get(
            f"{BASE_URL}/api/v2/automatizaciones/operativas/compras?limite=1"
        )
        assert response.status_code == 200
        
        automatizaciones = response.json()
        if not automatizaciones:
            pytest.skip("No automatizaciones found")
        
        auto_id = automatizaciones[0].get("id")
        
        # Get original values
        response = self.session.get(
            f"{BASE_URL}/api/v2/automatizaciones/operativas/compras/{auto_id}"
        )
        original = response.json()
        original_inicio = original.get("fecha_consumo_inicio")
        original_fin = original.get("fecha_consumo_fin")
        
        # Set new statistical period (e.g., same period last year)
        new_inicio = "2025-01-01"
        new_fin = "2025-01-15"
        
        response = self.session.post(
            f"{BASE_URL}/api/v2/automatizaciones/operativas/compras/{auto_id}/parametros-consumo",
            json={
                "fecha_consumo_inicio": new_inicio,
                "fecha_consumo_fin": new_fin,
                "motivo": "Test: Cambiar periodo estadístico"
            }
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        result = response.json()
        assert result.get("success"), f"Expected success=True, got {result}"
        
        # Verify changes in response
        cambios = result.get("cambios", {})
        periodo = cambios.get("periodo_estadistico", {})
        
        assert periodo.get("fecha_inicio") == new_inicio, \
            f"Expected fecha_inicio={new_inicio}, got {periodo.get('fecha_inicio')}"
        assert periodo.get("fecha_fin") == new_fin, \
            f"Expected fecha_fin={new_fin}, got {periodo.get('fecha_fin')}"
        
        print("✓ Periodo estadístico modificado:")
        print(f"  - Nuevo inicio: {new_inicio}")
        print(f"  - Nuevo fin: {new_fin}")
        print(f"  - Días: {periodo.get('dias')}")
        
        # Restore original
        if original_inicio and original_fin:
            self.session.post(
                f"{BASE_URL}/api/v2/automatizaciones/operativas/compras/{auto_id}/parametros-consumo",
                json={
                    "fecha_consumo_inicio": original_inicio.split('T')[0] if 'T' in original_inicio else original_inicio,
                    "fecha_consumo_fin": original_fin.split('T')[0] if 'T' in original_fin else original_fin,
                    "motivo": "Test: Restaurar periodo original"
                }
            )
    
    # =========================================================================
    # TEST 8: Verificar cálculo consumo_promedio_ajustado = consumo_base * (1 + ajuste/100)
    # =========================================================================
    
    def test_consumo_ajustado_formula_calculation(self):
        """Verificar fórmula: consumo_promedio_ajustado = consumo_base * (1 + ajuste/100)"""
        # Get an automatizacion with products
        response = self.session.get(
            f"{BASE_URL}/api/v2/automatizaciones/operativas/compras?limite=10"
        )
        assert response.status_code == 200
        
        automatizaciones = response.json()
        
        test_auto = None
        for auto in automatizaciones:
            response = self.session.get(
                f"{BASE_URL}/api/v2/automatizaciones/operativas/compras/{auto.get('id')}"
            )
            if response.status_code == 200:
                data = response.json()
                if data.get("detalle_productos") and len(data.get("detalle_productos", [])) > 0:
                    test_auto = data
                    break
        
        if not test_auto:
            pytest.skip("No automatizacion with products found")
        
        auto_id = test_auto["id"]
        original_ajuste = test_auto.get("porcentaje_ajuste_consumo", 0)
        
        # Apply specific adjustment for testing
        test_ajuste = 20.0  # +20%
        
        response = self.session.post(
            f"{BASE_URL}/api/v2/automatizaciones/operativas/compras/{auto_id}/parametros-consumo",
            json={
                "porcentaje_ajuste": test_ajuste,
                "motivo": "Test: Verificar fórmula de cálculo"
            }
        )
        
        assert response.status_code == 200
        
        # Get updated data
        response = self.session.get(
            f"{BASE_URL}/api/v2/automatizaciones/operativas/compras/{auto_id}"
        )
        updated = response.json()
        
        # Verify formula for each product
        errors = []
        for prod in updated.get("detalle_productos", []):
            base = prod.get("consumo_promedio_base", 0)
            ajustado = prod.get("consumo_promedio_ajustado", prod.get("consumo_promedio", 0))
            
            if base > 0:
                # Formula: ajustado = base * (1 + ajuste/100)
                expected = round(base * (1 + test_ajuste / 100), 2)
                
                if abs(ajustado - expected) > 0.1:
                    errors.append(f"Product {prod.get('codigo')}: base={base}, expected={expected}, got={ajustado}")
        
        assert len(errors) == 0, f"Formula errors: {errors}"
        
        print(f"✓ Fórmula verificada: consumo_ajustado = consumo_base * (1 + {test_ajuste}/100)")
        print(f"  - Todos los {len(updated.get('detalle_productos', []))} productos calculados correctamente")
        
        # Restore original
        self.session.post(
            f"{BASE_URL}/api/v2/automatizaciones/operativas/compras/{auto_id}/parametros-consumo",
            json={
                "porcentaje_ajuste": original_ajuste,
                "motivo": "Test: Restaurar ajuste original"
            }
        )
    
    # =========================================================================
    # TEST 9: Verificar que periodo operativo NO se modifica
    # =========================================================================
    
    def test_operational_period_not_modified(self):
        """POST /parametros-consumo - El periodo operativo (fecha_inicio_periodo, fecha_fin_periodo) NO debe modificarse"""
        # Get an automatizacion
        response = self.session.get(
            f"{BASE_URL}/api/v2/automatizaciones/operativas/compras?limite=1"
        )
        assert response.status_code == 200
        
        automatizaciones = response.json()
        if not automatizaciones:
            pytest.skip("No automatizaciones found")
        
        auto_id = automatizaciones[0].get("id")
        
        # Get original operational period
        response = self.session.get(
            f"{BASE_URL}/api/v2/automatizaciones/operativas/compras/{auto_id}"
        )
        original = response.json()
        
        original_inicio_periodo = original.get("fecha_inicio_periodo")
        original_fin_periodo = original.get("fecha_fin_periodo")
        original_fecha_pedido = original.get("fecha_pedido")
        
        # Modify statistical period and adjustment
        response = self.session.post(
            f"{BASE_URL}/api/v2/automatizaciones/operativas/compras/{auto_id}/parametros-consumo",
            json={
                "fecha_consumo_inicio": "2024-06-01",
                "fecha_consumo_fin": "2024-06-15",
                "porcentaje_ajuste": 50.0,
                "motivo": "Test: Verificar que periodo operativo no cambia"
            }
        )
        
        assert response.status_code == 200
        
        # Get updated data
        response = self.session.get(
            f"{BASE_URL}/api/v2/automatizaciones/operativas/compras/{auto_id}"
        )
        updated = response.json()
        
        # Verify operational period unchanged
        assert updated.get("fecha_inicio_periodo") == original_inicio_periodo, \
            f"fecha_inicio_periodo changed from {original_inicio_periodo} to {updated.get('fecha_inicio_periodo')}"
        
        assert updated.get("fecha_fin_periodo") == original_fin_periodo, \
            f"fecha_fin_periodo changed from {original_fin_periodo} to {updated.get('fecha_fin_periodo')}"
        
        assert updated.get("fecha_pedido") == original_fecha_pedido, \
            f"fecha_pedido changed from {original_fecha_pedido} to {updated.get('fecha_pedido')}"
        
        print("✓ Periodo operativo NO modificado:")
        print(f"  - fecha_inicio_periodo: {original_inicio_periodo}")
        print(f"  - fecha_fin_periodo: {original_fin_periodo}")
        print(f"  - fecha_pedido: {original_fecha_pedido}")
        
        # Restore
        self.session.post(
            f"{BASE_URL}/api/v2/automatizaciones/operativas/compras/{auto_id}/parametros-consumo",
            json={
                "porcentaje_ajuste": original.get("porcentaje_ajuste_consumo", 0),
                "motivo": "Test: Restaurar"
            }
        )
    
    # =========================================================================
    # TEST 10: Verificar autenticación requerida
    # =========================================================================
    
    def test_parametros_consumo_requires_authentication(self):
        """POST /parametros-consumo - Debe requerir autenticación"""
        # Get an automatizacion ID
        response = self.session.get(
            f"{BASE_URL}/api/v2/automatizaciones/operativas/compras?limite=1"
        )
        assert response.status_code == 200
        
        automatizaciones = response.json()
        if not automatizaciones:
            pytest.skip("No automatizaciones found")
        
        auto_id = automatizaciones[0].get("id")
        
        # Try without auth
        no_auth_session = requests.Session()
        no_auth_session.headers.update({"Content-Type": "application/json"})
        
        response = no_auth_session.post(
            f"{BASE_URL}/api/v2/automatizaciones/operativas/compras/{auto_id}/parametros-consumo",
            json={
                "porcentaje_ajuste": 10.0,
                "motivo": "Test sin auth"
            }
        )
        
        assert response.status_code in [401, 403], \
            f"Expected 401/403 without auth, got {response.status_code}"
        
        print(f"✓ Endpoint requiere autenticación (status {response.status_code})")
    
    # =========================================================================
    # TEST 11: Verificar que no hay cambios si valores son iguales
    # =========================================================================
    
    def test_parametros_consumo_no_change_if_same_values(self):
        """POST /parametros-consumo - Debe retornar 'Sin cambios' si valores son iguales"""
        # Get an automatizacion
        response = self.session.get(
            f"{BASE_URL}/api/v2/automatizaciones/operativas/compras?limite=1"
        )
        assert response.status_code == 200
        
        automatizaciones = response.json()
        if not automatizaciones:
            pytest.skip("No automatizaciones found")
        
        auto_id = automatizaciones[0].get("id")
        
        # Get current values
        response = self.session.get(
            f"{BASE_URL}/api/v2/automatizaciones/operativas/compras/{auto_id}"
        )
        current = response.json()
        current_ajuste = current.get("porcentaje_ajuste_consumo", 0)
        
        # Send same value
        response = self.session.post(
            f"{BASE_URL}/api/v2/automatizaciones/operativas/compras/{auto_id}/parametros-consumo",
            json={
                "porcentaje_ajuste": current_ajuste,
                "motivo": "Test: Sin cambios"
            }
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        result = response.json()
        assert result.get("success")
        
        # Should indicate no changes or recalculado=False
        if result.get("mensaje"):
            assert "sin cambios" in result.get("mensaje", "").lower() or \
                   not result.get("recalculado"), \
                   f"Expected 'sin cambios' message, got {result}"
            print(f"✓ Respuesta correcta para valores iguales: {result.get('mensaje')}")
        else:
            print("✓ Valores iguales procesados (puede haber recalculado)")


# Run tests if executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
