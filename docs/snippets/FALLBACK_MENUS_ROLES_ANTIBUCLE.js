// =============================================================================
// SNIPPETS: FALLBACK DE MENÚS Y ROLES - ANTI-BUCLE INFINITO
// OBJETIVO: Garantizar que la UI nunca se quede "pensando" si falla la API
// =============================================================================

// ─────────────────────────────────────────────────────────────────────────────
// /app/src/config/menuFallback.js
// ─────────────────────────────────────────────────────────────────────────────
export const menuFallback = [
  { id: 'crm', label: 'CRM', path: '/crm', icon: 'users', isSatelite: false },
  { id: 'comercial', label: 'Comercial', path: '/comercial', icon: 'chart-bar', isSatelite: false },
  { id: 'comedero', label: 'Comedero', path: '/comedero', icon: 'utensils', isSatelite: true },
  { id: 'super-caja', label: 'Super Caja', path: '/super-caja', icon: 'cash-register', isSatelite: true }
];

// ─────────────────────────────────────────────────────────────────────────────
// /app/src/components/BarraLateral.jsx
// ... dentro del useEffect o función de carga de menús
// ─────────────────────────────────────────────────────────────────────────────
try {
  const data = await api.get('/api/sistema/menus/usuario');
  setMenus(data);
} catch (error) {
  console.warn("Fallo en API, cargando fallback...", error);
  // FUERZA LA LECTURA DEL FALLBACK PARA QUE NO SE QUEDE PENSANDO
  setMenus(menuFallback); 
  setIsLoading(false); // Rompe el bucle de la ruedita
}

// ─────────────────────────────────────────────────────────────────────────────
// /app/src/components/RolesList.jsx
// ─────────────────────────────────────────────────────────────────────────────
try {
  const roles = await api.get('/roles');
  setRoles(roles);
} catch (error) {
  // Si falla, intenta recuperar desde localStorage o muestra un aviso amable
  const localRoles = localStorage.getItem('cached_roles');
  if (localRoles) {
    setRoles(JSON.parse(localRoles));
  } else {
    // Si no hay nada, muestra un mensaje útil en lugar de dejar la pantalla vacía
    console.error("No se pudieron cargar los roles");
  }
  setIsLoading(false);
}
