"""
RBAC Helper - SQL-First (P0-2 estabilización V1.0)
==================================================

Verificación de permisos RBAC contra EDARSAHUB SQL (fuente única de verdad).

REGLAS:
- NO MongoDB. Sin dependencia del stub legacy.
- NO conexiones live externas. Solo core.sql_first.db.get_sql_connection().
- La función pública DEBE seguir siendo `async` (8 call-sites usan `await`).
- PyMSSQL es síncrono: el núcleo SQL se ejecuta en run_in_threadpool para no
  bloquear el event loop (patrón recomendado FastAPI/Starlette).

current_user (modules/auth/repository._normalize_user) expone:
    - role           -> CodigoRol ('SUPERADMIN' | 'ADMIN' | ...)
    - UsuarioID      -> id numérico
    - email
"""

from typing import Any, Dict, List, Optional
from starlette.concurrency import run_in_threadpool

from core.sql_first.db import get_sql_connection


# Roles con bypass administrativo total (normalizados a MAYÚSCULAS)
BYPASS_ROLES = {
    "SUPERADMIN",
    "SUPERADMINISTRADOR",
    "SUPER ADMIN",
    "ADMIN",
    "ADMINISTRADOR",
}

# Nivel jerárquico mínimo para bypass (Administrador=90, SuperAdministrador=100)
BYPASS_NIVEL_MINIMO = 90


# =============================================================================
# Extractores tolerantes (firma flexible, no rompe llamadas legacy)
# =============================================================================

def _norm(value: Any) -> str:
    return str(value or "").strip().upper()


def _extract_current_user(*args, **kwargs) -> Optional[Dict[str, Any]]:
    for key in ("current_user", "user", "usuario"):
        value = kwargs.get(key)
        if isinstance(value, dict):
            return value
    for arg in args:
        if isinstance(arg, dict):
            return arg
    return None


def _extract_permiso(*args, **kwargs) -> str:
    for key in ("permiso", "permiso_requerido", "permission", "required_permission"):
        value = kwargs.get(key)
        if value:
            return str(value)
    for arg in args:
        if isinstance(arg, str) and arg.strip():
            return arg.strip()
    return ""


def _extract_usuario_id(current_user: Dict[str, Any]) -> Optional[int]:
    for key in ("UsuarioID", "_sql_usuario_id", "usuario_id", "user_id", "sql_user_id"):
        value = current_user.get(key)
        if value is not None and str(value).strip() != "":
            try:
                return int(value)
            except Exception:
                continue
    return None


def _extract_role(current_user: Dict[str, Any]) -> str:
    for key in ("role", "rol", "CodigoRol", "RolNombre", "NombreRol", "role_name", "nombre_rol"):
        value = current_user.get(key)
        if value:
            return _norm(value)
    return ""


def _module_candidates_from_permiso(permiso: str) -> List[str]:
    raw = (permiso or "").strip()
    if not raw:
        return []
    parts = [raw]
    for sep in (".", ":", "/", "\\", "|"):
        if sep in raw:
            parts.append(raw.split(sep, 1)[0])
    out: List[str] = []
    for p in parts:
        n = _norm(p).replace(" ", "_")
        if n and n not in out:
            out.append(n)
    return out


# =============================================================================
# Núcleo SQL síncrono (PyMSSQL) - se ejecuta en threadpool
# =============================================================================

def _has_bypass_role_sql(usuario_id: int) -> bool:
    sql = """
        SELECT TOP 1 1
        FROM Usuario_RolesContexto urc
        INNER JOIN Usuario_Roles r
            ON urc.RolID = r.RolID AND r.Activo = 1
        WHERE urc.UsuarioID = %s
          AND urc.Activo = 1
          AND (
                UPPER(LTRIM(RTRIM(r.CodigoRol))) IN ('SUPERADMIN', 'ADMIN')
                OR UPPER(LTRIM(RTRIM(r.NombreRol))) IN ('SUPERADMINISTRADOR', 'ADMINISTRADOR')
                OR r.NivelJerarquia >= 90
          )
    """
    with get_sql_connection() as conn:
        cur = conn.cursor()
        cur.execute(sql, (usuario_id,))
        return cur.fetchone() is not None


def _has_permission_sql(usuario_id: int, modules: List[str]) -> bool:
    if not modules:
        return False
    placeholders = ",".join(["%s"] * len(modules))
    sql = f"""
        SELECT TOP 1 1
        FROM Usuario_RolesContexto urc
        INNER JOIN Usuario_Roles r
            ON r.RolID = urc.RolID AND r.Activo = 1
        INNER JOIN Usuario_PermisosRolModulo prm
            ON prm.RolID = urc.RolID AND prm.Activo = 1 AND prm.Permitido = 1
        INNER JOIN Sistema_Modulos sm
            ON sm.ModuloID = prm.ModuloID
        WHERE urc.UsuarioID = %s
          AND urc.Activo = 1
          AND (
                UPPER(LTRIM(RTRIM(sm.Codigo))) IN ({placeholders})
                OR UPPER(REPLACE(LTRIM(RTRIM(sm.Nombre)), ' ', '_')) IN ({placeholders})
          )
    """
    params = [usuario_id] + modules + modules
    with get_sql_connection() as conn:
        cur = conn.cursor()
        cur.execute(sql, tuple(params))
        return cur.fetchone() is not None


def _verificar_sql(usuario_id: int, permiso: str) -> bool:
    """Núcleo síncrono. Fail-closed ante errores (el caller tiene fallback legacy)."""
    try:
        if _has_bypass_role_sql(usuario_id):
            return True
        modules = _module_candidates_from_permiso(permiso)
        if modules:
            return _has_permission_sql(usuario_id, modules)
        return False
    except Exception:
        return False


# =============================================================================
# API pública (ASÍNCRONA - 8 call-sites usan await)
# =============================================================================

async def verificar_permiso_rbac(*args, **kwargs) -> bool:
    """
    Verifica permiso RBAC contra EDARSAHUB SQL.

    Firma flexible (acepta (current_user, permiso) o kwargs). Ignora cualquier
    parámetro `db` legacy si se envía.

    Resolución:
      1. Bypass inmediato si current_user['role'] (CodigoRol) es admin -> sin SQL.
      2. Si no, consulta SQL (en threadpool) rol/permiso del usuario.
    """
    current_user = _extract_current_user(*args, **kwargs)
    if not current_user:
        return False

    # 1. Bypass rápido por rol del token (CodigoRol)
    if _extract_role(current_user) in BYPASS_ROLES:
        return True

    # 2. Verificación SQL para usuarios no-admin
    usuario_id = _extract_usuario_id(current_user)
    if not usuario_id:
        return False

    permiso = _extract_permiso(*args, **kwargs)
    return await run_in_threadpool(_verificar_sql, usuario_id, permiso)
