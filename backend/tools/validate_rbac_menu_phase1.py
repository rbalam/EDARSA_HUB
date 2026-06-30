#!/usr/bin/env python3
"""
Phase 1 RBAC/Menu API validator for EDARSAHUB.

This tool is intentionally read-only. It logs in with operator-provided test
users, calls the canonical RBAC endpoints, and writes a redacted validation
report under docs/reports/rbac_phase1/.
"""

from __future__ import annotations

import argparse
import datetime as dt
import http.cookiejar
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parents[2]
REPORT_DIR = ROOT_DIR / "docs" / "reports" / "rbac_phase1"

DEFAULT_MENU_KEYS = [
    "mis_tareas",
    "tablero_ejecutivo",
    "comercial",
    "compras",
    "operaciones",
    "finanzas",
    "produccion",
    "recursos_humanos",
    "reportes_bi",
    "catalogos",
    "centro_control",
    "servidores",
    "programacion",
    "automatizaciones",
    "asignaciones",
    "catalogo_sql",
    "explorador_bd",
    "alertas",
    "usuarios",
]

ROLE_ENV_SPECS = [
    ("SuperAdministrador", "TEST_SUPERADMIN_EMAIL", "TEST_SUPERADMIN_PASSWORD"),
    ("Administrador", "TEST_ADMIN_EMAIL", "TEST_ADMIN_PASSWORD"),
    ("Supervisor", "TEST_SUPERVISOR_EMAIL", "TEST_SUPERVISOR_PASSWORD"),
    ("UsuarioLimitado", "TEST_LIMITED_EMAIL", "TEST_LIMITED_PASSWORD"),
    ("UsuarioSinPermiso", "TEST_NOPERM_EMAIL", "TEST_NOPERM_PASSWORD"),
]


class ApiClient:
    def __init__(self, base_url: str, timeout: int) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.cookie_jar = http.cookiejar.CookieJar()
        self.opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(self.cookie_jar)
        )

    def api_url(self, path: str) -> str:
        if not path.startswith("/"):
            path = f"/{path}"

        if path.startswith("/api/") and self.base_url.endswith("/api"):
            return f"{self.base_url}{path[4:]}"

        return f"{self.base_url}{path}"

    def request_json(
        self,
        method: str,
        path: str,
        payload: dict[str, Any] | None = None,
        token: str | None = None,
    ) -> tuple[int, dict[str, Any]]:
        data = None
        headers = {"Accept": "application/json"}

        if payload is not None:
            data = json.dumps(payload).encode("utf-8")
            headers["Content-Type"] = "application/json"

        if token:
            headers["Authorization"] = f"Bearer {token}"

        request = urllib.request.Request(
            self.api_url(path),
            data=data,
            headers=headers,
            method=method,
        )

        try:
            with self.opener.open(request, timeout=self.timeout) as response:
                raw = response.read().decode("utf-8")
                return response.status, parse_json_body(raw)
        except urllib.error.HTTPError as exc:
            raw = exc.read().decode("utf-8", errors="replace")
            return exc.code, parse_json_body(raw)
        except urllib.error.URLError as exc:
            return 0, {"error": str(exc.reason)}


def parse_json_body(raw: str) -> dict[str, Any]:
    if not raw.strip():
        return {}

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return {"raw": raw[:1000]}

    if isinstance(parsed, dict):
        return parsed

    return {"value": parsed}


def load_user_specs(args: argparse.Namespace) -> list[dict[str, Any]]:
    raw_json = args.users_json or os.getenv("RBAC_PHASE1_USERS_JSON")

    if args.users_file:
        raw_json = Path(args.users_file).read_text(encoding="utf-8")

    if raw_json:
        users = json.loads(raw_json)
        if not isinstance(users, list):
            raise RuntimeError("RBAC_PHASE1_USERS_JSON debe ser un arreglo JSON.")
        return [normalize_user_spec(item) for item in users]

    users = []
    for label, email_env, password_env in ROLE_ENV_SPECS:
        email = os.getenv(email_env)
        password = os.getenv(password_env)
        if email and password:
            users.append(
                normalize_user_spec(
                    {
                        "label": label,
                        "email": email,
                        "password": password,
                    }
                )
            )

    if args.use_default_admin and not users:
        default_admin_password = os.getenv("EDARSAHUB_DEFAULT_ADMIN_PASSWORD")
        if not default_admin_password:
            raise RuntimeError(
                "EDARSAHUB_DEFAULT_ADMIN_PASSWORD es requerido con --use-default-admin."
            )

        users.append(
            normalize_user_spec(
                {
                    "label": "DefaultAdmin",
                    "email": os.getenv(
                        "EDARSAHUB_DEFAULT_ADMIN_EMAIL",
                        "admin@edarsa.com",
                    ),
                    "password": default_admin_password,
                    "expected_min_permissions": 1,
                }
            )
        )

    return users


