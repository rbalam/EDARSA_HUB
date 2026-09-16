#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / 'backend'
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

FORBIDDEN = re.compile(r'\b(insert|update|delete|merge|exec(?:ute)?|create|alter|drop|truncate|grant|revoke|deny|backup|restore|dbcc|use|waitfor|kill)\b', re.I)
SELECT_INTO = re.compile(r'\bselect\b[\s\S]*?\binto\b', re.I)

def _strip_literals_and_comments(sql: str) -> str:
    text = re.sub(r'/\*.*?\*/', ' ', sql, flags=re.S)
    text = re.sub(r'--[^\n\r]*', ' ', text)
    text = re.sub(r"N?'(?:''|[^'])*'", "''", text)
    return text

def validate_readonly_sql(sql: str) -> str:
    if not isinstance(sql, str) or not sql.strip():
        raise ValueError('SQL_REQUIRED')
    normalized = _strip_literals_and_comments(sql).strip()
    body = normalized[:-1].rstrip() if normalized.endswith(';') else normalized
    if ';' in body:
        raise ValueError('MULTI_STATEMENT_FORBIDDEN')
    first = re.match(r'^([A-Za-z]+)', body)
    if not first or first.group(1).upper() not in {'SELECT', 'WITH'}:
        raise ValueError('ONLY_SELECT_OR_WITH_ALLOWED')
    if FORBIDDEN.search(body):
        raise ValueError('DML_DDL_OR_CONTROL_FORBIDDEN')
    if SELECT_INTO.search(body):
        raise ValueError('SELECT_INTO_FORBIDDEN')
    return sql.strip()

def _json_value(value: Any) -> Any:
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, bytes):
        return value.hex()
    return value

ALLOWED_POS_SYSTEM_TYPES = {'MPRO', 'SOFTRESTAURANT'}
UNIT_CODE_RE = re.compile(r'^[A-Za-z0-9][A-Za-z0-9_-]{1,31}$')

def _query_evidence(conn, queries: list[dict[str, Any]], max_rows: int, *, target: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    evidence = []
    for item in queries:
        name = str(item.get('name') or '').strip()
        sql = validate_readonly_sql(str(item.get('sql') or ''))
        cur = conn.cursor()
        cur.execute(sql)
        columns = [d[0] for d in (cur.description or [])]
        rows = cur.fetchmany(max_rows + 1) if cur.description else []
        truncated = len(rows) > max_rows
        rows = rows[:max_rows]
        row = {
            'name': name,
            'columns': columns,
            'rows': [[_json_value(v) for v in result_row] for result_row in rows],
            'row_count_returned': len(rows),
            'truncated': truncated,
        }
        if target:
            row['target'] = target
        evidence.append(row)
    return evidence

def execute_queries(queries: list[dict[str, Any]], max_rows: int = 200, *, source: str = 'EDARSAHUB', units: list[str] | None = None, system_types: list[str] | None = None) -> dict[str, Any]:
    source_name = str(source or 'EDARSAHUB').strip().upper()
    unit_codes = [str(value).strip().upper() for value in (units or [])]
    requested_types = [str(value).strip().upper() for value in (system_types or [])]

    if source_name == 'EDARSAHUB':
        if unit_codes or requested_types:
            raise ValueError('EDARSAHUB_SOURCE_DOES_NOT_ACCEPT_POS_SELECTORS')
        from core.sql_first.db import readonly_sql_connection
        with readonly_sql_connection('default') as conn:
            evidence = _query_evidence(conn, queries, max_rows)
            try:
                conn.rollback()
            except Exception:
                pass
        return {'status': 'PASS', 'mode': 'READ_ONLY_SQL', 'connection': 'readonly_sql_connection:default', 'evidence': evidence}

    if source_name != 'POS':
        raise ValueError('INVALID_READONLY_SOURCE')
    if not unit_codes or any(not UNIT_CODE_RE.fullmatch(code) for code in unit_codes):
        raise ValueError('POS_UNITS_REQUIRED_OR_INVALID')
    if not requested_types or any(value not in ALLOWED_POS_SYSTEM_TYPES for value in requested_types):
        raise ValueError('POS_SYSTEM_TYPES_REQUIRED_OR_INVALID')

    from core.connections.pos_runtime_resolver import list_pos_runtime_contexts
    from core.sql_first.connection_factory import get_external_sql_connection

    contexts = list_pos_runtime_contexts(system_types=requested_types)
    evidence = []
    targets = []
    for code in unit_codes:
        matches = [context for context in contexts if context.unidad_codigo.upper() == code]
        if len(matches) != 1:
            raise ValueError(f'POS_UNIT_NOT_UNIQUELY_RESOLVED:{code}')
        context = matches[0]
        target = {
            'unidad_codigo': context.unidad_codigo,
            'system_type': context.system_type,
            'server_id': context.server_id,
            'database': context.database,
        }
        conn = get_external_sql_connection(context.external_connection_config(as_dict=False))
        try:
            evidence.extend(_query_evidence(conn, queries, max_rows, target=target))
            try:
                conn.rollback()
            except Exception:
                pass
        finally:
            conn.close()
        targets.append(target)

    return {
        'status': 'PASS',
        'mode': 'READ_ONLY_SQL',
        'connection': 'PosRuntimeResolver+get_external_sql_connection',
        'targets': targets,
        'evidence': evidence,
    }

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--queries-json', required=True)
    parser.add_argument('--max-rows', type=int, default=200)
    parser.add_argument('--source', choices=['EDARSAHUB', 'POS'], default='EDARSAHUB')
    parser.add_argument('--units-json', default='[]')
    parser.add_argument('--system-types-json', default='[]')
    args = parser.parse_args()
    try:
        queries = json.loads(args.queries_json)
        units = json.loads(args.units_json)
        system_types = json.loads(args.system_types_json)
        if not isinstance(queries, list) or not queries:
            raise ValueError('QUERIES_REQUIRED')
        if not isinstance(units, list) or not isinstance(system_types, list):
            raise ValueError('POS_SELECTORS_MUST_BE_LISTS')
        for item in queries:
            if not isinstance(item, dict) or not str(item.get('name') or '').strip():
                raise ValueError('QUERY_NAME_REQUIRED')
        result = execute_queries(
            queries,
            max_rows=max(1, min(args.max_rows, 500)),
            source=args.source,
            units=units,
            system_types=system_types,
        )
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        return 0
    except Exception as exc:
        print(json.dumps({'status': 'FAIL', 'error': f'{type(exc).__name__}:{exc}'}, ensure_ascii=False, sort_keys=True))
        return 2

if __name__ == '__main__':
    raise SystemExit(main())
