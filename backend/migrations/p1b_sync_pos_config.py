#!/usr/bin/env python3
"""
P1B - Migración SQL canónica: tablas de control de Sync POS para Inteligencia Comercial.

Crea (idempotente) en EDARSAHUB:
- dbo.Sistema_SyncPOS_Config       (control de ejecución: Habilitado / PermitirPOSAutomatico / frecuencia)
- dbo.Sistema_SyncPOS_EstadoUnidad (estado de última sync por unidad)
- dbo.Sistema_SyncPOS_Faltantes    (registro de huecos a backfill - DIFERIDO)
- dbo.Sistema_SyncPOS_Bitacora     (auditoría de ejecuciones)

CONFIG INICIAL = MODO SEGURO (autorizado por el usuario, Regla de Oro):
  Habilitado = 0
  PermitirPOSAutomatico = 0
  BackfillAutomaticoHabilitado = 0
El job horario queda PREPARADO pero NO conecta al POS hasta que el usuario lo encienda por SQL.

NO toca datos transaccionales. NO imprime secretos. Idempotente.
"""
import os
import sys
from pathlib import Path

BACKEND_DIR = Path("/app/backend")
ENV_PATH = BACKEND_DIR / ".env"


def load_env():
    if ENV_PATH.exists():
        for raw in ENV_PATH.read_text(encoding="utf-8", errors="ignore").splitlines():
            line = raw.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


load_env()
sys.path.insert(0, str(BACKEND_DIR))

from core.sql_first.db import get_sql_connection

DDL = r"""
SET NOCOUNT ON;

IF OBJECT_ID('dbo.Sistema_SyncPOS_Config', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.Sistema_SyncPOS_Config (
        SyncPOSConfigID BIGINT IDENTITY(1,1) NOT NULL PRIMARY KEY,
        Codigo NVARCHAR(80) NOT NULL UNIQUE,
        Nombre NVARCHAR(200) NOT NULL,
        Habilitado BIT NOT NULL DEFAULT 0,
        FrecuenciaMinutos INT NOT NULL DEFAULT 60,
        DiasAtrasAutomatico INT NOT NULL DEFAULT 2,
        DiasRevisionFaltantes INT NOT NULL DEFAULT 14,
        BackfillAutomaticoHabilitado BIT NOT NULL DEFAULT 0,
        MaxDiasBackfillPorCorrida INT NOT NULL DEFAULT 3,
        MaxUnidadesPorCorrida INT NOT NULL DEFAULT 10,
        TimeoutConexionSegundos INT NOT NULL DEFAULT 15,
        TimeoutQuerySegundos INT NOT NULL DEFAULT 180,
        PermitirPOSAutomatico BIT NOT NULL DEFAULT 0,
        FechaUltimaEjecucion DATETIME2(0) NULL,
        FechaSiguienteEjecucion DATETIME2(0) NULL,
        EstadoUltimaEjecucion NVARCHAR(50) NULL,
        MensajeUltimaEjecucion NVARCHAR(MAX) NULL,
        Activo BIT NOT NULL DEFAULT 1,
        FechaCreacion DATETIME2(0) NOT NULL DEFAULT SYSUTCDATETIME(),
        FechaActualizacion DATETIME2(0) NULL
    );
END;

IF NOT EXISTS (SELECT 1 FROM dbo.Sistema_SyncPOS_Config WHERE Codigo='INTELIGENCIA_COMERCIAL_POS')
BEGIN
    INSERT INTO dbo.Sistema_SyncPOS_Config (
        Codigo, Nombre, Habilitado, FrecuenciaMinutos, DiasAtrasAutomatico,
        DiasRevisionFaltantes, BackfillAutomaticoHabilitado, MaxDiasBackfillPorCorrida,
        MaxUnidadesPorCorrida, PermitirPOSAutomatico, Activo
    )
    VALUES (
        'INTELIGENCIA_COMERCIAL_POS',
        'Sincronizacion POS a EDARSAHUB SQL para Inteligencia Comercial (MODO SEGURO)',
        0,   -- Habilitado
        60,  -- FrecuenciaMinutos
        2,   -- DiasAtrasAutomatico
        14,  -- DiasRevisionFaltantes
        0,   -- BackfillAutomaticoHabilitado
        3,   -- MaxDiasBackfillPorCorrida
        10,  -- MaxUnidadesPorCorrida
        0,   -- PermitirPOSAutomatico
        1    -- Activo
    );
END;

IF OBJECT_ID('dbo.Sistema_SyncPOS_EstadoUnidad', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.Sistema_SyncPOS_EstadoUnidad (
        EstadoUnidadID BIGINT IDENTITY(1,1) NOT NULL PRIMARY KEY,
        UnidadNegocioID NVARCHAR(100) NOT NULL,
        UnidadNombre NVARCHAR(300) NULL,
        ServerID NVARCHAR(100) NULL,
        SystemType NVARCHAR(100) NULL,
        FechaUltimaSyncExitosa DATE NULL,
        FechaHoraUltimaSync DATETIME2(0) NULL,
        UltimoEstado NVARCHAR(50) NULL,
        UltimoMensaje NVARCHAR(MAX) NULL,
        TicketsUltimaSync INT NULL,
        LineasUltimaSync INT NULL,
        VentaUltimaSync DECIMAL(18,4) NULL,
        Activo BIT NOT NULL DEFAULT 1,
        FechaCreacion DATETIME2(0) NOT NULL DEFAULT SYSUTCDATETIME(),
        FechaActualizacion DATETIME2(0) NULL
    );
    CREATE UNIQUE INDEX UX_Sistema_SyncPOS_EstadoUnidad
        ON dbo.Sistema_SyncPOS_EstadoUnidad(UnidadNegocioID);
END;

IF OBJECT_ID('dbo.Sistema_SyncPOS_Faltantes', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.Sistema_SyncPOS_Faltantes (
        FaltanteID BIGINT IDENTITY(1,1) NOT NULL PRIMARY KEY,
        UnidadNegocioID NVARCHAR(100) NOT NULL,
        FechaOperacion DATE NOT NULL,
        Motivo NVARCHAR(200) NOT NULL,
        Estado NVARCHAR(50) NOT NULL DEFAULT 'PENDIENTE',
        Intentos INT NOT NULL DEFAULT 0,
        FechaDeteccion DATETIME2(0) NOT NULL DEFAULT SYSUTCDATETIME(),
        FechaUltimoIntento DATETIME2(0) NULL,
        FechaResolucion DATETIME2(0) NULL,
        Mensaje NVARCHAR(MAX) NULL,
        TicketsEsperados INT NULL,
        TicketsSincronizados INT NULL,
        LineasSincronizadas INT NULL,
        VentaSincronizada DECIMAL(18,4) NULL,
        Activo BIT NOT NULL DEFAULT 1
    );
    CREATE UNIQUE INDEX UX_Sistema_SyncPOS_Faltantes_UnidadFecha
        ON dbo.Sistema_SyncPOS_Faltantes(UnidadNegocioID, FechaOperacion)
        WHERE Estado IN ('PENDIENTE', 'PROCESANDO', 'ERROR');
END;

IF OBJECT_ID('dbo.Sistema_SyncPOS_Bitacora', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.Sistema_SyncPOS_Bitacora (
        BitacoraID BIGINT IDENTITY(1,1) NOT NULL PRIMARY KEY,
        BatchID UNIQUEIDENTIFIER NOT NULL DEFAULT NEWID(),
        TipoEjecucion NVARCHAR(50) NOT NULL,
        UnidadNegocioID NVARCHAR(100) NULL,
        FechaInicio DATE NULL,
        FechaFin DATE NULL,
        Estado NVARCHAR(50) NOT NULL,
        Mensaje NVARCHAR(MAX) NULL,
        Tickets INT NULL,
        Lineas INT NULL,
        Venta DECIMAL(18,4) NULL,
        DuracionSegundos INT NULL,
        FechaInicioEjecucion DATETIME2(0) NOT NULL DEFAULT SYSUTCDATETIME(),
        FechaFinEjecucion DATETIME2(0) NULL
    );
    CREATE INDEX IX_Sistema_SyncPOS_Bitacora_Fecha
        ON dbo.Sistema_SyncPOS_Bitacora(FechaInicioEjecucion DESC, TipoEjecucion, Estado);
END;
"""

