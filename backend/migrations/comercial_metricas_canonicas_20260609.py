"""
Migración: Catálogo SQL de Métricas Canónicas Comerciales.
==========================================================
Las métricas canónicas (cheque_promedio, ticket_promedio, etc.) dejan de vivir
SOLO en código: su DEFINICIÓN DECLARATIVA se almacena en SQL para poder
administrarse, documentarse, auditarse y versionarse.

- dbo.Comercial_Metricas_Canonicas: definición declarativa
  (operacion='campo' usa campo_base; operacion='ratio' usa numerador/denominador).
  Los "átomos" base provienen de dbo.Comercial_KPIs_Diarios_v2:
  ventas, ventas_sin_propina, propinas, cheques, pax.
- dbo.Comercial_Metricas_Sinonimos: alias -> métrica canónica.

Idempotente (CREATE IF NOT EXISTS + UPSERT). NO toca catálogos existentes.

Uso: cd /app/backend && set -a && source .env && set +a && \
     python -m migrations.comercial_metricas_canonicas_20260609
"""
import logging
from core.sql_first.db import get_sql_connection

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("mig_metricas_canonicas")

DDL = """
IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name='Comercial_Metricas_Canonicas')
BEGIN
  CREATE TABLE dbo.Comercial_Metricas_Canonicas (
    id uniqueidentifier NOT NULL CONSTRAINT DF_Metricas_id DEFAULT NEWID(),
    codigo nvarchar(60) NOT NULL,
    label nvarchar(120) NOT NULL,
    descripcion nvarchar(400) NULL,
    formato nvarchar(20) NOT NULL CONSTRAINT DF_Metricas_fmt DEFAULT 'decimal',
    operacion nvarchar(20) NOT NULL,                 -- 'campo' | 'ratio'
    campo_base nvarchar(60) NULL,
    numerador nvarchar(60) NULL,
    denominador nvarchar(60) NULL,
    excluye_propina bit NOT NULL CONSTRAINT DF_Metricas_prop DEFAULT 1,
    fuente_tabla nvarchar(120) NOT NULL CONSTRAINT DF_Metricas_src DEFAULT 'dbo.Comercial_KPIs_Diarios_v2',
    orden int NOT NULL CONSTRAINT DF_Metricas_ord DEFAULT 0,
    version int NOT NULL CONSTRAINT DF_Metricas_ver DEFAULT 1,
    activo bit NOT NULL CONSTRAINT DF_Metricas_act DEFAULT 1,
    created_at datetime2 NOT NULL CONSTRAINT DF_Metricas_cr DEFAULT SYSUTCDATETIME(),
    updated_at datetime2 NOT NULL CONSTRAINT DF_Metricas_up DEFAULT SYSUTCDATETIME(),
    created_by nvarchar(120) NULL,
    modified_by nvarchar(120) NULL,
    CONSTRAINT PK_Comercial_Metricas_Canonicas PRIMARY KEY (id),
    CONSTRAINT UX_Comercial_Metricas_codigo UNIQUE (codigo)
  );
END;
IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name='Comercial_Metricas_Sinonimos')
BEGIN
  CREATE TABLE dbo.Comercial_Metricas_Sinonimos (
    id uniqueidentifier NOT NULL CONSTRAINT DF_MetSin_id DEFAULT NEWID(),
    metrica_codigo nvarchar(60) NOT NULL,
    sinonimo nvarchar(60) NOT NULL,
    activo bit NOT NULL CONSTRAINT DF_MetSin_act DEFAULT 1,
    CONSTRAINT PK_Comercial_Metricas_Sinonimos PRIMARY KEY (id),
    CONSTRAINT UX_Comercial_Metricas_sinonimo UNIQUE (sinonimo)
  );
END;
"""

# (codigo, label, descripcion, formato, operacion, campo_base, numerador, denominador, excluye_propina, orden)
METRICAS = [
    (
        "ventas",
        "Ventas con IVA",
        "Venta visible para tableros y reportes; propinas separadas.",
        "moneda",
        "campo",
        "ventas",
        None,
        None,
        0,
        10,
    ),
    (
        "ventas_sin_propina",
        "Ventas sin propina",
        "Métrica auxiliar; no sustituye la venta visible.",
        "moneda",
        "campo",
        "ventas_sin_propina",
        None,
        None,
        1,
        20,
    ),
    (
        "propinas",
        "Propinas",
        "Total de propinas separado de ventas.",
        "moneda",
        "campo",
        "propinas",
        None,
        None,
        0,
        30,
    ),
    (
        "cheques",
        "Cheques",
        "Número de cuentas, tickets o comandas.",
        "entero",
        "campo",
        "cheques",
        None,
        None,
        0,
        40,
    ),
    (
        "pax",
        "PAX",
        "Número de comensales.",
        "entero",
        "campo",
        "pax",
        None,
        None,
        0,
        50,
    ),
    (
        "cheque_promedio",
        "Cheque promedio",
        "Ventas con IVA / cheques.",
        "moneda",
        "ratio",
        None,
        "ventas",
        "cheques",
        0,
        60,
    ),
    (
        "ticket_promedio",
        "Cheque promedio (alias legacy)",
        "Alias compatible de cheque_promedio.",
        "moneda",
        "ratio",
        None,
        "ventas",
        "cheques",
        0,
        70,
    ),
    (
        "pax_promedio",
        "Consumo promedio por PAX",
        "Ventas con IVA / PAX.",
        "moneda",
        "ratio",
        None,
        "ventas",
        "pax",
        0,
        80,
    ),
    (
        "pax_por_cheque",
        "PAX por cheque",
        "PAX / cheques.",
        "decimal",
        "ratio",
        None,
        "pax",
        "cheques",
        0,
        90,
    ),
    (
        "cheques_por_pax",
        "Cheques por PAX",
        "Cheques / PAX.",
        "decimal",
        "ratio",
        None,
        "cheques",
        "pax",
        0,
        100,
    ),
]

