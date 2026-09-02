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

def execute_queries(queries: list[dict[str, Any]], max_rows: int = 200) -> dict[str, Any]:
    from core.sql_first.db import readonly_sql_connection
    evidence = []
    with readonly_sql_connection('default') as conn:
        for item in queries:
            name = str(item.get('name') or '').strip()
            sql = validate_readonly_sql(str(item.get('sql') or ''))
            cur = conn.cursor()
            cur.execute(sql)
            columns = [d[0] for d in (cur.description or [])]
            rows = cur.fetchmany(max_rows + 1) if cur.description else []
            truncated = len(rows) > max_rows
            rows = rows[:max_rows]
            evidence.append({
                'name': name,
                'columns': columns,
                'rows': [[_json_value(v) for v in row] for row in rows],
                'row_count_returned': len(rows),
                'truncated': truncated,
            })
        try:
            conn.rollback()
        except Exception:
            pass
    return {'status': 'PASS', 'mode': 'READ_ONLY_SQL', 'connection': 'readonly_sql_connection:default', 'evidence': evidence}

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--queries-json', required=True)
    parser.add_argument('--max-rows', type=int, default=200)
    args = parser.parse_args()
    try:
        queries = json.loads(args.queries_json)
        if not isinstance(queries, list) or not queries:
            raise ValueError('QUERIES_REQUIRED')
        for item in queries:
            if not isinstance(item, dict) or not str(item.get('name') or '').strip():
                raise ValueError('QUERY_NAME_REQUIRED')
        result = execute_queries(queries, max_rows=max(1, min(args.max_rows, 500)))
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        return 0
    except Exception as exc:
        print(json.dumps({'status': 'FAIL', 'error': f'{type(exc).__name__}:{exc}'}, ensure_ascii=False, sort_keys=True))
        return 2

if __name__ == '__main__':
    raise SystemExit(main())