VERIFY = """
SELECT
    OBJECT_ID('dbo.Sistema_SyncPOS_Config','U')       AS cfg,
    OBJECT_ID('dbo.Sistema_SyncPOS_EstadoUnidad','U') AS est,
    OBJECT_ID('dbo.Sistema_SyncPOS_Faltantes','U')    AS fal,
    OBJECT_ID('dbo.Sistema_SyncPOS_Bitacora','U')     AS bit
"""


def main():
    conn = get_sql_connection()
    try:
        cur = conn.cursor()
        cur.execute(DDL)
        conn.commit()

        cur2 = conn.cursor()
        cur2.execute(VERIFY)
        row = cur2.fetchone()
        oids = list(row)
        if not all(oids):
            raise SystemExit(f"ERROR: alguna tabla no se creó. OBJECT_IDs={oids}")

        cur3 = conn.cursor()
        cur3.execute(
            "SELECT Codigo, Habilitado, PermitirPOSAutomatico, BackfillAutomaticoHabilitado, "
            "FrecuenciaMinutos FROM dbo.Sistema_SyncPOS_Config WHERE Codigo='INTELIGENCIA_COMERCIAL_POS'"
        )
        cfg = cur3.fetchone()
        print("OK: tablas Sistema_SyncPOS_* listas (idempotente).")
        print(f"   Config seed (MODO SEGURO): Codigo={cfg[0]} Habilitado={cfg[1]} "
              f"PermitirPOSAutomatico={cfg[2]} BackfillAutomaticoHabilitado={cfg[3]} "
              f"FrecuenciaMinutos={cfg[4]}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
