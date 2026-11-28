from pathlib import Path

from modules.ia_assistant.contextual import normalize_view_context, validate_actions

ROOT = Path(__file__).resolve().parents[1]
ROUTES = ROOT / "modules/ia_assistant/routes.py"
SERVICE = ROOT / "modules/ia_assistant/service.py"
QUERY_BRIDGE = ROOT / "modules/ia_assistant/query_bridge.py"
FRONT = ROOT.parent / "frontend/src/components/comercial/analytics/CanonicalTicketDrilldown.jsx"
COMERCIAL_PAGE = ROOT.parent / "frontend/src/pages/Comercial.js"
CONTEXTUAL_FRONT = ROOT.parent / "frontend/src/components/ia/IAContextual.jsx"
API = ROOT.parent / "frontend/src/services/iaAssistantApi.js"
GENERAL = ROOT.parent / "frontend/src/pages/IAAsistente.jsx"


def test_context_normalization_is_whitelist_and_drops_secrets():
    result = normalize_view_context({
        "modulo": "comercial",
        "view_id": "canonical_ticket_drilldown",
        "scope": {"unidad": "X", "token": "NO"},
        "password": "NO",
    })
    assert result["modulo"] == "comercial"
    assert "password" not in result
    assert "token" not in result["scope"]


def test_ui_actions_are_fail_closed():
    context = {"columnas_visibles": [{"key": "ventas"}, {"key": "fecha"}]}
    actions = validate_actions({
        "actions": [
            {"type": "APPLY_FILTERS", "payload": {"filters": {"ventas_min": 5000, "sql": "DROP"}}},
            {"type": "OPEN_VIEW", "payload": {"view_type": "bar_chart", "dataset": "tickets", "x_key": "fecha", "y_key": "ventas"}},
            {"type": "RUN_JAVASCRIPT", "payload": {"code": "alert(1)"}},
        ]
    }, context)
    assert len(actions) == 2
    assert actions[0]["payload"]["filters"] == {"ventas_min": 5000.0}
    assert actions[1]["payload"]["x_key"] == "fecha"
    assert actions[1]["payload"]["y_key"] == "ventas"


def test_existing_chat_contract_is_extended_not_replaced():
    routes = ROUTES.read_text(encoding="utf-8")
    service = SERVICE.read_text(encoding="utf-8")
    assert '@router.post("/chat")' in routes
    assert 'contexto_vista' in routes
    assert "require_explicit_permission_dual" in routes
    assert "IA_ASSISTANT_VER" in routes
    assert "plan_system_queries" in routes
    assert "execute_planned_queries" in routes
    assert "view_context" in service


def test_query_bridge_remains_get_only_and_no_generated_sql():
    bridge = QUERY_BRIDGE.read_text(encoding="utf-8")
    assert 'raw_path_item.get("get")' in bridge
    assert "client.get(" in bridge
    assert "client.post(" not in bridge


def test_frontend_reuses_existing_assistant_client_and_has_no_worker_key():
    front = CONTEXTUAL_FRONT.read_text(encoding="utf-8")
    api = API.read_text(encoding="utf-8")
    drill = FRONT.read_text(encoding="utf-8")
    comercial = COMERCIAL_PAGE.read_text(encoding="utf-8")
    general = GENERAL.read_text(encoding="utf-8")
    assert "iaAssistantApi" in front
    assert "IAContextualLauncher" in drill
    assert "IAContextualLauncher" in comercial
    assert "view_id: 'comercial_detalle_ventas'" in comercial
    assert "Selecciona un folio para abrir el ticket de venta." in comercial
    assert "contexto_vista" in api
    assert "EDARSA_AI_API_KEY" not in front
    assert "EDARSA_AI_API_KEY" not in api
    assert "IAAsistente" in general
