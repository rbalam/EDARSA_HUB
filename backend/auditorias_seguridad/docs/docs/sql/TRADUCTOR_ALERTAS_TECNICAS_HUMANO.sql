-- =============================================================================
-- SCRIPT: TRADUCTOR DE ALERTAS TÉCNICAS A IDIOMA HUMANO
-- OBJETIVO: Hacer comprensibles los errores de sincronización para todo el equipo
-- =============================================================================

SELECT 
    -- 1. Identificar la Sucursal de forma clara
    sucursal_id AS "Código",
    CASE 
        WHEN sucursal_id = '130' THEN '130° MÉRIDA'
        ELSE 'Otra Sucursal'
    END AS "Sucursal",

    -- 2. Mostrar la última hora en formato legible
    TO_CHAR(ultima_sincronizacion, 'DD/MM/YYYY HH24:MI') AS "Última Actualización",

    -- 3. TRADUCCIÓN DEL ESTADO TÉCNICO A IDIOMA HUMANO
    CASE 
        WHEN estado = 'EXITOSO' THEN '✅ TODO EN ORDEN. El sistema está al día y mostrando las ventas reales.'
        WHEN estado = 'PENDIENTE' THEN '⏳ EN ESPERA. El sistema está intentando conectar con las cajas de la sucursal.'
        WHEN estado = 'FALLIDO' OR mensaje_error LIKE '%502%' OR mensaje_error LIKE '%timeout%' 
             THEN '🚨 ANTENA CAÍDA. La plataforma no se puede comunicar con el servidor central.'
        ELSE '⚠️ REVISIÓN REQUERIDA. Los datos están en pausa preventiva.'
    END AS "Estado del Sistema",

    -- 4. DIAGNÓSTICO COMERCIAL EXPLICADO SENCILLAMENTE
    CASE 
        WHEN estado = 'EXITOSO' 
             THEN 'Las pantallas comerciales reflejan las operaciones de forma correcta.'
        WHEN mensaje_error LIKE '%502%' OR mensaje_error LIKE '%Connection refused%'
             THEN 'El servidor central (API) se desconectó. El sistema se protegió y congeló las pantallas.'
        WHEN ultima_sincronizacion < CURRENT_DATE 
             THEN 'No han subido las ventas de hoy. Las tarjetas comerciales marcarán 0.0% de forma temporal.'
        ELSE 'Aviso preventivo: No se detecta movimiento reciente en el punto de venta.'
    END AS "Diagnóstico Comercial",

    -- 5. ACCIÓN EXACTA DE QUÉ HACER (SIN CÓDIGO)
    CASE 
        WHEN estado = 'EXITOSO' THEN 'No hay que hacer nada. Puedes usar la plataforma con confianza.'
        WHEN mensaje_error LIKE '%502%' 
             THEN 'Copiar alerta y pedir a Emergent: "Favor de reiniciar el servicio de la API central que está caído".'
        WHEN ultima_sincronizacion < CURRENT_DATE 
             THEN 'Verificar que la caja física en Mérida tenga internet y que hayan abierto el turno correctamente.'
        ELSE 'Presiona el botón negro "Actualizar" en el menú comercial para intentar reconectar.'
    END AS "Solución Inmediata"

FROM control_sincronizaciones
WHERE sucursal_id = '130' OR sistema = 'EDARSAHUB';
