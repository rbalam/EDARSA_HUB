// /app/frontend/src/config/menuFallback.js
// Configuración de menús de respaldo para cuando la API no responde

export const menuFallback = [
  { id: 'crm', label: 'CRM', path: '/crm', isSatelite: false },
  { id: 'comercial', label: 'Comercial', path: '/comercial', isSatelite: false },
  { id: 'admin', label: 'Administración', path: '/admin', isSatelite: false },
  { id: 'comandero', label: 'Comandero', path: '/comandero', isSatelite: true },
  { id: 'super-caja', label: 'Super Caja', path: '/super-caja', isSatelite: true }
];

// Submenús expandidos para cada módulo principal
export const subMenusFallback = {
  crm: [
    { id: 'crm-dashboard', label: 'Dashboard CRM', path: '/crm/dashboard' },
    { id: 'crm-cuentas', label: 'Cuentas', path: '/crm/cuentas' },
    { id: 'crm-leads', label: 'Leads', path: '/crm/leads' },
    { id: 'crm-oportunidades', label: 'Oportunidades', path: '/crm/oportunidades' },
    { id: 'crm-pipeline', label: 'Pipeline', path: '/crm/pipeline' },
    { id: 'crm-actividades', label: 'Actividades', path: '/crm/actividades' },
    { id: 'crm-cotizaciones', label: 'Cotizaciones', path: '/crm/cotizaciones' },
    { id: 'crm-pedidos', label: 'Pedidos', path: '/crm/pedidos' },
    { id: 'crm-operaciones', label: 'Operaciones', path: '/crm/operaciones' },
    { id: 'crm-implementaciones', label: 'Implementaciones', path: '/crm/implementaciones' },
    { id: 'crm-postventa', label: 'Postventa', path: '/crm/postventa' },
    { id: 'crm-kpis', label: 'KPIs IA', path: '/crm/kpis' }
  ],
  comercial: [
    { id: 'comercial-dashboard', label: 'Dashboard Comercial', path: '/comercial' },
    { id: 'comercial-clientes', label: 'Clientes', path: '/comercial/clientes' },
    { id: 'comercial-costos', label: 'Costos y Márgenes', path: '/comercial/costos-margenes' },
    { id: 'comercial-pricing', label: 'Pricing IA', path: '/comercial/pricing-ia' }
  ],
  admin: [
    { id: 'admin-sync-monitor', label: 'Monitor de Sincronización', path: '/admin/sync-monitor' },
    { id: 'admin-dba', label: 'Credenciales DBA', path: '/admin/dba-credential' },
    { id: 'admin-config', label: 'Configuración Operativa', path: '/admin/configuracion-operativa' },
    { id: 'admin-calendario-corporativo', label: 'Días Especiales Comerciales', path: '/admin/calendario-corporativo' }
  ]
};

export default menuFallback;
