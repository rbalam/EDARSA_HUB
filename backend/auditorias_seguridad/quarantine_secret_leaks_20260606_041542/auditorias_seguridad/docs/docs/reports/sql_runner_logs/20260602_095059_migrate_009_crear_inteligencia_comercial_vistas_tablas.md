# EDARSAHUB SQL Runner Report

- Fecha: 2026-06-02T09:50:59.124313
- Modo: `migrate`
- Servidor: `54.39.104.176`
- Base de datos: `EDARSAHUB`
- Script: `/app/backend/database/migrations/009_crear_inteligencia_comercial_vistas_tablas.sql`

## Resultado
ERROR

## Detalle
```text
Error ejecutando SQL. Se hizo rollback. Detalle: (102, b"Incorrect syntax near '('.DB-Lib error message 20018, severity 15:\nGeneral SQL Server error: Check messages from the SQL Server\n")
```

## SQL ejecutado / revisado
```sql
/* ============================================================
   MIGRACIÓN: Vistas y Tablas Inteligencia Comercial
   Script: 009_crear_inteligencia_comercial_vistas_tablas.sql
   Modo: migrate
   
   Crea:
   - Vista Comercial_Inteligencia_VW_KPIsEjecutivos
   - Vista Comercial_Inteligencia_VW_SyncStatus
   - SP Sp_Validar_Inteligencia_Comercial_Status
   - Tabla Comercial_Inteligencia_VentasDetalleProducto
   ============================================================ */

-- 1. VISTA KPIs EJECUTIVOS
CREATE OR ALTER VIEW dbo.Comercial_Inteligencia_VW_KPIsEjecutivos
AS
SELECT
    k.unidad_negocio_id,
    k.unidad_negocio_nombre,
    k.server_id,
    k.sucursal_id,
    k.sucursal_nombre,
    k.sistema_origen,
    k.fecha_operacion,
    k.anio,
    k.mes,
    k.dia,
    ISNULL(k.ventas_total, 0) AS ventas_total,
    ISNULL(k.ventas_sin_propina, 0) AS ventas_sin_propina,
    ISNULL(k.propinas_total, 0) AS propinas_total,
    ISNULL(k.tickets_total, 0) AS tickets_total,
    ISNULL(k.pax_total, 0) AS pax_total,
    ISNULL(k.ticket_promedio, 0) AS ticket_promedio,
    ISNULL(k.pax_promedio, 0) AS pax_promedio,
    ISNULL(k.ventas_cerradas, 0) AS ventas_cerradas,
    ISNULL(k.ventas_abiertas, 0) AS ventas_abiertas,
    ISNULL(k.total_estimado_dia, 0) AS total_estimado_dia,
    k.es_venta_abierta,
    k.es_corte_cerrado,
    k.fuente_original,
    k.sync_run_id,
    k.fecha_sincronizacion,
    k.fecha_ultima_actualizacion
FROM dbo.Comercial_KPIs_Diarios_v2 k
WHERE ISNULL(k.activo, 1) = 1;
GO

-- 2. VISTA SYNC STATUS
CREATE OR ALTER VIEW dbo.Comercial_Inteligencia_VW_SyncStatus
AS
SELECT
    'Comercial_KPIs_Diarios_v2' AS fuente,
    MAX(fecha_operacion) AS ultima_fecha_operacion,
    MAX(fecha_sincronizacion) AS ultima_fecha_sincronizacion,
    COUNT_BIG(*) AS registros
FROM dbo.Comercial_KPIs_Diarios_v2
WHERE ISNULL(activo, 1) = 1

UNION ALL

SELECT
    'Comercial_Ventas_Dia_Abiertas_v2',
    MAX(fecha_operacion),
    MAX(fecha_ultima_actualizacion),
    COUNT_BIG(*)
FROM dbo.Comercial_Ventas_Dia_Abiertas_v2

UNION ALL

SELECT
    'Sync_PAX_Detalle',
    MAX(FechaOperacion),
    MAX(FechaSync),
    COUNT_BIG(*)
FROM dbo.Sync_PAX_Detalle

UNION ALL

SELECT
    'Sync_Sales',
    CAST(MAX(FechaHora) AS DATE),
    MAX(last_modified),
    COUNT_BIG(*)
FROM dbo.Sync_Sales;
GO

-- 3. STORED PROCEDURE VALIDACIÓN STATUS
CREATE OR ALTER PROCEDURE dbo.Sp_Validar_Inteligencia_Comercial_Status
AS
BEGIN
    SET NOCOUNT ON;

    SELECT
        fuente,
        ultima_fecha_operacion,
        ultima_fecha_sincronizacion,
        registros,
        CASE
            WHEN registros = 0 THEN 'SIN_DATOS'
            WHEN ultima_fecha_operacion IS NULL THEN 'SIN_DATOS'
            WHEN ultima_fecha_operacion < DATEADD(DAY, -2, CAST(GETDATE() AS DATE)) THEN 'STALE'
            ELSE 'OK'
        END AS estado
    FROM dbo.Comercial_Inteligencia_VW_SyncStatus;
END;
GO

-- 4. TABLA DETALLE VENTAS POR PRODUCTO
IF OBJECT_ID('dbo.Comercial_Inteligencia_VentasDetalleProducto', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.Comercial_Inteligencia_VentasDetalleProducto (
        id UNIQUEIDENTIFIER NOT NULL DEFAULT NEWID() PRIMARY KEY,
        unidad_negocio_id NVARCHAR(50) NULL,
        unidad_negocio_nombre NVARCHAR(100) NULL,
        server_id NVARCHAR(50) NULL,
        sucursal_id NVARCHAR(50) NULL,
        sucursal_nombre NVARCHAR(100) NULL,
        sistema_origen NVARCHAR(20) NULL,
        fecha_operacion DATE NOT NULL,
        fecha_hora DATETIME2 NULL,
        numero_ticket NVARCHAR(64) NULL,
        id_transaccion NVARCHAR(64) NULL,
        producto_codigo_fuente NVARCHAR(100) NULL,
        producto_id UNIQUEIDENTIFIER NULL,
        producto_nombre NVARCHAR(300) NULL,
        familia_id UNIQUEIDENTIFIER NULL,
        familia_nombre NVARCHAR(200) NULL,
        subfamilia_id UNIQUEIDENTIFIER NULL,
        subfamilia_nombre NVARCHAR(200) NULL,
        casa NVARCHAR(100) NULL,
        porcentaje_alcohol DECIMAL(5,2) NULL,
        es_alcohol BIT NULL,
        cantidad DECIMAL(18,4) NULL,
        precio_unitario DECIMAL(18,4) NULL,
        importe_bruto DECIMAL(18,4) NULL,
        importe_neto DECIMAL(18,4) NULL,
        descuento DECIMAL(18,4) NULL,
        propina DECIMAL(18,4) NULL,
        pax INT NULL,
        sync_run_id NVARCHAR(100) NULL,
        hash_origen NVARCHAR(64) NULL,
        fecha_sincronizacion DATETIME2 NOT NULL DEFAULT SYSDATETIME(),
        activo BIT NOT NULL DEFAULT 1
    );

    CREATE INDEX IX_Comercial_Intel_VentasDetalle_Fecha
    ON dbo.Comercial_Inteligencia_VentasDetalleProducto(fecha_operacion);

    CREATE INDEX IX_Comercial_Intel_VentasDetalle_Unidad
    ON dbo.Comercial_Inteligencia_VentasDetalleProducto(unidad_negocio_nombre, fecha_operacion);

    CREATE INDEX IX_Comercial_Intel_VentasDetalle_Producto
    ON dbo.Comercial_Inteligencia_VentasDetalleProducto(producto_codigo_fuente, fecha_operacion);

    CREATE UNIQUE INDEX UX_Comercial_Intel_VentasDetalle_NoDup
    ON dbo.Comercial_Inteligencia_VentasDetalleProducto(
        ISNULL(id_transaccion, ''),
        ISNULL(numero_ticket, ''),
        ISNULL(producto_codigo_fuente, ''),
        fecha_operacion
    );
END;
GO

```