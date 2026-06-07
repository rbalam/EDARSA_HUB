from core.unidades_service import UnidadesService
from core.corporate_filters.service import CorporateFilterService
"""
CENTRO DE CONTROL EDARSA - Gestión de Destinatarios de Alertas
===============================================================
P5-3D (NO-MONGO / SQL-First): los destinatarios se almacenan en EDARSAHUB SQL,
tabla dbo.Sistema_AlertasDestinatarios (ColeccionOrigen='alert_recipients').
El detalle del destinatario vive en PayloadMongo (JSON).

PayloadMongo (nuevo formato):
{
    "tipo": "email" | "whatsapp",
    "destinatario": "email@example.com" | "+521234567890",
    "nombre": "Nombre opcional",
    "activo": true,
    "created_at": "ISO-8601",
    "created_by": "user_email"
}
Compatibilidad: filas migradas usan extended-JSON (created_at: {"$date": ...}).
"""

import os
import json
import uuid
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

from core.sql_first.connection_factory import get_edarsahub_pymssql_connection

logger = logging.getLogger(__name__)

TABLE = "dbo.Sistema_AlertasDestinatarios"
COLECCION = "alert_recipients"


# ============================================================================
# HELPERS SQL / PAYLOAD
# ============================================================================

def _conn():
    return get_edarsahub_pymssql_connection(timeout=15, login_timeout=10)


def _parse_payload(payload_str: Optional[str]) -> Dict[str, Any]:
    try:
        return json.loads(payload_str) if payload_str else {}
    except Exception:
        return {}


def _created_at_iso(payload: Dict[str, Any]) -> Optional[str]:
    """Normaliza created_at desde JSON nuevo (str) o migrado ({'$date': ...})."""
    ca = payload.get("created_at")
    if isinstance(ca, dict):
        return ca.get("$date")
    return ca


def _row_to_recipient(row_id: Any, payload: Dict[str, Any], activo_col: Any) -> Dict[str, Any]:
    return {
        "id": str(row_id),
        "tipo": payload.get("tipo"),
        "destinatario": payload.get("destinatario"),
        "nombre": payload.get("nombre"),
        "activo": bool(activo_col),
        "created_at": _created_at_iso(payload),
        "created_by": payload.get("created_by"),
    }


# ============================================================================
# CRUD OPERATIONS (SQL-First)
# ============================================================================

def get_all_recipients(tipo: Optional[str] = None, solo_activos: bool = True) -> List[Dict[str, Any]]:
    """Obtiene todos los destinatarios de alertas desde SQL."""
    sql = (
        f"SELECT Id, PayloadMongo, Activo, FechaCreacion FROM {TABLE} "
        "WHERE ColeccionOrigen = %s"
    )
    params: list = [COLECCION]
    if solo_activos:
        sql += " AND Activo = 1"
    sql += " ORDER BY FechaCreacion DESC"

    conn = _conn()
    try:
        cur = conn.cursor(as_dict=True)
        cur.execute(sql, tuple(params))
        rows = cur.fetchall() or []
    finally:
        conn.close()

    recipients: List[Dict[str, Any]] = []
    for r in rows:
        payload = _parse_payload(r["PayloadMongo"])
        if tipo and payload.get("tipo") != tipo:
            continue
        recipients.append(_row_to_recipient(r["Id"], payload, r["Activo"]))
    return recipients


def get_email_recipients() -> List[str]:
    """Obtiene lista de emails activos para alertas"""
    recipients = get_all_recipients(tipo="email", solo_activos=True)
    return [r["destinatario"] for r in recipients if r.get("destinatario")]


def get_whatsapp_recipients() -> List[str]:
    """Obtiene lista de números WhatsApp activos para alertas"""
    recipients = get_all_recipients(tipo="whatsapp", solo_activos=True)
    return [r["destinatario"] for r in recipients if r.get("destinatario")]


