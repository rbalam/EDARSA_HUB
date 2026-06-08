"""
Migración: tabla canónica NO-LIVE de dimensiones de filtro de catálogo.
=======================================================================
CATALOGO-CANONICO-C1 (2026-06-09)

Crea dbo.Sync_Catalogo_Filtros: fuente única NO-LIVE para los dropdowns
Categoría / Familia / Subfamilia del módulo Análisis (y reutilizable por
cualquier pantalla). Reemplaza la lectura EN VIVO de los POS que hacía
/servers/{id}/report-filters (violaba la regla NO-LIVE y disparaba el
cooldown de EDARSAHUB en el host compartido de MPRO).

- MPRO: el endpoint deriva los filtros directamente de Sync_Productos
  (ya contiene Categoria/Familia/SubFamilia), por lo que NO se duplica aquí.
- SoftRestaurant: el Análisis filtra por la jerarquía de INSUMOS
  (clasificacionventa / gruposiclasificacion / gruposi) que NO vive en
  Sync_Productos (ventas). Esa jerarquía se sincroniza a esta tabla.

Idempotente.
"""
import os
from dotenv import load_dotenv

load_dotenv()

from core.db import execute_sql_query
from core.server_registry import EDARSAHUB_CONFIG as C

DDL = """
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'Sync_Catalogo_Filtros')
BEGIN
    CREATE TABLE dbo.Sync_Catalogo_Filtros (
        FiltroID UNIQUEIDENTIFIER NOT NULL DEFAULT NEWID() PRIMARY KEY,
        ServerID UNIQUEIDENTIFIER NOT NULL,
        SystemType NVARCHAR(50) NULL,
        Nivel NVARCHAR(20) NOT NULL,        -- CATEGORIA | FAMILIA | SUBFAMILIA
        Codigo NVARCHAR(50) NOT NULL,
        Nombre NVARCHAR(255) NULL,
        ParentCodigo NVARCHAR(50) NULL,
        Activo BIT NOT NULL DEFAULT 1,
        SyncRunID NVARCHAR(80) NULL,
        SyncedAtMexico DATETIME2 NULL,
        FechaModificacion DATETIME2 NULL,
        CONSTRAINT UQ_Sync_Catalogo_Filtros UNIQUE (ServerID, Nivel, Codigo)
    );
END
"""


def main():
    execute_sql_query(C['host'], C['port'], C['database'], C['username'], C['password'], DDL)
    chk = execute_sql_query(
        C['host'], C['port'], C['database'], C['username'], C['password'],
        "SELECT COUNT(*) cnt FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME='Sync_Catalogo_Filtros'"
    )
    print("Sync_Catalogo_Filtros existe:", chk)


if __name__ == "__main__":
    main()
