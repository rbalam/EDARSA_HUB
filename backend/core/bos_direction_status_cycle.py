from __future__ import annotations

import json
import os
import re
import tempfile
from pathlib import Path

from core.bos_direction_snapshot_publisher import (
    render_direction_snapshot,
    serialize_direction_snapshot,
)

_TIMESTAMP_RE = re.compile(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$')


def _history_filename(generated_at_utc: str) -> str:
    if not isinstance(generated_at_utc, str) or not _TIMESTAMP_RE.fullmatch(generated_at_utc):
        raise ValueError('generated_at_utc must use YYYY-MM-DDTHH:MM:SSZ')
    return generated_at_utc.replace('-', '').replace(':', '') + '.json'


def _atomic_replace(path: Path, payload: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary_name = tempfile.mkstemp(prefix=f'.{path.name}.', suffix='.tmp', dir=str(path.parent), text=True)
    temporary_path = Path(temporary_name)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_path, path)
    except BaseException:
        temporary_path.unlink(missing_ok=True)
        raise


def _write_history_once(path: Path, payload: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    except FileExistsError:
        existing = path.read_text(encoding='utf-8')
        if existing != payload:
            raise RuntimeError(f'HISTORY_COLLISION:{path.name}')
        return
    with os.fdopen(fd, 'w', encoding='utf-8') as handle:
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())


def run_direction_status_cycle(results_dir: str | Path, status_root: str | Path, generated_at_utc: str) -> dict[str, object]:
    root = Path(status_root)
    snapshot = render_direction_snapshot(results_dir, generated_at_utc)
    payload = serialize_direction_snapshot(snapshot)
    history_path = root / 'history' / _history_filename(generated_at_utc)
    latest_path = root / 'latest.json'
    _write_history_once(history_path, payload)
    _atomic_replace(latest_path, payload)
    return {'snapshot': snapshot, 'history_file': str(history_path), 'latest_file': str(latest_path)}
