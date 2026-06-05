"""
EDARSA HUB - Compras Module SQL Repository
==========================================
Repositorio SQL para parámetros de compras en EDARSAHUB.

FASE: COMPRAS-MONGO-001-F1 (Mayo 2026)
- Migración de compras_params de MongoDB a EDARSAHUB SQL
- Tabla destino: Compras_Parametros_Sucursal

ARQUITECTURA:
- Lee/Escribe exclusivamente en EDARSAHUB SQL
- CERO dependencias de MongoDB
- Reemplaza funciones get_compras_params y save_compras_params de MongoDB

Autor: E1 Agent
"""

import os
import logging
from typing import Dict, Optional, List
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# ============================================================================
# CONEXIÓN EDARSAHUB SQL
# ============================================================================

def _get_edarsahub_connection():
    """
    Obtiene conexión a EDARSAHUB SQL Server.
    Usa credenciales desde variables de entorno.
    """
    import pymssql
    
    host = os.environ.get('EDARSAHUB_HOST', '54.39.104.176')
    port = int(os.environ.get('EDARSAHUB_PORT', 1433))
    database = os.environ.get('EDARSAHUB_DATABASE', 'EDARSAHUB')
    username = os.environ.get('EDARSAHUB_USERNAME', 'HRLectura')
    password = os.environ.get('EDARSAHUB_PASSWORD', '')
    
    return pymssql.connect(
        server=host,
        port=port,
        database=database,
        user=username,
        password=password,
        timeout=30,
        login_timeout=15
    )


# ============================================================================
# DDL - CREACIÓN DE TABLA (IDEMPOTENTE)
# ============================================================================

DDL_COMPRAS_PARAMETROS_SUCURSAL = """
-- Tabla: Compras_Parametros_Sucursal
-- Almacena parámetros de configuración de compras por servidor/sucursal
-- Reemplaza colección MongoDB: compras_params

IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[Compras_Parametros_Sucursal]') AND type in (N'U'))
BEGIN
    CREATE TABLE [dbo].[Compras_Parametros_Sucursal] (
        [ParametroID] INT IDENTITY(1,1) PRIMARY KEY,
        
        -- Identificadores de ubicación
        [ServerID] VARCHAR(100) NOT NULL,
        [SucursalID] VARCHAR(50) NOT NULL,
        
        -- Parámetros de cálculo de pedidos
        [DiasInventario] INT NOT NULL DEFAULT 10,
        [ExcluirDomingos] BIT NOT NULL DEFAULT 1,
        [DiasInhabiles] NVARCHAR(MAX) NULL,  -- JSON array de fechas YYYY-MM-DD
        [DiasTransitoProveedor] INT NOT NULL DEFAULT 2,
        
        -- Metadata
        [Activo] BIT NOT NULL DEFAULT 1,
        [CreadoPor] VARCHAR(100) NULL,
        [ModificadoPor] VARCHAR(100) NULL,
        [FechaCreacion] DATETIME NOT NULL DEFAULT GETDATE(),
        [FechaModificacion] DATETIME NOT NULL DEFAULT GETDATE(),
        
        -- Constraint único para evitar duplicados
        CONSTRAINT [UQ_Compras_Parametros_Server_Sucursal] UNIQUE ([ServerID], [SucursalID])
    );
    
    -- Índices
    CREATE INDEX [IX_Compras_Parametros_ServerID] ON [dbo].[Compras_Parametros_Sucursal] ([ServerID]);
    CREATE INDEX [IX_Compras_Parametros_SucursalID] ON [dbo].[Compras_Parametros_Sucursal] ([SucursalID]);
    CREATE INDEX [IX_Compras_Parametros_Activo] ON [dbo].[Compras_Parametros_Sucursal] ([Activo]) WHERE [Activo] = 1;
    
    PRINT 'Tabla Compras_Parametros_Sucursal creada exitosamente';
END
ELSE
BEGIN
    PRINT 'Tabla Compras_Parametros_Sucursal ya existe';
END
"""


