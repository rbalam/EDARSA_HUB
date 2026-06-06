-- =============================================================================
-- SCRIPT: VIEW INTELIGENCIA COMERCIAL
-- OBJETIVO: Vista consolidada para análisis y reporting de ventas
-- =============================================================================

CREATE VIEW [dbo].[View_Inteligencia_Comercial] AS
SELECT 
    v.[Fecha],
    v.[TenantID],
    v.[Periodo],
    p.[NombreProducto],
    p.[Familia],
    p.[Subfamilia],
    p.[Casa],
    p.[PorcentajeAlcohol],
    v.[Cantidad],
    v.[ImporteNeto],
    v.[Pax],
    v.[Propina]
FROM [dbo].[Fact_Ventas_Consolidadas] v
INNER JOIN [dbo].[Products] p ON v.[IdProducto] = p.[Id];
