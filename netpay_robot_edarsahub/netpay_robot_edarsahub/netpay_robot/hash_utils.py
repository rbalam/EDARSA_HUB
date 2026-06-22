from __future__ import annotations

import hashlib
from pathlib import Path


def sha256_file(path: str | Path) -> str:
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def sha256_row(values: list[object]) -> str:
    normalized = '|'.join('' if v is None else str(v).strip() for v in values)
    return hashlib.sha256(normalized.encode('utf-8')).hexdigest()
