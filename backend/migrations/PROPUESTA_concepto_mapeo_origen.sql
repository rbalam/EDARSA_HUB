-- =====================================================================
-- PROPUESTA DDL (NO EJECUTADA) - Sub-fase B: Catálogo DB-driven de conceptos
-- Inventario_ConceptoMapeoOrigen (SystemType + ConceptoOrigen -> TipoMovimientoID)
-- =====================================================================
-- Objetivo: ELIMINAR el dict hardcodeado TIPO_MOVIMIENTO_SR_TO_EDARSAHUB y
-- resolver el tipo de movimiento desde DB (cumple REGLA DE ORO: no hardcode).
-- Pendiente de APROBACIÓN explícita del usuario (revisión SQL/rollback/PK/FK).
-- =====================================================================

-- ---------- FORWARD ----------
IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = 'Inventario_ConceptoMapeoOrigen')
BEGIN
    CREATE TABLE dbo.Inventario_ConceptoMapeoOrigen (
        ConceptoMapeoID   INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
        SystemType        VARCHAR(40)  NOT NULL,
        ConceptoOrigen    VARCHAR(40)  NOT NULL,   -- EPC/SPC/ETA... (SR) ó Mo_Tipo (MPRO)
        TipoMovimientoID  TINYINT      NOT NULL,   -- FK -> Inventario_TipoMovimiento
        Descripcion       VARCHAR(120) NULL,
        Activo            BIT NOT NULL CONSTRAINT DF_ICMO_Activo DEFAULT (1),
        FechaCreacion     DATETIME2 NOT NULL CONSTRAINT DF_ICMO_Fecha DEFAULT (SYSUTCDATETIME()),
        CONSTRAINT FK_ICMO_Tipo FOREIGN KEY (TipoMovimientoID)
            REFERENCES dbo.Inventario_TipoMovimiento (TipoMovimientoID),
        CONSTRAINT UQ_ICMO_Concepto UNIQUE (SystemType, ConceptoOrigen)
    );
END
GO

-- ---------- ROLLBACK ----------
-- IF EXISTS (SELECT 1 FROM sys.tables WHERE name = 'Inventario_ConceptoMapeoOrigen')
--     DROP TABLE dbo.Inventario_ConceptoMapeoOrigen;
-- GO

-- =====================================================================
-- SEED PROPUESTO (DML, pendiente de aprobación) - migra el dict actual a DB.
-- Mapeo SoftRestaurant (del dict TIPO_MOVIMIENTO_SR_TO_EDARSAHUB):
--   EPC->1 (ENTRADA_COMPRA)   SPC->2 (SALIDA_DEV_PROV)
--   ETA->5 (TRASPASO_ENTRADA) STA->6 (TRASPASO_SALIDA)
--   ECI->3 (AJUSTE_ENTRADA)   SCI->4 (AJUSTE_SALIDA)
--   EPA/EPL/EPB->3            SPA/SPM/SPD->4
-- NOTA: los conceptos NO listados deben revisarse contra la tabla `conceptos`
--       del POS (C.tipo E/S) para mapearlos correctamente. NO inventar.
-- INSERT INTO dbo.Inventario_ConceptoMapeoOrigen (SystemType, ConceptoOrigen, TipoMovimientoID) VALUES
--   ('SOFTRESTAURANT_PRO','EPC',1), ('SOFTRESTAURANT_PRO','SPC',2),
--   ('SOFTRESTAURANT_PRO','ETA',5), ('SOFTRESTAURANT_PRO','STA',6),
--   ('SOFTRESTAURANT_PRO','ECI',3), ('SOFTRESTAURANT_PRO','SCI',4),
--   ('SOFTRESTAURANT_PRO','EPA',3), ('SOFTRESTAURANT_PRO','EPL',3), ('SOFTRESTAURANT_PRO','EPB',3),
--   ('SOFTRESTAURANT_PRO','SPA',4), ('SOFTRESTAURANT_PRO','SPM',4), ('SOFTRESTAURANT_PRO','SPD',4);
-- =====================================================================
