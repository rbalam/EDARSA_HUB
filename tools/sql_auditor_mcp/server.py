#!/usr/bin/env python3
"""EDARSA SQL Auditor - MCP server de solo lectura.

Agente independiente del Worker de EDARSAHUB.

Seguridad por capas:
1. Autoriza al requester contra RBAC SQL canonico (Usuario_Catalogo).
2. Solo acepta una sentencia SELECT/WITH.
3. Bloquea keywords de escritura/DDL/ejecucion dinamica y comentarios SQL.
4. Ejecuta en transaccion no-autocommit y hace rollback siempre.
5. Exige credenciales SQL fisicamente de solo lectura y valida privilegios
   efectivos antes de ejecutar cualquier consulta del usuario.

Nunca expone passwords ni API keys en las respuestas MCP.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import os
import re
import sys
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, Iterable

from mcp.server.fastmcp import FastMCP

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from core.server_registry import get_server_connection_info, list_servers
from core.sql_first.connection_factory import (
    get_edarsahub_pymssql_connection,
    get_external_sql_connection,
)

APP_NAME = "EDARSA SQL Auditor"
REQUESTER_ENV = "EDARSA_SQL_AUDITOR_REQUESTER_EMAIL"
MAX_ROWS_HARD = int(os.environ.get("EDARSA_SQL_AUDITOR_MAX_ROWS", "5000"))
DEFAULT_ROWS = min(500, MAX_ROWS_HARD)

mcp = FastMCP(APP_NAME)

SUPERADMIN_ROLE_CODES = {"SUPERADMIN"}
SUPERADMIN_ROLE_NAMES = {"SUPERADMINISTRADOR", "SUPER ADMINISTRADOR"}
EXPECTED_RBAC_DATABASE = "EDARSAHUB"
EXPECTED_RBAC_LOGIN = "HRLECTURA"
EXPECTED_RBAC_USER = "HRLECTURA"

# Credenciales exclusivas del Auditor. Nunca se guardan passwords en GitHub.
# Cada servidor se habilita de manera explicita conforme se valida su login RO.
LOCAL_READONLY_CREDENTIALS = {
    "CIENFUEGOS": (
        "EDARSA_SQL_AUDITOR_CF_USER",
        "EDARSA_SQL_AUDITOR_CF_PASSWORD",
    ),
}

BLOCKED_SQL_WORDS = {
    "INSERT", "UPDATE", "DELETE", "MERGE", "DROP", "ALTER", "TRUNCATE",
    "CREATE", "EXEC", "EXECUTE", "GRANT", "REVOKE", "DENY", "BACKUP",
    "RESTORE", "DBCC", "BULK", "OPENROWSET", "OPENDATASOURCE", "INTO",
    "USE", "DECLARE", "SET", "KILL", "SHUTDOWN", "RECONFIGURE",
}

DANGEROUS_DATABASE_PERMISSIONS = {
    "ALTER",
    "ALTER ANY APPLICATION ROLE",
    "ALTER ANY ASSEMBLY",
    "ALTER ANY CERTIFICATE",
    "ALTER ANY CONTRACT",
    "ALTER ANY DATABASE AUDIT",
    "ALTER ANY DATABASE DDL TRIGGER",
    "ALTER ANY DATABASE EVENT NOTIFICATION",
    "ALTER ANY DATABASE EVENT SESSION",
    "ALTER ANY DATABASE SCOPED CONFIGURATION",
    "ALTER ANY DATASPACE",
    "ALTER ANY EXTERNAL DATA SOURCE",
    "ALTER ANY EXTERNAL FILE FORMAT",
    "ALTER ANY FULLTEXT CATALOG",
    "ALTER ANY MASK",
    "ALTER ANY MESSAGE TYPE",
    "ALTER ANY REMOTE SERVICE BINDING",
    "ALTER ANY ROLE",
    "ALTER ANY ROUTE",
    "ALTER ANY SCHEMA",
    "ALTER ANY SECURITY POLICY",
    "ALTER ANY SENSITIVITY CLASSIFICATION",
    "ALTER ANY SERVICE",
    "ALTER ANY SYMMETRIC KEY",
    "ALTER ANY USER",
    "AUTHENTICATE",
    "BACKUP DATABASE",
    "BACKUP LOG",
    "CONTROL",
    "CREATE AGGREGATE",
    "CREATE ASSEMBLY",
    "CREATE CERTIFICATE",
    "CREATE CONTRACT",
    "CREATE DATABASE DDL EVENT NOTIFICATION",
    "CREATE DEFAULT",
    "CREATE FULLTEXT CATALOG",
    "CREATE FUNCTION",
    "CREATE MESSAGE TYPE",
    "CREATE PROCEDURE",
    "CREATE QUEUE",
    "CREATE REMOTE SERVICE BINDING",
    "CREATE ROLE",
    "CREATE ROUTE",
    "CREATE RULE",
    "CREATE SCHEMA",
    "CREATE SERVICE",
    "CREATE SYMMETRIC KEY",
    "CREATE SYNONYM",
    "CREATE TABLE",
    "CREATE TYPE",
    "CREATE VIEW",
    "CREATE XML SCHEMA COLLECTION",
    "DELETE",
    "EXECUTE",
    "IMPERSONATE",
    "INSERT",
    "TAKE OWNERSHIP",
    "UPDATE",
}


def _norm(value: Any) -> str:
    return str(value or "").strip().upper()


def _row_to_dict(cursor: Any, row: Any) -> dict[str, Any]:
    if row is None:
        return {}
    columns = [str(item[0]) for item in (cursor.description or [])]
    return dict(zip(columns, row))


def _authorize() -> dict[str, Any]:
    """Fail-closed: valida requester contra RBAC SQL canonico, solo lectura."""
    email = str(os.environ.get(REQUESTER_ENV) or "").strip().lower()
    if not email or "@" not in email:
        raise PermissionError(f"{REQUESTER_ENV} no configurado o invalido")

    conn = None
    try:
        conn = get_edarsahub_pymssql_connection(autocommit=False)
        cursor = conn.cursor()

        cursor.execute(
            "SELECT DB_NAME() AS database_name, "
            "SUSER_SNAME() AS login_name, USER_NAME() AS database_user"
        )
        identity = _row_to_dict(cursor, cursor.fetchone())
        if (
            _norm(identity.get("database_name")) != EXPECTED_RBAC_DATABASE
            or _norm(identity.get("login_name")) != EXPECTED_RBAC_LOGIN
            or _norm(identity.get("database_user")) != EXPECTED_RBAC_USER
        ):
            raise PermissionError("RBAC_SQL_IDENTITY_MISMATCH")

        cursor.execute(
            """
            SELECT TOP 1
                uc.UsuarioID,
                uc.Email,
                uc.Username,
                uc.Activo,
                ur.CodigoRol,
                ur.NombreRol
            FROM dbo.Usuario_Catalogo uc
            LEFT JOIN dbo.Usuario_RolesAsignacion ura
                ON ura.UsuarioID = uc.UsuarioID
               AND ISNULL(ura.Activo,1)=1
               AND ISNULL(ura.EsPrincipal,0)=1
            LEFT JOIN dbo.Usuario_Roles ur
                ON ur.RolID = ura.RolID
            WHERE LOWER(uc.Email) = LOWER(%s)
               OR LOWER(uc.Username) = LOWER(%s)
            """,
            (email, email),
        )
        user = _row_to_dict(cursor, cursor.fetchone())

        if not user:
            raise PermissionError("REQUESTER_NOT_FOUND")
        if not bool(user.get("Activo")):
            raise PermissionError("REQUESTER_INACTIVE")

        role_code = _norm(user.get("CodigoRol"))
        role_name = _norm(user.get("NombreRol"))
        if role_code not in SUPERADMIN_ROLE_CODES and role_name not in SUPERADMIN_ROLE_NAMES:
            raise PermissionError("REQUESTER_NOT_SUPERADMIN")

        return {
            "usuario_id": user.get("UsuarioID"),
            "email": str(user.get("Email") or email).strip().lower(),
            "role_code": role_code,
            "role": role_name,
            "auth_source": "SQL_USUARIO_CATALOGO_HRLECTURA",
            "sql_identity": {
                "database": identity.get("database_name"),
                "login": identity.get("login_name"),
                "user": identity.get("database_user"),
            },
        }
    finally:
        if conn is not None:
            try:
                conn.rollback()
            except Exception:
                pass
            try:
                conn.close()
            except Exception:
                pass


def _validate_readonly_sql(sql: str) -> str:
    """Acepta una sola sentencia SELECT/WITH y rechaza superficies de escritura."""
    if not isinstance(sql, str) or not sql.strip():
        raise ValueError("SQL_REQUIRED")

    text = sql.strip()

    if "--" in text or "/*" in text or "*/" in text:
        raise ValueError("SQL_COMMENTS_NOT_ALLOWED")

    without_final = text[:-1].rstrip() if text.endswith(";") else text
    if ";" in without_final:
        raise ValueError("MULTI_STATEMENT_SQL_NOT_ALLOWED")

    upper = without_final.upper()
    if not (upper.startswith("SELECT") or upper.startswith("WITH")):
        raise ValueError("ONLY_SELECT_OR_WITH_ALLOWED")

    for word in BLOCKED_SQL_WORDS:
        if re.search(rf"\b{re.escape(word)}\b", upper):
            raise ValueError(f"BLOCKED_SQL_KEYWORD:{word}")

    if re.search(r"\b(?:XP_|SP_)[A-Z0-9_]*\b", upper):
        raise ValueError("SYSTEM_PROCEDURES_NOT_ALLOWED")

    return without_final


def _serialize(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, bytes):
        return "<binary>"
    return str(value)


def _masked_server(server: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": server.get("id"),
        "name": server.get("name"),
        "system_type": server.get("system_type"),
        "system_type_normalized": server.get("system_type_normalized"),
        "config_origin": server.get("config_origin"),
        "credential_source": server.get("credential_source"),
    }


def _apply_local_readonly_credentials(server: dict[str, Any]) -> dict[str, Any]:
    """Aplica credenciales RO locales por servidor, sin exponer secretos."""
    result = dict(server)
    name = _norm(result.get("name"))
    env_pair = LOCAL_READONLY_CREDENTIALS.get(name)
    if not env_pair:
        return result

    user_env, password_env = env_pair
    username = str(os.environ.get(user_env) or "").strip()
    password = os.environ.get(password_env)
    if not username or not password:
        raise PermissionError(
            f"READONLY_CREDENTIALS_NOT_CONFIGURED:{name}:{user_env}:{password_env}"
        )

    result["username"] = username
    result["password"] = password
    result["credential_source"] = "LOCAL_ENV_READONLY"
    return result


async def _all_servers_masked() -> list[dict[str, Any]]:
    servers = await list_servers(mask_secrets=True)
    return [_masked_server(s) for s in servers]


async def _resolve_server(selector: str) -> dict[str, Any]:
    selector = str(selector or "").strip()
    if not selector:
        raise ValueError("SERVER_REQUIRED")

    servers = await list_servers(mask_secrets=True)
    exact = [
        s for s in servers
        if str(s.get("id") or "").lower() == selector.lower()
        or str(s.get("mongodb_id") or "").lower() == selector.lower()
        or str(s.get("name") or "").strip().lower() == selector.lower()
    ]
    if not exact:
        raise ValueError(f"SERVER_NOT_FOUND:{selector}")
    if len(exact) > 1:
        raise ValueError(f"SERVER_AMBIGUOUS:{selector}")

    info = await get_server_connection_info(str(exact[0]["id"]))
    if not info:
        raise ValueError(f"SERVER_CONNECTION_INFO_UNAVAILABLE:{selector}")
    return _apply_local_readonly_credentials(info)


def _connect(server: dict[str, Any]):
    config = {
        "host": server.get("host"),
        "port": server.get("port", 1433),
        "database": server.get("database"),
        "username": server.get("username"),
        "password": server.get("password"),
        "login_timeout": 10,
        "timeout": 30,
        "as_dict": False,
    }
    return get_external_sql_connection(config)


def _assert_connection_is_readonly(cursor: Any) -> dict[str, Any]:
    """Rechaza conexiones con privilegios incompatibles con el Auditor."""
    cursor.execute(
        """
        SELECT
            DB_NAME() AS database_name,
            SUSER_SNAME() AS login_name,
            USER_NAME() AS database_user,
            IS_SRVROLEMEMBER('sysadmin') AS is_sysadmin,
            IS_ROLEMEMBER('db_owner') AS is_db_owner,
            IS_ROLEMEMBER('db_datareader') AS is_db_datareader,
            IS_ROLEMEMBER('db_datawriter') AS is_db_datawriter,
            HAS_PERMS_BY_NAME(DB_NAME(), 'DATABASE', 'SELECT') AS can_select
        """
    )
    identity = _row_to_dict(cursor, cursor.fetchone())

    if int(identity.get("is_sysadmin") or 0) != 0:
        raise PermissionError("SQL_LOGIN_NOT_READONLY:SYSADMIN")
    if int(identity.get("is_db_owner") or 0) != 0:
        raise PermissionError("SQL_LOGIN_NOT_READONLY:DB_OWNER")
    if int(identity.get("is_db_datawriter") or 0) != 0:
        raise PermissionError("SQL_LOGIN_NOT_READONLY:DB_DATAWRITER")
    if int(identity.get("can_select") or 0) != 1:
        raise PermissionError("SQL_LOGIN_WITHOUT_SELECT")

    cursor.execute(
        "SELECT permission_name FROM fn_my_permissions(NULL, 'DATABASE')"
    )
    effective_permissions = {
        _norm(row[0]) for row in cursor.fetchall() if row and row[0]
    }
    dangerous = sorted(effective_permissions & DANGEROUS_DATABASE_PERMISSIONS)
    if dangerous:
        raise PermissionError(
            "SQL_LOGIN_NOT_READONLY:PERMISSIONS:" + ",".join(dangerous)
        )

    return {
        "database": identity.get("database_name"),
        "login": identity.get("login_name"),
        "user": identity.get("database_user"),
        "is_db_datareader": int(identity.get("is_db_datareader") or 0),
        "effective_permissions": sorted(effective_permissions),
    }


def _execute_readonly(
    server: dict[str, Any],
    sql: str,
    *,
    params: Iterable[Any] | None = None,
    max_rows: int = DEFAULT_ROWS,
) -> dict[str, Any]:
    checked_sql = _validate_readonly_sql(sql)
    max_rows = max(1, min(int(max_rows), MAX_ROWS_HARD))
    conn = None
    cursor = None
    try:
        conn = _connect(server)
        cursor = conn.cursor()
        sql_identity = _assert_connection_is_readonly(cursor)

        if params is None:
            cursor.execute(checked_sql)
        else:
            module_name = str(cursor.__class__.__module__).lower()
            executable_sql = (
                checked_sql.replace("%s", "?")
                if "pyodbc" in module_name
                else checked_sql
            )
            cursor.execute(executable_sql, tuple(params))

        columns = [str(c[0]) for c in (cursor.description or [])]
        fetched = cursor.fetchmany(max_rows + 1) if cursor.description else []
        truncated = len(fetched) > max_rows
        rows = fetched[:max_rows]
        preview = [
            {columns[i]: _serialize(value) for i, value in enumerate(row)}
            for row in rows
        ]
        return {
            "columns": columns,
            "rows": preview,
            "rows_returned": len(preview),
            "truncated": truncated,
            "max_rows": max_rows,
            "sql_identity": sql_identity,
        }
    finally:
        if conn is not None:
            try:
                conn.rollback()
            except Exception:
                pass
            try:
                conn.close()
            except Exception:
                pass


def _canonical_row(row: dict[str, Any], columns: list[str]) -> str:
    return json.dumps([row.get(c) for c in columns], ensure_ascii=False, sort_keys=False, default=str)


def _digest(rows: list[dict[str, Any]], columns: list[str]) -> str:
    payload = "\n".join(sorted(_canonical_row(r, columns) for r in rows))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


@mcp.tool()
async def who_am_i() -> dict[str, Any]:
    """Valida y muestra la identidad RBAC usada por el SQL Auditor."""
    return _authorize()


@mcp.tool()
async def list_sql_servers() -> list[dict[str, Any]]:
    """Lista servidores SQL activos visibles, sin secretos."""
    _authorize()
    return await _all_servers_masked()


@mcp.tool()
async def list_tables(server: str, schema: str = "dbo") -> dict[str, Any]:
    """Lista tablas y vistas de un servidor SQL sin modificar datos."""
    _authorize()
    info = await _resolve_server(server)
    sql = """
        SELECT TABLE_SCHEMA, TABLE_NAME, TABLE_TYPE
        FROM INFORMATION_SCHEMA.TABLES
        WHERE TABLE_SCHEMA = %s
        ORDER BY TABLE_NAME
    """
    result = _execute_readonly(info, sql, params=(schema,), max_rows=MAX_ROWS_HARD)
    return {"server": _masked_server(info), **result}


@mcp.tool()
async def describe_table(server: str, table: str, schema: str = "dbo") -> dict[str, Any]:
    """Obtiene columnas y tipos de una tabla/vista."""
    _authorize()
    info = await _resolve_server(server)
    sql = """
        SELECT
            COLUMN_NAME,
            DATA_TYPE,
            CHARACTER_MAXIMUM_LENGTH,
            NUMERIC_PRECISION,
            NUMERIC_SCALE,
            IS_NULLABLE,
            ORDINAL_POSITION
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s
        ORDER BY ORDINAL_POSITION
    """
    result = _execute_readonly(info, sql, params=(schema, table), max_rows=MAX_ROWS_HARD)
    return {"server": _masked_server(info), "table": f"{schema}.{table}", **result}


@mcp.tool()
async def search_columns(server: str, text: str, max_rows: int = 500) -> dict[str, Any]:
    """Busca columnas por nombre para descubrir el esquema de una base."""
    _authorize()
    info = await _resolve_server(server)
    sql = """
        SELECT TABLE_SCHEMA, TABLE_NAME, COLUMN_NAME, DATA_TYPE
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE LOWER(COLUMN_NAME) LIKE LOWER(%s)
        ORDER BY TABLE_SCHEMA, TABLE_NAME, ORDINAL_POSITION
    """
    pattern = f"%{str(text or '').strip()}%"
    result = _execute_readonly(info, sql, params=(pattern,), max_rows=max_rows)
    return {"server": _masked_server(info), **result}


@mcp.tool()
async def run_select(server: str, sql: str, max_rows: int = DEFAULT_ROWS) -> dict[str, Any]:
    """Ejecuta exclusivamente SELECT/WITH de una sola sentencia."""
    auth = _authorize()
    info = await _resolve_server(server)
    result = _execute_readonly(info, sql, max_rows=max_rows)
    return {
        "requester": {"email": auth["email"], "auth_source": auth["auth_source"]},
        "server": _masked_server(info),
        **result,
    }


@mcp.tool()
async def compare_readonly_queries(
    source_server: str,
    source_sql: str,
    hub_server: str,
    hub_sql: str,
    key_columns: list[str] | None = None,
    max_rows: int = MAX_ROWS_HARD,
) -> dict[str, Any]:
    """Ejecuta dos SELECT y concilia sus resultados sin modificar ninguna BD."""
    auth = _authorize()
    source = await _resolve_server(source_server)
    hub = await _resolve_server(hub_server)

    left = _execute_readonly(source, source_sql, max_rows=max_rows)
    right = _execute_readonly(hub, hub_sql, max_rows=max_rows)

    common_columns = [c for c in left["columns"] if c in set(right["columns"])]
    comparison: dict[str, Any] = {
        "source_rows": left["rows_returned"],
        "hub_rows": right["rows_returned"],
        "source_truncated": left["truncated"],
        "hub_truncated": right["truncated"],
        "columns_equal": left["columns"] == right["columns"],
        "common_columns": common_columns,
        "source_hash": _digest(left["rows"], left["columns"]),
        "hub_hash": _digest(right["rows"], right["columns"]),
    }

    keys = [str(k) for k in (key_columns or []) if str(k).strip()]
    if keys:
        missing_left = [k for k in keys if k not in left["columns"]]
        missing_right = [k for k in keys if k not in right["columns"]]
        if missing_left or missing_right:
            comparison["key_error"] = {
                "missing_in_source": missing_left,
                "missing_in_hub": missing_right,
            }
        else:
            def make_map(rows: list[dict[str, Any]]) -> dict[tuple[Any, ...], dict[str, Any]]:
                return {tuple(row.get(k) for k in keys): row for row in rows}

            lm = make_map(left["rows"])
            rm = make_map(right["rows"])
            only_source = sorted(set(lm) - set(rm), key=str)
            only_hub = sorted(set(rm) - set(lm), key=str)
            changed = []
            for key in sorted(set(lm) & set(rm), key=str):
                diffs = {
                    col: {"source": lm[key].get(col), "hub": rm[key].get(col)}
                    for col in common_columns
                    if lm[key].get(col) != rm[key].get(col)
                }
                if diffs:
                    changed.append({"key": list(key), "differences": diffs})

            comparison.update({
                "key_columns": keys,
                "only_in_source_count": len(only_source),
                "only_in_hub_count": len(only_hub),
                "changed_count": len(changed),
                "only_in_source": [list(k) for k in only_source[:200]],
                "only_in_hub": [list(k) for k in only_hub[:200]],
                "changed": changed[:200],
                "detail_truncated": (
                    len(only_source) > 200 or len(only_hub) > 200 or len(changed) > 200
                ),
            })

    comparison["equal"] = (
        not left["truncated"]
        and not right["truncated"]
        and left["columns"] == right["columns"]
        and comparison["source_hash"] == comparison["hub_hash"]
    )

    return {
        "requester": {"email": auth["email"], "auth_source": auth["auth_source"]},
        "source_server": _masked_server(source),
        "hub_server": _masked_server(hub),
        "comparison": comparison,
    }


if __name__ == "__main__":
    transport = os.environ.get("EDARSA_SQL_AUDITOR_TRANSPORT", "stdio")
    mcp.run(transport=transport)
