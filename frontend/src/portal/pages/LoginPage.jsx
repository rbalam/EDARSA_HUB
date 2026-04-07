/**
 * SupplierHub - Página de Login
 * Diseño limpio con fondo claro
 */
import React, { useState } from 'react';
import { toast } from 'sonner';
import { FileText, ArrowRight } from 'lucide-react';

const API_URL = process.env.REACT_APP_BACKEND_URL || '';

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
    <div className="min-h-screen bg-zinc-50 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        {/* Logo */}
        <div className="flex items-center gap-3 mb-12">
          <div className="p-2 bg-zinc-100 rounded-lg">
            <FileText className="h-6 w-6 text-zinc-700" />
          </div>
          <span className="text-xl font-semibold text-zinc-900">SupplierHub</span>
        </div>

        {/* Título */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-zinc-900">Iniciar Sesión</h1>
          <p className="text-zinc-500 mt-2">Ingresa tu RFC y contraseña para acceder al portal</p>
        </div>

        {/* Formulario */}
        <form onSubmit={handleSubmit} className="space-y-5">
          <div>
            <label className="block text-sm font-medium text-zinc-700 mb-2">RFC</label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                <FileText className="h-5 w-5 text-zinc-400" />
              </div>
              <input
                type="text"
                value={rfc}
                onChange={(e) => setRfc(e.target.value.toUpperCase())}
                placeholder="XAXX010101000"
                maxLength={13}
                className="w-full pl-12 pr-4 py-3.5 bg-white border border-zinc-200 rounded-xl focus:ring-2 focus:ring-zinc-900 focus:border-transparent uppercase text-zinc-900 placeholder:text-zinc-400"
                data-testid="portal-rfc-input"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-zinc-700 mb-2">Contraseña</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              className="w-full px-4 py-3.5 bg-white border border-zinc-200 rounded-xl focus:ring-2 focus:ring-zinc-900 focus:border-transparent text-zinc-900 placeholder:text-zinc-400"
              data-testid="portal-password-input"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-zinc-900 text-white py-3.5 rounded-xl font-semibold hover:bg-zinc-800 disabled:opacity-50 disabled:cursor-not-allowed transition-all flex items-center justify-center gap-2"
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
          <p className="text-zinc-500">
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
