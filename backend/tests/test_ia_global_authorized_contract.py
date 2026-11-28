from __future__ import annotations

import os
from pathlib import Path

for key, value in {
    "EDARSAHUB_SQL_HOST": "localhost",
    "EDARSAHUB_SQL_DATABASE": "EDARSAHUB",
    "EDARSAHUB_SQL_USER": "test",
    "EDARSAHUB_SQL_PASSWORD": "test",
    "JWT_SECRET": "test-secret-for-ia-global",
}.items():
    os.environ.setdefault(key, value)

from modules.ia_assistant import access
from modules.ia_assistant import contextual
from modules.ia_assistant import service

ROOT = Path(__file__).resolve().parents[1]
QUERY_BRIDGE = ROOT / "modules/ia_assistant/query_bridge.py"
ROUTES = ROOT / "modules/ia_assistant/routes.py"
FRONT = ROOT.parent / "frontend/src/components/ia/IAContextual.jsx"
FRONT_DATA = ROOT.parent / "frontend/src/components/ia/iaContextualData.js"
EXPORTS = ROOT.parent / "frontend/src/portal-inteligencia/utils/exportUtils.js"


def test_access_context_is_sql_rbac_and_fail_closed(monkeypatch):
    monkeypatch.setattr(
        access.AuthRepository,
        "get_user_by_email",
        lambda _email: {
            "active": True,
            "_sql_usuario_id": 7,
            "email": "user@example.com",
        },
    )
    monkeypatch.setattr(
        access.RBACSQLService,
        "can_access_permission",
        lambda *_args: True,
    )
    monkeypatch.setattr(
        access.RBACSQLService,
        "get_effective_permissions",
        lambda *_args: ["IA_ASSISTANT_VER", "COMERCIAL_VER"],
    )
    monkeypatch.setattr(
        access.RBACSQLService,
        "build_context",
        lambda *_args: {
            "roles": [{"RolID": 1, "CodigoRol": "USUARIO"}],
            "empresas": [{"EmpresaID": 5}],
            "unidades_negocio": [{"UnidadNegocioID": "unidad-1"}],
            "sucursales": [{"ServidorID": "server-1", "SucursalCodigo": "001"}],
            "servidores": [{"ServidorID": "server-1"}],
        },
    )
    monkeypatch.setattr(
        access.RBACSQLService,
        "get_scope_assignment_state",
        lambda *_args: {
            "server_assignment_count": 1,
            "branch_assignment_count": 1,
        },
    )

    result = access.build_ai_access_context({"email": "user@example.com"})
    assert result["authorized"] is True
    assert "COMERCIAL_VER" in result["permission_codes"]
    assert result["unidades_negocio"] == [{"UnidadNegocioID": "unidad-1"}]
    assert result["source_policy"] == "EDARSAHUB_ONLY"


def test_contextual_actions_accept_backend_dataset_and_exports():
    datasets = [{
        "dataset_id": "edarsahub_ia_1",
        "columns": ["periodo", "ventas"],
        "rows": [
            {"periodo": "2026-10", "ventas": 100},
            {"periodo": "2025-10", "ventas": 90},
        ],
        "row_count": 2,
    }]
    actions = contextual.validate_actions(
        {
            "actions": [
                {
                    "type": "OPEN_VIEW",
                    "payload": {
                        "dataset_id": "edarsahub_ia_1",
                        "view_type": "bar_chart",
                        "x_key": "periodo",
                        "y_key": "ventas",
                    },
                },
                {
                    "type": "EXPORT_FILE",
                    "payload": {
                        "dataset_id": "edarsahub_ia_1",
                        "format": "xlsx",
                        "filename": "comparativo",
                    },
                },
                {
                    "type": "EXPORT_FILE",
                    "payload": {
                        "dataset_id": "missing",
                        "format": "pdf",
                    },
                },
            ]
        },
        {},
        datasets=datasets,
    )
    assert len(actions) == 2
    assert actions[0]["payload"]["dataset_id"] == "edarsahub_ia_1"
    assert actions[1]["payload"]["format"] == "xlsx"


def test_service_extracts_authorized_datasets():
    datasets = service.build_response_datasets([
        {
            "operation_id": "ventas_periodo",
            "ok": True,
            "data": {
                "rows": [
                    {"periodo": "2026-10", "ventas": 100},
                    {"periodo": "2025-10", "ventas": 90},
                ]
            },
        }
    ])
    assert datasets
    assert datasets[0]["source_operation_id"] == "ventas_periodo"
    assert datasets[0]["row_count"] == 2
    assert datasets[0]["source_policy"] == "EDARSAHUB_ONLY"


def test_planner_receives_view_and_rbac_context():
    source = (ROOT / "modules/ia_assistant/service.py").read_text(encoding="utf-8")
    routes = ROUTES.read_text(encoding="utf-8")
    assert "ALCANCE RBAC AUTORIZADO DEL USUARIO" in source
    assert "CONTEXTO DE VISTA ACTUAL" in source
    assert "view_context=view_context" in routes
    assert "access_context=access_context" in routes


def test_ia_data_source_is_edarsahub_only():
    bridge = QUERY_BRIDGE.read_text(encoding="utf-8")
    service_source = (ROOT / "modules/ia_assistant/service.py").read_text(
        encoding="utf-8"
    )
    assert "httpx.ASGITransport(app=app)" in bridge
    assert 'base_url="http://edarsahub.internal"' in bridge
    assert "web search" in service_source.lower()
    assert "source_policy" in service_source


def test_frontend_supports_popup_and_xlsx_txt_pdf():
    front = FRONT.read_text(encoding="utf-8")
    data = FRONT_DATA.read_text(encoding="utf-8")
    exports = EXPORTS.read_text(encoding="utf-8")
    assert "IAAnalysisModal" in front
    assert "EXPORT_FILE" in front
    assert "resolveActionDataset" in front
    assert "exportToExcel" in data
    assert "exportToPDF" in data
    assert "exportToTXT" in data
    assert "export function exportToTXT" in exports
    assert "EDARSA_AI_API_KEY" not in front
    assert "EDARSA_AI_API_KEY" not in data
