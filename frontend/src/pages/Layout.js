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
  Settings
} from 'lucide-react';
import { useState } from 'react';

const Layout = () => {
  const location = useLocation();
  const user = getUser();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  if (!isAuthenticated()) {
    return <Navigate to="/login" replace />;
  }

  // Módulos principales según arquitectura
  const modulos = [
    { name: 'Inventarios', href: '/reportes', icon: Package, roles: ['Usuario', 'Supervisor', 'Administrador'], modulo: 1 },
    { name: 'Compras', href: '/compras', icon: ShoppingCart, roles: ['Usuario', 'Supervisor', 'Administrador'], modulo: 4 },
  ];

  // Configuración y sistema
  const sistema = [
    { name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard, roles: ['Usuario', 'Supervisor', 'Administrador'] },
    { name: 'Servidores', href: '/servidores', icon: Server, roles: ['Administrador'] },
    { name: 'Alertas', href: '/alertas', icon: Bell, roles: ['Supervisor', 'Administrador'] },
    { name: 'Usuarios', href: '/usuarios', icon: Users, roles: ['Administrador'] },
  ];

  const filteredModulos = modulos.filter(item => item.roles.includes(user?.role));
  const filteredSistema = sistema.filter(item => item.roles.includes(user?.role));

  return (
    <div className="min-h-screen bg-zinc-50" data-testid="layout">
      {/* Mobile sidebar toggle */}
      <div className="lg:hidden fixed top-0 left-0 right-0 z-50 bg-zinc-900 px-4 py-3 flex items-center justify-between">
        <h1 className="text-white font-bold text-lg" style={{ fontFamily: 'Manrope, sans-serif' }}>Edarsa Hub</h1>
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
              Edarsa Hub
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