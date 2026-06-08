"""
Migración: completar esquema de refresh-token rotation en dbo.Sesiones.
======================================================================
AUTH-REFRESH (2026-06-09)

El módulo core/refresh_tokens.py (rotación + detección de replay) fue escrito
contra columnas que NUNCA se crearon en la tabla real dbo.Sesiones:
    FechaRevocacion, MotivoRevocacion, ReemplazadaPorSesionID, RevocadoPorUsuarioID
y un histórico dbo.SesionesHistorico. Esto causaba 500 en POST /api/auth/refresh
("Invalid column name 'MotivoRevocacion'") tras arreglar el bug de datetime.

Esta migración agrega las columnas faltantes y crea el histórico. Idempotente.
NO toca datos existentes.
"""
from dotenv import load_dotenv

load_dotenv()

from core.db import execute_sql_query
from core.server_registry import EDARSAHUB_CONFIG as C

DDL = """
IF COL_LENGTH('dbo.Sesiones','FechaRevocacion') IS NULL
    ALTER TABLE dbo.Sesiones ADD FechaRevocacion DATETIME NULL;
IF COL_LENGTH('dbo.Sesiones','MotivoRevocacion') IS NULL
    ALTER TABLE dbo.Sesiones ADD MotivoRevocacion VARCHAR(50) NULL;
IF COL_LENGTH('dbo.Sesiones','ReemplazadaPorSesionID') IS NULL
    ALTER TABLE dbo.Sesiones ADD ReemplazadaPorSesionID VARCHAR(50) NULL;
IF COL_LENGTH('dbo.Sesiones','RevocadoPorUsuarioID') IS NULL
    ALTER TABLE dbo.Sesiones ADD RevocadoPorUsuarioID VARCHAR(100) NULL;

IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'SesionesHistorico')
    CREATE TABLE dbo.SesionesHistorico (
        HistoricoID BIGINT IDENTITY(1,1) PRIMARY KEY,
        SesionID VARCHAR(50) NULL,
        UsuarioID VARCHAR(100) NULL,
        TipoUsuario VARCHAR(20) NULL,
        Accion VARCHAR(50) NULL,
        FechaAccion DATETIME NULL,
        IPCliente VARCHAR(45) NULL,
        UserAgent VARCHAR(500) NULL,
        DetallesJSON NVARCHAR(MAX) NULL,
        AccionRealizadaPor VARCHAR(100) NULL
    );
"""


def main():
    execute_sql_query(C['host'], C['port'], C['database'], C['username'], C['password'], DDL)
    cols = execute_sql_query(
        C['host'], C['port'], C['database'], C['username'], C['password'],
        "SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME='Sesiones' "
        "AND COLUMN_NAME IN ('FechaRevocacion','MotivoRevocacion','ReemplazadaPorSesionID','RevocadoPorUsuarioID')"
    )
    hist = execute_sql_query(
        C['host'], C['port'], C['database'], C['username'], C['password'],
        "SELECT COUNT(*) cnt FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME='SesionesHistorico'"
    )
    print("Sesiones columnas nuevas:", sorted([c['COLUMN_NAME'] for c in (cols or [])]))
    print("SesionesHistorico existe:", hist)


if __name__ == "__main__":
    main()
