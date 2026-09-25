"""
Migración: Catálogo Canónico de Sincronizaciones
================================================
Crea dbo.Sistema_Sync_Catalogo: fuente única (NO hardcode) de los tipos de
sincronización del sistema, agrupados por `Grupo`, con dependencias y orden de
ejecución. Reemplaza el dict hardcodeado TIPOS_SYNC del panel Re-sync.

- Configurable/editable vía API (CRUD).
- Dependencias en JSON: [{"codigo": "x", "obligatoria": false}]
- HandlerImplementado: 1 solo cuando existe un handler real de re-sync.

Idempotente: crea tabla si no existe; hace UPSERT (MERGE) del seed sin pisar
ediciones del usuario en filas ya existentes (solo inserta las que falten).

NO USA MONGODB - 100% SQL Server (EDARSAHUB).
"""
import os
import sys
import json
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
        timeout=60, login_timeout=30,
    )


DDL = """
IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = 'Sistema_Sync_Catalogo')
BEGIN
    CREATE TABLE dbo.Sistema_Sync_Catalogo (
        Codigo               NVARCHAR(100)  NOT NULL PRIMARY KEY,
        Nombre               NVARCHAR(200)  NOT NULL,
        Grupo                NVARCHAR(100)  NOT NULL,
        Descripcion          NVARCHAR(500)  NULL,
        Orden                INT            NOT NULL DEFAULT 100,
        NivelRiesgo          NVARCHAR(20)   NOT NULL DEFAULT 'MEDIO',
        PermiteResync        BIT            NOT NULL DEFAULT 1,
        PermiteDryRun        BIT            NOT NULL DEFAULT 1,
        RequiereUnidad       BIT            NOT NULL DEFAULT 1,
        RequiereRangoFechas  BIT            NOT NULL DEFAULT 1,
        RangoMaxDias         INT            NOT NULL DEFAULT 30,
        Handler              NVARCHAR(200)  NULL,
        HandlerImplementado  BIT            NOT NULL DEFAULT 0,
        TablaDestino         NVARCHAR(200)  NULL,
        Dependencias         NVARCHAR(MAX)  NULL,
        Activo               BIT            NOT NULL DEFAULT 1,
        FechaCreacion        DATETIME       NOT NULL DEFAULT GETDATE(),
        FechaActualizacion   DATETIME       NULL
    );
END
"""


def _seed():
    """Definición canónica inicial (grupos/tipos/dependencias)."""
    return [
        # ---------------- Grupo COMERCIAL ----------------
        dict(codigo='comercial_ventas_detalle', nombre='Detalle de Ventas (Sync_Sales)',
             grupo='Comercial', orden=10, nivel='MEDIO', resync=1, dry=1, unidad=1, rango=1,
             rmax=31, handler='backfill_sync_sales', impl=0, tabla='Sync_Sales',
             deps=[],
             desc='Sincroniza el detalle ticket/producto desde el POS hacia Sync_Sales.'),
        dict(codigo='comercial_ventas_cerradas', nombre='Ventas Cerradas (KPIs)',
             grupo='Comercial', orden=20, nivel='MEDIO', resync=1, dry=1, unidad=1, rango=1,
             rmax=30, handler='sync_softrestaurant_ventas_cerradas', impl=1,
             tabla='Comercial_KPIs_Diarios_v2',
             deps=[{'codigo': 'comercial_ventas_detalle', 'obligatoria': False}],
             desc='Sincroniza cheques cerrados (KPIs diarios) desde SoftRestaurant/MPRO.'),
        # ---------------- Grupo CATÁLOGOS ----------------
        dict(codigo='catalogo_productos', nombre='Catálogo de Productos',
             grupo='Catálogos', orden=10, nivel='BAJO', resync=1, dry=1, unidad=1, rango=0,
             rmax=0, handler='sync_catalogo_productos', impl=0, tabla='Sync_Productos',
             deps=[],
             desc='Sincroniza el catálogo de productos/insumos desde el POS.'),
        dict(codigo='catalogo_proveedores', nombre='Catálogo de Proveedores',
             grupo='Catálogos', orden=20, nivel='BAJO', resync=1, dry=1, unidad=1, rango=0,
             rmax=0, handler='sync_catalogo_proveedores', impl=0, tabla='Sync_Proveedores',
             deps=[],
             desc='Sincroniza el catálogo de proveedores desde el POS.'),
        dict(codigo='catalogo_filtros', nombre='Catálogo de Filtros / Familias',
             grupo='Catálogos', orden=30, nivel='BAJO', resync=1, dry=1, unidad=1, rango=0,
             rmax=0, handler='sync_catalogo_filtros', impl=0, tabla='Sync_Catalogo_Filtros',
             deps=[{'codigo': 'catalogo_productos', 'obligatoria': False}],
             desc='Sincroniza familias/grupos/filtros del catálogo (derivan de productos).'),
        # ---------------- Grupo INVENTARIOS ----------------
        dict(codigo='inventarios_requisiciones', nombre='Requisiciones / Órdenes de Compra',
             grupo='Inventarios', orden=10, nivel='MEDIO', resync=1, dry=1, unidad=1, rango=1,
             rmax=60, handler='sync_requisiciones', impl=0, tabla='Compras_Requisiciones_Sync',
             deps=[{'codigo': 'catalogo_productos', 'obligatoria': False},
                   {'codigo': 'catalogo_proveedores', 'obligatoria': False}],
             desc='Sincroniza requisiciones/órdenes de compra (encabezado y detalle).'),
        dict(codigo='inventarios_fisicos', nombre='Inventarios Físicos',
             grupo='Inventarios', orden=20, nivel='MEDIO', resync=1, dry=1, unidad=1, rango=1,
             rmax=60, handler='sync_inventarios_fisicos', impl=1,
             tabla='Compras_Inventarios_Fisicos_Sync',
             deps=[{'codigo': 'catalogo_productos', 'obligatoria': False}],
             desc='Sincroniza los inventarios físicos capturados en el POS.'),
    ]


def run():
    conn = _conn()
    cur = conn.cursor()
    print('[MIG] Creando tabla Sistema_Sync_Catalogo (si no existe)...')
    cur.execute(DDL)
    conn.commit()

    inserted = 0
    for r in _seed():
        cur.execute("SELECT COUNT(1) FROM dbo.Sistema_Sync_Catalogo WHERE Codigo=%s", (r['codigo'],))
        if cur.fetchone()[0] > 0:
            continue
        cur.execute(
            """
            INSERT INTO dbo.Sistema_Sync_Catalogo
            (Codigo, Nombre, Grupo, Descripcion, Orden, NivelRiesgo, PermiteResync,
             PermiteDryRun, RequiereUnidad, RequiereRangoFechas, RangoMaxDias, Handler,
             HandlerImplementado, TablaDestino, Dependencias, Activo)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,1)
            """,
            (r['codigo'], r['nombre'], r['grupo'], r['desc'], r['orden'], r['nivel'],
             r['resync'], r['dry'], r['unidad'], r['rango'], r['rmax'], r['handler'],
             r['impl'], r['tabla'], json.dumps(r['deps']))
        )
        inserted += 1
        print(f"  + {r['codigo']} ({r['grupo']})")
    conn.commit()

    cur.execute("SELECT Grupo, COUNT(1) FROM dbo.Sistema_Sync_Catalogo GROUP BY Grupo")
    print('[MIG] Resumen por grupo:')
    for g, c in cur.fetchall():
        print(f"    {g}: {c}")
    print(f'[MIG] Insertados nuevos: {inserted}')
    cur.close()
    conn.close()


if __name__ == '__main__':
    run()
