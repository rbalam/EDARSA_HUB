from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SERVICE = ROOT / "modules/ia_assistant/service.py"
FRONT = ROOT.parent / "frontend/src/components/ia/IAContextual.jsx"
RENDERER = ROOT.parent / "frontend/src/components/ia/visualization/IAVisualizationRenderer.jsx"


def test_backend_normalizes_inline_markdown_table_rows():
    source = SERVICE.read_text(encoding="utf-8")
    assert 're.sub(r"\\|\\s*\\|", "|\\n|", cleaned)' in source


def test_frontend_builds_comparison_dataset_from_answer_table():
    source = FRONT.read_text(encoding="utf-8")
    assert "buildPresentationDatasets" in source
    assert "answer_comparison_" in source
    assert "presentation_kind: 'comparison'" in source
    assert "periodColumns.length < 2" in source


def test_explicit_visual_request_overrides_partial_backend_open_view():
    source = FRONT.read_text(encoding="utf-8")
    assert "actions = actions.filter((action) => action?.type !== 'OPEN_VIEW')" in source
    assert "actions.unshift(localVisualAction)" in source


def test_real_chart_renderer_and_number_formatting_are_used():
    source = RENDERER.read_text(encoding="utf-8")
    assert "ResponsiveContainer" in source
    assert "<BarChart" in source
    assert "<LineChart" in source
    assert "formatDisplayValue" in source
