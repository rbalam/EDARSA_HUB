"""Contexto de acceso RBAC para el Asistente IA de EDARSAHUB.

La vista nunca concede permisos. Resuelve identidad SQL, permisos efectivos y
alcance explícito antes de que el planner seleccione operaciones read-only.
La autorización final vuelve a ocurrir en cada endpoint interno.
"""
from __future__ import annotations

from typing import Any, Dict, Iterable

from core.rbac_sql.service import RBACSQLService
from modules.auth.repository import AuthRepository

IA_PERMISSION = "IA_ASSISTANT_VER"
MAX_PERMISSION_CODES = 300
MAX_SCOPE_ROWS = 200


def _clean(value: Any) -> str:
    return str(value or "").strip()


def _resolve_user_record(current_user: Dict[str, Any]) -> Dict[str, Any]:
    candidate = dict(current_user or {})
    if candidate.get("_sql_usuario_id") or candidate.get("UsuarioID"):
        return candidate

    email = _clean(candidate.get("email")).lower()
    if not email:
        return {}

    record = AuthRepository.get_user_by_email(email)
    return dict(record or {})


def _safe_scope_rows(
    rows: Iterable[Any],
    allowed_keys: tuple[str, ...],
) -> list[dict[str, str]]:
    result: list[dict[str, str]] = []
    for row in list(rows or [])[:MAX_SCOPE_ROWS]:
        if not isinstance(row, dict):
            continue
        item: dict[str, str] = {}
        for key in allowed_keys:
            value = _clean(row.get(key))
            if value:
                item[key] = value
        if item:
            result.append(item)
    return result


def build_ai_access_context(
    current_user: Dict[str, Any],
) -> Dict[str, Any]:
    """Resuelve alcance IA exclusivamente desde RBAC SQL; falla cerrado."""
    record = _resolve_user_record(current_user)
    sql_user_id = record.get("_sql_usuario_id") or record.get("UsuarioID")

    if not sql_user_id:
        return {
            "authorized": False,
            "source": "RBAC_SQL",
            "source_policy": "EDARSAHUB_ONLY",
            "reason": "SQL_USER_NOT_RESOLVED",
        }

    if record.get("active") is False:
        return {
            "authorized": False,
            "source": "RBAC_SQL",
            "source_policy": "EDARSAHUB_ONLY",
            "reason": "USER_INACTIVE",
        }

    try:
        allowed = RBACSQLService.can_access_permission(sql_user_id, IA_PERMISSION)
        permissions = RBACSQLService.get_effective_permissions(sql_user_id)
        scope = RBACSQLService.build_context(sql_user_id) or {}
        assignment_state = RBACSQLService.get_scope_assignment_state(sql_user_id) or {}
    except Exception:
        return {
            "authorized": False,
            "source": "RBAC_SQL",
            "source_policy": "EDARSAHUB_ONLY",
            "reason": "RBAC_CONTEXT_UNAVAILABLE",
        }

    if not allowed:
        return {
            "authorized": False,
            "source": "RBAC_SQL",
            "source_policy": "EDARSAHUB_ONLY",
            "reason": "IA_PERMISSION_DENIED",
        }

    permission_codes = [
        _clean(code)
        for code in permissions or []
        if _clean(code)
    ][:MAX_PERMISSION_CODES]

    return {
        "authorized": True,
        "source": "RBAC_SQL",
        "source_policy": "EDARSAHUB_ONLY",
        "usuario_id": str(sql_user_id),
        "permission_codes": permission_codes,
        "roles": _safe_scope_rows(scope.get("roles"), ("RolID", "CodigoRol")),
        "empresas": _safe_scope_rows(scope.get("empresas"), ("EmpresaID",)),
        "unidades_negocio": _safe_scope_rows(
            scope.get("unidades_negocio"),
            ("UnidadNegocioID",),
        ),
        "sucursales": _safe_scope_rows(
            scope.get("sucursales"),
            ("ServidorID", "SucursalCodigo"),
        ),
        "servidores": _safe_scope_rows(scope.get("servidores"), ("ServidorID",)),
        "scope_assignment_state": {
            "server_assignment_count": int(
                assignment_state.get("server_assignment_count", 0)
            ),
            "branch_assignment_count": int(
                assignment_state.get("branch_assignment_count", 0)
            ),
        },
    }
