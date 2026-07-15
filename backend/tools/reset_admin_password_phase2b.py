#!/usr/bin/env python3
"""
Controlled Phase 2B admin password reset and RBAC/menu validation.

This tool intentionally never prints or writes plaintext passwords or password
hashes. It prompts for the new password, updates only the approved SQL user,
then reuses the in-memory password to run the redacted RBAC/menu validator.
"""

from __future__ import annotations

import argparse
import datetime as dt
import getpass
import json
import os
import sys
from pathlib import Path
from typing import Any

from modules.auth.password_reset import (
    hash_password,
    validate_password_strength,
)
from core.connections.edarsahub_writer_connection import (
    SQLWriterIdentity,
    open_validated_writer_connection,
)
from tools import validate_rbac_menu_phase1 as rbac_validator


ROOT_DIR = Path(__file__).resolve().parents[2]
REPORT_DIR = ROOT_DIR / "docs" / "reports" / "rbac_phase1"



def fetch_user_metadata(
    conn,
    email: str,
) -> list[dict[str, Any]]:
    cur = conn.cursor()
    try:
        cur.execute(
            """
            SELECT
                u.UsuarioID,
                u.Email,
                u.Username,
                u.Activo,
                CASE
                    WHEN u.PasswordHashTexto IS NOT NULL
                     AND LTRIM(RTRIM(CONVERT(
                         NVARCHAR(MAX),
                         u.PasswordHashTexto
                     ))) <> ''
                    THEN 'SI'
                    ELSE 'NO'
                END AS tiene_password_hash,
                r.CodigoRol,
                r.NombreRol,
                ura.EsPrincipal,
                ura.Activo AS rol_asignacion_activa
            FROM dbo.Usuario_Catalogo u
            LEFT JOIN dbo.Usuario_RolesAsignacion ura
                ON ura.UsuarioID = u.UsuarioID
            LEFT JOIN dbo.Usuario_Roles r
                ON r.RolID = ura.RolID
            WHERE LOWER(u.Email) = LOWER(%s)
               OR LOWER(u.Username) = LOWER(%s)
            ORDER BY
                ISNULL(ura.EsPrincipal, 0) DESC,
                ISNULL(ura.Activo, 0) DESC,
                r.CodigoRol
            """,
            (email, email),
        )
        cols = [col[0] for col in cur.description]
        return [
            dict(zip(cols, row))
            for row in cur.fetchall()
        ]
    finally:
        close = getattr(cur, "close", None)
        if close:
            close()



def resolve_single_active_user(
    conn,
    email: str,
) -> tuple[int, list[dict[str, Any]]]:
    rows = fetch_user_metadata(conn, email)
    user_ids = {row.get("UsuarioID") for row in rows if row.get("UsuarioID") is not None}

    if len(user_ids) != 1:
        raise RuntimeError(
            f"Se esperaba exactamente un usuario para {email}; encontrados={len(user_ids)}"
        )

    active_rows = [row for row in rows if bool(row.get("Activo"))]
    if not active_rows:
        raise RuntimeError(f"El usuario {email} existe pero no esta activo.")

    if not any(row.get("tiene_password_hash") == "SI" for row in rows):
        raise RuntimeError(f"El usuario {email} no tiene hash de password configurado.")

    return int(next(iter(user_ids))), rows


def sanitized_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    safe_keys = [
        "UsuarioID",
        "Email",
        "Username",
        "Activo",
        "tiene_password_hash",
        "CodigoRol",
        "NombreRol",
        "EsPrincipal",
        "rol_asignacion_activa",
    ]
    return [{key: row.get(key) for key in safe_keys} for row in rows]


def write_reset_report(
    email: str,
    before_rows: list[dict[str, Any]],
    after_rows: list[dict[str, Any]],
    validation_md: Path | None,
    validation_summary: dict[str, Any] | None,
) -> Path:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = REPORT_DIR / f"{timestamp}_phase2b_admin_password_reset.md"

    lines = [
        "# Fase 2B admin password reset",
        "",
        f"- Fecha: {dt.datetime.now().isoformat(timespec='seconds')}",
        f"- Usuario objetivo: `{email}`",
        "- Password plano: no impreso, no guardado",
        "- Hash bcrypt: no impreso, no guardado en reporte",
        "- Tabla actualizada: `dbo.Usuario_Catalogo.PasswordHashTexto`",
        "",
        "## Estado previo",
        "",
        "```",
    ]
    lines.extend(f"  {row}" for row in sanitized_rows(before_rows))
    lines.extend(["```", "", "## Estado posterior", "", "```"])
    lines.extend(f"  {row}" for row in sanitized_rows(after_rows))
    lines.extend(["```", ""])

    if validation_summary:
        lines.extend(
            [
                "## Validacion RBAC/Menu",
                "",
                f"- OK/WARN/FAIL: {validation_summary.get('ok', 0)}/"
                f"{validation_summary.get('warn', 0)}/{validation_summary.get('fail', 0)}",
                f"- Reporte MD: `{validation_md}`",
                "",
            ]
        )

    report_path.write_text("\n".join(lines), encoding="utf-8")
    return report_path


def prompt_new_password(email: str) -> str:
    password = getpass.getpass(f"Nuevo password para {email}: ")
    confirm = getpass.getpass("Confirmar nuevo password: ")
    if password != confirm:
        raise RuntimeError("Los passwords no coinciden.")

    valid, message = validate_password_strength(password)
    if not valid:
        raise RuntimeError(message)

    return password


