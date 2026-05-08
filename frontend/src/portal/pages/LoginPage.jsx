/**
 * Portal de Proveedores - Página de Login
 * Diseño de dos columnas: presentación izquierda + formulario derecho
 */
import React, { useState } from 'react';
import { toast } from 'sonner';
import { FileText, Lock, ArrowRight } from 'lucide-react';

const API_URL = process.env.REACT_APP_BACKEND_URL || '';

// Imagen de fondo - edificio corporativo de cristal
const BACKGROUND_IMAGE = 'https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?auto=format&fit=crop&w=1920&q=80';

export default function LoginPage({ onLogin, onRegister }) {
  const [rfc, setRfc] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!rfc || !password) {
      toast.error('Ingresa tu RFC y contraseña');
      return;
    }

    setLoading(true);
    try {
      // FASE AUTH-SECURITY-01: Usar credentials: 'include' para recibir cookie httpOnly
      const response = await fetch(`${API_URL}/api/portal/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',  // Recibir y enviar cookies
        body: JSON.stringify({ rfc: rfc.toUpperCase(), password })
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Error al iniciar sesión');
      }

      toast.success('Bienvenido');
      // El token ya está en la cookie httpOnly, solo pasamos supplier
      onLogin(data.token, data.supplier);
    } catch (error) {
      toast.error(error.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex">
      {/* Panel Izquierdo - Presentación */}
      <div 
        className="hidden lg:flex lg:w-1/2 relative bg-cover bg-center bg-no-repeat"
        style={{ backgroundImage: `url(${BACKGROUND_IMAGE})` }}
      >
        {/* Overlay azul oscuro */}
        <div className="absolute inset-0 bg-[#1a3a4a]/85"></div>
        
        {/* Contenido */}
        <div className="relative z-10 flex flex-col justify-center px-12 xl:px-16">
          {/* Ícono de edificio/documento */}
          <div className="mb-6">
            <svg 
              className="w-16 h-16 text-white/90" 
              viewBox="0 0 64 64" 
              fill="none" 
              stroke="currentColor" 
              strokeWidth="2"
            >
              <rect x="12" y="8" width="28" height="48" rx="2" />
              <rect x="18" y="16" width="6" height="6" rx="1" />
              <rect x="28" y="16" width="6" height="6" rx="1" />
              <rect x="18" y="26" width="6" height="6" rx="1" />
              <rect x="28" y="26" width="6" height="6" rx="1" />
              <rect x="18" y="36" width="6" height="6" rx="1" />
              <rect x="28" y="36" width="6" height="6" rx="1" />
              <rect x="21" y="46" width="10" height="10" rx="1" />
              <path d="M40 20h12v36H40" />
              <rect x="44" y="26" width="4" height="4" rx="0.5" />
              <rect x="44" y="34" width="4" height="4" rx="0.5" />
              <rect x="44" y="42" width="4" height="4" rx="0.5" />
            </svg>
          </div>

          {/* Título */}
          <h1 className="text-4xl xl:text-5xl font-bold text-white mb-6 leading-tight">
            Portal de Proveedores
          </h1>
          
          {/* Descripción */}
          <p className="text-lg xl:text-xl text-white/80 leading-relaxed max-w-md">
            Gestiona tus facturas, consulta el estado de tus pagos y mantén un control total de tu cuenta en un solo lugar.
          </p>
        </div>
      </div>

      {/* Panel Derecho - Formulario */}
      <div className="w-full lg:w-1/2 flex items-center justify-center bg-gray-50 p-6 sm:p-8">
        <div className="w-full max-w-md">
          {/* Card del formulario */}
          <div className="bg-white rounded-2xl shadow-lg p-8 sm:p-10">
            {/* Título del formulario */}
            <h2 className="text-3xl font-bold text-gray-900 mb-2">
              Iniciar Sesión
            </h2>
            <p className="text-gray-500 mb-8">
              Ingresa tu RFC y contraseña para acceder al portal
            </p>

            {/* Formulario */}
            <form onSubmit={handleSubmit} className="space-y-6">
              {/* Campo RFC */}
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">
                  RFC
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                    <FileText className="h-5 w-5 text-gray-400" />
                  </div>
                  <input
                    type="text"
                    value={rfc}
                    onChange={(e) => setRfc(e.target.value.toUpperCase())}
                    placeholder="XAXX010101000"
                    maxLength={13}
                    className="w-full pl-12 pr-4 py-3.5 bg-white border border-gray-200 rounded-xl focus:ring-2 focus:ring-gray-900 focus:border-transparent uppercase text-gray-900 placeholder:text-gray-400 transition-all"
                    data-testid="portal-rfc-input"
                  />
                </div>
              </div>

              {/* Campo Contraseña */}
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">
                  Contraseña
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                    <Lock className="h-5 w-5 text-gray-400" />
                  </div>
                  <input
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="••••••••"
                    className="w-full pl-12 pr-4 py-3.5 bg-white border border-gray-200 rounded-xl focus:ring-2 focus:ring-gray-900 focus:border-transparent text-gray-900 placeholder:text-gray-400 transition-all"
                    data-testid="portal-password-input"
                  />
                </div>
              </div>

              {/* Botón Ingresar */}
              <button
                type="submit"
                disabled={loading}
                className="w-full bg-gray-900 text-white py-4 rounded-xl font-semibold hover:bg-gray-800 disabled:opacity-50 disabled:cursor-not-allowed transition-all flex items-center justify-center gap-3"
                data-testid="portal-login-btn"
              >
                {loading ? (
                  <>
                    <div className="animate-spin rounded-full h-5 w-5 border-2 border-white border-t-transparent"></div>
                    <span>Ingresando...</span>
                  </>
                ) : (
                  <>
                    <span>Ingresar</span>
                    <ArrowRight className="h-5 w-5" />
                  </>
                )}
              </button>
            </form>

            {/* Registro */}
            <div className="mt-8 text-center">
              <p className="text-gray-500">
                ¿Primera vez en el portal?{' '}
                <button
                  onClick={onRegister}
                  className="text-gray-900 font-semibold hover:underline"
                  data-testid="portal-register-link"
                >
                  Regístrate aquí
                </button>
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
