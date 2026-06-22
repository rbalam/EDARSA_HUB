from __future__ import annotations

from pathlib import Path
from .layouts import detect_layout
from .importer import parse_netpay_workbook
from .hash_utils import sha256_file


class ManualNetPayImportService:
    """Servicio para carga manual Excel/copy-paste.

    Este servicio se conecta al mismo pipeline de staging que el robot.
    """

    def import_excel(self, path: str | Path) -> dict:
        digest = sha256_file(path)
        layout = detect_layout(path)
        if not layout.ok:
            return {'ok': False, 'sha256': digest, 'errors': layout.errors}
        parsed = parse_netpay_workbook(path)
        return {
            'ok': True,
            'sha256': digest,
            'report_kind': layout.report_kind,
            'sheets': [
                {'sheet': p.sheet_name, 'rows': len(p.rows), 'totals': {k: str(v) for k, v in p.totals.items()}}
                for p in parsed
            ],
        }
