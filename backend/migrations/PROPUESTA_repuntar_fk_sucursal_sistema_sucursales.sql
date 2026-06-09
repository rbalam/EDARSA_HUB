-- =====================================================================
-- PROPUESTA DDL (NO EJECUTADA) - Re-apuntar FK SucursalID a Sistema_Sucursales
-- Decisión usuario: Ruta 🅐. Pendiente de TU revisión/aprobación.
-- =====================================================================
-- PROBLEMA: Inventario_Movimientos.SucursalID -> RH_Cat_Sucursales (catálogo RRHH
-- DESALINEADO con las unidades). El catálogo LIMPIO (1:1 con unidades, con EmpresaID)
-- es Sistema_Sucursales (1=ORIGEN,2=130QRO,3=CIENFUEGOS,4=ESTELAR,5=130MID), que es
-- además el FK de Sistema_SucursalServidorMapeo y lo que ya devuelve el resolver.
--
-- FK actual: FK_Inventario_Movimientos_Sucursal (SucursalID -> RH_Cat_Sucursales.SucursalID)
-- Las tablas Inventario_Movimientos / Detalle están VACÍAS -> cambio de bajo riesgo.
-- =====================================================================

-- ---------- FORWARD ----------
-- 1) (Opcional pero recomendado) verificar que no haya datos que violen el nuevo FK:
--    SELECT COUNT(*) FROM Inventario_Movimientos m
--    WHERE NOT EXISTS (SELECT 1 FROM Sistema_Sucursales s WHERE s.SucursalID = m.SucursalID);
--    -- Debe ser 0 antes de continuar (hoy la tabla está vacía).

IF EXISTS (SELECT 1 FROM sys.foreign_keys WHERE name = 'FK_Inventario_Movimientos_Sucursal')
    ALTER TABLE dbo.Inventario_Movimientos DROP CONSTRAINT FK_Inventario_Movimientos_Sucursal;
GO

ALTER TABLE dbo.Inventario_Movimientos WITH CHECK
    ADD CONSTRAINT FK_Inventario_Movimientos_Sucursal
    FOREIGN KEY (SucursalID) REFERENCES dbo.Sistema_Sucursales (SucursalID);
GO

-- ---------- ROLLBACK (volver a RH_Cat_Sucursales) ----------
-- IF EXISTS (SELECT 1 FROM sys.foreign_keys WHERE name = 'FK_Inventario_Movimientos_Sucursal')
--     ALTER TABLE dbo.Inventario_Movimientos DROP CONSTRAINT FK_Inventario_Movimientos_Sucursal;
-- GO
-- ALTER TABLE dbo.Inventario_Movimientos WITH CHECK
--     ADD CONSTRAINT FK_Inventario_Movimientos_Sucursal
--     FOREIGN KEY (SucursalID) REFERENCES dbo.RH_Cat_Sucursales (SucursalID);
-- GO

-- =====================================================================
-- NOTA: Tras este cambio, resolver_sucursal_id (que ya devuelve IDs de
-- Sistema_Sucursales) queda 100% consistente con Inventario_Movimientos:
--   ORIGEN=1, 130QRO=2, CIENFUEGOS=3, ESTELAR=4, 130MID=5  (5/5, EmpresaID-aligned).
-- No se requiere DDL adicional. No se tocan otras FKs.
-- =====================================================================
