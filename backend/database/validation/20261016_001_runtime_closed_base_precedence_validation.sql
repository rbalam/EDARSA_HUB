SET NOCOUNT ON;

-- Closed-base precedence: si existe KPI base y el snapshot vigente del mismo día
-- no tiene ventas abiertas, Runtime debe ser idéntico al base en venta/tickets/PAX.
WITH latest_snapshot AS (
    SELECT
        a.*,
        ROW_NUMBER() OVER (
            PARTITION BY a.unidad_negocio_id
            ORDER BY a.fecha_operacion DESC, a.snapshot_timestamp DESC, a.fecha_ultima_actualizacion DESC
        ) AS rn
    FROM dbo.Comercial_Ventas_Dia_Abiertas_v2 a
),
violations AS (
    SELECT
        b.unidad_negocio_id,
        b.fecha_operacion,
        b.ventas_total AS base_ventas,
        r.ventas_total AS runtime_ventas,
        b.tickets_total AS base_tickets,
        r.tickets_total AS runtime_tickets,
        b.pax_total AS base_pax,
        r.pax_total AS runtime_pax
    FROM dbo.Comercial_KPIs_Diarios_v2 b
    JOIN dbo.vw_Comercial_KPIs_Diarios_v2_Runtime r
      ON r.unidad_negocio_pk=b.unidad_negocio_pk
     AND r.sucursal_id=b.sucursal_id
     AND r.fecha_operacion=b.fecha_operacion
    JOIN latest_snapshot s
      ON s.rn=1
     AND s.unidad_negocio_id=b.unidad_negocio_id
     AND s.fecha_operacion=b.fecha_operacion
    WHERE ISNULL(b.activo,1)=1
      AND ISNULL(b.es_demo,0)=0
      AND ISNULL(s.ventas_abiertas,0)=0
      AND (
          ABS(ISNULL(r.ventas_total,0)-ISNULL(b.ventas_total,0)) > 0.01
          OR ISNULL(r.tickets_total,0) <> ISNULL(b.tickets_total,0)
          OR ISNULL(r.pax_total,0) <> ISNULL(b.pax_total,0)
      )
)
SELECT * FROM violations;

IF EXISTS (SELECT 1 FROM violations)
    THROW 51161, 'RUNTIME_CLOSED_BASE_PRECEDENCE_VIOLATION', 1;
