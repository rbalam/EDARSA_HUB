// =============================================================================
// UTILIDAD: HANDLE SAVE GENÉRICO OFFLINE-FIRST
// OBJETIVO: Función reutilizable para cualquier entidad con persistencia local
// =============================================================================

/**
 * Lógica consolidada para persistencia offline-first.
 * Aplica este bloque en los componentes de Usuarios y Roles.
 */
const handleSave = async (data, endpoint) => {
  setIsLoading(true);
  try {
    // 1. Intento de guardado en servidor central
    const response = await api.post(endpoint, data);
    
    if (response.status === 200 || response.status === 201) {
      alert("Cambios guardados correctamente en el servidor.");
      onClose();
    }
  } catch (error) {
    console.warn(`La API falló al guardar en ${endpoint}. Aplicando persistencia local.`, error);
    
    // 2. Blindaje: Guardado en LocalStorage
    // Se identifica el tipo de datos para gestionar colas separadas
    const storageKey = endpoint.includes('usuarios') ? 'pending_user_updates' : 'pending_role_updates';
    const pendingChanges = JSON.parse(localStorage.getItem(storageKey) || '[]');
    
    pendingChanges.push({ 
      ...data, 
      timestamp: new Date().toISOString(),
      source: endpoint 
    });
    
    localStorage.setItem(storageKey, JSON.stringify(pendingChanges));
    
    // 3. Feedback inmediato al usuario
    alert("Error de conexión con el servidor. Los cambios se han guardado localmente y se sincronizarán al restablecerse el servicio.");
    onClose();
  } finally {
    // 4. Gestión de estados para liberar la interfaz
    setIsLoading(false);
  }
};

// =============================================================================
// EJEMPLO DE USO EN COMPONENTES
// =============================================================================

// En UserForm.jsx:
// const onSubmit = (userData) => handleSave(userData, '/usuarios/guardar');

// En RoleForm.jsx:
// const onSubmit = (rolData) => handleSave(rolData, '/roles/guardar');

export default handleSave;
