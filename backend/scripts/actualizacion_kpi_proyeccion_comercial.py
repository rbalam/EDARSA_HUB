# -*- coding: utf-8 -*-
# actualizacion_kpi_proyeccion_comercial.py
# Convertido de Node.js a Python para ejecución en Emergent
import pymssql
import os
from datetime import datetime
import calendar

DATABASE_CONFIG = {
    "server": os.environ.get('EDARSAHUB_HOST', '54.39.104.176'),
    "port": int(os.environ.get('EDARSAHUB_PORT', 1433)),
    "database": os.environ.get('EDARSAHUB_DATABASE', 'EDARSAHUB'),
    "username": os.environ.get('EDARSAHUB_USERNAME', 'HRLectura'),
    "password": os.environ.get('EDARSAHUB_PASSWORD', 'National09$'),
}

def get_days_in_month(month_name, year):
    """Retorna la cantidad exacta de días en el mes"""
    months = {
        'enero': 1, 'febrero': 2, 'marzo': 3, 'abril': 4, 'mayo': 5, 'junio': 6,
        'julio': 7, 'agosto': 8, 'septiembre': 9, 'octubre': 10, 'noviembre': 11, 'diciembre': 12
    }
    month_index = months.get(month_name.lower(), datetime.now().month)
    return calendar.monthrange(year, month_index)[1]

def recalibrate_kpi_month(month_name='Mayo', year=2026, dias_con_ventas=30.0):
    """Recalibra las proyecciones KPI para un mes específico"""
    days_in_month = get_days_in_month(month_name, year)
    
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
        print(f"[KPI PYTHON] % Mes: {month_name.upper()} | Días Calculados: {days_in_month}")
        
        # Primero verificar si existe la tabla
        cursor.execute("""
            IF OBJECT_ID('dbo.Sync_KPI_Ventas_Unidades', 'U') IS NULL
            BEGIN
                CREATE TABLE dbo.Sync_KPI_Ventas_Unidades (
                    id INT IDENTITY(1,1) PRIMARY KEY,
                    UnidadID VARCHAR(50) NOT NULL,
                    UnidadNombre NVARCHAR(100) NOT NULL,
                    Mes VARCHAR(50) NOT NULL,
                    Anio INT NOT NULL,
                    Ventas_Reales_M DECIMAL(18,4) DEFAULT 0,
                    Proyeccion_Ventas DECIMAL(18,4) DEFAULT 0,
                    Meta_Mensual DECIMAL(18,4) DEFAULT 0,
                    PorcentajeCumplimiento DECIMAL(5,2) DEFAULT 0,
                    UltimaActualizacion DATETIME DEFAULT GETDATE()
                );
                CREATE INDEX IX_KPI_Mes_Anio ON dbo.Sync_KPI_Ventas_Unidades (Mes, Anio);
            END
        """)
        conn.commit()
        
        # Ejecutar la actualización
        query = """
            UPDATE dbo.Sync_KPI_Ventas_Unidades
            SET 
                Proyeccion_Ventas = CAST((Ventas_Reales_M / %s) * %s AS DECIMAL(18, 4)),
                UltimaActualizacion = GETDATE()
            WHERE LOWER(Mes) = LOWER(%s) AND Anio = %s;
        """
        
        cursor.execute(query, (dias_con_ventas, days_in_month, month_name, year))
        rows_affected = cursor.rowcount
        conn.commit()
        
        print(f"[ÉXITO] Recalibradas {rows_affected} filas.")
        
        # Verificar datos
        cursor.execute("SELECT COUNT(*) FROM dbo.Sync_KPI_Ventas_Unidades")
        total = cursor.fetchone()[0]
        print(f"[VERIFICACIÓN] Total registros KPI: {total}")
        
        return True
    except Exception as e:
        conn.rollback()
        print(f"[ERROR]: {str(e)}")
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    recalibrate_kpi_month('Mayo', 2026, 30.0)
