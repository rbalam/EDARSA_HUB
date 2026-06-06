"""
EDARSA HUB - Script de creación de tablas para Cava de Socios
==============================================================
Módulo: 07. Cava de Socios / Socios Cava
Ubicación ERP: Comercial / Experiencia Cliente / Cava de Socios
Tipo: Módulo principal (Inventario en custodia de terceros)

Ejecutar una sola vez para crear las tablas en EDARSAHUB SQL Server.

Uso:
    python create_cava_socios_tables.py
"""

import pymssql
import os
from datetime import datetime

DB_CONFIG = {
    'host': os.environ.get('EDARSAHUB_HOST', '<REDACTED_EDARSAHUB_SQL_HOST>'),
    'port': int(os.environ.get('EDARSAHUB_PORT', '1433')),
    'database': os.environ.get('EDARSAHUB_DATABASE', 'EDARSAHUB'),
    'username': os.environ.get('EDARSAHUB_USERNAME', '<REDACTED_EDARSAHUB_SQL_USER>'),
    'password': os.environ.get('EDARSAHUB_PASSWORD', '<REDACTED_EDARSAHUB_SQL_PASSWORD>')
}


def get_connection():
    return pymssql.connect(
        server=DB_CONFIG['host'],
        port=DB_CONFIG['port'],
        database=DB_CONFIG['database'],
        user=DB_CONFIG['username'],
        password=DB_CONFIG['password'],
        autocommit=False
    )


