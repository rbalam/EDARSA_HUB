"""
Servicio SQL-First del RBAC Piloto (perfiles / roles / permisos de sistema).

Reemplaza la implementación legacy basada en MongoDB (`db.sec_perfiles`, `db.sec_roles`,
`db.users.sec_*`) por almacenamiento canónico en EDARSAHUB SQL:
  - dbo.Sistema_RBAC_PerfilCatalogo  : catálogo perfil -> roles (CSV)
  - dbo.Usuario_RBAC_Asignacion      : asignación por usuario (Tipo: PERFIL|ROL|PERMISO)

Mantiene la misma semántica del modelo legacy (era una capa piloto/informativa, no la
resolución de permisos en vivo de `rbac_helper`):
  - Asignar perfil = setea sec_perfil + sobrescribe sec_roles con los roles del perfil.
  - Retirar perfil = limpia sec_perfil y sec_roles.
  - Toggle rol/permiso = alta/baja individual.
"""
import logging
from typing import Any, Dict, List, Optional

from fastapi import HTTPException

from core.sql_first.db import get_sql_connection

logger = logging.getLogger(__name__)

# Whitelists piloto (idénticas al frontend RBAC_*_PILOTO / FASE 13)
PERMISOS_PILOTO = {
    "SISTEMA_ESTRUCTURA_VER",
    "SISTEMA_USUARIOS_VER",
    "SISTEMA_USUARIOS_CREAR",
    "SISTEMA_USUARIOS_EDITAR",
    "SISTEMA_USUARIOS_ELIMINAR",
    "SISTEMA_ROLES_VER",
    "SISTEMA_ROLES_CREAR",
    "SISTEMA_ROLES_EDITAR",
    "SISTEMA_ROLES_ELIMINAR",
}
ROLES_PILOTO = {
    "VISOR_ESTRUCTURA",
    "VISOR_SISTEMA",
    "VISOR_ADMIN",
    "ADMIN_USUARIOS",
    "GESTOR_SISTEMA",
}


def _connect():
    return get_sql_connection()


def _resolve_usuario_id(cur, email: str) -> Optional[int]:
    cur.execute("SELECT UsuarioID FROM dbo.Usuario_Catalogo WHERE LOWER(Email) = LOWER(%s)", (email,))
    row = cur.fetchone()
    return int(row[0]) if row else None


# ---------------------------------------------------------------------------
# Catálogo de perfiles
# ---------------------------------------------------------------------------
def get_perfiles_catalogo() -> List[Dict[str, Any]]:
    conn = _connect()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT Codigo, Nombre, RolesCsv FROM dbo.Sistema_RBAC_PerfilCatalogo WHERE Activo = 1 ORDER BY PerfilID"
        )
        perfiles = []
        for codigo, nombre, roles_csv in cur.fetchall():
            roles = [r.strip() for r in (roles_csv or "").split(",") if r.strip()]
            perfiles.append({"codigo": codigo, "nombre": nombre, "roles": roles, "activo": True})
        return perfiles
    finally:
        conn.close()


def _get_perfil(cur, codigo: str) -> Optional[Dict[str, Any]]:
    cur.execute(
        "SELECT Codigo, Nombre, RolesCsv FROM dbo.Sistema_RBAC_PerfilCatalogo WHERE Codigo = %s AND Activo = 1",
        (codigo,),
    )
    row = cur.fetchone()
    if not row:
        return None
    roles = [r.strip() for r in (row[2] or "").split(",") if r.strip()]
    return {"codigo": row[0], "nombre": row[1], "roles": roles}


# ---------------------------------------------------------------------------
# Asignaciones por usuario
# ---------------------------------------------------------------------------
def get_rbac_map() -> Dict[str, Dict[str, Any]]:
    """Devuelve {usuario_id_str: {sec_perfil, sec_roles[], sec_permisos[]}}."""
    conn = _connect()
    try:
        cur = conn.cursor()
        cur.execute("SELECT UsuarioID, Tipo, Codigo FROM dbo.Usuario_RBAC_Asignacion")
        out: Dict[str, Dict[str, Any]] = {}
        for usuario_id, tipo, codigo in cur.fetchall():
            uid = str(usuario_id)
            entry = out.setdefault(uid, {"sec_perfil": None, "sec_roles": [], "sec_permisos": []})
            if tipo == "PERFIL":
                entry["sec_perfil"] = codigo
            elif tipo == "ROL":
                entry["sec_roles"].append(codigo)
            elif tipo == "PERMISO":
                entry["sec_permisos"].append(codigo)
        return out
    finally:
        conn.close()


