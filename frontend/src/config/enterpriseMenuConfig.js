/**
 * EDARSAHUB ENTERPRISE MENU CONFIG
 *
 * MÁXIMAS OBLIGATORIAS:
 * 1. Ningún módulo/tablero nuevo debe agregarse como menú suelto de primer nivel.
 * 2. Todo nuevo módulo debe pertenecer a un grupo Enterprise.
 * 3. Todo nuevo tablero debe vivir dentro de Inteligencia, Operación, Finanzas,
 *    Administración/Sistema o Satélites, según corresponda.
 * 4. No duplicar rutas.
 * 5. No hardcodear permisos en componentes visuales.
 * 6. No cambiar endpoints desde el menú.
 * 7. No crear conexiones live desde tableros.
 * 8. Todo tablero debe consumir EDARSAHUB SQL como fuente de verdad.
 * 9. MongoDB no debe ser fuente de navegación ni permisos.
 * 10. La navegación debe ser estética, corta, buscable y agrupada.
 * 11. CANÓNICO/CENTRALIZADO OBLIGATORIO: cuando un elemento (filtro, dato, lógica,
 *     componente, endpoint) lo usen MÁS DE DOS menús/pantallas, DEBE ser canónico /
 *     centralizado (una sola fuente de verdad reutilizable). Prohibido duplicar.
 */

