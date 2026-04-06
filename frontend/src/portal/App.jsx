/**
 * SupplierHub - Portal de Proveedores
 * Diseño con sidebar izquierdo estilo original
 */
import React, { useState, useEffect } from 'react';
import { Toaster } from 'sonner';
import { 
  LayoutDashboard, FileText, Upload, FolderUp, CreditCard, 
  LogOut, ChevronDown, User
} from 'lucide-react';

// Páginas
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import DashboardPage from './pages/DashboardPage';
import InvoicesPage from './pages/InvoicesPage';
import UploadInvoicePage from './pages/UploadInvoicePage';
import BatchUploadPage from './pages/BatchUploadPage';
import PaymentsPage from './pages/PaymentsPage';

const API_URL = process.env.REACT_APP_BACKEND_URL || '';

export default function PortalProveedoresApp() {
  const [currentPage, setCurrentPage] = useState('login');
  const [supplier, setSupplier] = useState(null);
  const [token, setToken] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showUserMenu, setShowUserMenu] = useState(false);

  useEffect(() => {
    const savedToken = localStorage.getItem('portal_token');
    if (savedToken) {
      verifyToken(savedToken);
    } else {
      setLoading(false);
    }
  }, []);

  const verifyToken = async (tkn) => {
    try {
      const response = await fetch(`${API_URL}/api/portal/auth/me`, {
        headers: { 'Authorization': `Bearer ${tkn}` }
      });
      if (response.ok) {
        const data = await response.json();
        setSupplier(data);
        setToken(tkn);
        setCurrentPage('dashboard');
      } else {
        localStorage.removeItem('portal_token');
      }
    } catch (error) {
      console.error('Error verificando token:', error);
      localStorage.removeItem('portal_token');
    } finally {
      setLoading(false);
    }
  };

  const handleLogin = (tkn, supplierData) => {
    localStorage.setItem('portal_token', tkn);
    setToken(tkn);
    setSupplier(supplierData);
    setCurrentPage('dashboard');
  };

  const handleLogout = () => {
    localStorage.removeItem('portal_token');
    setToken(null);
    setSupplier(null);
    setCurrentPage('login');
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-zinc-100 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-zinc-800"></div>
      </div>
    );
  }

  // Login/Register
  if (!token) {
    if (currentPage === 'register') {
      return (
        <>
          <Toaster position="top-right" richColors />
          <RegisterPage onBack={() => setCurrentPage('login')} onSuccess={() => setCurrentPage('login')} />
        </>
      );
    }
    return (
      <>
        <Toaster position="top-right" richColors />
        <LoginPage onLogin={handleLogin} onRegister={() => setCurrentPage('register')} />
      </>
    );
  }

  const menuItems = [
    { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { id: 'invoices', label: 'Mis Facturas', icon: FileText },
    { id: 'upload', label: 'Subir Factura', icon: Upload },
    { id: 'batch', label: 'Carga Masiva', icon: FolderUp },
    { id: 'payments', label: 'Mis Pagos', icon: CreditCard },
  ];

  const renderPage = () => {
    switch (currentPage) {
      case 'dashboard':
        return <DashboardPage supplier={supplier} token={token} onNavigate={setCurrentPage} />;
      case 'invoices':
        return <InvoicesPage supplier={supplier} token={token} onNavigate={setCurrentPage} />;
      case 'upload':
        return <UploadInvoicePage supplier={supplier} token={token} onNavigate={setCurrentPage} />;
      case 'batch':
        return <BatchUploadPage supplier={supplier} token={token} onNavigate={setCurrentPage} />;
      case 'payments':
        return <PaymentsPage supplier={supplier} token={token} onNavigate={setCurrentPage} />;
      default:
        return <DashboardPage supplier={supplier} token={token} onNavigate={setCurrentPage} />;
    }
  };

  return (
    <div className="min-h-screen bg-zinc-50 flex">
      <Toaster position="top-right" richColors />
      
      {/* Sidebar */}
      <aside className="w-[180px] bg-zinc-900 text-white flex flex-col fixed h-full">
        {/* Logo */}
        <div className="p-4 border-b border-zinc-800">
          <div className="flex items-center gap-2">
            <FileText className="h-6 w-6" />
            <span className="font-bold text-lg">SupplierHub</span>
          </div>
        </div>

        {/* Menu */}
        <nav className="flex-1 py-4">
          {menuItems.map((item) => {
            const Icon = item.icon;
            const isActive = currentPage === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setCurrentPage(item.id)}
                className={`w-full flex items-center gap-3 px-4 py-3 text-sm transition-colors ${
                  isActive 
                    ? 'bg-zinc-800 text-white' 
                    : 'text-zinc-400 hover:bg-zinc-800 hover:text-white'
                }`}
              >
                <Icon className="h-4 w-4" />
                {item.label}
              </button>
            );
          })}
        </nav>

        {/* Supplier info at bottom */}
        <div className="p-4 border-t border-zinc-800">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-zinc-700 rounded-full flex items-center justify-center text-sm font-bold">
              {supplier?.razon_social?.charAt(0) || 'E'}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-xs font-medium truncate">{supplier?.razon_social?.substring(0, 15) || 'Proveedor'}...</p>
              <p className="text-xs text-zinc-500">{supplier?.rfc}</p>
            </div>
          </div>
        </div>
      </aside>

      {/* Main content */}
      <div className="flex-1 ml-[180px]">
        {/* Top header */}
        <header className="bg-white border-b border-zinc-200 px-6 py-3 flex items-center justify-end sticky top-0 z-10">
          <div className="relative">
            <button
              onClick={() => setShowUserMenu(!showUserMenu)}
              className="flex items-center gap-2 text-sm text-zinc-700 hover:text-zinc-900"
            >
              <div className="w-8 h-8 bg-zinc-200 rounded-full flex items-center justify-center">
                <User className="h-4 w-4" />
              </div>
              <span>{supplier?.email || supplier?.rfc}</span>
              <ChevronDown className="h-4 w-4" />
            </button>
            
            {showUserMenu && (
              <div className="absolute right-0 top-full mt-2 w-48 bg-white rounded-lg shadow-lg border py-2">
                <div className="px-4 py-2 border-b">
                  <p className="text-sm font-medium">{supplier?.nombre_contacto}</p>
                  <p className="text-xs text-zinc-500">{supplier?.rfc}</p>
                </div>
                <button
                  onClick={handleLogout}
                  className="w-full px-4 py-2 text-left text-sm text-red-600 hover:bg-red-50 flex items-center gap-2"
                >
                  <LogOut className="h-4 w-4" />
                  Cerrar sesión
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
