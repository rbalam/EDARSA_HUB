import os

# Lista de archivos a eliminar por ser conexiones en vivo no permitidas
archivos_a_borrar = [
    'backend/core/server_connection_manager.py',
    'backend/modules/automatizacion/detection_service.py'
]

print("--- Iniciando Migración Limpiadora SQL-ONLY ---")

# 1. Borrado de servicios de conexión en vivo
for archivo in archivos_a_borrar:
    if os.path.exists(archivo):
        os.remove(archivo)
        print(f"✅ Eliminado: {archivo}")

# 2. Limpieza de dependencias en requirements.txt
req_path = 'backend/requirements.txt'
if os.path.exists(req_path):
    with open(req_path, 'r') as f:
        lineas = f.readlines()
    with open(req_path, 'w') as f:
        for linea in lineas:
            if 'pymongo' not in linea and 'motor' not in linea:
                f.write(linea)
    print("✅ Limpiado: requirements.txt (eliminado pymongo/motor)")

# 3. Centralización del motor SQL en db.py
db_content = """from core.pool import pooled_connection
from typing import List, Dict, Any

def execute_hub_query(query: str, params: tuple = None) -> List[Dict[str, Any]]:
    # Conexión única a SQL Server centralizado
    with pooled_connection() as conn:
        cursor = conn.cursor(as_dict=True)
        cursor.execute(query, params or ())
        return list(cursor.fetchall())
"""
with open('backend/core/db.py', 'w') as f:
    f.write(db_content)
print("✅ Actualizado: core/db.py ahora es SQL-Only")
print("--- Migración finalizada exitosamente ---")
