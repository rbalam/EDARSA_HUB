/**
 * Portal Proveedores - Página de Registro
 */
import React, { useState } from 'react';
import { toast } from 'sonner';

const API_URL = process.env.REACT_APP_BACKEND_URL || '';

export default function RegisterPage({ onBack, onSuccess }) {
  const [formData, setFormData] = useState({
    rfc: '',
    razon_social: '',
    nombre_contacto: '',
    email: '',
    telefono: '',
    password: '',
    password_confirm: '',
    banco: '',
    clabe: '',
    cuenta: ''
  });
  const [loading, setLoading] = useState(false);
  const [step, setStep] = useState(1); // 1: Datos básicos, 2: Datos bancarios

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: name === 'rfc' ? value.toUpperCase() : value
    }));
  };

  const validateStep1 = () => {
    if (!formData.rfc || formData.rfc.length < 12) {
      toast.error('RFC inválido (debe tener 12-13 caracteres)');
      return false;
    }
    if (!formData.razon_social) {
      toast.error('Ingresa la razón social');
      return false;
    }
    if (!formData.nombre_contacto) {
      toast.error('Ingresa el nombre de contacto');
      return false;
    }
    if (!formData.email || !formData.email.includes('@')) {
      toast.error('Ingresa un email válido');
      return false;
    }
    if (!formData.password || formData.password.length < 6) {
      toast.error('La contraseña debe tener al menos 6 caracteres');
      return false;
    }
    if (formData.password !== formData.password_confirm) {
      toast.error('Las contraseñas no coinciden');
      return false;
    }
    return true;
  };

  const handleNextStep = () => {
    if (validateStep1()) {
      setStep(2);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    setLoading(true);
    try {
      const response = await fetch(`${API_URL}/api/portal/auth/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Error al registrar');
      }

      toast.success('Registro exitoso. Tu cuenta está pendiente de aprobación.');
      onSuccess();
    } catch (error) {
      toast.error(error.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-900 to-blue-700 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-lg p-8">
        <div className="text-center mb-6">
          <h1 className="text-2xl font-bold text-blue-800">Registro de Proveedor</h1>
          <p className="text-zinc-500 mt-1">Paso {step} de 2</p>
          
          {/* Progress bar */}
          <div className="flex gap-2 mt-4">
            <div className={`flex-1 h-2 rounded ${step >= 1 ? 'bg-blue-600' : 'bg-zinc-200'}`}></div>
            <div className={`flex-1 h-2 rounded ${step >= 2 ? 'bg-blue-600' : 'bg-zinc-200'}`}></div>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          {step === 1 && (
            <>
              <div>
                <label className="block text-sm font-medium text-zinc-700 mb-1">RFC *</label>
                <input
                  type="text"
                  name="rfc"
                  value={formData.rfc}
                  onChange={handleChange}
                  placeholder="XAXX010101000"
                  maxLength={13}
                  className="w-full px-4 py-2 border border-zinc-300 rounded-lg focus:ring-2 focus:ring-blue-500 uppercase"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-zinc-700 mb-1">Razón Social *</label>
                <input
                  type="text"
                  name="razon_social"
                  value={formData.razon_social}
                  onChange={handleChange}
                  placeholder="Empresa SA de CV"
                  className="w-full px-4 py-2 border border-zinc-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-zinc-700 mb-1">Nombre de Contacto *</label>
                <input
                  type="text"
                  name="nombre_contacto"
                  value={formData.nombre_contacto}
                  onChange={handleChange}
                  placeholder="Juan Pérez"
                  className="w-full px-4 py-2 border border-zinc-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-zinc-700 mb-1">Email *</label>
                  <input
                    type="email"
                    name="email"
                    value={formData.email}
                    onChange={handleChange}
                    placeholder="correo@empresa.com"
                    className="w-full px-4 py-2 border border-zinc-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-zinc-700 mb-1">Teléfono</label>
                  <input
                    type="tel"
                    name="telefono"
                    value={formData.telefono}
                    onChange={handleChange}
                    placeholder="55 1234 5678"
                    className="w-full px-4 py-2 border border-zinc-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-zinc-700 mb-1">Contraseña *</label>
                  <input
                    type="password"
                    name="password"
                    value={formData.password}
                    onChange={handleChange}
                    placeholder="Min. 6 caracteres"
                    className="w-full px-4 py-2 border border-zinc-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-zinc-700 mb-1">Confirmar *</label>
                  <input
                    type="password"
                    name="password_confirm"
                    value={formData.password_confirm}
                    onChange={handleChange}
                    placeholder="Repetir contraseña"
                    className="w-full px-4 py-2 border border-zinc-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </div>

              <button
                type="button"
                onClick={handleNextStep}
                className="w-full bg-blue-600 text-white py-3 rounded-lg font-semibold hover:bg-blue-700 transition-colors mt-4"
              >
                Siguiente
              </button>
            </>
          )}

          {step === 2 && (
            <>
              <div className="bg-blue-50 p-4 rounded-lg mb-4">
                <p className="text-sm text-blue-800">
                  <strong>Datos bancarios</strong> (opcionales pero recomendados para agilizar pagos)
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-zinc-700 mb-1">Banco</label>
                <input
                  type="text"
                  name="banco"
                  value={formData.banco}
                  onChange={handleChange}
                  placeholder="BBVA, Santander, etc."
                  className="w-full px-4 py-2 border border-zinc-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-zinc-700 mb-1">CLABE Interbancaria (18 dígitos)</label>
                <input
                  type="text"
                  name="clabe"
                  value={formData.clabe}
                  onChange={handleChange}
                  placeholder="012345678901234567"
                  maxLength={18}
                  className="w-full px-4 py-2 border border-zinc-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-zinc-700 mb-1">Número de Cuenta</label>
                <input
                  type="text"
                  name="cuenta"
                  value={formData.cuenta}
                  onChange={handleChange}
                  placeholder="1234567890"
                  className="w-full px-4 py-2 border border-zinc-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div className="flex gap-4 mt-6">
                <button
                  type="button"
                  onClick={() => setStep(1)}
                  className="flex-1 bg-zinc-200 text-zinc-700 py-3 rounded-lg font-semibold hover:bg-zinc-300 transition-colors"
                >
                  Atrás
                </button>
                <button
                  type="submit"
                  disabled={loading}
                  className="flex-1 bg-blue-600 text-white py-3 rounded-lg font-semibold hover:bg-blue-700 disabled:opacity-50 transition-colors"
                >
                  {loading ? 'Registrando...' : 'Completar Registro'}
                </button>
              </div>
            </>
          )}
        </form>

        <div className="mt-6 text-center">
          <button
            onClick={onBack}
            className="text-blue-600 text-sm hover:underline"
          >
            ← Volver al login
          </button>
        </div>
      </div>
    </div>
  );
}
