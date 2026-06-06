-- =============================================================================
-- SCRIPT: VERIFICACION MODULO SATELITE COMPANERO - SUCURSAL 130
-- OBJETIVO: Confirmar visibilidad del menú en barra lateral Mérida
-- =============================================================================

SELECT 
    nombre_modulo AS "Menú",
    CASE WHEN es_satelite = TRUE THEN 'Satélite Independent' ELSE 'Core' END AS "Tipo Módulo",
    CASE WHEN habilitado = TRUE THEN '✅ VISIBLE EN MÉRIDA' ELSE '❌ OCULTO' END AS "Estado"
FROM modulos_hub m
JOIN configuracion_sucursales_modulos sm ON m.id_modulo = sm.id_modulo
WHERE sm.id_sucursal = '130' AND m.id_modulo = 'COMPANERO_SAT';
