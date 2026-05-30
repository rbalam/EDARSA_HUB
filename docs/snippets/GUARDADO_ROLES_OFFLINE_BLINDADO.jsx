// =============================================================================
// SNIPPET: GUARDADO FORZADO DE ROLES EN MODO OFFLINE (BLINDAJE TOTAL)
// OBJETIVO: Permitir guardar roles incluso cuando la API está caída
// =============================================================================

// Reemplaza la función de guardado en el componente del Modal de Roles
const handleSave = async (e) => {
    // Evita que el formulario recargue la página si es un evento submit
    if (e && e.preventDefault) e.preventDefault(); 
    
    try {
        setIsLoading(true);

        // 1. Simulamos una pausa de red para evitar colapsos
        await new Promise(resolve => setTimeout(resolve, 500));

        // 2. Guardado Forzado en Memoria Local (Ignorando la API caída)
        const rolesGuardados = JSON.parse(localStorage.getItem('roles_backup_offline')) || [];
        
        // Asumiendo que tus datos del formulario están en una variable como 'rolData' o 'formData'
        const rolActualizado = {
            ...rolData, 
            id: rolData.id || Date.now(),
            fecha_modificacion: new Date().toISOString(),
            _estado_offline: 'pendiente_sincronizacion'
        };

        // Actualizamos la lista local
        const nuevaListaRoles = rolesGuardados.filter(r => r.id !== rolActualizado.id);
        nuevaListaRoles.push(rolActualizado);
        localStorage.setItem('roles_backup_offline', JSON.stringify(nuevaListaRoles));

        console.warn("[BLINDAJE] Rol guardado en modo offline.");
        
        // 3. Notificación de éxito y cierre forzado del modal
        alert("Cambios guardados localmente. Se sincronizarán cuando el servidor central responda.");
        
        if (typeof onClose === 'function') {
            onClose(); // Cierra el modal
        }

    } catch (error) {
        console.error("[ERROR BLINDAJE] No se pudo forzar el guardado local:", error);
    } finally {
        setIsLoading(false); // Quita el estado de "pensando" del botón
    }
};

// =============================================================================
// FUNCIÓN AUXILIAR: SINCRONIZAR ROLES OFFLINE CUANDO VUELVA LA CONEXIÓN
// =============================================================================
const sincronizarRolesOffline = async () => {
    const rolesPendientes = JSON.parse(localStorage.getItem('roles_backup_offline')) || [];
    const rolesConEstadoPendiente = rolesPendientes.filter(r => r._estado_offline === 'pendiente_sincronizacion');
    
    if (rolesConEstadoPendiente.length === 0) {
        console.log("[SYNC] No hay roles pendientes de sincronización");
        return;
    }
    
    console.log(`[SYNC] Sincronizando ${rolesConEstadoPendiente.length} roles...`);
    
    for (const rol of rolesConEstadoPendiente) {
        try {
            await api.post('/roles/guardar', rol);
            rol._estado_offline = 'sincronizado';
            console.log(`[SYNC] Rol "${rol.nombre}" sincronizado correctamente`);
        } catch (error) {
            console.error(`[SYNC] Error sincronizando rol "${rol.nombre}":`, error);
        }
    }
    
    // Actualizar localStorage con estados actualizados
    localStorage.setItem('roles_backup_offline', JSON.stringify(rolesPendientes));
};

export { handleSave, sincronizarRolesOffline };
