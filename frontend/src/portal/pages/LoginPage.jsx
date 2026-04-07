/**
 * SupplierHub - Página de Login
 * Diseño con imagen de fondo estilo EDARSA HUB
 */
import React, { useState } from 'react';
import { toast } from 'sonner';

const API_URL = process.env.REACT_APP_BACKEND_URL || '';

// Imagen de fondo - almacén/logística
const BACKGROUND_IMAGE = 'https://images.unsplash.com/photo-1771530789155-b1f03fbf82b5?auto=format&fit=crop&w=1920&q=80';

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
      const response = await fetch(`${API_URL}/api/portal/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ rfc: rfc.toUpperCase(), password })
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Error al iniciar sesión');
      }

      toast.success('Bienvenido');
      onLogin(data.token, data.supplier);
    } catch (error) {
      toast.error(error.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div 
      className="min-h-screen flex items-center justify-center p-4 bg-cover bg-center bg-no-repeat"
      style={{ 
        backgroundImage: `url(${BACKGROUND_IMAGE})`,
      }}
    >
      {/* Overlay oscuro */}
      <div className="absolute inset-0 bg-black/30"></div>
      
      {/* Card de Login */}
      <div className="relative z-10 bg-white/95 backdrop-blur-sm rounded-2xl shadow-2xl w-full max-w-md p-8">
        {/* Título */}
        <h1 className="text-3xl font-black text-zinc-900 tracking-tight">SUPPLIER HUB</h1>
        <p className="text-zinc-500 mt-2 mb-8">Ingresa tus credenciales para continuar</p>

        {/* Formulario */}
        <form onSubmit={handleSubmit} className="space-y-5">
          <div>
            <label className="block text-sm font-medium text-zinc-700 mb-2">RFC</label>
            <input
              type="text"
              value={rfc}
              onChange={(e) => setRfc(e.target.value.toUpperCase())}
              placeholder="XAXX010101000"
              maxLength={13}
              className="w-full px-4 py-3 bg-white border border-zinc-300 rounded-lg focus:ring-2 focus:ring-zinc-900 focus:border-transparent uppercase text-zinc-900 placeholder:text-zinc-400"
              data-testid="portal-rfc-input"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-zinc-700 mb-2">Contraseña</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              className="w-full px-4 py-3 bg-white border border-zinc-300 rounded-lg focus:ring-2 focus:ring-zinc-900 focus:border-transparent text-zinc-900 placeholder:text-zinc-400"
              data-testid="portal-password-input"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-zinc-900 text-white py-3.5 rounded-lg font-semibold hover:bg-zinc-800 disabled:opacity-50 disabled:cursor-not-allowed transition-all flex items-center justify-center gap-2"
            data-testid="portal-login-btn"
          >
            {loading ? (
              <>
                <div className="animate-spin rounded-full h-5 w-5 border-2 border-white border-t-transparent"></div>
                <span>Ingresando...</span>
              </>
            ) : (
              <span>Iniciar Sesión</span>
            )}
          </button>
        </form>

        {/* Registro */}
        <div className="mt-6 text-center">
          <p className="text-zinc-500 text-sm">
            ¿Primera vez en el portal?{' '}
            <button
              onClick={onRegister}
              className="text-zinc-900 font-semibold hover:underline"
            >
              Regístrate aquí
            </button>
          </p>
        </div>
      </div>
    </div>
  );
}
