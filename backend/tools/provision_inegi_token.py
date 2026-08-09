"""
Provisionador seguro del token INEGI.

REGLAS:
- No contiene token hardcodeado.
- Lee token exclusivamente desde variable de entorno INEGI_API_TOKEN.
- Exige SERVER_SECRET_KEY.
- Cifra con core.secret_manager.encrypt_secret.
- Falla si el resultado no queda realmente cifrado.
- No activa proveedor, serie ni scheduler.
- Solo actualiza la conexión INEGI existente.
"""

import os

from core.connections.edarsahub_writer_connection import (
    open_validated_writer_connection,
)
from core.guards.server_secret_guard import (
    require_server_secret_key,
)
from core.secret_manager import (
    encrypt_secret,
    is_encrypted_secret,
)


def build_encrypted_token() -> str:
    require_server_secret_key()

    token = os.getenv("INEGI_API_TOKEN", "").strip()

    if not token:
        raise RuntimeError(
            "INEGI_API_TOKEN no está configurado"
        )

    encrypted = encrypt_secret(token)

    if not is_encrypted_secret(encrypted):
        raise RuntimeError(
            "El token INEGI no pudo cifrarse; operación abortada"
        )

    return encrypted


def provision_encrypted_token(
    encrypted_token: str,
    connection_factory=open_validated_writer_connection,
) -> None:
    """
    Persiste exclusivamente el secreto cifrado de la conexión INEGI.

    Guardrails:
    - exactamente una conexión INEGI;
    - la conexión debe permanecer inactiva;
    - nunca modifica proveedor, serie ni scheduler;
    - UPDATE parametrizado;
    - transacción explícita;
    - rollback ante cualquier error;
    - valida estado final antes del commit.
    """
    if not is_encrypted_secret(encrypted_token):
        raise RuntimeError(
            "Se rechazó token INEGI no cifrado"
        )

    opened = connection_factory()

    if (
        isinstance(opened, tuple)
        and len(opened) == 2
    ):
        conn, _identity = opened
    else:
        # Compatibilidad exclusiva con factories inyectadas
        # por tests offline.
        conn = opened

    try:
        cur = conn.cursor()

        cur.execute(
            """
            SELECT
                id,
                activo
            FROM dbo.Servidores_Conexiones
            WHERE system_type = %s
            """,
            ("INEGI",),
        )

        rows = cur.fetchall()

        if len(rows) != 1:
            raise RuntimeError(
                "Se requiere exactamente una conexión INEGI"
            )

        connection_id, activo = rows[0]

        if bool(activo):
            raise RuntimeError(
                "La conexión INEGI debe permanecer inactiva "
                "durante la provisión"
            )

        cur.execute(
            """
            UPDATE dbo.Servidores_Conexiones
            SET
                api_key_encrypted = %s
            WHERE id = %s
              AND system_type = %s
              AND activo = 0
            """,
            (
                encrypted_token,
                connection_id,
                "INEGI",
            ),
        )

        if cur.rowcount != 1:
            raise RuntimeError(
                "La actualización del token INEGI no afectó "
                "exactamente una fila"
            )

        cur.execute(
            """
            SELECT
                activo,
                CASE
                    WHEN api_key_encrypted IS NULL THEN 0
                    WHEN LTRIM(RTRIM(api_key_encrypted)) = '' THEN 0
                    ELSE 1
                END AS token_set
            FROM dbo.Servidores_Conexiones
            WHERE id = %s
              AND system_type = %s
            """,
            (
                connection_id,
                "INEGI",
            ),
        )

        validation = cur.fetchone()

        if not validation:
            raise RuntimeError(
                "No fue posible validar la conexión INEGI"
            )

        activo_final, token_set = validation

        if bool(activo_final):
            raise RuntimeError(
                "INEGI fue activado inesperadamente; abortando"
            )

        if int(token_set or 0) != 1:
            raise RuntimeError(
                "El token INEGI no quedó persistido"
            )

        conn.commit()

    except Exception:
        try:
            conn.rollback()
        finally:
            raise

    finally:
        conn.close()


def main() -> None:
    """
    Provisiona el token cifrado sin activar INEGI.

    La ejecución de este entrypoint sí realiza DML.
    No debe ejecutarse hasta la fase explícita de provisión real.
    """
    encrypted = build_encrypted_token()
    provision_encrypted_token(encrypted)

    print("INEGI_TOKEN_PRESENTE=SI")
    print("INEGI_TOKEN_CIFRADO=SI")
    print("SQL_DML_EJECUTADO=SI")
    print("INEGI_ACTIVADO=NO")


if __name__ == "__main__":
    main()
