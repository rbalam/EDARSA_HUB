#!/usr/bin/env python3
"""
TEST SQL CONNECTION FROM SERVIDORES_CONEXIONES
==============================================
Prueba conexión SQL a un servidor usando credenciales
de Servidores_Conexiones (descifrando password).

Uso:
    python tools/test_sql_connection_from_servidores.py --unidad CIENFUEGOS
    python tools/test_sql_connection_from_servidores.py --server-name-like ManagmentPro

Autor: Agente E1
Fecha: 2026-06-02
"""

import argparse
import os
import sys

# Agregar backend al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.db import execute_sql_query

# Configuración EDARSAHUB
EDARSAHUB = {
    "host": "<REDACTED_EDARSAHUB_SQL_HOST>",
    "port": 1433,
    "database": "EDARSAHUB",
    "user": "<REDACTED_EDARSAHUB_SQL_USER>",
    "password": "<REDACTED_EDARSAHUB_SQL_PASSWORD>"
}


def get_server_config_by_unidad(unidad: str) -> dict:
    """Obtiene config del servidor asignado a una unidad."""
    query = f"""
    SELECT TOP 1
        u.codigo AS unidad_codigo,
        u.nombre AS unidad_nombre,
        u.sucursal_origen_id,
        s.id AS servidor_id,
        s.nombre AS servidor_nombre,
        s.system_type,
        s.tipo_conexion,
        s.host,
        s.port,
        s.database_name,
        s.username,
        s.password_encrypted
    FROM dbo.Unidades_Negocio u
    INNER JOIN dbo.Servidores_Conexiones s
        ON CONVERT(NVARCHAR(100), u.server_id) = CONVERT(NVARCHAR(100), s.id)
    WHERE u.codigo = '{unidad}'
       OR u.nombre LIKE '%{unidad}%'
    """
    
    result = execute_sql_query(
        EDARSAHUB["host"], EDARSAHUB["port"], EDARSAHUB["database"],
        EDARSAHUB["user"], EDARSAHUB["password"], query
    )
    
    return result[0] if result else None


def get_server_config_by_name(name_like: str) -> dict:
    """Obtiene config de servidor por nombre."""
    query = f"""
    SELECT TOP 1
        id AS servidor_id,
        nombre AS servidor_nombre,
        system_type,
        tipo_conexion,
        host,
        port,
        database_name,
        username,
        password_encrypted
    FROM dbo.Servidores_Conexiones
    WHERE nombre LIKE '%{name_like}%'
      AND tipo_conexion = 'DATA_SOURCE'
      AND activo = 1
    """
    
    result = execute_sql_query(
        EDARSAHUB["host"], EDARSAHUB["port"], EDARSAHUB["database"],
        EDARSAHUB["user"], EDARSAHUB["password"], query
    )
    
    return result[0] if result else None


def test_connection(config: dict) -> dict:
    """Prueba conexión al servidor POS."""
    result = {
        "servidor": config.get("servidor_nombre"),
        "host": config.get("host"),
        "port": config.get("port"),
        "database": config.get("database_name"),
        "username": config.get("username"),
        "decrypt_status": None,
        "connection_status": None,
        "test_query_status": None,
        "error": None
    }
    
    # 1. Verificar credenciales
    if not config.get("username"):
        result["error"] = "SIN_USUARIO"
        result["connection_status"] = "FAIL"
        return result
    
    if not config.get("password_encrypted"):
        result["error"] = "SIN_PASSWORD"
        result["connection_status"] = "FAIL"
        return result
    
    # 2. Descifrar password
    try:
        from core.secret_manager import decrypt_secret
        password = decrypt_secret(config["password_encrypted"])
        
        if not password:
            result["decrypt_status"] = "FAIL"
            result["error"] = "DECRYPT_VACIO"
            result["connection_status"] = "FAIL"
            return result
        
        result["decrypt_status"] = "OK"
        
    except Exception as e:
        result["decrypt_status"] = "FAIL"
        result["error"] = f"DECRYPT_ERROR: {type(e).__name__}"
        result["connection_status"] = "FAIL"
        return result
    
    # 3. Probar conexión
    try:
        host = config.get("host", "")
        port = config.get("port", 1433)
        database = config.get("database_name", "")
        username = config.get("username", "")
        
        # Query de prueba simple
        test_result = execute_sql_query(
            host, port, database, username, password,
            "SELECT 1 AS test_connection"
        )
        
        if test_result:
            result["connection_status"] = "OK"
            result["test_query_status"] = "OK"
        else:
            result["connection_status"] = "FAIL"
            result["error"] = "QUERY_SIN_RESULTADO"
            
    except Exception as e:
        result["connection_status"] = "FAIL"
        error_msg = str(e)
        
        if "inicio de sesión" in error_msg.lower() or "login" in error_msg.lower():
            result["error"] = "LOGIN_FAILED"
        elif "timeout" in error_msg.lower():
            result["error"] = "TIMEOUT"
        elif "unavailable" in error_msg.lower() or "connection refused" in error_msg.lower():
            result["error"] = "SERVER_UNAVAILABLE"
        else:
            result["error"] = f"CONNECTION_ERROR: {type(e).__name__}"
    
    return result


