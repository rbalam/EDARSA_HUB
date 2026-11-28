"""Contrato GATE-M2 R3: visibilidad de /worker-console en Menú Enterprise SQL + RBAC fail-closed."""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List

os.environ.setdefault("JWT_SECRET", "test-gate-m2-r3-menu-secret-only-unit-tests-1234567890")
os.environ.setdefault("EDARSAHUB_SQL_HOST", "127.0.0.1")
os.environ.setdefault("EDARSAHUB_SQL_PORT", "1433")
os.environ.setdefault("EDARSAHUB_SQL_DATABASE", "EDARSAHUB")
os.environ.setdefault("EDARSAHUB_SQL_USER", "HRLectura")
os.environ.setdefault("EDARSAHUB_SQL_PASSWORD", "test-placeholder")

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
TOOLS = ROOT / "tools" / "mirror_sync"
for p in (str(ROOT), str(BACKEND), str(TOOLS)):
    if p not in sys.path:
        sys.path.insert(0, p)

from modules.sistema.menu_service import MenuService  # noqa: E402
from tools.mirror_sync import readonly_audit_profiles as profiles  # noqa: E402


MIGRATION = ROOT / "backend/database/migrations/20261121_001_worker_console_enterprise_menu.sql"
VALIDATION = ROOT / "backend/database/validation/20261121_001_worker_console_enterprise_menu_validation.sql"
ROLLBACK = ROOT / "backend/database/rollback/20261121_001_worker_console_enterprise_menu_rollback.sql"
REGISTRY_JSON = ROOT / "frontend/src/config/enterpriseNavigationRegistry.json"
APP_JS = ROOT / "frontend/src/App.js"
MENU_JSX = ROOT / "frontend/src/components/navigation/EnterpriseNavigationMenu.jsx"


def test_sql_migration_validation_rollback_contracts():
    mig = MIGRATION.read_text(encoding="utf-8")
    val = VALIDATION.read_text(encoding="utf-8")
    rb = ROLLBACK.read_text(encoding="utf-8")

    # Guard fail-closed contra BD incorrecta en los 3 artefactos
    for text in (mig, val, rb):
        assert "DB_NAME() <> N'EDARSAHUB'" in text
        assert "DROP TABLE" not in text.upper()
        assert "TRUNCATE TABLE" not in text.upper()

    # Migración idempotente + anti-colisión + permiso fail-closed RBAC_ADMIN
    for token in (
        "dbo.Sistema_Modulos",
        "dbo.Sistema_ModulosMenus",
        "N'SISTEMA'",
        "N'sistema.worker_console'",
        "N'/worker-console'",
        "N'ShieldCheck'",
        "N'RBAC_ADMIN'",
        "IF NOT EXISTS",
        "UPDLOCK, HOLDLOCK",
    ):
        assert token in mig, f"Falta token requerido en migración: {token}"

    assert "VALIDATION_SUCCESS" in val
    assert "DELETE FROM dbo.Sistema_ModulosMenus" in rb
    assert "WHERE Codigo = N'sistema.worker_console'" in rb
    assert "AND Ruta = N'/worker-console'" in rb


def test_frontend_registry_route_and_icon_parity():
    reg = json.loads(REGISTRY_JSON.read_text(encoding="utf-8"))
    entry = reg["menuMappings"].get("sistema.worker_console")
    assert isinstance(entry, dict)
    assert entry["groupId"] == "plataforma-integraciones"
    assert entry["sectionId"] == "administracion-seguridad"
    assert entry["expectedPath"] == "/worker-console"
    assert entry["status"] == "active"

    app_src = APP_JS.read_text(encoding="utf-8")
    assert 'path="/worker-console"' in app_src
    assert "<ProtectedRoute><WorkerConsole /></ProtectedRoute>" in app_src

    menu_src = MENU_JSX.read_text(encoding="utf-8")
    assert "ShieldCheck" in menu_src


class _FakeMenuCursor:
    def __init__(self, modulos: List[Dict[str, Any]], menus: List[Dict[str, Any]]):
        self._modulos = modulos
        self._menus = menus
        self._current: List[Dict[str, Any]] = []

    def execute(self, sql: str, params=None):
        if "FROM dbo.Sistema_ModulosMenus" in sql:
            self._current = list(self._menus)
        elif "FROM dbo.Sistema_Modulos" in sql:
            self._current = list(self._modulos)
        else:
            self._current = []

    def fetchall(self):
        return list(self._current)


