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
import json
import logging
import uuid
from typing import Any, Dict, List, Optional, Tuple

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
        registrar_bitacora(
            usuario_email, "ASIGNAR", "ASIGNAR_PERFIL",
            f"Perfil {perfil_codigo} asignado ({len(perfil['roles'])} roles)",
            usuario_id=usuario_id,
            detalles={"perfil": perfil_codigo, "roles": perfil["roles"]},
            actor_email=actor,
        )
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
        registrar_bitacora(
            usuario_email, "REVOCAR", "RETIRAR_PERFIL", "Perfil retirado",
            usuario_id=usuario_id, actor_email=actor,
        )
        return {"success": True, "usuario": usuario_email, "mensaje": "Perfil retirado"}
    finally:
        conn.close()


def toggle_asignacion(usuario_email: str, tipo: str, codigo: str, accion: str, actor: Optional[str] = None) -> Dict[str, Any]:
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
        detalle = f"{label.capitalize()} {codigo} {verbo}"
        registrar_bitacora(
            usuario_email,
            "ASIGNAR" if accion == "ASIGNAR" else "REVOCAR",
            f"{accion}_{tipo}", detalle,
            usuario_id=usuario_id, actor_email=actor,
        )
        return {"success": True, "detail": detalle}
    finally:
        conn.close()


# =============================================================================
# BITÁCORA RBAC SQL-First (reemplaza Mongo sec_bitacora_admin)
# =============================================================================
def registrar_bitacora(
    usuario_email: Optional[str],
    tipo: str,
    accion: str,
    descripcion: str,
    *,
    usuario_id: Optional[int] = None,
    resultado: str = "exitoso",
    detalles: Optional[dict] = None,
    actor_email: Optional[str] = None,
    ip: Optional[str] = None,
) -> None:
    """Registra un evento de bitácora RBAC en SQL. No-fatal: si falla, no rompe
    la operación principal (solo loguea)."""
    try:
        conn = _connect()
        try:
            cur = conn.cursor()
            if usuario_id is None and usuario_email:
                usuario_id = _resolve_usuario_id(cur, usuario_email)
            detalles_json = json.dumps(detalles, ensure_ascii=False) if detalles is not None else None
            cur.execute(
                """INSERT INTO dbo.Usuario_RBAC_Bitacora
                   (EventoUUID, UsuarioAfectadoID, UsuarioAfectadoEmail, Tipo, Accion,
                    Resultado, Descripcion, Detalles, IP, AdministradorEmail)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                (str(uuid.uuid4()), usuario_id, usuario_email, tipo, accion,
                 resultado, descripcion, detalles_json, ip, actor_email),
            )
            conn.commit()
        finally:
            conn.close()
    except Exception as e:  # noqa: BLE001
        logger.warning("[RBAC-Bitacora] No se pudo registrar evento: %s", e)


def _map_evento(row) -> Dict[str, Any]:
    detalles = row[7]
    if detalles:
        try:
            detalles = json.loads(detalles)
        except (ValueError, TypeError):
            pass
    fecha = row[1]
    return {
        "id": row[0],
        "timestamp": fecha.isoformat() if hasattr(fecha, "isoformat") else fecha,
        "email": row[2],
        "tipo": row[3],
        "accion": row[4],
        "resultado": row[5],
        "descripcion": row[6],
        "detalles": detalles,
        "ip": row[8],
        "administrador_email": row[9],
    }


_BITACORA_COLS = (
    "EventoUUID, FechaEvento, UsuarioAfectadoEmail, Tipo, Accion, "
    "Resultado, Descripcion, Detalles, IP, AdministradorEmail"
)


def get_bitacora(
    fecha_inicio: Optional[str] = None,
    fecha_fin: Optional[str] = None,
    email: Optional[str] = None,
    resultado: Optional[str] = None,
    tipo: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
) -> Tuple[int, List[Dict[str, Any]]]:
    conn = _connect()
    try:
        cur = conn.cursor()
        where, params = [], []
        if fecha_inicio:
            where.append("FechaEvento >= %s")
            params.append(fecha_inicio)
        if fecha_fin:
            where.append("FechaEvento <= %s")
            params.append(f"{fecha_fin} 23:59:59")
        if email:
            where.append("UsuarioAfectadoEmail LIKE %s")
            params.append(f"%{email}%")
        if resultado:
            where.append("Resultado = %s")
            params.append(resultado)
        if tipo:
            where.append("Tipo = %s")
            params.append(tipo)
        wsql = ("WHERE " + " AND ".join(where)) if where else ""
        cur.execute(f"SELECT COUNT(*) FROM dbo.Usuario_RBAC_Bitacora {wsql}", tuple(params))
        total = cur.fetchone()[0]
        cur.execute(
            f"""SELECT {_BITACORA_COLS} FROM dbo.Usuario_RBAC_Bitacora {wsql}
                ORDER BY FechaEvento DESC, BitacoraID DESC
                OFFSET %s ROWS FETCH NEXT %s ROWS ONLY""",
            tuple(params) + (int(skip), int(limit)),
        )
        eventos = [_map_evento(r) for r in cur.fetchall()]
        return total, eventos
    finally:
        conn.close()


def get_bitacora_evento(evento_id: str) -> Optional[Dict[str, Any]]:
    conn = _connect()
    try:
        cur = conn.cursor()
        cur.execute(
            f"SELECT {_BITACORA_COLS} FROM dbo.Usuario_RBAC_Bitacora WHERE EventoUUID = %s",
            (evento_id,),
        )
        row = cur.fetchone()
        return _map_evento(row) if row else None
    finally:
        conn.close()
