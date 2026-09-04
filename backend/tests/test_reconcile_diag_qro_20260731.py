import asyncio
import json
from datetime import date
from pathlib import Path
from api.admin_scheduler_resync import _get_unidad_config, _ejecutar_dry_run

def test_diag_qro_20260731():
    unidad=_get_unidad_config('130QRO')
    assert unidad
    dry=asyncio.run(_ejecutar_dry_run('130QRO', unidad, date(2026,7,31), date(2026,7,31)))
    evidence={'success':dry.get('success'),'records_processed':dry.get('records_processed'),'detalle':dry.get('detalle'),'error_message':dry.get('error_message')}
    Path('tests/reconcile_diag_qro_20260731_evidence.json').write_text(json.dumps(evidence,default=str,ensure_ascii=False,indent=2),encoding='utf-8')
    assert dry.get('success') is True, dry
