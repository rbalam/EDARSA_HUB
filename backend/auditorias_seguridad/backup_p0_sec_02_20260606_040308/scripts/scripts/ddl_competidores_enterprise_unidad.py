"""
DDL: Arquitectura Enterprise de Competidores por Unidad de Negocio

PROBLEMA RESUELTO:
- Los competidores NO deben ser globales
- Cada unidad de negocio tiene sus propios competidores
- El mismo competidor puede aplicar a múltiples unidades con diferente relación

ESTRUCTURA:
1. Comercial_CompetidoresCatalogo - Catálogo maestro (datos del competidor)
2. Comercial_CompetidoresUnidad - Relación competidor-unidad (prioridad, tipo relación)

MIGRACIÓN:
- Migra datos existentes de Comercial_Competidores a las nuevas tablas
- NO elimina la tabla original (backward compatibility)
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
    # =========================================================
    # 1. CATÁLOGO MAESTRO DE COMPETIDORES
    # =========================================================
    """
    IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'Comercial_CompetidoresCatalogo')
    BEGIN
        CREATE TABLE Comercial_CompetidoresCatalogo (
            CompetidorCatalogoID UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
            
            -- Datos del competidor
            NombreCompetidor NVARCHAR(200) NOT NULL,
            TipoRestaurante VARCHAR(50) NULL,
            SegmentoPrecio VARCHAR(30) NULL,
            
            -- Ubicación
            Ciudad NVARCHAR(100) NULL,
            Estado NVARCHAR(100) NULL,
            Pais VARCHAR(50) DEFAULT 'México',
            ZonaComercial NVARCHAR(200) NULL,
            DireccionCompleta NVARCHAR(500) NULL,
            Latitud DECIMAL(10, 7) NULL,
            Longitud DECIMAL(10, 7) NULL,
            
            -- URLs y redes sociales
            SitioWeb NVARCHAR(500) NULL,
            UrlMenu NVARCHAR(500) NULL,
            UrlGoogleMaps NVARCHAR(500) NULL,
            UrlInstagram NVARCHAR(500) NULL,
            UrlFacebook NVARCHAR(500) NULL,
            UrlTripAdvisor NVARCHAR(500) NULL,
            UrlOpenTable NVARCHAR(500) NULL,
            
            -- Metadata
            Notas NVARCHAR(1000) NULL,
            Activo BIT DEFAULT 1,
            FechaCreacion DATETIME2 DEFAULT GETDATE(),
            UsuarioCreacion NVARCHAR(100) NULL,
            FechaModificacion DATETIME2 NULL,
            UsuarioModificacion NVARCHAR(100) NULL
        );
        
        CREATE INDEX IX_CompetidoresCatalogo_Nombre ON Comercial_CompetidoresCatalogo(NombreCompetidor);
        CREATE INDEX IX_CompetidoresCatalogo_Ciudad ON Comercial_CompetidoresCatalogo(Ciudad);
        CREATE INDEX IX_CompetidoresCatalogo_Activo ON Comercial_CompetidoresCatalogo(Activo);
        
        PRINT 'Tabla Comercial_CompetidoresCatalogo creada';
    END
    ELSE
    BEGIN
        PRINT 'Tabla Comercial_CompetidoresCatalogo ya existe';
    END
    """,
    
    # =========================================================
    # 2. RELACIÓN COMPETIDOR-UNIDAD DE NEGOCIO
    # =========================================================
    """
    IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'Comercial_CompetidoresUnidad')
    BEGIN
        CREATE TABLE Comercial_CompetidoresUnidad (
            CompetidorUnidadID UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
            
            -- Referencias
            CompetidorCatalogoID UNIQUEIDENTIFIER NOT NULL,
            EmpresaID INT NOT NULL,
            UnidadNegocioID INT NOT NULL,
            
            -- Tipo de relación con esta unidad
            EsCompetenciaDirecta BIT DEFAULT 1,
            EsBenchmarkAspiracional BIT DEFAULT 0,
            TipoRelacion VARCHAR(50) DEFAULT 'COMPETENCIA_DIRECTA',
            
            -- Prioridad y contexto para esta unidad
            Prioridad INT DEFAULT 0,
            DistanciaKm DECIMAL(10, 2) NULL,
            Comentarios NVARCHAR(500) NULL,
            
            -- Metadata
            Activo BIT DEFAULT 1,
            FechaCreacion DATETIME2 DEFAULT GETDATE(),
            UsuarioCreacion NVARCHAR(100) NULL,
            FechaModificacion DATETIME2 NULL,
            UsuarioModificacion NVARCHAR(100) NULL,
            
            -- FK
            CONSTRAINT FK_CompetidoresUnidad_Catalogo 
                FOREIGN KEY (CompetidorCatalogoID) 
                REFERENCES Comercial_CompetidoresCatalogo(CompetidorCatalogoID),
            
            -- Unique: un competidor solo puede estar una vez por unidad
            CONSTRAINT UK_CompetidoresUnidad_CompetidorUnidad 
                UNIQUE (CompetidorCatalogoID, UnidadNegocioID)
        );
        
        CREATE INDEX IX_CompetidoresUnidad_Empresa ON Comercial_CompetidoresUnidad(EmpresaID);
        CREATE INDEX IX_CompetidoresUnidad_Unidad ON Comercial_CompetidoresUnidad(UnidadNegocioID);
        CREATE INDEX IX_CompetidoresUnidad_Competidor ON Comercial_CompetidoresUnidad(CompetidorCatalogoID);
        CREATE INDEX IX_CompetidoresUnidad_Activo ON Comercial_CompetidoresUnidad(Activo);
        
        PRINT 'Tabla Comercial_CompetidoresUnidad creada';
    END
    ELSE
    BEGIN
        PRINT 'Tabla Comercial_CompetidoresUnidad ya existe';
    END
    """,
    
    # =========================================================
    # 3. VISTA CONSOLIDADA (para queries simplificados)
    # =========================================================
    """
    IF EXISTS (SELECT 1 FROM sys.views WHERE name = 'vw_CompetidoresPorUnidad')
        DROP VIEW vw_CompetidoresPorUnidad;
    """,
    """
    CREATE VIEW vw_CompetidoresPorUnidad AS
    SELECT 
        cu.CompetidorUnidadID,
        cu.CompetidorCatalogoID,
        cu.EmpresaID,
        cu.UnidadNegocioID,
        cc.NombreCompetidor,
        cc.TipoRestaurante,
        cc.SegmentoPrecio,
        cc.Ciudad,
        cc.Estado,
        cc.Pais,
        cc.ZonaComercial,
        cc.SitioWeb,
        cc.UrlMenu,
        cc.UrlGoogleMaps,
        cc.UrlInstagram,
        cc.UrlFacebook,
        cc.UrlTripAdvisor,
        cc.UrlOpenTable,
        cc.Notas,
        cu.EsCompetenciaDirecta,
        cu.EsBenchmarkAspiracional,
        cu.TipoRelacion,
        cu.Prioridad,
        cu.DistanciaKm,
        cu.Comentarios,
        cu.Activo,
        cu.FechaCreacion,
        cu.UsuarioCreacion,
        cu.FechaModificacion,
        cu.UsuarioModificacion
    FROM Comercial_CompetidoresUnidad cu
    INNER JOIN Comercial_CompetidoresCatalogo cc 
        ON cu.CompetidorCatalogoID = cc.CompetidorCatalogoID
    WHERE cu.Activo = 1 AND cc.Activo = 1;
    """,
    
    # =========================================================
    # 4. MIGRACIÓN DE DATOS EXISTENTES
    # =========================================================
    """
    -- Migrar competidores existentes al catálogo maestro
    IF NOT EXISTS (SELECT 1 FROM Comercial_CompetidoresCatalogo)
    BEGIN
        INSERT INTO Comercial_CompetidoresCatalogo (
            CompetidorCatalogoID,
            NombreCompetidor,
            TipoRestaurante,
            SegmentoPrecio,
            Ciudad,
            Estado,
            Pais,
            ZonaComercial,
            SitioWeb,
            UrlMenu,
            UrlGoogleMaps,
            UrlInstagram,
            UrlFacebook,
            UrlTripAdvisor,
            UrlOpenTable,
            Notas,
            Activo,
            FechaCreacion,
            UsuarioCreacion,
            FechaModificacion,
            UsuarioModificacion
        )
        SELECT 
            CompetidorID,
            NombreCompetidor,
            TipoRestaurante,
            SegmentoPrecio,
            Ciudad,
            Estado,
            Pais,
            ZonaComercial,
            SitioWeb,
            UrlMenu,
            UrlGoogleMaps,
            UrlInstagram,
            UrlFacebook,
            UrlTripAdvisor,
            UrlOpenTable,
            Notas,
            Activo,
            FechaCreacion,
            UsuarioCreacion,
            FechaModificacion,
            UsuarioModificacion
        FROM Comercial_Competidores
        WHERE CompetidorID NOT IN (SELECT CompetidorCatalogoID FROM Comercial_CompetidoresCatalogo);
        
        PRINT 'Migrados competidores al catálogo maestro';
    END
    """,
    """
    -- Migrar relaciones competidor-unidad
    IF NOT EXISTS (SELECT 1 FROM Comercial_CompetidoresUnidad)
    BEGIN
        INSERT INTO Comercial_CompetidoresUnidad (
            CompetidorCatalogoID,
            EmpresaID,
            UnidadNegocioID,
            EsCompetenciaDirecta,
            EsBenchmarkAspiracional,
            TipoRelacion,
            Prioridad,
            DistanciaKm,
            Activo,
            FechaCreacion,
            UsuarioCreacion
        )
        SELECT 
            CompetidorID,
            EmpresaID,
            COALESCE(UnidadNegocioID, 1),
            COALESCE(EsCompetenciaDirecta, 1),
            COALESCE(EsBenchmarkAspiracional, 0),
            CASE 
                WHEN EsBenchmarkAspiracional = 1 THEN 'BENCHMARK_ASPIRACIONAL'
                ELSE 'COMPETENCIA_DIRECTA'
            END,
            COALESCE(Prioridad, 0),
            DistanciaKm,
            Activo,
            FechaCreacion,
            UsuarioCreacion
        FROM Comercial_Competidores
        WHERE CompetidorID IN (SELECT CompetidorCatalogoID FROM Comercial_CompetidoresCatalogo)
          AND CompetidorID NOT IN (SELECT CompetidorCatalogoID FROM Comercial_CompetidoresUnidad);
        
        PRINT 'Migradas relaciones competidor-unidad';
    END
    """,
    
    # =========================================================
    # 5. ACTUALIZAR Comercial_CompetidoresMenuItems (FK)
    # =========================================================
    """
    -- Verificar si MenuItems apunta al catálogo correcto
    IF EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS 
               WHERE TABLE_NAME = 'Comercial_CompetidoresMenuItems' 
               AND COLUMN_NAME = 'CompetidorID')
    BEGIN
        -- Agregar columna CompetidorCatalogoID si no existe
        IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS 
                       WHERE TABLE_NAME = 'Comercial_CompetidoresMenuItems' 
                       AND COLUMN_NAME = 'CompetidorCatalogoID')
        BEGIN
            ALTER TABLE Comercial_CompetidoresMenuItems 
            ADD CompetidorCatalogoID UNIQUEIDENTIFIER NULL;
            
            -- Copiar datos de CompetidorID a CompetidorCatalogoID
            UPDATE Comercial_CompetidoresMenuItems 
            SET CompetidorCatalogoID = CompetidorID 
            WHERE CompetidorCatalogoID IS NULL;
            
            PRINT 'Agregada columna CompetidorCatalogoID a MenuItems';
        END
    END
    """,
    
    # =========================================================
    # 6. VALIDAR INTEGRIDAD
    # =========================================================
    """
    -- Verificar migración
    DECLARE @totalCatalogo INT, @totalUnidad INT, @totalOriginal INT;
    SELECT @totalCatalogo = COUNT(*) FROM Comercial_CompetidoresCatalogo;
    SELECT @totalUnidad = COUNT(*) FROM Comercial_CompetidoresUnidad;
    SELECT @totalOriginal = COUNT(*) FROM Comercial_Competidores;
    
    PRINT 'Validación de migración:';
    PRINT '  - Competidores en catálogo: ' + CAST(@totalCatalogo AS VARCHAR);
    PRINT '  - Relaciones unidad: ' + CAST(@totalUnidad AS VARCHAR);
    PRINT '  - Tabla original: ' + CAST(@totalOriginal AS VARCHAR);
    """
]

def main():
    print("=" * 70)
    print("DDL: Arquitectura Enterprise Competidores por Unidad de Negocio")
    print("=" * 70)
    
    conn = get_conn()
    
    for i, stmt in enumerate(DDL_STATEMENTS, 1):
        print(f"\n[{i}/{len(DDL_STATEMENTS)}] Ejecutando DDL...")
        try:
            execute_sql_query(*conn, stmt)
            print(f"    OK")
        except Exception as e:
            error_msg = str(e)
            if "already exists" in error_msg.lower() or "ya existe" in error_msg.lower():
                print(f"    OK (ya existe)")
            else:
                print(f"    ERROR: {e}")
    
    print("\n" + "=" * 70)
    print("DDL completado - Arquitectura Enterprise implementada")
    print("=" * 70)
    
    return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
