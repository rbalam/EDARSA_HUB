from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SQL = ROOT / 'docs/sql/FN_CALCULAR_PROYECCION_MENSUAL.sql'

def test_invalid_year_is_not_replaced_with_current_year():
    src = SQL.read_text(encoding='utf-8')
    assert 'SET @Anio = YEAR(GETDATE())' not in src
    assert 'IF @Anio IS NULL OR @Anio < 1900 OR @Anio > 2100' in src
    year_guard = src[src.index('IF @Anio IS NULL OR @Anio < 1900 OR @Anio > 2100'):src.index('-- Obtener la cantidad de días del mes')]
    assert 'RETURN NULL' in year_guard

def test_month_and_year_invalid_periods_fail_closed():
    src = SQL.read_text(encoding='utf-8')
    assert 'IF @NumeroMes IS NULL' in src
    assert src.count('RETURN NULL') >= 2
