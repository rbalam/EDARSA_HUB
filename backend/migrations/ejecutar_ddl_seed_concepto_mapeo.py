"""
Sub-fase B - Ejecuta DDL + SEED de Inventario_ConceptoMapeoOrigen (DB-driven).
Migra FIELMENTE el dict TIPO_MOVIMIENTO_SR_TO_EDARSAHUB a DB (sin inventar).
Idempotente. Valida y reporta.
"""
import sys
from pathlib import Path
from dotenv import load_dotenv
sys.path.insert(0, "/app/backend")
load_dotenv(Path("/app/backend/.env"))
import logging; logging.disable(logging.CRITICAL)
from core.sql_first.db import get_sql_connection
from modules.compras.sync_service import TIPO_MOVIMIENTO_SR_TO_EDARSAHUB

TABLE = "Inventario_ConceptoMapeoOrigen"
DDL = """
CREATE TABLE dbo.Inventario_ConceptoMapeoOrigen (
    ConceptoMapeoID   INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
    SystemType        VARCHAR(40)  NOT NULL,
    ConceptoOrigen    VARCHAR(40)  NOT NULL,
    TipoMovimientoID  TINYINT      NOT NULL,
    Descripcion       VARCHAR(120) NULL,
    Activo            BIT NOT NULL CONSTRAINT DF_ICMO_Activo DEFAULT (1),
    FechaCreacion     DATETIME2 NOT NULL CONSTRAINT DF_ICMO_Fecha DEFAULT (SYSUTCDATETIME()),
    CONSTRAINT FK_ICMO_Tipo FOREIGN KEY (TipoMovimientoID) REFERENCES dbo.Inventario_TipoMovimiento (TipoMovimientoID),
    CONSTRAINT UQ_ICMO_Concepto UNIQUE (SystemType, ConceptoOrigen)
)
"""


def main():
    conn = get_sql_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM sys.tables WHERE name=%s", (TABLE,))
    if cur.fetchone()[0] == 0:
        cur.execute(DDL); conn.commit()
        print(f"[OK] Tabla {TABLE} creada.")
    else:
        print(f"[SKIP] {TABLE} ya existe.")

    # SEED idempotente (NOT EXISTS por UQ)
    inserted = 0
    for concepto, tipo_id in TIPO_MOVIMIENTO_SR_TO_EDARSAHUB.items():
        cur.execute(
            f"""IF NOT EXISTS (SELECT 1 FROM {TABLE} WHERE SystemType=%s AND ConceptoOrigen=%s)
                INSERT INTO {TABLE} (SystemType, ConceptoOrigen, TipoMovimientoID, Descripcion)
                VALUES (%s,%s,%s,%s)""",
            ("SOFTRESTAURANT_PRO", concepto,
             "SOFTRESTAURANT_PRO", concepto, tipo_id, f"Migrado de dict (concepto {concepto})"),
        )
    conn.commit()

    # Validación
    cur.execute(f"SELECT COUNT(*) FROM {TABLE}")
    total = cur.fetchone()[0]
    cur.execute(f"SELECT COUNT(*) FROM {TABLE} m WHERE NOT EXISTS (SELECT 1 FROM Inventario_TipoMovimiento t WHERE t.TipoMovimientoID=m.TipoMovimientoID)")
    huerfanos = cur.fetchone()[0]
    print(f"[POST] filas={total} (esperado >= {len(TIPO_MOVIMIENTO_SR_TO_EDARSAHUB)}) | FK huérfanos={huerfanos} (debe 0)")

    # Resolver resuelve 'EPC'
    from core.inventarios.resolver_canonico import resolver_tipo_movimiento_desde_concepto
    r = resolver_tipo_movimiento_desde_concepto("SOFTRESTAURANT_PRO", "EPC")
    print(f"[RESOLVER] EPC -> {r} (esperado OK, id=1)")
    r2 = resolver_tipo_movimiento_desde_concepto("SOFTRESTAURANT_PRO", "CONCEPTO_INEXISTENTE")
    print(f"[RESOLVER] inexistente -> {r2.motivo} (esperado PENDIENTE_SIN_MAPEO)")
    conn.close()


if __name__ == "__main__":
    main()
