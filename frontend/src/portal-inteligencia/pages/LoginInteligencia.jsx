/**
 * Login del Portal de Inteligencia Comercial (usuarios EXTERNOS).
 * Pantalla propia, independiente del CRM. Sin mocks.
 */
import React, { useState } from 'react';
import { BarChart3, Loader2, Lock, Mail, AlertCircle } from 'lucide-react';
import { loginIntel } from '../api/client';
import { PasswordInput } from '@/components/auth/PasswordControls';

export default function LoginInteligencia({ onSuccess }) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    const res = await loginIntel(email.trim(), password);
    setLoading(false);
    if (res.ok) {
      onSuccess(res.user);
    } else {
      setError(res.error || 'No se pudo iniciar sesión');
    }
  };

  return (
    <div className="min-h-screen bg-slate-900 flex items-center justify-center p-6" data-testid="intel-login">
      <div className="max-w-md w-full">
        <div className="text-center mb-8">
          <div className="mx-auto w-14 h-14 rounded-2xl bg-emerald-500/15 flex items-center justify-center mb-4">
            <BarChart3 className="h-7 w-7 text-emerald-400" />
          </div>
          <h1 className="text-2xl font-bold text-white">Inteligencia Comercial</h1>
          <p className="text-sm text-slate-400 mt-1">Portal de consulta · Acceso de socios</p>
        </div>

        <form onSubmit={submit} className="bg-slate-800 border border-slate-700 rounded-2xl p-7 space-y-4">
          {error && (
            <div className="flex items-start gap-2 bg-red-500/10 border border-red-500/30 text-red-300 text-sm rounded-lg px-3 py-2" data-testid="intel-login-error">
              <AlertCircle className="h-4 w-4 mt-0.5 flex-shrink-0" />
              <span>{error}</span>
            </div>
          )}
          <div>
            <label className="text-xs text-slate-400 mb-1 block">Correo electrónico</label>
            <div className="relative">
              <Mail className="absolute left-3 top-2.5 h-4 w-4 text-slate-500" />
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                data-testid="intel-login-email"
                className="w-full bg-slate-700 text-white text-sm rounded-lg pl-9 pr-3 py-2.5 border border-slate-600 focus:border-emerald-400 focus:outline-none"
                placeholder="socio@empresa.com"
              />
            </div>
          </div>
          <div>
            <label className="text-xs text-slate-400 mb-1 block">Contraseña</label>
            <div className="relative">
              <PasswordInput
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                leftIcon={<Lock className="h-4 w-4" />}
                inputClassName="h-auto bg-slate-700 text-white text-sm rounded-lg pl-9 py-2.5 border-slate-600 focus:border-emerald-400 focus:outline-none"
                data-testid="intel-login-password"
              />
            </div>
          </div>
          <button
            type="submit"
            disabled={loading}
            data-testid="intel-login-submit"
            className="w-full inline-flex items-center justify-center gap-2 px-5 py-2.5 rounded-lg bg-emerald-500 hover:bg-emerald-600 disabled:opacity-60 text-white text-sm font-semibold transition-colors"
          >
            {loading && <Loader2 className="h-4 w-4 animate-spin" />}
            {loading ? 'Ingresando...' : 'Ingresar'}
          </button>
          <p className="text-xs text-slate-500 text-center pt-1">
            ¿Eres usuario interno de EDARSA?{' '}
            <a href="/login" className="text-emerald-400 hover:underline">Inicia sesión en el CRM</a>
          </p>
        </form>
      </div>
    </div>
  );
}
