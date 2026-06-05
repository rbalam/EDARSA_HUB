# -*- coding: utf-8 -*-
# actualizacion_kpi_proyeccion_comercial.py
import calendar
from datetime import datetime
import pymssql
import os

DATABASE_CONFIG = {
    "server": os.environ.get('EDARSAHUB_HOST', '54.39.104.176'),
    "port": int(os.environ.get('EDARSAHUB_PORT', 1433)),
    "database": os.environ.get('EDARSAHUB_DATABASE', 'EDARSAHUB'),
    "username": os.environ.get('EDARSAHUB_USERNAME', 'HRLectura'),
    "password": os.environ.get('EDARSAHUB_PASSWORD', 'National09$'),
}

def recalibrar_kpi_mes(mes_nombre="Mayo", anio=2026, dias_con_ventas=30.0):
    meses_map = {
        "enero": 1, "febrero": 2, "marzo": 3, "abril": 4, "mayo": 5, "junio": 6,
        "julio": 7, "agosto": 8, "septiembre": 9, "octubre": 10, "noviembre": 11, "diciembre": 12
    }
    mes_clean = mes_nombre.strip().lower()
    mes_num = meses_map.get(mes_clean, datetime.now().month)
    _, dias_totales = calendar.monthrange(anio, mes_num)
    
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
        print(f"[RECALIBRACION KPI] Aplicando tendencia para mes de {dias_totales} días totales...")
        
        # Asegurar tabla existe
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
            END
        """)
        conn.commit()
        
        cursor.execute("""
            UPDATE dbo.Sync_KPI_Ventas_Unidades
            SET 
                Proyeccion_Ventas = CAST((Ventas_Reales_M / %s) * %s AS DECIMAL(18, 4)),
                UltimaActualizacion = GETDATE()
            WHERE LOWER(Mes) = LOWER(%s) AND Anio = %s;
        """, (dias_con_ventas, dias_totales, mes_nombre, anio))
        
        filas = cursor.rowcount
        conn.commit()
        print(f"[KPI ÉXITO] Recalibradas {filas} registros en SQL Server.")
        return True
    except Exception as e:
        conn.rollback()
        print(f"[KPI ERROR] Falló el KPI dinámico: {str(e)}")
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    recalibrar_kpi_mes("Mayo", 2026, 30.0)
