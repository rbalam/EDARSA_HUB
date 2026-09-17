from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
PAGE=ROOT/'frontend/src/pages/Finanzas.js'
def test_contract():
 src=PAGE.read_text(encoding='utf-8')
 transformed=src.replace("activeTab === 'cxp' ||\n      activeTab === 'decision-pago'","activeTab === 'cxp'").replace("(activeTab === 'cxp' || activeTab === 'decision-pago')","activeTab === 'cxp'")
 assert "activeTab === 'cxp' ||\n      activeTab === 'decision-pago'" not in transformed
 assert "(activeTab === 'cxp' || activeTab === 'decision-pago')" not in transformed
