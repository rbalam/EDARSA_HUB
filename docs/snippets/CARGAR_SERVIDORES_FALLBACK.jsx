// =============================================================================
// SNIPPET: CARGAR SERVIDORES CON FALLBACK ROBUSTO
// OBJETIVO: Garantizar que el modal de permisos nunca quede sin opciones
// =============================================================================

// Guardar/Reemplazar en el componente del Modal de Permisos de Usuarios

const cargarServidores = async () => {
    try {
        setIsLoadingServers(true);
        const response = await api.get('/servidores'); // o la ruta que uses
        
        // Si la API responde bien pero viene vacía (por el interceptor 502)
        if (!response.data || response.data.length === 0) {
            throw new Error("API retornó lista vacía (Posible Error 502)");
        }
        
        setServidores(response.data);
    } catch (error) {
        console.warn("[FALLBACK] Error al cargar servidores, inyectando lista de respaldo:", error);
        
        // Fallback robusto: Si la API central falla, inyecta los servidores maestros localmente
        // para que nunca te quedes sin opciones en el modal de permisos.
        const servidoresRespaldo = [
            { id: 130, nombre: "130° MÉRIDA" },
            { id: 131, nombre: "130° QUERÉTARO" },
            { id: 132, nombre: "CIENFUEGOS" },
            { id: 133, nombre: "ORIGEN" },
            { id: 134, nombre: "LA ESTELAR" }
        ];
        
        setServidores(servidoresRespaldo);
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