def normalize_user_spec(spec: Any) -> dict[str, Any]:
    if not isinstance(spec, dict):
        raise RuntimeError("Cada usuario de prueba debe ser un objeto JSON.")

    email = str(spec.get("email") or "").strip()
    password = str(spec.get("password") or "")
    label = str(spec.get("label") or email or "usuario").strip()

    if not email or not password:
        raise RuntimeError(
            f"El usuario de prueba '{label}' requiere email y password."
        )

    normalized = dict(spec)
    normalized["email"] = email
    normalized["password"] = password
    normalized["label"] = label
    return normalized


def sorted_enabled_flags(flags: dict[str, Any]) -> tuple[list[str], list[str]]:
    enabled = sorted(key for key, value in flags.items() if bool(value))
    disabled = sorted(key for key, value in flags.items() if not bool(value))
    return enabled, disabled


def coerce_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def validate_expected_items(
    label: str,
    actual: set[str],
    expected: Any,
    failures: list[str],
) -> None:
    if expected is None:
        return

    expected_set = {str(item) for item in coerce_list(expected)}
    missing = sorted(expected_set - actual)
    if missing:
        failures.append(f"{label} faltantes: {', '.join(missing)}")


def analyze_spec(
    spec: dict[str, Any],
    effective_status: int,
    effective: dict[str, Any],
    menu_status: int,
    menu: dict[str, Any],
) -> dict[str, Any]:
    failures: list[str] = []
    risks: list[str] = []

    if effective_status != 200:
        failures.append(f"effective-permissions HTTP {effective_status}")
    if menu_status != 200:
        failures.append(f"menu-permissions HTTP {menu_status}")

    permissions_flat = effective.get("permissions_flat")
    if not isinstance(permissions_flat, list):
        failures.append("effective.permissions_flat no es lista")
        permissions_flat = []

    roles = effective.get("roles")
    if not isinstance(roles, list):
        failures.append("effective.roles no es lista")
        roles = []

    scope = effective.get("scope")
    if not isinstance(scope, dict):
        failures.append("effective.scope no es objeto")
        scope = {}

    menu_flags = menu.get("permisos_modulos")
    if not isinstance(menu_flags, dict):
        failures.append("menu.permisos_modulos no es objeto")
        menu_flags = {}

    source = effective.get("source") or menu.get("source")
    if source != "RBAC_SQL_CANONICAL_WITH_LEGACY_COMPAT":
        risks.append(f"fuente inesperada: {source!r}")

    tiene_acceso_global = bool(
        scope.get("tiene_acceso_global") or menu.get("tiene_acceso_global")
    )
    permissions_count = len(permissions_flat)

    if not tiene_acceso_global and permissions_count == 0:
        risks.append("usuario sin acceso global y sin permisos efectivos")

    expected_global = spec.get("expect_global_access")
    if expected_global is not None and bool(expected_global) != tiene_acceso_global:
        failures.append(
            "expect_global_access no coincide "
            f"(esperado={bool(expected_global)}, real={tiene_acceso_global})"
        )

    expected_min_permissions = spec.get("expected_min_permissions")
    if expected_min_permissions is not None:
        expected_min = int(expected_min_permissions)
        if permissions_count < expected_min:
            failures.append(
                "permisos efectivos por debajo del minimo "
                f"(esperado>={expected_min}, real={permissions_count})"
            )

    enabled, disabled = sorted_enabled_flags(menu_flags)
    enabled_set = set(enabled)
    disabled_set = set(disabled)

    validate_expected_items(
        "menus habilitados",
        enabled_set,
        spec.get("expected_enabled_menus"),
        failures,
    )
    validate_expected_items(
        "menus deshabilitados",
        disabled_set,
        spec.get("expected_disabled_menus"),
        failures,
    )

    menu_keys = set(menu_flags.keys())
    missing_default_keys = sorted(set(DEFAULT_MENU_KEYS) - menu_keys)
    if missing_default_keys:
        risks.append(
            "menu.permisos_modulos no incluye llaves esperadas: "
            + ", ".join(missing_default_keys)
        )

    if "mis_tareas" in menu_flags and not bool(menu_flags["mis_tareas"]):
        failures.append("mis_tareas debe estar habilitado para todo usuario autenticado")

    role_tokens = set()
    for role in roles:
        if not isinstance(role, dict):
            continue
        for key in ("codigo", "nombre"):
            value = role.get(key)
            if value:
                role_tokens.add(str(value).lower())

    expected_role = spec.get("expected_role")
    if expected_role and str(expected_role).lower() not in role_tokens:
        risks.append(
            "rol esperado no aparece en roles efectivos: "
            f"{expected_role!r}"
        )

    return {
        "label": spec["label"],
        "email": spec["email"],
        "status": "FAIL" if failures else "WARN" if risks else "OK",
        "failures": failures,
        "risks": risks,
        "source": source,
        "role_legacy": effective.get("role_legacy") or menu.get("role_legacy"),
        "roles": roles,
        "permissions_flat_count": permissions_count,
        "permissions_flat_sample": sorted(str(item) for item in permissions_flat)[:30],
        "scope": {
            "tiene_acceso_global": tiene_acceso_global,
            "fuente_acceso": scope.get("fuente_acceso") or menu.get("fuente_acceso"),
            "empresas_count": scope.get("empresas_count") or menu.get("empresas_count"),
            "servers_count": scope.get("servers_count") or menu.get("servers_count"),
        },
        "menu_enabled": enabled,
        "menu_disabled": disabled,
        "http": {
            "effective_permissions": effective_status,
            "menu_permissions": menu_status,
        },
    }


