"""
Regresión P2 (2026-06-09): RBAC string→SQL + eliminación de cifras hardcodeadas
en el fallback del Tablero Ejecutivo.

- Los porteros migrados (core/security.py, core/rbac/middleware.py, costos_margenes)
  ahora usan los helpers canónicos `es_admin`/`es_superadmin` (CodigoRol o NombreRol).
- El fallback del tablero ya NO devuelve cifras de ventas inventadas (Regla de Oro).
"""
import os
import re
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

from core.rbac_helper_sql import es_admin, es_superadmin  # noqa: E402


# --- Helpers canónicos cubren NombreRol legacy y CodigoRol canónico ---------
def test_es_superadmin_nombre_y_codigo():
    assert es_superadmin({"role": "SuperAdministrador"}) is True
    assert es_superadmin({"role": "SUPERADMIN"}) is True
    assert es_superadmin({"role": "Administrador"}) is False


def test_es_admin_admite_admin_y_superadmin():
    for rol in ("SuperAdministrador", "SUPERADMIN", "Administrador", "ADMIN"):
        assert es_admin({"role": rol}) is True, rol
    assert es_admin({"role": "Supervisor"}) is False
    assert es_admin({"role": "Usuario"}) is False


# --- costos_margenes: gates migrados a es_admin -----------------------------
def test_costos_margenes_check_admin_or_comercial():
    from modules.costos_margenes.routes import _check_admin_or_comercial
    assert _check_admin_or_comercial({"role": "SuperAdministrador"}) is True
    assert _check_admin_or_comercial({"role": "SUPERADMIN"}) is True
    assert _check_admin_or_comercial({"role": "Administrador"}) is True
    # Lista legacy de lectura preservada
    assert _check_admin_or_comercial({"role": "Supervisor"}) is True
    assert _check_admin_or_comercial({"role": "RolInexistente"}) is False


def test_costos_margenes_precios_admin_todos_permisos():
    from modules.costos_margenes.routes_precios import _get_user_permissions
    perms_super = _get_user_permissions({"role": "SUPERADMIN"})
    assert all(perms_super.values()) is True
    perms_admin = _get_user_permissions({"role": "Administrador"})
    assert all(perms_admin.values()) is True
    # Usuario básico: NO todos los permisos
    perms_user = _get_user_permissions({"role": "Usuario"})
    assert not all(perms_user.values())


# --- Tiers granulares migrados a CodigoRol canónico -------------------------
def test_costos_margenes_precios_tiers_canonicos():
    from modules.costos_margenes.routes_precios import _get_user_permissions
    # Aprobador (Supervisor real / Gerente): puede aprobar
    for rol in ("Supervisor", "SUPERVISOR", "GERENTE", "Gerente"):
        p = _get_user_permissions({"role": rol})
        assert p["aprobar_cambio_precio"] is True, rol
        assert p["solicitar_cambio_precio"] is True, rol
    # Comercial operativo / Ventas: solicita pero NO aprueba
    for rol in ("VENTAS", "Ventas", "ANALISTA_COMERCIAL"):
        p = _get_user_permissions({"role": rol})
        assert p["solicitar_cambio_precio"] is True, rol
        assert p["aprobar_cambio_precio"] is False, rol
    # Usuario/Visor: solo lectura
    for rol in ("Usuario", "USUARIO", "VISOR"):
        p = _get_user_permissions({"role": rol})
        assert p["ver_solicitudes_precio"] is True, rol
        assert p["solicitar_cambio_precio"] is False, rol
        assert p["aprobar_cambio_precio"] is False, rol
    # Rol desconocido: sin permisos
    p = _get_user_permissions({"role": "RolFantasma"})
    assert not any(p.values())


def test_costos_margenes_lectura_comercial_canonica():
    from modules.costos_margenes.routes import _check_admin_or_comercial
    # Cualquier rol canónico del staff tiene lectura
    for rol in ("Usuario", "Supervisor", "GERENTE", "VENTAS", "ANALISTA_COMERCIAL", "VISOR"):
        assert _check_admin_or_comercial({"role": rol}) is True, rol
    # Sin rol reconocido -> sin acceso
    assert _check_admin_or_comercial({"role": "RolFantasma"}) is False
    assert _check_admin_or_comercial({"role": ""}) is False


# --- Tablero Ejecutivo: fallback sin cifras de ventas hardcodeadas -----------
def test_tablero_fallback_sin_cifras_hardcodeadas():
    ruta = os.path.join(os.path.dirname(__file__), "..", "modules", "comercial", "routes.py")
    with open(ruta, "r", encoding="utf-8") as f:
        contenido = f.read()
    # Cifras del antiguo caché estático que ya NO deben existir
    for cifra in ("15710000", "16809700", "4130000", "3570000", "2470000"):
        assert cifra not in contenido, f"Cifra hardcodeada {cifra} sigue presente en el fallback"
    # El fallback honesto debe marcar la fuente como no disponible
    assert "SQL_NO_DISPONIBLE" in contenido
