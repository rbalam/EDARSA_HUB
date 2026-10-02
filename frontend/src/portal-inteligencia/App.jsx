/**
 * Portal de Inteligencia Comercial IA - EDARSAHUB
 * Dashboard ejecutivo con análisis de ventas por:
 * - Producto, Categoría, Familia, Subfamilia
 * - PAX, Propinas, Horarios (Desayuno/Comida/Cena)
 * - Casas/Distribuidores
 * 
 * NOTA: Este componente puede ser renderizado:
 * 1. Como ruta dentro del CRM principal (/inteligencia-comercial/*)
 * 2. Como aplicación standalone vía subdominio (inteligencia.edarsa.com.mx)
 */
import React, { useState, useEffect } from 'react';
import {
  LayoutDashboard, BarChart3, Wine, Clock, Users, 
  DollarSign, TrendingUp, LogOut, ChevronDown, User,
  Package, Layers, Building2, Percent, Droplet, Tag, LineChart, FileBarChart
} from 'lucide-react';

// Páginas
import DashboardIA from './pages/DashboardIA';
import VentasProductoPage from './pages/VentasProductoPage';
import VentasFamiliaPage from './pages/VentasFamiliaPage';
import VentasHorarioPage from './pages/VentasHorarioPage';
import VentasCasaPage from './pages/VentasCasaPage';
import VentasAlcoholPage from './pages/VentasAlcoholPage';
import ClasificacionAdminPage from './pages/ClasificacionAdminPage';
import ReporteadorBI from './pages/ReporteadorBI';
import AnalisisPAXPage from './pages/AnalisisPAXPage';
import BenchmarkGrupoPage from './pages/BenchmarkGrupoPage';
import ReportesISCAMPage from './pages/ReportesISCAMPage';
import api, { getToken } from '../lib/api';
import { ShieldAlert } from 'lucide-react';
import { intelApi, getMeIntel, logoutIntel, haySesionIntel } from './api/client';
import LoginInteligencia from './pages/LoginInteligencia';

// Mensajes honestos de sesión (sin modo demo).
const MENSAJES_AUTH = {
  SIN_SESION: { titulo: 'Sin sesión activa', detalle: 'Inicia sesión en EDARSA HUB para acceder al Portal de Inteligencia Comercial.' },
  SESION_EXPIRADA: { titulo: 'Sesión expirada', detalle: 'Tu sesión caducó. Vuelve a iniciar sesión para continuar.' },
  SIN_PERMISO: { titulo: 'Sin permiso', detalle: 'Tu usuario no tiene permiso para ver la Inteligencia Comercial. Contacta a un administrador.' },
};

function AuthGate({ estado }) {
  const m = MENSAJES_AUTH[estado] || MENSAJES_AUTH.SIN_SESION;
  const mostrarLogin = estado === 'SIN_SESION' || estado === 'SESION_EXPIRADA';
  return (
    <div className="min-h-screen bg-slate-900 flex items-center justify-center p-6" data-testid={`auth-gate-${String(estado).toLowerCase()}`}>
      <div className="max-w-md w-full bg-slate-800 border border-slate-700 rounded-2xl p-8 text-center">
        <div className="mx-auto w-12 h-12 rounded-full bg-amber-500/15 flex items-center justify-center mb-4">
          <ShieldAlert className="h-6 w-6 text-amber-400" />
        </div>
        <h1 className="text-xl font-semibold text-white">{m.titulo}</h1>
        <p className="text-sm text-slate-400 mt-2">{m.detalle}</p>
        {mostrarLogin && (
          <button
            onClick={() => { window.location.href = '/login'; }}
            data-testid="auth-gate-login-btn"
            className="mt-6 inline-flex items-center justify-center gap-2 px-5 py-2.5 rounded-lg bg-emerald-500 hover:bg-emerald-600 text-white text-sm font-medium transition-colors"
          >
            Ir al inicio de sesión
          </button>
        )}
      </div>
    </div>
  );
}

