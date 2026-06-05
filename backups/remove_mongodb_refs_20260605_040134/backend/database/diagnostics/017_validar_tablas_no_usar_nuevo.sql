/* ============================================================
   DIAGNÓSTICO: Validación de Tablas NO_USAR_NUEVO
   Muestra tablas marcadas como NO_USAR_NUEVO con conteo de registros
   ============================================================ */

SELECT
    g.esquema,
    g.nombre_tabla,
    g.modulo,
    g.categoria,
    g.estado,
    g.tabla_reemplazo,
    g.observaciones,
    SUM(p.rows) AS registros_aproximados
FROM dbo.Sistema_Gobierno_Tablas g
LEFT JOIN sys.tables t
    ON t.name = g.nombre_tabla
LEFT JOIN sys.schemas s
    ON s.schema_id = t.schema_id
    AND s.name = g.esquema
LEFT JOIN sys.partitions p
    ON p.object_id = t.object_id
    AND p.index_id IN (0, 1)
WHERE g.estado = 'NO_USAR_NUEVO'
GROUP BY
    g.esquema,
    g.nombre_tabla,
    g.modulo,
    g.categoria,
    g.estado,
    g.tabla_reemplazo,
    g.observaciones
ORDER BY g.modulo, g.nombre_tabla;
