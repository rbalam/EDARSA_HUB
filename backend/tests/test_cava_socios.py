"""
EDARSA HUB - Tests para Módulo Cava de Socios
==============================================
Pruebas unitarias de esquemas, rutas, resolución de alcance RBAC y servicio de Cavas.
"""

import pytest
from uuid import UUID
from unittest.mock import MagicMock, patch
from fastapi import HTTPException
from pydantic import ValidationError

from modules.cava_socios.routes import (
    router,
    SocioCreate,
    SocioUpdate,
    BotellaCreate,
    ConsumoCreate,
    _resolve_cava_scope,
)
from modules.cava_socios.service import CavaSociosService


class TestCavaSociosSchemas:
    """Pruebas para esquemas de Pydantic"""

    @pytest.mark.unit
    def test_socio_create_valid(self):
        socio = SocioCreate(
            nombre_completo="Juan Pérez",
            numero_socio="SOC-001",
            email="juan@example.com",
            telefono="5551234567",
            tipo_membresia="VIP",
            maximo_botellas=24,
        )
        assert socio.nombre_completo == "Juan Pérez"
        assert socio.tipo_membresia == "VIP"
        assert socio.maximo_botellas == 24

    @pytest.mark.unit
    def test_socio_create_invalid_nombre(self):
        with pytest.raises(ValidationError):
            SocioCreate(nombre_completo="AB")  # Mínimo 3 caracteres

    @pytest.mark.unit
    def test_socio_update_valid(self):
        update = SocioUpdate(
            nombre_completo="Juan Pérez Modificado",
            email="nuevo@example.com",
            estatus="SUSPENDIDO",
        )
        assert update.nombre_completo == "Juan Pérez Modificado"
        assert update.estatus == "SUSPENDIDO"

    @pytest.mark.unit
    def test_botella_create_valid(self):
        botella = BotellaCreate(
            producto_nombre="Vega Sicilia Único 2010",
            tipo_bebida="VINO_TINTO",
            añada="2010",
            valor_declarado=15000.0,
        )
        assert botella.producto_nombre == "Vega Sicilia Único 2010"
        assert botella.valor_declarado == 15000.0

    @pytest.mark.unit
    def test_consumo_create_valid(self):
        consumo = ConsumoCreate(
            porcentaje_consumido=50.0,
            motivo="Celebración aniversario",
            generar_cargo_descorche=True,
            monto_descorche=350.0,
        )
        assert consumo.porcentaje_consumido == 50.0
        assert consumo.monto_descorche == 350.0


