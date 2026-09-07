from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

from core.bos_evidence_collector import build_direction_snapshot


def _to_json_native(value: object) -> object:
    return json.loads(json.dumps(value, ensure_ascii=False))


def render_direction_snapshot(results_dir: str | Path, generated_at_utc: str) -> dict[str, object]:
    if not generated_at_utc or not isinstance(generated_at_utc, str):
        raise ValueError('generated_at_utc is required')
    snapshot = build_direction_snapshot(results_dir)
    snapshot['generated_at_utc'] = generated_at_utc
    normalized = _to_json_native(snapshot)
    if not isinstance(normalized, dict):
        raise TypeError('direction snapshot must serialize to a JSON object')
    return normalized


def serialize_direction_snapshot(snapshot: dict[str, object]) -> str:
    return json.dumps(snapshot, ensure_ascii=False, sort_keys=True, indent=2) + '\n'


def publish_direction_snapshot(
    results_dir: str | Path,
    output_file: str | Path,
    generated_at_utc: str,
) -> dict[str, object]:
    snapshot = render_direction_snapshot(results_dir, generated_at_utc)
    destination = Path(output_file)
    destination.parent.mkdir(parents=True, exist_ok=True)
    payload = serialize_direction_snapshot(snapshot)

    fd, temporary_name = tempfile.mkstemp(
        prefix=f'.{destination.name}.',
        suffix='.tmp',
        dir=str(destination.parent),
        text=True,
    )
    temporary_path = Path(temporary_name)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_path, destination)
    except BaseException:
        try:
            temporary_path.unlink(missing_ok=True)
        finally:
            raise

    return snapshot
