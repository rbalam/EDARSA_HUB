"""
Migración: Catálogo Comercial Enriquecido de Productos (Bloque B).
==================================================================
COMERCIAL-ENRIQUECIDO-B1 (2026-06-09)

Crea las tablas canónicas NO destructivas para enriquecer el catálogo de
productos con atributos comerciales/alcohol que el SYNC no gestiona:

  dbo.Comercial_Productos_Enriquecidos
    - Enlace 1:1 con dbo.Sync_Productos.ProductoID (producto_id).
    - Patrón snake_case espejo de Comercial_Inteligencia_VentasDetalleProducto
      (id uniqueidentifier PK DEFAULT NEWID()), subsistema que la consumirá.
    - NO duplica el catálogo base: nombre/familia/etc. se leen por JOIN a
      Sync_Productos. Aquí viven SOLO los campos de enriquecimiento.

  dbo.Comercial_Marcas_Diccionario
    - Diccionario canónico marca -> grupo_comercial/categoria/tipo_alcohol/grado.
    - Reemplaza listas hardcodeadas de casas/marcas (la fuente es la tabla).

NO toca dbo.Producto_Catalogo (vacía, PK INT, sin campos alcohol) por decisión.
Idempotente.
"""
import os
from dotenv import load_dotenv

load_dotenv()

from core.db import execute_sql_query
from core.server_registry import EDARSAHUB_CONFIG as C

DDL_ENRIQUECIDOS = """
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'Comercial_Productos_Enriquecidos')
BEGIN
    CREATE TABLE dbo.Comercial_Productos_Enriquecidos (
        id                      UNIQUEIDENTIFIER NOT NULL CONSTRAINT DF_CPE_id DEFAULT NEWID(),
        producto_id             UNIQUEIDENTIFIER NULL,
        server_id               NVARCHAR(50)  NULL,
        system_type             NVARCHAR(20)  NULL,
        unidad_codigo           NVARCHAR(50)  NULL,
        codigo_producto_origen  NVARCHAR(100) NULL,
        nombre_producto         NVARCHAR(300) NULL,
        familia_origen          NVARCHAR(200) NULL,
        grupo_comercial         NVARCHAR(200) NULL,
        casa_comercial          NVARCHAR(200) NULL,
        marca                   NVARCHAR(200) NULL,
        categoria               NVARCHAR(150) NULL,
        subcategoria            NVARCHAR(150) NULL,
        tipo_alcohol            NVARCHAR(100) NULL,
        es_alcoholico           BIT NOT NULL CONSTRAINT DF_CPE_esalc DEFAULT 0,
        grado_alcohol           DECIMAL(5,2)  NULL,
        presentacion_ml         DECIMAL(12,2) NULL,
        presentacion_texto      NVARCHAR(100) NULL,
        ean                     NVARCHAR(50)  NULL,
        imagen_url              NVARCHAR(500) NULL,
        proveedor_id            UNIQUEIDENTIFIER NULL,
        representante_id        UNIQUEIDENTIFIER NULL,
        precio_venta            DECIMAL(18,4) NULL,
        confianza               DECIMAL(5,2)  NULL,
        requiere_validacion     BIT NOT NULL CONSTRAINT DF_CPE_reqval DEFAULT 0,
        regla_usada             NVARCHAR(200) NULL,
        fuente_grupo_url        NVARCHAR(500) NULL,
        fuente_grado_url        NVARCHAR(500) NULL,
        observaciones           NVARCHAR(1000) NULL,
        activo                  BIT NOT NULL CONSTRAINT DF_CPE_activo DEFAULT 1,
        fuente                  NVARCHAR(100) NULL CONSTRAINT DF_CPE_fuente DEFAULT 'EDARSAHUB',
        fecha_creacion          DATETIME2 NOT NULL CONSTRAINT DF_CPE_fcrea DEFAULT SYSUTCDATETIME(),
        fecha_actualizacion     DATETIME2 NULL,
        usuario_creacion        NVARCHAR(100) NULL,
        usuario_actualizacion   NVARCHAR(100) NULL,
        CONSTRAINT PK_Comercial_Productos_Enriquecidos PRIMARY KEY (id)
    );
END
"""

