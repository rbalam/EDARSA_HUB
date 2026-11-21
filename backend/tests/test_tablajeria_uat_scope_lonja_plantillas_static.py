from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

def read(path: str) -> str:
    return (ROOT / path).read_text(encoding='utf-8')

def test_uat_scope_fix_contract_files_exist():
    sql = read('backend/modules/tablajeria/sql/uatscope_lonja_plantillas.sql')
    doc = read('docs/TABLAJERIA_UAT_SCOPE_FIX_LONJA_PLANTILLAS_IMPLEMENTATION_R1.md')
    for token in ['Tablajeria_LonjasDisponibles', 'SkuKgCodigo', 'SkuPiezaCodigo', 'GramajePorPiezaGramos', 'CostoFijo', 'ProrrateaCosto']:
        assert token in sql
    for token in ['lonjas individualmente', 'doble control kg/pz', 'plantillas', 'Produccion: NO tocada']:
        assert token in doc
