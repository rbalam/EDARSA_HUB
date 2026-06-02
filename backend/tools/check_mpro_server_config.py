import argparse
import os
import sys
from sqlalchemy import create_engine, text

try:
    from core.secret_manager import decrypt_secret
except Exception:
    decrypt_secret = None


def get_engine():
    db_url = (
        os.getenv("DATABASE_URL")
        or os.getenv("SQLALCHEMY_DATABASE_URL")
        or os.getenv("EDARSAHUB_DATABASE_URL")
    )
    if not db_url:
        raise RuntimeError("No se encontró URL de EDARSAHUB SQL")
    return create_engine(db_url, pool_pre_ping=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--unidad", required=True, help="Ejemplo: 130QRO u ORIGEN")
    args = parser.parse_args()

    engine = get_engine()

    with engine.connect() as conn:
        row = conn.execute(text("""
            SELECT TOP 1
                u.codigo AS unidad_codigo,
                u.nombre AS unidad_nombre,
                u.system_type AS unidad_system_type,
                s.id AS servidor_id,
                s.nombre AS servidor_nombre,
                s.system_type AS servidor_system_type,
                s.tipo_conexion,
                s.host,
                s.port,
                s.database_name,
                s.api_url,
                s.api_key_encrypted,
                s.username,
                s.password_encrypted,
                s.activo,
                s.visible_en_operaciones,
                s.source_status,
                s.ultimo_error_sync
            FROM dbo.Unidades_Negocio u
            INNER JOIN dbo.Servidores_Conexiones s
                ON CONVERT(NVARCHAR(100), u.server_id) = CONVERT(NVARCHAR(100), s.id)
            WHERE u.codigo = :unidad
               OR u.nombre LIKE :unidad_like
            ORDER BY u.orden, u.nombre
        """), {
            "unidad": args.unidad,
            "unidad_like": f"%{args.unidad}%"
        }).mappings().first()

    if not row:
        raise RuntimeError(f"No se encontró servidor para unidad {args.unidad}")

    print("=== MPRO SERVER CONFIG ===")
    print(f"unidad_codigo={row['unidad_codigo']}")
    print(f"unidad_nombre={row['unidad_nombre']}")
    print(f"unidad_system_type={row['unidad_system_type']}")
    print(f"servidor_nombre={row['servidor_nombre']}")
    print(f"servidor_system_type={row['servidor_system_type']}")
    print(f"tipo_conexion={row['tipo_conexion']}")
    print(f"host={row['host']}")
    print(f"port={row['port']}")
    print(f"database_name={row['database_name']}")
    print(f"api_url_status={'CONFIGURADA' if row['api_url'] else 'SIN_API_URL'}")
    print(f"api_key_status={'CONFIGURADA' if row['api_key_encrypted'] else 'SIN_API_KEY'}")
    print(f"sql_user_status={'CONFIGURADO' if row['username'] else 'SIN_USUARIO_SQL'}")
    print(f"sql_password_status={'CONFIGURADO' if row['password_encrypted'] else 'SIN_PASSWORD_SQL'}")
    print(f"activo={row['activo']}")
    print(f"visible_en_operaciones={row['visible_en_operaciones']}")
    print(f"source_status={row['source_status']}")
    print(f"ultimo_error_sync={row['ultimo_error_sync']}")

    if row["api_url"]:
        print("CONCLUSION=MPRO_API_CONFIGURADA")
    elif row["username"] and row["password_encrypted"]:
        print("CONCLUSION=MPRO_SQL_DIRECTO_CONFIGURADO")
    else:
        print("CONCLUSION=CONFIGURACION_INCOMPLETA_O_REQUIERE_ADAPTADOR")

    if row["api_key_encrypted"] and decrypt_secret:
        try:
            key = decrypt_secret(row["api_key_encrypted"])
            print("API_KEY_DECRYPT_STATUS=OK")
            print("API_KEY_LENGTH=", len(key) if key else 0)
        except Exception as e:
            print("API_KEY_DECRYPT_STATUS=FAIL")
            print("API_KEY_ERROR_TYPE=", type(e).__name__)
            print("API_KEY_ERROR=", str(e))


if __name__ == "__main__":
    main()
