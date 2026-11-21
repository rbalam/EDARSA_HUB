"""Offline tests for the closed MPRO legacy batch capability; never contacts SQL."""
from __future__ import annotations
import base64
import io
import json
from pathlib import Path
import sys
from zipfile import ZipFile

import pytest
from cryptography.fernet import Fernet

SCRIPTS = Path(__file__).resolve().parents[1] / 'scripts'
sys.path.insert(0, str(SCRIPTS))
import mpro_inventarios_ctrl1_batch as batch


def _encrypted_minimal(monkeypatch, tmp_path):
    monkeypatch.setenv('SERVER_SECRET_KEY', Fernet.generate_key().decode())
    monkeypatch.setattr(batch, 'SCOPE', (('130QRO', '2026-03'),))
    body = {
        'schema': batch.ARCHIVE_SCHEMA,
        'created_at_utc': '2026-10-27T00:00:00Z',
        'scope': [{'unidad': '130QRO', 'mes': '2026-03'}],
        'months': [{'unidad':'130QRO', 'mes':'2026-03', 'status':'NO_CHANGES', 'changes':0}],
        'total_changes': 0,
    }
    body['digest_sha256'] = batch.manifest_digest(body)
    with io.BytesIO() as buf:
        with ZipFile(buf, 'w') as z:
            z.writestr('manifest.json', json.dumps(body).encode())
        encrypted = Fernet(batch.recovery_key()).encrypt(buf.getvalue())
    target = tmp_path / batch.ARCHIVE_FILENAME
    target.write_bytes(encrypted)
    return target


def test_scope_excludes_mixed_periods_and_no_data_periods():
    assert len(batch.SCOPE) == 12
    assert ('130QRO', '2026-09') not in batch.SCOPE
    assert ('130QRO', '2026-10') not in batch.SCOPE
    assert ('ORIGEN', '2026-01') not in batch.SCOPE
    assert ('ORIGEN', '2026-08') in batch.SCOPE
    assert ('130QRO', '2026-03') in batch.SCOPE
    with pytest.raises(RuntimeError, match='SCOPE_NOT_ALLOWED'):
        batch.filename_for('130QRO', '2026-09')


def test_recovery_subkey_is_not_server_secret(monkeypatch):
    master = Fernet.generate_key().decode()
    monkeypatch.setenv('SERVER_SECRET_KEY', master)
    child = batch.recovery_key().decode()
    assert child != master
    assert len(base64.urlsafe_b64decode(child)) == 32


def test_encrypted_artifact_verifies_and_tamper_fails(monkeypatch, tmp_path):
    file = _encrypted_minimal(monkeypatch, tmp_path)
    manifest, snapshots = batch.decrypt_and_verify(file)
    assert manifest['total_changes'] == 0 and snapshots == {}
    b = bytearray(file.read_bytes())
    b[len(b) // 2] ^= 1
    file.write_bytes(b)
    with pytest.raises(Exception):
        batch.decrypt_and_verify(file)


def test_apply_fail_closed_without_github_context(monkeypatch, tmp_path):
    file = _encrypted_minimal(monkeypatch, tmp_path)
    monkeypatch.delenv('GITHUB_ACTIONS', raising=False)
    with pytest.raises(RuntimeError, match='APPLY_SOLO_DESDE_GITHUB_ACTIONS'):
        batch.apply(file)


def test_legacy_never_updates_mixed_months_and_requires_snapshot():
    legacy_source = (SCRIPTS / 'resync_mpro_inventarios_legacy_safe.py').read_text()
    assert 'MES_MEZCLADO_LEGACY_CANONICO_BLOQUEADO' in legacy_source
    assert 'GUARDIA_FORMATO: LEGACY_EXCLUSIVO' in legacy_source
    assert '_assert_same_changes(snapshot, locked_changes)' in legacy_source
    assert 'VERIFICACION_SQL_INDEPENDIENTE' in legacy_source
    assert 'Mv_Cantidad_Control_1' in legacy_source
    assert 'WHERE m.EmpresaID=%s AND m.SucursalID=%s' in legacy_source
    assert 'INSERT INTO dbo.Inventario_MovimientosDetalle' not in legacy_source
    assert 'DELETE FROM dbo.Inventario_MovimientosDetalle' not in legacy_source