def add_recipient(
    tipo: str,
    destinatario: str,
    nombre: Optional[str] = None,
    created_by: Optional[str] = None
) -> Dict[str, Any]:
    """Agrega un nuevo destinatario de alertas (SQL)."""
    # Validar tipo
    if tipo not in ["email", "whatsapp"]:
        raise ValueError("Tipo debe ser 'email' o 'whatsapp'")

    # Validar destinatario
    destinatario = (destinatario or "").strip()
    if not destinatario:
        raise ValueError("Destinatario no puede estar vacío")

    # Para WhatsApp, asegurar formato E.164
    if tipo == "whatsapp":
        if not destinatario.startswith("+"):
            destinatario = "+" + destinatario
        destinatario = destinatario.replace(" ", "").replace("-", "")

    # Verificar duplicado (mismo tipo+destinatario)
    for existing in get_all_recipients(solo_activos=False):
        if existing.get("tipo") == tipo and existing.get("destinatario") == destinatario:
            raise ValueError(f"El destinatario {destinatario} ya existe")

    new_id = str(uuid.uuid4())
    created_at = datetime.now(timezone.utc).isoformat()
    payload = {
        "tipo": tipo,
        "destinatario": destinatario,
        "nombre": nombre,
        "activo": True,
        "created_at": created_at,
        "created_by": created_by,
    }

    conn = _conn()
    try:
        cur = conn.cursor()
        cur.execute(
            f"INSERT INTO {TABLE} "
            "(Id, MongoId, ColeccionOrigen, PayloadMongo, MigradoDesdeMongo, Activo, FechaMigracion, FechaCreacion) "
            "VALUES (%s, %s, %s, %s, 0, 1, GETDATE(), GETDATE())",
            (new_id, uuid.uuid4().hex, COLECCION, json.dumps(payload, ensure_ascii=False)),
        )
        conn.commit()
    finally:
        conn.close()

    logger.info(f"[RECIPIENTS] Nuevo destinatario agregado (SQL): {tipo} - {destinatario}")
    return {
        "id": new_id,
        "tipo": tipo,
        "destinatario": destinatario,
        "nombre": nombre,
        "activo": True,
        "created_at": created_at,
        "created_by": created_by,
    }


def update_recipient(
    recipient_id: str,
    activo: Optional[bool] = None,
    nombre: Optional[str] = None
) -> Dict[str, Any]:
    """Actualiza un destinatario existente (SQL)."""
    if activo is None and nombre is None:
        raise ValueError("No hay datos para actualizar")

    conn = _conn()
    try:
        cur = conn.cursor(as_dict=True)
        cur.execute(
            f"SELECT Id, PayloadMongo, Activo FROM {TABLE} WHERE Id = %s AND ColeccionOrigen = %s",
            (recipient_id, COLECCION),
        )
        row = cur.fetchone()
        if not row:
            raise ValueError("Destinatario no encontrado")

        payload = _parse_payload(row["PayloadMongo"])
        if nombre is not None:
            payload["nombre"] = nombre
        nuevo_activo = bool(activo) if activo is not None else bool(row["Activo"])
        payload["activo"] = nuevo_activo

        cur2 = conn.cursor()
        cur2.execute(
            f"UPDATE {TABLE} SET PayloadMongo = %s, Activo = %s, FechaActualizacion = GETDATE() "
            "WHERE Id = %s AND ColeccionOrigen = %s",
            (json.dumps(payload, ensure_ascii=False), 1 if nuevo_activo else 0, recipient_id, COLECCION),
        )
        conn.commit()
    finally:
        conn.close()

    logger.info(f"[RECIPIENTS] Destinatario actualizado (SQL): {recipient_id}")
    return _row_to_recipient(recipient_id, payload, nuevo_activo)


def delete_recipient(recipient_id: str) -> bool:
    """Elimina un destinatario (SQL)."""
    conn = _conn()
    try:
        cur = conn.cursor()
        cur.execute(
            f"DELETE FROM {TABLE} WHERE Id = %s AND ColeccionOrigen = %s",
            (recipient_id, COLECCION),
        )
        affected = cur.rowcount
        conn.commit()
    finally:
        conn.close()

    if not affected:
        raise ValueError("Destinatario no encontrado")

    logger.info(f"[RECIPIENTS] Destinatario eliminado (SQL): {recipient_id}")
    return True


def get_recipients_summary() -> Dict[str, Any]:
    """Obtiene un resumen de los destinatarios configurados."""
    email_recipients = get_all_recipients(tipo="email", solo_activos=True)
    whatsapp_recipients = get_all_recipients(tipo="whatsapp", solo_activos=True)

    return {
        "email": {
            "count": len(email_recipients),
            "recipients": [
                {
                    "id": r["id"],
                    "destinatario": r["destinatario"][:3] + "***" + r["destinatario"][r["destinatario"].find("@"):] if r.get("destinatario") and "@" in r["destinatario"] else "***",
                    "nombre": r.get("nombre")
                }
                for r in email_recipients
            ]
        },
        "whatsapp": {
            "count": len(whatsapp_recipients),
            "recipients": [
                {
                    "id": r["id"],
                    "destinatario": r["destinatario"][:5] + "***" + r["destinatario"][-4:] if r.get("destinatario") and len(r["destinatario"]) > 9 else "***",
                    "nombre": r.get("nombre")
                }
                for r in whatsapp_recipients
            ]
        },
        "total": len(email_recipients) + len(whatsapp_recipients)
    }
