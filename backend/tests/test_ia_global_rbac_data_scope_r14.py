from pathlib import Path

import pytest

from modules.comercial_analytics.repository_tickets import list_discounts
from modules.ia_assistant import query_bridge

ROOT = Path(__file__).resolve().parents[1]
ROUTES = ROOT / "modules/comercial_analytics/routes.py"
SERVICE = ROOT / "modules/ia_assistant/service.py"


def test_catalog_prioritizes_user_intent_over_current_view():
    catalog = [
        {
            "operation_id": "ventas_actuales",
            "path": "/api/comercial/ventas",
            "summary": "Ventas del periodo",
            "tags": ["Comercial"],
            "parameters": [],
        },
        {
            "operation_id": "commercial_discounts",
            "path": "/api/comercial/analytics/descuentos",
            "summary": "Descuentos aplicados en ventas por ticket y producto",
            "tags": ["Commercial Analytics"],
            "parameters": [],
        },
    ]
    ranked = query_bridge.catalog_for_prompt(
        catalog,
        "dame el detalle de los descuentos aplicados",
        context_text="vista ventas detalle ventas ticket comercial",
        limit=2,
    )
    assert ranked[0]["operation_id"] == "commercial_discounts"


def test_discount_repository_returns_edarsahub_dataset():
    calls = []

    def fake(sql, params):
        calls.append((sql, params))
        if "COUNT(*) AS total" in sql:
            return [{"total": 1}]
        if "tickets_con_descuento" in sql:
            return [{"descuento_total": 125.5, "tickets_con_descuento": 1}]
        return [{
            "unidad_negocio_id": "CF",
            "unidad": "CIENFUEGOS",
            "sucursal": "001",
            "fecha_operacion": "2026-10-08",
            "fecha_hora": "2026-10-08T13:00:00",
            "numero_ticket": "1001",
            "producto_codigo": "P1",
            "producto": "Producto",
            "familia": "Alimentos",
            "cantidad": 1,
            "precio_unitario": 1000,
            "importe_bruto": 1000,
            "importe_neto": 874.5,
            "descuento": 125.5,
            "descuento_pct": 12.55,
            "tipo_descuento_id": "DESC10",
            "tipo_descuento_descripcion": "Descuento autorizado",
            "tipo_descuento_valor": 10,
            "partida_comentario_descuento": "Autorizado",
            "ticket_comentario_descuento": None,
        }]

    result = list_discounts(
        fecha_inicio="2026-10-01",
        fecha_fin="2026-10-08",
        allowed_unit_codes=["CF"],
        unidad_negocio_id="CF",
        query_executor=fake,
    )
    assert result["resumen"]["descuento_total"] == 125.5
    assert result["items"][0]["tipo_descuento_descripcion"] == "Descuento autorizado"
    assert result["traceability"]["source_policy"] == "EDARSAHUB_ONLY"
    assert result["traceability"]["rbac"] == "UNIDADES_AUTORIZADAS"
    assert len(calls) == 3


def test_discount_repository_rejects_unit_outside_profile_scope():
    with pytest.raises(PermissionError):
        list_discounts(
            fecha_inicio="2026-10-01",
            fecha_fin="2026-10-08",
            allowed_unit_codes=["CF"],
            unidad_negocio_id="ORIGEN",
            query_executor=lambda _sql, _params: [],
        )


def test_planner_declares_view_is_not_authorization_boundary():
    source = SERVICE.read_text(encoding="utf-8")
    routes = ROUTES.read_text(encoding="utf-8")
    assert "NO limites la consulta a la tabla," in source
    assert "columnas visibles" in source
    assert "La intención explícita del mensaje tiene prioridad" in source
    assert 'No respondas "no autorizado" solo porque' in source
    assert '"/descuentos"' in routes
    assert "list_discounts" in routes
