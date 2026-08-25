#!/usr/bin/env python3
"""Canonical SQL-first requester authorization for the ChatGPT worker.

Transport authentication (GitHub) and EDARSAHUB functional authorization are
separate concerns. This module resolves the declared requester against the
canonical EDARSAHUB SQL user catalog and permits global worker use only for an
active SUPERADMIN. It never hardcodes user emails.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from modules.auth.repository import AuthRepository

SUPERADMIN_ROLE_CODES = {"SUPERADMIN"}
SUPERADMIN_ROLE_NAMES = {"SUPERADMINISTRADOR", "SUPER ADMINISTRADOR"}


def _norm(value: Any) -> str:
    return str(value or "").strip().upper()


def authorize_requester(requester: Any) -> dict[str, Any]:
    if not isinstance(requester, dict):
        return {"allowed": False, "reason": "REQUESTER_REQUIRED"}

    email = str(requester.get("email") or "").strip().lower()
    if not email or "@" not in email:
        return {"allowed": False, "reason": "REQUESTER_EMAIL_INVALID"}

    try:
        user = AuthRepository.get_user_by_email(email)
    except Exception:
        return {"allowed": False, "reason": "REQUESTER_RBAC_LOOKUP_FAILED"}

    if not user:
        return {"allowed": False, "reason": "REQUESTER_NOT_FOUND"}
    if not bool(user.get("active")):
        return {"allowed": False, "reason": "REQUESTER_INACTIVE"}

    role_code = _norm(user.get("role_code") or user.get("_sql_rol_codigo"))
    role_name = _norm(user.get("role"))
    if role_code not in SUPERADMIN_ROLE_CODES and role_name not in SUPERADMIN_ROLE_NAMES:
        return {
            "allowed": False,
            "reason": "REQUESTER_NOT_SUPERADMIN",
            "usuario_id": user.get("UsuarioID") or user.get("_sql_usuario_id"),
            "role_code": role_code,
            "role": role_name,
        }

    return {
        "allowed": True,
        "reason": "SUPERADMIN_CANONICAL",
        "usuario_id": user.get("UsuarioID") or user.get("_sql_usuario_id"),
        "email": str(user.get("email") or email).strip().lower(),
        "role_code": role_code,
        "role": role_name,
        "auth_source": user.get("auth_source") or "SQL_USUARIO_CATALOGO",
        "request_source": str(requester.get("source") or "").strip(),
        "project": str(requester.get("project") or "").strip(),
        "chat": str(requester.get("chat") or "").strip(),
    }