def ensure_table_exists() -> str:
    """
    Asegura que la tabla Compras_Parametros_Sucursal exista en EDARSAHUB.
    DDL idempotente - no falla si ya existe.
    
    Returns:
        Mensaje de estado
    """
    try:
        conn = _get_edarsahub_connection()
        cursor = conn.cursor()
        cursor.execute(DDL_COMPRAS_PARAMETROS_SUCURSAL)
        conn.commit()
        cursor.close()
        conn.close()
        logger.info("[COMPRAS_SQL] Tabla Compras_Parametros_Sucursal verificada/creada")
        return "Tabla Compras_Parametros_Sucursal creada/verificada exitosamente"
    except Exception as e:
        logger.error(f"[COMPRAS_SQL] Error creando tabla: {e}")
        raise


# ============================================================================
# FUNCIONES CRUD - PARÁMETROS DE COMPRAS
# ============================================================================

def get_compras_params_sql(server_id: str, sucursal: str) -> Optional[Dict]:
    """
    Obtiene los parámetros de compras desde EDARSAHUB SQL.
    
    REEMPLAZA: get_compras_params() de MongoDB
    
    Args:
        server_id: ID del servidor
        sucursal: ID de la sucursal
        
    Returns:
        Dict con parámetros o None si no existe configuración
    """
    try:
        conn = _get_edarsahub_connection()
        cursor = conn.cursor(as_dict=True)
        
        query = """
            SELECT 
                ParametroID,
                ServerID as server_id,
                SucursalID as sucursal,
                DiasInventario as dias_inventario,
                ExcluirDomingos as excluir_domingos,
                DiasInhabiles as dias_inhabiles,
                DiasTransitoProveedor as dias_transito_proveedor,
                Activo,
                FechaCreacion,
                FechaModificacion
            FROM Compras_Parametros_Sucursal
            WHERE ServerID = %s AND SucursalID = %s AND Activo = 1
        """
        
        cursor.execute(query, (server_id, sucursal))
        row = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        if row:
            # Parsear dias_inhabiles de JSON string a lista
            dias_inhabiles = []
            if row.get('dias_inhabiles'):
                import json
                try:
                    dias_inhabiles = json.loads(row['dias_inhabiles'])
                except:
                    dias_inhabiles = []
            
            result = {
                'server_id': row['server_id'],
                'sucursal': row['sucursal'],
                'dias_inventario': row['dias_inventario'],
                'excluir_domingos': bool(row['excluir_domingos']),
                'dias_inhabiles': dias_inhabiles,
                'dias_transito_proveedor': row['dias_transito_proveedor'],
                '_source': 'EDARSAHUB_SQL',
                '_table': 'Compras_Parametros_Sucursal'
            }
            
            logger.debug(f"[COMPRAS_SQL] Parámetros encontrados para {server_id}/{sucursal}")
            return result
        
        logger.debug(f"[COMPRAS_SQL] No hay parámetros configurados para {server_id}/{sucursal}")
        return None
        
    except Exception as e:
        logger.error(f"[COMPRAS_SQL] Error obteniendo parámetros: {e}")
        # Retornar None en caso de error de conexión
        # El servicio manejará los defaults
        return None


def save_compras_params_sql(server_id: str, sucursal: str, params: Dict, usuario: str = None) -> bool:
    """
    Guarda los parámetros de compras en EDARSAHUB SQL.
    Usa UPSERT (INSERT o UPDATE si existe).
    
    REEMPLAZA: save_compras_params() de MongoDB
    
    Args:
        server_id: ID del servidor
        sucursal: ID de la sucursal
        params: Dict con parámetros a guardar
        usuario: Usuario que realiza la modificación (opcional)
        
    Returns:
        True si se guardó correctamente, False si hubo error
    """
    try:
        import json
        
        conn = _get_edarsahub_connection()
        cursor = conn.cursor()
        
        # Extraer parámetros con defaults
        dias_inventario = params.get('dias_inventario', 10)
        excluir_domingos = 1 if params.get('excluir_domingos', True) else 0
        dias_inhabiles = params.get('dias_inhabiles', [])
        dias_transito_proveedor = params.get('dias_transito_proveedor', 2)
        
        # Convertir dias_inhabiles a JSON string
        dias_inhabiles_json = json.dumps(dias_inhabiles) if dias_inhabiles else '[]'
        
        # UPSERT usando MERGE
        upsert_query = """
            MERGE Compras_Parametros_Sucursal AS target
            USING (SELECT %s AS ServerID, %s AS SucursalID) AS source
            ON target.ServerID = source.ServerID AND target.SucursalID = source.SucursalID
            WHEN MATCHED THEN
                UPDATE SET 
                    DiasInventario = %s,
                    ExcluirDomingos = %s,
                    DiasInhabiles = %s,
                    DiasTransitoProveedor = %s,
                    ModificadoPor = %s,
                    FechaModificacion = GETDATE(),
                    Activo = 1
            WHEN NOT MATCHED THEN
                INSERT (ServerID, SucursalID, DiasInventario, ExcluirDomingos, 
                        DiasInhabiles, DiasTransitoProveedor, CreadoPor, ModificadoPor, Activo)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 1);
        """
        
        cursor.execute(upsert_query, (
            # Para USING
            server_id, sucursal,
            # Para UPDATE
            dias_inventario, excluir_domingos, dias_inhabiles_json, dias_transito_proveedor, usuario,
            # Para INSERT
            server_id, sucursal, dias_inventario, excluir_domingos, 
            dias_inhabiles_json, dias_transito_proveedor, usuario, usuario
        ))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info(f"[COMPRAS_SQL] Parámetros guardados para {server_id}/{sucursal}")
        return True
        
    except Exception as e:
        logger.error(f"[COMPRAS_SQL] Error guardando parámetros: {e}")
        return False


