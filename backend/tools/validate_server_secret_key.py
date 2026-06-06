import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from core.secret_manager import decrypt_secret
except Exception as exc:
    print("IMPORT_ERROR=core.secret_manager.decrypt_secret")
    print(f"ERROR_TYPE={type(exc).__name__}")
    print(f"ERROR={exc}")
    sys.exit(1)

try:
    from core.guards.server_secret_guard import require_server_secret_key
except Exception as exc:
    print("IMPORT_ERROR=core.guards.server_secret_guard")
    print(f"ERROR_TYPE={type(exc).__name__}")
    print(f"ERROR={exc}")
    sys.exit(1)

from core.db import execute_sql_query

EDARSAHUB = {
    "host": os.getenv('EDARSAHUB_SQL_HOST'),
    "port": 1433,
    "database": "EDARSAHUB",
    "user": os.getenv('EDARSAHUB_SQL_USER'),
    "password": os.getenv('EDARSAHUB_SQL_PASSWORD')
}


def main():
    key = os.getenv("SERVER_SECRET_KEY")

    print("SERVER_SECRET_KEY_STATUS=", "CONFIGURADA" if key else "NO_CONFIGURADA")
    print("SERVER_SECRET_KEY_LENGTH=", len(key) if key else 0)

    try:
        require_server_secret_key()
    except Exception as exc:
        print("RESULT=FAIL")
        print("REASON=", str(exc))
        sys.exit(1)

    rows = execute_sql_query(
        EDARSAHUB["host"], EDARSAHUB["port"], EDARSAHUB["database"],
        EDARSAHUB["user"], EDARSAHUB["password"],
        """
        SELECT
            nombre,
            system_type,
            tipo_conexion,
            CASE
                WHEN password_encrypted IS NULL OR LTRIM(RTRIM(password_encrypted)) = '' THEN 0
                ELSE 1
            END AS tiene_password,
            CASE
                WHEN api_key_encrypted IS NULL OR LTRIM(RTRIM(api_key_encrypted)) = '' THEN 0
                ELSE 1
            END AS tiene_api_key,
            password_encrypted,
            api_key_encrypted
        FROM dbo.Servidores_Conexiones
        WHERE activo = 1
          AND (
                password_encrypted IS NOT NULL
                OR api_key_encrypted IS NOT NULL
              )
        ORDER BY nombre
        """
    )

    total = 0
    ok = 0
    fail = 0

    print("=== DECRYPT VALIDATION ===")

    for row in rows:
        nombre = row["nombre"]
        system_type = row["system_type"]
        tipo_conexion = row["tipo_conexion"]

        if row["tiene_password"]:
            total += 1
            try:
                value = decrypt_secret(row["password_encrypted"])
                if value:
                    ok += 1
                    print(
                        f"{nombre} | {system_type} | {tipo_conexion} | "
                        f"PASSWORD_DECRYPT=OK | LENGTH={len(value)}"
                    )
                else:
                    fail += 1
                    print(
                        f"{nombre} | {system_type} | {tipo_conexion} | "
                        "PASSWORD_DECRYPT=EMPTY"
                    )
            except Exception as exc:
                fail += 1
                print(
                    f"{nombre} | {system_type} | {tipo_conexion} | "
                    f"PASSWORD_DECRYPT=FAIL | {type(exc).__name__}: {exc}"
                )

        if row["tiene_api_key"]:
            total += 1
            try:
                value = decrypt_secret(row["api_key_encrypted"])
                if value:
                    ok += 1
                    print(
                        f"{nombre} | {system_type} | {tipo_conexion} | "
                        f"API_KEY_DECRYPT=OK | LENGTH={len(value)}"
                    )
                else:
                    fail += 1
                    print(
                        f"{nombre} | {system_type} | {tipo_conexion} | "
                        "API_KEY_DECRYPT=EMPTY"
                    )
            except Exception as exc:
                fail += 1
                print(
                    f"{nombre} | {system_type} | {tipo_conexion} | "
                    f"API_KEY_DECRYPT=FAIL | {type(exc).__name__}: {exc}"
                )

    print("=== SUMMARY ===")
    print(f"TOTAL_SECRETS={total}")
    print(f"DECRYPT_OK={ok}")
    print(f"DECRYPT_FAIL={fail}")

    if fail > 0:
        print("RESULT=FAIL")
        sys.exit(1)

    print("RESULT=OK")


if __name__ == "__main__":
    main()
