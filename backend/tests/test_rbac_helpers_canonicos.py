"""
Regresión: helpers de autorización canónicos en core/rbac_helper_sql.py.

Verifican que la resolución de rol use el catálogo SQL (23 roles) y que la
semántica de los gates legacy se preserve, corrigiendo además la negación falsa
al SUPERADMIN en gates '== Administrador' / ['Administrador','Supervisor'].
"""
from dotenv import load_dotenv

load_dotenv("/app/backend/.env")

from core.rbac_helper_sql import (  # noqa: E402
    get_role_code,
    es_superadmin,
    es_admin,
    es_supervisor_o_superior,
)


def test_resolucion_codigo_desde_nombre_legacy_y_codigo():
    assert get_role_code({"role": "SuperAdministrador"}) == "SUPERADMIN"
    assert get_role_code({"role_code": "SUPERADMIN"}) == "SUPERADMIN"
    assert get_role_code({"role": "Administrador"}) == "ADMIN"
    assert get_role_code({"_sql_rol_codigo": "ADMIN"}) == "ADMIN"
    assert get_role_code({"role": "Supervisor"}) == "SUPERVISOR"
    assert get_role_code({"role": "Usuario"}) == "USUARIO"
    assert get_role_code({"role": "Visor"}) == "VISOR"
    assert get_role_code({}) == ""


def test_es_superadmin():
    assert es_superadmin({"role": "SuperAdministrador"})
    assert es_superadmin({"role_code": "SUPERADMIN"})
    assert not es_superadmin({"role": "Administrador"})
    assert not es_superadmin({"role": "Supervisor"})


def test_es_admin_incluye_superadmin_no_otros():
    assert es_admin({"role": "SuperAdministrador"})   # superadmin pasa gates admin
    assert es_admin({"role": "Administrador"})
    assert not es_admin({"role": "Supervisor"})
    assert not es_admin({"role": "Usuario"})
    assert not es_admin({"role": "Visor"})


def test_es_supervisor_o_superior():
    assert es_supervisor_o_superior({"role": "SuperAdministrador"})
    assert es_supervisor_o_superior({"role": "Administrador"})
    assert es_supervisor_o_superior({"role": "Supervisor"})
    assert not es_supervisor_o_superior({"role": "Usuario"})
    assert not es_supervisor_o_superior({"role": "Visor"})


def test_rol_no_admin_no_falso_positivo():
    # Un Gerente (existe en SQL) NO debe ser tratado como admin por nivel.
    assert get_role_code({"role": "Gerente"}) == "GERENTE"
    assert not es_admin({"role": "Gerente"})
    assert not es_superadmin({"role": "Gerente"})


def test_clave_rol_legacy_compat():
    # compatibilidad con la clave 'rol' (legacy)
    assert es_superadmin({"rol": "SuperAdministrador"})