export const enterpriseMenuGroups = [
  {
    id: "operacion",
    label: "Operación",
    icon: "Activity",
    color: "#F59E0B",
    description: "Ventas, compras, inventarios y operación diaria",
    children: [
      {
        id: "comercial",
        label: "Comercial / Ventas",
        path: "/comercial",
        icon: "ShoppingCart",
        section: "Ventas",
        keywords: ["ventas", "comercial", "margenes", "costos", "precios", "tickets"]
      },
      {
        id: "costos-margenes",
        label: "Costos y Márgenes",
        path: "/comercial/costos-margenes",
        icon: "Calculator",
        section: "Costos / Precios",
        keywords: ["costos", "margenes", "rentabilidad", "benchmark", "tasas", "precios"]
      },
      {
        id: "pricing-ia",
        label: "Pricing IA",
        path: "/comercial/pricing-ia",
        icon: "Percent",
        section: "Costos / Precios",
        keywords: ["pricing", "precios", "ia", "benchmark", "competidores", "tasas", "margenes"]
      },
      {
        id: "compras",
        label: "Compras",
        path: "/compras",
        icon: "Package",
        section: "Compras",
        keywords: ["compras", "ordenes", "pedidos", "proveedores"]
      },
      {
        id: "inventarios",
        label: "Inventarios / Operaciones",
        path: "/reportes",
        icon: "Boxes",
        section: "Inventarios",
        keywords: ["inventarios", "almacen", "conteos", "operaciones", "diferencias", "reportes", "metricas", "analisis", "informes"]
      },
      {
        id: "tablajeria",
        label: "Tablajería / Producción",
        path: "/tablajeria",
        icon: "Grid3X3",
        section: "Producción",
        keywords: ["produccion", "tablajeria", "recetas", "transformacion"]
      }
    ]
  },

  {
    id: "finanzas-group",
    label: "Finanzas",
    icon: "DollarSign",
    color: "#10B981",
    description: "Dinero, bancos, contabilidad, comisiones y cobros",
    children: [
      {
        id: "finanzas-dashboard",
        label: "Finanzas",
        path: "/finanzas",
        icon: "DollarSign",
        section: "Finanzas",
        keywords: ["finanzas", "flujo", "egresos", "ingresos"]
      },
      {
        id: "host-to-host",
        label: "Host to Host Bancario",
        path: "/host-to-host",
        comingSoon: true,
        icon: "Building2",
        section: "Bancos",
        keywords: ["bancos", "host", "pagos", "bancario"]
      },
      {
        id: "contabilidad",
        label: "Contabilidad",
        path: "/contabilidad",
        comingSoon: true,
        icon: "Calculator",
        section: "Contabilidad",
        keywords: ["contabilidad", "polizas", "cuentas"]
      },
      {
        id: "comisiones",
        label: "Comisiones",
        path: "/comisiones",
        comingSoon: true,
        icon: "Percent",
        section: "Comisiones",
        keywords: ["comisiones", "tarjetas", "netpay"]
      }
    ]
  },

  {
    id: "personas",
    label: "Personas",
    icon: "Users",
    color: "#8B5CF6",
    description: "Colaboradores, clientes, socios y relaciones",
    children: [
      {
        id: "rh",
        label: "Recursos Humanos",
        path: "/recursos-humanos",
        icon: "Users",
        section: "Capital Humano",
        keywords: ["rh", "nomina", "personal", "empleados"]
      },
      {
        id: "crm",
        label: "CRM / Relaciones",
        path: "/crm",
        icon: "Contact",
        section: "Relaciones",
        keywords: ["crm", "clientes", "relaciones"]
      }
    ]
  },

  {
    id: "inteligencia",
    label: "Inteligencia",
    icon: "BarChart3",
    color: "#3B82F6",
    description: "Dirección, BI, IA, auditoría y tableros",
    children: [
      {
        id: "direccion",
        label: "Dirección / Tablero Ejecutivo",
        path: "/tablero-ejecutivo",
        icon: "LayoutDashboard",
        section: "Dirección",
        keywords: ["direccion", "dashboard", "ejecutivo", "tablero", "kpi"]
      },
      {
        id: "reportes-bi",
        label: "Reportes BI / Analítica",
        path: "/reportes-bi",
        icon: "PieChart",
        section: "Analítica",
        keywords: ["bi", "reportes", "analitica", "power bi"]
      },
      {
        id: "inteligencia-artificial",
        label: "Inteligencia Artificial",
        path: "/inteligencia-artificial",
        comingSoon: true,
        icon: "Brain",
        section: "IA",
        keywords: ["ia", "inteligencia artificial", "agentes"]
      },
      {
        id: "calidad-auditoria",
        label: "Calidad / Auditoría",
        path: "/auditoria",
        comingSoon: true,
        icon: "ShieldCheck",
        section: "Auditoría",
        keywords: ["auditoria", "calidad", "control", "revision"]
      }
    ]
  },

  {
    id: "gestion",
    label: "Gestión",
    icon: "ClipboardList",
    color: "#EC4899",
    description: "Proyectos, tareas, incidencias y marketing",
    children: [
      {
        id: "proyectos",
        label: "Proyectos / Tareas",
        path: "/proyectos",
        comingSoon: true,
        icon: "ClipboardList",
        section: "Proyectos",
        keywords: ["proyectos", "tareas", "workflow"]
      },
      {
        id: "marketing",
        label: "Marketing",
        path: "/marketing",
        comingSoon: true,
        icon: "Megaphone",
        section: "Marketing",
        keywords: ["marketing", "campañas"]
      }
    ]
  },

  {
    id: "corporativo",
    label: "Corporativo",
    icon: "Building",
    color: "#64748B",
    description: "Estructura empresarial, activos y catálogos",
    children: [
      {
        id: "activos-fijos",
        label: "Activos Fijos",
        path: "/activos-fijos",
        comingSoon: true,
        icon: "Grid3X3",
        section: "Activos",
        keywords: ["activos", "fijos", "mantenimiento"]
      },
      {
        id: "catalogos-maestros",
        label: "Catálogos Maestros",
        path: "/catalogos",
        icon: "Database",
        section: "Catálogos",
        keywords: ["catalogos", "maestros", "productos", "proveedores"]
      }
    ]
  },

  {
    id: "integraciones",
    label: "Integraciones",
    icon: "Plug",
    color: "#06B6D4",
    description: "Conectores, APIs, sincronizaciones y sistemas externos",
    children: [
      {
        id: "integraciones-conectores",
        label: "Integraciones / Conectores",
        path: "/integraciones",
        comingSoon: true,
        icon: "Plug",
        section: "Conectores",
        keywords: ["integraciones", "conectores", "apis", "sincronizaciones"]
      }
    ]
  },

  {
    id: "administracion",
    label: "Administración / Sistema",
    icon: "Settings",
    color: "#EF4444",
    description: "Control, infraestructura, seguridad y configuración",
    adminOnly: true,
    children: [
      {
        id: "centro-control",
        label: "Centro de Control",
        path: "/centro-control",
        icon: "ShieldCheck",
        section: "Control Operativo",
        keywords: ["centro", "control", "monitoreo"]
      },
      {
        id: "mis-tareas",
        label: "Mis Tareas",
        path: "/mis-tareas",
        icon: "ClipboardList",
        section: "Control Operativo",
        keywords: ["tareas", "pendientes"]
      },
      {
        id: "alertas",
        label: "Alertas",
        path: "/alertas",
        icon: "Bell",
        section: "Control Operativo",
        keywords: ["alertas", "notificaciones"]
      },
      {
        id: "servidores",
        label: "Servidores",
        path: "/servidores",
        icon: "Server",
        section: "Infraestructura",
        keywords: ["servidores", "conexiones"]
      },
      {
        id: "explorador-bd",
        label: "Explorador BD",
        path: "/explorador-bd",
        icon: "Table",
        section: "Infraestructura",
        keywords: ["explorador", "base de datos", "bd"]
      },
      {
        id: "catalogo-sql",
        label: "Catálogo SQL",
        path: "/catalogo-consultas",
        icon: "Database",
        section: "Infraestructura",
        keywords: ["catalogo", "sql", "tablas"]
      },
      {
        id: "programacion",
        label: "Programación",
        path: "/scheduler",
        icon: "Clock",
        section: "Automatización",
        keywords: ["programacion", "scheduler", "jobs", "sincronizacion", "re-sincronizar", "analisis inventario"]
      },
      {
        id: "sync-monitor",
        label: "Monitor de Sincronización",
        path: "/admin/sync-monitor",
        icon: "RefreshCw",
        section: "Automatización",
        keywords: ["sincronizacion", "sync", "catalogos", "monitor", "estado", "servidores"]
      },
      {
        id: "automatizaciones",
        label: "Automatizaciones",
        path: "/automatizaciones",
        icon: "CalendarCheck",
        section: "Automatización",
        keywords: ["automatizaciones", "procesos"]
      },
      {
        id: "asignaciones",
        label: "Asignaciones",
        path: "/configuracion/asignaciones",
        icon: "UserCog",
        section: "Automatización",
        keywords: ["asignaciones", "responsables"]
      },
      {
        id: "usuarios",
        label: "Usuarios",
        path: "/usuarios",
        icon: "Users",
        section: "Seguridad",
        keywords: ["usuarios", "seguridad"]
      },
      {
        id: "config-operativa",
        label: "Config. Operativa",
        path: "/admin/configuracion-operativa",
        icon: "Settings",
        section: "Configuración",
        keywords: ["configuracion", "operativa", "parametros"]
      },
      {
        id: "calendario-corporativo",
        label: "Días Especiales Comerciales",
        path: "/admin/calendario-corporativo",
        icon: "CalendarDays",
        section: "Configuración",
        keywords: [
          "calendario",
          "eventos",
          "fechas importantes",
          "filtros",
          "empresa",
          "unidad"
        ]
      }
    ]
  },

  {
    id: "satelites",
    label: "Satélites",
    icon: "Grid3X3",
    color: "#F97316",
    description: "Aplicaciones operativas satélite conectadas a EDARSAHUB",
    satelliteGroup: true,
    children: [
      {
        id: "cava-socios",
        label: "Cavas - Dashboard",
        path: "/cava-socios",
        icon: "Wine",
        section: "Cavas",
        satellite: true,
        keywords: ["cava", "cavas", "socios", "vino", "dashboard"]
      },
      {
        id: "cava-socios-directorio",
        label: "Cavas - Socios",
        path: "/cava-socios/socios",
        icon: "Users",
        section: "Cavas",
        satellite: true,
        keywords: ["cava", "socios", "membresias", "clientes"]
      },
      {
        id: "cava-socios-inventario",
        label: "Cavas - Inventario & Kardex",
        path: "/cava-socios/inventario",
        icon: "Package",
        section: "Cavas",
        satellite: true,
        keywords: ["cava", "inventario", "kardex", "auditoria", "custodia", "botellas"]
      },
      {
        id: "cava-socios-consumos",
        label: "Cavas - Consumos",
        path: "/cava-socios/consumos",
        icon: "TrendingDown",
        section: "Cavas",
        satellite: true,
        keywords: ["cava", "consumos", "descorches", "movimientos"]
      },
      {
        id: "comandero-restaurantero",
        label: "Comandero Restaurantero",
        path: "/comandero",
        icon: "Utensils",
        section: "Restaurantes",
        satellite: true,
        keywords: ["comandero", "restaurante", "mesas", "comandas"]
      },
      {
        id: "super-caja",
        label: "Super Caja",
        path: "/super-caja",
        icon: "Store",
        section: "POS",
        satellite: true,
        keywords: ["pos", "punto de venta", "caja", "super caja"]
      },
      {
        id: "portal-inteligencia-comercial-satelite",
        label: "Portal Inteligencia Comercial",
        path: "/inteligencia-comercial",
        icon: "BarChart3",
        section: "Analítica Comercial",
        satellite: true,
        keywords: ["portal", "inteligencia comercial", "pic", "ventas", "analitica"]
      },
      {
        id: "coa",
        label: "COA - Operaciones Administrativas",
        path: "/coa",
        icon: "ClipboardList",
        section: "Administracion",
        satellite: true,
        keywords: ["coa", "operaciones administrativas", "facturacion", "nominas", "comisiones", "expedientes"]
      }
    ]
  }
];

export const defaultFavoriteMenuIds = [
  "/comercial",
  "/tablero-ejecutivo",
  "/reportes"
];

export function flattenEnterpriseMenu(groups = enterpriseMenuGroups) {
  return groups.flatMap(group =>
    group.children.map(item => ({
      ...item,
      groupId: group.id,
      groupLabel: group.label,
      groupColor: group.color,
      groupDescription: group.description
    }))
  );
}

export function filterEnterpriseMenuByRole(groups, user) {
  const role = String(user?.role || user?.rol || "").toUpperCase();
  const isSuperAdmin = role === "SUPERADMIN" || role === "SUPER_ADMIN" || role === "SUPERADMINISTRADOR";
  const isAdmin = role === "ADMIN" || role === "ADMINISTRADOR";

  return groups
    .filter(group => {
      if (group.adminOnly && !(isSuperAdmin || isAdmin)) return false;
      return true;
    })
    .map(group => ({
      ...group,
      children: group.children
    }));
}
