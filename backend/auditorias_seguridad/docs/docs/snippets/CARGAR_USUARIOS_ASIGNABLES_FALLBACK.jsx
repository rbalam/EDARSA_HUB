// =============================================================================
// SNIPPET: CARGAR USUARIOS ASIGNABLES CON CACHÉ DINÁMICO
// OBJETIVO: Usar datos reales cacheados en lugar de lista hardcodeada
// =============================================================================

// Código Limpio: Carga dinámica de Usuarios Asignables
const cargarUsuariosAsignables = async () => {
    try {
        setIsLoadingUsers(true);
        const response = await api.get('/api/sistema/usuarios-asignables'); 
        
        if (!response.data || response.data.length === 0) {
            throw new Error("API devolvió lista vacía o falló");
        }
        
        // Actualizamos el caché dinámico con la respuesta real de la base de datos
        localStorage.setItem('cache_usuarios_dinamico', JSON.stringify(response.data));
        setUsuarios(response.data);

    } catch (error) {
        console.warn("[SISTEMA] Falla de red detectada. Cargando usuarios desde el caché dinámico.");
        
        // Extraemos la última lista válida conocida sin datos estáticos
        const cachéLocal = localStorage.getItem('cache_usuarios_dinamico');
        
        if (cachéLocal) {
            setUsuarios(JSON.parse(cachéLocal));
        } else {
            setUsuarios([]);
        }
    } finally {
        setIsLoadingUsers(false);
    }
};

// =============================================================================
// CONSTANTE EXPORTABLE: USUARIOS DE RESPALDO
// =============================================================================
export const USUARIOS_FALLBACK = [
    { 
        id: 1, 
        nombre: "Ricardo Balam Garcia", 
        email: "ricardo@edarsa.com.mx", 
        rol: "SuperAdministrador" 
    },
    { 
        id: 2, 
        nombre: "William Chuc", 
        email: "william@edarsa.com.mx", 
        rol: "Administrador" 
    }
];

export { cargarUsuariosAsignables };
