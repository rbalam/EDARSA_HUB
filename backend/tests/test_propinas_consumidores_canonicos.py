from pathlib import Path
import ast


ROOT = Path(__file__).resolve().parents[2]

COMERCIAL = ROOT / (
    "backend/modules/comercial_v2/routes.py"
)

EJECUTIVO = ROOT / (
    "backend/modules/dashboard_ejecutivo/routes.py"
)

TABLERO = ROOT / (
    "frontend/src/pages/TableroEjecutivo.js"
)

KPI_SERVICE = ROOT / (
    "backend/core/kpis_canonicos/service.py"
)


def test_comercial_v2_separa_propinas_del_dia_del_acumulado():
    text = COMERCIAL.read_text(encoding="utf-8")

    ast.parse(text)

    assert "excluir_dia_operativo_actual=True" in text
    assert "'_dia_actual_separado'" in text
    assert "u['propinas_total'] = propinas_dia" not in text
    assert "totales['propinas_total'] =" not in text

def test_comercial_v2_publica_detalle_completo_de_propinas():
    text = COMERCIAL.read_text(encoding="utf-8")

    for marker in (
        '"propinas_abiertas": '
        "float(v.get('propinas_abiertas') or 0)",
        '"propinas_cerradas_dia": '
        "float(v.get('propinas_cerradas_dia') or 0)",
        '"propinas_total": '
        "float(v.get('propinas_total') or 0)",
        '"tickets_cerrados_dia":',
        '"pax_cerrados_dia":',
    ):
        assert marker in text


def test_dashboard_ejecutivo_conserva_propinas_y_dia_separado():
    text = EJECUTIVO.read_text(encoding="utf-8")

    ast.parse(text)

    assert "resumen_periodo_desglosado" in text
    assert '"ventas_dia_actual"' in text
    assert '"propinas_total"' in text
    assert '"CERRADO_SIN_DIA_OPERATIVO_ACTUAL"' in text

def test_tablero_ejecutivo_no_descarta_propinas():
    text = TABLERO.read_text(encoding="utf-8")

    assert (
        "propinas: u.propinas_total || 0"
        in text
    )

    assert (
        "propinas_total: u.propinas_total || 0"
        in text
    )

    assert (
        "propinas: totales.propinas_total || 0"
        in text
    )

    assert (
        "propinas_total: totales.propinas_total || 0"
        in text
    )


def test_raiz_canonica_contiene_propinas_separadas():
    text = KPI_SERVICE.read_text(encoding="utf-8")

    ast.parse(text)

    assert (
        "SUM(CAST(propinas_total AS float))"
        in text
    )

    assert (
        '"propinas": propinas'
        in text
    )

    assert (
        '"source_table": '
        '"dbo.vw_Comercial_KPIs_Diarios_v2_Runtime"'
        in text
    )
