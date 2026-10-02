from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def read(p): return (ROOT/p).read_text(encoding='utf-8')
def test_gate6_contract():
 repo=read('backend/modules/catalogo_ampliado/repository.py'); e2e=read('backend/tests/test_catalogo_ampliado_gate6_e2e_real.py'); wf=read('.github/workflows/catalogo-ampliado-gate6-e2e.yml')
 assert '?' not in repo and '%s' in repo
 assert 'NIVEL_ACCESO_TOTAL' in e2e and 'cleanup' in e2e and 'residue' in e2e
 for x in ('/personas','/vinculos','/documentos','/versiones','/kardex','/vencimientos','/alertas/reglas'): assert x in e2e
 assert 'environment: development' in wf and 'Edarsahub_Produccion' not in wf and 'production_touched=false' in wf
