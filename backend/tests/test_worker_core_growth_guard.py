from __future__ import annotations

import hashlib
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.mirror_sync import universal_job_bridge as bridge
from tools.mirror_sync import universal_job_dispatcher as dispatcher


def _write(path: Path, content: str = 'old') -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding='utf-8')


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_bridge_rejects_new_file_inside_backend_core(tmp_path, monkeypatch):
    monkeypatch.setattr(bridge, 'ROOT', tmp_path)
    (tmp_path / 'backend' / 'core').mkdir(parents=True)
    errors = bridge.validate_action({'type': 'write_file','path': 'backend/core/new_feature.py','content': 'x = 1\n'}, 1)
    assert 'ACTION_1_CORE_GROWTH_FORBIDDEN' in errors


def test_bridge_allows_controlled_edit_of_existing_core_file(tmp_path, monkeypatch):
    monkeypatch.setattr(bridge, 'ROOT', tmp_path)
    target = tmp_path / 'backend' / 'core' / 'existing.py'
    _write(target)
    errors = bridge.validate_action({'type': 'write_file','path': 'backend/core/existing.py','content': 'new\n'}, 1)
    assert not any('CORE_GROWTH_FORBIDDEN' in item for item in errors)


def test_bridge_allows_new_file_outside_core(tmp_path, monkeypatch):
    monkeypatch.setattr(bridge, 'ROOT', tmp_path)
    errors = bridge.validate_action({'type': 'write_file','path': 'backend/modules/example/new_feature.py','content': 'x = 1\n'}, 1)
    assert not any('CORE_GROWTH_FORBIDDEN' in item for item in errors)


def test_dispatcher_rejects_new_file_inside_backend_core(tmp_path):
    (tmp_path / 'backend' / 'core').mkdir(parents=True)
    with pytest.raises(RuntimeError, match='CORE_GROWTH_FORBIDDEN'):
        dispatcher.apply_action(tmp_path, {'type': 'write_file','path': 'backend/core/new_feature.py','content': 'x = 1\n'})


def test_dispatcher_allows_existing_core_refactor_with_hash(tmp_path):
    target = tmp_path / 'backend' / 'core' / 'existing.py'
    _write(target, 'old\n')
    changed = dispatcher.apply_action(tmp_path, {'type': 'write_file','path': 'backend/core/existing.py','content': 'new\n','expected_sha256': _sha256(target)})
    assert changed == 'backend/core/existing.py'
    assert target.read_text(encoding='utf-8') == 'new\n'


def test_dispatcher_allows_new_file_outside_core(tmp_path):
    changed = dispatcher.apply_action(tmp_path, {'type': 'write_file','path': 'backend/modules/example/new_feature.py','content': 'x = 1\n'})
    assert changed == 'backend/modules/example/new_feature.py'
    assert (tmp_path / changed).is_file()
