#!/usr/bin/env python3
"""Ejecutor controlado para la auditoria read-only de Cortes Z.

Solo se permite en Edarsahub_Desarrollo. Usa la excepcion temporal autorizada
para Preview/Development: carga /app/backend/.env mediante python-dotenv sin
imprimir valores. Exige el usuario configurado HRLectura y la base EDARSAHUB;
el runner canonico valida tambien la identidad SQL efectiva antes del SELECT.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

from dotenv import load_dotenv


ROOT = Path("/app")
BACKEND = ROOT / "backend"
ENV_FILE = BACKEND / ".env"
SQL_FILE = (
    BACKEND
    / "database"
    / "diagnostics"
    / "20260716_020_cortes_z_runtime_audit.sql"
)
RUNNER_REPORT_DEFAULT = Path("/var/tmp/edarsahub_cortes_z_runtime_audit")
REQUIRED_ENV = (
    "EDARSAHUB_SQL_HOST",
    "EDARSAHUB_SQL_DATABASE",
    "EDARSAHUB_SQL_USER",
    "EDARSAHUB_SQL_PASSWORD",
)


def _git(*args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def _validate_environment() -> None:
    if not ROOT.joinpath(".git").exists():
        raise RuntimeError("/app no es el repositorio esperado")

    branch = _git("branch", "--show-current")
    if branch != "Edarsahub_Desarrollo":
        raise RuntimeError(f"Rama no autorizada: {branch}")

    if not ENV_FILE.is_file():
        raise RuntimeError("No existe /app/backend/.env en Preview/Development")

    if not SQL_FILE.is_file():
        raise RuntimeError(f"No existe la auditoria SQL: {SQL_FILE}")

    load_dotenv(ENV_FILE, override=False)

    missing = [name for name in REQUIRED_ENV if not os.getenv(name)]
    if missing:
        raise RuntimeError(
            "Variables SQL canonicas ausentes: " + ", ".join(missing)
        )

    database = os.getenv("EDARSAHUB_SQL_DATABASE", "")
    user = os.getenv("EDARSAHUB_SQL_USER", "")

    if database.upper() != "EDARSAHUB":
        raise RuntimeError("EDARSAHUB_SQL_DATABASE no apunta a EDARSAHUB")

    if user != "HRLectura":
        raise RuntimeError(
            "EDARSAHUB_SQL_USER no es el login read-only autorizado HRLectura"
        )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output-dir",
        default=str(RUNNER_REPORT_DEFAULT),
        help="Directorio externo al repositorio para el reporte",
    )
    args = parser.parse_args()

    output_dir = Path(args.output_dir).resolve()
    if ROOT == output_dir or ROOT in output_dir.parents:
        raise RuntimeError("El reporte no puede escribirse dentro de /app")
    output_dir.mkdir(parents=True, exist_ok=True)

    _validate_environment()

    sys.path.insert(0, str(BACKEND))
    from tools import edarsahub_sql_runner as runner

    runner.REPORT_DIR = output_dir
    sys.argv = [
        "edarsahub_sql_runner.py",
        "--mode",
        "diagnostic",
        "--script",
        str(SQL_FILE),
    ]

    print("AUDIT_MODE=READ_ONLY")
    print("ENV_SOURCE=backend/.env_preview_development_exception")
    print("CONFIGURED_DATABASE=EDARSAHUB")
    print("CONFIGURED_LOGIN=HRLectura")
    print("SECRETS_PRINTED=0")
    return runner.main()


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
