"""
Portal de Inteligencia Comercial - EXTERNO
==========================================
Login propio + usuarios externos acotados por unidad de negocio, para que socios/
clientes externos consulten la Inteligencia Comercial SIN entrar al CRM completo.

Patrón espejo del Portal de Proveedores pero 100% SQL Server (MÁXIMA NO-MONGO):
- Cookie httpOnly separada: `edarsa_intel_access_token`
- JWT (HS256) con claim type = `portal_intel`
- Hash de contraseñas con bcrypt (passlib)
- Usuarios en dbo.Portal_Inteligencia_Usuarios (cada uno con unidades asignadas)

Admin (alta/baja/edición) protegido por el admin del CRM principal.
Los endpoints de datos `/api/inteligencia/*` aceptan auth DUAL (interno CRM o
externo intel) vía `intel_portal_guard`, y para externos restringen a sus unidades.
"""
import os
import json
import uuid
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any

import jwt
from fastapi import APIRouter, Request, Response, Depends, HTTPException
from passlib.context import CryptContext

from core.sql_first.db import get_sql_connection
from core.security import JWT_SECRET, JWT_ALGORITHM, get_current_user_dual
from core.rbac import require_explicit_permission_dual

logger = logging.getLogger(__name__)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

router = APIRouter(prefix="/portal-intel", tags=["Portal Inteligencia Externo"])

INTEL_COOKIE_NAME = "edarsa_intel_access_token"
INTEL_COOKIE_MAX_AGE = 24 * 60 * 60  # 24h
INTEL_TOKEN_TYPE = "portal_intel"


# ============================================================================
# Helpers SQL
# ============================================================================
def _query(sql: str, params: tuple = None) -> List[Dict[str, Any]]:
    conn = get_sql_connection()
    cur = conn.cursor(as_dict=True)
    cur.execute(sql, params) if params else cur.execute(sql)
    rows = list(cur.fetchall())
    cur.close()
    conn.close()
    return rows


def _write(sql: str, params: tuple = None) -> int:
    conn = get_sql_connection()
    cur = conn.cursor()
    cur.execute(sql, params) if params else cur.execute(sql)
    affected = cur.rowcount
    conn.commit()
    cur.close()
    conn.close()
    return affected


def _parse_unidades(raw) -> List[str]:
    if not raw:
        return []
    try:
        v = json.loads(raw)
        return [str(x) for x in v] if isinstance(v, list) else []
    except Exception:
        return []


def _row_to_user(r: Dict[str, Any], incluir_hash: bool = False) -> Dict[str, Any]:
    out = {
        "id": r["Id"],
        "email": r["Email"],
        "nombre": r.get("Nombre") or "",
        "unidades": _parse_unidades(r.get("UnidadesAsignadas")),
        "activo": bool(r.get("Activo")),
        "ultimo_acceso": r.get("UltimoAcceso").isoformat() if isinstance(r.get("UltimoAcceso"), datetime) else None,
        "fecha_creacion": r.get("FechaCreacion").isoformat() if isinstance(r.get("FechaCreacion"), datetime) else None,
    }
    if incluir_hash:
        out["password_hash"] = r.get("PasswordHash")
    return out


def _get_user_by_email(email: str, incluir_hash: bool = False) -> Optional[Dict[str, Any]]:
    rows = _query("SELECT * FROM dbo.Portal_Inteligencia_Usuarios WHERE Email=%s", (email.lower().strip(),))
    return _row_to_user(rows[0], incluir_hash) if rows else None


def _get_user_by_id(uid: str) -> Optional[Dict[str, Any]]:
    rows = _query("SELECT * FROM dbo.Portal_Inteligencia_Usuarios WHERE Id=%s", (uid,))
    return _row_to_user(rows[0]) if rows else None


