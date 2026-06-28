import { Outlet, useLocation, Link, useNavigate } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import logger from '@/services/logger';
import { Button } from '@/components/ui/button';
import EnterpriseSidebarMenu from '@/components/navigation/EnterpriseSidebarMenu';
import { 
  LayoutDashboard, 
  Server, 
  Package, 
  Bell, 
  Users, 
  LogOut,
  Menu,
  X,
  ShoppingCart,
  TrendingUp,
  Database,
  TableProperties,
  PieChart,
  Warehouse,
  DollarSign,
  Factory,
  UserCircle,
  BarChart3,
  ClipboardList,
  Upload,
  ChevronDown,
  ChevronRight,
  BookOpen,
  Building2,
  Clock,
  CalendarCheck,
  Shield,
  Settings,
  UserCog,
  Key,
  Target,
  Kanban,
  UserPlus,
  Briefcase,
  Beef,
  Layers,
  FileText,
  FilePlus,
  Activity,
  Truck,
  Receipt,
  FileCheck,
  Wine,
  Smartphone,
  Link as LinkIcon,
  ChefHat,
  CreditCard,
  LayoutGrid,
  Calculator,
  ShoppingBag,
  Users2
} from 'lucide-react';
import { useState, useEffect, useMemo } from 'react';
import api from '@/lib/api';
import { useAccessContext } from '@/hooks/useAccessContext';
import { useMenusByContext } from '@/hooks/useMenusByContext';

// Mapeo de nombres de iconos a componentes Lucide
const ICON_MAP = {
  'PieChart': PieChart,
  'TrendingUp': TrendingUp,
  'Target': Target,
  'Building2': Building2,
  'FileCheck': FileCheck,
  'FileText': FileText,
  'Package': Package,
  'Truck': Truck,
  'Calculator': Calculator,
  'ShoppingCart': ShoppingCart,
  'Warehouse': Warehouse,
  'Boxes': Package,
  'Beef': Beef,
  'Layers': Layers,
  'FilePlus': FilePlus,
  'Wine': Wine,
  'Users': Users,
  'DollarSign': DollarSign,
  'UserCircle': UserCircle,
  'Upload': Upload,
  'BarChart3': BarChart3,
  'BookOpen': BookOpen,
  'Shield': Shield,
  'Server': Server,
  'Clock': Clock,
  'CalendarCheck': CalendarCheck,
  'UserCog': UserCog,
  'Database': Database,
  'TableProperties': TableProperties,
  'Bell': Bell,
  'Settings': Settings,
  'ClipboardList': ClipboardList,
  'ShoppingBag': ShoppingBag,
  'CreditCard': CreditCard,
  'LayoutGrid': LayoutGrid,
  'Receipt': Receipt,
  'Smartphone': Smartphone,
  'Link': LinkIcon,
  'ChefHat': ChefHat,
  'Users2': Users2,
  'UserPlus': UserPlus,
  'Briefcase': Briefcase,
  'Kanban': Kanban,
  'Factory': Factory,
  'Key': Key,
  'Activity': Activity,
};

// P5-10B: Desactivar fallback hardcodeado - SQL canónico es la única fuente
const ENABLE_HARDCODED_MENU_FALLBACK = false;

// ENTERPRISE MENU: Flag para usar el nuevo menú Enterprise (agrupado y buscable)
// Cuando esté en true, usa EnterpriseSidebarMenu en lugar del sidebar actual
const USE_ENTERPRISE_MENU = true; // Enterprise visual activo con fuente SQL canónica

