from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ISCAM = ROOT / 'backend/modules/inteligencia_comercial/iscam_routes.py'


def _comandas_block():
    text = ISCAM.read_text(encoding='utf-8')
    start = text.index('@iscam_router.get("/comandas")')
    end = text.index('# ============================================================================\n# 4)', start)
    return text[start:end]


def test_comandas_none_uses_safe_iso_serialization():
    block = _comandas_block()
    assert '"fecha": _iso(r["fecha"])' in block
    assert 'r["fecha"].isoformat() if r["fecha"] else None' not in block


def test_comandas_keeps_canonical_executive_detail_source():
    block = _comandas_block()
    assert 'dbo.Comercial_Inteligencia_VentasDetalleProducto' in block
    assert 'fecha_operacion >= %s AND fecha_operacion < %s' in block
    assert 'ISNULL(activo,1)=1' in block
    assert 'ISNULL(es_kpi_valido,1)=1' in block
    assert 'Sync_Sales' not in block
    assert 'OPENJSON' not in block
