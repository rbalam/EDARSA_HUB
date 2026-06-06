// =============================================================================
// SNIPPET: CARGAR SERVIDORES CON CACHÉ DINÁMICO DE RESPALDO
// OBJETIVO: Usar datos reales cacheados en lugar de lista hardcodeada
// =============================================================================

// Código Limpio: Carga dinámica con Caché de Respaldo
const cargarServidores = async () => {
    try {
        setIsLoadingServers(true);
        // Intenta la conexión normal
        const response = await api.get('/api/servidores'); 
        
        if (!response.data || response.data.length === 0) {
            throw new Error("API retornó lista vacía (Posible Error 502)");
        }
        
        // Si hay éxito, guardamos la información real y actualizada en la memoria oculta
        localStorage.setItem('cache_servidores_dinamico', JSON.stringify(response.data));
        setServidores(response.data);

    } catch (error) {
        console.warn("[SISTEMA] Fallo de red. Cargando unidades desde el caché dinámico local.");
        
        // Solución limpia: Leemos el caché dinámico en lugar de una lista hardcodeada
        const cachéLocal = localStorage.getItem('cache_servidores_dinamico');
        
        if (cachéLocal) {
            setServidores(JSON.parse(cachéLocal));
        } else {
            // Solo si el usuario nunca ha cargado la página con éxito antes
            setServidores([]);
            console.error("No hay datos en caché para mostrar las unidades.");
        }
    } finally {
        setIsLoadingServers(false);
    }
};

// =============================================================================
// CONSTANTE EXPORTABLE: SERVIDORES DE RESPALDO
// =============================================================================
export const SERVIDORES_FALLBACK = [
    { id: 130, nombre: "130° MÉRIDA" },
    { id: 131, nombre: "130° QUERÉTARO" },
    { id: 132, nombre: "CIENFUEGOS" },
    { id: 133, nombre: "ORIGEN" },
    { id: 134, nombre: "LA ESTELAR" }
];
