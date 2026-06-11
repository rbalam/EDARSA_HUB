"""
Migración: Enriquecimiento de Inteligencia Comercial
====================================================
Habilita poblar, por TICKET:
  (a) Tipo de servicio  -> columnas nuevas en dbo.Sync_Sales
  (b) Formas de pago     -> dbo.Finanzas_CortesCaja_DetallePagos (tabla canónica
      existente, hoy VACÍA y sin uso) con columnas de enlace a nivel ticket/unidad.

Cambios (idempotentes, NO destructivos):
  - Sync_Sales: + TipoServicioID NVARCHAR(20) NULL, + TipoServicio NVARCHAR(120) NULL
  - Finanzas_CortesCaja_DetallePagos:
      * CorteCajaID -> NULLABLE (best-effort; los pagos por ticket no siempre
        tienen corte sincronizado, p.ej. MPRO)
      * + UnidadNegocio NVARCHAR(100) NULL
      * + NumeroTicket  NVARCHAR(64)  NULL
      * + FechaHora     DATETIME      NULL
      * + Propina       DECIMAL(18,4) NULL
      * Índices para el drill-down ISCAM: (UnidadNegocio, NumeroTicket) y (UnidadNegocio, FechaHora)

NO USA MONGODB - 100% SQL Server (EDARSAHUB).
"""
import os
import sys
import pymssql

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'))
except Exception:
    pass


def _conn():
    return pymssql.connect(
        server=os.getenv('EDARSAHUB_SQL_HOST'),
        port=int(os.getenv('EDARSAHUB_SQL_PORT', '1433')),
        database=os.getenv('EDARSAHUB_SQL_DATABASE'),
        user=os.getenv('EDARSAHUB_SQL_USER'),
        password=os.getenv('EDARSAHUB_SQL_PASSWORD'),
        timeout=120, login_timeout=30,
    )


DDL = [
    # --- Sync_Sales: tipo de servicio por ticket ---
    "IF COL_LENGTH('dbo.Sync_Sales','TipoServicioID') IS NULL "
    "ALTER TABLE dbo.Sync_Sales ADD TipoServicioID NVARCHAR(20) NULL;",
    "IF COL_LENGTH('dbo.Sync_Sales','TipoServicio') IS NULL "
    "ALTER TABLE dbo.Sync_Sales ADD TipoServicio NVARCHAR(120) NULL;",

    # --- DetallePagos: columnas de enlace a nivel ticket/unidad ---
    "IF COL_LENGTH('dbo.Finanzas_CortesCaja_DetallePagos','UnidadNegocio') IS NULL "
    "ALTER TABLE dbo.Finanzas_CortesCaja_DetallePagos ADD UnidadNegocio NVARCHAR(100) NULL;",
    "IF COL_LENGTH('dbo.Finanzas_CortesCaja_DetallePagos','NumeroTicket') IS NULL "
    "ALTER TABLE dbo.Finanzas_CortesCaja_DetallePagos ADD NumeroTicket NVARCHAR(64) NULL;",
    "IF COL_LENGTH('dbo.Finanzas_CortesCaja_DetallePagos','FechaHora') IS NULL "
    "ALTER TABLE dbo.Finanzas_CortesCaja_DetallePagos ADD FechaHora DATETIME NULL;",
    "IF COL_LENGTH('dbo.Finanzas_CortesCaja_DetallePagos','Propina') IS NULL "
    "ALTER TABLE dbo.Finanzas_CortesCaja_DetallePagos ADD Propina DECIMAL(18,4) NULL;",
]

# CorteCajaID -> NULLABLE (best-effort). Se hace por separado para detectar estado.
ALTER_CORTECAJAID_NULLABLE = (
    "IF EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS "
    "  WHERE TABLE_NAME='Finanzas_CortesCaja_DetallePagos' "
    "    AND COLUMN_NAME='CorteCajaID' AND IS_NULLABLE='NO') "
    "ALTER TABLE dbo.Finanzas_CortesCaja_DetallePagos ALTER COLUMN CorteCajaID BIGINT NULL;"
)

INDEXES = [
    "IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name='IX_DetallePagos_Unidad_Ticket' "
    "  AND object_id=OBJECT_ID('dbo.Finanzas_CortesCaja_DetallePagos')) "
    "CREATE INDEX IX_DetallePagos_Unidad_Ticket ON dbo.Finanzas_CortesCaja_DetallePagos(UnidadNegocio, NumeroTicket);",
    "IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name='IX_DetallePagos_Unidad_Fecha' "
    "  AND object_id=OBJECT_ID('dbo.Finanzas_CortesCaja_DetallePagos')) "
    "CREATE INDEX IX_DetallePagos_Unidad_Fecha ON dbo.Finanzas_CortesCaja_DetallePagos(UnidadNegocio, FechaHora);",
    "IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name='IX_SyncSales_Unidad_TipoServicio' "
    "  AND object_id=OBJECT_ID('dbo.Sync_Sales')) "
    "CREATE INDEX IX_SyncSales_Unidad_TipoServicio ON dbo.Sync_Sales(UnidadNegocio, TipoServicioID);",
]


def run():
    conn = _conn()
    cur = conn.cursor()
    try:
        for sql in DDL:
            cur.execute(sql)
            conn.commit()
        # CorteCajaID nullable
        try:
            cur.execute(ALTER_CORTECAJAID_NULLABLE)
            conn.commit()
            print("[OK] CorteCajaID -> NULLABLE (o ya lo era)")
        except Exception as e:
            print(f"[WARN] No se pudo alterar CorteCajaID (posible FK/índice): {e}")
        for sql in INDEXES:
            try:
                cur.execute(sql)
                conn.commit()
            except Exception as e:
                print(f"[WARN] índice: {e}")
        print("[OK] Migración enrich_tiposervicio_detallepagos aplicada.")
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    run()