# ============================================================================
# JWT + Cookie
# ============================================================================
def _create_intel_token(user_id: str, email: str) -> str:
    payload = {
        "sub": user_id,
        "email": email,
        "type": INTEL_TOKEN_TYPE,
        "exp": datetime.now(timezone.utc) + timedelta(seconds=INTEL_COOKIE_MAX_AGE),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def _set_intel_cookie(response: Response, token: str) -> None:
    is_production = os.environ.get("ENV", "production").lower() == "production"
    response.set_cookie(
        key=INTEL_COOKIE_NAME,
        value=token,
        httponly=True,
        secure=is_production,
        samesite="lax",
        path="/api",
        max_age=INTEL_COOKIE_MAX_AGE,
    )


def _clear_intel_cookie(response: Response) -> None:
    response.delete_cookie(key=INTEL_COOKIE_NAME, path="/api")


def _extract_intel_token(request: Request) -> Optional[str]:
    auth = request.headers.get("authorization", "")
    if auth.startswith("Bearer "):
        t = auth.replace("Bearer ", "").strip()
        if t and t not in ("null", "undefined", ""):
            # Sólo aceptar si es token de tipo intel (ignorar tokens internos)
            try:
                p = jwt.decode(t, JWT_SECRET, algorithms=[JWT_ALGORITHM])
                if p.get("type") == INTEL_TOKEN_TYPE:
                    return t
            except Exception:
                pass
    return request.cookies.get(INTEL_COOKIE_NAME)


def get_current_intel_user(request: Request) -> Dict[str, Any]:
    """Resuelve el usuario externo de Inteligencia desde cookie/Bearer (type=portal_intel)."""
    token = _extract_intel_token(request)
    if not token:
        raise HTTPException(status_code=401, detail="No autenticado (portal inteligencia)")
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Sesión expirada")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token inválido")
    if payload.get("type") != INTEL_TOKEN_TYPE:
        raise HTTPException(status_code=401, detail="Token no válido para este portal")
    user = _get_user_by_id(payload.get("sub"))
    if not user:
        raise HTTPException(status_code=401, detail="Usuario no encontrado")
    if not user["activo"]:
        raise HTTPException(status_code=403, detail="Usuario desactivado")
    return user


# ============================================================================
# GUARD DUAL para /api/inteligencia/*  (interno CRM  O  externo intel + scoping)
# ============================================================================
async def intel_portal_guard(request: Request):
    """
    Permite acceso a los endpoints de Inteligencia a:
      - Usuarios INTERNOS del CRM (Bearer/cookie interna): acceso completo.
      - Usuarios EXTERNOS del portal (cookie intel): SOLO sus unidades asignadas.
    Para externos exige que el query param `unidad` sea una de sus unidades
    (no se permite 'todas'/global). Endpoints sin filtro de unidad (ej. /unidades)
    quedan exentos del chequeo de unidad.
    """
    # 1) ¿Usuario interno del CRM?
    try:
        await get_current_user_dual(request)
        request.state.intel_unidades = None  # None = acceso completo
        return
    except HTTPException:
        pass
    except Exception:
        pass

    # 2) ¿Usuario externo del portal de inteligencia?
    user = get_current_intel_user(request)  # lanza 401/403 si no válido
    allowed = user.get("unidades") or []
    from core.unidades_service import UnidadesService

    allowed_pks = {
        str(pk)
        for value in allowed
        for pk in (UnidadesService.resolver_pk(value),)
        if pk
    }
    if not allowed_pks:
        raise HTTPException(
            status_code=403,
            detail="El usuario no tiene unidades canónicas activas asignadas.",
        )
    request.state.intel_unidades = sorted(allowed_pks)
    request.state.intel_user = user

    # Exentos del chequeo de unidad (endpoints que no filtran por unidad)
    path = request.url.path.rstrip("/")
    exentos = ("/unidades", "/paginas")
    if any(path.endswith(e) for e in exentos):
        return

    unidad = request.query_params.get("unidad")
    if not unidad or unidad.lower() == "todas":
        raise HTTPException(
            status_code=403,
            detail="Selecciona una de tus unidades asignadas (la vista consolidada de todas no está disponible para tu usuario).",
        )
    unidad_pk = UnidadesService.resolver_pk(unidad)
    if not unidad_pk:
        raise HTTPException(
            status_code=400,
            detail="Unidad de negocio inválida o inactiva.",
        )
    if str(unidad_pk) not in allowed_pks:
        raise HTTPException(status_code=403, detail="No tienes acceso a esa unidad de negocio.")
    request.state.intel_unidad_pk = str(unidad_pk)


# ============================================================================
# AUTENTICACIÓN EXTERNA
# ============================================================================
@router.post("/auth/login")
async def login_intel(data: dict, response: Response):
    email = (data.get("email") or "").lower().strip()
    password = data.get("password") or ""
    if not email or not password:
        raise HTTPException(status_code=400, detail="Email y contraseña requeridos")

    user = _get_user_by_email(email, incluir_hash=True)
    if not user or not pwd_context.verify(password, user.get("password_hash") or ""):
        raise HTTPException(status_code=401, detail="Email o contraseña incorrectos")
    if not user["activo"]:
        raise HTTPException(status_code=403, detail="Tu cuenta está desactivada. Contacta al administrador.")

    token = _create_intel_token(user["id"], user["email"])
    _set_intel_cookie(response, token)
    _write("UPDATE dbo.Portal_Inteligencia_Usuarios SET UltimoAcceso=%s WHERE Id=%s",
           (datetime.now(timezone.utc), user["id"]))
    user.pop("password_hash", None)
    return {"token": token, "user": user}


