from __future__ import annotations

import ast
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASELINE_SHA = 'de53545b2f1db2591dc43387828e3db7c0b7a7d6'
ROUTES_REL = 'backend/modules/inteligencia_comercial/iscam_routes.py'
FRONT_REL = 'frontend/src/portal-inteligencia/pages/ReportesISCAMPage.jsx'


def _current(rel: str) -> str:
    return (ROOT / rel).read_text(encoding='utf-8')


def _baseline(rel: str) -> str:
    result = subprocess.run(
        ['git', 'show', f'{BASELINE_SHA}:{rel}'],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    return result.stdout


def _python_function(text: str, name: str) -> str:
    tree = ast.parse(text)
    lines = text.splitlines(keepends=True)
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name:
            return ''.join(lines[node.lineno - 1:node.end_lineno])
    raise AssertionError(f'Funcion no encontrada: {name}')


def _between(text: str, start: str, end: str) -> str:
    assert start in text, f'Marcador inicial no encontrado: {start}'
    assert end in text, f'Marcador final no encontrado: {end}'
    return text.split(start, 1)[1].split(end, 1)[0]


def test_backend_cuentas_y_comandas_permanecen_iguales_al_baseline_r49():
    current = _current(ROUTES_REL)
    baseline = _baseline(ROUTES_REL)
    for name in ('resumen_cuentas', 'cuenta_detalle', 'comandas_venta'):
        assert _python_function(current, name) == _python_function(baseline, name), (
            f'LOCK_R50: {name} cambio respecto al baseline certificado R49. '
            'Las correcciones de otros reportes ISCAM no pueden modificar esta funcion.'
        )


def test_frontend_descriptores_cuentas_y_comandas_permanecen_iguales():
    current = _current(FRONT_REL)
    baseline = _baseline(FRONT_REL)
    current_cuentas = _between(current, "if (sub === 'cuentas') {", "if (sub === 'comandas') {")
    baseline_cuentas = _between(baseline, "if (sub === 'cuentas') {", "if (sub === 'comandas') {")
    current_comandas = _between(current, "if (sub === 'comandas') {", "if (sub === 'pagos-ticket') {")
    baseline_comandas = _between(baseline, "if (sub === 'comandas') {", "if (sub === 'pagos-ticket') {")
    assert current_cuentas == baseline_cuentas, 'LOCK_R50: descriptor frontend de Cuentas fue modificado'
    assert current_comandas == baseline_comandas, 'LOCK_R50: descriptor frontend de Comandas fue modificado'


def test_frontend_tablas_cuentas_y_comandas_permanecen_iguales():
    current = _current(FRONT_REL)
    baseline = _baseline(FRONT_REL)
    current_cuentas = _between(current, 'function TablaCuentas', 'function TablaComandas')
    baseline_cuentas = _between(baseline, 'function TablaCuentas', 'function TablaComandas')
    current_comandas = _between(current, 'function TablaComandas', 'function TablaFormas')
    baseline_comandas = _between(baseline, 'function TablaComandas', 'function TablaFormas')
    assert current_cuentas == baseline_cuentas, 'LOCK_R50: TablaCuentas fue modificada'
    assert current_comandas == baseline_comandas, 'LOCK_R50: TablaComandas fue modificada'


def test_frontend_drill_de_cuenta_permanece_igual():
    current = _current(FRONT_REL)
    baseline = _baseline(FRONT_REL)
    current_drill = _between(current, 'const drillCuenta = async', 'const drillTiposServicio = async')
    baseline_drill = _between(baseline, 'const drillCuenta = async', 'const drillTiposServicio = async')
    assert current_drill == baseline_drill, 'LOCK_R50: drillCuenta fue modificado'
