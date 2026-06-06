#!/usr/bin/env python3
"""
Script para crear la tabla Unidades_Negocio en EDARSAHUB SQL Server.
Esta tabla centraliza el mapeo de servidores a unidades de negocio,
eliminando la dependencia de MongoDB para esta información.

Arquitectura: EDARSAHUB SQL como fuente primaria de verdad.
"""

import sys
import os
sys.path.insert(0, '/app/backend')

from core.db import execute_sql_query

# Configuración EDARSAHUB
EDARSAHUB_CONFIG = {
    'host': os.getenv('EDARSAHUB_SQL_HOST'),
    'port': 1433,
    'database': 'EDARSAHUB',
    'username': os.getenv('EDARSAHUB_SQL_USER'),
    'password': os.getenv('EDARSAHUB_SQL_PASSWORD')
}

def execute_hub_query(query: str):
    """Ejecuta una query en EDARSAHUB SQL Server."""
    return execute_sql_query(
        EDARSAHUB_CONFIG['host'],
        EDARSAHUB_CONFIG['port'],
        EDARSAHUB_CONFIG['database'],
        EDARSAHUB_CONFIG['username'],
        EDARSAHUB_CONFIG['password'],
        query
    )

def check_table_exists():
    """Verifica si la tabla Unidades_Negocio ya existe."""
    query = """
    SELECT COUNT(*) as count 
    FROM INFORMATION_SCHEMA.TABLES 
    WHERE TABLE_NAME = 'Unidades_Negocio'
    """
    result = execute_hub_query(query)
    return result and result[0].get('count', 0) > 0

def create_table():
    """Crea la tabla Unidades_Negocio en EDARSAHUB."""
    
    # DDL para crear la tabla
    create_table_sql = """
    -- Crear tabla Unidades_Negocio si no existe
    IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'Unidades_Negocio')
    BEGIN
        CREATE TABLE Unidades_Negocio (
            id UNIQUEIDENTIFIER DEFAULT NEWID() PRIMARY KEY,
            nombre NVARCHAR(100) NOT NULL,
            codigo NVARCHAR(50) NOT NULL,
            server_id NVARCHAR(100) NOT NULL,
            sucursal_origen_id NVARCHAR(50) NULL,
            system_type NVARCHAR(50) NOT NULL DEFAULT 'SoftRestaurant',
            activo BIT DEFAULT 1,
            orden INT DEFAULT 0,
            -- Metadatos
            created_at DATETIME DEFAULT GETDATE(),
            updated_at DATETIME DEFAULT GETDATE(),
            -- Índices
            CONSTRAINT UQ_Unidades_Server_Sucursal UNIQUE (server_id, sucursal_origen_id)
        );
        
        -- Índice para búsquedas rápidas
        CREATE INDEX IX_Unidades_ServerID ON Unidades_Negocio(server_id);
        CREATE INDEX IX_Unidades_Codigo ON Unidades_Negocio(codigo);
        
        PRINT 'Tabla Unidades_Negocio creada exitosamente';
    END
    ELSE
    BEGIN
        PRINT 'La tabla Unidades_Negocio ya existe';
    END
    """
    
    try:
        execute_hub_query(create_table_sql)
        print("✅ Tabla Unidades_Negocio verificada/creada en EDARSAHUB")
        return True
    except Exception as e:
        print(f"❌ Error creando tabla: {e}")
        return False

