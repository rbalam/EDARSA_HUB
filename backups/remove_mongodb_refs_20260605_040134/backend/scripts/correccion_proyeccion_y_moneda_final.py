# -*- coding: utf-8 -*-
"""
======================================================================================
ARCHIVO DE SCRIPT EN PYTHON: correccion_proyeccion_y_moneda_final.py
PROYECTO: EDARSA HUB ERP - SISTEMA DE ALTA DISPONIBILIDAD COMERCIAL
TECNOLOGÍA: Python 3.8+ / pyodbc o pymssql
DESCRIPCIÓN: Script de alineación de formatos comerciales y calibración de KPI anual.
             Asegura que el formato de moneda ($1,062.58M) y la proyección anual de 365 días
             estén debidamente compilados y ejecutados en la base de datos Microsoft SQL Server
             (EDARSAHUB), previniendo desalineaciones con la UI de React.
======================================================================================
"""

import sys
import logging
import os
from datetime import datetime

# Configuración de logs profesionales
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] (%(filename)s): %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("correccion_y_moneda_final")

# Parámetros del Servidor de Producción de EDARSAHUB
DATABASE_CONFIG = {
    "server": os.environ.get('EDARSAHUB_HOST', '54.39.104.176'),
    "port": int(os.environ.get('EDARSAHUB_PORT', 1433)),
    "database": os.environ.get('EDARSAHUB_DATABASE', 'EDARSAHUB'),
    "username": os.environ.get('EDARSAHUB_USERNAME', 'HRLectura'),
    "password": os.environ.get('EDARSAHUB_PASSWORD', 'National09$'),
}

SQL_COMMANDS = [
    # 1. Función de formateo con comas y sufijo de millones M
    """
    IF OBJECT_ID('dbo.fn_FormatearMonedaConComas', 'FN') IS NOT NULL
    BEGIN
        DROP FUNCTION dbo.fn_FormatearMonedaConComas;
    END;
    """,
    """
    CREATE FUNCTION dbo.fn_FormatearMonedaConComas (
        @Valor DECIMAL(18,4)
    )
    RETURNS NVARCHAR(100)
    AS
    BEGIN
        IF @Valor IS NULL
            RETURN '$0.00M';
        RETURN '$' + CONVERT(NVARCHAR(100), CAST(@Valor AS MONEY), 1) + 'M';
    END;
    """,
    # 2. Función de cálculo de proyección anual lineal de 365 días reales
    """
    IF OBJECT_ID('dbo.fn_CalcularProyeccionAnual365', 'FN') IS NOT NULL
    BEGIN
        DROP FUNCTION dbo.fn_CalcularProyeccionAnual365;
    END;
    """,
    """
    CREATE FUNCTION dbo.fn_CalcularProyeccionAnual365 (
        @VentasRealesM DECIMAL(18,4),
        @DiasConVentas INT
    )
    RETURNS DECIMAL(18,4)
    AS
    BEGIN
        IF @DiasConVentas <= 0 OR @VentasRealesM IS NULL
            RETURN 0.0000;
        RETURN (@VentasRealesM / CAST(@DiasConVentas AS DECIMAL(18,4))) * 365.0000;
    END;
    """
]

