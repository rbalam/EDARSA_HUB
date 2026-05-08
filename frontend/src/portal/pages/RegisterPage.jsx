/**
 * SupplierHub - Página de Registro
 * Diseño limpio con fondo claro
 */
import React, { useState } from 'react';
import { toast } from 'sonner';
import { FileText, ArrowLeft, ArrowRight, Check } from 'lucide-react';

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
  const [step, setStep] = useState(1);

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
    <div className="min-h-screen bg-zinc-50 flex items-center justify-center p-4">
      <div className="w-full max-w-lg">
        {/* Logo */}
        <div className="flex items-center gap-3 mb-8">
          <div className="p-2 bg-zinc-100 rounded-lg">
            <FileText className="h-6 w-6 text-zinc-700" />
          </div>
          <span className="text-xl font-semibold text-zinc-900">SupplierHub</span>
        </div>

        {/* Título y Progress */}
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-zinc-900">Registro de Proveedor</h1>
          <p className="text-zinc-500 mt-1">Paso {step} de 2</p>
          
          <div className="flex gap-2 mt-4">
            <div className={`flex-1 h-1.5 rounded-full ${step >= 1 ? 'bg-zinc-900' : 'bg-zinc-200'}`}></div>
            <div className={`flex-1 h-1.5 rounded-full ${step >= 2 ? 'bg-zinc-900' : 'bg-zinc-200'}`}></div>
          </div>
        </div>

        {/* Formulario */}
        <form onSubmit={handleSubmit} className="space-y-4">
          {step === 1 && (
            <>
              <div>
                <label className="block text-sm font-medium text-zinc-700 mb-2">RFC *</label>
                <input
                  type="text"
                  name="rfc"
                  value={formData.rfc}
                  onChange={handleChange}
                  placeholder="XAXX010101000"
                  maxLength={13}
                  className="w-full px-4 py-3 bg-white border border-zinc-200 rounded-xl focus:ring-2 focus:ring-zinc-900 focus:border-transparent uppercase"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-zinc-700 mb-2">Razón Social *</label>
                <input
                  type="text"
                  name="razon_social"
                  value={formData.razon_social}
                  onChange={handleChange}
                  placeholder="Empresa SA de CV"
                  className="w-full px-4 py-3 bg-white border border-zinc-200 rounded-xl focus:ring-2 focus:ring-zinc-900 focus:border-transparent"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-zinc-700 mb-2">Nombre de Contacto *</label>
                <input
                  type="text"
                  name="nombre_contacto"
                  value={formData.nombre_contacto}
                  onChange={handleChange}
                  placeholder="Juan Pérez"
                  className="w-full px-4 py-3 bg-white border border-zinc-200 rounded-xl focus:ring-2 focus:ring-zinc-900 focus:border-transparent"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-zinc-700 mb-2">Email *</label>
                  <input
                    type="email"
                    name="email"
                    value={formData.email}
                    onChange={handleChange}
                    placeholder="correo@empresa.com"
                    className="w-full px-4 py-3 bg-white border border-zinc-200 rounded-xl focus:ring-2 focus:ring-zinc-900 focus:border-transparent"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-zinc-700 mb-2">Teléfono</label>
                  <input
                    type="tel"
                    name="telefono"
                    value={formData.telefono}
                    onChange={handleChange}
                    placeholder="55 1234 5678"
                    className="w-full px-4 py-3 bg-white border border-zinc-200 rounded-xl focus:ring-2 focus:ring-zinc-900 focus:border-transparent"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-zinc-700 mb-2">Contraseña *</label>
                  <input
                    type="password"
                    name="password"
                    value={formData.password}
                    onChange={handleChange}
                    placeholder="Min. 6 caracteres"
                    className="w-full px-4 py-3 bg-white border border-zinc-200 rounded-xl focus:ring-2 focus:ring-zinc-900 focus:border-transparent"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-zinc-700 mb-2">Confirmar *</label>
                  <input
                    type="password"
                    name="password_confirm"
                    value={formData.password_confirm}
                    onChange={handleChange}
                    placeholder="Repetir contraseña"
                    className="w-full px-4 py-3 bg-white border border-zinc-200 rounded-xl focus:ring-2 focus:ring-zinc-900 focus:border-transparent"
                  />
                </div>
              </div>

              <button
                type="button"
                onClick={handleNextStep}
                className="w-full bg-zinc-900 text-white py-3.5 rounded-xl font-semibold hover:bg-zinc-800 transition-all flex items-center justify-center gap-2 mt-6"
              >
                <span>Siguiente</span>
                <ArrowRight className="h-5 w-5" />
              </button>
            </>
          )}

          {step === 2 && (
            <>
              <div className="bg-zinc-100 p-4 rounded-xl mb-4">
                <p className="text-sm text-zinc-700">
                  <strong>Datos bancarios</strong> (opcionales pero recomendados para agilizar pagos)
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-zinc-700 mb-2">Banco</label>
                <input
                  type="text"
                  name="banco"
                  value={formData.banco}
                  onChange={handleChange}
                  placeholder="BBVA, Santander, etc."
                  className="w-full px-4 py-3 bg-white border border-zinc-200 rounded-xl focus:ring-2 focus:ring-zinc-900 focus:border-transparent"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-zinc-700 mb-2">CLABE Interbancaria (18 dígitos)</label>
                <input
                  type="text"
                  name="clabe"
                  value={formData.clabe}
                  onChange={handleChange}
                  placeholder="012345678901234567"
                  maxLength={18}
                  className="w-full px-4 py-3 bg-white border border-zinc-200 rounded-xl focus:ring-2 focus:ring-zinc-900 focus:border-transparent"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-zinc-700 mb-2">Número de Cuenta</label>
                <input
                  type="text"
                  name="cuenta"
                  value={formData.cuenta}
                  onChange={handleChange}
                  placeholder="1234567890"
                  className="w-full px-4 py-3 bg-white border border-zinc-200 rounded-xl focus:ring-2 focus:ring-zinc-900 focus:border-transparent"
                />
              </div>

              <div className="flex gap-4 mt-6">
                <button
                  type="button"
                  onClick={() => setStep(1)}
                  className="flex-1 bg-zinc-200 text-zinc-700 py-3.5 rounded-xl font-semibold hover:bg-zinc-300 transition-all flex items-center justify-center gap-2"
                >
                  <ArrowLeft className="h-5 w-5" />
                  <span>Atrás</span>
                </button>
                <button
                  type="submit"
                  disabled={loading}
                  className="flex-1 bg-zinc-900 text-white py-3.5 rounded-xl font-semibold hover:bg-zinc-800 disabled:opacity-50 transition-all flex items-center justify-center gap-2"
                >
                  {loading ? (
                    <>
                      <div className="animate-spin rounded-full h-5 w-5 border-2 border-white border-t-transparent"></div>
                      <span>Registrando...</span>
                    </>
                  ) : (
                    <>
                      <Check className="h-5 w-5" />
                      <span>Completar</span>
                    </>
                  )}
                </button>
              </div>
            </>
          )}
        </form>

        {/* Volver */}
        <div className="mt-6 text-center">
          <button
            onClick={onBack}
            className="text-zinc-500 text-sm hover:text-zinc-900 flex items-center justify-center gap-1 mx-auto"
          >
            <ArrowLeft className="h-4 w-4" />
            Volver al login
          </button>
        </div>
      </div>
    </div>
  );
}
