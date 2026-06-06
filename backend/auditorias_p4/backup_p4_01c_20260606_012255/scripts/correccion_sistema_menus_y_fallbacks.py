# -*- coding: utf-8 -*-
# correccion_sistema_menus_y_fallbacks.py
import pymssql
import os

DATABASE_CONFIG = {
    "server": os.environ.get('EDARSAHUB_HOST', '<REDACTED_EDARSAHUB_SQL_HOST>'),
    "port": int(os.environ.get('EDARSAHUB_PORT', 1433)),
    "database": os.environ.get('EDARSAHUB_DATABASE', 'EDARSAHUB'),
    "username": os.environ.get('EDARSAHUB_USERNAME', '<REDACTED_EDARSAHUB_SQL_USER>'),
    "password": os.environ.get('EDARSAHUB_PASSWORD', '<REDACTED_EDARSAHUB_SQL_PASSWORD>'),
}

MENUS_DATA = [
    ("Tablero Ejecutivo", "Tablero Ejecutivo", "LayoutDashboard", "kpis", 1, 1, "OPERADOR_EDARSA"),
    ("Marketing CRM", "Marketing CRM", "Users", "crm", 1, 2, "OPERADOR_EDARSA"),
    ("Ventas & Flujos (Emergent)", "Ventas (Emergent)", "Cpu", "flows", 1, 3, "OPERADOR_EDARSA"),
    ("Inventarios FinOps", "Inventarios FinOps", "Database", "costos-placeholder", 1, 4, "OPERADOR_EDARSA"),
    ("Soporte (Tickets)", "Soporte Tareas", "LifeBuoy", "tickets", 1, 5, "OPERADOR_EDARSA")
]

def deploy_menus():
    conn = pymssql.connect(
        server=DATABASE_CONFIG['server'],
        port=DATABASE_CONFIG['port'],
        database=DATABASE_CONFIG['database'],
        user=DATABASE_CONFIG['username'],
        password=DATABASE_CONFIG['password'],
        timeout=30
    )
    cursor = conn.cursor()
    
    try:
        print("[DEPLOY MENUS] Asegurando tabla de menús en SQL remoto...")
        cursor.execute("""
            IF OBJECT_ID('dbo.Sync_Menus', 'U') IS NULL
            BEGIN
                CREATE TABLE dbo.Sync_Menus (
                    id INT IDENTITY(1,1) PRIMARY KEY,
                    titulo NVARCHAR(100) NOT NULL,
                    label NVARCHAR(100) NOT NULL,
                    icon NVARCHAR(50) NOT NULL,
                    route NVARCHAR(100) NOT NULL,
                    active BIT DEFAULT 1,
                    orden INT NOT NULL,
                    rol_permitido NVARCHAR(100) DEFAULT 'OPERADOR_EDARSA',
                    ultima_actualizacion DATETIME DEFAULT GETDATE()
                );
            END;
        """)
        
        cursor.execute("TRUNCATE TABLE dbo.Sync_Menus;")
        
        for menu in MENUS_DATA:
            cursor.execute("""
                INSERT INTO dbo.Sync_Menus (titulo, label, icon, route, active, orden, rol_permitido)
                VALUES (%s, %s, %s, %s, %s, %s, %s);
            """, menu)
        
        conn.commit()
        print("[ÉXITO] Menús dinámicos implantados con éxito.")
        
        # Verificar
        cursor.execute("SELECT COUNT(*) FROM dbo.Sync_Menus")
        count = cursor.fetchone()[0]
        print(f"[VERIFICACIÓN] Total menús: {count}")
        
        return True
    except Exception as e:
        conn.rollback()
        print(f"[ERROR MENUS] Falló el deploy de menús: {str(e)}")
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    deploy_menus()