def main():
    parser = argparse.ArgumentParser(
        description="Prueba conexión SQL usando credenciales de Servidores_Conexiones"
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--unidad", help="Código de unidad (ej: CIENFUEGOS, 130QRO)")
    group.add_argument("--server-name-like", help="Nombre parcial del servidor (ej: ManagmentPro)")
    
    args = parser.parse_args()
    
    print("=" * 70)
    print("TEST SQL CONNECTION FROM SERVIDORES_CONEXIONES")
    print("=" * 70)
    print()
    
    # 1. Verificar SERVER_SECRET_KEY
    print("1. VERIFICAR SERVER_SECRET_KEY")
    print("-" * 40)
    
    key = os.getenv("SERVER_SECRET_KEY")
    if not key:
        print("   STATUS: NO_CONFIGURADA")
        print()
        print("=" * 70)
        print("RESULT=FAIL")
        print("REASON=SERVER_SECRET_KEY no configurada")
        print("ACTION=Configurar SERVER_SECRET_KEY antes de continuar")
        print("=" * 70)
        return 1
    
    print("   STATUS: CONFIGURADA")
    print(f"   LENGTH: {len(key)}")
    
    # 2. Obtener configuración del servidor
    print()
    print("2. OBTENER CONFIGURACIÓN")
    print("-" * 40)
    
    if args.unidad:
        print(f"   BUSCANDO: Unidad '{args.unidad}'")
        config = get_server_config_by_unidad(args.unidad)
        if config:
            print(f"   UNIDAD: {config.get('unidad_codigo')} - {config.get('unidad_nombre')}")
            if config.get('sucursal_origen_id'):
                print(f"   SUCURSAL: {config.get('sucursal_origen_id')}")
    else:
        print(f"   BUSCANDO: Servidor '{args.server_name_like}'")
        config = get_server_config_by_name(args.server_name_like)
    
    if not config:
        print("   STATUS: NO_ENCONTRADO")
        print()
        print("=" * 70)
        print("RESULT=FAIL")
        print("REASON=No se encontró servidor/unidad")
        print("=" * 70)
        return 1
    
    print(f"   SERVIDOR: {config.get('servidor_nombre')}")
    print(f"   SYSTEM_TYPE: {config.get('system_type')}")
    print(f"   TIPO_CONEXION: {config.get('tipo_conexion')}")
    print(f"   HOST: {config.get('host')}:{config.get('port')}")
    print(f"   DATABASE: {config.get('database_name')}")
    print(f"   USUARIO: {'CONFIGURADO' if config.get('username') else 'SIN_USUARIO'}")
    print(f"   PASSWORD: {'ENCRYPTED' if config.get('password_encrypted') else 'SIN_PASSWORD'}")
    
    # 3. Probar conexión
    print()
    print("3. PROBAR CONEXIÓN")
    print("-" * 40)
    
    result = test_connection(config)
    
    print(f"   DECRYPT: {result['decrypt_status']}")
    print(f"   CONNECTION: {result['connection_status']}")
    
    if result.get('test_query_status'):
        print(f"   TEST_QUERY: {result['test_query_status']}")
    
    if result.get('error'):
        print(f"   ERROR: {result['error']}")
    
    # 4. Resultado final
    print()
    print("=" * 70)
    
    if result['connection_status'] == "OK":
        print("RESULT=OK")
        print(f"SERVIDOR={config.get('servidor_nombre')}")
        print(f"HOST={config.get('host')}")
        print(f"DATABASE={config.get('database_name')}")
        print("Conexión exitosa - Puede proceder con dry-run")
        print("=" * 70)
        return 0
    else:
        print("RESULT=FAIL")
        print(f"SERVIDOR={config.get('servidor_nombre')}")
        print(f"ERROR={result.get('error')}")
        print("No ejecutar dry-run hasta resolver el error")
        print("=" * 70)
        return 1


if __name__ == "__main__":
    sys.exit(main())
