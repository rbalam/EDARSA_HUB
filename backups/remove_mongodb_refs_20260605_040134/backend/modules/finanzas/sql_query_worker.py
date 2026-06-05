#!/usr/bin/env python3
"""
EDARSA HUB - SQL Query Worker con Encoding Forzado
===================================================

Este script se ejecuta como subprocess con encoding UTF-8 forzado
para evitar problemas de encoding con pytds en ambiente supervisor.

USO:
    python3 sql_query_worker.py <host> <port> <database> <username> <password> <query_base64>

SALIDA:
    JSON con resultados o error
"""
import sys
import os
import locale
import codecs
import json
import base64
from decimal import Decimal
from datetime import datetime, date

# Forzar encoding UTF-8 de múltiples formas
os.environ['PYTHONIOENCODING'] = 'utf-8'
os.environ['LANG'] = 'C.UTF-8'
os.environ['LC_ALL'] = 'C.UTF-8'
os.environ['LC_CTYPE'] = 'C.UTF-8'

# Intentar establecer locale
try:
    locale.setlocale(locale.LC_ALL, 'C.UTF-8')
except locale.Error:
    try:
        locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
    except locale.Error:
        pass

# Reconfigurar stdout/stderr con UTF-8
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# Reemplazar stdout/stderr con wrappers UTF-8
sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, errors='replace')
sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, errors='replace')


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
    
    Formatos soportados:
    - "servidor" → (servidor, port)
    - "servidor,puerto" → (servidor, puerto)
    - "servidor\\instancia" → (servidor\\instancia, None)  # sin puerto
    - "servidor,puerto\\instancia" → (servidor\\instancia, None)  # instancia ignora puerto
    
    pytds no permite especificar puerto E instancia simultáneamente.
    """
    server = host
    parsed_port = int(port) if port else None
    
    # Verificar si hay instancia (backslash)
    if '\\' in host:
        # Hay instancia - no usar puerto separado
        # El servidor se queda como "host\\instance" pero sin el puerto embebido
        if ',' in host:
            # Formato: servidor,puerto\instancia → extraer servidor\instancia
            parts = host.split(',', 1)
            base_server = parts[0]
            # El resto contiene "puerto\instancia"
            rest = parts[1]
            if '\\' in rest:
                instance = rest.split('\\', 1)[1]
                server = f"{base_server}\\{instance}"
            else:
                # Raro caso pero manejar
                server = host
        # Con instancia, pytds no acepta puerto separado
        parsed_port = None
        
    elif ',' in host:
        # Solo puerto embebido, sin instancia
        parts = host.split(',', 1)
        server = parts[0]
        parsed_port = int(parts[1])
    
    return server, parsed_port


def execute_query(host, port, database, username, password, query):
    """Ejecuta una query SQL y retorna los resultados."""
    import pytds
    
    try:
        # Parsear host para extraer servidor y puerto correctamente
        server, parsed_port = parse_connection_string(host, port)
        
        # Construir parámetros de conexión
        conn_params = {
            'server': server,
            'database': database,
            'user': username,
            'password': password,
            'timeout': 30,
            'login_timeout': 15,
            'bytes_to_unicode': True
        }
        
        # Solo agregar puerto si está definido y no hay instancia
        if parsed_port:
            conn_params['port'] = parsed_port
        
        conn = pytds.connect(**conn_params)
        
        cursor = conn.cursor()
        cursor.execute(query)
        
        # Obtener nombres de columnas
        columns = [desc[0] for desc in cursor.description]
        
        # Leer resultados con manejo de encoding
        results = []
        try:
            all_rows = cursor.fetchall()
        except UnicodeDecodeError as ude:
            # Si falla fetchall por encoding, intentar fila por fila
            all_rows = []
            while True:
                try:
                    row = cursor.fetchone()
                    if row is None:
                        break
                    all_rows.append(row)
                except UnicodeDecodeError:
                    continue  # Saltar fila problemática
                except Exception:
                    break
        
        for row in all_rows:
            try:
                row_dict = {}
                for i, col in enumerate(columns):
                    val = row[i]
                    # Sanitizar valores
                    if isinstance(val, Decimal):
                        val = float(val)
                    elif isinstance(val, (datetime, date)):
                        val = val.isoformat()
                    elif isinstance(val, bytes):
                        val = val.decode('utf-8', errors='replace')
                    elif isinstance(val, str):
                        # Sanitizar strings con caracteres problemáticos
                        val = val.encode('utf-8', errors='replace').decode('utf-8')
                    row_dict[col] = val
                results.append(row_dict)
            except Exception:
                continue  # Saltar fila con error
        
        conn.close()
        
        return {
            "success": True,
            "data": results,
            "count": len(results)
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__
        }


def main():
    if len(sys.argv) != 7:
        print(json.dumps({
            "success": False,
            "error": "Usage: sql_query_worker.py <host> <port> <database> <username> <password> <query_base64>"
        }))
        sys.exit(1)
    
    host = sys.argv[1]
    port = sys.argv[2]
    database = sys.argv[3]
    username = sys.argv[4]
    password = sys.argv[5]
    query_b64 = sys.argv[6]
    
    # Decodificar query
    try:
        query = base64.b64decode(query_b64).decode('utf-8')
    except Exception as e:
        print(json.dumps({
            "success": False,
            "error": f"Error decodificando query: {e}"
        }))
        sys.exit(1)
    
    # Ejecutar query
    result = execute_query(host, port, database, username, password, query)
    
    # Imprimir resultado como JSON
    print(json.dumps(result, default=json_serializer, ensure_ascii=False))


if __name__ == "__main__":
    main()
