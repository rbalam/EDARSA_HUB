from __future__ import annotations

import re


FORBIDDEN_SQL = re.compile(
    r"\b("
    r"insert|update|delete|merge|exec(?:ute)?|create|alter|drop|truncate|"
    r"grant|revoke|deny|backup|restore|dbcc|use|waitfor|kill|reconfigure|"
    r"openrowset|opendatasource|bulk|shutdown"
    r")\b",
    re.IGNORECASE,
)
SELECT_INTO = re.compile(r"\bselect\b[\s\S]*?\binto\b", re.IGNORECASE)
XP_OR_SP = re.compile(r"\b(?:xp_|sp_)[A-Za-z0-9_]*\b", re.IGNORECASE)


def _strip_literals_and_comments(sql: str) -> str:
    text = re.sub(r"/\*.*?\*/", " ", sql, flags=re.DOTALL)
    text = re.sub(r"--[^\n\r]*", " ", text)
    text = re.sub(r"N?'(?:''|[^'])*'", "''", text)
    return text


def validate_readonly_sql(sql: str) -> str:
    if not isinstance(sql, str) or not sql.strip():
        raise ValueError("SQL_REQUIRED")

    normalized = _strip_literals_and_comments(sql).strip()
    body = normalized[:-1].rstrip() if normalized.endswith(";") else normalized

    if ";" in body:
        raise ValueError("MULTI_STATEMENT_FORBIDDEN")

    first = re.match(r"^([A-Za-z]+)", body)
    if not first or first.group(1).upper() not in {"SELECT", "WITH"}:
        raise ValueError("ONLY_SELECT_OR_WITH_ALLOWED")

    if FORBIDDEN_SQL.search(body) or XP_OR_SP.search(body):
        raise ValueError("DML_DDL_OR_CONTROL_FORBIDDEN")

    if SELECT_INTO.search(body):
        raise ValueError("SELECT_INTO_FORBIDDEN")

    return sql.strip()


def validate_readonly_sql_result(sql: str) -> tuple[bool, str]:
    try:
        validate_readonly_sql(sql)
        return True, ""
    except ValueError as exc:
        return False, str(exc)
