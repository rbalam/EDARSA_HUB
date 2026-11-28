from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SERVICE = ROOT / "modules/ia_assistant/service.py"
FRONT = ROOT.parent / "frontend/src/components/ia/IAContextual.jsx"
RENDERER = ROOT.parent / "frontend/src/components/ia/visualization/IAVisualizationRenderer.jsx"


def test_assistant_forbids_mermaid_and_prefers_structured_visuals():
    source = SERVICE.read_text(encoding="utf-8")
    assert "NO generes Mermaid" in source
    assert "xychart-beta" in source
    assert "_sanitize_assistant_visual_markup" in source
    assert "DEBES devolver una" in source
    assert "acción OPEN_VIEW" in source


def test_contextual_frontend_renders_tables_and_auto_opens_chart():
    source = FRONT.read_text(encoding="utf-8")
    assert "IAMessageContent" in source
    assert "isTableSeparator" in source
    assert "inferVisualAction" in source
    assert "previousDatasets" in source
    assert "autoVisual" in source
    assert "executeAction(autoVisual, datasets)" in source


def test_frontend_hides_mermaid_blocks_from_chat():
    source = FRONT.read_text(encoding="utf-8")
    assert "stripVisualCodeBlocks" in source
    assert "mermaid|xychart-beta" in source


def test_visual_renderer_is_canonical_and_extracted_from_orchestrator():
    front = FRONT.read_text(encoding="utf-8")
    renderer = RENDERER.read_text(encoding="utf-8")
    assert "IAAnalysisModal" in front
    assert "from 'recharts'" not in front
    assert "IAVisualizationRenderer" in renderer
