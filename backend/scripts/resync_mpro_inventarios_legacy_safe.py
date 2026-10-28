#!/usr/bin/env python3
"""EDARSAHUB: reconciliacion mensual Legacy MPRO, enero-octubre 2026.

Reutiliza los mapeos canonicos de inventario y compara las cantidades
Mv_Cantidad_Control_1 con las filas historicas MOVIMIENTO_POS existentes.
No modifica sincronizadores ni crea/borra filas. No permite actualizar
meses mixtos donde conviven MOVIMIENTO_POS y MOVIMIENTO_POS|concepto.
Siempre requiere snapshot verificado y copia externa previa al apply.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
import os
import sys
from collections import defaultdict
from decimal import Decimal, InvalidOperation, ROUND_HALF_EVEN

# Alcance obligatorio por CLI; la identidad se obtiene exclusivamente del HUB.
EMPRESA = None
SUCURSAL = None
UNIDAD = None
SUCURSAL_MP = None
INICIO = None
FIN = None
MES = None
FECHA_DESDE = None
FECHA_HASTA = None
ESCALA = Decimal('0.000001')


def establecer_alcance(unidad, mes):
    global UNIDAD, MES, INICIO, FIN, FECHA_DESDE, FECHA_HASTA
    if unidad not in ('130QRO', 'ORIGEN'):
        raise RuntimeError('UNIDAD_NO_AUTORIZADA')
    if not isinstance(mes, str) or len(mes) != 7 or mes[:5] != '2026-':
        raise RuntimeError('MES_NO_AUTORIZADO')
    try:
        numero = int(mes[5:])
    except ValueError as exc:
        raise RuntimeError('MES_NO_AUTORIZADO') from exc
    if numero < 1 or numero > 10 or mes != '2026-%02d' % numero:
        raise RuntimeError('MES_FUERA_DE_ENERO_OCTUBRE_2026')
    UNIDAD, MES = unidad, mes
    INICIO = '2026%02d01' % numero
    FIN = '2026%02d01' % (numero+1)
    FECHA_DESDE = '2026-%02d-01' % numero
    FECHA_HASTA = '2026-%02d-01' % (numero+1)


def texto_alcance():
    return '%s/%s' % (UNIDAD, MES)


def token_alcance():
    return '%s-%s' % (UNIDAD, MES.replace('-', ''))

def decimal_6(value):
    try:
        x = Decimal(str(round(abs(float(value)), 6))).quantize(ESCALA, rounding=ROUND_HALF_EVEN)
        if not x.is_finite():
            raise ValueError('CANTIDAD_NO_FINITA')
        return x
    except (InvalidOperation, TypeError, ValueError, OverflowError) as err:
        raise ValueError('CANTIDAD_INVALIDA') from err


def load_configuration():
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    for path in ('/app/backend/.env', '/app/.env'):
        if os.path.isfile(path):
            load_dotenv(path, override=False)


def required(name):
    v = os.getenv(name)
    if not v:
        raise RuntimeError('CONFIGURACION_AUSENTE:' + name)
    return v


def sql_connect(pymssql, *, writer=False, source=None):
    if source is None:
        base = dict(server=required('EDARSAHUB_SQL_HOST'),
                    port=int(os.getenv('EDARSAHUB_SQL_PORT') or '1433'),
                    database=required('EDARSAHUB_SQL_DATABASE'))
        prefix = 'EDARSAHUB_SQL_WRITER' if writer else 'EDARSAHUB_SQL'
        base.update(user=required(prefix + '_USER'), password=required(prefix + '_PASSWORD'))
    else:
        raw = str(source['host']).split('\\', 1)[0].strip()
        port = int(source.get('port') or 1433)
        if ',' in raw:
            host_part, maybe_port = raw.rsplit(',', 1)
            if maybe_port.strip().isdigit():
                raw, port = host_part.strip(), int(maybe_port.strip())
        encrypted = str(source.get('password_encrypted') or '')
        if encrypted.startswith('enc:v1:'):
            from cryptography.fernet import Fernet
            password = Fernet(required('SERVER_SECRET_KEY').encode()).decrypt(
                encrypted[len('enc:v1:'):].encode()).decode()
        else:
            password = encrypted
        if not password:
            raise RuntimeError('CREDENCIAL_ORIGEN_INDISPONIBLE')
        base = dict(server=raw, port=port, database=source['database_name'],
                    user=source['username'], password=password)
    return pymssql.connect(**base, login_timeout=15, timeout=90,
                           as_dict=True, autocommit=(not writer))


def identity(conn, *, writer=False):
    cur = conn.cursor(as_dict=True)
    cur.execute('SELECT DB_NAME() AS db, SUSER_SNAME() AS login, USER_NAME() AS usuario')
    row = cur.fetchone()
    if str(row['db']).upper() != 'EDARSAHUB':
        raise RuntimeError('BASE_INCORRECTA')
    if writer:
        if str(row['login']).lower() != 'gptescritura' or str(row['usuario']).lower() != 'hub_escritura':
            raise RuntimeError('IDENTIDAD_ESCRITURA_INCORRECTA')
    else:
        if str(row['login']).lower() != 'hrlectura':
            raise RuntimeError('LECTOR_INCORRECTO')
    return row


def unique_mapping(cur, query, parameters, key_field, value_field):
    cur.execute(query, parameters)
    result = {}
    for row in cur.fetchall() or []:
        key = str(row[key_field]).strip()
        value = int(row[value_field])
        if key in result and result[key] != value:
            raise RuntimeError('MAPEO_AMBIGUO:' + key)
        result[key] = value
    return result


def get_configuration(conn):
    global EMPRESA, SUCURSAL, SUCURSAL_MP
    cur = conn.cursor(as_dict=True)
    cur.execute('''
        SELECT s.id, s.host, ISNULL(s.port,1433) AS port,
               s.database_name, s.username, s.password_encrypted,
               s.system_type, u.sucursal_origen_id
        FROM dbo.Unidades_Negocio AS u
        INNER JOIN dbo.Servidores_Conexiones AS s
          ON LOWER(CONVERT(varchar(36),u.server_id)) = LOWER(CONVERT(varchar(36),s.id))
        WHERE UPPER(LTRIM(RTRIM(u.codigo)))=%s
          AND ISNULL(u.activo,0)=1 AND ISNULL(s.activo,0)=1
    ''', (UNIDAD,))
    sources = cur.fetchall() or []
    if len(sources) != 1:
        raise RuntimeError('ORIGEN_NO_UNICO_O_NO_DISPONIBLE')
    source = sources[0]
    system = str(source['system_type'] or '').upper()
    if not any(s in system for s in ('MPRO', 'MANAGEMENT', 'MANAGMENT')):
        raise RuntimeError('FUENTE_NO_MANAGEMENTPRO')
    SUCURSAL_MP = str(source['sucursal_origen_id'] or '').strip()
    if not SUCURSAL_MP:
        raise RuntimeError('CODIGO_SUCURSAL_ORIGEN_NO_CONFIGURADO')
    cur.execute('''SELECT EmpresaID FROM dbo.Sistema_Empresas
                   WHERE UPPER(LTRIM(RTRIM(CodigoEmpresa)))=%s AND Activo=1''', (UNIDAD,))
    emp = cur.fetchall() or []
    if len(emp) != 1:
        raise RuntimeError('EMPRESA_CANONICA_NO_UNICA')
    EMPRESA = int(emp[0]['EmpresaID'])
    cur.execute('''SELECT SucursalID FROM dbo.Sistema_Sucursales
                   WHERE EmpresaID=%s AND Activo=1''', (EMPRESA,))
    suc = cur.fetchall() or []
    if len(suc) != 1:
        raise RuntimeError('SUCURSAL_CANONICA_NO_UNICA')
    SUCURSAL = int(suc[0]['SucursalID'])
    if UNIDAD == '130QRO' and (EMPRESA, SUCURSAL, SUCURSAL_MP) != (2, 2, '0021'):
        raise RuntimeError('IDENTIDAD_130QRO_CAMBIO_INESPERADO')
    if UNIDAD == 'ORIGEN' and (EMPRESA, SUCURSAL, SUCURSAL_MP) != (1, 1, '0023'):
        raise RuntimeError('IDENTIDAD_ORIGEN_CAMBIO_INESPERADO')

    products = unique_mapping(cur, '''
        SELECT CodigoFuente, ProductoID FROM dbo.Producto_MapeoOrigen
         WHERE ServerID=%s AND UPPER(SystemType)='MPRO' AND Activo=1
    ''', (str(source['id']),), 'CodigoFuente', 'ProductoID')
    warehouses = unique_mapping(cur, '''
        SELECT CodigoAlmacen, AlmacenID FROM dbo.Inventario_Almacenes
         WHERE EmpresaID=%s AND SucursalID=%s AND Activo=1
    ''', (EMPRESA, SUCURSAL), 'CodigoAlmacen', 'AlmacenID')
    concepts = unique_mapping(cur, '''
        SELECT ConceptoOrigen, TipoMovimientoID
          FROM dbo.Inventario_ConceptoMapeoOrigen
         WHERE UPPER(SystemType)='MPRO' AND Activo=1
    ''', (), 'ConceptoOrigen', 'TipoMovimientoID')
    if UNIDAD == '130QRO' and MES == '2026-10':
        if products.get('0000000061') != 2014:
            raise RuntimeError('MAPEO_PRODUCTO_CERTIFICADO_INCORRECTO')
        if '0001' not in warehouses or '112' not in concepts:
            raise RuntimeError('MAPEO_ALMACEN_CONCEPTO_CERTIFICADO_INCORRECTO')
    if not products or not warehouses or not concepts:
        raise RuntimeError('MAPEOS_CANONICOS_INCOMPLETOS')
    return source, products, warehouses, concepts


def read_pos(pymssql, source):
    conn = sql_connect(pymssql, source=source)
    try:
        cur = conn.cursor(as_dict=True)
        # Exactamente el SELECT MPRO del sincronizador vigente, con fechas delimitadas.
        cur.execute('''
            SELECT Mv_Fecha AS fecha,
                   CAST(Al_Cve_Almacen AS varchar(50)) AS almacen_cod,
                   CAST(Tm_Cve_Tipo_Movimiento AS varchar(50)) AS concepto,
                   CAST(Pr_Cve_Producto AS varchar(50)) AS producto_cod,
                   ISNULL(Mv_Cantidad_Control_1,0) AS cantidad,
                   CAST(Mv_Documento AS varchar(50)) AS folio
            FROM dbo.Movimiento
            WHERE Sc_Cve_Sucursal=%s AND Mv_Fecha >= %s AND Mv_Fecha < %s
        ''', (SUCURSAL_MP, INICIO, FIN))
        rows = cur.fetchall() or []
        return rows
    finally:
        conn.close()


def normalize_date(value):
    day = str(value or '')[:10]
    if len(day) != 10 or not (FECHA_DESDE <= day < FECHA_HASTA):
        raise RuntimeError('FECHA_FUERA_DEL_MES:' + day)
    return day


def source_groups(rows, products, warehouses, concepts):
    grouped = defaultdict(lambda: Decimal('0'))
    pending = defaultdict(int)
    for row in rows:
        quantity = decimal_6(row['cantidad'])
        if quantity <= 0:
            pending['cantidad_cero'] += 1
            continue
        prod_key = str(row.get('producto_cod') or '').strip()
        ware_key = str(row.get('almacen_cod') or '').strip()
        con_key = str(row.get('concepto') or '').strip().upper()
        if prod_key not in products:
            pending['producto_sin_mapeo'] += 1
            continue
        if ware_key not in warehouses:
            pending['almacen_sin_mapeo'] += 1
            continue
        if con_key not in concepts:
            pending['concepto_sin_mapeo'] += 1
            continue
        natural = (EMPRESA, SUCURSAL, warehouses[ware_key], concepts[con_key],
                   normalize_date(row['fecha']), str(row.get('folio') or '').strip()[:30],
                   'MOVIMIENTO_POS', products[prod_key])
        grouped[natural] += quantity
    if not grouped:
        raise RuntimeError('SIN_LLAVES_CANONICAS_RESUELTAS')
    return grouped, dict(pending)


DESTINATION_SQL = '''
    SELECT m.MovimientoID, m.EmpresaID, m.SucursalID, m.AlmacenID,
           m.TipoMovimientoID, CONVERT(varchar(10),m.FechaMovimiento,120) AS fecha,
           m.FolioReferencia, m.ReferenciaTipo, d.ProductoID, d.Cantidad
      FROM dbo.Inventario_Movimientos AS m {locks}
      JOIN dbo.Inventario_MovimientosDetalle AS d {locks}
        ON d.MovimientoID=m.MovimientoID
     WHERE m.EmpresaID=%s AND m.SucursalID=%s
       AND m.FechaMovimiento >= %s AND m.FechaMovimiento < %s
       AND m.ReferenciaTipo = 'MOVIMIENTO_POS'
       AND ISNULL(m.Activo,1)=1
'''


def read_destination(conn, *, lock=False):
    cur = conn.cursor(as_dict=True)
    locks = 'WITH (UPDLOCK,HOLDLOCK)' if lock else ''
    cur.execute(DESTINATION_SQL.format(locks=locks), (EMPRESA, SUCURSAL, INICIO, FIN))
    return cur.fetchall() or []


def destination_key(row):
    return (int(row['EmpresaID']), int(row['SucursalID']), int(row['AlmacenID']),
            int(row['TipoMovimientoID']), normalize_date(row['fecha']),
            str(row.get('FolioReferencia') or '').strip()[:30],
            str(row['ReferenciaTipo'] or '').strip().upper(),
            int(row['ProductoID']))


def compute_plan(grouped, existing):
    by_key = defaultdict(list)
    by_id = defaultdict(list)
    for row in existing:
        by_key[destination_key(row)].append(row)
        by_id[(int(row['MovimientoID']), int(row['ProductoID']))].append(row)
    changes = []
    missing = 0
    unchanged = 0
    ambiguous = 0
    for natural, desired in grouped.items():
        found = by_key.get(natural, [])
        if len(found) > 1:
            ambiguous += 1
            continue
        if not found:
            missing += 1
            continue
        row = found[0]
        current = decimal_6(row['Cantidad'])
        if current != desired:
            changes.append((int(row['MovimientoID']), int(row['ProductoID']), natural,
                            current, desired))
        else:
            unchanged += 1
    if ambiguous:
        raise RuntimeError('LLAVES_DUPLICADAS_DESTINO:' + str(ambiguous))
    return changes, missing, unchanged


def summary(changes, missing, unchanged, source_count, grouped, pending):
    print('=== MPRO %s / %s ===' % (UNIDAD, MES), flush=True)
    print('SUCURSAL_MP:', SUCURSAL_MP, 'EMPRESA_ID:', EMPRESA, 'SUCURSAL_ID:', SUCURSAL)
    print('Filas del origen:', source_count)
    print('Llaves origen (mapeo canonico, referencia Legacy):', len(grouped))
    print('Ya correctas:', unchanged)
    print('Por corregir:', len(changes))
    print('Sin detalle Legacy correspondiente (NO SE INSERTAN):', missing)
    print('Pendientes de mapeo/cantidad cero:', pending)
    for mid, prod, _, old, new in changes[:20]:
        print('  MovimientoID=%s ProductoID=%s: %s -> %s' % (mid, prod, old, new))
    if len(changes) > 20:
        print('  ... %d diferencias adicionales' % (len(changes) - 20))


def guarded_update(writer, changes):
    cur = writer.cursor(as_dict=True)
    for mid, prod, natural, old, new in changes:
        _, _, almacen, tipo, fecha, folio, referencia, _ = natural
        cur.execute('''
            UPDATE d SET d.Cantidad=%s
              FROM dbo.Inventario_MovimientosDetalle d
              JOIN dbo.Inventario_Movimientos m ON m.MovimientoID=d.MovimientoID
             WHERE m.MovimientoID=%s AND d.ProductoID=%s AND d.Cantidad=%s
               AND m.EmpresaID=%s AND m.SucursalID=%s
               AND m.AlmacenID=%s AND m.TipoMovimientoID=%s
               AND CONVERT(varchar(10),m.FechaMovimiento,120)=%s
               AND ISNULL(m.FolioReferencia,'')=%s
               AND m.ReferenciaTipo=%s AND ISNULL(m.Activo,1)=1
        ''', (new, mid, prod, old, EMPRESA, SUCURSAL,
              almacen, tipo, fecha, folio, referencia))
        if cur.rowcount != 1:
            raise RuntimeError('UPDATE_NO_UNICO:' + str(mid))



def assert_legacy_exclusive_month(conn, *, lock=False):
    """Prevent updates to mixed-format months, locking range while applying."""
    cur = conn.cursor(as_dict=True)
    hint = 'WITH (UPDLOCK,HOLDLOCK)' if lock else ''
    sql = """
        SELECT
          SUM(CASE WHEN m.ReferenciaTipo='MOVIMIENTO_POS' THEN 1 ELSE 0 END) AS legacy,
          SUM(CASE WHEN m.ReferenciaTipo LIKE 'MOVIMIENTO_POS|%' THEN 1 ELSE 0 END) AS canonico
        FROM dbo.Inventario_Movimientos AS m {hint}
        WHERE m.EmpresaID=%s AND m.SucursalID=%s
          AND m.FechaMovimiento >= %s AND m.FechaMovimiento < %s
          AND ISNULL(m.Activo,1)=1
    """.format(hint=hint)
    cur.execute(sql, (EMPRESA, SUCURSAL, INICIO, FIN))
    r = cur.fetchone() or {}
    legacy = int(r.get('legacy') or 0)
    canonico = int(r.get('canonico') or 0)
    if canonico:
        raise RuntimeError('MES_MEZCLADO_LEGACY_CANONICO_BLOQUEADO: legacy=%d canonico=%d' % (legacy, canonico))
    print('GUARDIA_FORMATO: LEGACY_EXCLUSIVO; encabezados=%d; canonicos=0' % legacy, flush=True)
    return legacy


RECOVERY_SCHEMA = 'edarsahub.inventarios.mpro.legacy.mensual.beforeimage.v1'


def _json_hash(body):
    raw = json.dumps(body, sort_keys=True, ensure_ascii=False,
                     separators=(',', ':')).encode('utf-8')
    return hashlib.sha256(raw).hexdigest()


def _file_path(raw):
    if not raw:
        raise RuntimeError('FALTA_ARCHIVO_RESPALDO: use --snapshot-file')
    path = Path(raw).expanduser()
    if not path.is_absolute():
        raise RuntimeError('ARCHIVO_DEBE_TENER_RUTA_ABSOLUTA')
    if path.suffix.lower() != '.json':
        raise RuntimeError('ARCHIVO_DEBE_SER_JSON')
    return path


def _make_snapshot(changes, source_count, grouped, missing, unchanged):
    if not changes:
        raise RuntimeError('NO_HAY_DIFERENCIAS_QUE_RESPALDAR')
    if len(changes) > 5000:
        raise RuntimeError('EXCESO_DE_CAMBIOS')
    entries = []
    for mid, prod, natural, old, new in sorted(changes, key=lambda r:(r[0],r[1])):
        entries.append({
            'MovimientoID': mid,
            'ProductoID': prod,
            'EmpresaID': natural[0],
            'SucursalID': natural[1],
            'AlmacenID': natural[2],
            'TipoMovimientoID': natural[3],
            'FechaMovimiento': natural[4],
            'FolioReferencia': natural[5],
            'ReferenciaTipo': natural[6],
            'CantidadAnterior': str(old),
            'CantidadCorrecta': str(new),
        })
    body = {
        'schema': RECOVERY_SCHEMA,
        'database': 'EDARSAHUB',
        'unidad': UNIDAD,
        'sucursal_origen': SUCURSAL_MP,
        'inicio_inclusivo': INICIO,
        'fin_exclusivo': FIN,
        'fecha_creacion_utc': datetime.now(timezone.utc).isoformat(),
        'total_filas_origen': source_count,
        'total_llaves_origen': len(grouped),
        'filas_ya_correctas': unchanged,
        'filas_sin_destino': missing,
        'cantidad_a_restaurar': len(entries),
        'filas': entries,
    }
    return dict(body, sha256=_json_hash(body))


def _save_snapshot(path, snapshot):
    if not path.parent.is_dir():
        raise RuntimeError('CARPETA_DEL_RESPALDO_NO_EXISTE')
    # Exclusivo: jamas sustituir una imagen previa ya creada.
    content = json.dumps(snapshot, ensure_ascii=False, sort_keys=True,
                         indent=2).encode('utf-8') + b'\n'
    fd = os.open(str(path), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(fd, 'wb') as file:
            file.write(content)
            file.flush()
            os.fsync(file.fileno())
    except Exception:
        try:
            path.unlink()
        except OSError:
            pass
        raise
    print('IMAGEN_PREVIA_GUARDADA:', path)
    print('FILAS_RESPALDADAS:', snapshot['cantidad_a_restaurar'])
    print('SHA256_IMAGEN:', snapshot['sha256'])
    print('IMPORTANTE: copie/descargue este JSON fuera de Preview ANTES de --apply.')
    print('RESULTADO: RESPALDO_LOGICO; SQL NO MODIFICADO')


def _read_snapshot(path):
    if path.is_symlink() or not path.is_file():
        raise RuntimeError('ARCHIVO_RESPALDO_INEXISTENTE_O_ENLACE')
    data = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(data, dict):
        raise RuntimeError('RESPALDO_FORMATO_INVALIDO')
    checksum = data.pop('sha256', None)
    if not checksum or checksum != _json_hash(data):
        raise RuntimeError('INTEGRIDAD_SHA256_RESPALDO_INVALIDA')
    data['sha256'] = checksum
    if (data.get('schema') != RECOVERY_SCHEMA or data.get('database') != 'EDARSAHUB'
            or data.get('unidad') != UNIDAD or data.get('sucursal_origen') != SUCURSAL_MP
            or data.get('inicio_inclusivo') != INICIO or data.get('fin_exclusivo') != FIN):
        raise RuntimeError('RESPALDO_ALCANCE_INCORRECTO')
    rows = data.get('filas')
    if not isinstance(rows, list) or not rows or len(rows) > 5000:
        raise RuntimeError('RESPALDO_NUMERO_FILAS_INCORRECTO')
    if len(rows) != int(data.get('cantidad_a_restaurar') or 0):
        raise RuntimeError('RESPALDO_CONTEO_INCONSISTENTE')
    keys = set()
    for r in rows:
        k = (int(r['MovimientoID']), int(r['ProductoID']))
        if k in keys or (int(r['EmpresaID']), int(r['SucursalID'])) != (EMPRESA, SUCURSAL):
            raise RuntimeError('RESPALDO_IDENTIDAD_DUPLICADA_O_INCORRECTA')
        keys.add(k)
        if not (FECHA_DESDE <= r['FechaMovimiento'] < FECHA_HASTA):
            raise RuntimeError('RESPALDO_FECHA_FUERA_DE_MES')
        if decimal_6(r['CantidadAnterior']) <= 0 or decimal_6(r['CantidadCorrecta']) <= 0:
            raise RuntimeError('RESPALDO_CANTIDAD_INVALIDA')
    return data


def _changes_from_snapshot(snapshot, *, reverse=False):
    result = []
    for r in snapshot['filas']:
        natural = (
            int(r['EmpresaID']), int(r['SucursalID']),
            int(r['AlmacenID']), int(r['TipoMovimientoID']),
            r['FechaMovimiento'], r['FolioReferencia'],
            r['ReferenciaTipo'], int(r['ProductoID']),
        )
        old, new = decimal_6(r['CantidadAnterior']), decimal_6(r['CantidadCorrecta'])
        result.append((int(r['MovimientoID']), int(r['ProductoID']), natural,
                       new if reverse else old, old if reverse else new))
    return result


def _assert_same_changes(snapshot, current):
    expected = _changes_from_snapshot(snapshot)
    if sorted(expected) != sorted(current):
        raise RuntimeError('EL_PLAN_Y_EL_RESPALDO_NO_COINCIDEN; NINGUN_CAMBIO')


def _assert_snapshot_state(snapshot, existing, *, expected_correct):
    by_id = defaultdict(list)
    for row in existing:
        by_id[(int(row['MovimientoID']), int(row['ProductoID']))].append(row)
    for mid, prod, natural, old, new in _changes_from_snapshot(snapshot):
        rows = by_id.get((mid, prod), [])
        if len(rows) != 1 or destination_key(rows[0]) != natural:
            raise RuntimeError('MOVIMIENTO_RESTAURACION_IDENTIDAD_INCORRECTA:' + str(mid))
        expected = new if expected_correct else old
        if decimal_6(rows[0]['Cantidad']) != expected:
            raise RuntimeError('MOVIMIENTO_RESTAURACION_CANTIDAD_CAMBIO:' + str(mid))


def _writer_session(writer):
    ident = identity(writer, writer=True)
    cur = writer.cursor(as_dict=True)
    cur.execute('SET XACT_ABORT ON')
    cur.execute('SET LOCK_TIMEOUT 15000')
    cur.execute('SET DEADLOCK_PRIORITY LOW')
    cur.execute("SELECT COALESCE(HAS_PERMS_BY_NAME('dbo.Inventario_MovimientosDetalle','OBJECT','UPDATE'),0) AS permiso")
    if int(cur.fetchone()['permiso']) != 1:
        raise RuntimeError('WRITER_SIN_PERMISO_UPDATE')
    return ident


def _confirm(phrase):
    entered = input('Escriba ' + phrase + ' para continuar: ').strip()
    if entered != phrase:
        raise RuntimeError('OPERACION_CANCELADA')


def _restore(pymssql, snapshot):
    print('OPERACION: RESTAURACION DE VALORES ANTERIORES, SOLAMENTE LAS FILAS RESPALDADAS.')
    _confirm('RESTAURAR-' + token_alcance())
    writer = sql_connect(pymssql, writer=True)
    try:
        _writer_session(writer)
        assert_legacy_exclusive_month(writer, lock=True)
        locked = read_destination(writer, lock=True)
        _assert_snapshot_state(snapshot, locked, expected_correct=True)
        guarded_update(writer, _changes_from_snapshot(snapshot, reverse=True))
        _assert_snapshot_state(snapshot, read_destination(writer, lock=True),
                               expected_correct=False)
        writer.commit()
        print('RESULTADO: RESTAURACION_COMMIT_OK; filas:', len(snapshot['filas']))
    except Exception:
        writer.rollback()
        print('RESULTADO: RESTAURACION_ROLLBACK', file=sys.stderr)
        raise
    finally:
        writer.close()
    verify = sql_connect(pymssql)
    try:
        identity(verify)
        _assert_snapshot_state(snapshot, read_destination(verify), expected_correct=False)
        print('VERIFICACION_RESTAURACION: OK')
    finally:
        verify.close()


def main():
    parser = argparse.ArgumentParser(description='Reconciliacion exclusiva Legacy MPRO 2026 por sucursal/mes: audit, snapshot, apply, rollback')
    parser.add_argument('--unidad', choices=('130QRO', 'ORIGEN'), required=True)
    parser.add_argument('--mes', required=True, help='2026-01 a 2026-10; una sucursal y un mes por ejecucion')
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--audit', action='store_true', help='Solo comparar; predeterminado')
    mode.add_argument('--snapshot', action='store_true', help='Guardar imagen previa JSON de filas afectadas; SIN escritura SQL')
    mode.add_argument('--apply', action='store_true', help='Actualizar cantidades existentes usando una imagen previa verificada')
    mode.add_argument('--rollback', action='store_true', help='Restaurar exclusivamente las cantidades previas del JSON')
    parser.add_argument('--snapshot-file', help='Archivo JSON absoluto de las cantidades antes del cambio')
    args = parser.parse_args()
    if (args.snapshot or args.apply or args.rollback) and not args.snapshot_file:
        parser.error('--snapshot-file es obligatorio para snapshot/apply/rollback')
    establecer_alcance(args.unidad, args.mes)

    load_configuration()
    import pymssql
    backup_path = _file_path(args.snapshot_file) if args.snapshot_file else None
    reader = sql_connect(pymssql)
    try:
        identity(reader)
        source, products, warehouses, concepts = get_configuration(reader)
        assert_legacy_exclusive_month(reader)
        if args.rollback:
            snapshot = _read_snapshot(backup_path)
        else:
            pos = read_pos(pymssql, source)
            if not pos:
                if args.snapshot or args.apply:
                    raise RuntimeError('SIN_MOVIMIENTOS_EN_ORIGEN; NADA_QUE_CORREGIR')
                print('=== MPRO %s / %s ===' % (UNIDAD, MES))
                print('SUCURSAL_MP:', SUCURSAL_MP, 'EMPRESA_ID:', EMPRESA, 'SUCURSAL_ID:', SUCURSAL)
                print('RESULTADO: SIN_MOVIMIENTOS_EN_ORIGEN; SQL NO MODIFICADO')
                return
            grouped, pending = source_groups(pos, products, warehouses, concepts)
            changes, missing, unchanged = compute_plan(grouped, read_destination(reader))
    finally:
        reader.close()
    if args.rollback:
        _restore(pymssql, snapshot)
        return
    summary(changes, missing, unchanged, len(pos), grouped, pending)

    if args.snapshot:
        _save_snapshot(backup_path,
                       _make_snapshot(changes, len(pos), grouped, missing, unchanged))
        return
    if not args.apply:
        print('RESULTADO: AUDITORIA, SQL NO MODIFICADO')
        return

    snapshot = _read_snapshot(backup_path)
    _assert_same_changes(snapshot, changes)
    if len(changes) > 5000:
        raise RuntimeError('EXCESO_DE_CAMBIOS')
    print('SQL COMPARTIDO PREVIEW/PRODUCCION. Alcance:', texto_alcance())
    print('Este proceso tiene imagen previa verificada:', backup_path)
    print('COMPRUEBE QUE UNA COPIA DEL JSON YA ESTA FUERA DE PREVIEW.')
    _confirm('COPIA-EXTERNA-' + token_alcance())
    writer = sql_connect(pymssql, writer=True)
    try:
        ident = _writer_session(writer)
        assert_legacy_exclusive_month(writer, lock=True)
        locked_changes, locked_missing, locked_unchanged = compute_plan(
            grouped, read_destination(writer, lock=True))
        if (locked_changes, locked_missing, locked_unchanged) != (changes, missing, unchanged):
            raise RuntimeError('EL_DESTINO_CAMBIO_DURANTE_EL_PREFLIGHT')
        _assert_same_changes(snapshot, locked_changes)
        guarded_update(writer, locked_changes)
        after_changes, _, _ = compute_plan(grouped, read_destination(writer, lock=True))
        if after_changes:
            raise RuntimeError('POSTVERIFICACION_FALLIDA')
        _assert_snapshot_state(snapshot, read_destination(writer, lock=True), expected_correct=True)
        writer.commit()
        print('RESULTADO: COMMIT_OK; cantidades actualizadas:', len(locked_changes))
        print('IDENTIDAD_SQL:', ident['login'], '/', ident['usuario'])
    except Exception:
        writer.rollback()
        print('RESULTADO: ROLLBACK / SIN CONFIRMACION', file=sys.stderr)
        raise
    finally:
        writer.close()

    verify = sql_connect(pymssql)
    try:
        identity(verify)
        assert_legacy_exclusive_month(verify)
        final_changes, _, _ = compute_plan(grouped, read_destination(verify))
        if final_changes:
            raise RuntimeError('VERIFICACION_LECTORA_NO_COINCIDE:' + str(len(final_changes)))
        _assert_snapshot_state(snapshot, read_destination(verify), expected_correct=True)
        print('VERIFICACION_SQL_INDEPENDIENTE: OK - 0 diferencias en filas existentes')
    finally:
        verify.close()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('CANCELADO_POR_USUARIO; SQL NO MODIFICADO SI NO HUBO COMMIT', file=sys.stderr)
        sys.exit(130)
    except Exception as exc:
        print('ERROR: %s: %s' % (type(exc).__name__, str(exc)[:180]), file=sys.stderr)
        sys.exit(1)
