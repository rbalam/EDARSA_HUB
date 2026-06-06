"""
EDARSA HUB - Tests de Automatización Operativa de Compras (Fase 4.1 y 4.2)
==========================================================================
Tests para el detector automático de pedidos y tareas operativas.

ENDPOINTS TESTEADOS:
- POST /api/v2/automatizaciones/operativas/compras/detector/ejecutar
- GET /api/v2/automatizaciones/operativas/compras/detector/estado
- GET /api/v2/automatizaciones/operativas/compras/detector/bitacora
- GET /api/v2/automatizaciones/operativas/compras/pedidos-procesados
- GET /api/v2/automatizaciones/operativas/compras/tareas
- GET /api/v2/automatizaciones/operativas/compras/kpis
- GET /api/v2/automatizaciones/operativas/compras

COLECCIONES MONGODB:
- pedidos_procesados_automatizacion
- auditoria_compras_bitacora
- tareas_operativas_compras
"""

import pytest
import requests
import os

# Import centralized test credentials
from conftest import TEST_ADMIN_EMAIL, TEST_ADMIN_PASSWORD

# Base URL from environment
BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://erp-crm-enterprise-1.preview.emergentagent.com').rstrip('/')

# Test credentials (centralized)
TEST_CREDENTIALS = {
    "email": os.environ.get("TEST_ADMIN_EMAIL", TEST_ADMIN_EMAIL),
    "password": os.environ.get("TEST_ADMIN_PASSWORD", TEST_ADMIN_PASSWORD)
}


