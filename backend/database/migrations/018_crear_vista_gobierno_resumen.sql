/* ============================================================
   VISTA: Sistema_VW_Gobierno_Tablas_Resumen
   Resumen agrupado por módulo, categoría y estado
   ============================================================ */

CREATE OR ALTER VIEW dbo.Sistema_VW_Gobierno_Tablas_Resumen
AS
SELECT
    modulo,
    categoria,
    estado,
    COUNT(*) AS total_tablas,
    SUM(CASE WHEN estado = 'NO_USAR_NUEVO' THEN 1 ELSE 0 END) AS total_no_usar_nuevo,
    SUM(CASE WHEN categoria = 'SIN_CLASIFICAR' THEN 1 ELSE 0 END) AS total_sin_clasificar
FROM dbo.Sistema_Gobierno_Tablas
GROUP BY modulo, categoria, estado;
