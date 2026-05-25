/**
 * COSTOS-ALERTAS-001-D: Tab de Reglas de Margen
 * =============================================
 * UI para configurar reglas de margen esperado con jerarquía:
 * Producto > Subfamilia > Familia > Grupo
 * 
 * Endpoints utilizados:
 * - GET /api/comercial/alertas-margen/reglas
 * - POST /api/comercial/alertas-margen/reglas
 * - PUT /api/comercial/alertas-margen/reglas/{id}
 * - DELETE /api/comercial/alertas-margen/reglas/{id}
 * - GET /api/comercial/alertas-margen/resolver-regla
 * - POST /api/comercial/alertas-margen/evaluar
 * - GET /api/comercial/alertas-margen/estadisticas
 * - GET /api/comercial/alertas-margen/umbrales
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
  AlertTriangle, Plus, Edit, Trash2, Search, RefreshCw, CheckCircle,
  XCircle, Target, Layers, Package, ChevronDown, ChevronUp, X, Save,
  TrendingDown, TrendingUp, Info, Settings, Eye, Play, Filter
} from 'lucide-react';
import api from '@/lib/api';

// ==================== CONSTANTES ====================

const NIVELES_APLICACION = [
  { value: 'GRUPO', label: 'Grupo', description: 'Aplica a todo el grupo de productos', icon: Layers, color: 'blue' },
  { value: 'FAMILIA', label: 'Familia', description: 'Aplica a una familia específica', icon: Package, color: 'green' },
  { value: 'SUBFAMILIA', label: 'Subfamilia', description: 'Aplica a una subfamilia', icon: Package, color: 'purple' },
  { value: 'PRODUCTO', label: 'Producto', description: 'Regla específica para un producto', icon: Target, color: 'orange' }
];

const SEVERIDADES = [
  { value: 'INFORMATIVA', label: 'Informativa', color: 'blue', description: '0-2 puntos bajo' },
  { value: 'MEDIA', label: 'Media', color: 'yellow', description: '2-5 puntos bajo' },
  { value: 'ALTA', label: 'Alta', color: 'orange', description: '5-10 puntos bajo' },
  { value: 'CRITICA', label: 'Crítica', color: 'red', description: '+10 puntos bajo' }
];

// ==================== UTILIDADES ====================

const formatPercent = (value) => {
  if (value === null || value === undefined) return '-';
  return `${Number(value).toFixed(1)}%`;
};

const formatDate = (dateStr) => {
  if (!dateStr) return '-';
  try {
    return new Date(dateStr).toLocaleDateString('es-MX', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  } catch {
    return dateStr;
  }
};

const getNivelConfig = (nivel) => {
  return NIVELES_APLICACION.find(n => n.value === nivel) || NIVELES_APLICACION[0];
};

const getSeveridadConfig = (severidad) => {
  return SEVERIDADES.find(s => s.value === severidad) || SEVERIDADES[0];
};

// ==================== COMPONENTES AUXILIARES ====================

const NivelBadge = ({ nivel }) => {
  const config = getNivelConfig(nivel);
  const Icon = config.icon;
  const colorClasses = {
    blue: 'bg-blue-100 text-blue-700 border-blue-200',
    green: 'bg-green-100 text-green-700 border-green-200',
    purple: 'bg-purple-100 text-purple-700 border-purple-200',
    orange: 'bg-orange-100 text-orange-700 border-orange-200'
  };
  
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-1 rounded text-xs font-medium border ${colorClasses[config.color]}`}>
      <Icon className="w-3 h-3" />
      {config.label}
    </span>
  );
};

const SeveridadBadge = ({ severidad }) => {
  const config = getSeveridadConfig(severidad);
  const colorClasses = {
    blue: 'bg-blue-100 text-blue-700',
    yellow: 'bg-yellow-100 text-yellow-700',
    orange: 'bg-orange-100 text-orange-700',
    red: 'bg-red-100 text-red-700'
  };
  
  return (
    <span className={`inline-flex items-center px-2 py-1 rounded text-xs font-medium ${colorClasses[config.color]}`}>
      {config.label}
    </span>
  );
};

const StatCard = ({ title, value, icon: Icon, color = 'blue', subtitle }) => (
  <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
    <div className="flex items-center justify-between">
      <div>
        <p className="text-sm text-gray-500">{title}</p>
        <p className={`text-2xl font-bold text-${color}-600`}>{value}</p>
        {subtitle && <p className="text-xs text-gray-400 mt-1">{subtitle}</p>}
      </div>
      <div className={`p-3 bg-${color}-100 rounded-full`}>
        <Icon className={`w-6 h-6 text-${color}-600`} />
      </div>
    </div>
  </div>
);

// ==================== MODAL CREAR/EDITAR REGLA ====================

const ModalRegla = ({ isOpen, onClose, regla, onSave, loading }) => {
  const [form, setForm] = useState({
    nivel_aplicacion: 'GRUPO',
    entidad_codigo: '',
    margen_esperado: 30,
    severidad_base: 'MEDIA',
    descripcion: '',
    activo: true
  });
  
  useEffect(() => {
    if (regla) {
      setForm({
        nivel_aplicacion: regla.nivel_aplicacion || 'GRUPO',
        entidad_codigo: regla.entidad_codigo || '',
        margen_esperado: regla.margen_esperado || 30,
        severidad_base: regla.severidad_base || 'MEDIA',
        descripcion: regla.descripcion || '',
        activo: regla.activo !== false
      });
    } else {
      setForm({
        nivel_aplicacion: 'GRUPO',
        entidad_codigo: '',
        margen_esperado: 30,
        severidad_base: 'MEDIA',
        descripcion: '',
        activo: true
      });
    }
  }, [regla, isOpen]);
  
  if (!isOpen) return null;
  
  const handleSubmit = (e) => {
    e.preventDefault();
    onSave(form);
  };
  
  const nivelConfig = getNivelConfig(form.nivel_aplicacion);
  
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-lg max-h-[90vh] overflow-hidden">
        <div className="p-4 border-b flex justify-between items-center bg-gradient-to-r from-orange-600 to-orange-700">
          <h3 className="text-lg font-semibold text-white flex items-center gap-2">
            <AlertTriangle className="w-5 h-5" />
            {regla ? 'Editar Regla de Margen' : 'Nueva Regla de Margen'}
          </h3>
          <button onClick={onClose} className="p-1 hover:bg-orange-800 rounded text-white">
            <X className="w-5 h-5" />
          </button>
        </div>
        
        <form onSubmit={handleSubmit} className="p-6 space-y-4 overflow-y-auto max-h-[calc(90vh-140px)]">
          {/* Info de jerarquía */}
          <div className="bg-blue-50 rounded-lg p-3 text-sm">
            <div className="flex items-start gap-2">
              <Info className="w-4 h-4 text-blue-600 mt-0.5" />
              <div>
                <p className="font-medium text-blue-800">Jerarquía de Reglas</p>
                <p className="text-blue-600 text-xs mt-1">
                  Producto {">"} Subfamilia {">"} Familia {">"} Grupo
                </p>
                <p className="text-blue-600 text-xs">
                  La regla más específica siempre tiene prioridad.
                </p>
              </div>
            </div>
          </div>
          
          {/* Nivel de aplicación */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Nivel de Aplicación *
            </label>
            <div className="grid grid-cols-2 gap-2">
              {NIVELES_APLICACION.map((nivel) => {
                const Icon = nivel.icon;
                const isSelected = form.nivel_aplicacion === nivel.value;
                return (
                  <button
                    key={nivel.value}
                    type="button"
                    onClick={() => setForm({ ...form, nivel_aplicacion: nivel.value })}
                    className={`p-3 rounded-lg border-2 text-left transition-all ${
                      isSelected
                        ? `border-${nivel.color}-500 bg-${nivel.color}-50`
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                  >
                    <div className="flex items-center gap-2">
                      <Icon className={`w-4 h-4 ${isSelected ? `text-${nivel.color}-600` : 'text-gray-400'}`} />
                      <span className={`font-medium ${isSelected ? `text-${nivel.color}-700` : 'text-gray-700'}`}>
                        {nivel.label}
                      </span>
                    </div>
                    <p className="text-xs text-gray-500 mt-1">{nivel.description}</p>
                  </button>
                );
              })}
            </div>
          </div>
          
          {/* Código de entidad */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Código de {nivelConfig.label} *
            </label>
            <input
              type="text"
              value={form.entidad_codigo}
              onChange={(e) => setForm({ ...form, entidad_codigo: e.target.value.toUpperCase() })}
              placeholder={`Ej: ${form.nivel_aplicacion === 'GRUPO' ? 'ALIMENTOS' : form.nivel_aplicacion === 'FAMILIA' ? 'CARNES' : form.nivel_aplicacion === 'PRODUCTO' ? 'RIB-EYE-500G' : 'CORTES-PREMIUM'}`}
              required
              className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500 uppercase"
              data-testid="input-entidad-codigo"
            />
            <p className="text-xs text-gray-500 mt-1">
              Debe coincidir exactamente con el código en el sistema
            </p>
          </div>
          
          {/* Margen esperado */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Margen Esperado (%) *
            </label>
            <div className="flex items-center gap-3">
              <input
                type="range"
                min="0"
                max="100"
                step="1"
                value={form.margen_esperado}
                onChange={(e) => setForm({ ...form, margen_esperado: Number(e.target.value) })}
                className="flex-1 h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-orange-500"
              />
              <div className="flex items-center gap-1">
                <input
                  type="number"
                  min="0"
                  max="100"
                  step="0.1"
                  value={form.margen_esperado}
                  onChange={(e) => setForm({ ...form, margen_esperado: Number(e.target.value) })}
                  className="w-20 px-2 py-1 border rounded text-center font-bold text-orange-600"
                />
                <span className="text-gray-500">%</span>
              </div>
            </div>
            <div className="flex justify-between text-xs text-gray-400 mt-1">
              <span>0% (sin margen)</span>
              <span>100% (todo ganancia)</span>
            </div>
          </div>
          
          {/* Severidad base */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Severidad Base de Alerta
            </label>
            <div className="grid grid-cols-4 gap-2">
              {SEVERIDADES.map((sev) => {
                const isSelected = form.severidad_base === sev.value;
                const bgColors = {
                  blue: isSelected ? 'bg-blue-100 border-blue-500' : 'bg-gray-50 border-gray-200',
                  yellow: isSelected ? 'bg-yellow-100 border-yellow-500' : 'bg-gray-50 border-gray-200',
                  orange: isSelected ? 'bg-orange-100 border-orange-500' : 'bg-gray-50 border-gray-200',
                  red: isSelected ? 'bg-red-100 border-red-500' : 'bg-gray-50 border-gray-200'
                };
                return (
                  <button
                    key={sev.value}
                    type="button"
                    onClick={() => setForm({ ...form, severidad_base: sev.value })}
                    className={`p-2 rounded-lg border-2 text-center transition-all ${bgColors[sev.color]}`}
                  >
                    <span className={`text-sm font-medium ${isSelected ? `text-${sev.color}-700` : 'text-gray-600'}`}>
                      {sev.label}
                    </span>
                  </button>
                );
              })}
            </div>
          </div>
          
          {/* Descripción */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Descripción (opcional)
            </label>
            <textarea
              value={form.descripcion}
              onChange={(e) => setForm({ ...form, descripcion: e.target.value })}
              placeholder="Ej: Margen mínimo para productos premium de carnes"
              rows={2}
              className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500 resize-none"
            />
          </div>
        </form>
        
        <div className="p-4 border-t bg-gray-50 flex justify-end gap-3">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 border rounded-lg hover:bg-gray-100 transition-colors"
          >
            Cancelar
          </button>
          <button
            onClick={handleSubmit}
            disabled={loading || !form.entidad_codigo}
            className="px-4 py-2 bg-orange-600 text-white rounded-lg hover:bg-orange-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            data-testid="btn-guardar-regla"
          >
            {loading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
            Guardar Regla
          </button>
        </div>
      </div>
    </div>
  );
};

// ==================== MODAL RESOLVER REGLA ====================

const ModalResolverRegla = ({ isOpen, onClose }) => {
  const [form, setForm] = useState({
    producto_clave: '',
    subfamilia_codigo: '',
    familia_codigo: '',
    grupo_codigo: ''
  });
  const [resultado, setResultado] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  
  const handleResolver = async () => {
    setLoading(true);
    setError(null);
    setResultado(null);
    
    try {
      const params = new URLSearchParams();
      if (form.producto_clave) params.append('producto_clave', form.producto_clave);
      if (form.subfamilia_codigo) params.append('subfamilia_codigo', form.subfamilia_codigo);
      if (form.familia_codigo) params.append('familia_codigo', form.familia_codigo);
      if (form.grupo_codigo) params.append('grupo_codigo', form.grupo_codigo);
      
      const response = await api.get(`/comercial/alertas-margen/resolver-regla?${params.toString()}`);
      setResultado(response.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Error al resolver regla');
    } finally {
      setLoading(false);
    }
  };
  
  if (!isOpen) return null;
  
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-md">
        <div className="p-4 border-b flex justify-between items-center bg-gradient-to-r from-blue-600 to-blue-700">
          <h3 className="text-lg font-semibold text-white flex items-center gap-2">
            <Eye className="w-5 h-5" />
            Resolver Regla por Jerarquía
          </h3>
          <button onClick={onClose} className="p-1 hover:bg-blue-800 rounded text-white">
            <X className="w-5 h-5" />
          </button>
        </div>
        
        <div className="p-6 space-y-4">
          <p className="text-sm text-gray-600">
            Ingresa los códigos para ver qué regla aplica según la jerarquía.
          </p>
          
          <div className="space-y-3">
            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1">Producto</label>
              <input
                type="text"
                value={form.producto_clave}
                onChange={(e) => setForm({ ...form, producto_clave: e.target.value.toUpperCase() })}
                placeholder="Código de producto"
                className="w-full px-3 py-2 border rounded text-sm uppercase"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1">Subfamilia</label>
              <input
                type="text"
                value={form.subfamilia_codigo}
                onChange={(e) => setForm({ ...form, subfamilia_codigo: e.target.value.toUpperCase() })}
                placeholder="Código de subfamilia"
                className="w-full px-3 py-2 border rounded text-sm uppercase"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1">Familia</label>
              <input
                type="text"
                value={form.familia_codigo}
                onChange={(e) => setForm({ ...form, familia_codigo: e.target.value.toUpperCase() })}
                placeholder="Código de familia"
                className="w-full px-3 py-2 border rounded text-sm uppercase"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1">Grupo</label>
              <input
                type="text"
                value={form.grupo_codigo}
                onChange={(e) => setForm({ ...form, grupo_codigo: e.target.value.toUpperCase() })}
                placeholder="Código de grupo"
                className="w-full px-3 py-2 border rounded text-sm uppercase"
              />
            </div>
          </div>
          
          <button
            onClick={handleResolver}
            disabled={loading}
            className="w-full py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 flex items-center justify-center gap-2"
          >
            {loading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
            Resolver Regla
          </button>
          
          {error && (
            <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
              {error}
            </div>
          )}
          
          {resultado && (
            <div className={`p-4 rounded-lg border ${
              resultado.fuente === 'SIN_REGLA' 
                ? 'bg-gray-50 border-gray-200' 
                : 'bg-green-50 border-green-200'
            }`}>
              <div className="flex items-center gap-2 mb-2">
                {resultado.fuente === 'SIN_REGLA' ? (
                  <XCircle className="w-5 h-5 text-gray-500" />
                ) : (
                  <CheckCircle className="w-5 h-5 text-green-600" />
                )}
                <span className="font-medium">
                  {resultado.fuente === 'SIN_REGLA' ? 'Sin regla aplicable' : `Regla de ${resultado.fuente}`}
                </span>
              </div>
              {resultado.fuente !== 'SIN_REGLA' && (
                <div className="space-y-1 text-sm">
                  <p><span className="text-gray-500">Margen esperado:</span> <span className="font-bold text-green-700">{formatPercent(resultado.margen_esperado)}</span></p>
                  <p><span className="text-gray-500">Entidad:</span> {resultado.entidad_codigo}</p>
                  {resultado.descripcion && (
                    <p><span className="text-gray-500">Descripción:</span> {resultado.descripcion}</p>
                  )}
                </div>
              )}
              {resultado.mensaje && (
                <p className="text-xs text-gray-500 mt-2">{resultado.mensaje}</p>
              )}
            </div>
          )}
        </div>
        
        <div className="p-4 border-t bg-gray-50 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 border rounded-lg hover:bg-gray-100"
          >
            Cerrar
          </button>
        </div>
      </div>
    </div>
  );
};

// ==================== MODAL EVALUAR MARGEN ====================

const ModalEvaluarMargen = ({ isOpen, onClose }) => {
  const [form, setForm] = useState({
    margen_actual: 25,
    producto_clave: '',
    familia_codigo: '',
    grupo_codigo: ''
  });
  const [resultado, setResultado] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  
  const handleEvaluar = async () => {
    setLoading(true);
    setError(null);
    setResultado(null);
    
    try {
      const response = await api.post('/comercial/alertas-margen/evaluar', {
        margen_actual: form.margen_actual,
        producto_clave: form.producto_clave || undefined,
        familia_codigo: form.familia_codigo || undefined,
        grupo_codigo: form.grupo_codigo || undefined
      });
      setResultado(response.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Error al evaluar margen');
    } finally {
      setLoading(false);
    }
  };
  
  if (!isOpen) return null;
  
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-md">
        <div className="p-4 border-b flex justify-between items-center bg-gradient-to-r from-purple-600 to-purple-700">
          <h3 className="text-lg font-semibold text-white flex items-center gap-2">
            <Target className="w-5 h-5" />
            Evaluar Margen
          </h3>
          <button onClick={onClose} className="p-1 hover:bg-purple-800 rounded text-white">
            <X className="w-5 h-5" />
          </button>
        </div>
        
        <div className="p-6 space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Margen Actual (%) *
            </label>
            <div className="flex items-center gap-2">
              <input
                type="range"
                min="0"
                max="100"
                value={form.margen_actual}
                onChange={(e) => setForm({ ...form, margen_actual: Number(e.target.value) })}
                className="flex-1 accent-purple-500"
              />
              <input
                type="number"
                value={form.margen_actual}
                onChange={(e) => setForm({ ...form, margen_actual: Number(e.target.value) })}
                className="w-20 px-2 py-1 border rounded text-center font-bold"
              />
              <span>%</span>
            </div>
          </div>
          
          <div className="grid grid-cols-3 gap-2">
            <div>
              <label className="block text-xs text-gray-500 mb-1">Producto</label>
              <input
                type="text"
                value={form.producto_clave}
                onChange={(e) => setForm({ ...form, producto_clave: e.target.value.toUpperCase() })}
                className="w-full px-2 py-1 border rounded text-sm uppercase"
                placeholder="Código"
              />
            </div>
            <div>
              <label className="block text-xs text-gray-500 mb-1">Familia</label>
              <input
                type="text"
                value={form.familia_codigo}
                onChange={(e) => setForm({ ...form, familia_codigo: e.target.value.toUpperCase() })}
                className="w-full px-2 py-1 border rounded text-sm uppercase"
                placeholder="Código"
              />
            </div>
            <div>
              <label className="block text-xs text-gray-500 mb-1">Grupo</label>
              <input
                type="text"
                value={form.grupo_codigo}
                onChange={(e) => setForm({ ...form, grupo_codigo: e.target.value.toUpperCase() })}
                className="w-full px-2 py-1 border rounded text-sm uppercase"
                placeholder="Código"
              />
            </div>
          </div>
          
          <button
            onClick={handleEvaluar}
            disabled={loading}
            className="w-full py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 flex items-center justify-center gap-2"
          >
            {loading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
            Evaluar Margen
          </button>
          
          {error && (
            <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
              {error}
            </div>
          )}
          
          {resultado && (
            <div className={`p-4 rounded-lg border ${
              resultado.tiene_alerta 
                ? 'bg-red-50 border-red-200' 
                : 'bg-green-50 border-green-200'
            }`}>
              <div className="flex items-center gap-2 mb-3">
                {resultado.tiene_alerta ? (
                  <AlertTriangle className="w-5 h-5 text-red-600" />
                ) : (
                  <CheckCircle className="w-5 h-5 text-green-600" />
                )}
                <span className={`font-medium ${resultado.tiene_alerta ? 'text-red-700' : 'text-green-700'}`}>
                  {resultado.tiene_alerta ? 'ALERTA: Margen Bajo' : 'OK: Margen Cumple'}
                </span>
              </div>
              
              <div className="grid grid-cols-2 gap-3 text-sm">
                <div>
                  <span className="text-gray-500">Margen actual:</span>
                  <p className="font-bold">{formatPercent(resultado.margen_actual)}</p>
                </div>
                <div>
                  <span className="text-gray-500">Margen esperado:</span>
                  <p className="font-bold">{formatPercent(resultado.margen_esperado)}</p>
                </div>
                <div>
                  <span className="text-gray-500">Diferencia:</span>
                  <p className={`font-bold ${resultado.diferencia_puntos > 0 ? 'text-red-600' : 'text-green-600'}`}>
                    {resultado.diferencia_puntos > 0 ? '-' : '+'}{Math.abs(resultado.diferencia_puntos || 0).toFixed(1)} pts
                  </p>
                </div>
                <div>
                  <span className="text-gray-500">Severidad:</span>
                  <p><SeveridadBadge severidad={resultado.severidad} /></p>
                </div>
              </div>
              
              <p className="text-xs text-gray-500 mt-3 pt-2 border-t">
                Fuente: Regla de {resultado.fuente_regla || 'N/A'}
              </p>
            </div>
          )}
        </div>
        
        <div className="p-4 border-t bg-gray-50 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 border rounded-lg hover:bg-gray-100"
          >
            Cerrar
          </button>
        </div>
      </div>
    </div>
  );
};

// ==================== COMPONENTE PRINCIPAL ====================

const TabReglasMargen = () => {
  const [reglas, setReglas] = useState([]);
  const [estadisticas, setEstadisticas] = useState(null);
  const [umbrales, setUmbrales] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [filtroNivel, setFiltroNivel] = useState('');
  const [busqueda, setBusqueda] = useState('');
  
  // Modales
  const [modalRegla, setModalRegla] = useState({ open: false, regla: null });
  const [modalResolver, setModalResolver] = useState(false);
  const [modalEvaluar, setModalEvaluar] = useState(false);
  const [savingRegla, setSavingRegla] = useState(false);
  
  // Cargar datos
  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    
    try {
      const [reglasRes, statsRes, umbralesRes] = await Promise.all([
        api.get('/comercial/alertas-margen/reglas?page_size=100'),
        api.get('/comercial/alertas-margen/estadisticas'),
        api.get('/comercial/alertas-margen/umbrales')
      ]);
      
      setReglas(reglasRes.data.reglas || []);
      setEstadisticas(statsRes.data);
      setUmbrales(umbralesRes.data.umbrales || []);
    } catch (err) {
      setError(err.response?.data?.detail || 'Error al cargar datos');
    } finally {
      setLoading(false);
    }
  }, []);
  
  useEffect(() => {
    fetchData();
  }, [fetchData]);
  
  // Guardar regla
  const handleSaveRegla = async (form) => {
    setSavingRegla(true);
    
    try {
      if (modalRegla.regla) {
        await api.put(`/comercial/alertas-margen/reglas/${modalRegla.regla.regla_id}`, form);
      } else {
        await api.post('/comercial/alertas-margen/reglas', form);
      }
      
      setModalRegla({ open: false, regla: null });
      fetchData();
    } catch (err) {
      alert(err.response?.data?.detail?.mensaje || err.response?.data?.detail || 'Error al guardar regla');
    } finally {
      setSavingRegla(false);
    }
  };
  
  // Desactivar regla
  const handleDesactivarRegla = async (regla) => {
    if (!window.confirm(`¿Desactivar regla "${regla.entidad_codigo}"?`)) return;
    
    try {
      await api.delete(`/comercial/alertas-margen/reglas/${regla.regla_id}`);
      fetchData();
    } catch (err) {
      alert(err.response?.data?.detail || 'Error al desactivar regla');
    }
  };
  
  // Filtrar reglas
  const reglasFiltradas = reglas.filter(r => {
    if (filtroNivel && r.nivel_aplicacion !== filtroNivel) return false;
    if (busqueda && !r.entidad_codigo.toLowerCase().includes(busqueda.toLowerCase())) return false;
    return true;
  });
  
  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <RefreshCw className="w-8 h-8 animate-spin text-orange-500" />
        <span className="ml-3 text-gray-600">Cargando reglas de margen...</span>
      </div>
    );
  }
  
  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">
        <AlertTriangle className="w-5 h-5 inline mr-2" />
        {error}
        <button onClick={fetchData} className="ml-4 text-sm underline">Reintentar</button>
      </div>
    );
  }
  
  return (
    <div className="space-y-6">
      {/* Estadísticas */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard
          title="Total Reglas"
          value={estadisticas?.total_reglas || 0}
          icon={Settings}
          color="blue"
        />
        <StatCard
          title="Reglas Activas"
          value={estadisticas?.reglas_activas || 0}
          icon={CheckCircle}
          color="green"
        />
        <StatCard
          title="Por Grupo"
          value={estadisticas?.por_nivel?.GRUPO || 0}
          icon={Layers}
          color="purple"
        />
        <StatCard
          title="Por Producto"
          value={estadisticas?.por_nivel?.PRODUCTO || 0}
          icon={Target}
          color="orange"
        />
      </div>
      
      {/* Info de Umbrales */}
      <div className="bg-white rounded-lg shadow-sm border p-4">
        <h3 className="font-medium text-gray-800 mb-3 flex items-center gap-2">
          <Info className="w-4 h-4 text-blue-500" />
          Umbrales de Severidad
        </h3>
        <div className="flex flex-wrap gap-3">
          {umbrales.map((u) => (
            <div
              key={u.severidad}
              className="flex items-center gap-2 px-3 py-1 rounded-full text-sm"
              style={{ backgroundColor: `${u.color}20`, color: u.color }}
            >
              <span className="w-2 h-2 rounded-full" style={{ backgroundColor: u.color }} />
              <span className="font-medium">{u.severidad}:</span>
              <span>{u.puntos_desde} - {u.puntos_hasta} pts</span>
            </div>
          ))}
        </div>
      </div>
      
      {/* Toolbar */}
      <div className="bg-white rounded-lg shadow-sm border p-4">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            {/* Búsqueda */}
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                type="text"
                value={busqueda}
                onChange={(e) => setBusqueda(e.target.value)}
                placeholder="Buscar código..."
                className="pl-9 pr-4 py-2 border rounded-lg w-48 focus:outline-none focus:ring-2 focus:ring-orange-500"
              />
            </div>
            
            {/* Filtro por nivel */}
            <select
              value={filtroNivel}
              onChange={(e) => setFiltroNivel(e.target.value)}
              className="px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500"
            >
              <option value="">Todos los niveles</option>
              {NIVELES_APLICACION.map((n) => (
                <option key={n.value} value={n.value}>{n.label}</option>
              ))}
            </select>
            
            <button
              onClick={fetchData}
              className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg"
              title="Actualizar"
            >
              <RefreshCw className="w-5 h-5" />
            </button>
          </div>
          
          <div className="flex items-center gap-2">
            <button
              onClick={() => setModalResolver(true)}
              className="px-3 py-2 border border-blue-300 text-blue-600 rounded-lg hover:bg-blue-50 flex items-center gap-2 text-sm"
              data-testid="btn-resolver-regla"
            >
              <Eye className="w-4 h-4" />
              Resolver Regla
            </button>
            <button
              onClick={() => setModalEvaluar(true)}
              className="px-3 py-2 border border-purple-300 text-purple-600 rounded-lg hover:bg-purple-50 flex items-center gap-2 text-sm"
              data-testid="btn-evaluar-margen"
            >
              <Target className="w-4 h-4" />
              Evaluar Margen
            </button>
            <button
              onClick={() => setModalRegla({ open: true, regla: null })}
              className="px-4 py-2 bg-orange-600 text-white rounded-lg hover:bg-orange-700 flex items-center gap-2"
              data-testid="btn-nueva-regla"
            >
              <Plus className="w-4 h-4" />
              Nueva Regla
            </button>
          </div>
        </div>
      </div>
      
      {/* Tabla de Reglas */}
      <div className="bg-white rounded-lg shadow-sm border overflow-hidden">
        <table className="w-full">
          <thead className="bg-gray-50 border-b">
            <tr>
              <th className="text-left px-4 py-3 text-sm font-medium text-gray-600">Nivel</th>
              <th className="text-left px-4 py-3 text-sm font-medium text-gray-600">Código</th>
              <th className="text-center px-4 py-3 text-sm font-medium text-gray-600">Margen Esperado</th>
              <th className="text-center px-4 py-3 text-sm font-medium text-gray-600">Severidad</th>
              <th className="text-left px-4 py-3 text-sm font-medium text-gray-600">Descripción</th>
              <th className="text-center px-4 py-3 text-sm font-medium text-gray-600">Estado</th>
              <th className="text-center px-4 py-3 text-sm font-medium text-gray-600">Acciones</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {reglasFiltradas.length === 0 ? (
              <tr>
                <td colSpan={7} className="px-4 py-8 text-center text-gray-500">
                  No hay reglas configuradas
                </td>
              </tr>
            ) : (
              reglasFiltradas.map((regla) => (
                <tr key={regla.regla_id} className="hover:bg-gray-50">
                  <td className="px-4 py-3">
                    <NivelBadge nivel={regla.nivel_aplicacion} />
                  </td>
                  <td className="px-4 py-3 font-mono text-sm font-medium">
                    {regla.entidad_codigo}
                  </td>
                  <td className="px-4 py-3 text-center">
                    <span className="text-lg font-bold text-orange-600">
                      {formatPercent(regla.margen_esperado)}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-center">
                    <SeveridadBadge severidad={regla.severidad_base} />
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-600 max-w-xs truncate">
                    {regla.descripcion || '-'}
                  </td>
                  <td className="px-4 py-3 text-center">
                    {regla.activo ? (
                      <span className="inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs bg-green-100 text-green-700">
                        <CheckCircle className="w-3 h-3" />
                        Activa
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs bg-gray-100 text-gray-500">
                        <XCircle className="w-3 h-3" />
                        Inactiva
                      </span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-center">
                    <div className="flex items-center justify-center gap-1">
                      <button
                        onClick={() => setModalRegla({ open: true, regla })}
                        className="p-1.5 text-blue-600 hover:bg-blue-50 rounded"
                        title="Editar"
                      >
                        <Edit className="w-4 h-4" />
                      </button>
                      {regla.activo && (
                        <button
                          onClick={() => handleDesactivarRegla(regla)}
                          className="p-1.5 text-red-600 hover:bg-red-50 rounded"
                          title="Desactivar"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
      
      {/* Jerarquía Visual */}
      <div className="bg-gradient-to-r from-orange-50 to-amber-50 rounded-lg border border-orange-200 p-4">
        <h4 className="font-medium text-orange-800 mb-3 flex items-center gap-2">
          <Layers className="w-4 h-4" />
          Jerarquía de Resolución de Reglas
        </h4>
        <div className="flex items-center gap-3 text-sm">
          <div className="flex items-center gap-2 px-3 py-2 bg-orange-100 rounded-lg">
            <Target className="w-4 h-4 text-orange-600" />
            <span className="font-medium text-orange-700">PRODUCTO</span>
            <span className="text-orange-500">(más específico)</span>
          </div>
          <ChevronDown className="w-4 h-4 text-gray-400 rotate-[-90deg]" />
          <div className="flex items-center gap-2 px-3 py-2 bg-purple-100 rounded-lg">
            <Package className="w-4 h-4 text-purple-600" />
            <span className="font-medium text-purple-700">SUBFAMILIA</span>
          </div>
          <ChevronDown className="w-4 h-4 text-gray-400 rotate-[-90deg]" />
          <div className="flex items-center gap-2 px-3 py-2 bg-green-100 rounded-lg">
            <Package className="w-4 h-4 text-green-600" />
            <span className="font-medium text-green-700">FAMILIA</span>
          </div>
          <ChevronDown className="w-4 h-4 text-gray-400 rotate-[-90deg]" />
          <div className="flex items-center gap-2 px-3 py-2 bg-blue-100 rounded-lg">
            <Layers className="w-4 h-4 text-blue-600" />
            <span className="font-medium text-blue-700">GRUPO</span>
            <span className="text-blue-500">(más general)</span>
          </div>
        </div>
      </div>
      
      {/* Modales */}
      <ModalRegla
        isOpen={modalRegla.open}
        onClose={() => setModalRegla({ open: false, regla: null })}
        regla={modalRegla.regla}
        onSave={handleSaveRegla}
        loading={savingRegla}
      />
      
      <ModalResolverRegla
        isOpen={modalResolver}
        onClose={() => setModalResolver(false)}
      />
      
      <ModalEvaluarMargen
        isOpen={modalEvaluar}
        onClose={() => setModalEvaluar(false)}
      />
    </div>
  );
};

export default TabReglasMargen;
