"""
Script para crear tablas de tracking de jobs del scheduler en EDARSAHUB SQL Server.
Reemplaza las colecciones MongoDB para los jobs de detección.
"""

import pymssql

# Configuración EDARSAHUB
EDARSAHUB_CONFIG = {
    'host': '<REDACTED_EDARSAHUB_SQL_HOST>',
    'port': 1433,
    'database': 'EDARSAHUB',
    'username': '<REDACTED_EDARSAHUB_SQL_USER>',
    'password': '<REDACTED_EDARSAHUB_SQL_PASSWORD>'
}

# SQL para crear tablas de tracking de jobs
CREATE_INVENTARIOS_PROCESADOS_SQL = """
-- Tabla para tracking de inventarios procesados automáticamente
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='Scheduler_InventariosProcesados' AND xtype='U')
BEGIN
    CREATE TABLE Scheduler_InventariosProcesados (
        ID INT IDENTITY(1,1) PRIMARY KEY,
        SistemaOrigen VARCHAR(50) NOT NULL,
        ServerID VARCHAR(50) NOT NULL,
        SucursalID VARCHAR(50) NOT NULL,
        AlmacenID VARCHAR(50) NOT NULL,
        FolioInventario VARCHAR(100) NOT NULL,
        Estado VARCHAR(20) DEFAULT 'EN_PROCESO',
        Intentos INT DEFAULT 1,
        FechaDeteccion DATETIME DEFAULT GETUTCDATE(),
        FechaProcesamiento DATETIME,
        FechaUltimoIntento DATETIME DEFAULT GETUTCDATE(),
        ErrorMensaje NVARCHAR(MAX),
        WorkflowID VARCHAR(50),
        DetallesJSON NVARCHAR(MAX),
        CONSTRAINT UQ_Inventario_Clave UNIQUE (SistemaOrigen, ServerID, SucursalID, AlmacenID, FolioInventario),
        INDEX IX_Inventarios_Estado (Estado),
        INDEX IX_Inventarios_Server (ServerID),
        INDEX IX_Inventarios_Fecha (FechaDeteccion)
    );
    PRINT 'Tabla Scheduler_InventariosProcesados creada';
END
ELSE
BEGIN
    PRINT 'Tabla Scheduler_InventariosProcesados ya existe';
END
"""

CREATE_PEDIDOS_PROCESADOS_SQL = """
-- Tabla para tracking de pedidos detectados automáticamente
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='Scheduler_PedidosProcesados' AND xtype='U')
BEGIN
    CREATE TABLE Scheduler_PedidosProcesados (
        ID INT IDENTITY(1,1) PRIMARY KEY,
        SistemaOrigen VARCHAR(50) NOT NULL,
        ServerID VARCHAR(50) NOT NULL,
        EmpresaID VARCHAR(50) NOT NULL,
        SucursalID VARCHAR(50),
        FolioPedido VARCHAR(100) NOT NULL,
        Estado VARCHAR(20) DEFAULT 'DETECTADO',
        FechaDeteccion DATETIME DEFAULT GETUTCDATE(),
        FechaProcesamiento DATETIME,
        TipoDocumento VARCHAR(50),
        DetallesJSON NVARCHAR(MAX),
        CONSTRAINT UQ_Pedido_Clave UNIQUE (SistemaOrigen, ServerID, EmpresaID, FolioPedido),
        INDEX IX_Pedidos_Estado (Estado),
        INDEX IX_Pedidos_Server (ServerID),
        INDEX IX_Pedidos_Fecha (FechaDeteccion)
    );
    PRINT 'Tabla Scheduler_PedidosProcesados creada';
END
ELSE
BEGIN
    PRINT 'Tabla Scheduler_PedidosProcesados ya existe';
END
"""

CREATE_BITACORA_JOBS_SQL = """
-- Tabla para bitácora de ejecuciones de jobs
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='Scheduler_BitacoraJobs' AND xtype='U')
BEGIN
    CREATE TABLE Scheduler_BitacoraJobs (
        ID INT IDENTITY(1,1) PRIMARY KEY,
        JobName VARCHAR(100) NOT NULL,
        RunID VARCHAR(50) NOT NULL,
        Accion VARCHAR(50) NOT NULL,
        FechaAccion DATETIME DEFAULT GETUTCDATE(),
        ServerID VARCHAR(50),
        DetallesJSON NVARCHAR(MAX),
        Exito BIT DEFAULT 1,
        MensajeError NVARCHAR(MAX),
        INDEX IX_Bitacora_Job (JobName),
        INDEX IX_Bitacora_Run (RunID),
        INDEX IX_Bitacora_Fecha (FechaAccion)
    );
    PRINT 'Tabla Scheduler_BitacoraJobs creada';
END
ELSE
BEGIN
    PRINT 'Tabla Scheduler_BitacoraJobs ya existe';
END
"""

def create_tables():
    """Crea las tablas de tracking de jobs en EDARSAHUB."""
    print(f"Conectando a {EDARSAHUB_CONFIG['host']}:{EDARSAHUB_CONFIG['port']}/{EDARSAHUB_CONFIG['database']}...")
    
    try:
        conn = pymssql.connect(
            server=EDARSAHUB_CONFIG['host'],
            port=EDARSAHUB_CONFIG['port'],
            database=EDARSAHUB_CONFIG['database'],
            user=EDARSAHUB_CONFIG['username'],
            password=EDARSAHUB_CONFIG['password'],
            timeout=30,
            login_timeout=15
        )
        cursor = conn.cursor()
        
        print("\n--- Creando tabla Scheduler_InventariosProcesados ---")
        cursor.execute(CREATE_INVENTARIOS_PROCESADOS_SQL)
        conn.commit()
        
        print("\n--- Creando tabla Scheduler_PedidosProcesados ---")
        cursor.execute(CREATE_PEDIDOS_PROCESADOS_SQL)
        conn.commit()
        
        print("\n--- Creando tabla Scheduler_BitacoraJobs ---")
        cursor.execute(CREATE_BITACORA_JOBS_SQL)
        conn.commit()
        
        # Verificar que se crearon
        print("\n--- Verificando tablas ---")
        cursor.execute("""
            SELECT name FROM sysobjects 
            WHERE xtype='U' AND name LIKE 'Scheduler_%'
        """)
        tables = cursor.fetchall()
        print(f"Tablas encontradas: {[t[0] for t in tables]}")
        
        cursor.close()
        conn.close()
        
        print("\n✅ Tablas de scheduler creadas exitosamente")
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False

if __name__ == "__main__":
    create_tables()
