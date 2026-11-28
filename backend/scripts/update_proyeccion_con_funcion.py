# -*- coding: utf-8 -*-
# update_proyeccion_con_funcion.py - Recalculación Masiva
import pymssql
import os

DATABASE_CONFIG = {
    "server": os.environ.get('EDARSAHUB_HOST', os.getenv('EDARSAHUB_SQL_HOST')),
    "port": int(os.environ.get('EDARSAHUB_PORT', 1433)),
    "database": os.environ.get('EDARSAHUB_DATABASE', 'EDARSAHUB'),
    "username": os.environ.get('EDARSAHUB_USERNAME', os.getenv('EDARSAHUB_SQL_USER')),
    "password": os.environ.get('EDARSAHUB_PASSWORD', os.getenv('EDARSAHUB_SQL_PASSWORD')),
}

def ejecutar_proyeccion_masiva(anio=2026):
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
        print("[PROYECCION DAEMON] Ejecutando calculador síncrono en SQL...")
        cursor.execute("""
            UPDATE dbo.Sync_KPI_Ventas_Unidades
            SET 
                Proyeccion_Ventas = dbo.fn_CalcularProyeccionMensual(
                    Ventas_Reales_M, 
                    Dias_Con_Ventas,
                    Mes, 
                    Anio
                ),
                UltimaActualizacion = GETDATE()
            WHERE Anio = %s;
        """, (anio,))
        
        filas_actualizadas = cursor.rowcount
        
        cursor.execute("""
            INSERT INTO dbo.Sync_Logs (service, type, message, timestamp, operador)
            VALUES (%s, %s, %s, GETDATE(), %s);
        """, ("UPDATE_PROY_DAEMON", "SUCCESS", f"Actualizadas {filas_actualizadas} unidades para el {anio}.", "EMERGENT_PYTHON"))
        
        conn.commit()
        print(f" -> ¡Transacción Exitosa! {filas_actualizadas} períodos actualizados.")
        return True
    except Exception as e:
        conn.rollback()
        print(f" -> [ERROR] Error en actualización: {str(e)}")
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    ejecutar_proyeccion_masiva(2026)
