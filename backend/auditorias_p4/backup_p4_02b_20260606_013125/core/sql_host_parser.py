from core.unidades_service import UnidadesService
from core.corporate_filters.service import CorporateFilterService
"""
SQL Server Host Parser

Parsea formatos de host SQL Server:
1. host simple: server.com
2. host con puerto: server.com,6969
3. host con instancia: server.com\\nationalsoft
4. host con puerto e instancia: servercienfuegos.ddns.net,6669\\nationalsoft

Uso:
    from core.sql_host_parser import parse_sql_server_host
    
    config = parse_sql_server_host("servercienfuegos.ddns.net,6669\\nationalsoft", 1433)
    # Resultado:
    # {
    #   "host": "servercienfuegos.ddns.net",
    #   "port": 6669,
    #   "instance": "nationalsoft",
    #   "server_for_pyodbc": "servercienfuegos.ddns.net,6669",
    #   "server_for_pymssql": "servercienfuegos.ddns.net"
    # }
"""

from typing import Dict, Optional, Any
import re


def parse_sql_server_host(raw_host: str, raw_port: Optional[int] = None) -> Dict[str, Any]:
    """
    Parsea un host SQL Server y devuelve configuración normalizada.
    
    Args:
        raw_host: Host en cualquier formato SQL Server
        raw_port: Puerto por defecto (usado solo si raw_host no incluye puerto)
    
    Returns:
        Dict con:
        - host: hostname limpio
        - port: puerto (int)
        - instance: nombre de instancia o None
        - server_for_pyodbc: string para pyodbc
        - server_for_pymssql: string para pymssql
        - raw_host: host original
    """
    if not raw_host:
        return {
            "host": None,
            "port": raw_port or 1433,
            "instance": None,
            "server_for_pyodbc": None,
            "server_for_pymssql": None,
            "raw_host": raw_host
        }
    
    host = raw_host.strip()
    port = None
    instance = None
    
    # Extraer instancia (después de backslash)
    # Formato: server.com\instancia o server.com,puerto\instancia
    if '\\' in host:
        parts = host.split('\\', 1)
        host = parts[0]
        instance = parts[1] if len(parts) > 1 else None
    
    # Extraer puerto (después de coma)
    # Formato: server.com,puerto
    if ',' in host:
        parts = host.split(',', 1)
        host = parts[0]
        try:
            port = int(parts[1])
        except (ValueError, IndexError):
            pass
    
    # Usar puerto raw_port solo si no se extrajo puerto del host
    if port is None:
        port = raw_port if raw_port else 1433
    
    # Construir strings para drivers
    # pyodbc: SERVER=host,port (o SERVER=host\instancia si no hay puerto explícito)
    # pymssql: server=host, port=port
    
    if port and port != 1433:
        server_for_pyodbc = f"{host},{port}"
    elif instance:
        server_for_pyodbc = f"{host}\\{instance}"
    else:
        server_for_pyodbc = host
    
    server_for_pymssql = host
    
    return {
        "host": host,
        "port": port,
        "instance": instance,
        "server_for_pyodbc": server_for_pyodbc,
        "server_for_pymssql": server_for_pymssql,
        "raw_host": raw_host
    }


def get_pymssql_connection_params(raw_host: str, raw_port: Optional[int] = None,
                                   username: str = None, password: str = None,
                                   database: str = None, timeout: int = 30) -> Dict[str, Any]:
    """
    Genera parámetros para pymssql.connect() a partir de host raw.
    
    Args:
        raw_host: Host en cualquier formato SQL Server
        raw_port: Puerto por defecto
        username: Usuario SQL
        password: Password SQL
        database: Nombre de base de datos
        timeout: Timeout en segundos
    
    Returns:
        Dict con parámetros para pymssql.connect()
    """
    parsed = parse_sql_server_host(raw_host, raw_port)
    
    params = {
        "server": parsed["server_for_pymssql"],
        "port": parsed["port"],
        "timeout": timeout
    }
    
    if username:
        params["user"] = username
    if password:
        params["password"] = password
    if database:
        params["database"] = database
    
    return params


