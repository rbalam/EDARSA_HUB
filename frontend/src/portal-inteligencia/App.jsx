/**
 * Portal de Inteligencia Comercial IA - EDARSAHUB
 * Dashboard ejecutivo con análisis de ventas por:
 * - Producto, Categoría, Familia, Subfamilia
 * - PAX, Propinas, Horarios (Desayuno/Comida/Cena)
 * - Casas/Distribuidores (Diageo, Casa Cuervo, Pernod, etc.)
 */
import React, { useState, useEffect } from 'react';
import { Toaster } from 'sonner';
import { 
  LayoutDashboard, BarChart3, Wine, Clock, Users, 
  DollarSign, TrendingUp, LogOut, ChevronDown, User,
  Package, Layers, Building2, Percent
} from 'lucide-react';

// Páginas
import DashboardIA from './pages/DashboardIA';
import VentasProductoPage from './pages/VentasProductoPage';
import VentasFamiliaPage from './pages/VentasFamiliaPage';
import VentasHorarioPage from './pages/VentasHorarioPage';
import VentasCasaPage from './pages/VentasCasaPage';
import AnalisisPAXPage from './pages/AnalisisPAXPage';

const API_URL = process.env.REACT_APP_BACKEND_URL || '';

export default function PortalInteligenciaApp() {
  const [currentPage, setCurrentPage] = useState('dashboard');
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showUserMenu, setShowUserMenu] = useState(false);
  const [unidadSeleccionada, setUnidadSeleccionada] = useState('todas');

  useEffect(() => {
    // Verificar si hay sesión activa del CRM principal
    checkSession();
  }, []);

  const checkSession = async () => {
    // Timeout de 3 segundos para la verificación de sesión
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 3000);
    
    try {
      const response = await fetch(`${API_URL}/api/auth/me`, {
        credentials: 'include',
        signal: controller.signal
      });
      
      clearTimeout(timeoutId);
      
      if (response.ok) {
        const data = await response.json();
        setUser(data);
      } else {
        // Modo demo para externos (respuesta 401, etc.)
        setUser({ 
          nombre: 'Usuario Externo', 
          rol: 'CONSULTOR_EXTERNO',
          email: 'demo@edarsa.com'
        });
      }
    } catch (error) {
      clearTimeout(timeoutId);
      // Fallback a modo demo (timeout o error de red)
      setUser({ 
        nombre: 'Usuario Demo', 
        rol: 'DEMO',
        email: 'demo@inteligencia.edarsa.com'
      });
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    setUser(null);
    window.location.href = '/';
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-900 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-emerald-400 mx-auto"></div>
          <p className="mt-4 text-slate-400">Cargando Inteligencia Comercial...</p>
        </div>
      </div>
    );
  }

  const menuItems = [
    { id: 'dashboard', label: 'Dashboard IA', icon: LayoutDashboard },
    { id: 'productos', label: 'Por Producto', icon: Package },
    { id: 'familias', label: 'Familia/Subfamilia', icon: Layers },
    { id: 'horarios', label: 'Por Horario', icon: Clock },
    { id: 'casas', label: 'Casas/Distribuidores', icon: Building2 },
    { id: 'pax', label: 'Análisis PAX', icon: Users },
  ];

  const renderPage = () => {
    const props = { 
      user, 
      unidadSeleccionada, 
      setUnidadSeleccionada,
      onNavigate: setCurrentPage 
    };
    
    switch (currentPage) {
      case 'dashboard':
        return <DashboardIA {...props} />;
      case 'productos':
        return <VentasProductoPage {...props} />;
      case 'familias':
        return <VentasFamiliaPage {...props} />;
      case 'horarios':
        return <VentasHorarioPage {...props} />;
      case 'casas':
        return <VentasCasaPage {...props} />;
      case 'pax':
        return <AnalisisPAXPage {...props} />;
      default:
        return <DashboardIA {...props} />;
    }
  };

  return (
    <div className="min-h-screen flex bg-slate-900">
      <Toaster position="top-right" richColors />
      
      {/* Sidebar - Estilo oscuro premium */}
      <aside className="w-[200px] bg-slate-800 border-r border-slate-700 flex flex-col fixed h-full">
        {/* Logo */}
        <div className="p-4 border-b border-slate-700">
          <div className="flex items-center gap-2">
            <BarChart3 className="h-6 w-6 text-emerald-400" />
            <div>
              <span className="font-bold text-lg text-white">Inteligencia</span>
              <p className="text-xs text-slate-400">Comercial IA</p>
            </div>
          </div>
        </div>

        {/* Selector de Unidad */}
        <div className="p-3 border-b border-slate-700">
          <label className="text-xs text-slate-400 mb-1 block">Unidad de Negocio</label>
          <select 
            value={unidadSeleccionada}
            onChange={(e) => setUnidadSeleccionada(e.target.value)}
            className="w-full bg-slate-700 text-white text-sm rounded px-2 py-1.5 border border-slate-600 focus:border-emerald-400 focus:outline-none"
          >
            <option value="todas">Todas las Unidades</option>
            <option value="cienfuegos">CIENFUEGOS</option>
            <option value="merida">130° MÉRIDA</option>
            <option value="queretaro">130° QUERÉTARO</option>
            <option value="estelar">LA ESTELAR</option>
            <option value="origen">ORIGEN</option>
          </select>
        </div>

        {/* Menu */}
        <nav className="flex-1 py-4 overflow-y-auto">
          {menuItems.map((item) => {
            const Icon = item.icon;
            const isActive = currentPage === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setCurrentPage(item.id)}
                data-testid={`menu-${item.id}`}
                className={`w-full flex items-center gap-3 px-4 py-3 text-sm transition-all ${
                  isActive 
                    ? 'bg-emerald-500/20 text-emerald-400 border-r-2 border-emerald-400' 
                    : 'text-slate-400 hover:bg-slate-700/50 hover:text-white'
                }`}
              >
                <Icon className="h-4 w-4" />
                {item.label}
              </button>
            );
          })}
        </nav>

        {/* User info at bottom */}
        <div className="p-4 border-t border-slate-700">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-emerald-500/20 rounded-full flex items-center justify-center text-sm font-bold text-emerald-400">
              {user?.nombre?.charAt(0) || 'U'}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-xs font-medium text-white truncate">{user?.nombre || 'Usuario'}</p>
              <p className="text-xs text-slate-500">{user?.rol || 'Consultor'}</p>
            </div>
          </div>
        </div>
      </aside>

      {/* Main content */}
      <div className="flex-1 ml-[200px]">
        {/* Top header */}
        <header className="bg-slate-800/50 backdrop-blur border-b border-slate-700 px-6 py-3 flex items-center justify-between sticky top-0 z-10">
          <div className="flex items-center gap-4">
            <h1 className="text-lg font-semibold text-white">
              {menuItems.find(m => m.id === currentPage)?.label || 'Dashboard'}
            </h1>
            <span className="px-2 py-0.5 bg-emerald-500/20 text-emerald-400 text-xs rounded-full">
              {unidadSeleccionada === 'todas' ? 'Consolidado' : unidadSeleccionada.toUpperCase()}
            </span>
          </div>
          
          <div className="relative">
            <button
              onClick={() => setShowUserMenu(!showUserMenu)}
              className="flex items-center gap-2 text-sm text-slate-300 hover:text-white"
            >
              <div className="w-8 h-8 bg-slate-700 rounded-full flex items-center justify-center">
                <User className="h-4 w-4" />
              </div>
              <span>{user?.email || 'Usuario'}</span>
              <ChevronDown className="h-4 w-4" />
            </button>
            
            {showUserMenu && (
              <div className="absolute right-0 top-full mt-2 w-48 bg-slate-800 rounded-lg shadow-lg border border-slate-700 py-2">
                <div className="px-4 py-2 border-b border-slate-700">
                  <p className="text-sm font-medium text-white">{user?.nombre}</p>
                  <p className="text-xs text-slate-400">{user?.email}</p>
                </div>
                <button
                  onClick={handleLogout}
                  className="w-full px-4 py-2 text-left text-sm text-red-400 hover:bg-red-500/10 flex items-center gap-2"
                  data-testid="inteligencia-logout-btn"
                >
                  <LogOut className="h-4 w-4" />
                  Salir al CRM
                </button>
              </div>
            )}
          </div>
        </header>

        {/* Page content */}
        <main className="p-6">
          {renderPage()}
        </main>
      </div>
    </div>
  );
}