class TestAutomatizacionComprasFase4:
    """Tests para Fase 4.1 y 4.2 - Detector de Pedidos y Tareas Operativas"""
    
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
    # FASE 4.1: DETECTOR DE PEDIDOS - ESTADO
    # =========================================================================
    
    def test_detector_estado_returns_200(self):
        """GET /detector/estado - Debe retornar estado del job"""
        response = self.session.get(
            f"{BASE_URL}/api/v2/automatizaciones/operativas/compras/detector/estado"
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        # Verificar estructura de respuesta
        assert "ultima_ejecucion" in data, "Missing 'ultima_ejecucion' in response"
        assert "job_info" in data, "Missing 'job_info' in response"
        assert "intervalo_segundos" in data, "Missing 'intervalo_segundos' in response"
        
        # Verificar intervalo configurado (5 minutos = 300 segundos)
        assert data["intervalo_segundos"] == 300, f"Expected 300s interval, got {data['intervalo_segundos']}"
        
        print(f"✓ Detector estado: ultima_ejecucion={data.get('ultima_ejecucion')}, intervalo={data['intervalo_segundos']}s")
    
    def test_detector_estado_shows_job_info(self):
        """GET /detector/estado - Debe mostrar info del job si está registrado"""
        response = self.session.get(
            f"{BASE_URL}/api/v2/automatizaciones/operativas/compras/detector/estado"
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Si el job está registrado, debe tener info
        if data.get("job_info"):
            job_info = data["job_info"]
            assert "id" in job_info or "name" in job_info, "Job info should have id or name"
            print(f"✓ Job info: {job_info}")
        else:
            print("⚠ Job info is None (scheduler may not be running)")
    
    # =========================================================================
    # FASE 4.1: DETECTOR DE PEDIDOS - EJECUCIÓN MANUAL
    # =========================================================================
    
    def test_detector_ejecutar_manual_returns_200(self):
        """POST /detector/ejecutar - Debe ejecutar detector manualmente"""
        response = self.session.post(
            f"{BASE_URL}/api/v2/automatizaciones/operativas/compras/detector/ejecutar",
            json={}
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data.get("success"), f"Expected success=True, got {data}"
        assert "mensaje" in data, "Missing 'mensaje' in response"
        assert "estadisticas" in data, "Missing 'estadisticas' in response"
        
        # Verificar estructura de estadísticas
        stats = data["estadisticas"]
        expected_keys = [
            "empresas_procesadas",
            "servidores_consultados",
            "pedidos_detectados",
            "pedidos_nuevos",
            "ya_procesados",
            "tareas_creadas",
            "auditorias_iniciadas",
            "fallidos"
        ]
        for key in expected_keys:
            assert key in stats, f"Missing '{key}' in estadisticas"
        
        print(f"✓ Detector ejecutado: {stats}")
    
    def test_detector_ejecutar_con_empresa_filter(self):
        """POST /detector/ejecutar - Debe aceptar filtro por empresa"""
        response = self.session.post(
            f"{BASE_URL}/api/v2/automatizaciones/operativas/compras/detector/ejecutar",
            json={"empresa_id": "empresa_test_inexistente"}
        )
        
        # Debe retornar 200 aunque no encuentre la empresa
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data.get("success")
        
        # Con empresa inexistente, no debe procesar nada
        stats = data.get("estadisticas", {})
        assert stats.get("empresas_procesadas", 0) == 0, "Should not process any empresa with invalid filter"
        
        print(f"✓ Detector con filtro empresa: {stats}")
    
    def test_detector_ejecutar_requires_auth(self):
        """POST /detector/ejecutar - Debe requerir autenticación"""
        # Request sin token
        response = requests.post(
            f"{BASE_URL}/api/v2/automatizaciones/operativas/compras/detector/ejecutar",
            json={},
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code in [401, 403], f"Expected 401/403 without auth, got {response.status_code}"
        print("✓ Detector ejecutar requiere autenticación")
    
    # =========================================================================
    # FASE 4.1: BITÁCORA DEL DETECTOR
    # =========================================================================
    
    def test_bitacora_detector_returns_200(self):
        """GET /detector/bitacora - Debe retornar bitácora de ejecuciones"""
        response = self.session.get(
            f"{BASE_URL}/api/v2/automatizaciones/operativas/compras/detector/bitacora"
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "total" in data, "Missing 'total' in response"
        assert "eventos" in data, "Missing 'eventos' in response"
        assert isinstance(data["eventos"], list), "eventos should be a list"
        
        print(f"✓ Bitácora detector: {data['total']} eventos")
    
    def test_bitacora_detector_respects_limite(self):
        """GET /detector/bitacora - Debe respetar parámetro limite"""
        response = self.session.get(
            f"{BASE_URL}/api/v2/automatizaciones/operativas/compras/detector/bitacora",
            params={"limite": 5}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # No debe retornar más del límite
        assert len(data["eventos"]) <= 5, f"Expected max 5 eventos, got {len(data['eventos'])}"
        
        print(f"✓ Bitácora con limite=5: {len(data['eventos'])} eventos")
    
    def test_bitacora_evento_structure(self):
        """GET /detector/bitacora - Eventos deben tener estructura correcta"""
        response = self.session.get(
            f"{BASE_URL}/api/v2/automatizaciones/operativas/compras/detector/bitacora",
            params={"limite": 10}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        if data["eventos"]:
            evento = data["eventos"][0]
            # Verificar campos esperados
            assert "id" in evento, "Evento missing 'id'"
            assert "job" in evento, "Evento missing 'job'"
            assert "evento" in evento, "Evento missing 'evento'"
            assert "fecha" in evento, "Evento missing 'fecha'"
            
            print(f"✓ Evento estructura: job={evento['job']}, evento={evento['evento']}")
        else:
            print("⚠ No hay eventos en bitácora")
    
    # =========================================================================
    # FASE 4.1: PEDIDOS PROCESADOS (ANTI-DUPLICADOS)
    # =========================================================================
    
    def test_pedidos_procesados_returns_200(self):
        """GET /pedidos-procesados - Debe retornar lista de pedidos procesados"""
        response = self.session.get(
            f"{BASE_URL}/api/v2/automatizaciones/operativas/compras/pedidos-procesados"
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "total" in data, "Missing 'total' in response"
        assert "pedidos" in data, "Missing 'pedidos' in response"
        assert isinstance(data["pedidos"], list), "pedidos should be a list"
        
        print(f"✓ Pedidos procesados: {data['total']} registros")
    
    def test_pedidos_procesados_filter_by_empresa(self):
        """GET /pedidos-procesados - Debe filtrar por empresa_id"""
        response = self.session.get(
            f"{BASE_URL}/api/v2/automatizaciones/operativas/compras/pedidos-procesados",
            params={"empresa_id": "empresa_test"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Todos los pedidos deben ser de la empresa filtrada
        for pedido in data["pedidos"]:
            if "empresa_id" in pedido:
                assert pedido["empresa_id"] == "empresa_test", f"Pedido has wrong empresa_id: {pedido['empresa_id']}"
        
        print(f"✓ Pedidos filtrados por empresa: {data['total']}")
    
    def test_pedidos_procesados_filter_by_estado(self):
        """GET /pedidos-procesados - Debe filtrar por estado"""
        response = self.session.get(
            f"{BASE_URL}/api/v2/automatizaciones/operativas/compras/pedidos-procesados",
            params={"estado": "PENDIENTE_INVENTARIO"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Todos los pedidos deben tener el estado filtrado
        for pedido in data["pedidos"]:
            if "estado" in pedido:
                assert pedido["estado"] == "PENDIENTE_INVENTARIO", f"Pedido has wrong estado: {pedido['estado']}"
        
        print(f"✓ Pedidos filtrados por estado: {data['total']}")
    
    def test_pedidos_procesados_structure(self):
        """GET /pedidos-procesados - Pedidos deben tener estructura correcta"""
        response = self.session.get(
            f"{BASE_URL}/api/v2/automatizaciones/operativas/compras/pedidos-procesados",
            params={"limite": 10}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        if data["pedidos"]:
            pedido = data["pedidos"][0]
            # Verificar campos clave - empresa_id es el eje en Fase 4.1, pero puede haber datos legacy con server_id
            assert "pedido_folio" in pedido, "Pedido missing 'pedido_folio'"
            assert "origen" in pedido, "Pedido missing 'origen'"
            assert "fecha_procesado" in pedido, "Pedido missing 'fecha_procesado'"
            
            # empresa_id o server_id deben existir (empresa_id es el nuevo estándar)
            has_identifier = "empresa_id" in pedido or "server_id" in pedido
            assert has_identifier, "Pedido missing both 'empresa_id' and 'server_id'"
            
            identifier = pedido.get('empresa_id') or pedido.get('server_id')
            estado = pedido.get('estado', 'N/A')
            print(f"✓ Pedido estructura: id={identifier}, folio={pedido['pedido_folio']}, estado={estado}")
        else:
            print("⚠ No hay pedidos procesados")
    
    # =========================================================================
    # FASE 4.2: TAREAS OPERATIVAS
    # =========================================================================
    
    def test_tareas_operativas_returns_200(self):
        """GET /tareas - Debe retornar lista de tareas operativas"""
        response = self.session.get(
            f"{BASE_URL}/api/v2/automatizaciones/operativas/compras/tareas"
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "total" in data, "Missing 'total' in response"
        assert "tareas" in data, "Missing 'tareas' in response"
        assert isinstance(data["tareas"], list), "tareas should be a list"
        
        print(f"✓ Tareas operativas: {data['total']} registros")
    
    def test_tareas_operativas_filter_by_empresa(self):
        """GET /tareas - Debe filtrar por empresa_id"""
        response = self.session.get(
            f"{BASE_URL}/api/v2/automatizaciones/operativas/compras/tareas",
            params={"empresa_id": "empresa_test"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Todos las tareas deben ser de la empresa filtrada
        for tarea in data["tareas"]:
            if "empresa_id" in tarea:
                assert tarea["empresa_id"] == "empresa_test"
        
        print(f"✓ Tareas filtradas por empresa: {data['total']}")
    
    def test_tareas_operativas_filter_by_estado(self):
        """GET /tareas - Debe filtrar por estado"""
        response = self.session.get(
            f"{BASE_URL}/api/v2/automatizaciones/operativas/compras/tareas",
            params={"estado": "PENDIENTE"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        for tarea in data["tareas"]:
            if "estado" in tarea:
                assert tarea["estado"] == "PENDIENTE"
        
        print(f"✓ Tareas filtradas por estado PENDIENTE: {data['total']}")
    
    def test_tareas_operativas_structure(self):
        """GET /tareas - Tareas deben tener estructura correcta"""
        response = self.session.get(
            f"{BASE_URL}/api/v2/automatizaciones/operativas/compras/tareas",
            params={"limite": 10}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        if data["tareas"]:
            tarea = data["tareas"][0]
            # Verificar campos clave de tarea operativa
            expected_fields = [
                "id", "tipo", "estado", "prioridad",
                "empresa_id", "empresa_nombre",
                "pedido_folio", "titulo", "descripcion",
                "fecha_creacion"
            ]
            for field in expected_fields:
                assert field in tarea, f"Tarea missing '{field}'"
            
            # Verificar que tipo es CAPTURA_INVENTARIO
            assert tarea["tipo"] == "CAPTURA_INVENTARIO", f"Expected tipo=CAPTURA_INVENTARIO, got {tarea['tipo']}"
            
            print(f"✓ Tarea estructura: id={tarea['id']}, tipo={tarea['tipo']}, estado={tarea['estado']}")
        else:
            print("⚠ No hay tareas operativas")
    
    # =========================================================================
    # KPIS DE AUTOMATIZACIONES
    # =========================================================================
    
    def test_kpis_returns_200(self):
        """GET /kpis - Debe retornar KPIs de automatizaciones"""
        response = self.session.get(
            f"{BASE_URL}/api/v2/automatizaciones/operativas/compras/kpis"
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        # KPIs debe ser un dict con métricas
        assert isinstance(data, dict), "KPIs should be a dict"
        
        print(f"✓ KPIs: {data}")
    
    def test_kpis_filter_by_server(self):
        """GET /kpis - Debe aceptar filtro por server_id"""
        response = self.session.get(
            f"{BASE_URL}/api/v2/automatizaciones/operativas/compras/kpis",
            params={"server_id": "server_test"}
        )
        
        assert response.status_code == 200
        print("✓ KPIs con filtro server_id")
    
    # =========================================================================
    # LISTA DE AUTOMATIZACIONES
    # =========================================================================
    
    def test_listar_automatizaciones_returns_200(self):
        """GET /compras - Debe retornar lista de automatizaciones"""
        response = self.session.get(
            f"{BASE_URL}/api/v2/automatizaciones/operativas/compras"
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        # Puede ser lista o dict con lista
        if isinstance(data, dict):
            assert "automatizaciones" in data or "items" in data or "total" in data, \
                f"Unexpected response structure: {data.keys()}"
        
        print(f"✓ Automatizaciones listadas: {data}")
    
    def test_listar_automatizaciones_filter_by_estado(self):
        """GET /compras - Debe filtrar por estado"""
        response = self.session.get(
            f"{BASE_URL}/api/v2/automatizaciones/operativas/compras",
            params={"estado": "EN_REVISION_GERENCIA"}
        )
        
        assert response.status_code == 200
        print("✓ Automatizaciones filtradas por estado")
    
    def test_listar_automatizaciones_filter_by_sucursal(self):
        """GET /compras - Debe filtrar por sucursal_id"""
        response = self.session.get(
            f"{BASE_URL}/api/v2/automatizaciones/operativas/compras",
            params={"sucursal_id": "SUC001"}
        )
        
        assert response.status_code == 200
        print("✓ Automatizaciones filtradas por sucursal")
    
    def test_listar_automatizaciones_respects_limite(self):
        """GET /compras - Debe respetar parámetro limite"""
        response = self.session.get(
            f"{BASE_URL}/api/v2/automatizaciones/operativas/compras",
            params={"limite": 5}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verificar que no excede el límite
        if isinstance(data, list):
            assert len(data) <= 5
        elif isinstance(data, dict) and "automatizaciones" in data:
            assert len(data["automatizaciones"]) <= 5
        
        print("✓ Automatizaciones con limite=5")
    
    # =========================================================================
    # TESTS DE SEGURIDAD Y PERMISOS
    # =========================================================================
    
    def test_all_endpoints_require_auth(self):
        """Todos los endpoints deben requerir autenticación"""
        endpoints = [
            ("GET", "/api/v2/automatizaciones/operativas/compras/detector/estado"),
            ("GET", "/api/v2/automatizaciones/operativas/compras/detector/bitacora"),
            ("GET", "/api/v2/automatizaciones/operativas/compras/pedidos-procesados"),
            ("GET", "/api/v2/automatizaciones/operativas/compras/tareas"),
            ("GET", "/api/v2/automatizaciones/operativas/compras/kpis"),
            ("GET", "/api/v2/automatizaciones/operativas/compras"),
        ]
        
        for method, endpoint in endpoints:
            if method == "GET":
                response = requests.get(f"{BASE_URL}{endpoint}")
            else:
                response = requests.post(f"{BASE_URL}{endpoint}", json={})
            
            assert response.status_code in [401, 403], \
                f"{method} {endpoint} should require auth, got {response.status_code}"
        
        print("✓ Todos los endpoints requieren autenticación")


class TestTareasOperativasWorkflow:
    """Tests para el workflow de tareas operativas (Fase 4.2)"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup: obtener token de autenticación"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        response = self.session.post(
            f"{BASE_URL}/api/auth/login",
            json=TEST_CREDENTIALS
        )
        if response.status_code == 200:
            token = response.json().get("token")
            self.session.headers.update({"Authorization": f"Bearer {token}"})
        else:
            pytest.skip("Authentication failed")
    
    def test_obtener_tarea_por_id_404(self):
        """GET /tareas/{tarea_id} - Debe retornar 404 para tarea inexistente"""
        response = self.session.get(
            f"{BASE_URL}/api/v2/automatizaciones/operativas/compras/tareas/tarea_inexistente_123"
        )
        
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("✓ Tarea inexistente retorna 404")
    
    def test_completar_tarea_404(self):
        """POST /tareas/{tarea_id}/completar - Debe retornar 404 para tarea inexistente"""
        response = self.session.post(
            f"{BASE_URL}/api/v2/automatizaciones/operativas/compras/tareas/tarea_inexistente_123/completar"
        )
        
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("✓ Completar tarea inexistente retorna 404")
    
    def test_asignar_tarea_404(self):
        """POST /tareas/{tarea_id}/asignar - Debe retornar 404 para tarea inexistente"""
        response = self.session.post(
            f"{BASE_URL}/api/v2/automatizaciones/operativas/compras/tareas/tarea_inexistente_123/asignar",
            params={"usuario_id": "user123"}
        )
        
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("✓ Asignar tarea inexistente retorna 404")
    
    def test_workflow_tarea_existente(self):
        """Test workflow completo si existe una tarea"""
        # Primero obtener lista de tareas
        response = self.session.get(
            f"{BASE_URL}/api/v2/automatizaciones/operativas/compras/tareas",
            params={"limite": 1}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        if data["tareas"]:
            tarea_id = data["tareas"][0]["id"]
            
            # Obtener detalle
            detail_response = self.session.get(
                f"{BASE_URL}/api/v2/automatizaciones/operativas/compras/tareas/{tarea_id}"
            )
            assert detail_response.status_code == 200
            
            tarea = detail_response.json()
            assert tarea["id"] == tarea_id
            
            print(f"✓ Workflow tarea existente: {tarea_id}")
        else:
            print("⚠ No hay tareas para probar workflow")


class TestAutomatizacionComprasExistentes:
    """Tests para automatizaciones existentes"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup: obtener token de autenticación"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        response = self.session.post(
            f"{BASE_URL}/api/auth/login",
            json=TEST_CREDENTIALS
        )
        if response.status_code == 200:
            token = response.json().get("token")
            self.session.headers.update({"Authorization": f"Bearer {token}"})
        else:
            pytest.skip("Authentication failed")
    
    def test_obtener_automatizacion_404(self):
        """GET /compras/{automatizacion_id} - Debe retornar 404 para ID inexistente"""
        response = self.session.get(
            f"{BASE_URL}/api/v2/automatizaciones/operativas/compras/automatizacion_inexistente_123"
        )
        
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("✓ Automatización inexistente retorna 404")
    
    def test_obtener_automatizacion_existente(self):
        """GET /compras/{automatizacion_id} - Debe retornar automatización existente"""
        # Primero obtener lista
        list_response = self.session.get(
            f"{BASE_URL}/api/v2/automatizaciones/operativas/compras",
            params={"limite": 1}
        )
        
        assert list_response.status_code == 200
        data = list_response.json()
        
        # Buscar automatizaciones en la respuesta
        automatizaciones = []
        if isinstance(data, list):
            automatizaciones = data
        elif isinstance(data, dict):
            automatizaciones = data.get("automatizaciones", data.get("items", []))
        
        if automatizaciones:
            auto_id = automatizaciones[0].get("id") or automatizaciones[0].get("automatizacion_id")
            
            if auto_id:
                detail_response = self.session.get(
                    f"{BASE_URL}/api/v2/automatizaciones/operativas/compras/{auto_id}"
                )
                assert detail_response.status_code == 200
                
                detail_response.json()
                print(f"✓ Automatización existente: {auto_id}")
            else:
                print("⚠ Automatización sin ID")
        else:
            print("⚠ No hay automatizaciones para probar")
    
    def test_obtener_bitacora_automatizacion_404(self):
        """GET /compras/{automatizacion_id}/bitacora - Debe retornar 404 o vacío para ID inexistente"""
        response = self.session.get(
            f"{BASE_URL}/api/v2/automatizaciones/operativas/compras/automatizacion_inexistente_123/bitacora"
        )
        
        # Puede retornar 404 o lista vacía
        assert response.status_code in [200, 404], f"Expected 200 or 404, got {response.status_code}"
        print(f"✓ Bitácora automatización inexistente: status={response.status_code}")


# =============================================================================
# EJECUCIÓN DIRECTA
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