const Layout = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(() => {
    try {
      return localStorage.getItem('edarsahub_sidebar_collapsed') === 'true';
    } catch {
      return false;
    }
  });
  const [expandedMenus, setExpandedMenus] = useState({});
  const [menuPermissions, setMenuPermissions] = useState({});
  const [permissionsLoaded, setPermissionsLoaded] = useState(false);
  
  // NUEVO: Estado para menús desde SQL
  const [sqlMenus, setSqlMenus] = useState(null);
  const [sqlMenusLoaded, setSqlMenusLoaded] = useState(false);
  const [useSqlMenus, setUseSqlMenus] = useState(false);

  // Contexto activo (unidad de negocio) y menús filtrados por esa unidad.
  // La fuente de datos del menú es el MISMO endpoint canónico; solo cambia
  // que ahora respeta la unidad activa. NO se rompe el menú Enterprise.
  const { context: accessContext } = useAccessContext();
  const unidadActiva = accessContext?.unidad_activa || null;
  const { menus: ctxMenus, error: ctxMenusError } = useMenusByContext(unidadActiva);

  // NUEVO: Sincronizar menús SQL por contexto -> estado del Layout (con fallback)
  useEffect(() => {
    if (!user) return;

    if (Array.isArray(ctxMenus) && ctxMenus.length > 0) {
      setSqlMenus(ctxMenus);
      setUseSqlMenus(true);
      logger.info('Menús SQL (contexto) cargados:', ctxMenus.length, 'módulos | unidad:', unidadActiva);
    } else if (ctxMenusError) {
      // Regla #4: fallback visual solo si el endpoint falla.
      logger.warn('Menús SQL no disponibles, usando fallback hardcoded:', ctxMenusError.message);
      setUseSqlMenus(false);
    }
    setSqlMenusLoaded(true);
  }, [user, ctxMenus, ctxMenusError, unidadActiva]);

  // Cargar permisos de menú desde el backend (RBAC centralizado)
  useEffect(() => {
    const loadMenuPermissions = async () => {
      try {
        const response = await api.get('/auth/me/menu-permissions');
        const data = response.data || {};
        setMenuPermissions(data.permisos_modulos || {});
        setPermissionsLoaded(true);
      } catch (error) {
        logger.error('Error loading menu permissions:', error);
        // Fallback: dar acceso básico basado en rol legacy
        const role = user?.role || '';
        const isAdmin = role.toLowerCase().includes('admin') || role.toLowerCase().includes('super');
        setMenuPermissions({
          mis_tareas: true,
          tablero_ejecutivo: isAdmin || role === 'Supervisor',
          comercial: true,
          crm: true,
          compras: true,
          operaciones: true,
          finanzas: isAdmin || role === 'Supervisor',
          produccion: isAdmin || role === 'Supervisor',
          recursos_humanos: isAdmin || role === 'Supervisor',
          reportes_bi: isAdmin || role === 'Supervisor',
          catalogos: isAdmin || role === 'Supervisor',
          centro_control: isAdmin || role === 'Supervisor' || role === 'Director',
          servidores: isAdmin,
          programacion: isAdmin || role === 'Supervisor',
          automatizaciones: isAdmin || role === 'Supervisor',
          asignaciones: isAdmin,
          catalogo_sql: isAdmin || role === 'Supervisor',
          explorador_bd: isAdmin,
          alertas: isAdmin || role === 'Supervisor',
          usuarios: isAdmin,
          cava_socios: true,
          pos_generico: isAdmin || role === 'Supervisor',
          comandero: isAdmin || role === 'Supervisor',
          edarsa_go: isAdmin || role === 'Supervisor',
          chef_ia: isAdmin || role === 'Supervisor',
          portal_proveedores: isAdmin,
          portal_comisionistas: isAdmin,
          portal_clientes: isAdmin,
        });
        setPermissionsLoaded(true);
      }
    };
    
    if (user) {
      loadMenuPermissions();
    }
  }, [user]);

  // Función para verificar si el usuario tiene acceso a un módulo
  // P5-10B: Backend SQL canónico decide visibilidad
  const hasAccess = (item) => {
    // Si el ítem viene del backend SQL con visible=true, confiar en eso
    if (item && Object.prototype.hasOwnProperty.call(item, 'visible')) {
      return item.visible === true;
    }
    
    // Si usamos menús SQL, todos los ítems retornados ya están autorizados
    if (useSqlMenus) {
      return true;
    }
    
    // Fallback desactivado por máxima de oro
    if (!ENABLE_HARDCODED_MENU_FALLBACK) {
      return false;
    }
    
    return false;
  };

  // Toggle submenu expansion con anti-atasco y re-hidratación forzada
  const [submenuTimestamps, setSubmenuTimestamps] = useState({});
  
  const toggleSubmenu = (menuName, e) => {
    // 1. Evitar propagación absoluta para no activar elementos padres
    if (e) {
      e.stopPropagation();
      e.preventDefault();
    }
    
    // 2. Verificar si el menú está "atascado" (abierto por más de 5 segundos)
    const now = Date.now();
    const lastToggle = submenuTimestamps[menuName] || 0;
    const isStuck = expandedMenus[menuName] && (now - lastToggle > 5000);
    
    // 3. Forzar actualización del estado con re-hidratación visual
    setExpandedMenus(prev => {
      const currentState = prev[menuName];
      // Si está atascado, forzar cierre
      if (isStuck) {
        console.log(`[UI] Menú ${menuName} atascado - forzando cierre`);
        return { ...prev, [menuName]: false };
      }
      // Toggle normal
      const newState = !currentState;
      console.log(`[UI] Toggle ${menuName}: ${currentState} → ${newState}`);
      return { ...prev, [menuName]: newState };
    });
    
    // 4. Registrar timestamp del toggle
    setSubmenuTimestamps(prev => ({ ...prev, [menuName]: now }));
  };

  // ============================================
  // MÓDULOS OPERATIVOS (Estructura ERP)
  // ============================================
  
  const modulos = [
    { 
      name: 'Mis Tareas', 
      href: '/mis-tareas', 
      icon: ClipboardList, 
      roles: ['Usuario', 'Supervisor', 'Administrador'],
    },
    { 
      name: 'Tablero Ejecutivo', 
      href: '/tablero-ejecutivo', 
      icon: PieChart, 
      roles: ['Supervisor', 'Administrador'],
    },
    { 
      name: 'Comercial', 
      href: '/comercial', 
      icon: TrendingUp, 
      roles: ['Usuario', 'Supervisor', 'Administrador'],
      submenus: [
        {
          name: 'Dashboard Comercial',
          href: '/comercial',
          icon: TrendingUp,
          roles: ['Usuario', 'Supervisor', 'Administrador']
        },
        {
          name: 'Clientes',
          href: '/comercial/clientes',
          icon: Users,
          roles: ['Usuario', 'Supervisor', 'Administrador']
        },
        {
          name: 'Costos y Márgenes',
          href: '/comercial/costos-margenes',
          icon: Calculator,
          roles: ['Usuario', 'Supervisor', 'Administrador']
        },
        {
          name: 'Pricing IA',
          href: '/comercial/pricing-ia',
          icon: Target,
          roles: ['Usuario', 'Supervisor', 'Administrador']
        }
      ]
    },
    { 
      name: 'CRM', 
      href: '/crm', 
      icon: Target, 
      roles: ['Usuario', 'Supervisor', 'Administrador'],
      submenus: [
        {
          name: 'Dashboard CRM',
          href: '/crm/dashboard',
          icon: PieChart,
          roles: ['Usuario', 'Supervisor', 'Administrador']
        },
        {
          name: 'Cuentas',
          href: '/crm/cuentas',
          icon: Building2,
          roles: ['Usuario', 'Supervisor', 'Administrador']
        },
        {
          name: 'Solicitudes Alta',
          href: '/crm/solicitudes-alta',
          icon: FileCheck,
          roles: ['Usuario', 'Supervisor', 'Administrador']
        },
        {
          name: 'Leads',
          href: '/crm/leads',
          icon: UserPlus,
          roles: ['Usuario', 'Supervisor', 'Administrador']
        },
        {
          name: 'Oportunidades',
          href: '/crm/oportunidades',
          icon: Briefcase,
          roles: ['Usuario', 'Supervisor', 'Administrador']
        },
        {
          name: 'Pipeline',
          href: '/crm/pipeline',
          icon: Kanban,
          roles: ['Usuario', 'Supervisor', 'Administrador']
        },
        {
          name: 'Actividades',
          href: '/crm/actividades',
          icon: Activity,
          roles: ['Usuario', 'Supervisor', 'Administrador']
        },
        {
          name: 'Cotizaciones',
          href: '/crm/cotizaciones',
          icon: Receipt,
          roles: ['Usuario', 'Supervisor', 'Administrador']
        },
        {
          name: 'Pedidos',
          href: '/crm/pedidos',
          icon: Package,
          roles: ['Usuario', 'Supervisor', 'Administrador']
        },
        {
          name: 'Remisiones',
          href: '/crm/remisiones',
          icon: Truck,
          roles: ['Usuario', 'Supervisor', 'Administrador']
        },
        {
          name: 'Operaciones',
          href: '/crm/operaciones',
          icon: Factory,
          roles: ['Usuario', 'Supervisor', 'Administrador']
        },
        {
          name: 'Implementaciones',
          href: '/crm/implementaciones',
          icon: Settings,
          roles: ['Usuario', 'Supervisor', 'Administrador']
        },
        {
          name: 'Postventa',
          href: '/crm/postventa',
          icon: Shield,
          roles: ['Usuario', 'Supervisor', 'Administrador']
        },
        {
          name: 'KPIs IA',
          href: '/crm/kpis',
          icon: BarChart3,
          roles: ['Supervisor', 'Administrador']
        }
      ]
    },
    { 
      name: 'Compras', 
      href: '/compras', 
      icon: ShoppingCart, 
      roles: ['Usuario', 'Supervisor', 'Administrador'],
    },
    { 
      name: 'Operaciones', 
      href: '/reportes', 
      icon: Warehouse, 
      roles: ['Usuario', 'Supervisor', 'Administrador'],
    },
    { 
      name: 'Finanzas', 
      href: '/finanzas', 
      icon: DollarSign, 
      roles: ['Supervisor', 'Administrador'],
      badge: 'Próx.'
    },
    { 
      name: 'Producción', 
      href: '/produccion', 
      icon: Factory, 
      roles: ['Usuario', 'Supervisor', 'Administrador'],
      submenus: [
        {
          name: 'Tablajería',
          href: '/tablajeria/dashboard',
          icon: Beef,
          roles: ['Usuario', 'Supervisor', 'Administrador']
        },
        {
          name: 'Órdenes',
          href: '/tablajeria/ordenes',
          icon: FileText,
          roles: ['Usuario', 'Supervisor', 'Administrador']
        },
        {
          name: 'Captura Directa',
          href: '/tablajeria/captura-directa',
          icon: FilePlus,
          roles: ['Operador', 'Supervisor', 'Administrador']
        },
        {
          name: 'Plantillas',
          href: '/tablajeria/plantillas',
          icon: Layers,
          roles: ['Usuario', 'Supervisor', 'Administrador']
        }
      ]
    },
    { 
      name: 'Cava de Socios', 
      href: '/cava-socios', 
      icon: Wine, 
      roles: ['Usuario', 'Supervisor', 'Administrador'],
      submenus: [
        {
          name: 'Dashboard',
          href: '/cava-socios',
          icon: PieChart,
          roles: ['Usuario', 'Supervisor', 'Administrador']
        },
        {
          name: 'Socios',
          href: '/cava-socios/socios',
          icon: Users,
          roles: ['Usuario', 'Supervisor', 'Administrador']
        }
      ]
    },
    { 
      name: 'Recursos Humanos', 
      href: '/recursos-humanos', 
      icon: UserCircle, 
      roles: ['Supervisor', 'Administrador'],
      badge: 'Próx.',
      submenus: [
        {
          name: 'Importador RH',
          href: '/importador-rh',
          icon: Upload,
          roles: ['Administrador']
        }
      ]
    },
    { 
      name: 'Reportes BI', 
      href: '/reportes-bi', 
      icon: BarChart3, 
      roles: ['Supervisor', 'Administrador'],
      badge: 'Próx.'
    },
    { 
      name: 'Catálogos', 
      href: '/catalogos', 
      icon: BookOpen, 
      roles: ['Supervisor', 'Administrador'],
    },
  ];

  // ============================================
  // SISTEMA (Administración y Configuración)
  // ============================================
  
  const sistema = [
    { name: 'Centro de Control', href: '/centro-control', icon: Shield, roles: ['SuperAdministrador', 'SUPERADMIN', 'Administrador', 'ADMIN', 'Supervisor', 'Director'] },
    { name: 'Servidores', href: '/servidores', icon: Server, roles: ['SuperAdministrador', 'SUPERADMIN', 'Administrador', 'ADMIN'] },
    { name: 'Programación', href: '/scheduler', icon: Clock, roles: ['SuperAdministrador', 'SUPERADMIN', 'Administrador', 'ADMIN', 'Supervisor'] },
    { name: 'Automatizaciones', href: '/automatizaciones', icon: CalendarCheck, roles: ['SuperAdministrador', 'SUPERADMIN', 'Administrador', 'ADMIN', 'Supervisor', 'Gerente', 'Director', 'Auditor'] },
    { name: 'Asignaciones', href: '/configuracion/asignaciones', icon: UserCog, roles: ['SuperAdministrador', 'SUPERADMIN', 'Administrador', 'ADMIN'] },
    { name: 'Catálogo SQL', href: '/catalogo-consultas', icon: Database, roles: ['SuperAdministrador', 'SUPERADMIN', 'Supervisor', 'Administrador', 'ADMIN'] },
    { name: 'Explorador BD', href: '/explorador-bd', icon: TableProperties, roles: ['SuperAdministrador', 'SUPERADMIN', 'Administrador', 'ADMIN'] },
    { name: 'Alertas', href: '/alertas', icon: Bell, roles: ['SuperAdministrador', 'SUPERADMIN', 'Supervisor', 'Administrador', 'ADMIN'] },
    { name: 'Usuarios', href: '/usuarios', icon: Users, roles: ['SuperAdministrador', 'SUPERADMIN', 'Administrador', 'ADMIN'] },
    { name: 'Config. Operativa', href: '/admin/configuracion-operativa', icon: Settings, roles: ['SuperAdministrador', 'SUPERADMIN', 'Administrador', 'ADMIN'] },
    { name: 'DBA Diagnóstico', href: '/admin/dba-credential', icon: Key, roles: ['SuperAdministrador', 'SUPERADMIN'] },
  ];

  const filteredModulos = modulos.filter(item => hasAccess(item));
  const filteredSistema = sistema.filter(item => hasAccess(item));

  // ==================================================
  // MENÚS DINÁMICOS DESDE SQL (P5-10B)
  // ==================================================
  
  // Transformar menús SQL a estructura renderizable
  const transformSqlMenus = useMemo(() => {
    if (!sqlMenus || sqlMenus.length === 0) return null;
    
    const principales = [];
    const satelites = [];
    const portales = [];
    const sistemaItems = [];
    
    sqlMenus.forEach(modulo => {
      const menus = modulo.menus || [];
      const esSatelite = modulo.es_satelite === true;
      const esPortal = modulo.es_portal === true;
      const codigo = modulo.codigo || '';
      
      // Mapear a estructura del componente
      const moduloTransformado = {
        name: modulo.nombre || codigo,
        href: menus[0]?.ruta || '#',
        icon: ICON_MAP[modulo.icono] || LayoutDashboard,
        codigo: codigo,
        visible: modulo.visible !== false,
        submenus: menus.length > 1 ? menus.map(m => ({
          name: m.nombre,
          href: m.ruta,
          icon: ICON_MAP[m.icono] || ChevronRight,
          visible: m.visible !== false
        })) : [],
        // Si solo tiene 1 menú, usar su ruta directamente
        ...(menus.length === 1 && { href: menus[0].ruta })
      };
      
      // P5-10B: Clasificar usando los campos que envía el backend SQL
      if (codigo === 'SISTEMA' || codigo.startsWith('SISTEMA_') || codigo === 'CENTRO_CONTROL') {
        // Extraer ítems de sistema del módulo SISTEMA/Administración
        if (menus.length > 0) {
          menus.forEach(m => {
            sistemaItems.push({
              name: m.nombre,
              href: m.ruta,
              icon: ICON_MAP[m.icono] || Settings,
              visible: m.visible !== false
            });
          });
        }
      } else if (esSatelite) {
        satelites.push(moduloTransformado);
      } else if (esPortal) {
        portales.push(moduloTransformado);
      } else {
        principales.push(moduloTransformado);
      }
    });
    
    return { principales, satelites, portales, sistema: sistemaItems };
  }, [sqlMenus]);
  
  // Determinar qué menús usar
  const menusFinal = useMemo(() => {
    if (useSqlMenus && transformSqlMenus) {
      return {
        modulos: transformSqlMenus.principales,
        satelites: transformSqlMenus.satelites,
        portales: transformSqlMenus.portales,
        sistema: transformSqlMenus.sistema,
        source: 'SQL'
      };
    }
    // Fallback hardcodeado con satélites inyectados
    const satelitesFallback = [
      {
        name: 'Super Caja',
        href: '/super-caja',
        icon: CreditCard,
        codigo: 'SUPER_CAJA_SAT'
      },
      {
        name: 'Comandero',
        href: '/comandero',
        icon: ChefHat,
        codigo: 'COMANDERO_01'
      }
    ];
    
    return {
      modulos: filteredModulos,
      satelites: satelitesFallback,
      portales: [],
      sistema: filteredSistema,
      source: 'FALLBACK'
    };
  }, [useSqlMenus, transformSqlMenus, filteredModulos, filteredSistema]);

  const toggleSidebarCollapsed = () => {
    setSidebarCollapsed(prev => {
      const next = !prev;
      try {
        localStorage.setItem('edarsahub_sidebar_collapsed', String(next));
      } catch {}
      return next;
    });
  };

  const handleLogout = () => {
    try {
      logout?.();
    } finally {
      navigate('/login', { replace: true });
    }
  };

  // Nota: La verificación de autenticación se hace en ProtectedRoute, no aquí
  // Esto evita conflictos con los portales externos

  return (
    <div className="min-h-screen bg-zinc-50" data-testid="layout">
      {/* Mobile sidebar toggle */}
      <div className="lg:hidden fixed top-0 left-0 right-0 z-50 bg-zinc-900 px-4 py-3 flex items-center justify-between">
        <h1 className="text-white font-bold text-lg" style={{ fontFamily: 'Manrope, sans-serif' }}>EDARSA HUB</h1>
        <Button 
          variant="ghost" 
          size="icon"
          onClick={() => setSidebarOpen(!sidebarOpen)}
          className="text-white hover:bg-zinc-800"
          data-testid="mobile-menu-toggle"
        >
          {sidebarOpen ? <X /> : <Menu />}
        </Button>
      </div>

      {/* Sidebar */}
      <aside 
        className={`fixed inset-y-0 left-0 z-40 bg-zinc-900 transform transition-all duration-200 lg:translate-x-0 ${sidebarCollapsed ? 'w-20' : 'w-80'} ${
          sidebarOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
        data-testid="sidebar"
      >
        <div className="flex flex-col h-full">
          <div className={`border-b border-zinc-800 ${sidebarCollapsed ? 'p-3' : 'p-6'}`}>
            <div className="flex items-center justify-between gap-2">
              {!sidebarCollapsed && (
                <div className="min-w-0">
                  <h1 className="text-xl font-extrabold text-white" style={{ fontFamily: 'Manrope, sans-serif' }}>
                    EDARSA HUB
                  </h1>
                  <p className="text-zinc-400 text-sm mt-1 break-words">{user?.name}</p>
                  <p className="text-zinc-500 text-xs break-words">{user?.role}</p>
                </div>
              )}
              <button
                type="button"
                onClick={toggleSidebarCollapsed}
                className="shrink-0 h-9 w-9 rounded-xl text-zinc-400 hover:text-white hover:bg-white/10 transition-all"
                title={sidebarCollapsed ? 'Mostrar menú' : 'Ocultar menú'}
                aria-label={sidebarCollapsed ? 'Mostrar menú' : 'Ocultar menú'}
                data-testid="sidebar-collapse-toggle"
              >
                {sidebarCollapsed ? <Menu size={18} /> : <X size={18} />}
              </button>
            </div>
          </div>

          <nav className="flex-1 p-4 space-y-1 overflow-y-auto" data-testid="sidebar-nav">
            {/* P5-10B: Menú Enterprise (agrupado y buscable) */}
            {USE_ENTERPRISE_MENU ? (
              <EnterpriseSidebarMenu 
                user={user}
                sqlMenus={sqlMenus}
                collapsed={sidebarCollapsed}
              />
            ) : (
              <>
            {/* Indicador de fuente de menús (solo dev) */}
            {process.env.NODE_ENV === 'development' && (
              <div className="px-4 py-1 text-[9px] text-zinc-600">
                Menús: {menusFinal.source}
              </div>
            )}
            
            {/* Sección: Módulos Principales */}
            <div className="mb-4">
              <p className="text-xs font-semibold text-zinc-500 uppercase tracking-wider px-4 mb-2">Módulos</p>
              {menusFinal.modulos.map((item) => {
                const Icon = item.icon;
                const isActive = location.pathname === item.href;
                const hasSubmenus = item.submenus && item.submenus.length > 0;
                const filteredSubmenus = hasSubmenus 
                  ? item.submenus.filter(sub => hasAccess(sub))
                  : [];
                const isExpanded = expandedMenus[item.name] || filteredSubmenus.some(sub => location.pathname === sub.href);
                const hasActiveSubmenu = filteredSubmenus.some(sub => location.pathname === sub.href);
                
                return (
                  <div key={item.name}>
                    {/* Menu item principal */}
                    {hasSubmenus && filteredSubmenus.length > 0 ? (
                      <div className="flex items-center">
                        <Link
                          to={item.href}
                          onClick={() => {
                            setSidebarOpen(false);
                            if (!isExpanded) setExpandedMenus(prev => ({ ...prev, [item.name]: true }));
                          }}
                          className={`flex-1 flex items-center gap-3 px-4 py-3 rounded-l-md transition-colors ${
                            isActive || hasActiveSubmenu
                              ? 'bg-zinc-800 text-white' 
                              : 'text-zinc-400 hover:bg-zinc-800 hover:text-white'
                          }`}
                          data-testid={`nav-${item.name.toLowerCase().replace(/\s+/g, '-')}`}
                        >
                          <Icon className="h-5 w-5" />
                          <span className="font-medium flex-1 text-left">{item.name}</span>
                          {item.badge && (
                            <span className="text-[10px] px-1.5 py-0.5 bg-amber-500/20 text-amber-400 rounded">
                              {item.badge}
                            </span>
                          )}
                        </Link>
                        <button
                          onClick={(e) => toggleSubmenu(item.name, e)}
                          className={`px-2 py-3 rounded-r-md transition-colors ${
                            isActive || hasActiveSubmenu
                              ? 'bg-zinc-800 text-white' 
                              : 'text-zinc-400 hover:bg-zinc-800 hover:text-white'
                          }`}
                          data-testid={`nav-${item.name.toLowerCase().replace(/\s+/g, '-')}-toggle`}
                          role="button"
                          aria-label={isExpanded ? "Cerrar submenú" : "Abrir submenú"}
                        >
                          {isExpanded ? (
                            <ChevronDown className="h-4 w-4" />
                          ) : (
                            <ChevronRight className="h-4 w-4" />
                          )}
                        </button>
                      </div>
                    ) : (
                      <Link
                        to={item.href}
                        onClick={() => setSidebarOpen(false)}
                        className={`flex items-center gap-3 px-4 py-3 rounded-md transition-colors ${
                          isActive 
                            ? 'bg-zinc-800 text-white' 
                            : 'text-zinc-400 hover:bg-zinc-800 hover:text-white'
                        }`}
                        data-testid={`nav-${item.name.toLowerCase().replace(/\s+/g, '-')}`}
                      >
                        <Icon className="h-5 w-5" />
                        <span className="font-medium flex-1">{item.name}</span>
                        {item.badge && (
                          <span className="text-[10px] px-1.5 py-0.5 bg-amber-500/20 text-amber-400 rounded">
                            {item.badge}
                          </span>
                        )}
                      </Link>
                    )}
                    
                    {/* Submenus */}
                    {hasSubmenus && filteredSubmenus.length > 0 && isExpanded && (
                      <div className="ml-4 mt-1 space-y-1 border-l border-zinc-700 pl-3">
                        {filteredSubmenus.map((submenu) => {
                          const SubIcon = submenu.icon;
                          const isSubActive = location.pathname === submenu.href;
                          
                          return (
                            <Link
                              key={submenu.name}
                              to={submenu.href}
                              onClick={() => setSidebarOpen(false)}
                              className={`flex items-center gap-3 px-3 py-2 rounded-md transition-colors text-sm ${
                                isSubActive 
                                  ? 'bg-zinc-800 text-white' 
                                  : 'text-zinc-400 hover:bg-zinc-800 hover:text-white'
                              }`}
                              data-testid={`nav-${submenu.name.toLowerCase().replace(/\s+/g, '-')}`}
                            >
                              <SubIcon className="h-4 w-4" />
                              <span className="font-medium">{submenu.name}</span>
                            </Link>
                          );
                        })}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>

            {/* Sección: Satélites Operativos (Solo si hay) */}
            {menusFinal.satelites && menusFinal.satelites.length > 0 && (
              <div className="mb-4">
                <p className="text-xs font-semibold text-amber-500/80 uppercase tracking-wider px-4 mb-2">
                  Satélites
                </p>
                {menusFinal.satelites.map((item) => {
                  const Icon = item.icon || Smartphone;
                  const isActive = location.pathname === item.href || location.pathname.startsWith(item.href?.split('/')[1] ? `/${item.href.split('/')[1]}` : '');
                  const hasSubmenus = item.submenus && item.submenus.length > 0;
                  const isExpanded = expandedMenus[item.name];
                  
                  return (
                    <div key={item.name}>
                      {hasSubmenus ? (
                        <div className="flex items-center">
                          <Link
                            to={item.href}
                            onClick={() => {
                              setSidebarOpen(false);
                              if (!isExpanded) setExpandedMenus(prev => ({ ...prev, [item.name]: true }));
                            }}
                            className={`flex-1 flex items-center gap-3 px-4 py-2.5 rounded-l-md transition-colors ${
                              isActive
                                ? 'bg-amber-900/30 text-amber-300 border-l-2 border-amber-500' 
                                : 'text-zinc-400 hover:bg-zinc-800 hover:text-white'
                            }`}
                            data-testid={`nav-satelite-${item.name?.toLowerCase().replace(/\s+/g, '-')}`}
                          >
                            <Icon className="h-5 w-5" />
                            <span className="font-medium flex-1 text-left text-sm">{item.name}</span>
                          </Link>
                          <button
                            onClick={(e) => toggleSubmenu(item.name, e)}
                            className={`px-2 py-2.5 rounded-r-md transition-colors ${
                              isActive
                                ? 'bg-amber-900/30 text-amber-300' 
                                : 'text-zinc-400 hover:bg-zinc-800 hover:text-white'
                            }`}
                            role="button"
                            aria-label={isExpanded ? "Cerrar submenú" : "Abrir submenú"}
                          >
                            {isExpanded ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
                          </button>
                        </div>
                      ) : (
                        <Link
                          to={item.href}
                          onClick={() => setSidebarOpen(false)}
                          className={`flex items-center gap-3 px-4 py-2.5 rounded-md transition-colors ${
                            isActive 
                              ? 'bg-amber-900/30 text-amber-300 border-l-2 border-amber-500' 
                              : 'text-zinc-400 hover:bg-zinc-800 hover:text-white'
                          }`}
                          data-testid={`nav-satelite-${item.name?.toLowerCase().replace(/\s+/g, '-')}`}
                        >
                          <Icon className="h-5 w-5" />
                          <span className="font-medium text-sm">{item.name}</span>
                        </Link>
                      )}
                      
                      {/* Submenús de satélite */}
                      {hasSubmenus && isExpanded && (
                        <div className="ml-4 mt-1 space-y-1 border-l border-amber-700/30 pl-3">
                          {item.submenus.map((submenu) => {
                            const SubIcon = submenu.icon || ChevronRight;
                            const isSubActive = location.pathname === submenu.href;
                            
                            return (
                              <Link
                                key={submenu.name}
                                to={submenu.href}
                                onClick={() => setSidebarOpen(false)}
                                className={`flex items-center gap-3 px-3 py-2 rounded-md transition-colors text-sm ${
                                  isSubActive 
                                    ? 'bg-amber-900/20 text-amber-200' 
                                    : 'text-zinc-400 hover:bg-zinc-800 hover:text-white'
                                }`}
                              >
                                <SubIcon className="h-4 w-4" />
                                <span className="font-medium">{submenu.name}</span>
                              </Link>
                            );
                          })}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            )}

            {/* Sección: Portales Externos (Solo si hay) */}
            {menusFinal.portales && menusFinal.portales.length > 0 && (
              <div className="mb-4">
                <p className="text-xs font-semibold text-blue-500/80 uppercase tracking-wider px-4 mb-2">
                  Portales
                </p>
                {menusFinal.portales.map((item) => {
                  const Icon = item.icon || LinkIcon;
                  const isActive = location.pathname === item.href;
                  
                  return (
                    <Link
                      key={item.name}
                      to={item.href}
                      onClick={() => setSidebarOpen(false)}
                      className={`flex items-center gap-3 px-4 py-2.5 rounded-md transition-colors ${
                        isActive 
                          ? 'bg-blue-900/30 text-blue-300 border-l-2 border-blue-500' 
                          : 'text-zinc-400 hover:bg-zinc-800 hover:text-white'
                      }`}
                      data-testid={`nav-portal-${item.name?.toLowerCase().replace(/\s+/g, '-')}`}
                    >
                      <Icon className="h-5 w-5" />
                      <span className="font-medium text-sm">{item.name}</span>
                    </Link>
                  );
                })}
              </div>
            )}

            {/* Sección: Sistema */}
            <div>
              <p className="text-xs font-semibold text-zinc-500 uppercase tracking-wider px-4 mb-2">Sistema</p>
              {menusFinal.sistema.map((item) => {
                const Icon = item.icon || Settings;
                const isActive = location.pathname === item.href;
                
                return (
                  <Link
                    key={item.name}
                    to={item.href}
                    onClick={() => setSidebarOpen(false)}
                    className={`flex items-center gap-3 px-4 py-3 rounded-md transition-colors ${
                      isActive 
                        ? 'bg-zinc-800 text-white' 
                        : 'text-zinc-400 hover:bg-zinc-800 hover:text-white'
                    }`}
                    data-testid={`nav-${item.name?.toLowerCase().replace(/\s+/g, '-')}`}
                  >
                    <Icon className="h-5 w-5" />
                    <span className="font-medium">{item.name}</span>
                  </Link>
                );
              })}
            </div>
              </>
            )}
          </nav>

          <div className={`${sidebarCollapsed ? 'p-3' : 'p-4'} border-t border-zinc-800`}>
            <Button
              variant="ghost"
              className={`text-zinc-400 hover:text-white hover:bg-zinc-800 ${
                sidebarCollapsed ? 'w-11 h-11 justify-center p-0 mx-auto' : 'w-full justify-start'
              }`}
              onClick={handleLogout}
              data-testid="logout-button"
              title="Cerrar Sesión"
              aria-label="Cerrar Sesión"
            >
              <LogOut className={sidebarCollapsed ? "h-5 w-5" : "h-5 w-5 mr-3"} />
              {!sidebarCollapsed && <span>Cerrar Sesión</span>}
            </Button>
          </div>
        </div>
      </aside>

      {/* Main content */}
      <main className={`${sidebarCollapsed ? 'lg:ml-20' : 'lg:ml-80'} pt-16 lg:pt-0`} data-testid="main-content">
        <div className="p-4 md:p-6 lg:p-8">
          <Outlet />
        </div>
      </main>

      {/* Overlay for mobile */}
      {sidebarOpen && (
        <div 
          className="fixed inset-0 bg-black/50 z-30 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}
    </div>
  );
};

export default Layout;