"""
Script DDL para agregar columnas UrlFacebook y Notas a Comercial_Competidores

Ejecutar una vez para actualizar la estructura de la tabla.
Idempotente: verifica si las columnas existen antes de agregarlas.
"""

import os
import sys
sys.path.insert(0, '/app/backend')

from core.db import execute_sql_query
from core.server_registry import EDARSAHUB_CONFIG

def get_conn():
    return (
        EDARSAHUB_CONFIG['host'],
        EDARSAHUB_CONFIG['port'],
        EDARSAHUB_CONFIG['database'],
        EDARSAHUB_CONFIG['username'],
        EDARSAHUB_CONFIG['password']
    )

DDL_STATEMENTS = [
    # Agregar UrlFacebook si no existe
    """
    IF NOT EXISTS (
        SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_NAME = 'Comercial_Competidores' AND COLUMN_NAME = 'UrlFacebook'
    )
    BEGIN
        ALTER TABLE Comercial_Competidores ADD UrlFacebook NVARCHAR(500) NULL;
        PRINT 'Columna UrlFacebook agregada';
    END
    ELSE
    BEGIN
        PRINT 'Columna UrlFacebook ya existe';
    END
    """,
    
    # Agregar Notas si no existe
    """
    IF NOT EXISTS (
        SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_NAME = 'Comercial_Competidores' AND COLUMN_NAME = 'Notas'
    )
    BEGIN
        ALTER TABLE Comercial_Competidores ADD Notas NVARCHAR(1000) NULL;
        PRINT 'Columna Notas agregada';
    END
    ELSE
    BEGIN
        PRINT 'Columna Notas ya existe';
    END
    """
]

def main():
    print("=" * 60)
    print("DDL: Agregar columnas UrlFacebook y Notas a Comercial_Competidores")
    print("=" * 60)
    
    conn = get_conn()
    
    for i, stmt in enumerate(DDL_STATEMENTS, 1):
        print(f"\n[{i}/{len(DDL_STATEMENTS)}] Ejecutando DDL...")
        try:
            execute_sql_query(*conn, stmt)
            print(f"    OK")
        except Exception as e:
            print(f"    ERROR: {e}")
    
    print("\n" + "=" * 60)
    print("DDL completado")
    print("=" * 60)

if __name__ == "__main__":
    main()
