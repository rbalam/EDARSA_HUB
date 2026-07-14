"""Endpoint temporal y fail-closed para auditar RBAC/menu de todos los usuarios.

No acepta SQL del cliente, no modifica datos y solo puede ejecutarlo un
SUPERADMIN efectivo. La conexion es exclusivamente HRLectura.
"""

from __future__ import annotations

import hashlib
import json
import logging
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.encoders import jsonable_encoder

from core.connections.edarsahub_readonly_repository import (
    validate_readonly_identity,
)
from core.connections.hrlectura_connection_factory import (
    build_hrlectura_connection_factory,
)
from core.rbac_helper_sql import es_superadmin
from core.security import get_current_user
from core.sql_first.connection_factory import (
    get_edarsahub_pymssql_connection,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/admin-sql/rbac-audit",
    tags=["Admin SQL RBAC Audit"],
)

BACKEND_DIR = Path(__file__).resolve().parents[2]
AUDIT_SQL_PATH = (
    BACKEND_DIR
    / "database"
    / "validation"
    / "20260713_017_rbac_menu_all_users_audit.sql"
)
EXPECTED_SQL_SHA256 = (
    "7df465ca125249b000b3e92f65f5477e2840aa3c763aea1a12f52202a68ce9bb"
)
REPO_ROOT = BACKEND_DIR.parent
REPORT_DIR = REPO_ROOT / ".runtime" / "rbac_audit"

_FORBIDDEN_SQL_PATTERNS = (
    r"\bALTER\b",
    r"\bCREATE\b",
    r"\bDELETE\b",
    r"\bDROP\b",
    r"\bEXEC(?:UTE)?\b",
    r"\bINSERT\b",
    r"\bMERGE\b",
    r"\bTRUNCATE\b",
    r"\bUPDATE\b",
)


def _strip_sql_comments(sql: str) -> str:
    without_blocks = re.sub(r"/\*[\s\S]*?\*/", " ", sql)
    return re.sub(r"--[^\r\n]*", " ", without_blocks)


def _validate_fixed_sql(sql: str) -> None:
    actual_sha = hashlib.sha256(sql.encode("utf-8")).hexdigest()
    if actual_sha != EXPECTED_SQL_SHA256:
        raise RuntimeError(
            "El SQL fijo de auditoria no coincide con el SHA aprobado"
        )

    inspected = _strip_sql_comments(sql)
    for pattern in _FORBIDDEN_SQL_PATTERNS:
        if re.search(pattern, inspected, flags=re.IGNORECASE):
            raise RuntimeError(
                f"SQL de auditoria bloqueado por patron: {pattern}"
            )


def _split_batches(sql: str) -> list[str]:
    batches = re.split(
        r"^\s*GO\s*$",
        sql,
        flags=re.IGNORECASE | re.MULTILINE,
    )
    return [batch.strip() for batch in batches if batch.strip()]


def _open_readonly_connection(profile: str):
    if profile != "default":
        raise RuntimeError("Perfil SQL read-only no autorizado")

    return get_edarsahub_pymssql_connection(
        timeout=60,
        login_timeout=15,
        autocommit=False,
    )


def _build_connection_factory():
    return build_hrlectura_connection_factory(
        connection_opener=_open_readonly_connection,
    )


def _require_effective_superadmin(
    current_user: dict[str, Any],
    connection: Any,
) -> None:
    try:
        claim_is_superadmin = es_superadmin(current_user)
    except Exception as exc:
        logger.exception("No se pudo resolver el rol canonico del actor")
        raise HTTPException(
            status_code=403,
            detail="No fue posible validar el rol SUPERADMIN",
        ) from exc

    if not claim_is_superadmin:
        raise HTTPException(
            status_code=403,
            detail="Se requiere rol SUPERADMIN",
        )

    email = str(current_user.get("email") or "").strip()
    username = str(current_user.get("username") or "").strip()

    if not email and not username:
        raise HTTPException(
            status_code=403,
            detail="Actor sin identidad verificable",
        )

    cursor = connection.cursor(as_dict=True)
    try:
        cursor.execute(
            """
        SELECT TOP 1
            u.UsuarioID,
            r.CodigoRol
        FROM dbo.Usuario_Catalogo AS u
        INNER JOIN dbo.Usuario_RolesAsignacion AS ura
            ON ura.UsuarioID = u.UsuarioID
           AND ISNULL(ura.Activo, 1) = 1
        INNER JOIN dbo.Usuario_Roles AS r
            ON r.RolID = ura.RolID
           AND ISNULL(r.Activo, 1) = 1
        WHERE ISNULL(u.Activo, 1) = 1
          AND (
                (NULLIF(%s, '') IS NOT NULL
                 AND LOWER(LTRIM(RTRIM(ISNULL(u.Email, '')))) =
                     LOWER(LTRIM(RTRIM(%s))))
             OR (NULLIF(%s, '') IS NOT NULL
                 AND LOWER(LTRIM(RTRIM(ISNULL(u.Username, '')))) =
                     LOWER(LTRIM(RTRIM(%s))))
          )
          AND UPPER(LTRIM(RTRIM(ISNULL(r.CodigoRol, '')))) =
              'SUPERADMIN'
        """,
            (email, email, username, username),
        )

        if cursor.fetchone() is None:
            raise HTTPException(
                status_code=403,
                detail="El actor no tiene SUPERADMIN activo en SQL",
            )
    finally:
        cursor.close()