def create_tables():
    """Crea las tablas para el módulo Cava de Socios."""
    
    conn = get_connection()
    cursor = conn.cursor()
    
    tables = []
    
    # 1. Tabla de Socios de Cava
    tables.append(("CavaSocios_Socios", """
        CREATE TABLE CavaSocios_Socios (
            SocioID UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
            EmpresaID UNIQUEIDENTIFIER NOT NULL,
            -- Datos del socio
            NumeroSocio VARCHAR(50) NOT NULL,
            NombreCompleto NVARCHAR(200) NOT NULL,
            Email VARCHAR(150),
            Telefono VARCHAR(50),
            -- Relación con cliente CRM
            ClienteCRMID UNIQUEIDENTIFIER NULL,
            -- Tipo de membresía
            TipoMembresia VARCHAR(50) DEFAULT 'ESTANDAR',  -- ESTANDAR, PREMIUM, VIP, CORPORATIVO
            FechaAltaMembresia DATE,
            FechaVencimientoMembresia DATE,
            -- Límites y configuración
            MaximoBotellas INT DEFAULT 12,
            -- Estado
            Estatus VARCHAR(30) DEFAULT 'ACTIVO',  -- ACTIVO, SUSPENDIDO, CANCELADO, VENCIDO
            Activo BIT DEFAULT 1,
            -- Auditoría
            FechaCreacion DATETIME2 DEFAULT GETUTCDATE(),
            UsuarioCreacionID UNIQUEIDENTIFIER,
            FechaModificacion DATETIME2,
            UsuarioModificacionID UNIQUEIDENTIFIER,
            Observaciones NVARCHAR(500),
            -- Índices
            CONSTRAINT UQ_CavaSocios_NumeroSocio UNIQUE (EmpresaID, NumeroSocio)
        )
    """))
    
    # 2. Tabla de Botellas en Cava
    tables.append(("CavaSocios_Botellas", """
        CREATE TABLE CavaSocios_Botellas (
            BotellaID UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
            EmpresaID UNIQUEIDENTIFIER NOT NULL,
            SocioID UNIQUEIDENTIFIER NOT NULL,
            -- Datos del producto
            ProductoCodigo VARCHAR(50),
            ProductoNombre NVARCHAR(200) NOT NULL,
            Marca NVARCHAR(100),
            TipoBebida VARCHAR(50),  -- VINO_TINTO, VINO_BLANCO, WHISKY, TEQUILA, MEZCAL, OTRO
            Añada VARCHAR(10),
            Capacidad DECIMAL(10,2),  -- ml
            -- Ubicación física
            UbicacionCava NVARCHAR(50),  -- Ej: "RACK-A-12"
            -- Valores
            ValorDeclarado DECIMAL(18,2) DEFAULT 0,
            -- Estado
            EstatusBotella VARCHAR(30) DEFAULT 'EN_CAVA',  -- EN_CAVA, CONSUMIDA, RETIRADA, DAÑADA
            -- Fechas
            FechaIngreso DATETIME2 DEFAULT GETUTCDATE(),
            FechaConsumo DATETIME2,
            FechaRetiro DATETIME2,
            -- Trazabilidad
            NivelActual DECIMAL(5,2) DEFAULT 100,  -- Porcentaje restante
            -- Evidencia
            FotoIngresoURL NVARCHAR(500),
            -- Auditoría
            FechaCreacion DATETIME2 DEFAULT GETUTCDATE(),
            UsuarioCreacionID UNIQUEIDENTIFIER,
            FechaModificacion DATETIME2,
            UsuarioModificacionID UNIQUEIDENTIFIER,
            Observaciones NVARCHAR(500),
            -- FK
            CONSTRAINT FK_CavaSocios_Botellas_Socio FOREIGN KEY (SocioID) 
                REFERENCES CavaSocios_Socios(SocioID)
        )
    """))
    
    # 3. Tabla de Movimientos de Cava
    tables.append(("CavaSocios_Movimientos", """
        CREATE TABLE CavaSocios_Movimientos (
            MovimientoID UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
            EmpresaID UNIQUEIDENTIFIER NOT NULL,
            BotellaID UNIQUEIDENTIFIER NOT NULL,
            SocioID UNIQUEIDENTIFIER NOT NULL,
            -- Tipo de movimiento
            TipoMovimiento VARCHAR(30) NOT NULL,  -- ENTRADA, CONSUMO_PARCIAL, CONSUMO_TOTAL, RETIRO, TRANSFERENCIA, AJUSTE
            -- Cantidades
            NivelAnterior DECIMAL(5,2),  -- Porcentaje antes
            NivelNuevo DECIMAL(5,2),  -- Porcentaje después
            CantidadConsumida DECIMAL(10,2),  -- ml consumidos
            -- Contexto
            MotivoMovimiento NVARCHAR(200),
            -- Relaciones con otros módulos
            ReservacionID UNIQUEIDENTIFIER NULL,
            EventoID UNIQUEIDENTIFIER NULL,
            CuentaPOSID UNIQUEIDENTIFIER NULL,
            -- Cargo generado
            GeneroCargo BIT DEFAULT 0,
            MontoCargo DECIMAL(18,2) DEFAULT 0,
            CargoConceptoID UNIQUEIDENTIFIER NULL,
            -- Responsable
            MeseroID UNIQUEIDENTIFIER NULL,
            AutorizadoPor UNIQUEIDENTIFIER NULL,
            -- Ubicación
            SucursalID UNIQUEIDENTIFIER,
            -- Evidencia
            FotoEvidenciaURL NVARCHAR(500),
            -- Fechas
            FechaMovimiento DATETIME2 DEFAULT GETUTCDATE(),
            -- Auditoría
            FechaCreacion DATETIME2 DEFAULT GETUTCDATE(),
            UsuarioCreacionID UNIQUEIDENTIFIER,
            Observaciones NVARCHAR(500),
            -- FKs
            CONSTRAINT FK_CavaSocios_Movimientos_Botella FOREIGN KEY (BotellaID) 
                REFERENCES CavaSocios_Botellas(BotellaID),
            CONSTRAINT FK_CavaSocios_Movimientos_Socio FOREIGN KEY (SocioID) 
                REFERENCES CavaSocios_Socios(SocioID)
        )
    """))
    
    # 4. Tabla de Cargos por Servicio
    tables.append(("CavaSocios_Cargos", """
        CREATE TABLE CavaSocios_Cargos (
            CargoID UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
            EmpresaID UNIQUEIDENTIFIER NOT NULL,
            SocioID UNIQUEIDENTIFIER NOT NULL,
            -- Tipo de cargo
            TipoCargo VARCHAR(50) NOT NULL,  -- SERVICIO_DESCORCHE, ALMACENAJE_MENSUAL, CONSUMO, EVENTO, OTRO
            ConceptoCargo NVARCHAR(200) NOT NULL,
            -- Monto
            Monto DECIMAL(18,2) NOT NULL,
            Impuesto DECIMAL(18,2) DEFAULT 0,
            Total DECIMAL(18,2) NOT NULL,
            -- Estado
            EstatusCargo VARCHAR(30) DEFAULT 'PENDIENTE',  -- PENDIENTE, FACTURADO, PAGADO, CANCELADO
            -- Relaciones
            BotellaID UNIQUEIDENTIFIER NULL,
            MovimientoID UNIQUEIDENTIFIER NULL,
            ReservacionID UNIQUEIDENTIFIER NULL,
            FacturaID UNIQUEIDENTIFIER NULL,
            -- Fechas
            FechaCargo DATETIME2 DEFAULT GETUTCDATE(),
            FechaPago DATETIME2,
            -- Auditoría
            FechaCreacion DATETIME2 DEFAULT GETUTCDATE(),
            UsuarioCreacionID UNIQUEIDENTIFIER,
            FechaModificacion DATETIME2,
            UsuarioModificacionID UNIQUEIDENTIFIER,
            Observaciones NVARCHAR(500),
            -- FKs
            CONSTRAINT FK_CavaSocios_Cargos_Socio FOREIGN KEY (SocioID) 
                REFERENCES CavaSocios_Socios(SocioID),
            CONSTRAINT FK_CavaSocios_Cargos_Botella FOREIGN KEY (BotellaID) 
                REFERENCES CavaSocios_Botellas(BotellaID),
            CONSTRAINT FK_CavaSocios_Cargos_Movimiento FOREIGN KEY (MovimientoID) 
                REFERENCES CavaSocios_Movimientos(MovimientoID)
        )
    """))
    
    # 5. Tabla de Configuración de Cava por Empresa
    tables.append(("CavaSocios_Configuracion", """
        CREATE TABLE CavaSocios_Configuracion (
            ConfigID UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
            EmpresaID UNIQUEIDENTIFIER NOT NULL UNIQUE,
            -- Capacidad
            CapacidadTotalBotellas INT DEFAULT 500,
            -- Tarifas por defecto
            TarifaDescorche DECIMAL(18,2) DEFAULT 350,
            TarifaAlmacenajeMensual DECIMAL(18,2) DEFAULT 150,
            -- Políticas
            DiasGraciaVencimiento INT DEFAULT 30,
            MaximoBotellasEstandar INT DEFAULT 12,
            MaximoBotellasVIP INT DEFAULT 24,
            -- Notificaciones
            DiasAnticipacionVencimiento INT DEFAULT 15,
            -- Auditoría
            FechaCreacion DATETIME2 DEFAULT GETUTCDATE(),
            UsuarioCreacionID UNIQUEIDENTIFIER,
            FechaModificacion DATETIME2,
            UsuarioModificacionID UNIQUEIDENTIFIER
        )
    """))
    
    # 6. Índices adicionales
    indexes = [
        "CREATE INDEX IX_CavaSocios_Socios_Empresa ON CavaSocios_Socios(EmpresaID)",
        "CREATE INDEX IX_CavaSocios_Socios_ClienteCRM ON CavaSocios_Socios(ClienteCRMID)",
        "CREATE INDEX IX_CavaSocios_Botellas_Socio ON CavaSocios_Botellas(SocioID)",
        "CREATE INDEX IX_CavaSocios_Botellas_Estatus ON CavaSocios_Botellas(EstatusBotella)",
        "CREATE INDEX IX_CavaSocios_Movimientos_Botella ON CavaSocios_Movimientos(BotellaID)",
        "CREATE INDEX IX_CavaSocios_Movimientos_Fecha ON CavaSocios_Movimientos(FechaMovimiento)",
        "CREATE INDEX IX_CavaSocios_Cargos_Socio ON CavaSocios_Cargos(SocioID)",
        "CREATE INDEX IX_CavaSocios_Cargos_Estatus ON CavaSocios_Cargos(EstatusCargo)"
    ]
    
    print("=" * 60)
    print("EDARSA HUB - Creación de Tablas Cava de Socios")
    print("=" * 60)
    
    try:
        # Crear tablas
        for table_name, ddl in tables:
            # Verificar si existe
            cursor.execute("""
                SELECT 1 FROM INFORMATION_SCHEMA.TABLES 
                WHERE TABLE_NAME = %s
            """, (table_name,))
            
            if cursor.fetchone():
                print(f"[EXISTE] {table_name}")
            else:
                cursor.execute(ddl)
                print(f"[CREADA] {table_name}")
        
        # Crear índices
        print("\nCreando índices...")
        for idx_sql in indexes:
            try:
                cursor.execute(idx_sql)
                print(f"  [OK] {idx_sql.split('IX_')[1].split(' ')[0] if 'IX_' in idx_sql else 'Index'}")
            except Exception as e:
                if "already exists" in str(e).lower() or "ya existe" in str(e).lower():
                    print(f"  [EXISTE] Index")
                else:
                    print(f"  [WARN] {e}")
        
        conn.commit()
        
        print("\n" + "=" * 60)
        print("Tablas de Cava de Socios creadas exitosamente")
        print("=" * 60)
        
        print("\nTablas creadas:")
        print("  - CavaSocios_Socios: Catálogo de socios")
        print("  - CavaSocios_Botellas: Inventario en custodia")
        print("  - CavaSocios_Movimientos: Entradas, consumos, retiros")
        print("  - CavaSocios_Cargos: Cargos por servicios")
        print("  - CavaSocios_Configuracion: Configuración por empresa")
        
    except Exception as e:
        conn.rollback()
        print(f"\n[ERROR] {e}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    create_tables()