def confirm_target(email: str, usuario_id: int) -> None:
    print(
        f"Usuario objetivo: {email} "
        f"(UsuarioID={usuario_id})"
    )
    confirmation = input(
        "Escribe el email exacto para confirmar: "
    ).strip()

    if confirmation.casefold() != email.casefold():
        raise RuntimeError(
            "Confirmacion del usuario objetivo incorrecta."
        )


def update_password_and_audit(
    conn,
    usuario_id: int,
    email: str,
    password_hash: str,
    identity: SQLWriterIdentity,
) -> None:
    cur = conn.cursor()
    try:
        cur.execute(
            """
            UPDATE dbo.Usuario_Catalogo
            SET PasswordHashTexto = %s,
                UltimoCambioPassword = GETUTCDATE(),
                FechaModificacion = GETUTCDATE(),
                DebeCambiarPassword = 0,
                PasswordTemporal = 0
            WHERE UsuarioID = %s
              AND Activo = 1
            """,
            (password_hash, usuario_id),
        )

        if cur.rowcount != 1:
            raise RuntimeError(
                "La actualizacion no afecto exactamente "
                "un usuario activo."
            )

        detail = json.dumps(
            {
                "usuario_id_sql": usuario_id,
                "tool": "reset_admin_password_phase2b.py",
                "password_plaintext_stored": False,
                "hash_reported": False,
                "database_name": identity.database_name,
                "login_name": identity.login_name,
                "user_name": identity.user_name,
                "transactional_audit": True,
            },
            sort_keys=True,
        )

        cur.execute(
            """
            INSERT INTO dbo.Usuario_LogRecuperacion (
                Evento,
                Email,
                IPOrigen,
                UserAgent,
                Resultado,
                Detalle
            )
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (
                "admin_manual_password_reset_success",
                email,
                "local-cli",
                "reset_admin_password_phase2b.py",
                1,
                detail,
            ),
        )
    finally:
        close = getattr(cur, "close", None)
        if close:
            close()


def run_rbac_validation(email: str, password: str, base_url: str) -> tuple[Path, dict[str, Any]]:
    specs = [
        {
            "label": "Admin",
            "email": email,
            "password": password,
            "expect_global_access": True,
            "expected_min_permissions": 1,
        }
    ]
    results = [rbac_validator.validate_user(specs[0], base_url=base_url, timeout=20)]
    _, md_path = rbac_validator.write_reports(base_url, specs, results)
    summary = rbac_validator.summarize_results(results)
    return md_path, summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Reset controlado de password admin y validacion RBAC/menu Fase 2B."
    )
    parser.add_argument(
        "--email",
        required=True,
        help="Email exacto del usuario objetivo.",
    )
    parser.add_argument(
        "--base-url",
        default=(
            os.getenv("EDARSAHUB_API_URL")
            or os.getenv("REACT_APP_BACKEND_URL")
            or "http://localhost:8001"
        ),
    )
    parser.add_argument(
        "--i-understand-this-updates-sql",
        action="store_true",
        help="Confirmacion explicita requerida para actualizar Usuario_Catalogo.",
    )
    parser.add_argument(
        "--skip-validation",
        action="store_true",
        help="Actualiza password y auditoria SQL sin ejecutar validacion RBAC/Menu.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if not args.i_understand_this_updates_sql:
        print(
            "Bloqueado: agrega "
            "--i-understand-this-updates-sql "
            "para confirmar la escritura.",
            file=sys.stderr,
        )
        return 2

    password = ""
    conn = None
    writer_identity = None
    before_rows = []
    after_rows = []

    try:
        conn, writer_identity = (
            open_validated_writer_connection()
        )

        usuario_id, before_rows = (
            resolve_single_active_user(
                conn,
                args.email,
            )
        )

        confirm_target(args.email, usuario_id)
        password = prompt_new_password(args.email)
        new_hash = hash_password(password)

        update_password_and_audit(
            conn,
            usuario_id,
            args.email,
            new_hash,
            writer_identity,
        )

        after_rows = fetch_user_metadata(
            conn,
            args.email,
        )

        conn.commit()
    except Exception as exc:
        if conn is not None:
            try:
                conn.rollback()
            except Exception:
                pass

        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    finally:
        if conn is not None:
            conn.close()

    try:
        validation_md = None
        validation_summary = None

        if not args.skip_validation:
            validation_md, validation_summary = (
                run_rbac_validation(
                    args.email,
                    password,
                    args.base_url,
                )
            )

        reset_report = write_reset_report(
            args.email,
            before_rows,
            after_rows,
            validation_md,
            validation_summary,
        )

        print(
            "Password actualizado sin exponer secretos."
        )
        print(
            "Escritura y auditoria confirmadas "
            "en una sola transaccion."
        )
        print(
            "Identidad SQL: "
            f"database={writer_identity.database_name}, "
            f"login={writer_identity.login_name}, "
            f"user={writer_identity.user_name}"
        )
        print(f"Reporte reset: {reset_report}")

        if args.skip_validation:
            print(
                "Validacion RBAC/Menu omitida "
                "por --skip-validation."
            )
            return 0

        print(f"Reporte RBAC/Menu: {validation_md}")
        print(
            "Resultado Fase 2B RBAC/Menu: "
            f"OK={validation_summary.get('ok', 0)} "
            f"WARN={validation_summary.get('warn', 0)} "
            f"FAIL={validation_summary.get('fail', 0)}"
        )

        if (
            validation_summary.get("fail", 0)
            or validation_summary.get("warn", 0)
        ):
            return 1

        return 0
    except Exception as exc:
        print(
            "SQL confirmado, pero fallo la validacion "
            f"posterior: {exc}",
            file=sys.stderr,
        )
        return 1
    finally:
        password = ""


if __name__ == "__main__":
    raise SystemExit(main())