# Índices (idempotentes, mínimos y útiles)
DDL_INDICES = [
    # Enlace 1:1 con el producto canónico (filtrado: solo filas con producto_id)
    ("UQ_CPE_producto_id",
     "CREATE UNIQUE INDEX UQ_CPE_producto_id ON dbo.Comercial_Productos_Enriquecidos(producto_id) WHERE producto_id IS NOT NULL"),
    # Clave operativa (server + codigo): NO única (en el origen un mismo código
    # puede reutilizarse con distinto producto_id). El enlace 1:1 real es producto_id.
    ("IX_CPE_srv_cod",
     "CREATE INDEX IX_CPE_srv_cod ON dbo.Comercial_Productos_Enriquecidos(server_id, codigo_producto_origen)"),
    ("IX_CPE_codigo", "CREATE INDEX IX_CPE_codigo ON dbo.Comercial_Productos_Enriquecidos(codigo_producto_origen)"),
    ("IX_CPE_marca", "CREATE INDEX IX_CPE_marca ON dbo.Comercial_Productos_Enriquecidos(marca)"),
    ("IX_CPE_grupo", "CREATE INDEX IX_CPE_grupo ON dbo.Comercial_Productos_Enriquecidos(grupo_comercial)"),
    ("IX_CPE_categoria", "CREATE INDEX IX_CPE_categoria ON dbo.Comercial_Productos_Enriquecidos(categoria)"),
    ("IX_CPE_tipoalc", "CREATE INDEX IX_CPE_tipoalc ON dbo.Comercial_Productos_Enriquecidos(tipo_alcohol)"),
    ("IX_CPE_esalc", "CREATE INDEX IX_CPE_esalc ON dbo.Comercial_Productos_Enriquecidos(es_alcoholico)"),
    ("IX_CPE_unidad", "CREATE INDEX IX_CPE_unidad ON dbo.Comercial_Productos_Enriquecidos(unidad_codigo)"),
    ("IX_CPE_busqueda_comercial",
     "CREATE INDEX IX_CPE_busqueda_comercial ON dbo.Comercial_Productos_Enriquecidos(unidad_codigo, grupo_comercial, marca, categoria, tipo_alcohol)"),
]

DDL_DICCIONARIO = """
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'Comercial_Marcas_Diccionario')
BEGIN
    CREATE TABLE dbo.Comercial_Marcas_Diccionario (
        id                UNIQUEIDENTIFIER NOT NULL CONSTRAINT DF_CMD_id DEFAULT NEWID(),
        marca             NVARCHAR(200) NOT NULL,
        patron            NVARCHAR(300) NULL,
        grupo_comercial   NVARCHAR(200) NULL,
        casa_comercial    NVARCHAR(200) NULL,
        categoria         NVARCHAR(150) NULL,
        subcategoria_base NVARCHAR(150) NULL,
        tipo_alcohol      NVARCHAR(100) NULL,
        grado_default     DECIMAL(5,2)  NULL,
        fuente_grupo_url  NVARCHAR(500) NULL,
        fuente_grado      NVARCHAR(500) NULL,
        activo            BIT NOT NULL CONSTRAINT DF_CMD_activo DEFAULT 1,
        fecha_creacion    DATETIME2 NOT NULL CONSTRAINT DF_CMD_fcrea DEFAULT SYSUTCDATETIME(),
        CONSTRAINT PK_Comercial_Marcas_Diccionario PRIMARY KEY (id)
    );
    CREATE UNIQUE INDEX UQ_CMD_marca ON dbo.Comercial_Marcas_Diccionario(marca);
END
"""


def _q(sql):
    return execute_sql_query(C['host'], C['port'], C['database'], C['username'], C['password'], sql)


def main():
    print("[B1] Creando dbo.Comercial_Productos_Enriquecidos...")
    _q(DDL_ENRIQUECIDOS)
    for nombre, ddl in DDL_INDICES:
        guard = (f"IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name='{nombre}' "
                 f"AND object_id=OBJECT_ID('dbo.Comercial_Productos_Enriquecidos'))\n{ddl}")
        _q(guard)
    print("[B1] Creando dbo.Comercial_Marcas_Diccionario...")
    _q(DDL_DICCIONARIO)

    chk = _q("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES "
             "WHERE TABLE_NAME IN ('Comercial_Productos_Enriquecidos','Comercial_Marcas_Diccionario')")
    print("[B1] Tablas existentes:", [r['TABLE_NAME'] for r in chk])
    idx = _q("SELECT name FROM sys.indexes WHERE object_id=OBJECT_ID('dbo.Comercial_Productos_Enriquecidos') AND name IS NOT NULL")
    print("[B1] Índices:", [r['name'] for r in idx])


if __name__ == "__main__":
    main()
