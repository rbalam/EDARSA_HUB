"""
PASO 1 (Ruta B) - Ejecuta el DDL de Producto_MapeoOrigen en EDARSAHUB.
Idempotente: solo crea si NO existe. Valida y reporta. NO inserta datos.
NO imprime secretos.
"""
import sys
from pathlib import Path
from dotenv import load_dotenv
sys.path.insert(0, "/app/backend")
load_dotenv(Path("/app/backend/.env"))
import logging; logging.disable(logging.CRITICAL)
from core.sql_first.db import get_sql_connection

TABLE = "Producto_MapeoOrigen"

DDL_TABLE = """
CREATE TABLE dbo.Producto_MapeoOrigen (
    MapeoOrigenID   INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
    ServerID        UNIQUEIDENTIFIER  NOT NULL,
    SystemType      VARCHAR(40)       NOT NULL,
    CodigoFuente    VARCHAR(100)      NOT NULL,
    ProductoID      INT               NOT NULL,
    OrigenInsumoID  UNIQUEIDENTIFIER  NULL,
    Activo          BIT  NOT NULL CONSTRAINT DF_PMO_Activo DEFAULT (1),
    FechaCreacion   DATETIME2 NOT NULL CONSTRAINT DF_PMO_Fecha DEFAULT (SYSUTCDATETIME()),
    CONSTRAINT FK_PMO_Producto FOREIGN KEY (ProductoID) REFERENCES dbo.Producto_Catalogo (ProductoID),
    CONSTRAINT UQ_PMO_Origen UNIQUE (ServerID, SystemType, CodigoFuente)
)
"""
DDL_INDEX = "CREATE INDEX IX_PMO_Producto ON dbo.Producto_MapeoOrigen (ProductoID)"


def main():
    conn = get_sql_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM sys.tables WHERE name = %s", (TABLE,))
    if cur.fetchone()[0] > 0:
        print(f"[SKIP] {TABLE} ya existe. No se ejecuta DDL (idempotente).")
    else:
        cur.execute(DDL_TABLE)
        cur.execute(DDL_INDEX)
        conn.commit()
        print(f"[OK] Tabla {TABLE} creada + índice IX_PMO_Producto.")

    # Validación
    cur2 = conn.cursor(as_dict=True)
    cur2.execute("""SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE FROM INFORMATION_SCHEMA.COLUMNS
                    WHERE TABLE_NAME=%s ORDER BY ORDINAL_POSITION""", (TABLE,))
    print("\n=== ESQUEMA ===")
    for r in cur2.fetchall():
        print(f"   {r['COLUMN_NAME']:<16}{r['DATA_TYPE']:<18}null={r['IS_NULLABLE']}")

    cur2.execute("""SELECT i.name idx, i.is_unique, i.is_primary_key FROM sys.indexes i
                    WHERE i.object_id = OBJECT_ID('dbo.'+%s) AND i.name IS NOT NULL""", (TABLE,))
    print("\n=== ÍNDICES ===")
    for r in cur2.fetchall():
        print(f"   {r['idx']:<24} unique={bool(r['is_unique'])} pk={bool(r['is_primary_key'])}")

    cur2.execute("""SELECT fk.name fk, OBJECT_NAME(fk.referenced_object_id) ref
                    FROM sys.foreign_keys fk WHERE fk.parent_object_id = OBJECT_ID('dbo.'+%s)""", (TABLE,))
    print("\n=== FOREIGN KEYS ===")
    for r in cur2.fetchall():
        print(f"   {r['fk']} -> {r['ref']}")

    cur.execute(f"SELECT COUNT(*) FROM [{TABLE}]")
    print(f"\n=== FILAS: {cur.fetchone()[0]} (debe ser 0) ===")
    conn.close()


if __name__ == "__main__":
    main()