@router.post("/auth/logout")
async def logout_intel(response: Response):
    _clear_intel_cookie(response)
    return {"message": "Sesión cerrada"}


@router.get("/auth/me")
async def me_intel(request: Request):
    return get_current_intel_user(request)


# ============================================================================
# ADMIN (protegido por admin del CRM)
# ============================================================================
async def _require_crm_admin(
    current_user: Dict[str, Any] = Depends(
        require_explicit_permission_dual(
            "INTELIGENCIA_COMERCIAL_GESTIONAR"
        )
    ),
) -> Dict[str, Any]:
    """Exige permiso efectivo SQL, no texto del rol."""
    return current_user


@router.get("/admin/usuarios")
async def admin_listar_usuarios(current=Depends(_require_crm_admin)):
    rows = _query("SELECT * FROM dbo.Portal_Inteligencia_Usuarios ORDER BY FechaCreacion DESC")
    return {"success": True, "usuarios": [_row_to_user(r) for r in rows]}


@router.post("/admin/usuarios")
async def admin_crear_usuario(data: dict, current=Depends(_require_crm_admin)):
    email = (data.get("email") or "").lower().strip()
    password = data.get("password") or ""
    nombre = data.get("nombre") or ""
    unidades = data.get("unidades") or []
    if not email or not password:
        raise HTTPException(status_code=400, detail="Email y contraseña requeridos")
    if len(password) < 6:
        raise HTTPException(status_code=400, detail="La contraseña debe tener al menos 6 caracteres")
    if _get_user_by_email(email):
        raise HTTPException(status_code=400, detail="Ese email ya está registrado")
    if not isinstance(unidades, list) or len(unidades) == 0:
        raise HTTPException(status_code=400, detail="Asigna al menos una unidad de negocio")

    uid = str(uuid.uuid4())
    _write(
        """INSERT INTO dbo.Portal_Inteligencia_Usuarios
           (Id, Email, PasswordHash, Nombre, UnidadesAsignadas, Activo, CreadoPor)
           VALUES (%s,%s,%s,%s,%s,1,%s)""",
        (uid, email, pwd_context.hash(password), nombre, json.dumps(unidades), current.get("email", "admin")),
    )
    return {"success": True, "usuario": _get_user_by_id(uid)}


@router.put("/admin/usuarios/{uid}")
async def admin_actualizar_usuario(uid: str, data: dict, current=Depends(_require_crm_admin)):
    if not _get_user_by_id(uid):
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    sets, vals = [], []
    if "nombre" in data:
        sets.append("Nombre=%s"); vals.append(data["nombre"])
    if "unidades" in data:
        unidades = data["unidades"]
        if not isinstance(unidades, list) or len(unidades) == 0:
            raise HTTPException(status_code=400, detail="Asigna al menos una unidad de negocio")
        sets.append("UnidadesAsignadas=%s"); vals.append(json.dumps(unidades))
    if "activo" in data:
        sets.append("Activo=%s"); vals.append(1 if data["activo"] else 0)
    if "password" in data and data["password"]:
        if len(data["password"]) < 6:
            raise HTTPException(status_code=400, detail="La contraseña debe tener al menos 6 caracteres")
        sets.append("PasswordHash=%s"); vals.append(pwd_context.hash(data["password"]))
    if not sets:
        return {"success": True, "usuario": _get_user_by_id(uid)}
    sets.append("FechaActualizacion=%s"); vals.append(datetime.now(timezone.utc))
    vals.append(uid)
    _write(f"UPDATE dbo.Portal_Inteligencia_Usuarios SET {', '.join(sets)} WHERE Id=%s", tuple(vals))
    return {"success": True, "usuario": _get_user_by_id(uid)}


@router.delete("/admin/usuarios/{uid}")
async def admin_eliminar_usuario(uid: str, current=Depends(_require_crm_admin)):
    if not _get_user_by_id(uid):
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    _write("DELETE FROM dbo.Portal_Inteligencia_Usuarios WHERE Id=%s", (uid,))
    return {"success": True}
