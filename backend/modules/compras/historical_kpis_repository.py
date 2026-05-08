"""
EDARSA HUB - Compras Historical KPIs Repository
================================================
Repositorio para UPSERT idempotente de KPIs históricos de Compras
en EDARSAHUB SQL Server.

Fecha: 2026-04-26
Tabla destino: Compras_KPIs_Historico

KPIs soportados:
- INVENTARIO_FISICO: Conteos de inventario por almacén/fecha
- PEDIDO: Pedidos/requisiciones por fecha
- ORDEN_COMPRA: Órdenes de compra por proveedor/fecha  
- ENTRADA_COMPRA: Entradas de compra (facturas proveedor)
"""

import logging
import os
import sys
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone

sys.path.insert(0, '/app/backend')

logger = logging.getLogger(__name__)


def get_edarsahub_server():
    """Obtiene configuración del servidor EDARSAHUB desde MongoDB."""
    from dotenv import load_dotenv
    load_dotenv('/app/backend/.env')
    from pymongo import MongoClient
    
    client = MongoClient(os.environ['MONGO_URL'])
    db = client[os.environ['DB_NAME']]
    
    srv = db.servers.find_one({'name': 'EDARSA HUB', 'active': True})
    if not srv:
        raise ValueError("Servidor EDARSA HUB no encontrado en MongoDB")
    
    # Descifrar password si está cifrado
    password = srv.get('password', '')
    if password.startswith('enc:'):
        from core.secret_manager import decrypt_secret
        password = decrypt_secret(password)
    
    return {
        "host": srv.get("host"),
        "port": srv.get("port", 1433),
        "database": srv.get("database"),
        "username": srv.get("username"),
        "password": password,
    }


def get_edarsahub_connection():
    """Obtiene conexión a EDARSAHUB SQL Server."""
    import pytds
    config = get_edarsahub_server()
    return pytds.connect(
        server=config["host"],
        port=config["port"],
        database=config["database"],
        user=config["username"],
        password=config["password"],
        timeout=30
    )


