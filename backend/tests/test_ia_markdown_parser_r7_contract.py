from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SERVICE = ROOT / "modules/ia_assistant/service.py"
FRONT = ROOT.parent / "frontend/src/components/ia/IAContextual.jsx"


def test_backend_uses_real_regex_tokens_not_literal_backslashes():
    source = SERVICE.read_text(encoding="utf-8")
    assert 'r"\\|\\s*\\|"' in source
    assert 'r"\\n{3,}"' in source
    assert 'r"\\\\|\\\\s*\\\\|"' not in source


def test_frontend_splits_real_newlines_and_parses_real_pipes():
    source = FRONT.read_text(encoding="utf-8")
    assert ".split('\\n')" in source
    assert ".replace(/^\\|/, '')" in source
    assert ".replace(/\\|$/, '')" in source
    assert "cell.replace(/\\s/g, '')" in source
    assert ".split('\\\\n')" not in source


def test_frontend_regexes_are_not_double_escaped():
    source = FRONT.read_text(encoding="utf-8")
    assert ".replace(/\\|\\s*\\|/g, '|\\n|')" in source
    assert "replace(/[$,%\\s,]/g, '')" in source
    assert "replace(/[\\u0300-\\u036f]/g, '')" in source


def test_assistant_table_uses_full_panel_width():
    source = FRONT.read_text(encoding="utf-8")
    assert "block w-full max-w-full" in source
    assert "max-w-full overflow-x-auto" in source