SINONIMOS = {
    "ventas": [
        "venta_total",
        "ventas_total",
        "ventas_con_iva",
        "ventas_visibles",
    ],
    "ventas_sin_propina": [
        "venta_neta",
        "ventas_netas",
    ],
    "propinas": [
        "propina",
        "propinas_total",
    ],
    "cheques": [
        "tickets",
        "comandas",
        "cuentas",
        "tickets_total",
    ],
    "pax": [
        "comensales",
        "pax_total",
    ],
    "cheque_promedio": [
        "cheque_medio",
    ],
    "ticket_promedio": [
        "ticket_medio",
    ],
    "pax_promedio": [
        "venta_por_pax",
        "consumo_per_capita",
        "consumo_promedio_pax",
        "venta_pax",
    ],
    "pax_por_cheque": [
        "personas_por_cheque",
        "personas_por_cuenta",
        "pax_por_ticket",
    ],
    "cheques_por_pax": [
        "rotacion_por_comensal",
    ],
}

UPSERT_METRICA = """
MERGE dbo.Comercial_Metricas_Canonicas AS t
USING (SELECT %s AS codigo) AS s ON t.codigo = s.codigo
WHEN MATCHED THEN UPDATE SET
    label=%s, descripcion=%s, formato=%s, operacion=%s, campo_base=%s,
    numerador=%s, denominador=%s, excluye_propina=%s, orden=%s,
    version=t.version, updated_at=SYSUTCDATETIME(), modified_by='migration', activo=1
WHEN NOT MATCHED THEN INSERT
    (codigo, label, descripcion, formato, operacion, campo_base, numerador, denominador, excluye_propina, orden, created_by)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'migration');
"""

UPSERT_SINONIMO = """
MERGE dbo.Comercial_Metricas_Sinonimos AS target
USING (
    SELECT
        %s AS sinonimo,
        %s AS metrica_codigo
) AS source
ON target.sinonimo = source.sinonimo
WHEN MATCHED THEN
    UPDATE SET
        metrica_codigo = source.metrica_codigo,
        activo = 1
WHEN NOT MATCHED THEN
    INSERT (
        metrica_codigo,
        sinonimo,
        activo
    )
    VALUES (
        source.metrica_codigo,
        source.sinonimo,
        1
    );
"""


def run():
    conn = get_sql_connection()
    cur = conn.cursor()
    logger.info("Creando tablas (idempotente)…")
    cur.execute(DDL)
    conn.commit()

    for m in METRICAS:
        codigo, label, desc, fmt, op, cb, num, den, exprop, orden = m
        if codigo == "ventas_sin_propina":
            continue
        cur.execute(UPSERT_METRICA, (
            codigo, label, desc, fmt, op, cb, num, den, exprop, orden,
            codigo, label, desc, fmt, op, cb, num, den, exprop, orden,
        ))
    conn.commit()
    logger.info("UPSERT %d métricas", len(METRICAS))

    cur.execute("""
        UPDATE dbo.Comercial_Metricas_Canonicas
        SET
            activo = 0,
            updated_at = SYSUTCDATETIME(),
            modified_by = 'migration'
        WHERE codigo IN ('ventas_brutas', 'ventas_sin_propina');
    """)
    conn.commit()

    n_sin = 0
    for codigo, alias in SINONIMOS.items():
        if codigo == "ventas_sin_propina":
            continue
        for a in alias:
            cur.execute(UPSERT_SINONIMO, (a, codigo))
            n_sin += 1
    conn.commit()
    logger.info("UPSERT %d sinónimos", n_sin)
    cur.execute("""
        UPDATE dbo.Comercial_Metricas_Sinonimos
        SET activo = 0
        WHERE sinonimo IN (
            'venta_neta',
            'ventas_netas',
            'ventas_con_propina'
        );
    """)
    conn.commit()

    cur.execute("SELECT COUNT(*) FROM dbo.Comercial_Metricas_Canonicas")
    nm = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM dbo.Comercial_Metricas_Sinonimos")
    ns = cur.fetchone()[0]
    logger.info("==== OK: métricas=%d sinónimos=%d ====", nm, ns)
    conn.close()


if __name__ == "__main__":
    run()
