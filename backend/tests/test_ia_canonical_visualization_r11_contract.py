from pathlib import Path

from modules.ia_assistant import contextual

ROOT = Path(__file__).resolve().parents[1]
FRONT = ROOT.parent / "frontend/src/components/ia/IAContextual.jsx"
RENDERER = ROOT.parent / "frontend/src/components/ia/visualization/IAVisualizationRenderer.jsx"
PALETTE = ROOT.parent / "frontend/src/components/ia/visualization/chartPalette.js"
CONTRACT = ROOT.parent / "frontend/src/components/ia/visualization/visualizationContract.js"


def test_palette_has_exactly_ten_colors_and_cycles():
    source = PALETTE.read_text(encoding="utf-8")
    colors = [token for token in source.split("'") if token.startswith("#") and len(token) == 7]
    assert len(colors) == 10
    assert "% IA_CHART_PALETTE.length" in source


def test_renderer_is_canonical_and_transversal():
    front = FRONT.read_text(encoding="utf-8")
    renderer = RENDERER.read_text(encoding="utf-8")
    assert "IAAnalysisModal" in front
    assert "from 'recharts'" not in front
    assert "IAVisualizationRenderer" in renderer
    assert "<Cell" in renderer
    assert "<Legend" in renderer
    assert "iaChartColor(index)" in renderer
    assert "series.map" in renderer
    assert "comercial" not in renderer.lower()
    assert "inventario" not in renderer.lower()


def test_open_view_accepts_authorized_series_and_keeps_y_key_compatibility():
    assert contextual.MAX_CHART_SERIES == 10
    actions = contextual.validate_actions(
        {"actions": [{"type": "OPEN_VIEW", "payload": {
            "dataset_id": "d1",
            "view_type": "bar_chart",
            "x_key": "periodo",
            "series": [
                {"key": "ventas", "label": "Ventas"},
                {"key": "pax", "label": "PAX"},
            ],
        }}]},
        {},
        datasets=[{
            "dataset_id": "d1",
            "columns": ["periodo", "ventas", "pax"],
            "rows": [],
            "row_count": 0,
        }],
    )
    assert actions[0]["payload"]["series"] == [
        {"key": "ventas", "label": "Ventas"},
        {"key": "pax", "label": "PAX"},
    ]
    assert actions[0]["payload"]["y_key"] == "ventas"


def test_frontend_visual_contract_is_generic():
    source = CONTRACT.read_text(encoding="utf-8")
    assert "table" in source
    assert "bar_chart" in source
    assert "line_chart" in source
    assert "kpi_cards" in source
    assert "MAX_IA_CHART_SERIES = 10" in source
