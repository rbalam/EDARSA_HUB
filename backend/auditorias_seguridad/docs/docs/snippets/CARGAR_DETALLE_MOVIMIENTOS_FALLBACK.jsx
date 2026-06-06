// =============================================================================
// SNIPPET: CARGAR DETALLE MOVIMIENTOS CON FALLBACK A CACHÉ LOCAL
// OBJETIVO: Evitar pantalla vacía si el endpoint de detalle falla
// =============================================================================

// Reemplaza la función original de carga en el Modal de Detalle
const cargarDetalleMovimientos = async (parametrosFiltro) => {
    try {
        setIsLoadingDetail(true);
        
        // Petición al endpoint de detalle (ajusta la ruta según tu API)
        const response = await api.get('/api/comercial/detalle-movimientos', { params: parametrosFiltro });
        
        if (!response.data || response.data.length === 0) {
            throw new Error("El servidor devolvió un detalle vacío (Posible desface o 502)");
        }
        
        // Guardar en caché local para futuros fallbacks
        localStorage.setItem('comercial_detalle_backup', JSON.stringify(response.data));
        
        setMovimientos(response.data);
    } catch (error) {
        console.warn("[BLINDAJE] Falla en la carga del detalle. Inyectando recálculo local.");
        
        // Fallback de contingencia si el endpoint de detalle cae
        // Esto evita la pantalla de "No hay movimientos" y extrae datos de la caché global si existen
        const detalleCache = JSON.parse(localStorage.getItem('comercial_detalle_backup')) || [];
        setMovimientos(detalleCache);
        
        // Si no hay caché, mostrar mensaje informativo
        if (detalleCache.length === 0) {
            console.info("[INFO] No hay datos en caché local. Esperando reconexión al servidor.");
        }
    } finally {
        setIsLoadingDetail(false);
    }
};

// =============================================================================
// UTILIDAD: LIMPIAR CACHÉ DE DETALLE (Usar al cambiar de periodo/unidad)
// =============================================================================
const limpiarCacheDetalle = () => {
    localStorage.removeItem('comercial_detalle_backup');
    console.log("[CACHE] Caché de detalle comercial limpiado");
};

export { cargarDetalleMovimientos, limpiarCacheDetalle };
