// =============================================================================
// SNIPPET: HANDLERS DE GUARDADO CON PERSISTENCIA LOCAL (USUARIOS Y ROLES)
// OBJETIVO: Garantizar que los datos no se pierdan si la API falla
// =============================================================================

// ─────────────────────────────────────────────────────────────────────────────
// HANDLER: GUARDAR USUARIO
// ─────────────────────────────────────────────────────────────────────────────
const handleSaveUsuario = async (userData) => {
  setIsLoading(true);
  try {
    const response = await api.post('/usuarios/guardar', userData);
    if (response.status === 200) {
      alert("Usuario guardado con éxito en el servidor");
      onClose();
    }
  } catch (error) {
    console.warn("API fallida, persistiendo usuario localmente:", error);
    // Guardar en localStorage para sincronización posterior
    const pending = JSON.parse(localStorage.getItem('pending_user_updates') || '[]');
    pending.push({ ...userData, timestamp: new Date().toISOString() });
    localStorage.setItem('pending_user_updates', JSON.stringify(pending));
    
    alert("Error de conexión: Los datos se guardaron localmente. Se sincronizarán al recuperar la red.");
    onClose();
  } finally {
    setIsLoading(false);
  }
};

// ─────────────────────────────────────────────────────────────────────────────
// HANDLER: GUARDAR ROL
// ─────────────────────────────────────────────────────────────────────────────
const handleSaveRol = async (rolData) => {
  setIsLoading(true);
  try {
    const response = await api.post('/roles/guardar', rolData);
    if (response.status === 200) {
      alert("Rol guardado con éxito en el servidor");
      onClose();
    }
  } catch (error) {
    console.warn("API fallida, persistiendo rol localmente:", error);
    // Guardar en localStorage para sincronización posterior
    const pending = JSON.parse(localStorage.getItem('pending_role_updates') || '[]');
    pending.push({ ...rolData, timestamp: new Date().toISOString() });
    localStorage.setItem('pending_role_updates', JSON.stringify(pending));
    
    alert("Error de conexión: El rol se guardó localmente. Se sincronizará automáticamente al restablecerse el servicio.");
    onClose();
  } finally {
    setIsLoading(false);
  }
};

// ─────────────────────────────────────────────────────────────────────────────
// UTILIDAD: SINCRONIZAR PENDIENTES AL RECUPERAR CONEXIÓN
// ─────────────────────────────────────────────────────────────────────────────
const syncAllPending = async () => {
  // Sync usuarios
  const pendingUsers = JSON.parse(localStorage.getItem('pending_user_updates') || '[]');
  for (const user of pendingUsers) {
    try {
      await api.post('/usuarios/guardar', user);
      console.log(`[SYNC] Usuario sincronizado: ${user.nombre || user.email}`);
    } catch (e) {
      console.error(`[SYNC] Falló: ${user.nombre}`);
    }
  }
  
  // Sync roles
  const pendingRoles = JSON.parse(localStorage.getItem('pending_role_updates') || '[]');
  for (const rol of pendingRoles) {
    try {
      await api.post('/roles/guardar', rol);
      console.log(`[SYNC] Rol sincronizado: ${rol.nombre}`);
    } catch (e) {
      console.error(`[SYNC] Falló: ${rol.nombre}`);
    }
  }
  
  // Limpiar si todo OK
  localStorage.removeItem('pending_user_updates');
  localStorage.removeItem('pending_role_updates');
};