def test_menu_service_rbac_visibility_superadmin_vs_non_superadmin():
    modulos = [
        {
            "ModuloID": 27,
            "Codigo": "SISTEMA",
            "Nombre": "Administración Sistema",
            "Descripcion": "Sistema",
            "Icono": "Settings",
            "Orden": 27,
            "EsPrincipal": True,
            "EsSatelite": False,
            "EsPortal": False,
            "URLExterna": None,
            "Activo": True,
        }
    ]
    menus = [
        {
            "MenuID": 61,
            "ModuloID": 27,
            "MenuPadreID": None,
            "Codigo": "sistema.usuarios",
            "Nombre": "Usuarios",
            "Descripcion": "Gestión de usuarios",
            "Icono": "Users",
            "Ruta": "/usuarios",
            "Orden": 9,
            "RequierePermiso": "usuarios",
            "Activo": True,
        },
        {
            "MenuID": 999,
            "ModuloID": 27,
            "MenuPadreID": None,
            "Codigo": "sistema.worker_console",
            "Nombre": "Universal Worker Console",
            "Descripcion": "Consola operativa de Universal Worker V4, auditoria y estado SQL canonico",
            "Icono": "ShieldCheck",
            "Ruta": "/worker-console",
            "Orden": 12,
            "RequierePermiso": "RBAC_ADMIN",
            "Activo": True,
        },
    ]

    svc = MenuService()

    # 1. SUPERADMIN ve sistema.worker_console activo y visible
    sa_result = svc._obtener_menus_usuario_resuelto(
        _FakeMenuCursor(modulos, menus),
        superadmin=True,
        permisos_modulo=set(),
    )
    assert len(sa_result) == 1
    sa_codes = [m["codigo"] for m in sa_result[0]["menus"]]
    assert "sistema.worker_console" in sa_codes
    wc_item = [m for m in sa_result[0]["menus"] if m["codigo"] == "sistema.worker_console"][0]
    assert wc_item["ruta"] == "/worker-console"
    assert wc_item["activo"] is True
    assert wc_item["visible"] is True
    assert wc_item["requiere_permiso"] == "RBAC_ADMIN"

    # 2. ADMIN con solo permiso de módulo RBAC (RBAC_VER) o USUARIOS NO ve sistema.worker_console (fail-closed)
    admin_result = svc._obtener_menus_usuario_resuelto(
        _FakeMenuCursor(modulos, menus),
        superadmin=False,
        permisos_modulo={"RBAC", "USUARIOS", "SISTEMA"},
    )
    admin_codes = [m["codigo"] for mod in admin_result for m in mod["menus"]]
    assert "sistema.usuarios" in admin_codes
    assert "sistema.worker_console" not in admin_codes

    # 3. Usuario operativo sin permisos de sistema NO ve sistema.worker_console
    op_result = svc._obtener_menus_usuario_resuelto(
        _FakeMenuCursor(modulos, menus),
        superadmin=False,
        permisos_modulo={"COMERCIAL"},
    )
    op_codes = [m["codigo"] for mod in op_result for m in mod["menus"]]
    assert "sistema.worker_console" not in op_codes


def test_readonly_audit_profile_worker_console_menu():
    assert profiles.is_allowed_readonly_audit_profile("worker_console_enterprise_menu_v1") is True
    checks = profiles.build_readonly_audit_checks("worker_console_enterprise_menu_v1")
    assert len(checks) == 1
    assert checks[0]["type"] == "sql_readonly_audit"
    assert checks[0]["source"] == "EDARSAHUB"
    qnames = [q["name"] for q in checks[0]["queries"]]
    assert qnames == [
        "worker_console_menu_sql_identity",
        "sistema_module_status",
        "worker_console_menu_row",
    ]
    for q in checks[0]["queries"]:
        sql_up = q["sql"].upper()
        assert sql_up.startswith("SELECT ")
        for forbidden in ("INSERT ", "UPDATE ", "DELETE ", "DROP ", "ALTER "):
            assert forbidden not in sql_up


def test_enterprise_navigation_guardian_script_passes():
    script = ROOT / "frontend/scripts/validate_enterprise_navigation.js"
    proc = subprocess.run(
        ["node", str(script)],
        cwd=str(ROOT / "frontend"),
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, f"validate_enterprise_navigation failed: {proc.stdout}\n{proc.stderr}"
    assert "ENTERPRISE_NAVIGATION_GUARDIAN=PASS" in proc.stdout
