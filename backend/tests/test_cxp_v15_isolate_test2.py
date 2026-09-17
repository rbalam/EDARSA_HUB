from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
UI=ROOT/'frontend/src/components/finanzas/FinanzasDecisionPago.jsx'
def test_contract():
 src=UI.read_text(encoding='utf-8')
 assert 'limite_pago' in src
 assert 'disponible' in src
 assert 'porcentaje_utilizado' in src
