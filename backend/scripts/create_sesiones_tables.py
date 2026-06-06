"""
Script para crear tablas de sesiones en EDARSAHUB SQL Server.
Ejecutar una sola vez para resolver el error 'Invalid object name Sesiones'.
"""

import pymssql
import os

# Configuración EDARSAHUB
EDARSAHUB_CONFIG = {
    'host': os.getenv('EDARSAHUB_SQL_HOST'),
    'port': 1433,
    'database': 'EDARSAHUB',
    'username': os.getenv('EDARSAHUB_SQL_USER'),
    'password': os.getenv('EDARSAHUB_SQL_PASSWORD')
}

# SQL para crear las tablas
CREATE_SESIONES_SQL = """
-- Tabla principal de sesiones activas
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='Sesiones' AND xtype='U')
BEGIN
    CREATE TABLE Sesiones (
        SesionID VARCHAR(50) PRIMARY KEY,
        UsuarioID VARCHAR(50) NOT NULL,
        TipoUsuario VARCHAR(20) DEFAULT 'interno',
        RefreshTokenHash VARCHAR(128) NOT NULL,
        FamiliaTokenID VARCHAR(50) NOT NULL,
        FechaCreacion DATETIME DEFAULT GETUTCDATE(),
        FechaExpiracion DATETIME NOT NULL,
        UltimaActividad DATETIME DEFAULT GETUTCDATE(),
        EstaActiva BIT DEFAULT 1,
        IPCliente VARCHAR(45),
        UserAgent VARCHAR(500),
        FechaModificacion DATETIME DEFAULT GETUTCDATE(),
        INDEX IX_Sesiones_Usuario (UsuarioID),
        INDEX IX_Sesiones_Familia (FamiliaTokenID),
        INDEX IX_Sesiones_Expiracion (FechaExpiracion),
        INDEX IX_Sesiones_Activa (EstaActiva)
    );
    PRINT 'Tabla Sesiones creada exitosamente';
END
ELSE
BEGIN
    PRINT 'Tabla Sesiones ya existe';
END
"""

CREATE_SESIONES_HISTORICO_SQL = """
-- Tabla de historial de acciones de sesiones
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='SesionesHistorico' AND xtype='U')
BEGIN
    CREATE TABLE SesionesHistorico (
        HistoricoID INT IDENTITY(1,1) PRIMARY KEY,
        SesionID VARCHAR(50) NOT NULL,
        UsuarioID VARCHAR(50) NOT NULL,
        TipoUsuario VARCHAR(20),
        Accion VARCHAR(50) NOT NULL,
        FechaAccion DATETIME DEFAULT GETUTCDATE(),
        IPCliente VARCHAR(45),
        UserAgent VARCHAR(500),
        DetallesJSON NVARCHAR(MAX),
        AccionRealizadaPor VARCHAR(50),
        INDEX IX_SesionesHistorico_Sesion (SesionID),
        INDEX IX_SesionesHistorico_Usuario (UsuarioID),
        INDEX IX_SesionesHistorico_Fecha (FechaAccion)
    );
    PRINT 'Tabla SesionesHistorico creada exitosamente';
END
ELSE
BEGIN
    PRINT 'Tabla SesionesHistorico ya existe';
END
"""

def create_tables():
    """Crea las tablas de sesiones en EDARSAHUB."""
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
        
        print("\n--- Creando tabla Sesiones ---")
        cursor.execute(CREATE_SESIONES_SQL)
        conn.commit()
        
        print("\n--- Creando tabla SesionesHistorico ---")
        cursor.execute(CREATE_SESIONES_HISTORICO_SQL)
        conn.commit()
        
        # Verificar que se crearon
        print("\n--- Verificando tablas ---")
        cursor.execute("SELECT name FROM sysobjects WHERE xtype='U' AND name IN ('Sesiones', 'SesionesHistorico')")
        tables = cursor.fetchall()
        print(f"Tablas encontradas: {[t[0] for t in tables]}")
        
        cursor.close()
        conn.close()
        
        print("\n✅ Tablas creadas exitosamente")
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False

if __name__ == "__main__":
    create_tables()
