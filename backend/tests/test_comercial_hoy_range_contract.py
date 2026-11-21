from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ROUTES = ROOT / "modules/comercial/routes.py"


def test_periodo_dia_precedes_month_selectors():
    text = ROUTES.read_text(encoding="utf-8")
    assert 'if periodo == "mes" and meses and lista_anios:' in text
    assert 'elif periodo == "dia":' in text

    month_idx = text.index('if periodo == "mes" and meses and lista_anios:')
    day_idx = text.index('elif periodo == "dia":', month_idx)
    assert month_idx < day_idx

    block = text[month_idx:day_idx]
    assert 'fecha_ini = f"{year}-{str(mes_min).zfill(2)}-01"' in block


def test_hoy_has_single_day_range():
    text = ROUTES.read_text(encoding="utf-8")
    day_idx = text.index('elif periodo == "dia":')
    week_idx = text.index('elif periodo == "semana":', day_idx)
    block = text[day_idx:week_idx]
    assert "fecha_ini = hoy.strftime('%Y-%m-%d')" in block
    assert "fecha_fin = hoy.strftime('%Y-%m-%d')" in block
