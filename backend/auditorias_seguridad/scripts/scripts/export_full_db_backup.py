#!/usr/bin/env python3
"""
EDARSAHUB - Export Full Database Backup
Genera DDL + Data de todas las tablas en formato SQL
"""

import os
import sys
import json
import pymssql
from datetime import datetime, date
from decimal import Decimal

# Configuración
BACKUP_DIR = sys.argv[1] if len(sys.argv) > 1 else "/app/downloads/EDARSAHUB_BACKUP"

HOST = os.environ.get("EDARSAHUB_HOST", "<REDACTED_EDARSAHUB_SQL_HOST>")
PORT = int(os.environ.get("EDARSAHUB_PORT", "1433"))
DATABASE = os.environ.get("EDARSAHUB_DATABASE", "EDARSAHUB")
USER = os.environ.get("EDARSAHUB_USERNAME", "<REDACTED_EDARSAHUB_SQL_USER>")
PASSWORD = os.environ.get("EDARSAHUB_PASSWORD", "<REDACTED_EDARSAHUB_SQL_PASSWORD>")

def get_connection():
    return pymssql.connect(
        server=HOST,
        port=PORT,
        user=USER,
        password=PASSWORD,
        database=DATABASE,
        as_dict=True
    )

def serialize_value(val):
    """Serializa un valor para INSERT SQL"""
    if val is None:
        return "NULL"
    elif isinstance(val, bool):
        return "1" if val else "0"
    elif isinstance(val, (int, float, Decimal)):
        return str(val)
    elif isinstance(val, datetime):
        return f"'{val.strftime('%Y-%m-%d %H:%M:%S')}'"
    elif isinstance(val, date):
        return f"'{val.strftime('%Y-%m-%d')}'"
    elif isinstance(val, bytes):
        return f"0x{val.hex()}"
    else:
        # Escapar comillas simples
        escaped = str(val).replace("'", "''")
        return f"N'{escaped}'"

def export_table_ddl(cursor, table_name):
    """Obtiene el DDL aproximado de una tabla"""
    ddl_lines = []
    
    # Obtener columnas
    cursor.execute(f"""
        SELECT 
            c.COLUMN_NAME,
            c.DATA_TYPE,
            c.CHARACTER_MAXIMUM_LENGTH,
            c.NUMERIC_PRECISION,
            c.NUMERIC_SCALE,
            c.IS_NULLABLE,
            c.COLUMN_DEFAULT
        FROM INFORMATION_SCHEMA.COLUMNS c
        WHERE c.TABLE_NAME = '{table_name}' AND c.TABLE_SCHEMA = 'dbo'
        ORDER BY c.ORDINAL_POSITION
    """)
    columns = cursor.fetchall()
    
    if not columns:
        return None
    
    ddl_lines.append(f"-- =================================================")
    ddl_lines.append(f"-- Tabla: {table_name}")
    ddl_lines.append(f"-- Exportado: {datetime.now().isoformat()}")
    ddl_lines.append(f"-- =================================================")
    ddl_lines.append(f"")
    ddl_lines.append(f"IF OBJECT_ID('dbo.{table_name}', 'U') IS NOT NULL")
    ddl_lines.append(f"    DROP TABLE dbo.{table_name};")
    ddl_lines.append(f"GO")
    ddl_lines.append(f"")
    ddl_lines.append(f"CREATE TABLE dbo.{table_name} (")
    
    col_defs = []
    for col in columns:
        col_name = col['COLUMN_NAME']
        data_type = col['DATA_TYPE'].upper()
        max_len = col['CHARACTER_MAXIMUM_LENGTH']
        precision = col['NUMERIC_PRECISION']
        scale = col['NUMERIC_SCALE']
        nullable = col['IS_NULLABLE']
        default = col['COLUMN_DEFAULT']
        
        # Construir tipo de dato
        if data_type in ('VARCHAR', 'NVARCHAR', 'CHAR', 'NCHAR'):
            if max_len == -1:
                type_str = f"{data_type}(MAX)"
            else:
                type_str = f"{data_type}({max_len})"
        elif data_type in ('DECIMAL', 'NUMERIC'):
            type_str = f"{data_type}({precision},{scale})"
        elif data_type == 'FLOAT' and precision:
            type_str = f"FLOAT({precision})"
        else:
            type_str = data_type
        
        # NULL/NOT NULL
        null_str = "NULL" if nullable == 'YES' else "NOT NULL"
        
        # Default
        default_str = ""
        if default:
            default_str = f" DEFAULT {default}"
        
        col_defs.append(f"    [{col_name}] {type_str} {null_str}{default_str}")
    
    ddl_lines.append(",\n".join(col_defs))
    ddl_lines.append(");")
    ddl_lines.append("GO")
    ddl_lines.append("")
    
    # Obtener índices
    cursor.execute(f"""
        SELECT 
            i.name AS index_name,
            i.type_desc,
            i.is_unique,
            i.is_primary_key,
            STRING_AGG(c.name, ', ') WITHIN GROUP (ORDER BY ic.key_ordinal) AS columns
        FROM sys.indexes i
        INNER JOIN sys.index_columns ic ON i.object_id = ic.object_id AND i.index_id = ic.index_id
        INNER JOIN sys.columns c ON ic.object_id = c.object_id AND ic.column_id = c.column_id
        WHERE i.object_id = OBJECT_ID('dbo.{table_name}')
        GROUP BY i.name, i.type_desc, i.is_unique, i.is_primary_key
    """)
    indexes = cursor.fetchall()
    
    for idx in indexes:
        if idx['is_primary_key']:
            ddl_lines.append(f"ALTER TABLE dbo.{table_name} ADD CONSTRAINT [{idx['index_name']}] PRIMARY KEY ({idx['columns']});")
        elif idx['is_unique']:
            ddl_lines.append(f"CREATE UNIQUE INDEX [{idx['index_name']}] ON dbo.{table_name} ({idx['columns']});")
        elif idx['index_name']:
            ddl_lines.append(f"CREATE INDEX [{idx['index_name']}] ON dbo.{table_name} ({idx['columns']});")
    
    ddl_lines.append("GO")
    ddl_lines.append("")
    
    return "\n".join(ddl_lines)