def insert_unidades():
    """Inserta los datos de unidades de negocio."""
    
    # Datos de las 5 unidades de negocio actuales
    # REGLA: SoftRestaurant -> sucursal_origen_id = NULL (1 servidor = 1 unidad)
    #        MPRO -> sucursal_origen_id = código (1 servidor = múltiples sucursales)
    unidades = [
        # SoftRestaurant (sucursal_origen_id = NULL)
        {
            'nombre': '130° MERIDA',
            'codigo': '130MID',
            'server_id': 'a5547321-1139-4d2b-9d53-182ca737b6b6',
            'sucursal_origen_id': None,  # SoftRestaurant NO usa código de sucursal
            'system_type': 'SoftRestaurant',
            'orden': 1
        },
        {
            'nombre': 'CIENFUEGOS',
            'codigo': 'CIENFUEGOS',
            'server_id': '6d053c22-523e-48c0-b72b-96081e2d781b',
            'sucursal_origen_id': None,
            'system_type': 'SoftRestaurant',
            'orden': 2
        },
        {
            'nombre': 'LA ESTELAR',
            'codigo': 'ESTELAR',
            'server_id': 'a5ff0e25-f029-43db-b634-d4ac814c904f',
            'sucursal_origen_id': None,
            'system_type': 'SoftRestaurant',
            'orden': 3
        },
        # MPRO (usa sucursal_origen_id para identificar sucursales dentro del servidor)
        {
            'nombre': '130° QUERETARO',
            'codigo': '130QRO',
            'server_id': '1b230a06-ffaf-4c70-bd27-b1be3579dea6',
            'sucursal_origen_id': '0021',
            'system_type': 'MPRO',
            'orden': 4
        },
        {
            'nombre': 'ORIGEN',
            'codigo': 'ORIGEN',
            'server_id': '1b230a06-ffaf-4c70-bd27-b1be3579dea6',
            'sucursal_origen_id': '0023',
            'system_type': 'MPRO',
            'orden': 5
        },
    ]
    
    inserted = 0
    for u in unidades:
        suc_id = f"'{u['sucursal_origen_id']}'" if u['sucursal_origen_id'] else 'NULL'
        
        insert_sql = f"""
        IF NOT EXISTS (
            SELECT 1 FROM Unidades_Negocio 
            WHERE server_id = '{u['server_id']}' 
            AND (sucursal_origen_id = {suc_id} OR (sucursal_origen_id IS NULL AND {suc_id} IS NULL))
        )
        BEGIN
            INSERT INTO Unidades_Negocio (nombre, codigo, server_id, sucursal_origen_id, system_type, orden, activo)
            VALUES ('{u['nombre']}', '{u['codigo']}', '{u['server_id']}', {suc_id}, '{u['system_type']}', {u['orden']}, 1);
            PRINT 'Insertado: {u['nombre']}';
        END
        ELSE
        BEGIN
            -- Actualizar si ya existe
            UPDATE Unidades_Negocio 
            SET nombre = '{u['nombre']}',
                codigo = '{u['codigo']}',
                system_type = '{u['system_type']}',
                orden = {u['orden']},
                updated_at = GETDATE()
            WHERE server_id = '{u['server_id']}' 
            AND (sucursal_origen_id = {suc_id} OR (sucursal_origen_id IS NULL AND {suc_id} IS NULL));
            PRINT 'Actualizado: {u['nombre']}';
        END
        """
        
        try:
            execute_hub_query(insert_sql)
            inserted += 1
            print(f"  ✅ {u['nombre']} ({u['system_type']})")
        except Exception as e:
            print(f"  ❌ Error insertando {u['nombre']}: {e}")
    
    return inserted

def verify_data():
    """Verifica los datos insertados."""
    query = """
    SELECT 
        nombre,
        codigo,
        server_id,
        sucursal_origen_id,
        system_type,
        orden,
        activo
    FROM Unidades_Negocio
    ORDER BY orden
    """
    
    try:
        results = execute_hub_query(query)
        print("\n📋 Unidades de Negocio en EDARSAHUB:")
        print("-" * 80)
        for r in results:
            suc_id = r.get('sucursal_origen_id') or 'NULL'
            print(f"  {r['orden']}. {r['nombre']:20} | {r['system_type']:15} | sucursal: {suc_id}")
        print("-" * 80)
        print(f"Total: {len(results)} unidades")
        return results
    except Exception as e:
        print(f"❌ Error verificando datos: {e}")
        return []

def main():
    print("=" * 60)
    print("CREACIÓN DE TABLA Unidades_Negocio EN EDARSAHUB SQL")
    print("=" * 60)
    print(f"Host: {EDARSAHUB_CONFIG['host']}")
    print(f"Database: {EDARSAHUB_CONFIG['database']}")
    print()
    
    # 1. Crear tabla
    print("1️⃣ Creando/verificando tabla...")
    if not create_table():
        print("❌ No se pudo crear la tabla. Abortando.")
        return False
    
    # 2. Insertar datos
    print("\n2️⃣ Insertando unidades de negocio...")
    inserted = insert_unidades()
    print(f"\n   Procesadas: {inserted} unidades")
    
    # 3. Verificar
    print("\n3️⃣ Verificando datos...")
    data = verify_data()
    
    if len(data) >= 5:
        print("\n✅ ÉXITO: Tabla Unidades_Negocio configurada correctamente en EDARSAHUB")
        return True
    else:
        print("\n⚠️ ADVERTENCIA: Menos de 5 unidades encontradas")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
