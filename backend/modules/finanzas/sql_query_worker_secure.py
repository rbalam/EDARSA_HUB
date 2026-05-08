#!/usr/bin/env python3
"""
EDARSA HUB - SQL Query Worker (Secure)
======================================

Worker que ejecuta queries SQL y lee credenciales desde stdin.

FINANZAS-CXP-MPRO-CREDENTIALS-SECURITY-01:
- Credenciales vienen por stdin como JSON, NO por argumentos CLI
- Esto evita que el password sea visible en `ps aux` o `/proc/[pid]/cmdline`
- NUNCA imprimir credenciales a stdout/stderr

USO:
    echo '{"host":"...", "port":1433, ...}' | python sql_query_worker_secure.py

ENTRADA (stdin JSON):
    {
        "host": "server.example.com",
        "port": 1433,
        "database": "mydatabase",
        "username": "user",
        "password": "secret",
        "query_b64": "U0VMRUNUIFRPUCAxMCAqIEZST00gbXl0YWJsZQ=="
    }

SALIDA (stdout JSON):
    {"success": true, "data": [...], "count": N}
    O
    {"success": false, "error": "...", "error_type": "..."}
"""

import sys
import json
import base64
from datetime import datetime, date
from decimal import Decimal


def json_serializer(obj):
    """Serializa tipos especiales a JSON."""
    import uuid
    if isinstance(obj, Decimal):
        return float(obj)
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    if isinstance(obj, bytes):
        return obj.decode('utf-8', errors='replace')
    if isinstance(obj, uuid.UUID):
        return str(obj)
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


def parse_connection_string(host, port):
    """
    Parsea el host para extraer servidor y puerto.
    
    En pytds, la instancia se pasa como parte del servidor: "servidor\\instancia"
    y el puerto se especifica separadamente (pero NO junto con instancia).
    """
    server = host
    parsed_port = int(port) if port else None
    
    if '\\' in host:
        if ',' in host:
            parts = host.split(',', 1)
            base_server = parts[0]
            rest = parts[1]
            if '\\' in rest:
                instance = rest.split('\\', 1)[1]
                server = f"{base_server}\\{instance}"
            else:
                server = host
        parsed_port = None
        
    elif ',' in host:
        parts = host.split(',', 1)
        server = parts[0]
        parsed_port = int(parts[1])
    
    return server, parsed_port


def execute_query(host, port, database, username, password, query):
    """Ejecuta una query SQL y retorna los resultados."""
    import pytds
    
    try:
        server, parsed_port = parse_connection_string(host, port)
        
        conn_params = {
            'server': server,
            'database': database,
            'user': username,
            'password': password,
            'timeout': 30,
            'login_timeout': 15,
            'bytes_to_unicode': True
        }
        
        if parsed_port:
            conn_params['port'] = parsed_port
        
        conn = pytds.connect(**conn_params)
        
        try:
            cursor = conn.cursor()
            cursor.execute(query)
            
            columns = [desc[0] for desc in cursor.description] if cursor.description else []
            rows = cursor.fetchall()
            
            results = []
            for row in rows:
                row_dict = {}
                for i, col in enumerate(columns):
                    row_dict[col] = row[i]
                results.append(row_dict)
            
            return {
                "success": True,
                "data": results,
                "count": len(results)
            }
        finally:
            conn.close()
            
    except Exception as e:
        # SEGURIDAD: No incluir credenciales en el mensaje de error
        error_msg = str(e)
        # Remover password si accidentalmente aparece
        if password and password in error_msg:
            error_msg = error_msg.replace(password, '***')
        
        return {
            "success": False,
            "error": error_msg,
            "error_type": type(e).__name__
        }


def main():
    """Lee credenciales de stdin y ejecuta la query."""
    try:
        # Leer JSON de stdin
        stdin_data = sys.stdin.read()
        
        if not stdin_data:
            print(json.dumps({
                "success": False,
                "error": "No input received on stdin",
                "error_type": "NO_INPUT"
            }))
            return
        
        # Parsear JSON
        try:
            payload = json.loads(stdin_data)
        except json.JSONDecodeError as e:
            print(json.dumps({
                "success": False,
                "error": f"Invalid JSON input: {e}",
                "error_type": "JSON_ERROR"
            }))
            return
        
        # Extraer credenciales
        host = payload.get('host', '')
        port = payload.get('port', 1433)
        database = payload.get('database', '')
        username = payload.get('username', '')
        password = payload.get('password', '')
        query_b64 = payload.get('query_b64', '')
        
        # Validar campos requeridos
        if not all([host, database, username, query_b64]):
            print(json.dumps({
                "success": False,
                "error": "Missing required fields: host, database, username, query_b64",
                "error_type": "MISSING_FIELDS"
            }))
            return
        
        # Decodificar query
        try:
            query = base64.b64decode(query_b64).decode('utf-8')
        except Exception as e:
            print(json.dumps({
                "success": False,
                "error": f"Failed to decode query: {e}",
                "error_type": "DECODE_ERROR"
            }))
            return
        
        # Ejecutar query
        result = execute_query(host, port, database, username, password, query)
        
        # Output JSON
        print(json.dumps(result, default=json_serializer, ensure_ascii=False))
        
    except Exception as e:
        print(json.dumps({
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__
        }))


if __name__ == "__main__":
    main()
