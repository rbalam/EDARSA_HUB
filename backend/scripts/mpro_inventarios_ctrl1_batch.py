#!/usr/bin/env python3
"""MPRO inventory legacy 2026: encrypted offsite backup before scoped SQL updates.

Closed, one-off correction of existing MOVIMIENTO_POS details only.
No INSERT, DELETE, source-side DML, or modifications to permanent schedulers.
Mixed legacy/canonical months 130QRO 2026-09/10 are always excluded.
This script is designed for two sequential GitHub Actions jobs:
  (1) prepare: read-only audit + encrypt an immutable before-image artifact
  (2) apply: authenticate downloaded artifact + use existing guarded writer.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import io
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from zipfile import ZipFile, ZIP_DEFLATED

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes

import resync_mpro_inventarios_legacy_safe as legacy

SCOPE = tuple([('130QRO', f'2026-{m:02d}') for m in range(3, 9)] +
              [('ORIGEN', f'2026-{m:02d}') for m in range(5, 11)])
ARCHIVE_SCHEMA = 'edarsahub.mpro.inventory.ctrl1.encrypted-beforeimages.2026.v1'
ARCHIVE_FILENAME = 'mpro_inventory_ctrl1_2026_beforeimages.fernet'
MAX_SNAPSHOTS = 12
MAX_ARCHIVE_SIZE = 12_000_000
HKDF_INFO = b'edarsahub:mpro-inventory:2026:beforeimage:fernet:v1'


def recovery_key() -> bytes:
    """Domain-separated subkey, never print the master or derived secret."""
    master = os.environ.get('SERVER_SECRET_KEY', '')
    if not master:
        raise RuntimeError('SERVER_SECRET_KEY_MISSING')
    try:
        raw = base64.urlsafe_b64decode(master)
    except Exception as exc:
        raise RuntimeError('SERVER_SECRET_KEY_FORMAT_INVALID') from exc
    if len(raw) != 32:
        raise RuntimeError('SERVER_SECRET_KEY_LENGTH_INVALID')
    subkey = HKDF(algorithm=hashes.SHA256(), length=32,
                  salt=b'EDARSAHUB-MPRO-CTRL1-2026-RECOVERY',
                  info=HKDF_INFO).derive(raw)
    return base64.urlsafe_b64encode(subkey)


def manifest_digest(data: dict) -> str:
    encoded = json.dumps(data, sort_keys=True, separators=(',', ':'),
                         ensure_ascii=False).encode('utf-8')
    return hashlib.sha256(encoded).hexdigest()


def filename_for(unit: str, month: str) -> str:
    if (unit, month) not in SCOPE:
        raise RuntimeError('SCOPE_NOT_ALLOWED')
    return f'{unit}_{month.replace("-", "")}_ANTES.json'


def _json_bytes(value) -> bytes:
    return (json.dumps(value, sort_keys=True, ensure_ascii=False,
                       indent=2) + '\n').encode('utf-8')


def _load_month(unit, month, pymssql):
    legacy.establecer_alcance(unit, month)
    legacy.load_configuration()
    reader = legacy.sql_connect(pymssql)
    try:
        legacy.identity(reader)
        source, products, warehouses, concepts = legacy.get_configuration(reader)
        count_legacy = legacy.assert_legacy_exclusive_month(reader)
        if count_legacy <= 0:
            raise RuntimeError(f'NO_LEGACY_HEADERS:{unit}:{month}')
        pos = legacy.read_pos(pymssql, source)
        if not pos:
            raise RuntimeError(f'SOURCE_EMPTY:{unit}:{month}')
        grouped, pending = legacy.source_groups(pos, products, warehouses, concepts)
        changes, missing, unchanged = legacy.compute_plan(
            grouped, legacy.read_destination(reader))
        return pos, grouped, pending, changes, missing, unchanged
    finally:
        reader.close()


def prepare(output_dir: Path) -> None:
    """Never receives writer credentials and never opens a writable connection."""
    import pymssql
    out = output_dir.resolve()
    if not out.is_dir():
        raise RuntimeError('OUTPUT_DIRECTORY_MISSING')
    if (out / ARCHIVE_FILENAME).exists():
        raise RuntimeError('PREVIOUS_ARCHIVE_EXISTS')
    manifest = {'schema': ARCHIVE_SCHEMA,
                'created_at_utc': datetime.now(timezone.utc).isoformat(),
                'scope': [{'unidad': u, 'mes': m} for u, m in SCOPE],
                'months': []}
    snapshots: dict[str, bytes] = {}
    total_changes = 0
    for unit, month in SCOPE:
        pos, grouped, pending, changes, missing, unchanged = _load_month(unit, month, pymssql)
        entry = {'unidad': unit, 'mes': month, 'status': 'CHANGES' if changes else 'NO_CHANGES',
                 'changes': len(changes), 'unchanged': unchanged, 'missing_not_inserted': missing,
                 'source_rows': len(pos), 'mapped_keys': len(grouped),
                 'unmapped_source_rows': int(pending.get('producto_sin_mapeo', 0)),
                 'zero_source_rows': int(pending.get('cantidad_cero', 0))}
        if changes:
            snapshot = legacy._make_snapshot(changes, len(pos), grouped, missing, unchanged)
            name = filename_for(unit, month)
            raw = _json_bytes(snapshot)
            snapshots[name] = raw
            entry['snapshot_file'] = name
            entry['snapshot_bytes_sha256'] = hashlib.sha256(raw).hexdigest()
            entry['snapshot_body_sha256'] = snapshot['sha256']
            total_changes += len(changes)
        manifest['months'].append(entry)
        print(f'AUDITADO {unit}/{month} correctas={unchanged} corregir={len(changes)} '
              f'sin_detalle={missing} sin_mapeo={entry["unmapped_source_rows"]} '
              f'cantidades_cero={entry["zero_source_rows"]}', flush=True)

    manifest['total_changes'] = total_changes
    manifest['digest_sha256'] = manifest_digest(manifest)
    with io.BytesIO() as buf:
        with ZipFile(buf, 'w', compression=ZIP_DEFLATED) as z:
            z.writestr('manifest.json', _json_bytes(manifest))
            for name, raw in sorted(snapshots.items()):
                z.writestr(name, raw)
        plaintext = buf.getvalue()
    if len(plaintext) > MAX_ARCHIVE_SIZE:
        raise RuntimeError('ARCHIVE_TOO_LARGE')
    encrypted = Fernet(recovery_key()).encrypt(plaintext)
    # Check that ciphertext decrypts exactly before its offsite upload.
    if Fernet(recovery_key()).decrypt(encrypted) != plaintext:
        raise RuntimeError('ENCRYPTION_SELFTEST_FAILED')
    path = out / ARCHIVE_FILENAME
    fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    with os.fdopen(fd, 'wb') as f:
        f.write(encrypted)
        f.flush()
        os.fsync(f.fileno())
    print(f'BACKUP_CIFRADO_GENERADO={path.name} bytes={len(encrypted)} '
          f'periodos={len(SCOPE)} cambios={total_changes}', flush=True)
    print('SQL_SIN_MODIFICACIONES=SI', flush=True)


def decrypt_and_verify(path: Path) -> tuple[dict, dict[str, bytes]]:
    if path.is_symlink() or not path.is_file():
        raise RuntimeError('ENCRYPTED_ARTIFACT_NOT_FOUND')
    if path.stat().st_size > MAX_ARCHIVE_SIZE * 2:
        raise RuntimeError('ENCRYPTED_ARTIFACT_TOO_LARGE')
    plain = Fernet(recovery_key()).decrypt(path.read_bytes())
    if len(plain) > MAX_ARCHIVE_SIZE:
        raise RuntimeError('PLAINTEXT_ARCHIVE_TOO_LARGE')
    with ZipFile(io.BytesIO(plain)) as z:
        files = z.namelist()
        if len(files) > MAX_SNAPSHOTS + 1 or len(files) != len(set(files)):
            raise RuntimeError('ARCHIVE_FILE_COUNT_INVALID')
        if 'manifest.json' not in files:
            raise RuntimeError('ARCHIVE_NO_MANIFEST')
        manifest = json.loads(z.read('manifest.json'))
        if manifest.get('schema') != ARCHIVE_SCHEMA:
            raise RuntimeError('BACKUP_SCHEMA_INVALID')
        dg = manifest.pop('digest_sha256', '')
        if not dg or manifest_digest(manifest) != dg:
            raise RuntimeError('MANIFEST_INTEGRITY_INVALID')
        manifest['digest_sha256'] = dg
        expected = [{'unidad': u, 'mes': m} for u, m in SCOPE]
        if manifest.get('scope') != expected:
            raise RuntimeError('SCOPE_MISMATCH')
        rows = manifest.get('months')
        if not isinstance(rows, list) or len(rows) != len(SCOPE):
            raise RuntimeError('MONTH_COUNT_MISMATCH')
        actual_names = {'manifest.json'}
        raw_snapshots = {}
        for (unit, month), entry in zip(SCOPE, rows):
            if (entry.get('unidad'), entry.get('mes')) != (unit, month):
                raise RuntimeError('MONTH_ORDER_OR_ID_MISMATCH')
            status = entry.get('status')
            changes = entry.get('changes')
            if status not in {'CHANGES', 'NO_CHANGES'} or not isinstance(changes, int) or changes < 0:
                raise RuntimeError('STATUS_OR_CHANGES_INVALID')
            if status == 'NO_CHANGES':
                if changes != 0 or entry.get('snapshot_file'):
                    raise RuntimeError('UNCHANGED_MONTH_SNAPSHOT_INVALID')
            else:
                if not 0 < changes <= 5000:
                    raise RuntimeError('CHANGES_COUNT_INVALID')
                name = filename_for(unit, month)
                if entry.get('snapshot_file') != name or name not in files:
                    raise RuntimeError('SNAPSHOT_NAME_MISSING')
                actual_names.add(name)
                raw = z.read(name)
                if hashlib.sha256(raw).hexdigest() != entry.get('snapshot_bytes_sha256'):
                    raise RuntimeError('SNAPSHOT_BYTES_INTEGRITY_INVALID')
                data = json.loads(raw)
                if data.get('sha256') != entry.get('snapshot_body_sha256'):
                    raise RuntimeError('SNAPSHOT_DIGEST_MISMATCH')
                if int(data.get('cantidad_a_restaurar') or 0) != changes:
                    raise RuntimeError('SNAPSHOT_COUNT_MISMATCH')
                raw_snapshots[name] = raw
        if set(files) != actual_names:
            raise RuntimeError('UNEXPECTED_FILES_IN_ARCHIVE')
        if sum(int(e['changes']) for e in rows) != manifest.get('total_changes'):
            raise RuntimeError('TOTAL_CHANGE_COUNT_MISMATCH')
        return manifest, raw_snapshots


def verify_only(path: Path) -> None:
    manifest, snapshots = decrypt_and_verify(path)
    print('BACKUP_EXTERNO_VERIFICADO=SI '
          f'periodos={len(manifest["months"])} '
          f'snapshots={len(snapshots)} '
          f'filas={manifest["total_changes"]}', flush=True)


def verify_live_state(manifest: dict, snapshots: dict[str, bytes]) -> None:
    """Fail closed if origin, mapping, or destination shifted after backup."""
    import pymssql
    with tempfile.TemporaryDirectory(prefix='edarsa-mpro-readonly-') as td:
        for (unit, month), entry in zip(SCOPE, manifest['months']):
            pos, grouped, pending, changes, missing, unchanged = _load_month(unit, month, pymssql)
            if (len(pos) != entry['source_rows']
                    or len(grouped) != entry['mapped_keys']
                    or missing != entry['missing_not_inserted']
                    or unchanged != entry['unchanged']
                    or len(changes) != entry['changes']
                    or int(pending.get('producto_sin_mapeo', 0)) != entry['unmapped_source_rows']
                    or int(pending.get('cantidad_cero', 0)) != entry['zero_source_rows']):
                raise RuntimeError(f'ORIGIN_OR_DESTINATION_DRIFT:{unit}:{month}')
            if entry['status'] == 'CHANGES':
                name = filename_for(unit, month)
                p = Path(td) / name
                fd = os.open(p, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
                with os.fdopen(fd, 'wb') as stream:
                    stream.write(snapshots[name])
                snapshot = legacy._read_snapshot(p)
                legacy._assert_same_changes(snapshot, changes)
            elif changes:
                raise RuntimeError(f'UNEXPECTED_CHANGES_IN_CLEAN_MONTH:{unit}:{month}')
            print(f'PREFLIGHT_INDEPENDIENTE_OK {unit}/{month} cambios={len(changes)}', flush=True)


def apply(path: Path) -> None:
    """Only safe after GitHub Actions uploaded an immutable encrypted artifact."""
    if os.environ.get('GITHUB_ACTIONS') != 'true':
        raise RuntimeError('APPLY_SOLO_DESDE_GITHUB_ACTIONS')
    if os.environ.get('GITHUB_REPOSITORY') != 'rbalam/EDARSA_HUB' or \
            os.environ.get('GITHUB_REF') != 'refs/heads/Edarsahub_Desarrollo':
        raise RuntimeError('GITHUB_REPO_OR_BRANCH_INVALID')
    if os.environ.get('MPRO_OFFSITE_ARTIFACT_UPLOADED') != 'true':
        raise RuntimeError('BACKUP_EXTERNO_NO_CERTIFICADO')
    if os.environ.get('EDARSAHUB_SQL_DATABASE', '').upper() != 'EDARSAHUB':
        raise RuntimeError('EDARSAHUB_DATABASE_NOT_ALLOWED')
    if not os.getenv('EDARSAHUB_SQL_WRITER_USER') or not os.getenv('EDARSAHUB_SQL_WRITER_PASSWORD'):
        raise RuntimeError('CANONICAL_WRITER_NOT_AVAILABLE')
    manifest, snapshots = decrypt_and_verify(path)
    # Validate every month before any SQL write. Each apply independently revalidates
    # with UPDLOCK/HOLDLOCK and verifies the committed quantities via HRLectura.
    verify_live_state(manifest, snapshots)
    if not snapshots:
        print('RESULTADO: NINGUN_CAMBIO_PENDIENTE; SQL NO MODIFICADO', flush=True)
        return
    with tempfile.TemporaryDirectory(prefix='edarsa-mpro-recovery-') as tmp:
        tmpdir = Path(tmp)
        for (unit, month), entry in zip(SCOPE, manifest['months']):
            if entry['status'] == 'NO_CHANGES':
                continue
            name = filename_for(unit, month)
            snapshot_path = tmpdir / name
            fd = os.open(snapshot_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            with os.fdopen(fd, 'wb') as f:
                f.write(snapshots[name])
            token = f'COPIA-EXTERNA-{unit}-{month.replace("-", "")}'
            cmd = [sys.executable, str(Path(__file__).with_name('resync_mpro_inventarios_legacy_safe.py')),
                   '--unidad', unit, '--mes', month, '--apply',
                   '--snapshot-file', str(snapshot_path)]
            try:
                result = subprocess.run(cmd, input=token + '\n', text=True,
                                        capture_output=True, timeout=3600, check=False)
            except subprocess.TimeoutExpired as exc:
                raise RuntimeError(f'UPDATE_TIMEOUT:{unit}:{month}; verificar SQL antes de reintentar') from exc
            ok_commit = f'RESULTADO: COMMIT_OK; cantidades actualizadas: {entry["changes"]}'
            if result.returncode != 0 or ok_commit not in result.stdout or \
                    'VERIFICACION_SQL_INDEPENDIENTE: OK' not in result.stdout:
                # Error may occur after commit; never blindly retry.
                err = next((s for s in result.stderr.splitlines() if s.startswith('ERROR: ')), 'UNSPECIFIED_ERROR')
                print(f'BLOQUEADO={unit}/{month} rc={result.returncode} motivo={err[:220]}', flush=True)
                raise RuntimeError(f'REQUIERE_REVISION_SIN_REINTENTO:{unit}:{month}')
            print(f'COMMIT_VERIFICADO {unit}/{month} actualizados={entry["changes"]}', flush=True)
    print('RESULTADO: LOTES_CON_CAMBIOS_APLICADOS_Y_VERIFICADOS', flush=True)
    print('NO_SE_INSERTARON_MOVIMIENTOS=SI; MESES_MIXTOS_130QRO_09_10_BLOQUEADOS=SI', flush=True)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument('--phase', choices=['prepare', 'verify', 'apply'], required=True)
    p.add_argument('--directory', default=None)
    p.add_argument('--encrypted-file', default=None)
    args = p.parse_args()
    legacy.load_configuration()
    if args.phase == 'prepare':
        if not args.directory:
            p.error('--directory required for prepare')
        prepare(Path(args.directory))
    else:
        if not args.encrypted_file:
            p.error('--encrypted-file required for verify and apply')
        if args.phase == 'verify':
            verify_only(Path(args.encrypted_file))
        else:
            apply(Path(args.encrypted_file))


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('OPERACION_CANCELADA_SIN_CERTIFICACION', file=sys.stderr)
        sys.exit(130)
    except Exception as exc:
        print('ERROR: ' + type(exc).__name__ + ':' + str(exc)[:200], file=sys.stderr)
        sys.exit(1)
