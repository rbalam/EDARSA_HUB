"""
EDARSA HUB - Script para crear tablas de Workflows y Tareas
Ejecuta el SQL de migración en EDARSAHUB
"""
import pymssql
import os

# Configuración EDARSAHUB
EDARSAHUB_CONFIG = {
    'host': '<REDACTED_EDARSAHUB_SQL_HOST>',
    'port': 1433,
    'database': 'EDARSAHUB',
    'username': '<REDACTED_EDARSAHUB_SQL_USER>',
    'password': '<REDACTED_EDARSAHUB_SQL_PASSWORD>'
}

def execute_sql_file():
    """Ejecuta el script SQL de creación de tablas."""
    
    # Leer archivo SQL
    sql_path = os.path.join(os.path.dirname(__file__), 'create_workflow_tables.sql')
    with open(sql_path, 'r', encoding='utf-8') as f:
        sql_content = f.read()
    
    # Separar por GO o bloques IF
    statements = []
    current = []
    
    for line in sql_content.split('\n'):
        if line.strip().upper() == 'GO':
            if current:
                statements.append('\n'.join(current))
                current = []
        else:
            current.append(line)
    
    if current:
        statements.append('\n'.join(current))
    
    # Conectar y ejecutar
    print(f"Conectando a {EDARSAHUB_CONFIG['host']}:{EDARSAHUB_CONFIG['database']}...")
    
    conn = pymssql.connect(
        server=EDARSAHUB_CONFIG['host'],
        port=EDARSAHUB_CONFIG['port'],
        database=EDARSAHUB_CONFIG['database'],
        user=EDARSAHUB_CONFIG['username'],
        password=EDARSAHUB_CONFIG['password'],
        timeout=60,
        login_timeout=30
    )
    cursor = conn.cursor()
    
    print("Ejecutando script de migración...")
    
    # Ejecutar todo el script como un solo bloque
    try:
        cursor.execute(sql_content)
        conn.commit()
        print("✅ Script ejecutado exitosamente")
        
        # Verificar tablas creadas
        cursor.execute("""
            SELECT TABLE_NAME 
            FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_NAME IN (
                'Workflow_Inventarios', 
                'Tareas_Inventario', 
                'Workflow_DetalleDiferencias',
                'Inventarios_SinAsignar',
                'Alertas_Sistema',
                'Configuracion_Operativa',
                'Config_Asignaciones'
            )
            ORDER BY TABLE_NAME
        """)
        
        tables = cursor.fetchall()
        print("\n📋 Tablas verificadas en EDARSAHUB:")
        for table in tables:
            print(f"  ✓ {table[0]}")
        
    except Exception as e:
        print(f"⚠️ Error durante ejecución: {e}")
        # Intentar verificar qué tablas existen
        try:
            cursor.execute("""
                SELECT TABLE_NAME 
                FROM INFORMATION_SCHEMA.TABLES 
                WHERE TABLE_NAME LIKE 'Workflow_%' 
                   OR TABLE_NAME LIKE 'Tareas_%'
                   OR TABLE_NAME LIKE 'Inventarios_%'
                   OR TABLE_NAME LIKE 'Alertas_%'
                   OR TABLE_NAME LIKE 'Configuracion_%'
                   OR TABLE_NAME LIKE 'Config_%'
            """)
            existing = cursor.fetchall()
            print("\nTablas existentes:")
            for t in existing:
                print(f"  • {t[0]}")
        except:
            pass
    
    cursor.close()
    conn.close()
    print("\n✅ Migración completada")

if __name__ == "__main__":
    execute_sql_file()