def export_table_data(cursor, table_name, batch_size=1000):
    """Exporta los datos de una tabla en formato INSERT"""
    # Obtener columnas
    cursor.execute(f"""
        SELECT COLUMN_NAME
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_NAME = '{table_name}' AND TABLE_SCHEMA = 'dbo'
        ORDER BY ORDINAL_POSITION
    """)
    columns = [row['COLUMN_NAME'] for row in cursor.fetchall()]
    
    if not columns:
        return None, 0
    
    # Contar registros
    cursor.execute(f"SELECT COUNT(*) AS cnt FROM dbo.[{table_name}]")
    total_rows = cursor.fetchone()['cnt']
    
    if total_rows == 0:
        return f"-- Tabla {table_name}: 0 registros\n", 0
    
    # Exportar datos
    data_lines = []
    data_lines.append(f"-- =================================================")
    data_lines.append(f"-- Datos: {table_name} ({total_rows} registros)")
    data_lines.append(f"-- =================================================")
    data_lines.append(f"SET IDENTITY_INSERT dbo.[{table_name}] ON;")
    data_lines.append(f"GO")
    data_lines.append("")
    
    col_list = ", ".join([f"[{c}]" for c in columns])
    
    cursor.execute(f"SELECT * FROM dbo.[{table_name}]")
    rows = cursor.fetchall()
    
    for row in rows:
        values = []
        for col in columns:
            values.append(serialize_value(row[col]))
        
        values_str = ", ".join(values)
        data_lines.append(f"INSERT INTO dbo.[{table_name}] ({col_list}) VALUES ({values_str});")
    
    data_lines.append("")
    data_lines.append(f"SET IDENTITY_INSERT dbo.[{table_name}] OFF;")
    data_lines.append("GO")
    data_lines.append("")
    
    return "\n".join(data_lines), total_rows