def validate_user(
    spec: dict[str, Any],
    base_url: str,
    timeout: int,
) -> dict[str, Any]:
    client = ApiClient(base_url=base_url, timeout=timeout)

    login_status, login_body = client.request_json(
        "POST",
        "/api/auth/login",
        payload={"email": spec["email"], "password": spec["password"]},
    )

    if login_status != 200:
        return {
            "label": spec["label"],
            "email": spec["email"],
            "status": "FAIL",
            "failures": [f"login HTTP {login_status}"],
            "risks": [],
            "http": {"login": login_status},
        }

    token = login_body.get("token") or login_body.get("access_token")
    if not token:
        return {
            "label": spec["label"],
            "email": spec["email"],
            "status": "FAIL",
            "failures": ["login no devolvio token"],
            "risks": [],
            "http": {"login": login_status},
        }

    effective_status, effective = client.request_json(
        "GET",
        "/api/auth/me/effective-permissions",
        token=str(token),
    )
    menu_status, menu = client.request_json(
        "GET",
        "/api/auth/me/menu-permissions",
        token=str(token),
    )

    result = analyze_spec(
        spec=spec,
        effective_status=effective_status,
        effective=effective,
        menu_status=menu_status,
        menu=menu,
    )
    result["http"]["login"] = login_status
    return result


