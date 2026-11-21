from pathlib import Path
import importlib.util

ROOT = Path(__file__).resolve().parents[2]
SQL = ROOT / 'docs/sql/FN_CALCULAR_PROYECCION_MENSUAL.sql'
HELPER = ROOT / 'backend/scripts/fn_calcular_proyeccion_mensual.py'
UPDATER = ROOT / 'backend/scripts/update_proyeccion_con_funcion.py'

def test_sql_has_no_fixed_may_fallback():
    src = SQL.read_text(encoding='utf-8')
    assert 'ELSE 5 -- fallback al mes de Mayo' not in src
    assert 'ELSE NULL' in src
    assert 'IF @NumeroMes IS NULL' in src
    assert 'RETURN NULL' in src

def test_python_helper_rejects_invalid_month_instead_of_may():
    spec = importlib.util.spec_from_file_location('proj', HELPER)
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(mod)
    assert mod.py_calcular_proyeccion_mensual(100, 10, 'mes-invalido', 2026) is None

def test_mass_updater_does_not_invent_may_days():
    src = UPDATER.read_text(encoding='utf-8')
    assert "Mes = 'Mayo'" not in src
    assert 'DATEFROMPARTS(Anio, 5, 1)' not in src
    assert 'Dias_Con_Ventas,' in src