def main():
    print(f"=" * 60)
    print(f"EDARSAHUB - BACKUP COMPLETO")
    print(f"=" * 60)
    print(f"Host: {HOST}:{PORT}")
    print(f"Database: {DATABASE}")
    print(f"Destino: {BACKUP_DIR}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print()
    
    os.makedirs(BACKUP_DIR, exist_ok=True)
    
    conn = get_connection()
    cursor = conn.cursor()
    
    # Obtener lista de tablas
    cursor.execute("""
        SELECT TABLE_NAME 
        FROM INFORMATION_SCHEMA.TABLES 
        WHERE TABLE_TYPE = 'BASE TABLE' AND TABLE_SCHEMA = 'dbo'
        ORDER BY TABLE_NAME
    """)
    tables = [row['TABLE_NAME'] for row in cursor.fetchall()]
    
    print(f"Tablas encontradas: {len(tables)}")
    print()
    
    # Archivos de salida
    ddl_file = os.path.join(BACKUP_DIR, "01_DDL_SCHEMA.sql")
    data_file = os.path.join(BACKUP_DIR, "02_DATA_INSERTS.sql")
    summary_file = os.path.join(BACKUP_DIR, "00_SUMMARY.md")
    
    ddl_content = []
    data_content = []
    summary_data = []
    
    ddl_content.append(f"-- EDARSAHUB Database Schema Export")
    ddl_content.append(f"-- Generated: {datetime.now().isoformat()}")
    ddl_content.append(f"-- Tables: {len(tables)}")
    ddl_content.append(f"")
    ddl_content.append(f"USE EDARSAHUB;")
    ddl_content.append(f"GO")
    ddl_content.append(f"")
    
    data_content.append(f"-- EDARSAHUB Data Export")
    data_content.append(f"-- Generated: {datetime.now().isoformat()}")
    data_content.append(f"")
    data_content.append(f"USE EDARSAHUB;")
    data_content.append(f"GO")
    data_content.append(f"")
    
    total_records = 0
    
    for i, table in enumerate(tables, 1):
        print(f"[{i}/{len(tables)}] Exportando: {table}...", end=" ", flush=True)
        
        try:
            # DDL
            ddl = export_table_ddl(cursor, table)
            if ddl:
                ddl_content.append(ddl)
            
            # Data
            data, row_count = export_table_data(cursor, table)
            if data:
                data_content.append(data)
            
            total_records += row_count
            print(f"OK ({row_count} registros)")
            summary_data.append((table, row_count))
            
        except Exception as e:
            print(f"ERROR: {e}")
            summary_data.append((table, f"ERROR: {e}"))
    
    # Escribir archivos
    with open(ddl_file, 'w', encoding='utf-8') as f:
        f.write("\n".join(ddl_content))
    
    with open(data_file, 'w', encoding='utf-8') as f:
        f.write("\n".join(data_content))
    
    # Summary
    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write(f"# EDARSAHUB Database Backup\n\n")
        f.write(f"**Generado:** {datetime.now().isoformat()}\n")
        f.write(f"**Host:** {HOST}:{PORT}\n")
        f.write(f"**Database:** {DATABASE}\n")
        f.write(f"**Tablas:** {len(tables)}\n")
        f.write(f"**Total Registros:** {total_records:,}\n\n")
        f.write(f"## Archivos\n\n")
        f.write(f"| Archivo | Descripcion |\n")
        f.write(f"|---------|-------------|\n")
        f.write(f"| 01_DDL_SCHEMA.sql | Estructura de tablas e indices |\n")
        f.write(f"| 02_DATA_INSERTS.sql | Datos de todas las tablas |\n\n")
        f.write(f"## Contenido por Tabla\n\n")
        f.write(f"| Tabla | Registros |\n")
        f.write(f"|-------|----------:|\n")
        for table, count in summary_data:
            if isinstance(count, int):
                f.write(f"| {table} | {count:,} |\n")
            else:
                f.write(f"| {table} | {count} |\n")
        f.write(f"| **TOTAL** | **{total_records:,}** |\n")
    
    cursor.close()
    conn.close()
    
    print()
    print(f"=" * 60)
    print(f"BACKUP COMPLETADO")
    print(f"=" * 60)
    print(f"Tablas: {len(tables)}")
    print(f"Registros totales: {total_records:,}")
    print(f"Archivos generados:")
    print(f"  - {ddl_file}")
    print(f"  - {data_file}")
    print(f"  - {summary_file}")
    print()

if __name__ == "__main__":
    main()
