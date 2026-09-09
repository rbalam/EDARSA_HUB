from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path

from core.bos_direction_status_cycle import run_direction_status_cycle


def resolve_bos_direction_paths() -> tuple[Path, Path]:
    root_raw = str(os.environ.get('EDARSAHUB_ROOT') or '').strip()
    if not root_raw:
        raise RuntimeError('EDARSAHUB_ROOT_REQUIRED')
    root = Path(root_raw)
    results_raw = str(os.environ.get('BOS_DIRECTION_RESULTS_DIR') or '').strip()
    status_raw = str(os.environ.get('BOS_DIRECTION_STATUS_ROOT') or '').strip()
    results_dir = Path(results_raw) if results_raw else root / '.git' / 'universal-worker-queue' / 'results'
    status_root = Path(status_raw) if status_raw else root / '.git' / 'bos-direction-status'
    return results_dir, status_root


def execute_bos_direction_status(generated_at_utc: str | None = None) -> dict[str, object]:
    results_dir, status_root = resolve_bos_direction_paths()
    timestamp = generated_at_utc or datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    return run_direction_status_cycle(
        results_dir=results_dir,
        status_root=status_root,
        generated_at_utc=timestamp,
    )
