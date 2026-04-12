import { Outlet, Navigate, useLocation, Link } from 'react-router-dom';
import { isAuthenticated, getUser, logout } from '@/lib/auth';
import { Button } from '@/components/ui/button';
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
  ChevronRight
} from 'lucide-react';
import { useState } from 'react';

const Layout = () => {
  const location = useLocation();
  const user = getUser();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [expandedMenus, setExpandedMenus] = useState({});

  if (!isAuthenticated()) {
    return <Navigate to="/login" replace />;
  }

  // Toggle submenu expansion
  const toggleSubmenu = (menuName) => {
    setExpandedMenus(prev => ({
      ...prev,
      [menuName]: !prev[menuName]
    }));
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
    },
    { 
      name: 'Compras', 
      href: '/compras', 
      icon: ShoppingCart, 
      roles: ['Usuario', 'Supervisor', 'Administrador'],
    },
    { 
      name: 'Inventarios', 
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
      roles: ['Supervisor', 'Administrador'],
      badge: 'Próx.'
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
  ];

  // ============================================
  // SISTEMA (Administración y Configuración)
  // ============================================
  
  const sistema = [
    { name: 'Servidores', href: '/servidores', icon: Server, roles: ['Administrador'] },
    { name: 'Catálogo SQL', href: '/catalogo-consultas', icon: Database, roles: ['Supervisor', 'Administrador'] },
    { name: 'Explorador BD', href: '/explorador-bd', icon: TableProperties, roles: ['Administrador'] },
    { name: 'Alertas', href: '/alertas', icon: Bell, roles: ['Supervisor', 'Administrador'] },
    { name: 'Usuarios', href: '/usuarios', icon: Users, roles: ['Administrador'] },
  ];

  const filteredModulos = modulos.filter(item => item.roles.includes(user?.role));
  const filteredSistema = sistema.filter(item => item.roles.includes(user?.role));

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
        className={`fixed inset-y-0 left-0 z-40 w-64 bg-zinc-900 transform transition-transform duration-200 lg:translate-x-0 ${
          sidebarOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
        data-testid="sidebar"
      >
        <div className="flex flex-col h-full">
          <div className="p-6 border-b border-zinc-800">
            <h1 className="text-xl font-extrabold text-white" style={{ fontFamily: 'Manrope, sans-serif' }}>
              EDARSA HUB
            </h1>
            <p className="text-zinc-400 text-sm mt-1">{user?.name}</p>
            <p className="text-zinc-500 text-xs">{user?.role}</p>
          </div>

          <nav className="flex-1 p-4 space-y-1 overflow-y-auto" data-testid="sidebar-nav">
            {/* Sección: Módulos */}
            <div className="mb-4">
              <p className="text-xs font-semibold text-zinc-500 uppercase tracking-wider px-4 mb-2">Módulos</p>
              {filteredModulos.map((item) => {
                const Icon = item.icon;
                const isActive = location.pathname === item.href;
                const hasSubmenus = item.submenus && item.submenus.length > 0;
                const filteredSubmenus = hasSubmenus 
                  ? item.submenus.filter(sub => sub.roles.includes(user?.role))
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
                          onClick={() => toggleSubmenu(item.name)}
                          className={`px-2 py-3 rounded-r-md transition-colors ${
                            isActive || hasActiveSubmenu
                              ? 'bg-zinc-800 text-white' 
                              : 'text-zinc-400 hover:bg-zinc-800 hover:text-white'
                          }`}
                          data-testid={`nav-${item.name.toLowerCase().replace(/\s+/g, '-')}-toggle`}
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

            {/* Sección: Sistema */}
            <div>
              <p className="text-xs font-semibold text-zinc-500 uppercase tracking-wider px-4 mb-2">Sistema</p>
              {filteredSistema.map((item) => {
                const Icon = item.icon;
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
                    data-testid={`nav-${item.name.toLowerCase()}`}
                  >
                    <Icon className="h-5 w-5" />
                    <span className="font-medium">{item.name}</span>
                  </Link>
                );
              })}
            </div>
          </nav>

          <div className="p-4 border-t border-zinc-800">
            <Button
              variant="ghost"
              className="w-full justify-start text-zinc-400 hover:text-white hover:bg-zinc-800"
              onClick={logout}
              data-testid="logout-button"
            >
              <LogOut className="h-5 w-5 mr-3" />
              Cerrar Sesión
            </Button>
          </div>
        </div>
      </aside>

      {/* Main content */}
      <main className="lg:ml-64 pt-16 lg:pt-0" data-testid="main-content">
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