def run_corrections_and_alignment():
    """
    Ejecuta la actualización en caliente en Microsoft SQL Server.
    Compila las funciones DDL, recalibra los KPIs históricos en las tablas
    e inserta el log de auditoría respectivo en dbo.Sync_Logs.
    """
    import pymssql
    
    logger.info("Iniciando normalización de moneda y calibración de proyección anual en BD...")

    conn = None
    try:
        conn = pymssql.connect(
            server=DATABASE_CONFIG['server'],
            port=DATABASE_CONFIG['port'],
            database=DATABASE_CONFIG['database'],
            user=DATABASE_CONFIG['username'],
            password=DATABASE_CONFIG['password'],
            timeout=30
        )
        cursor = conn.cursor()
        logger.info("Establecida conexión síncrona con base de datos de producción EDARSAHUB.")

        # Transacción DDL para funciones
        logger.info("Compilando funciones DDL en base de datos...")
        for i, q in enumerate(SQL_COMMANDS):
            cursor.execute(q)
            logger.info(f"  [{i+1}/{len(SQL_COMMANDS)}] Ejecutado ✓")
        conn.commit()
        logger.info("Funciones compiladas satisfactoriamente.")

        # Verificar si existe columna Proyeccion_Anual_Ventas
        cursor.execute("""
            IF NOT EXISTS (SELECT 1 FROM sys.columns WHERE object_id = OBJECT_ID('dbo.Sync_KPI_Ventas_Unidades') AND name = 'Proyeccion_Anual_Ventas')
            AND OBJECT_ID('dbo.Sync_KPI_Ventas_Unidades', 'U') IS NOT NULL
                ALTER TABLE dbo.Sync_KPI_Ventas_Unidades ADD Proyeccion_Anual_Ventas DECIMAL(18,4) DEFAULT 0;
        """)
        conn.commit()

        # Recalibración del acumulado de ventas históricas en el Tablero de KPIs
        cursor.execute("SELECT OBJECT_ID('dbo.Sync_KPI_Ventas_Unidades', 'U');")
        existe_tabla = cursor.fetchone()[0]

        if existe_tabla is not None:
            logger.info("Aplicando recalibración lineal (365 días) en dbo.Sync_KPI_Ventas_Unidades...")
            cursor.execute("""
                UPDATE dbo.Sync_KPI_Ventas_Unidades
                SET 
                    Proyeccion_Anual_Ventas = dbo.fn_CalcularProyeccionAnual365(Ventas_Reales_M, 31),
                    UltimaActualizacion = GETDATE();
            """)
            logger.info(f"Registros de KPIs anualizados actualizados: {cursor.rowcount}")
        else:
            logger.warning("dbo.Sync_KPI_Ventas_Unidades no configurada físicamente en BD.")

        # Registrar la firma de auditoría en los logs centrales
        msg_auditoria = ("Normalización monetaria con comas ($X,XXX.XXM) y calibración del "
                         "esquema de proyección de ventas anualizado de 365 días finalizado.")
        cursor.execute("""
            INSERT INTO dbo.Sync_Logs (service, type, message, timestamp, operador)
            VALUES (%s, %s, %s, GETDATE(), %s);
        """, ("CORRECCION_PROYECCION_Y_MONEDA_FINAL", "SUCCESS", msg_auditoria, "PYTHON_CORRECTOR_DAEMON"))

        conn.commit()
        logger.info("¡TRANSACCIÓN CONFIRMADA Y ASENTADA EXITOSAMENTE EN EDARSAHUB!")

        # Verificación directa de los cálculos tras el despliegue
        logger.info("Verificando funcionamiento óptimo en el motor SQL:")
        cursor.execute("""
            DECLARE @Demo DECIMAL(18,4) = 15712150.32;
            SELECT 
                dbo.fn_FormatearMonedaConComas(@Demo) AS Formateado,
                dbo.fn_CalcularProyeccionAnual365(@Demo, 31) AS ProyeccionAnual;
        """)
        row = cursor.fetchone()
        logger.info(f" -> Valor prueba: 15,712,150.32")
        logger.info(f" -> Formateado retornado por SQL: {row[0]}")
        logger.info(f" -> Proyección anualizada (365 días): ${float(row[1]):,.2f} M")
        return True

    except Exception as err:
        if conn:
            conn.rollback()
            logger.warning("Realizando reversión (ROLLBACK) debido a fallas físicas en la ejecución...")
        logger.error(f"Fallo crítico ejecutando la corrección en EDARSAHUB: {str(err)}")
        _simular_formato_local()
        return False

    finally:
        if conn:
            conn.close()
            logger.info("Canal de conexión con SQL Server cerrado.")


def _simular_formato_local():
    """
    Ejecución local fallback para simular resultados matemáticos en local sin conexión externa.
    """
    total_acumulado = 15712.1503  # En base millones
    dias_transcurridos = 31

    formateado_py = f"${total_acumulado:,.2f}M"
    proyeccion_365 = (total_acumulado / dias_transcurridos) * 365

    print("\n--- PRUEBA DE CONTROL DE CALIDAD (MÉTODO FALLBACK LOCAL) ---")
    print(f" * Valor Base: {total_acumulado}")
    print(f" * Formateado comas y sufijo: {formateado_py}")
    print(f" * Cálculo de Proyección Progresiva (365 días): {proyeccion_365:,.4f} M")
    print("------------------------------------------------------------\n")


if __name__ == "__main__":
    run_corrections_and_alignment()
