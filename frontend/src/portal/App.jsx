/**
 * Portal de Proveedores - App Principal
 * Subproyecto separado de EDARSA HUB
 * NO modifica nada de EDARSA HUB
 */
import React, { useState, useEffect } from 'react';
import { Toaster } from 'sonner';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import DashboardPage from './pages/DashboardPage';
import InvoicesPage from './pages/InvoicesPage';
import UploadInvoicePage from './pages/UploadInvoicePage';
import AccountStatusPage from './pages/AccountStatusPage';

const API_URL = process.env.REACT_APP_BACKEND_URL || '';

export default function PortalProveedoresApp() {
  const [currentPage, setCurrentPage] = useState('login');
  const [supplier, setSupplier] = useState(null);
  const [token, setToken] = useState(null);
  const [loading, setLoading] = useState(true);

  // Verificar sesión al cargar
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
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  // Renderizar página según estado
  const renderPage = () => {
    if (!token) {
      if (currentPage === 'register') {
        return <RegisterPage onBack={() => setCurrentPage('login')} onSuccess={() => setCurrentPage('login')} />;
      }
      return <LoginPage onLogin={handleLogin} onRegister={() => setCurrentPage('register')} />;
    }

    switch (currentPage) {
      case 'dashboard':
        return <DashboardPage supplier={supplier} token={token} onNavigate={setCurrentPage} />;
      case 'invoices':
        return <InvoicesPage supplier={supplier} token={token} onNavigate={setCurrentPage} />;
      case 'upload':
        return <UploadInvoicePage supplier={supplier} token={token} onNavigate={setCurrentPage} />;
      case 'account':
        return <AccountStatusPage supplier={supplier} token={token} onNavigate={setCurrentPage} />;
      default:
        return <DashboardPage supplier={supplier} token={token} onNavigate={setCurrentPage} />;
    }
  };

  return (
    <div className="min-h-screen bg-zinc-100">
      <Toaster position="top-right" richColors />
      
      {/* Header si está logueado */}
      {token && (
        <header className="bg-blue-800 text-white shadow-lg">
          <div className="max-w-7xl mx-auto px-4 py-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <h1 className="text-xl font-bold">Portal Proveedores</h1>
                <span className="text-blue-200 text-sm">|</span>
                <span className="text-blue-200 text-sm">{supplier?.razon_social}</span>
              </div>
              
              <nav className="flex items-center gap-4">
                <button
                  onClick={() => setCurrentPage('dashboard')}
                  className={`px-3 py-1 rounded text-sm ${currentPage === 'dashboard' ? 'bg-blue-700' : 'hover:bg-blue-700'}`}
                >
                  Inicio
                </button>
                <button
                  onClick={() => setCurrentPage('invoices')}
                  className={`px-3 py-1 rounded text-sm ${currentPage === 'invoices' ? 'bg-blue-700' : 'hover:bg-blue-700'}`}
                >
                  Mis Facturas
                </button>
                <button
                  onClick={() => setCurrentPage('upload')}
                  className={`px-3 py-1 rounded text-sm ${currentPage === 'upload' ? 'bg-blue-700' : 'hover:bg-blue-700'}`}
                >
                  Subir Factura
                </button>
                <button
                  onClick={() => setCurrentPage('account')}
                  className={`px-3 py-1 rounded text-sm ${currentPage === 'account' ? 'bg-blue-700' : 'hover:bg-blue-700'}`}
                >
                  Estado de Cuenta
                </button>
                <button
                  onClick={handleLogout}
                  className="px-3 py-1 rounded text-sm bg-red-600 hover:bg-red-700 ml-4"
                >
                  Salir
                </button>
              </nav>
            </div>
          </div>
        </header>
      )}
      
      {/* Contenido principal */}
      <main className={token ? "max-w-7xl mx-auto px-4 py-6" : ""}>
        {renderPage()}
      </main>
    </div>
  );
}
