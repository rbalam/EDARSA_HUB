// =============================================================================
// SNIPPET: MENU FALLBACK CON MÓDULOS SATÉLITES INYECTADOS
// OBJETIVO: Garantizar visibilidad de menús incluso sin conexión al servidor
// =============================================================================

// MODIFICACIÓN EXIGIDA: Agregar los satélites al arreglo por defecto
export const menuFallback = [
  {
    title: 'CRM',
    path: '/crm',
    icon: 'crm-icon',
    isNative: true
  },
  {
    title: 'Comercial',
    path: '/comercial',
    icon: 'chart-icon',
    isNative: true
  },
  // ─── INYECCIÓN DE TUS NUEVOS MÓDULOS SATÉLITES ───
  {
    title: 'Comedero',
    path: '/comedero',
    icon: 'utensils',
    isSatelite: true, // Registrado como satélite independiente
    roles: ['SuperAdministrador']
  },
  {
    title: 'Super Caja',
    path: '/super-caja',
    icon: 'cash-register',
    isSatelite: true, // Registrado como satélite independiente
    roles: ['SuperAdministrador']
  }
];
