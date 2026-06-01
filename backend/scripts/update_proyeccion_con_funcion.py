# -*- coding: utf-8 -*-
# update_proyeccion_con_funcion.py - Recalculación Masiva
import pymssql
import os

DATABASE_CONFIG = {
    "server": os.environ.get('EDARSAHUB_HOST', '54.39.104.176'),
    "port": int(os.environ.get('EDARSAHUB_PORT', 1433)),
    "database": os.environ.get('EDARSAHUB_DATABASE', 'EDARSAHUB'),
    "username": os.environ.get('EDARSAHUB_USERNAME', 'HRLectura'),
    "password": os.environ.get('EDARSAHUB_PASSWORD', 'National09$'),
}

def execute_projection_update(anio=2026):
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
        print(f"[PROYECCIÓN PYTHON] Actualizando base transaccional para {anio}...")
        
        # Primero crear la función si no existe
        cursor.execute("""
            IF OBJECT_ID('dbo.fn_CalcularProyeccionMensual', 'FN') IS NULL
            BEGIN
                EXEC('
                CREATE FUNCTION dbo.fn_CalcularProyeccionMensual (
                    @VentasRealesM DECIMAL(18,4),
                    @DiasConVentas DECIMAL(10,2),
                    @Mes VARCHAR(50),
                    @Anio INT
                )
                RETURNS DECIMAL(18,4)
                AS
                BEGIN
                    DECLARE @DiasTotales INT;
                    DECLARE @MesNum INT = CASE LOWER(@Mes)
                        WHEN ''enero'' THEN 1 WHEN ''febrero'' THEN 2 WHEN ''marzo'' THEN 3
                        WHEN ''abril'' THEN 4 WHEN ''mayo'' THEN 5 WHEN ''junio'' THEN 6
                        WHEN ''julio'' THEN 7 WHEN ''agosto'' THEN 8 WHEN ''septiembre'' THEN 9
                        WHEN ''octubre'' THEN 10 WHEN ''noviembre'' THEN 11 WHEN ''diciembre'' THEN 12
                        ELSE 1
                    END;
                    SET @DiasTotales = DAY(EOMONTH(DATEFROMPARTS(@Anio, @MesNum, 1)));
                    IF @DiasConVentas <= 0 OR @VentasRealesM IS NULL
                        RETURN 0.0000;
                    RETURN CAST((@VentasRealesM / @DiasConVentas) * @DiasTotales AS DECIMAL(18,4));
                END
                ')
            END
        """)
        conn.commit()
        
        # Ejecutar actualización
        cursor.execute("""
            UPDATE dbo.Sync_KPI_Ventas_Unidades
            SET 
                Proyeccion_Ventas = dbo.fn_CalcularProyeccionMensual(
                    Ventas_Reales_M, 
                    ISNULL(Dias_Con_Ventas, CASE WHEN Mes = 'Mayo' THEN 30.0 ELSE DAY(EOMONTH(DATEFROMPARTS(Anio, 5, 1))) END),
                    Mes, 
                    Anio
                ),
                UltimaActualizacion = GETDATE()
            WHERE Anio = %s;
        """, (anio,))
        
        rows_affected = cursor.rowcount
        
        # Log de auditoría
        cursor.execute("""
            INSERT INTO dbo.Sync_Logs (service, type, message, timestamp, operador)
            VALUES ('PYTHON_PROY_DAEMON', 'SUCCESS', %s, GETDATE(), 'EMERGENT_PY_WORKER');
        """, (f'Actualizadas {rows_affected} filas aplicando función escalar para el {anio}.',))
        
        conn.commit()
        print(f"[ÉXITO] Actualización de proyecciones completada: {rows_affected} registros.")
        return True
    except Exception as e:
        conn.rollback()
        print(f"[ERROR] Descartando transacción: {str(e)}")
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    execute_projection_update(2026)