export default function PortalInteligenciaApp() {
  const [currentPage, setCurrentPage] = useState('dashboard');
  const [user, setUser] = useState(null);
  const [esExterno, setEsExterno] = useState(false);
  const [authEstado, setAuthEstado] = useState('CARGANDO'); // CARGANDO | OK | SIN_SESION | SESION_EXPIRADA | SIN_PERMISO
  const [loading, setLoading] = useState(true);
  const [showUserMenu, setShowUserMenu] = useState(false);
  const [unidadSeleccionada, setUnidadSeleccionada] = useState('todas');
  const [periodo, setPeriodo] = useState('mes');
  const [unidades, setUnidades] = useState([]);

  useEffect(() => {
    checkSession();
  }, []);

  // Unidades dinámicas desde SQL (sin hardcode) una vez autenticado.
  // El backend ya filtra por las unidades asignadas si el usuario es EXTERNO.
  useEffect(() => {
    if (authEstado !== 'OK') return;
    (async () => {
      try {
        const client = esExterno ? intelApi : api;
        const res = await client.get('/inteligencia/unidades');
        const lista = res.data?.unidades || [];
        setUnidades(lista);
        // Externo: no existe vista consolidada; pre-seleccionar su primera unidad.
        if (esExterno && lista.length > 0) {
          setUnidadSeleccionada((prev) => (prev === 'todas' ? lista[0].codigo : prev));
        }
      } catch { setUnidades([]); }
    })();
  }, [authEstado, esExterno]);

  // Sesión DUAL: 1) interno (Bearer del CRM)  2) externo (cookie del portal).
  const checkSession = async () => {
    // 1) Usuario interno del CRM
    if (getToken()) {
      try {
        const res = await api.get('/auth/me');
        setUser(res.data);
        setEsExterno(false);
        setAuthEstado('OK');
        setLoading(false);
        return;
      } catch (err) {
        const status = err?.response?.status;
        if (status === 403) { setAuthEstado('SIN_PERMISO'); setLoading(false); return; }
        // si 401, intentamos sesión externa abajo
      }
    }
    // 2) Usuario externo del portal (cookie)
    if (haySesionIntel()) {
      const me = await getMeIntel();
      if (me.ok) {
        setUser(me.user);
        setEsExterno(true);
        setAuthEstado('OK');
        setLoading(false);
        return;
      }
    }
    setAuthEstado('SIN_SESION');
    setLoading(false);
  };

  const handleLogout = async () => {
    if (esExterno) {
      await logoutIntel();
      setUser(null);
      window.location.reload();
      return;
    }
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

  // Usuario no autenticado: mostrar LOGIN EXTERNO propio (no redirigir al CRM).
  if (authEstado === 'SIN_SESION' || authEstado === 'SESION_EXPIRADA') {
    return (
      <LoginInteligencia
        onSuccess={(u) => { setUser(u); setEsExterno(true); setAuthEstado('OK'); }}
      />
    );
  }
  if (authEstado !== 'OK') {
    return <AuthGate estado={authEstado} />;
  }


  const menuItems = [
    { id: 'dashboard', label: 'Dashboard IA', icon: LayoutDashboard },
    { id: 'productos', label: 'Por Producto', icon: Package },
    { id: 'familias', label: 'Familia/Subfamilia', icon: Layers },
    { id: 'alcohol', label: 'Bebidas (Alcohol)', icon: Droplet },
    { id: 'horarios', label: 'Por Horario', icon: Clock },
    { id: 'casas', label: 'Casas/Distribuidores', icon: Building2 },
    { id: 'pax', label: 'Análisis PAX', icon: Users },
    { id: 'benchmark', label: 'Benchmark Grupo', icon: TrendingUp },
    { id: 'reporteador-bi', label: 'Reporteador BI', icon: LineChart },
    { id: 'iscam', label: 'Reportes ISCAM', icon: FileBarChart },
    { id: 'clasificacion', label: 'Clasificación (admin)', icon: Tag },
  // Usuarios EXTERNOS: solo vistas de consulta (sin administración/clasificación).
  ].filter((item) => !esExterno || item.id !== 'clasificacion');

  const renderPage = () => {
    const props = { 
      user, 
      unidadSeleccionada, 
      setUnidadSeleccionada,
      periodo,
      setPeriodo,
      onNavigate: setCurrentPage 
    };
    
    switch (currentPage) {
      case 'dashboard':
        return <DashboardIA {...props} />;
      case 'productos':
        return <VentasProductoPage {...props} />;
      case 'familias':
        return <VentasFamiliaPage {...props} />;
      case 'alcohol':
        return <VentasAlcoholPage {...props} />;
      case 'horarios':
        return <VentasHorarioPage {...props} />;
      case 'casas':
        return <VentasCasaPage {...props} />;
      case 'pax':
        return <AnalisisPAXPage {...props} />;
      case 'benchmark':
        return <BenchmarkGrupoPage {...props} />;
      case 'clasificacion':
        return <ClasificacionAdminPage {...props} />;
      case 'reporteador-bi':
        return <ReporteadorBI {...props} />;
      case 'iscam':
        return <ReportesISCAMPage {...props} />;
      default:
        return <DashboardIA {...props} />;
    }
  };

  return (
    <div className="min-h-screen flex bg-slate-900">
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
            data-testid="unidad-selector"
            className="w-full bg-slate-700 text-white text-sm rounded px-2 py-1.5 border border-slate-600 focus:border-emerald-400 focus:outline-none"
          >
            {!esExterno && <option value="todas">Todas las Unidades</option>}
            {unidades.map((u) => (
              <option key={u.codigo} value={u.codigo}>{u.nombre || u.codigo}</option>
            ))}
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
              <p className="text-xs text-slate-500">{user?.rol || user?.role || 'Consultor'}</p>
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
                  {esExterno ? 'Cerrar sesión' : 'Salir al CRM'}
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