def get_all_compras_params_sql() -> List[Dict]:
    """
    Obtiene todos los parámetros de compras configurados.
    Útil para administración y debugging.
    
    Returns:
        Lista de configuraciones
    """
    try:
        conn = _get_edarsahub_connection()
        cursor = conn.cursor(as_dict=True)
        
        query = """
            SELECT 
                ParametroID,
                ServerID as server_id,
                SucursalID as sucursal,
                DiasInventario as dias_inventario,
                ExcluirDomingos as excluir_domingos,
                DiasInhabiles as dias_inhabiles,
                DiasTransitoProveedor as dias_transito_proveedor,
                Activo,
                FechaCreacion,
                FechaModificacion
            FROM Compras_Parametros_Sucursal
            WHERE Activo = 1
            ORDER BY ServerID, SucursalID
        """
        
        cursor.execute(query)
        rows = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        result = []
        for row in rows:
            import json
            dias_inhabiles = []
            if row.get('dias_inhabiles'):
                try:
                    dias_inhabiles = json.loads(row['dias_inhabiles'])
                except:
                    pass
            
            result.append({
                'server_id': row['server_id'],
                'sucursal': row['sucursal'],
                'dias_inventario': row['dias_inventario'],
                'excluir_domingos': bool(row['excluir_domingos']),
                'dias_inhabiles': dias_inhabiles,
                'dias_transito_proveedor': row['dias_transito_proveedor'],
                'activo': bool(row['Activo']),
                'fecha_creacion': str(row['FechaCreacion']) if row.get('FechaCreacion') else None,
                'fecha_modificacion': str(row['FechaModificacion']) if row.get('FechaModificacion') else None
            })
        
        return result
        
    except Exception as e:
        logger.error(f"[COMPRAS_SQL] Error listando parámetros: {e}")
        return []


def delete_compras_params_sql(server_id: str, sucursal: str) -> bool:
    """
    Elimina (soft delete) parámetros de compras.
    
    Args:
        server_id: ID del servidor
        sucursal: ID de la sucursal
        
    Returns:
        True si se eliminó correctamente
    """
    try:
        conn = _get_edarsahub_connection()
        cursor = conn.cursor()
        
        query = """
            UPDATE Compras_Parametros_Sucursal
            SET Activo = 0, FechaModificacion = GETDATE()
            WHERE ServerID = %s AND SucursalID = %s
        """
        
        cursor.execute(query, (server_id, sucursal))
        conn.commit()
        
        rows_affected = cursor.rowcount
        cursor.close()
        conn.close()
        
        logger.info(f"[COMPRAS_SQL] Parámetros eliminados para {server_id}/{sucursal}")
        return rows_affected > 0
        
    except Exception as e:
        logger.error(f"[COMPRAS_SQL] Error eliminando parámetros: {e}")
        return False


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    'ensure_table_exists',
    'get_compras_params_sql',
    'save_compras_params_sql',
    'get_all_compras_params_sql',
    'delete_compras_params_sql',
]
