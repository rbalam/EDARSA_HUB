"""
Regresión P1 RBAC Hardening — migración de gates hardcodeados a helper canónico.

Cubre:
- security.py: filter_servers_by_permissions (es_admin) y validate_for_explorer (get_role_code)
- solicitudes_catalogo.py: gates de aprobar/crear/autorizar/rechazar incluyen SUPERADMIN (opción b)
- Semántica canónica de los helpers (fallback de roles de sistema, sin DB).

Las pruebas son estáticas + semánticas (vía _CODE_FALLBACK) para no depender de la DB.
"""
from pathlib import Path

from core.rbac_helper_sql import (
    get_role_code,
    es_admin,
    es_superadmin,
    es_supervisor_o_superior,
)

BACKEND = Path(__file__).resolve().parents[1]


# ---------------------------------------------------------------------------
# Semántica canónica de los helpers (opción b: SUPERADMIN incluido en admin/supervisor)
# ---------------------------------------------------------------------------
def test_get_role_code_normaliza_legacy_y_codigo():
    assert get_role_code({"role": "SuperAdministrador"}) == "SUPERADMIN"
    assert get_role_code({"role": "Administrador"}) == "ADMIN"
    assert get_role_code({"role": "Supervisor"}) == "SUPERVISOR"
    assert get_role_code({"role": "SUPERADMIN"}) == "SUPERADMIN"
    assert get_role_code({"role": "Usuario"}) == "USUARIO"


def test_es_superadmin_solo_superadmin():
    assert es_superadmin({"role": "SuperAdministrador"}) is True
    assert es_superadmin({"role": "Administrador"}) is False
    assert es_superadmin({"role": "Supervisor"}) is False


def test_es_admin_incluye_superadmin():
    assert es_admin({"role": "SuperAdministrador"}) is True
    assert es_admin({"role": "Administrador"}) is True
    assert es_admin({"role": "Supervisor"}) is False
    assert es_admin({"role": "Usuario"}) is False


def test_es_supervisor_o_superior_incluye_superadmin():
    assert es_supervisor_o_superior({"role": "SuperAdministrador"}) is True
    assert es_supervisor_o_superior({"role": "Administrador"}) is True
    assert es_supervisor_o_superior({"role": "Supervisor"}) is True
    assert es_supervisor_o_superior({"role": "Usuario"}) is False


def test_validate_for_explorer_gate_canonico():
    """El gate del Explorador SQL debe bloquear no-admins y permitir SUPERADMIN/ADMIN.
    Antes comparaba contra nombre legacy y bloqueaba al código 'SUPERADMIN'."""
    from core.security import SQLSanitizer as V
    # SUPERADMIN por código canónico (antes era bloqueado erróneamente)
    r = V.validate_for_explorer("SELECT 1", user_role="SUPERADMIN")
    assert r.is_safe is True
    # Administrador legacy permitido
    r = V.validate_for_explorer("SELECT 1", user_role="Administrador")
    assert r.is_safe is True
    # Usuario sin privilegios bloqueado
    r = V.validate_for_explorer("SELECT 1", user_role="Usuario")
    assert r.is_safe is False
    assert "explorador" in (r.blocked_reason or "").lower()
    # Sin user_role (None) → no aplica el gate de rol (comportamiento previo preservado)
    r = V.validate_for_explorer("SELECT 1", user_role=None)
    assert r.is_safe is True


# ---------------------------------------------------------------------------
# Estáticas: sin hardcodes legacy y uso del helper canónico
# ---------------------------------------------------------------------------
def test_solicitudes_catalogo_sin_hardcodes_y_con_helper():
    src = (BACKEND / "modules/rh/solicitudes_catalogo.py").read_text(encoding="utf-8")
    assert "from core.rbac_helper_sql import" in src
    # No deben quedar comparaciones legacy por nombre de rol
    for legacy in (
        'role == "Administrador"',
        'role != "Administrador"',
        'role not in ["Supervisor", "Administrador"]',
        'role == "Supervisor"',
    ):
        assert legacy not in src, f"Hardcode legacy persistente: {legacy}"
    # Gates canónicos presentes
    assert "es_supervisor_o_superior(current_user)" in src
    assert "es_admin(current_user)" in src


def test_security_filter_servers_usa_es_admin():
    src = (BACKEND / "core/security.py").read_text(encoding="utf-8")
    assert "if es_admin(user):" in src
    assert "if role in ['SuperAdministrador', 'Administrador']:" not in src
    assert "user_role not in ['Administrador', 'SuperAdministrador']" not in src
