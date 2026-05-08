-- ============================================================================
-- MIGRACIÓN: Crear tabla Finanzas_KPIs_Historico
-- Fecha: 2026-04-26
-- Descripción: Tabla para almacenar KPIs históricos de Finanzas consolidados
--              de múltiples fuentes (Cortes Z, CxP, Ingresos TPV)
-- ============================================================================

-- Verificar/Crear tabla principal
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[Finanzas_KPIs_Historico]') AND type in (N'U'))
BEGIN
    CREATE TABLE [dbo].[Finanzas_KPIs_Historico] (
        -- Identificadores
        id INT IDENTITY(1,1) PRIMARY KEY,
        run_id VARCHAR(50) NOT NULL,               -- ID de ejecución de carga
        server_id VARCHAR(100) NOT NULL,           -- ID del servidor fuente
        sucursal_id VARCHAR(100) NOT NULL,         -- ID de sucursal
        system_type_normalized VARCHAR(50) NOT NULL, -- SOFTRESTAURANT, MANAGEMENTPRO
        fecha DATE NOT NULL,                       -- Fecha del KPI
        
        -- Tipo de KPI
        kpi_tipo VARCHAR(50) NOT NULL,             -- CORTE_Z, CXP, INGRESO_TPV, EGRESO
        
        -- Métricas de Ingresos (Cortes Z)
        ventas_efectivo DECIMAL(18,2) DEFAULT 0,
        ventas_tarjeta_debito DECIMAL(18,2) DEFAULT 0,
        ventas_tarjeta_credito DECIMAL(18,2) DEFAULT 0,
        ventas_tarjeta_amex DECIMAL(18,2) DEFAULT 0,
        ventas_otros DECIMAL(18,2) DEFAULT 0,
        ventas_total DECIMAL(18,2) DEFAULT 0,
        propinas DECIMAL(18,2) DEFAULT 0,
        
        -- Comisiones TPV calculadas
        comision_debito DECIMAL(18,2) DEFAULT 0,
        comision_credito DECIMAL(18,2) DEFAULT 0,
        comision_amex DECIMAL(18,2) DEFAULT 0,
        comision_total DECIMAL(18,2) DEFAULT 0,
        
        -- Métricas de Egresos (CxP)
        cxp_facturas_count INT DEFAULT 0,
        cxp_monto_total DECIMAL(18,2) DEFAULT 0,
        cxp_monto_alimentos DECIMAL(18,2) DEFAULT 0,
        cxp_monto_bebidas DECIMAL(18,2) DEFAULT 0,
        cxp_monto_otros DECIMAL(18,2) DEFAULT 0,
        cxp_saldo_pendiente DECIMAL(18,2) DEFAULT 0,
        
        -- Flujo de caja neto
        flujo_efectivo_neto DECIMAL(18,2) DEFAULT 0,
        
        -- Metadatos
        empresa_id VARCHAR(100),
        empresa_nombre NVARCHAR(200),
        origen VARCHAR(50) DEFAULT 'HISTORICAL_LOAD', -- HISTORICAL_LOAD, SYNC_NIGHTLY
        fecha_carga DATETIME DEFAULT GETDATE(),
        fecha_actualizacion DATETIME DEFAULT GETDATE(),
        
        -- Constraint único para idempotencia
        CONSTRAINT UX_Finanzas_KPIs_Historico UNIQUE (
            server_id, 
            sucursal_id, 
            system_type_normalized, 
            fecha, 
            kpi_tipo
        )
    );
    
    -- Índices para consultas frecuentes
    CREATE INDEX IX_Finanzas_KPIs_Historico_Fecha ON Finanzas_KPIs_Historico(fecha);
    CREATE INDEX IX_Finanzas_KPIs_Historico_Server ON Finanzas_KPIs_Historico(server_id);
    CREATE INDEX IX_Finanzas_KPIs_Historico_Sucursal ON Finanzas_KPIs_Historico(sucursal_id);
    CREATE INDEX IX_Finanzas_KPIs_Historico_Tipo ON Finanzas_KPIs_Historico(kpi_tipo);
    CREATE INDEX IX_Finanzas_KPIs_Historico_RunId ON Finanzas_KPIs_Historico(run_id);
    
    PRINT 'Tabla Finanzas_KPIs_Historico creada exitosamente';
END
ELSE
BEGIN
    PRINT 'Tabla Finanzas_KPIs_Historico ya existe';
END
GO

-- ============================================================================
-- Vista: Resumen diario de Finanzas por sucursal
-- ============================================================================
IF EXISTS (SELECT * FROM sys.views WHERE name = 'vw_Finanzas_Resumen_Diario')
    DROP VIEW vw_Finanzas_Resumen_Diario;
GO

CREATE VIEW vw_Finanzas_Resumen_Diario AS
SELECT 
    fecha,
    sucursal_id,
    empresa_nombre,
    -- Ingresos
    SUM(CASE WHEN kpi_tipo = 'CORTE_Z' THEN ventas_total ELSE 0 END) AS ingresos_total,
    SUM(CASE WHEN kpi_tipo = 'CORTE_Z' THEN ventas_efectivo ELSE 0 END) AS ingresos_efectivo,
    SUM(CASE WHEN kpi_tipo = 'CORTE_Z' THEN ventas_tarjeta_debito + ventas_tarjeta_credito + ventas_tarjeta_amex ELSE 0 END) AS ingresos_tarjetas,
    -- Comisiones
    SUM(comision_total) AS comisiones_total,
    -- Egresos
    SUM(CASE WHEN kpi_tipo = 'CXP' THEN cxp_monto_total ELSE 0 END) AS egresos_total,
    SUM(CASE WHEN kpi_tipo = 'CXP' THEN cxp_saldo_pendiente ELSE 0 END) AS saldo_pendiente,
    -- Flujo neto
    SUM(CASE WHEN kpi_tipo = 'CORTE_Z' THEN ventas_total ELSE 0 END) 
        - SUM(comision_total) 
        - SUM(CASE WHEN kpi_tipo = 'CXP' THEN cxp_monto_total ELSE 0 END) AS flujo_neto_estimado
FROM Finanzas_KPIs_Historico
GROUP BY fecha, sucursal_id, empresa_nombre;
GO

PRINT 'Vista vw_Finanzas_Resumen_Diario creada';
GO
