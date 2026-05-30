// =============================================================================
// SNIPPET: HANDLE SAVE ROLES CON PERSISTENCIA LOCAL (OFFLINE-FIRST)
// OBJETIVO: Si la API falla, guardar en LocalStorage para sync posterior
// =============================================================================

const handleSave = async (rolData) => {
  setIsLoading(true);
  try {
    // Intentar guardar mediante la API
    const response = await api.post('/roles/guardar', rolData);
    if (response.status === 200) {
      alert("Rol guardado con éxito");
      onClose();
    }
  } catch (error) {
    console.warn("La API falló, aplicando persistencia local:", error);
    // Blindaje: Guardar en LocalStorage para sincronizar cuando la red sea estable
    const pendingRoles = JSON.parse(localStorage.getItem('pending_role_updates') || '[]');
    pendingRoles.push({ ...rolData, timestamp: new Date().toISOString() });
    localStorage.setItem('pending_role_updates', JSON.stringify(pendingRoles));
    
    alert("Error de conexión: Rol guardado localmente. Se sincronizará al recuperar el servicio.");
    onClose();
  } finally {
    setIsLoading(false);
  }
};

// =============================================================================
// FUNCIÓN AUXILIAR: Sincronizar roles pendientes cuando vuelva la conexión
// =============================================================================
const syncPendingRoles = async () => {
  const pendingRoles = JSON.parse(localStorage.getItem('pending_role_updates') || '[]');
  if (pendingRoles.length === 0) return;

  const failedRoles = [];
  
  for (const rol of pendingRoles) {
    try {
      await api.post('/roles/guardar', rol);
      console.log(`[SYNC] Rol sincronizado: ${rol.nombre}`);
    } catch (error) {
      failedRoles.push(rol);
      console.error(`[SYNC] Falló sincronización para rol: ${rol.nombre}`);
    }
  }

  localStorage.setItem('pending_role_updates', JSON.stringify(failedRoles));
  
  if (failedRoles.length === 0) {
    console.log('[SYNC] Todos los roles pendientes fueron sincronizados');
  }
};