def asignar_perfil(usuario_email: str, perfil_codigo: str, actor: str) -> Dict[str, Any]:
    conn = _connect()
    try:
        cur = conn.cursor()
        perfil = _get_perfil(cur, perfil_codigo)
        if not perfil:
            raise HTTPException(status_code=404, detail=f"Perfil {perfil_codigo} no encontrado o inactivo")
        usuario_id = _resolve_usuario_id(cur, usuario_email)
        if not usuario_id:
            raise HTTPException(status_code=404, detail=f"Usuario {usuario_email} no encontrado")

        # Sobrescribe perfil + roles (limpia PERFIL y ROL previos)
        cur.execute(
            "DELETE FROM dbo.Usuario_RBAC_Asignacion WHERE UsuarioID = %s AND Tipo IN ('PERFIL','ROL')",
            (usuario_id,),
        )
        cur.execute(
            "INSERT INTO dbo.Usuario_RBAC_Asignacion (UsuarioID, Tipo, Codigo, AsignadoPor) VALUES (%s,'PERFIL',%s,%s)",
            (usuario_id, perfil_codigo, actor),
        )
        for rol in perfil["roles"]:
            cur.execute(
                "INSERT INTO dbo.Usuario_RBAC_Asignacion (UsuarioID, Tipo, Codigo, AsignadoPor) VALUES (%s,'ROL',%s,%s)",
                (usuario_id, rol, actor),
            )
        conn.commit()
        return {
            "success": True,
            "usuario": usuario_email,
            "perfil": perfil_codigo,
            "roles_aplicados": perfil["roles"],
            "mensaje": f"Perfil {perfil_codigo} asignado exitosamente",
        }
    finally:
        conn.close()


def retirar_perfil(usuario_email: str, actor: str) -> Dict[str, Any]:
    conn = _connect()
    try:
        cur = conn.cursor()
        usuario_id = _resolve_usuario_id(cur, usuario_email)
        if not usuario_id:
            raise HTTPException(status_code=404, detail=f"Usuario {usuario_email} no encontrado")
        cur.execute(
            "DELETE FROM dbo.Usuario_RBAC_Asignacion WHERE UsuarioID = %s AND Tipo IN ('PERFIL','ROL')",
            (usuario_id,),
        )
        conn.commit()
        return {"success": True, "usuario": usuario_email, "mensaje": "Perfil retirado"}
    finally:
        conn.close()


def toggle_asignacion(usuario_email: str, tipo: str, codigo: str, accion: str) -> Dict[str, Any]:
    tipo = tipo.upper()
    accion = (accion or "").upper()
    if tipo == "ROL" and codigo not in ROLES_PILOTO:
        raise HTTPException(status_code=400, detail=f"Rol '{codigo}' no está en whitelist piloto")
    if tipo == "PERMISO" and codigo not in PERMISOS_PILOTO:
        raise HTTPException(status_code=400, detail=f"Permiso '{codigo}' no está en whitelist piloto")
    if accion not in ("ASIGNAR", "RETIRAR"):
        raise HTTPException(status_code=400, detail="accion debe ser ASIGNAR o RETIRAR")

    conn = _connect()
    try:
        cur = conn.cursor()
        usuario_id = _resolve_usuario_id(cur, usuario_email)
        if not usuario_id:
            raise HTTPException(status_code=404, detail=f"Usuario {usuario_email} no encontrado")

        if accion == "RETIRAR":
            cur.execute(
                "DELETE FROM dbo.Usuario_RBAC_Asignacion WHERE UsuarioID = %s AND Tipo = %s AND Codigo = %s",
                (usuario_id, tipo, codigo),
            )
        else:
            cur.execute(
                "SELECT 1 FROM dbo.Usuario_RBAC_Asignacion WHERE UsuarioID = %s AND Tipo = %s AND Codigo = %s",
                (usuario_id, tipo, codigo),
            )
            if not cur.fetchone():
                cur.execute(
                    "INSERT INTO dbo.Usuario_RBAC_Asignacion (UsuarioID, Tipo, Codigo, AsignadoPor) VALUES (%s,%s,%s,%s)",
                    (usuario_id, tipo, codigo, usuario_email),
                )
        conn.commit()
        label = "rol" if tipo == "ROL" else "permiso"
        verbo = "asignado" if accion == "ASIGNAR" else "retirado"
        return {"success": True, "detail": f"{label.capitalize()} {codigo} {verbo}"}
    finally:
        conn.close()