def _execute_batches(connection: Any, sql: str) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []

    for batch_number, batch in enumerate(_split_batches(sql), start=1):
        cursor = connection.cursor(as_dict=True)
        try:
            cursor.execute(batch)

            if cursor.description:
                rows = cursor.fetchall()
                results.append(
                    {
                        "batch": batch_number,
                        "type": "resultset",
                        "row_count": len(rows),
                        "rows": rows,
                    }
                )
            else:
                results.append(
                    {
                        "batch": batch_number,
                        "type": "command",
                        "row_count": int(cursor.rowcount or 0),
                        "rows": [],
                    }
                )
        finally:
            cursor.close()

    return results


def _write_report(payload: dict[str, Any]) -> Path:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    report_path = REPORT_DIR / f"rbac_menu_all_users_{timestamp}.json"
    report_path.write_text(
        json.dumps(
            jsonable_encoder(payload),
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    return report_path


@router.post("/users/execute")
def execute_all_users_rbac_audit(
    current_user: dict[str, Any] = Depends(get_current_user),
):
    """Ejecuta la auditoria fija RBAC/menu sin cambios de datos."""

    if not AUDIT_SQL_PATH.is_file():
        raise HTTPException(
            status_code=500,
            detail="No existe el SQL fijo de auditoria",
        )

    sql = AUDIT_SQL_PATH.read_text(encoding="utf-8")

    try:
        _validate_fixed_sql(sql)
    except Exception as exc:
        logger.exception("SQL fijo RBAC invalido")
        raise HTTPException(
            status_code=500,
            detail="SQL fijo de auditoria invalido",
        ) from exc

    connection = None
    payload: dict[str, Any] = {
        "ok": False,
        "audited_at_utc": datetime.now(timezone.utc).isoformat(),
        "sql_sha256": EXPECTED_SQL_SHA256,
        "actor_email": str(current_user.get("email") or ""),
        "actor_username": str(current_user.get("username") or ""),
    }

    try:
        connection = _build_connection_factory()()
        identity = validate_readonly_identity(connection)
        _require_effective_superadmin(current_user, connection)
        results = _execute_batches(connection, sql)
        connection.rollback()

        payload.update(
            {
                "ok": True,
                "identity": identity,
                "batch_count": len(results),
                "resultsets": results,
            }
        )
        report_path = _write_report(payload)

        return {
            "ok": True,
            "report_path": str(report_path),
            "batch_count": len(results),
            "row_counts": [
                {
                    "batch": item["batch"],
                    "row_count": item["row_count"],
                }
                for item in results
            ],
            "identity": identity,
        }

    except HTTPException:
        if connection is not None:
            connection.rollback()
        raise
    except Exception as exc:
        if connection is not None:
            connection.rollback()

        payload.update(
            {
                "error_type": type(exc).__name__,
                "error": str(exc),
            }
        )
        report_path = _write_report(payload)
        logger.exception("Fallo la auditoria RBAC/menu de usuarios")

        raise HTTPException(
            status_code=500,
            detail={
                "message": "Fallo la auditoria RBAC/menu",
                "report_path": str(report_path),
                "error_type": type(exc).__name__,
            },
        ) from exc
    finally:
        if connection is not None:
            connection.close()

# ============================================================================
# AUDITORIA ESTRUCTURAL RBAC 018
# Endpoint fijo, read-only, SUPERADMIN y protegido por SHA.
# No altera el endpoint histórico /users/execute.
# ============================================================================

SCHEMA_AUDIT_SQL_PATH = (
    BACKEND_DIR
    / "database"
    / "validation"
    / "20260713_018_rbac_schema_convergence_audit.sql"
)
SCHEMA_EXPECTED_SQL_SHA256 = (
    "9eb2a1ebf2cc038c0f6924e890f9e707c50aa0a99da8982dc34b87512ae23604"
)
SCHEMA_EXPECTED_RESULTSETS = 9
SCHEMA_RESULTSET_NAMES = (
    "identity",
    "objects",
    "columns",
    "keys",
    "foreign_keys",
    "indexes",
    "triggers",
    "dependencies",
    "table_sizes",
)


def _validate_schema_sql(raw_sql: bytes) -> str:
    actual_sha = hashlib.sha256(raw_sql).hexdigest()

    if actual_sha != SCHEMA_EXPECTED_SQL_SHA256:
        raise RuntimeError(
            "El SQL fijo 018 no coincide con el SHA aprobado"
        )

    try:
        sql = raw_sql.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise RuntimeError(
            "El SQL fijo 018 no es UTF-8 válido"
        ) from exc

    inspected = _strip_sql_comments(sql)

    for pattern in _FORBIDDEN_SQL_PATTERNS:
        if re.search(pattern, inspected, flags=re.IGNORECASE):
            raise RuntimeError(
                "SQL 018 bloqueado por patrón prohibido: "
                f"{pattern}"
            )

    return sql


def _execute_schema_resultsets(
    connection: Any,
    sql: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], int]:
    resultsets: list[dict[str, Any]] = []
    command_sets: list[dict[str, Any]] = []
    cursor = connection.cursor(as_dict=True)
    iterations = 0

    try:
        cursor.execute(sql)

        while True:
            iterations += 1

            if iterations > 100:
                raise RuntimeError(
                    "Se excedió el máximo de resultados SQL permitido"
                )

            if cursor.description:
                columns = [
                    str(column[0])
                    for column in cursor.description
                ]
                rows = cursor.fetchall()

                resultsets.append(
                    {
                        "resultset_number": len(resultsets) + 1,
                        "columns": columns,
                        "row_count": len(rows),
                        "rows": rows,
                    }
                )
            else:
                command_sets.append(
                    {
                        "sequence": (
                            len(resultsets)
                            + len(command_sets)
                            + 1
                        ),
                        "row_count": int(cursor.rowcount or 0),
                    }
                )

            has_next = cursor.nextset()

            if not has_next:
                break
    finally:
        cursor.close()

    if len(resultsets) != SCHEMA_EXPECTED_RESULTSETS:
        raise RuntimeError(
            "Cantidad inesperada de resultsets para SQL 018: "
            f"expected={SCHEMA_EXPECTED_RESULTSETS} "
            f"actual={len(resultsets)}"
        )

    for index, name in enumerate(SCHEMA_RESULTSET_NAMES):
        resultsets[index]["name"] = name

    identity_rows = resultsets[0]["rows"]

    if len(identity_rows) != 1:
        raise RuntimeError(
            "El resultset identity no contiene exactamente una fila"
        )

    identity = identity_rows[0]

    expected_identity = {
        "database_name": "EDARSAHUB",
        "login_name": "HRLectura",
        "database_user": "HRLectura",
    }

    for field, expected_value in expected_identity.items():
        actual_value = identity.get(field)

        if actual_value != expected_value:
            raise RuntimeError(
                f"Identidad inválida para {field}: "
                f"expected={expected_value!r} "
                f"actual={actual_value!r}"
            )

    return resultsets, command_sets, iterations


def _write_schema_report(
    payload: dict[str, Any],
) -> tuple[Path, str]:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime(
        "%Y%m%dT%H%M%SZ"
    )
    report_path = (
        REPORT_DIR
        / f"rbac_schema_convergence_{timestamp}.json"
    )
    temporary_path = report_path.with_suffix(".json.tmp")

    encoded = json.dumps(
        jsonable_encoder(payload),
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    )

    temporary_path.write_text(
        encoded,
        encoding="utf-8",
    )
    temporary_path.replace(report_path)

    report_sha = hashlib.sha256(
        encoded.encode("utf-8")
    ).hexdigest()

    return report_path, report_sha


@router.post("/schema/execute")
def execute_schema_convergence_audit(
    current_user: dict[str, Any] = Depends(get_current_user),
):
    """Ejecuta la auditoría estructural RBAC 018 sin modificar datos."""

    if not SCHEMA_AUDIT_SQL_PATH.is_file():
        raise HTTPException(
            status_code=500,
            detail="No existe el SQL fijo de auditoría 018",
        )

    try:
        raw_sql = SCHEMA_AUDIT_SQL_PATH.read_bytes()
        sql = _validate_schema_sql(raw_sql)
    except Exception as exc:
        logger.exception("SQL fijo RBAC 018 inválido")
        raise HTTPException(
            status_code=500,
            detail="SQL fijo de auditoría 018 inválido",
        ) from exc

    connection = None
    payload: dict[str, Any] = {
        "ok": False,
        "audit_type": "rbac_schema_convergence",
        "audited_at_utc": datetime.now(
            timezone.utc
        ).isoformat(),
        "sql_path": str(SCHEMA_AUDIT_SQL_PATH),
        "sql_sha256": SCHEMA_EXPECTED_SQL_SHA256,
        "actor_email": str(
            current_user.get("email") or ""
        ),
        "actor_username": str(
            current_user.get("username") or ""
        ),
    }

    try:
        connection = _build_connection_factory()()

        identity = validate_readonly_identity(connection)
        _require_effective_superadmin(
            current_user,
            connection,
        )

        (
            resultsets,
            command_sets,
            nextset_iterations,
        ) = _execute_schema_resultsets(
            connection,
            sql,
        )

        connection.rollback()

        payload.update(
            {
                "ok": True,
                "identity": identity,
                "expected_resultsets": (
                    SCHEMA_EXPECTED_RESULTSETS
                ),
                "resultset_count": len(resultsets),
                "command_set_count": len(command_sets),
                "nextset_iterations": nextset_iterations,
                "resultsets": resultsets,
                "command_sets": command_sets,
            }
        )

        report_path, report_sha = _write_schema_report(
            payload
        )

        return {
            "ok": True,
            "report_path": str(report_path),
            "report_sha256": report_sha,
            "resultset_count": len(resultsets),
            "command_set_count": len(command_sets),
            "nextset_iterations": nextset_iterations,
            "row_counts": [
                {
                    "resultset_number": item[
                        "resultset_number"
                    ],
                    "name": item["name"],
                    "row_count": item["row_count"],
                }
                for item in resultsets
            ],
            "identity": identity,
        }

    except HTTPException:
        if connection is not None:
            connection.rollback()
        raise

    except Exception as exc:
        if connection is not None:
            connection.rollback()

        payload.update(
            {
                "error_type": type(exc).__name__,
                "error": str(exc),
            }
        )

        report_path, report_sha = _write_schema_report(
            payload
        )

        logger.exception(
            "Falló la auditoría estructural RBAC 018"
        )

        raise HTTPException(
            status_code=500,
            detail={
                "message": (
                    "Falló la auditoría estructural RBAC 018"
                ),
                "report_path": str(report_path),
                "report_sha256": report_sha,
                "error_type": type(exc).__name__,
            },
        ) from exc

    finally:
        if connection is not None:
            connection.close()

# ============================================================================
# AUDITORIA RBAC 019 SECCIONADA
# Nueve llamadas independientes, fijas, read-only y protegidas por SHA.
# ============================================================================

SECTIONED_SCHEMA_AUDIT_SQL_PATH = (
    BACKEND_DIR
    / "database"
    / "validation"
    / "20260714_019_rbac_schema_convergence_sectioned_audit.sql"
)
SECTIONED_SCHEMA_EXPECTED_SQL_SHA256 = (
    "f3785feabf73aef0a88f430b66b8aacefb397959275cb12d46f2b8b1aff64f0e"
)
SECTIONED_SCHEMA_SECTION_COUNT = 9
SECTIONED_SCHEMA_NAMES = (
    "identity",
    "objects",
    "columns",
    "keys",
    "foreign_keys",
    "indexes",
    "triggers",
    "dependencies",
    "table_sizes",
)


def _write_schema_section_report(
    payload: dict[str, Any],
    section_number: int,
) -> tuple[Path, str]:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime(
        "%Y%m%dT%H%M%SZ"
    )

    report_path = (
        REPORT_DIR
        / (
            "rbac_schema_section_"
            f"{section_number:02d}_{timestamp}.json"
        )
    )
    temporary_path = report_path.with_suffix(".json.tmp")

    encoded = json.dumps(
        jsonable_encoder(payload),
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    )

    temporary_path.write_text(
        encoded,
        encoding="utf-8",
    )
    temporary_path.replace(report_path)

    report_sha = hashlib.sha256(
        encoded.encode("utf-8")
    ).hexdigest()

    return report_path, report_sha


@router.post("/schema/sections/{section_number}/execute")
def execute_schema_section_audit(
    section_number: int,
    current_user: dict[str, Any] = Depends(get_current_user),
):
    """Ejecuta una sección fija de la auditoría estructural RBAC."""

    if not 1 <= section_number <= SECTIONED_SCHEMA_SECTION_COUNT:
        raise HTTPException(
            status_code=400,
            detail=(
                "section_number debe estar entre 1 y "
                f"{SECTIONED_SCHEMA_SECTION_COUNT}"
            ),
        )

    if not SECTIONED_SCHEMA_AUDIT_SQL_PATH.is_file():
        raise HTTPException(
            status_code=500,
            detail="No existe el SQL fijo de auditoría 019",
        )

    raw_sql = SECTIONED_SCHEMA_AUDIT_SQL_PATH.read_bytes()
    actual_sha = hashlib.sha256(raw_sql).hexdigest()

    if actual_sha != SECTIONED_SCHEMA_EXPECTED_SQL_SHA256:
        raise HTTPException(
            status_code=500,
            detail="SQL fijo de auditoría 019 inválido",
        )

    try:
        sql = raw_sql.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise HTTPException(
            status_code=500,
            detail="SQL fijo de auditoría 019 no es UTF-8",
        ) from exc

    inspected = _strip_sql_comments(sql)

    for pattern in _FORBIDDEN_SQL_PATTERNS:
        if re.search(pattern, inspected, flags=re.IGNORECASE):
            raise HTTPException(
                status_code=500,
                detail="SQL fijo de auditoría 019 bloqueado",
            )

    batches = _split_batches(sql)

    if len(batches) != SECTIONED_SCHEMA_SECTION_COUNT:
        raise HTTPException(
            status_code=500,
            detail="Cantidad inválida de secciones SQL 019",
        )

    section_name = SECTIONED_SCHEMA_NAMES[
        section_number - 1
    ]
    batch = batches[section_number - 1]

    connection = None
    cursor = None

    payload: dict[str, Any] = {
        "ok": False,
        "audit_type": "rbac_schema_section",
        "section_number": section_number,
        "section_name": section_name,
        "audited_at_utc": datetime.now(
            timezone.utc
        ).isoformat(),
        "sql_sha256": SECTIONED_SCHEMA_EXPECTED_SQL_SHA256,
        "actor_email": str(
            current_user.get("email") or ""
        ),
        "actor_username": str(
            current_user.get("username") or ""
        ),
    }

    try:
        connection = _build_connection_factory()()
        identity = validate_readonly_identity(connection)

        _require_effective_superadmin(
            current_user,
            connection,
        )

        cursor = connection.cursor(as_dict=True)
        cursor.execute(batch)

        if not cursor.description:
            raise RuntimeError(
                "La sección SQL no produjo un resultset"
            )

        columns = [
            str(column[0])
            for column in cursor.description
        ]
        rows = cursor.fetchall()

        connection.rollback()

        if section_number == 1:
            if len(rows) != 1:
                raise RuntimeError(
                    "La sección identity no produjo una fila"
                )

            identity_row = rows[0]

            for field, expected in {
                "database_name": "EDARSAHUB",
                "login_name": "HRLectura",
                "database_user": "HRLectura",
            }.items():
                if identity_row.get(field) != expected:
                    raise RuntimeError(
                        f"Identidad inválida para {field}"
                    )

        payload.update(
            {
                "ok": True,
                "identity": identity,
                "resultset": {
                    "columns": columns,
                    "row_count": len(rows),
                    "rows": rows,
                },
            }
        )

        report_path, report_sha = _write_schema_section_report(
            payload,
            section_number,
        )

        return {
            "ok": True,
            "section_number": section_number,
            "section_name": section_name,
            "row_count": len(rows),
            "report_path": str(report_path),
            "report_sha256": report_sha,
            "identity": identity,
        }

    except HTTPException:
        if connection is not None:
            connection.rollback()
        raise

    except Exception as exc:
        if connection is not None:
            connection.rollback()

        payload.update(
            {
                "error_type": type(exc).__name__,
                "error": str(exc),
            }
        )

        report_path, report_sha = _write_schema_section_report(
            payload,
            section_number,
        )

        logger.exception(
            "Falló sección %s de auditoría RBAC 019",
            section_number,
        )

        raise HTTPException(
            status_code=500,
            detail={
                "message": "Falló sección de auditoría RBAC 019",
                "section_number": section_number,
                "report_path": str(report_path),
                "report_sha256": report_sha,
                "error_type": type(exc).__name__,
            },
        ) from exc

    finally:
        if cursor is not None:
            cursor.close()

        if connection is not None:
            connection.close()