def check_table_exists() -> bool:
    """Verifica si la tabla Compras_KPIs_Historico existe."""
    try:
        conn = get_edarsahub_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) FROM sys.objects 
            WHERE object_id = OBJECT_ID(N'[dbo].[Compras_KPIs_Historico]') 
            AND type in (N'U')
        """)
        result = cursor.fetchone()[0]
        conn.close()
        return result > 0
    except Exception as e:
        logger.error(f"Error verificando tabla: {e}")
        return False


def create_table_if_not_exists() -> str:
    """Crea la tabla Compras_KPIs_Historico si no existe."""
    try:
        conn = get_edarsahub_connection()
        cursor = conn.cursor()
        
        create_sql = """
        IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[Compras_KPIs_Historico]') AND type in (N'U'))
        BEGIN
            CREATE TABLE [dbo].[Compras_KPIs_Historico] (
                [id] INT IDENTITY(1,1) PRIMARY KEY,
                [run_id] NVARCHAR(50) NOT NULL,
                [server_id] NVARCHAR(50) NOT NULL,
                [sucursal_id] NVARCHAR(50) NOT NULL,
                [system_type_normalized] NVARCHAR(50) NOT NULL,
                [fecha] DATE NOT NULL,
                [kpi_tipo] NVARCHAR(50) NOT NULL,
                
                -- Inventarios Físicos
                [inv_conteos_count] INT DEFAULT 0,
                [inv_productos_count] INT DEFAULT 0,
                [inv_almacenes] NVARCHAR(500) DEFAULT '',
                
                -- Pedidos
                [ped_pedidos_count] INT DEFAULT 0,
                [ped_total_monto] DECIMAL(18,4) DEFAULT 0,
                [ped_productos_count] INT DEFAULT 0,
                
                -- Órdenes de Compra
                [oc_ordenes_count] INT DEFAULT 0,
                [oc_total_monto] DECIMAL(18,4) DEFAULT 0,
                [oc_proveedores_count] INT DEFAULT 0,
                
                -- Entradas de Compra
                [ec_entradas_count] INT DEFAULT 0,
                [ec_total_monto] DECIMAL(18,4) DEFAULT 0,
                [ec_productos_count] INT DEFAULT 0,
                
                -- Metadata
                [empresa_id] NVARCHAR(50) DEFAULT '',
                [empresa_nombre] NVARCHAR(200) DEFAULT '',
                [created_at] DATETIME DEFAULT GETDATE(),
                [updated_at] DATETIME DEFAULT GETDATE()
            );
            
            -- Índice único para idempotencia
            CREATE UNIQUE INDEX IX_Compras_KPIs_Unique 
            ON [dbo].[Compras_KPIs_Historico] (server_id, sucursal_id, fecha, kpi_tipo);
            
            -- Índices para consultas frecuentes
            CREATE INDEX IX_Compras_KPIs_Fecha ON [dbo].[Compras_KPIs_Historico] (fecha);
            CREATE INDEX IX_Compras_KPIs_Tipo ON [dbo].[Compras_KPIs_Historico] (kpi_tipo);
        END
        """
        
        cursor.execute(create_sql)
        conn.commit()
        conn.close()
        
        return "Tabla Compras_KPIs_Historico creada/verificada exitosamente"
    except Exception as e:
        logger.error(f"Error creando tabla: {e}")
        return f"Error: {e}"


def upsert_compras_kpi_historico(
    run_id: str,
    server_id: str,
    sucursal_id: str,
    system_type: str,
    fecha: str,
    kpi_tipo: str,
    kpi_data: Dict[str, Any],
    empresa_id: str = "",
    empresa_nombre: str = ""
) -> Dict[str, Any]:
    """
    Realiza UPSERT de un registro de KPI de Compras en SQL Server.
    Usa INSERT con manejo de duplicados mediante verificación previa.
    """
    
    try:
        conn = get_edarsahub_connection()
        cursor = conn.cursor()
        
        # Verificar si existe
        check_sql = """
        SELECT id FROM Compras_KPIs_Historico 
        WHERE server_id = %s AND sucursal_id = %s AND fecha = %s AND kpi_tipo = %s
        """
        cursor.execute(check_sql, (server_id, sucursal_id, fecha, kpi_tipo))
        existing = cursor.fetchone()
        
        if existing:
            # UPDATE
            update_sql = """
            UPDATE Compras_KPIs_Historico SET
                run_id = %s,
                system_type_normalized = %s,
                inv_conteos_count = %s,
                inv_productos_count = %s,
                inv_almacenes = %s,
                ped_pedidos_count = %s,
                ped_total_monto = %s,
                ped_productos_count = %s,
                oc_ordenes_count = %s,
                oc_total_monto = %s,
                oc_proveedores_count = %s,
                ec_entradas_count = %s,
                ec_total_monto = %s,
                ec_productos_count = %s,
                empresa_id = %s,
                empresa_nombre = %s,
                updated_at = GETDATE()
            WHERE server_id = %s AND sucursal_id = %s AND fecha = %s AND kpi_tipo = %s
            """
            cursor.execute(update_sql, (
                run_id,
                system_type,
                kpi_data.get('inv_conteos_count', 0),
                kpi_data.get('inv_productos_count', 0),
                kpi_data.get('inv_almacenes', ''),
                kpi_data.get('ped_pedidos_count', 0),
                kpi_data.get('ped_total_monto', 0),
                kpi_data.get('ped_productos_count', 0),
                kpi_data.get('oc_ordenes_count', 0),
                kpi_data.get('oc_total_monto', 0),
                kpi_data.get('oc_proveedores_count', 0),
                kpi_data.get('ec_entradas_count', 0),
                kpi_data.get('ec_total_monto', 0),
                kpi_data.get('ec_productos_count', 0),
                empresa_id,
                empresa_nombre,
                server_id, sucursal_id, fecha, kpi_tipo
            ))
            conn.commit()
            conn.close()
            return {"status": "updated", "id": existing[0]}
        else:
            # INSERT
            insert_sql = """
            INSERT INTO Compras_KPIs_Historico (
                run_id, server_id, sucursal_id, system_type_normalized, fecha, kpi_tipo,
                inv_conteos_count, inv_productos_count, inv_almacenes,
                ped_pedidos_count, ped_total_monto, ped_productos_count,
                oc_ordenes_count, oc_total_monto, oc_proveedores_count,
                ec_entradas_count, ec_total_monto, ec_productos_count,
                empresa_id, empresa_nombre
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(insert_sql, (
                run_id, server_id, sucursal_id, system_type, fecha, kpi_tipo,
                kpi_data.get('inv_conteos_count', 0),
                kpi_data.get('inv_productos_count', 0),
                kpi_data.get('inv_almacenes', ''),
                kpi_data.get('ped_pedidos_count', 0),
                kpi_data.get('ped_total_monto', 0),
                kpi_data.get('ped_productos_count', 0),
                kpi_data.get('oc_ordenes_count', 0),
                kpi_data.get('oc_total_monto', 0),
                kpi_data.get('oc_proveedores_count', 0),
                kpi_data.get('ec_entradas_count', 0),
                kpi_data.get('ec_total_monto', 0),
                kpi_data.get('ec_productos_count', 0),
                empresa_id, empresa_nombre
            ))
            conn.commit()
            conn.close()
            return {"status": "inserted", "id": None}
            
    except Exception as e:
        logger.error(f"Error en upsert Compras KPI: {e}")
        return {"status": "error", "message": str(e)}
