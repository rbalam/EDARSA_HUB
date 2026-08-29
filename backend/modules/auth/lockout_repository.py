"""
Auth Lockout Repository - SQL Only
==================================
Protección contra fuerza bruta: bloquea temporalmente una cuenta tras
N intentos fallidos de login. Persiste en SQL Server (sin MongoDB).

Tabla: dbo.Sistema_Seguridad_LoginIntentos (se crea de forma idempotente).
"""
import logging
from typing import Optional
from core.sql_first.db import get_sql_connection

logger = logging.getLogger(__name__)

# Constantes de política (no son credenciales; configurables por código)
MAX_INTENTOS = 5          # intentos fallidos antes de bloquear
BLOQUEO_MINUTOS = 15      # duración del bloqueo


def _ensure_table(cur) -> None:
    """Crea la tabla de intentos de login si no existe (idempotente)."""
    cur.execute(
        """
        IF NOT EXISTS (
            SELECT 1 FROM sys.tables WHERE name = 'Sistema_Seguridad_LoginIntentos'
        )
        CREATE TABLE dbo.Sistema_Seguridad_LoginIntentos (
            Identificador   NVARCHAR(320) NOT NULL PRIMARY KEY,
            Intentos        INT           NOT NULL CONSTRAINT DF_SSLI_Intentos DEFAULT (0),
            BloqueadoHasta  DATETIME2     NULL,
            UltimoIntento   DATETIME2     NOT NULL CONSTRAINT DF_SSLI_Ultimo DEFAULT (SYSUTCDATETIME())
        )
        """
    )


def check_lockout(email: str) -> Optional[str]:
    """
    Devuelve la marca de tiempo (ISO) hasta la que la cuenta está bloqueada,
    o None si no está bloqueada. Fail-open ante errores de infraestructura.
    """
    ident = (email or "").strip().lower()
    if not ident:
        return None
    conn = get_sql_connection()
    cur = conn.cursor()
    try:
        _ensure_table(cur)
        cur.execute(
            """
            SELECT CONVERT(NVARCHAR(33), BloqueadoHasta, 126)
            FROM dbo.Sistema_Seguridad_LoginIntentos
            WHERE Identificador = %s
              AND BloqueadoHasta IS NOT NULL
              AND BloqueadoHasta > SYSUTCDATETIME()
            """,
            (ident,),
        )
        row = cur.fetchone()
        conn.commit()
        return row[0] if row else None
    except Exception as e:
        logger.warning(f"[Lockout] check_lockout fail-open para {ident}: {e}")
        try:
            conn.rollback()
        except Exception:
            pass
        return None


def register_failed_attempt(email: str) -> None:
    """Registra un intento fallido; bloquea la cuenta al alcanzar MAX_INTENTOS."""
    ident = (email or "").strip().lower()
    if not ident:
        return
    conn = get_sql_connection()
    cur = conn.cursor()
    try:
        _ensure_table(cur)
        cur.execute(
            """
            UPDATE dbo.Sistema_Seguridad_LoginIntentos
            SET Intentos = Intentos + 1, UltimoIntento = SYSUTCDATETIME()
            WHERE Identificador = %s
            """,
            (ident,),
        )
        if cur.rowcount == 0:
            cur.execute(
                """
                INSERT INTO dbo.Sistema_Seguridad_LoginIntentos
                    (Identificador, Intentos, UltimoIntento)
                VALUES (%s, 1, SYSUTCDATETIME())
                """,
                (ident,),
            )
        cur.execute(
            "SELECT Intentos FROM dbo.Sistema_Seguridad_LoginIntentos WHERE Identificador = %s",
            (ident,),
        )
        row = cur.fetchone()
        intentos = int(row[0]) if row else 0
        if intentos >= MAX_INTENTOS:
            # Bloquear y reiniciar el contador para la próxima ventana
            cur.execute(
                """
                UPDATE dbo.Sistema_Seguridad_LoginIntentos
                SET BloqueadoHasta = DATEADD(MINUTE, %s, SYSUTCDATETIME()), Intentos = 0
                WHERE Identificador = %s
                """,
                (BLOQUEO_MINUTOS, ident),
            )
            logger.warning(f"[Lockout] Cuenta {ident} bloqueada por {BLOQUEO_MINUTOS} min")
        conn.commit()
    except Exception as e:
        logger.warning(f"[Lockout] register_failed_attempt error para {ident}: {e}")
        try:
            conn.rollback()
        except Exception:
            pass


def clear_attempts(email: str) -> None:
    """Limpia intentos fallidos tras un login exitoso."""
    ident = (email or "").strip().lower()
    if not ident:
        return
    conn = get_sql_connection()
    cur = conn.cursor()
    try:
        _ensure_table(cur)
        cur.execute(
            "DELETE FROM dbo.Sistema_Seguridad_LoginIntentos WHERE Identificador = %s",
            (ident,),
        )
        conn.commit()
    except Exception as e:
        logger.warning(f"[Lockout] clear_attempts error para {ident}: {e}")
        try:
            conn.rollback()
        except Exception:
            pass
