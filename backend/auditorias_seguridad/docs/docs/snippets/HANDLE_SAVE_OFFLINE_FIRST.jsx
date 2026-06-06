// =============================================================================
// SNIPPET: HANDLE SAVE CON PERSISTENCIA LOCAL (OFFLINE-FIRST)
// OBJETIVO: Si la API falla, guardar en LocalStorage para sync posterior
// =============================================================================

// Script de reparación para handleSave en UserForm.jsx
const handleSave = async (userData) => {
  setIsLoading(true);
  try {
    // Intentar guardar mediante la API
    const response = await api.post('/usuarios/guardar', userData);
    if (response.status === 200) {
      alert("Usuario guardado con éxito");
      onClose();
    }
  } catch (error) {
    console.warn("La API falló, aplicando persistencia local:", error);
    // Blindaje: Si la API falla, guardar en LocalStorage para sincronización posterior
    const pendingChanges = JSON.parse(localStorage.getItem('pending_user_updates') || '[]');
    pendingChanges.push({ ...userData, timestamp: new Date().toISOString() });
    localStorage.setItem('pending_user_updates', JSON.stringify(pendingChanges));
    
    alert("Error de conexión: Los cambios se guardaron localmente y se sincronizarán al recuperar red.");
    onClose();
  } finally {
    setIsLoading(false);
  }
};

// =============================================================================
// FUNCIÓN AUXILIAR: Sincronizar cambios pendientes cuando vuelva la conexión
// =============================================================================
const syncPendingChanges = async () => {
  const pendingChanges = JSON.parse(localStorage.getItem('pending_user_updates') || '[]');
  if (pendingChanges.length === 0) return;

  const failedChanges = [];
  
  for (const change of pendingChanges) {
    try {
      await api.post('/usuarios/guardar', change);
      console.log(`[SYNC] Usuario sincronizado: ${change.nombre || change.email}`);
    } catch (error) {
      failedChanges.push(change);
      console.error(`[SYNC] Falló sincronización para: ${change.nombre || change.email}`);
    }
  }

  // Actualizar localStorage solo con los que fallaron
  localStorage.setItem('pending_user_updates', JSON.stringify(failedChanges));
  
  if (failedChanges.length === 0) {
    console.log('[SYNC] Todos los cambios pendientes fueron sincronizados');
  }
};
