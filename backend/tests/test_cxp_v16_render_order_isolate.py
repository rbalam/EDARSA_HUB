from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def test_order():
 src=(ROOT/'frontend/src/pages/Finanzas.js').read_text(encoding='utf-8')
 start=src.index('const renderDecisionPago')
 end=src.index('const renderComprobaciones', start)
 assert end > start
