from pathlib import Path
import ast

from core.kpis_canonicos.service import runtime_dia_operativo_actual_predicate


ROOT = Path(__file__).resolve().parents[2]
SERVICE = ROOT / "backend/core/kpis_canonicos/service.py"
REPOSITORY = ROOT / "backend/modules/comercial_v2/repository_readonly.py"
COMERCIAL = ROOT / "backend/modules/comercial_v2/routes.py"
EJECUTIVO = ROOT / "backend/modules/dashboard_ejecutivo/routes.py"
INTELIGENCIA = ROOT / "backend/modules/inteligencia_comercial/routes.py"
TABLERO = ROOT / "frontend/src/pages/TableroEjecutivo.js"
DASHBOARD_IA = ROOT / "frontend/src/portal-inteligencia/pages/DashboardIA.jsx"


def test_predicado_canonico_soporta_tres_modos():
    assert runtime_dia_operativo_actual_predicate("k", "incluir") == ""
    excluir = runtime_dia_operativo_actual_predicate("k", "excluir")
    solo = runtime_dia_operativo_actual_predicate("k", "solo")
    assert "NOT (EXISTS" in excluir
    assert "Comercial_Ventas_Dia_Abiertas_v2" in excluir
    assert solo.startswith("EXISTS")


def test_servicio_publica_desglose_unico():
    text = SERVICE.read_text(encoding="utf-8")
    ast.parse(text)
    assert "def resumen_periodo_desglosado" in text
    assert '"acumulado_cerrado"' in text
    assert '"dia_actual"' in text
    assert '"total_incluyendo_dia"' in text


def test_comercial_excluye_dia_y_lo_publica_separado():
    repository = REPOSITORY.read_text(encoding="utf-8")
    comercial = COMERCIAL.read_text(encoding="utf-8")
    ast.parse(repository)
    ast.parse(comercial)
    assert "runtime_dia_operativo_actual_predicate" in repository
    assert comercial.count("excluir_dia_operativo_actual=True") == 2
    assert '"ventas_dia_actual"' in comercial
    assert "u['ventas_total'] = total_dia" not in comercial


def test_ejecutivo_e_inteligencia_consumen_desglose_canonico():
    ejecutivo = EJECUTIVO.read_text(encoding="utf-8")
    inteligencia = INTELIGENCIA.read_text(encoding="utf-8")
    ast.parse(ejecutivo)
    ast.parse(inteligencia)
    assert "resumen_periodo_desglosado" in ejecutivo
    assert "resumen_periodo_desglosado" in inteligencia
    assert '"ventas_dia_actual"' in ejecutivo
    assert '"ventas_dia_actual"' in inteligencia


def test_frontend_identifica_acumulado_y_dia_separado():
    tablero = TABLERO.read_text(encoding="utf-8")
    inteligencia = DASHBOARD_IA.read_text(encoding="utf-8")
    assert "Acumulado Cerrado" in tablero
    assert "Operación del día" in inteligencia
    assert "Separada del acumulado cerrado" in inteligencia