def redact_specs(specs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    safe_specs = []
    for spec in specs:
        safe = {key: value for key, value in spec.items() if key != "password"}
        safe["password"] = "***"
        safe_specs.append(safe)
    return safe_specs


def write_reports(
    base_url: str,
    specs: list[dict[str, Any]],
    results: list[dict[str, Any]],
) -> tuple[Path, Path]:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")

    payload = {
        "generated_at": dt.datetime.now().isoformat(timespec="seconds"),
        "base_url": base_url,
        "users": redact_specs(specs),
        "results": results,
        "summary": summarize_results(results),
    }

    json_path = REPORT_DIR / f"{timestamp}_rbac_menu_phase1.json"
    md_path = REPORT_DIR / f"{timestamp}_rbac_menu_phase1.md"

    json_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    md_path.write_text(render_markdown(payload), encoding="utf-8")
    return json_path, md_path


def summarize_results(results: list[dict[str, Any]]) -> dict[str, Any]:
    counts = {"OK": 0, "WARN": 0, "FAIL": 0}
    for result in results:
        counts[result.get("status", "FAIL")] = counts.get(result.get("status"), 0) + 1

    return {
        "total": len(results),
        "ok": counts.get("OK", 0),
        "warn": counts.get("WARN", 0),
        "fail": counts.get("FAIL", 0),
        "has_failures": counts.get("FAIL", 0) > 0,
        "has_warnings": counts.get("WARN", 0) > 0,
    }


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Fase 1 RBAC/Menu API validation",
        "",
        f"- Fecha: {payload['generated_at']}",
        f"- API base: `{payload['base_url']}`",
        f"- Usuarios evaluados: {payload['summary']['total']}",
        f"- OK/WARN/FAIL: {payload['summary']['ok']}/"
        f"{payload['summary']['warn']}/{payload['summary']['fail']}",
        "",
        "## Resultados",
        "",
    ]

    for result in payload["results"]:
        lines.extend(
            [
                f"### {result['label']} - {result['status']}",
                f"- Email: `{result['email']}`",
                f"- HTTP: `{result.get('http', {})}`",
                f"- Fuente: `{result.get('source', 'N/A')}`",
                f"- Role legacy: `{result.get('role_legacy', 'N/A')}`",
                f"- Permisos efectivos: {result.get('permissions_flat_count', 0)}",
                f"- Acceso global: {result.get('scope', {}).get('tiene_acceso_global')}",
                f"- Menus habilitados: {', '.join(result.get('menu_enabled', [])) or 'ninguno'}",
                "",
            ]
        )

        if result.get("failures"):
            lines.append("Fallas:")
            lines.extend(f"- {item}" for item in result["failures"])
            lines.append("")

        if result.get("risks"):
            lines.append("Riesgos:")
            lines.extend(f"- {item}" for item in result["risks"])
            lines.append("")

        sample = result.get("permissions_flat_sample") or []
        if sample:
            lines.append("Muestra de permisos:")
            lines.extend(f"- `{item}`" for item in sample)
            lines.append("")

    lines.extend(
        [
            "## Nota operativa",
            "",
            "Este reporte no incluye passwords ni tokens. Si aparece WARN por usuario sin "
            "permisos efectivos, revisar primero la semilla SQL RBAC antes de tocar el menu.",
            "",
        ]
    )

    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Valida endpoints RBAC/menu de Fase 1 contra usuarios reales."
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
        "--users-json",
        help="JSON array de usuarios. Tambien puede usarse RBAC_PHASE1_USERS_JSON.",
    )
    parser.add_argument(
        "--users-file",
        help="Archivo JSON con usuarios de prueba.",
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
    parser.add_argument(
        "--use-default-admin",
        action="store_true",
        help=(
            "Usa EDARSAHUB_DEFAULT_ADMIN_EMAIL/EDARSAHUB_DEFAULT_ADMIN_PASSWORD "
            "solo si no se proporcionan usuarios."
        ),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    specs = load_user_specs(args)

    if not specs:
        print(
            "No hay usuarios de prueba. Define RBAC_PHASE1_USERS_JSON o variables "
            "TEST_*_EMAIL/TEST_*_PASSWORD.",
            file=sys.stderr,
        )
        return 2

    results = []
    for spec in specs:
        print(f"Validando {spec['label']} ({spec['email']})...")
        results.append(validate_user(spec, args.base_url, args.timeout))

    json_path, md_path = write_reports(args.base_url, specs, results)
    summary = summarize_results(results)

    print(
        "Resultado Fase 1 RBAC/Menu: "
        f"OK={summary['ok']} WARN={summary['warn']} FAIL={summary['fail']}"
    )
    print(f"Reporte JSON: {json_path}")
    print(f"Reporte MD: {md_path}")

    if summary["has_failures"]:
        return 1
    if args.strict and summary["has_warnings"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