def get_pyodbc_connection_string(raw_host: str, raw_port: Optional[int] = None,
                                  username: str = None, password: str = None,
                                  database: str = None, driver: str = None) -> str:
    """
    Genera connection string para pyodbc.connect() a partir de host raw.
    
    Args:
        raw_host: Host en cualquier formato SQL Server
        raw_port: Puerto por defecto
        username: Usuario SQL
        password: Password SQL
        database: Nombre de base de datos
        driver: Driver ODBC (default: ODBC Driver 17 for SQL Server)
    
    Returns:
        Connection string para pyodbc
    """
    parsed = parse_sql_server_host(raw_host, raw_port)
    
    if not driver:
        driver = "ODBC Driver 17 for SQL Server"
    
    parts = [
        f"DRIVER={{{driver}}}",
        f"SERVER={parsed['server_for_pyodbc']}"
    ]
    
    if database:
        parts.append(f"DATABASE={database}")
    if username:
        parts.append(f"UID={username}")
    if password:
        parts.append(f"PWD={password}")
    
    return ";".join(parts)


def test_connection_pymssql(raw_host: str, raw_port: Optional[int] = None,
                            username: str = None, password: str = None,
                            database: str = None, timeout: int = 10) -> Dict[str, Any]:
    """
    Prueba conexión con pymssql.
    
    Returns:
        Dict con:
        - success: bool
        - error: mensaje de error si falló
        - parsed: configuración parseada
        - connection_params: parámetros usados (sin password)
    """
    import pymssql
    
    parsed = parse_sql_server_host(raw_host, raw_port)
    params = get_pymssql_connection_params(raw_host, raw_port, username, password, database, timeout)
    
    # Copia sin password para log
    params_log = {k: v for k, v in params.items() if k != 'password'}
    
    result = {
        "success": False,
        "error": None,
        "parsed": parsed,
        "connection_params": params_log
    }
    
    try:
        conn = pymssql.connect(**params)
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.fetchone()
        conn.close()
        result["success"] = True
    except pymssql.OperationalError as e:
        error_str = str(e)
        if 'Login failed' in error_str or '18456' in error_str:
            result["error"] = "AUTH_FAILED: Credenciales incorrectas"
        elif 'Cannot open database' in error_str:
            result["error"] = f"DB_NOT_FOUND: Base de datos '{database}' no existe"
        elif 'timeout' in error_str.lower():
            result["error"] = "TIMEOUT: Conexión expiró"
        else:
            result["error"] = f"SQL_ERROR: {error_str}"
    except Exception as e:
        result["error"] = f"GENERAL_ERROR: {str(e)}"
    
    return result


# Tests unitarios
if __name__ == "__main__":
    test_cases = [
        ("server.com", None),
        ("server.com", 1433),
        ("server.com,6969", None),
        ("server.com,6969", 1433),  # puerto del host debe ganar
        ("server.com\\nationalsoft", None),
        ("server.com\\nationalsoft", 1433),
        ("servercienfuegos.ddns.net,6669\\nationalsoft", None),
        ("servercienfuegos.ddns.net,6669\\nationalsoft", 1433),  # puerto del host debe ganar
        ("130mid.ddns.net", 1433),
        ("serverestelar.ddns.net,6969", None),
    ]
    
    print("=" * 80)
    print("TEST CASES parse_sql_server_host")
    print("=" * 80)
    
    for raw_host, raw_port in test_cases:
        result = parse_sql_server_host(raw_host, raw_port)
        print(f"\nInput: raw_host='{raw_host}', raw_port={raw_port}")
        print(f"  host: {result['host']}")
        print(f"  port: {result['port']}")
        print(f"  instance: {result['instance']}")
        print(f"  pyodbc: {result['server_for_pyodbc']}")
        print(f"  pymssql: {result['server_for_pymssql']}")
