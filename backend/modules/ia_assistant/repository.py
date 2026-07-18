"""Persistencia SQL canónica del Asistente IA."""

from __future__ import annotations

import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List

from core.sql_first.connection_factory import (
    get_edarsahub_pymssql_connection,
)

logger = logging.getLogger(__name__)


class SchemaNotReadyError(RuntimeError):
    """El esquema SQL obligatorio todavía no está instalado."""


def _connection():
    return get_edarsahub_pymssql_connection(
        timeout=30,
        login_timeout=10,
    )


def _normalize_email(value: str) -> str:
    email = str(value or "").strip().lower()

    if not email:
        raise ValueError(
            "El email del usuario es obligatorio"
        )

    return email


def _normalize_uuid(value: str) -> str:
    return str(uuid.UUID(str(value)))


def _serialize_datetime(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()

    return value


def schema_status() -> Dict[str, Any]:
    conn = None

    try:
        conn = _connection()
        cur = conn.cursor(as_dict=True)

        cur.execute(
            """
            SELECT
                CASE
                    WHEN OBJECT_ID(
                        'dbo.IA_Assistant_Sesiones',
                        'U'
                    ) IS NOT NULL
                    THEN 1
                    ELSE 0
                END AS sesiones_existe,
                CASE
                    WHEN OBJECT_ID(
                        'dbo.IA_Assistant_Mensajes',
                        'U'
                    ) IS NOT NULL
                    THEN 1
                    ELSE 0
                END AS mensajes_existe,
                CASE
                    WHEN EXISTS (
                        SELECT 1
                        FROM sys.foreign_keys
                        WHERE name =
                            'FK_IA_Assistant_Mensajes_Sesion'
                    )
                    THEN 1
                    ELSE 0
                END AS fk_existe
            """
        )

        row = cur.fetchone() or {}

        ready = all(
            bool(row.get(key))
            for key in (
                "sesiones_existe",
                "mensajes_existe",
                "fk_existe",
            )
        )

        return {
            "ready": ready,
            "sesiones_existe": bool(
                row.get("sesiones_existe")
            ),
            "mensajes_existe": bool(
                row.get("mensajes_existe")
            ),
            "fk_existe": bool(
                row.get("fk_existe")
            ),
        }

    except Exception:
        logger.exception(
            "No fue posible validar el esquema IA"
        )

        return {
            "ready": False,
            "sesiones_existe": False,
            "mensajes_existe": False,
            "fk_existe": False,
            "error": "sql_unavailable",
        }

    finally:
        if conn is not None:
            conn.close()


def assert_schema_ready() -> None:
    if not schema_status().get("ready"):
        raise SchemaNotReadyError(
            "El esquema SQL del Asistente IA "
            "no está instalado"
        )


def create_session(
    usuario_email: str,
    titulo: str,
    modelo: str,
) -> Dict[str, Any]:
    assert_schema_ready()

    session_id = str(uuid.uuid4())
    email = _normalize_email(usuario_email)

    title = (
        titulo or "Nueva conversación"
    ).strip()

    title = title[:300] or "Nueva conversación"

    conn = _connection()

    try:
        cur = conn.cursor()

        cur.execute(
            """
            INSERT INTO dbo.IA_Assistant_Sesiones (
                SesionID,
                UsuarioEmail,
                Titulo,
                Modelo,
                Activo
            )
            VALUES (%s, %s, %s, %s, 1)
            """,
            (
                session_id,
                email,
                title,
                modelo,
            ),
        )

        conn.commit()

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()

    return {
        "sesion_id": session_id,
        "titulo": title,
        "modelo": modelo,
    }


def list_sessions(
    usuario_email: str,
) -> List[Dict[str, Any]]:
    assert_schema_ready()

    conn = _connection()

    try:
        cur = conn.cursor(as_dict=True)

        cur.execute(
            """
            SELECT
                CONVERT(
                    NVARCHAR(36),
                    s.SesionID
                ) AS SesionID,
                s.Titulo,
                s.Modelo,
                s.FechaCreacion,
                s.FechaActualizacion,
                (
                    SELECT COUNT(*)
                    FROM dbo.IA_Assistant_Mensajes m
                    WHERE m.SesionID = s.SesionID
                ) AS TotalMensajes
            FROM dbo.IA_Assistant_Sesiones s
            WHERE LOWER(s.UsuarioEmail) = LOWER(%s)
              AND s.Activo = 1
            ORDER BY
                s.FechaActualizacion DESC,
                s.FechaCreacion DESC
            """,
            (
                _normalize_email(
                    usuario_email
                ),
            ),
        )

        rows = cur.fetchall() or []

    finally:
        conn.close()

    return [
        {
            "sesion_id": row.get(
                "SesionID"
            ),
            "titulo": row.get(
                "Titulo"
            ),
            "modelo": row.get(
                "Modelo"
            ),
            "fecha_creacion": (
                _serialize_datetime(
                    row.get("FechaCreacion")
                )
            ),
            "fecha_actualizacion": (
                _serialize_datetime(
                    row.get(
                        "FechaActualizacion"
                    )
                )
            ),
            "total_mensajes": int(
                row.get("TotalMensajes") or 0
            ),
        }
        for row in rows
    ]


def session_exists_for_user(
    sesion_id: str,
    usuario_email: str,
) -> bool:
    assert_schema_ready()

    conn = _connection()

    try:
        cur = conn.cursor(as_dict=True)

        cur.execute(
            """
            SELECT TOP 1
                1 AS ok
            FROM dbo.IA_Assistant_Sesiones
            WHERE SesionID = %s
              AND LOWER(UsuarioEmail) = LOWER(%s)
              AND Activo = 1
            """,
            (
                _normalize_uuid(
                    sesion_id
                ),
                _normalize_email(
                    usuario_email
                ),
            ),
        )

        return bool(cur.fetchone())

    finally:
        conn.close()


def get_messages(
    sesion_id: str,
    usuario_email: str,
) -> List[Dict[str, Any]]:
    assert_schema_ready()

    conn = _connection()

    try:
        cur = conn.cursor(as_dict=True)

        cur.execute(
            """
            SELECT
                m.Rol,
                m.Contenido,
                m.FechaCreacion
            FROM dbo.IA_Assistant_Mensajes m
            INNER JOIN dbo.IA_Assistant_Sesiones s
                ON s.SesionID = m.SesionID
            WHERE m.SesionID = %s
              AND LOWER(s.UsuarioEmail) = LOWER(%s)
              AND s.Activo = 1
            ORDER BY
                m.FechaCreacion,
                m.MensajeID
            """,
            (
                _normalize_uuid(
                    sesion_id
                ),
                _normalize_email(
                    usuario_email
                ),
            ),
        )

        rows = cur.fetchall() or []

    finally:
        conn.close()

    return [
        {
            "rol": row.get("Rol"),
            "contenido": row.get(
                "Contenido"
            ),
            "fecha_creacion": (
                _serialize_datetime(
                    row.get("FechaCreacion")
                )
            ),
        }
        for row in rows
    ]


def deactivate_session(
    sesion_id: str,
    usuario_email: str,
) -> bool:
    assert_schema_ready()

    conn = _connection()

    try:
        cur = conn.cursor()

        cur.execute(
            """
            UPDATE dbo.IA_Assistant_Sesiones
            SET
                Activo = 0,
                FechaActualizacion =
                    SYSUTCDATETIME()
            WHERE SesionID = %s
              AND LOWER(UsuarioEmail) = LOWER(%s)
              AND Activo = 1
            """,
            (
                _normalize_uuid(
                    sesion_id
                ),
                _normalize_email(
                    usuario_email
                ),
            ),
        )

        affected = int(
            cur.rowcount or 0
        )

        conn.commit()

        return affected > 0

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()


def save_exchange(
    sesion_id: str,
    usuario_email: str,
    user_text: str,
    assistant_text: str,
) -> bool:
    assert_schema_ready()

    session_uuid = _normalize_uuid(
        sesion_id
    )

    email = _normalize_email(
        usuario_email
    )

    user_message_id = str(
        uuid.uuid4()
    )

    assistant_message_id = str(
        uuid.uuid4()
    )

    generated_title = (
        user_text.strip()[:80]
    )

    conn = _connection()

    try:
        cur = conn.cursor(as_dict=True)

        cur.execute(
            """
            SELECT TOP 1
                Titulo
            FROM dbo.IA_Assistant_Sesiones
                WITH (UPDLOCK, ROWLOCK)
            WHERE SesionID = %s
              AND LOWER(UsuarioEmail) = LOWER(%s)
              AND Activo = 1
            """,
            (
                session_uuid,
                email,
            ),
        )

        if not cur.fetchone():
            conn.rollback()
            return False

        cur.execute(
            """
            INSERT INTO dbo.IA_Assistant_Mensajes (
                MensajeID,
                SesionID,
                Rol,
                Contenido
            )
            VALUES (%s, %s, %s, %s)
            """,
            (
                user_message_id,
                session_uuid,
                "user",
                user_text,
            ),
        )

        cur.execute(
            """
            INSERT INTO dbo.IA_Assistant_Mensajes (
                MensajeID,
                SesionID,
                Rol,
                Contenido
            )
            VALUES (%s, %s, %s, %s)
            """,
            (
                assistant_message_id,
                session_uuid,
                "assistant",
                assistant_text,
            ),
        )

        cur.execute(
            """
            UPDATE dbo.IA_Assistant_Sesiones
            SET
                Titulo = CASE
                    WHEN Titulo =
                        N'Nueva conversación'
                    THEN %s
                    ELSE Titulo
                END,
                FechaActualizacion =
                    SYSUTCDATETIME()
            WHERE SesionID = %s
              AND LOWER(UsuarioEmail) = LOWER(%s)
              AND Activo = 1
            """,
            (
                generated_title
                or "Nueva conversación",
                session_uuid,
                email,
            ),
        )

        conn.commit()
        return True

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()