class TestCavaScopeResolution:
    """Pruebas para la resolución de alcance RBAC en Cavas"""

    UNIT_ID = "19e076fb-c6de-4ea5-84ab-1caa9e86082c"

    @pytest.mark.unit
    @patch("modules.cava_socios.routes.context_service.get_user_context")
    @patch("modules.cava_socios.routes.enrich_current_user_with_sql_id")
    def test_resolve_cava_scope_success(self, mock_enrich, mock_get_context):
        mock_user = {"id": "user-123", "email": "test@edarsa.com"}
        mock_enrich.return_value = mock_user
        mock_get_context.return_value = {
            "unidad_activa": self.UNIT_ID,
            "unidades_permitidas": [
                {"UnidadNegocioID": self.UNIT_ID, "EmpresaID": 5}
            ],
        }

        scope = _resolve_cava_scope(mock_user, self.UNIT_ID)
        assert scope["empresa_id"] == self.UNIT_ID
        assert scope["unidad_negocio_pk"] == self.UNIT_ID

    @pytest.mark.unit
    @patch("modules.cava_socios.routes.context_service.get_user_context")
    @patch("modules.cava_socios.routes.enrich_current_user_with_sql_id")
    def test_resolve_cava_scope_unauthorized_unit(self, mock_enrich, mock_get_context):
        mock_user = {"id": "user-123"}
        mock_enrich.return_value = mock_user
        mock_get_context.return_value = {
            "unidad_activa": "8d46691e-7f28-42fc-a7f8-7797e34e5c2e",
            "unidades_permitidas": [
                {"UnidadNegocioID": self.UNIT_ID, "EmpresaID": 5}
            ],
        }

        with pytest.raises(HTTPException) as exc_info:
            _resolve_cava_scope(mock_user, "8d46691e-7f28-42fc-a7f8-7797e34e5c2e")
        assert exc_info.value.status_code == 403

    @pytest.mark.unit
    @patch("modules.cava_socios.routes.context_service.get_user_context")
    @patch("modules.cava_socios.routes.enrich_current_user_with_sql_id")
    def test_resolve_cava_scope_uses_unit_when_corporate_empresa_missing(self, mock_enrich, mock_get_context):
        mock_user = {"id": "user-123"}
        mock_enrich.return_value = mock_user
        mock_get_context.return_value = {
            "unidad_activa": self.UNIT_ID,
            "unidades_permitidas": [
                {"UnidadNegocioID": self.UNIT_ID, "EmpresaID": None}
            ],
        }

        scope = _resolve_cava_scope(mock_user, self.UNIT_ID)
        assert scope["empresa_id"] == self.UNIT_ID
        assert scope["unidad_negocio_pk"] == self.UNIT_ID

    @pytest.mark.unit
    @patch("modules.cava_socios.routes.context_service.get_user_context")
    @patch("modules.cava_socios.routes.enrich_current_user_with_sql_id")
    def test_resolve_cava_scope_normalizes_uuid_case(self, mock_enrich, mock_get_context):
        mock_user = {"id": "user-123"}
        mock_enrich.return_value = mock_user
        mock_get_context.return_value = {
            "unidad_activa": self.UNIT_ID.upper(),
            "unidades_permitidas": [
                {"UnidadNegocioID": self.UNIT_ID, "EmpresaID": None}
            ],
        }

        scope = _resolve_cava_scope(mock_user, self.UNIT_ID.upper())
        assert scope["empresa_id"] == self.UNIT_ID
        assert scope["unidad_negocio_pk"] == self.UNIT_ID

    @pytest.mark.unit
    @patch("modules.cava_socios.routes.context_service.get_user_context")
    @patch("modules.cava_socios.routes.enrich_current_user_with_sql_id")
    def test_resolve_cava_scope_accepts_uuid_object(self, mock_enrich, mock_get_context):
        mock_user = {"id": "user-123"}
        mock_enrich.return_value = mock_user
        unit_id = UUID(self.UNIT_ID)
        mock_get_context.return_value = {
            "unidad_activa": unit_id,
            "unidades_permitidas": [
                {"UnidadNegocioID": unit_id, "EmpresaID": None}
            ],
        }

        scope = _resolve_cava_scope(mock_user, str(unit_id).upper())
        assert scope["empresa_id"] == self.UNIT_ID
        assert scope["unidad_negocio_pk"] == self.UNIT_ID

    @pytest.mark.unit
    @patch("modules.cava_socios.routes.context_service.get_user_context")
    @patch("modules.cava_socios.routes.enrich_current_user_with_sql_id")
    def test_resolve_cava_scope_invalid_uuid_fails_closed(self, mock_enrich, mock_get_context):
        mock_user = {"id": "user-123"}
        mock_enrich.return_value = mock_user
        mock_get_context.return_value = {
            "unidad_activa": "NOT-A-UUID",
            "unidades_permitidas": [
                {"UnidadNegocioID": self.UNIT_ID, "EmpresaID": None}
            ],
        }

        with pytest.raises(HTTPException) as exc_info:
            _resolve_cava_scope(mock_user, "NOT-A-UUID")
        assert exc_info.value.status_code == 403


class TestCavaSociosService:
    """Pruebas unitarias para métodos del servicio CavaSociosService"""

    @pytest.mark.unit
    def test_actualizar_socio_success(self):
        service = CavaSociosService()
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = ("SOCIO-123",)

        with patch.object(service, "_get_connection", return_value=mock_conn):
            data = {
                "nombre_completo": "Carlos Ruiz",
                "numero_socio": "SOC-100",
                "email": "carlos@example.com",
                "telefono": "5559876543",
                "tipo_membresia": "PREMIUM",
                "maximo_botellas": 24,
                "fecha_vencimiento": "2027-12-31",
                "observaciones": "Cliente VIP",
                "estatus": "ACTIVO",
            }
            res = service.actualizar_socio("SOCIO-123", "EMP-99", data, "USER-77")

            assert res["socio_id"] == "SOCIO-123"
            assert res["mensaje"] == "Socio actualizado exitosamente"
            mock_cursor.execute.assert_called()
            mock_conn.commit.assert_called_once()

    @pytest.mark.unit
    def test_actualizar_socio_not_found(self):
        service = CavaSociosService()
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = None  # Socio no existe

        with patch.object(service, "_get_connection", return_value=mock_conn):
            data = {"nombre_completo": "Inexistente"}
            with pytest.raises(ValueError) as exc_info:
                service.actualizar_socio("INVALID-ID", "EMP-99", data, "USER-77")
            assert "Socio no encontrado" in str(exc_info.value)
            mock_conn.rollback.assert_called_once()


class TestCavaSociosRouterRegistration:
    """Prueba que el router esté correctamente montado en FastAPI"""

    @pytest.mark.unit
    def test_routes_registered_in_app(self):
        from server import app

        paths = [route.path for route in app.routes if hasattr(route, "path")]
        assert "/api/cava-socios/dashboard" in paths
        assert "/api/cava-socios/socios" in paths
        assert "/api/cava-socios/socios/{socio_id}" in paths
        assert "/api/cava-socios/socios/{socio_id}/botellas" in paths
        assert "/api/cava-socios/botellas/{botella_id}/consumo" in paths
