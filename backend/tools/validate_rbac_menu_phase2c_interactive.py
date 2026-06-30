#!/usr/bin/env python3
"""
Interactive Phase 2C RBAC/Menu API validator.

This wrapper intentionally never stores or prints passwords. It prompts for
candidate user passwords in memory, skips blank entries, and reuses the
existing redacted RBAC/menu validator.
"""

from __future__ import annotations

import argparse
import getpass
import os
import sys
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR / "backend") not in sys.path:
    sys.path.insert(0, str(ROOT_DIR / "backend"))

from tools import validate_rbac_menu_phase1 as rbac_validator


DEFAULT_CANDIDATES = [
    {
        "label": "SuperAdministrador",
        "email": "qa.superadmin@edarsa.com",
        "expect_global_access": True,
        "expected_min_permissions": 1,
    },
    {
        "label": "Administrador",
        "email": "carlosruz@edarsa.com.mx",
        "expected_min_permissions": 1,
    },
    {
        "label": "Supervisor",
        "email": "noxte@alpyc.com",
        "expected_min_permissions": 1,
        "expected_disabled_menus": ["catalogo_sql", "explorador_bd", "servidores"],
    },
    {
        "label": "Operador",
        "email": "almacen@cienfuegos.mx",
        "expected_min_permissions": 1,
        "expected_enabled_menus": ["mis_tareas"],
        "expected_disabled_menus": ["catalogo_sql", "explorador_bd", "servidores", "usuarios"],
    },
]


def parse_user_arg(raw: str) -> dict[str, Any]:
    parts = raw.split(":", 2)
    if len(parts) < 2:
        raise argparse.ArgumentTypeError(
            "--user debe tener formato Label:email[:expected_min_permissions]"
        )

    spec: dict[str, Any] = {
        "label": parts[0].strip(),
        "email": parts[1].strip(),
        "expected_min_permissions": 1,
    }
    if len(parts) == 3 and parts[2].strip():
        spec["expected_min_permissions"] = int(parts[2])

    if not spec["label"] or not spec["email"]:
        raise argparse.ArgumentTypeError("Label y email son requeridos.")

    return spec


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Valida RBAC/Menu Fase 2C pidiendo passwords en memoria."
    )
    parser.add_argument(
        "--base-url",
        default=(
            os.getenv("EDARSAHUB_API_URL")
            or os.getenv("REACT_APP_BACKEND_URL")
            or "http://localhost:8001"
        ),
        help="Base URL del backend. Acepta host raiz o URL terminada en /api.",
    )
    parser.add_argument(
        "--user",
        action="append",
        type=parse_user_arg,
        help="Usuario a validar: Label:email[:min_permissions]. Repetible.",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=20,
        help="Timeout HTTP por request, en segundos.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Regresa exit code 1 si hay WARN ademas de FAIL.",
    )
    return parser.parse_args()


def collect_specs(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    specs = []
    for candidate in candidates:
        email = candidate["email"]
        password = getpass.getpass(
            f"Password para {candidate['label']} ({email}); Enter para omitir: "
        )
        if not password:
            continue

        spec = dict(candidate)
        spec["password"] = password
        specs.append(spec)

    return specs


def main() -> int:
    args = parse_args()
    candidates = args.user or DEFAULT_CANDIDATES
    specs = collect_specs(candidates)

    if not specs:
        print("No se capturo ningun password; no hay validacion API que ejecutar.")
        return 2

    results = []
    for spec in specs:
        print(f"Validando {spec['label']} ({spec['email']})...")
        results.append(
            rbac_validator.validate_user(spec, args.base_url, timeout=args.timeout)
        )

    _, md_path = rbac_validator.write_reports(args.base_url, specs, results)
    summary = rbac_validator.summarize_results(results)

    print(
        "Resultado Fase 2C RBAC/Menu API: "
        f"OK={summary['ok']} WARN={summary['warn']} FAIL={summary['fail']}"
    )
    print(f"Reporte MD: {md_path}")

    for spec in specs:
        spec["password"] = ""

    if summary["has_failures"]:
        return 1
    if args.strict and summary["has_warnings"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
