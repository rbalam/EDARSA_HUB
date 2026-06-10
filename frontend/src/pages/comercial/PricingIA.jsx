/**
 * FASE 1C-3I-D: Frontend Motor de Precios Sugeridos IA y Benchmark
 * ==================================================================
 * Interfaz completa para gestionar competidores, capturar precios,
 * solicitar analisis IA y visualizar resultados de benchmark.
 * 
 * CONSUME ENDPOINTS:
 * - GET/POST /api/comercial/competidores/*
 * - GET/POST /api/comercial/competidores/{id}/menu-items/*
 * - POST /api/comercial/pricing-ai/analizar-producto
 * - POST /api/comercial/pricing-ai/analizar-benchmark
 * - GET /api/comercial/pricing-ai/analisis/{id}
 * - GET /api/comercial/benchmark/resumen/{unidad_id}
 * 
 * REGLAS:
 * - EDARSAHUB SQL es el cerebro
 * - CERO MongoDB
 * - El frontend NO llama directamente a GPT/OpenAI
 * - Toda llamada IA pasa por backend
 * - Las sugerencias IA son RECOMENDACIONES, no precios oficiales
 * - NO modificar precios oficiales
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
  Brain, Building2, DollarSign, BarChart2, RefreshCw, Search, Filter,
  Plus, Edit2, Trash2, Eye, AlertCircle, CheckCircle, Clock, X,
  AlertTriangle, TrendingUp, TrendingDown, ChevronDown, ChevronUp,
  Target, Sparkles, History, FileText, Users, Tag, ExternalLink,
  Zap, Info, ShieldAlert, ThumbsUp, ThumbsDown, Loader2, Store, Folder, Layers
} from 'lucide-react';
import api from '@/lib/api';
import TabBenchmarkSectorial from './TabBenchmarkSectorial';

// Importar componentes de visualización y listas (FASE 1C-3I-F y 1C-3I-G)
import {
  ChartAnalisisPorDia,
  ChartDistribucionConfianza,
  ChartProductosMasAnalizados,
  ExportButton,
  TabListasCompetidores
} from './PricingIACharts';

// ==================== UTILIDADES ====================

const formatCurrency = (value) => {
  if (value === null || value === undefined) return 'Sin dato';
  if (value === 0) return '$0.00';
  return new Intl.NumberFormat('es-MX', {
    style: 'currency',
    currency: 'MXN',
    minimumFractionDigits: 2
  }).format(value);
};

const formatPercent = (value) => {
  if (value === null || value === undefined) return 'Sin dato';
  return `${(value * 100).toFixed(1)}%`;
};

const formatDate = (dateStr) => {
  if (!dateStr) return 'Sin fecha';
  try {
    return new Date(dateStr).toLocaleString('es-MX', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  } catch {
    return dateStr;
  }
};

// ==================== BADGE DE CONFIANZA IA ====================

const ConfianzaBadge = ({ confianza, size = 'md' }) => {
  const config = {
    ALTA: { 
      bg: 'bg-green-100', 
      text: 'text-green-700', 
      border: 'border-green-300',
      icon: CheckCircle,
      label: 'Confianza Alta'
    },
    MEDIA: { 
      bg: 'bg-yellow-100', 
      text: 'text-yellow-700', 
      border: 'border-yellow-300',
      icon: AlertTriangle,
      label: 'Confianza Media'
    },
    BAJA: { 
      bg: 'bg-red-100', 
      text: 'text-red-700', 
      border: 'border-red-300',
      icon: AlertCircle,
      label: 'Confianza Baja'
    }
  };
  
  const cfg = config[confianza] || config.BAJA;
  const Icon = cfg.icon;
  const sizeClass = size === 'lg' ? 'px-3 py-1.5 text-sm' : 'px-2 py-1 text-xs';
  
  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full border ${cfg.bg} ${cfg.text} ${cfg.border} ${sizeClass} font-medium`}>
      <Icon className={size === 'lg' ? 'w-4 h-4' : 'w-3 h-3'} />
      {cfg.label}
    </span>
  );
};

// ==================== BADGE REVISION HUMANA ====================

const RevisionHumanaBadge = ({ requiere }) => {
  if (!requiere) return null;
  
  return (
    <span className="inline-flex items-center gap-1 px-2 py-1 rounded text-xs font-medium bg-orange-100 text-orange-700 border border-orange-300">
      <ShieldAlert className="w-3 h-3" />
      Requiere Revision Humana
    </span>
  );
};

// ==================== CARD DE RESUMEN ====================

const SummaryCard = ({ title, value, icon: Icon, color = 'blue', subtitle, onClick }) => (
  <div 
    className={`bg-white rounded-lg shadow-sm border border-gray-200 p-4 ${onClick ? 'cursor-pointer hover:shadow-md transition-shadow' : ''}`}
    onClick={onClick}
  >
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

// ==================== TABS ====================

const TabButton = ({ active, onClick, icon: Icon, label, badge }) => (
  <button
    onClick={onClick}
    className={`flex items-center gap-2 px-4 py-2.5 text-sm font-medium rounded-t-lg transition-colors
      ${active 
        ? 'bg-white text-blue-600 border-t border-l border-r border-gray-200 -mb-px' 
        : 'text-gray-500 hover:text-gray-700 hover:bg-gray-100'
      }`}
    data-testid={`tab-${label.toLowerCase().replace(/\s+/g, '-')}`}
  >
    <Icon className="w-4 h-4" />
    {label}
    {badge !== undefined && (
      <span className={`ml-1 px-1.5 py-0.5 text-xs rounded-full ${active ? 'bg-blue-100 text-blue-700' : 'bg-gray-200 text-gray-600'}`}>
        {badge}
      </span>
    )}
  </button>
);

// ==================== MODAL COMPETIDOR ====================

const CompetidorModal = ({ isOpen, onClose, competidor, onSave, loading }) => {
  const [form, setForm] = useState({
    nombre_competidor: '',
    tipo_restaurante: 'casual_dining',
    segmento_precio: 'MEDIO',
    zona_comercial: '',
    sitio_web: '',
    url_google_maps: '',
    url_instagram: '',
    url_facebook: '',
    url_tripadvisor: '',
    url_opentable: '',
    es_competencia_directa: true,
    es_benchmark_aspiracional: false,
    notas: ''
  });
  
  useEffect(() => {
    if (competidor) {
      setForm({
        nombre_competidor: competidor.nombre_competidor || '',
        tipo_restaurante: competidor.tipo_restaurante || 'casual_dining',
        segmento_precio: competidor.segmento_precio || 'MEDIO',
        zona_comercial: competidor.zona_comercial || '',
        sitio_web: competidor.sitio_web || '',
        url_google_maps: competidor.url_google_maps || '',
        url_instagram: competidor.url_instagram || '',
        url_facebook: competidor.url_facebook || '',
        url_tripadvisor: competidor.url_tripadvisor || '',
        url_opentable: competidor.url_opentable || '',
        es_competencia_directa: competidor.es_competencia_directa ?? true,
        es_benchmark_aspiracional: competidor.es_benchmark_aspiracional ?? false,
        notas: competidor.notas || ''
      });
    } else {
      setForm({
        nombre_competidor: '',
        tipo_restaurante: 'casual_dining',
        segmento_precio: 'MEDIO',
        zona_comercial: '',
        sitio_web: '',
        url_google_maps: '',
        url_instagram: '',
        url_facebook: '',
        url_tripadvisor: '',
        url_opentable: '',
        es_competencia_directa: true,
        es_benchmark_aspiracional: false,
        notas: ''
      });
    }
  }, [competidor, isOpen]);
  
  if (!isOpen) return null;
  
  const handleSubmit = (e) => {
    e.preventDefault();
    onSave(form);
  };
  
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-2xl max-h-[90vh] overflow-hidden">
        <div className="p-4 border-b flex justify-between items-center bg-gradient-to-r from-blue-600 to-blue-700">
          <h3 className="text-lg font-semibold text-white flex items-center gap-2">
            <Store className="w-5 h-5" />
            {competidor ? 'Editar Competidor' : 'Nuevo Competidor'}
          </h3>
          <button onClick={onClose} className="p-1 hover:bg-blue-800 rounded text-white">
            <X className="w-5 h-5" />
          </button>
        </div>
        
        <form onSubmit={handleSubmit} className="p-6 space-y-4 overflow-y-auto max-h-[calc(90vh-140px)]">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Nombre del Competidor *
            </label>
            <input
              type="text"
              value={form.nombre_competidor}
              onChange={(e) => setForm({ ...form, nombre_competidor: e.target.value })}
              placeholder="Ej: La Carniceria del Centro"
              required
              maxLength={200}
              className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              data-testid="input-nombre-competidor"
            />
          </div>
          
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Tipo de Negocio
              </label>
              <select
                value={form.tipo_restaurante}
                onChange={(e) => setForm({ ...form, tipo_restaurante: e.target.value })}
                className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="fine_dining">Fine Dining</option>
                <option value="casual_dining">Casual Dining</option>
                <option value="fast_casual">Fast Casual</option>
                <option value="quick_service">Quick Service</option>
                <option value="bar_restaurant">Bar Restaurant</option>
                <option value="steakhouse">Steakhouse</option>
                <option value="seafood">Seafood</option>
                <option value="mexican">Mexicano</option>
                <option value="international">Internacional</option>
                <option value="fusion">Fusion</option>
                <option value="otro">Otro</option>
              </select>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Nivel de Precio
              </label>
              <select
                value={form.segmento_precio}
                onChange={(e) => setForm({ ...form, segmento_precio: e.target.value })}
                className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="ECONOMICO">Economico</option>
                <option value="MEDIO">Medio</option>
                <option value="MEDIO_ALTO">Medio-Alto</option>
                <option value="PREMIUM">Premium</option>
                <option value="LUJO">Lujo</option>
              </select>
            </div>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Ubicacion de Referencia
            </label>
            <input
              type="text"
              value={form.zona_comercial}
              onChange={(e) => setForm({ ...form, zona_comercial: e.target.value })}
              placeholder="Ej: Col. Polanco, CDMX"
              maxLength={200}
              className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Sitio Web
            </label>
            <input
              type="url"
              value={form.sitio_web}
              onChange={(e) => setForm({ ...form, sitio_web: e.target.value })}
              placeholder="https://..."
              className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          
          {/* REDES SOCIALES Y MONITOREO */}
          <div className="border-t pt-4 mt-4">
            <label className="block text-sm font-medium text-gray-700 mb-3">
              Redes Sociales y Monitoreo
            </label>
            
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-xs text-gray-500 mb-1">Google Maps</label>
                <input
                  type="url"
                  value={form.url_google_maps}
                  onChange={(e) => setForm({ ...form, url_google_maps: e.target.value })}
                  placeholder="https://goo.gl/maps/..."
                  className="w-full px-3 py-2 text-sm border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              
              <div>
                <label className="block text-xs text-gray-500 mb-1">Instagram</label>
                <input
                  type="url"
                  value={form.url_instagram}
                  onChange={(e) => setForm({ ...form, url_instagram: e.target.value })}
                  placeholder="https://instagram.com/..."
                  className="w-full px-3 py-2 text-sm border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              
              <div>
                <label className="block text-xs text-gray-500 mb-1">Facebook</label>
                <input
                  type="url"
                  value={form.url_facebook}
                  onChange={(e) => setForm({ ...form, url_facebook: e.target.value })}
                  placeholder="https://facebook.com/..."
                  className="w-full px-3 py-2 text-sm border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              
              <div>
                <label className="block text-xs text-gray-500 mb-1">TripAdvisor</label>
                <input
                  type="url"
                  value={form.url_tripadvisor}
                  onChange={(e) => setForm({ ...form, url_tripadvisor: e.target.value })}
                  placeholder="https://tripadvisor.com/..."
                  className="w-full px-3 py-2 text-sm border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              
              <div className="col-span-2">
                <label className="block text-xs text-gray-500 mb-1">OpenTable</label>
                <input
                  type="url"
                  value={form.url_opentable}
                  onChange={(e) => setForm({ ...form, url_opentable: e.target.value })}
                  placeholder="https://opentable.com/..."
                  className="w-full px-3 py-2 text-sm border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>
          </div>
          
          <div className="flex gap-6">
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={form.es_competencia_directa}
                onChange={(e) => setForm({ ...form, es_competencia_directa: e.target.checked })}
                className="w-4 h-4 text-blue-600 rounded"
              />
              <span className="text-sm text-gray-700">Competencia Directa</span>
            </label>
            
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={form.es_benchmark_aspiracional}
                onChange={(e) => setForm({ ...form, es_benchmark_aspiracional: e.target.checked })}
                className="w-4 h-4 text-purple-600 rounded"
              />
              <span className="text-sm text-gray-700">Benchmark Aspiracional</span>
            </label>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Notas
            </label>
            <textarea
              value={form.notas}
              onChange={(e) => setForm({ ...form, notas: e.target.value })}
              placeholder="Observaciones adicionales..."
              rows={2}
              maxLength={1000}
              className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
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
            disabled={loading || !form.nombre_competidor}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            data-testid="btn-guardar-competidor"
          >
            {loading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <CheckCircle className="w-4 h-4" />}
            Guardar
          </button>
        </div>
      </div>
    </div>
  );
};

// ==================== MODAL MENU ITEM ====================

const MenuItemModal = ({ isOpen, onClose, menuItem, competidorId, onSave, loading }) => {
  const [form, setForm] = useState({
    nombre_producto_competidor: '',
    categoria_competidor: '',
    precio: '',
    unidad_medida: 'PIEZA',
    descripcion_producto: '',
    es_producto_premium: false,
    fecha_captura: new Date().toISOString().split('T')[0],
    notas: ''
  });
  
  useEffect(() => {
    if (menuItem) {
      setForm({
        nombre_producto_competidor: menuItem.nombre_producto_competidor || '',
        categoria_competidor: menuItem.categoria_competidor || '',
        precio: menuItem.precio?.toString() || '',
        unidad_medida: menuItem.unidad_medida || 'PIEZA',
        descripcion_producto: menuItem.descripcion_producto || '',
        es_producto_premium: menuItem.es_producto_premium ?? false,
        fecha_captura: menuItem.fecha_captura?.split('T')[0] || new Date().toISOString().split('T')[0],
        notas: menuItem.notas || ''
      });
    } else {
      setForm({
        nombre_producto_competidor: '',
        categoria_competidor: '',
        precio: '',
        unidad_medida: 'PIEZA',
        descripcion_producto: '',
        es_producto_premium: false,
        fecha_captura: new Date().toISOString().split('T')[0],
        notas: ''
      });
    }
  }, [menuItem, isOpen]);
  
  if (!isOpen) return null;
  
  const handleSubmit = (e) => {
    e.preventDefault();
    onSave({
      ...form,
      competidor_id: competidorId,
      precio: parseFloat(form.precio) || 0
    });
  };
  
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-lg max-h-[90vh] overflow-hidden">
        <div className="p-4 border-b flex justify-between items-center bg-gradient-to-r from-green-600 to-green-700">
          <h3 className="text-lg font-semibold text-white flex items-center gap-2">
            <Tag className="w-5 h-5" />
            {menuItem ? 'Editar Precio' : 'Capturar Precio'}
          </h3>
          <button onClick={onClose} className="p-1 hover:bg-green-800 rounded text-white">
            <X className="w-5 h-5" />
          </button>
        </div>
        
        <form onSubmit={handleSubmit} className="p-6 space-y-4 overflow-y-auto max-h-[calc(90vh-140px)]">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Nombre del Producto *
            </label>
            <input
              type="text"
              value={form.nombre_producto_competidor}
              onChange={(e) => setForm({ ...form, nombre_producto_competidor: e.target.value })}
              placeholder="Ej: Rib Eye 500g"
              required
              maxLength={300}
              className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
              data-testid="input-nombre-producto"
            />
          </div>
          
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Precio *
              </label>
              <div className="relative">
                <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500">$</span>
                <input
                  type="number"
                  value={form.precio}
                  onChange={(e) => setForm({ ...form, precio: e.target.value })}
                  placeholder="0.00"
                  required
                  min="0"
                  step="0.01"
                  className="w-full pl-8 pr-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
                  data-testid="input-precio"
                />
              </div>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Unidad
              </label>
              <select
                value={form.unidad_medida}
                onChange={(e) => setForm({ ...form, unidad_medida: e.target.value })}
                className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
              >
                <option value="PIEZA">Pieza</option>
                <option value="KG">Kilogramo</option>
                <option value="GR">Gramos</option>
                <option value="LT">Litro</option>
                <option value="ML">Mililitro</option>
                <option value="PORCION">Porcion</option>
              </select>
            </div>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Categoria
            </label>
            <input
              type="text"
              value={form.categoria_competidor}
              onChange={(e) => setForm({ ...form, categoria_competidor: e.target.value })}
              placeholder="Ej: Cortes Premium, Entradas, etc."
              maxLength={100}
              className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Descripcion
            </label>
            <textarea
              value={form.descripcion_producto}
              onChange={(e) => setForm({ ...form, descripcion_producto: e.target.value })}
              placeholder="Descripcion del producto..."
              rows={2}
              maxLength={500}
              className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500 resize-none"
            />
          </div>
          
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Fecha de Captura
              </label>
              <input
                type="date"
                value={form.fecha_captura}
                onChange={(e) => setForm({ ...form, fecha_captura: e.target.value })}
                className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
              />
            </div>
            
            <div className="flex items-end pb-2">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={form.es_producto_premium}
                  onChange={(e) => setForm({ ...form, es_producto_premium: e.target.checked })}
                  className="w-4 h-4 text-purple-600 rounded"
                />
                <span className="text-sm text-gray-700">Producto Premium</span>
              </label>
            </div>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Notas
            </label>
            <input
              type="text"
              value={form.notas}
              onChange={(e) => setForm({ ...form, notas: e.target.value })}
              placeholder="Observaciones..."
              maxLength={500}
              className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
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
            disabled={loading || !form.nombre_producto_competidor || !form.precio}
            className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            data-testid="btn-guardar-precio"
          >
            {loading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <DollarSign className="w-4 h-4" />}
            Guardar Precio
          </button>
        </div>
      </div>
    </div>
  );
};

// ==================== MODAL ANALISIS IA PRODUCTO ====================

const AnalisisIAProductoModal = ({ isOpen, onClose, onAnalizar, loading }) => {
  const [form, setForm] = useState({
    codigo_producto: '',
    server_id: '',
    empresa_id: 1,
    unidad_negocio_id: 1,
    margen_objetivo: 0.35,
    lista_id: ''
  });
  const [servidores, setServidores] = useState([]);
  const [listasCompetidores, setListasCompetidores] = useState([]);
  const [loadingListas, setLoadingListas] = useState(false);
  
  useEffect(() => {
    // Cargar servidores disponibles
    api.get('/servidores/list')
      .then(res => setServidores(res.data.servidores || res.data || []))
      .catch(() => setServidores([]));
    
    // Cargar listas de competidores
    setLoadingListas(true);
    api.get('/comercial/pricing/listas-competidores?activo=true')
      .then(res => setListasCompetidores(res.data.listas || []))
      .catch(() => setListasCompetidores([]))
      .finally(() => setLoadingListas(false));
  }, []);
  
  if (!isOpen) return null;
  
  const handleSubmit = (e) => {
    e.preventDefault();
    // Enviar lista_id solo si se seleccionó una
    const payload = { ...form };
    if (!payload.lista_id) {
      delete payload.lista_id;
    }
    onAnalizar(payload);
  };
  
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-md">
        <div className="p-4 border-b flex justify-between items-center bg-gradient-to-r from-purple-600 to-purple-700">
          <h3 className="text-lg font-semibold text-white flex items-center gap-2">
            <Brain className="w-5 h-5" />
            Analisis IA de Producto
          </h3>
          <button onClick={onClose} className="p-1 hover:bg-purple-800 rounded text-white">
            <X className="w-5 h-5" />
          </button>
        </div>
        
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div className="bg-purple-50 rounded-lg p-3 text-sm text-purple-700">
            <div className="flex items-start gap-2">
              <Info className="w-4 h-4 mt-0.5 flex-shrink-0" />
              <p>
                El analisis IA genera una <strong>RECOMENDACION</strong> de precio 
                basada en costos, margenes y benchmark de competencia. 
                No modifica precios oficiales.
              </p>
            </div>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Servidor / Unidad *
            </label>
            <select
              value={form.server_id}
              onChange={(e) => setForm({ ...form, server_id: e.target.value })}
              required
              className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
              data-testid="select-servidor"
            >
              <option value="">Seleccionar...</option>
              {servidores.map(s => (
                <option key={s.id || s.uuid} value={s.id || s.uuid}>
                  {s.nombre || s.name || s.id}
                </option>
              ))}
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Codigo de Producto *
            </label>
            <input
              type="text"
              value={form.codigo_producto}
              onChange={(e) => setForm({ ...form, codigo_producto: e.target.value })}
              placeholder="Ej: RIBEYE500, P-001"
              required
              className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
              data-testid="input-codigo-producto"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Margen Objetivo
            </label>
            <div className="flex items-center gap-2">
              <input
                type="range"
                min="0.1"
                max="0.6"
                step="0.05"
                value={form.margen_objetivo}
                onChange={(e) => setForm({ ...form, margen_objetivo: parseFloat(e.target.value) })}
                className="flex-1"
              />
              <span className="text-sm font-medium text-purple-600 w-14 text-right">
                {(form.margen_objetivo * 100).toFixed(0)}%
              </span>
            </div>
          </div>
          
          {/* Selector de Lista de Competidores */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              <span className="flex items-center gap-1">
                <Folder className="w-4 h-4" />
                Lista de Competidores (Opcional)
              </span>
            </label>
            <select
              value={form.lista_id}
              onChange={(e) => setForm({ ...form, lista_id: e.target.value })}
              className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
              data-testid="select-lista-competidores"
              disabled={loadingListas}
            >
              <option value="">Sin filtro (Benchmark general)</option>
              {listasCompetidores.map(lista => (
                <option key={lista.lista_id} value={lista.lista_id}>
                  {lista.nombre_lista} ({lista.total_competidores || 0} competidores)
                </option>
              ))}
            </select>
            <p className="text-xs text-gray-500 mt-1">
              {form.lista_id 
                ? 'El analisis solo usara competidores de la lista seleccionada' 
                : 'Se usaran todos los competidores configurados'}
            </p>
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
            disabled={loading || !form.codigo_producto || !form.server_id}
            className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            data-testid="btn-analizar-ia"
          >
            {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />}
            Analizar con IA
          </button>
        </div>
      </div>
    </div>
  );
};

// ==================== MODAL RESULTADO ANALISIS IA ====================

const ResultadoAnalisisModal = ({ isOpen, onClose, resultado }) => {
  if (!isOpen || !resultado) return null;
  
  const data = resultado.data || {};
  
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 overflow-y-auto py-4">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-2xl mx-4">
        <div className="p-4 border-b flex justify-between items-center bg-gradient-to-r from-purple-600 to-indigo-600">
          <h3 className="text-lg font-semibold text-white flex items-center gap-2">
            <Brain className="w-5 h-5" />
            Resultado Analisis IA
          </h3>
          <button onClick={onClose} className="p-1 hover:bg-purple-800 rounded text-white">
            <X className="w-5 h-5" />
          </button>
        </div>
        
        <div className="p-6 space-y-6 max-h-[70vh] overflow-y-auto">
          {/* Header con estado */}
          <div className={`p-4 rounded-lg ${resultado.success ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'}`}>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                {resultado.success ? (
                  <CheckCircle className="w-5 h-5 text-green-600" />
                ) : (
                  <AlertCircle className="w-5 h-5 text-red-600" />
                )}
                <span className={`font-medium ${resultado.success ? 'text-green-700' : 'text-red-700'}`}>
                  {resultado.mensaje}
                </span>
              </div>
              <span className="text-xs text-gray-500">Modelo: {resultado.modelo_ia}</span>
            </div>
          </div>
          
          {resultado.success && data && (
            <>
              {/* Producto */}
              <div className="bg-gray-50 rounded-lg p-4">
                <h4 className="font-semibold text-gray-800 mb-2">{data.producto}</h4>
                <div className="flex gap-4">
                  {data.confianza && <ConfianzaBadge confianza={data.confianza} size="lg" />}
                  {data.requiere_revision && <RevisionHumanaBadge requiere={true} />}
                </div>
              </div>
              
              {/* Comparacion de precios */}
              <div className="grid grid-cols-3 gap-4">
                <div className="bg-white border rounded-lg p-4 text-center">
                  <div className="text-xs text-gray-500 mb-1">Precio Actual</div>
                  <div className="text-xl font-bold text-gray-800">
                    {formatCurrency(data.precio_actual)}
                  </div>
                </div>
                <div className="bg-white border rounded-lg p-4 text-center">
                  <div className="text-xs text-gray-500 mb-1">Precio Base Calculado</div>
                  <div className="text-xl font-bold text-blue-600">
                    {formatCurrency(data.precio_base_calculado)}
                  </div>
                </div>
                <div className="bg-purple-50 border border-purple-200 rounded-lg p-4 text-center">
                  <div className="text-xs text-purple-600 mb-1 flex items-center justify-center gap-1">
                    <Sparkles className="w-3 h-3" />
                    Precio Sugerido IA
                  </div>
                  <div className="text-xl font-bold text-purple-700">
                    {formatCurrency(data.precio_sugerido_ia)}
                  </div>
                </div>
              </div>
              
              {/* Margenes */}
              <div className="grid grid-cols-2 gap-4">
                <div className="bg-white border rounded-lg p-4">
                  <div className="text-xs text-gray-500 mb-1">Margen Actual</div>
                  <div className={`text-lg font-semibold ${(data.margen_actual || 0) < 0.2 ? 'text-orange-600' : 'text-green-600'}`}>
                    {formatPercent(data.margen_actual)}
                  </div>
                </div>
                <div className="bg-white border rounded-lg p-4">
                  <div className="text-xs text-gray-500 mb-1">Margen Sugerido</div>
                  <div className="text-lg font-semibold text-purple-600">
                    {formatPercent(data.margen_sugerido)}
                  </div>
                </div>
              </div>
              
              {/* Justificacion */}
              {data.justificacion && (
                <div className="bg-blue-50 rounded-lg p-4">
                  <h5 className="font-semibold text-blue-800 mb-2 flex items-center gap-2">
                    <FileText className="w-4 h-4" />
                    Justificacion IA
                  </h5>
                  <p className="text-blue-700 text-sm whitespace-pre-wrap">{data.justificacion}</p>
                </div>
              )}
              
              {/* Posicionamiento */}
              {data.posicionamiento && (
                <div className="bg-gray-50 rounded-lg p-4">
                  <h5 className="font-semibold text-gray-800 mb-2 flex items-center gap-2">
                    <Target className="w-4 h-4" />
                    Posicionamiento vs Competencia
                  </h5>
                  <p className="text-gray-700 text-sm">{data.posicionamiento}</p>
                </div>
              )}
              
              {/* Recomendacion */}
              {data.recomendacion && (
                <div className={`rounded-lg p-4 ${
                  data.recomendacion === 'APROBAR' ? 'bg-green-50 border border-green-200' :
                  data.recomendacion === 'REVISAR' ? 'bg-yellow-50 border border-yellow-200' :
                  'bg-red-50 border border-red-200'
                }`}>
                  <h5 className={`font-semibold mb-1 flex items-center gap-2 ${
                    data.recomendacion === 'APROBAR' ? 'text-green-800' :
                    data.recomendacion === 'REVISAR' ? 'text-yellow-800' :
                    'text-red-800'
                  }`}>
                    {data.recomendacion === 'APROBAR' ? <ThumbsUp className="w-4 h-4" /> :
                     data.recomendacion === 'REVISAR' ? <AlertTriangle className="w-4 h-4" /> :
                     <ThumbsDown className="w-4 h-4" />}
                    Recomendacion: {data.recomendacion}
                  </h5>
                </div>
              )}
              
              {/* Observaciones */}
              {data.observaciones && (
                <div className="text-sm text-gray-600 bg-gray-50 rounded p-3">
                  <span className="font-medium">Observaciones:</span> {data.observaciones}
                </div>
              )}
              
              {/* Lista de competidores usada */}
              {data.lista_usada && (
                <div className="text-sm bg-indigo-50 border border-indigo-200 rounded p-3 flex items-center gap-2">
                  <Folder className="w-4 h-4 text-indigo-600" />
                  <span className="text-indigo-700">
                    <span className="font-medium">Filtrado por lista:</span> {data.lista_usada.nombre_lista} 
                    ({data.lista_usada.total_competidores} competidores)
                  </span>
                </div>
              )}
              
              {/* ID del analisis */}
              {resultado.analisis_id && (
                <div className="text-xs text-gray-400 flex items-center gap-1">
                  <History className="w-3 h-3" />
                  ID Analisis: {resultado.analisis_id}
                </div>
              )}
            </>
          )}
        </div>
        
        <div className="p-4 border-t bg-gray-50 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700"
          >
            Cerrar
          </button>
        </div>
      </div>
    </div>
  );
};

// ==================== MODAL ANALISIS BENCHMARK IA ====================

const AnalisisBenchmarkModal = ({ isOpen, onClose, onAnalizar, loading }) => {
  const [listaId, setListaId] = useState('');
  const [listasCompetidores, setListasCompetidores] = useState([]);
  const [loadingListas, setLoadingListas] = useState(false);
  
  useEffect(() => {
    if (isOpen) {
      // Cargar listas de competidores
      setLoadingListas(true);
      api.get('/comercial/pricing/listas-competidores?activo=true')
        .then(res => setListasCompetidores(res.data.listas || []))
        .catch(() => setListasCompetidores([]))
        .finally(() => setLoadingListas(false));
    }
  }, [isOpen]);
  
  if (!isOpen) return null;
  
  const handleSubmit = (e) => {
    e.preventDefault();
    onAnalizar(listaId || null);
  };
  
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-md">
        <div className="p-4 border-b flex justify-between items-center bg-gradient-to-r from-indigo-600 to-indigo-700">
          <h3 className="text-lg font-semibold text-white flex items-center gap-2">
            <BarChart2 className="w-5 h-5" />
            Analisis Benchmark IA
          </h3>
          <button onClick={onClose} className="p-1 hover:bg-indigo-800 rounded text-white">
            <X className="w-5 h-5" />
          </button>
        </div>
        
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div className="bg-indigo-50 rounded-lg p-3 text-sm text-indigo-700">
            <div className="flex items-start gap-2">
              <Info className="w-4 h-4 mt-0.5 flex-shrink-0" />
              <p>
                El analisis de benchmark evalua el <strong>posicionamiento de precios</strong> de 
                tu unidad vs la competencia. Genera insights sobre oportunidades y riesgos.
              </p>
            </div>
          </div>
          
          {/* Selector de Lista de Competidores */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              <span className="flex items-center gap-1">
                <Folder className="w-4 h-4" />
                Lista de Competidores
              </span>
            </label>
            <select
              value={listaId}
              onChange={(e) => setListaId(e.target.value)}
              className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
              data-testid="select-lista-benchmark"
              disabled={loadingListas}
            >
              <option value="">Benchmark General (todos los competidores)</option>
              {listasCompetidores.map(lista => (
                <option key={lista.lista_id} value={lista.lista_id}>
                  {lista.nombre_lista} ({lista.total_competidores || 0} competidores)
                </option>
              ))}
            </select>
            <p className="text-xs text-gray-500 mt-1">
              {listaId 
                ? 'Solo se analizaran los competidores de la lista seleccionada' 
                : 'Se incluiran todos los competidores configurados en el benchmark'}
            </p>
          </div>
          
          {/* Info adicional */}
          <div className="bg-gray-50 rounded-lg p-3 text-xs text-gray-600">
            <p className="font-medium mb-1">El benchmark incluye:</p>
            <ul className="list-disc list-inside space-y-1">
              <li>Evaluacion de posicionamiento vs competencia</li>
              <li>Identificacion de oportunidades</li>
              <li>Deteccion de riesgos</li>
              <li>Recomendaciones estrategicas</li>
            </ul>
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
            disabled={loading}
            className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            data-testid="btn-ejecutar-benchmark"
          >
            {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <BarChart2 className="w-4 h-4" />}
            Ejecutar Benchmark
          </button>
        </div>
      </div>
    </div>
  );
};

// ==================== TAB COMPETIDORES ====================

const TabCompetidores = ({ empresaId, unidadId }) => {
  const [competidores, setCompetidores] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [modalOpen, setModalOpen] = useState(false);
  const [selectedCompetidor, setSelectedCompetidor] = useState(null);
  const [saving, setSaving] = useState(false);
  const [busqueda, setBusqueda] = useState('');
  
  const cargarCompetidores = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams();
      if (empresaId) params.append('empresa_id', empresaId);
      if (unidadId) params.append('unidad_negocio_id', unidadId);
      params.append('page_size', '100');
      
      const res = await api.get(`/comercial/competidores?${params}`);
      setCompetidores(res.data.competidores || []);
    } catch (err) {
      setError(err.response?.data?.detail || err.message);
    } finally {
      setLoading(false);
    }
  }, [empresaId, unidadId]);
  
  useEffect(() => {
    cargarCompetidores();
  }, [cargarCompetidores]);
  
  const handleSaveCompetidor = async (form) => {
    setSaving(true);
    try {
      const payload = {
        ...form,
        empresa_id: empresaId || 1,
        unidad_negocio_id: unidadId || 1
      };
      
      if (selectedCompetidor) {
        await api.put(`/comercial/competidores/${selectedCompetidor.competidor_id}`, payload);
      } else {
        await api.post('/comercial/competidores', payload);
      }
      
      setModalOpen(false);
      setSelectedCompetidor(null);
      cargarCompetidores();
    } catch (err) {
      alert('Error: ' + (err.response?.data?.detail || err.message));
    } finally {
      setSaving(false);
    }
  };
  
  const handleDeleteCompetidor = async (id) => {
    if (!window.confirm('Esta seguro de inactivar este competidor?')) return;
    
    try {
      await api.delete(`/comercial/competidores/${id}`);
      cargarCompetidores();
    } catch (err) {
      alert('Error: ' + (err.response?.data?.detail || err.message));
    }
  };
  
  const competidoresFiltrados = busqueda 
    ? competidores.filter(c => 
        c.nombre_competidor?.toLowerCase().includes(busqueda.toLowerCase()) ||
        c.tipo_negocio?.toLowerCase().includes(busqueda.toLowerCase())
      )
    : competidores;
  
  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            type="text"
            value={busqueda}
            onChange={(e) => setBusqueda(e.target.value)}
            placeholder="Buscar competidor..."
            className="w-full pl-10 pr-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            data-testid="search-competidores"
          />
        </div>
        
        <div className="flex gap-2">
          <button
            onClick={cargarCompetidores}
            disabled={loading}
            className="p-2 border rounded-lg hover:bg-gray-50 transition-colors"
            title="Recargar"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
          <button
            onClick={() => { setSelectedCompetidor(null); setModalOpen(true); }}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            data-testid="btn-nuevo-competidor"
          >
            <Plus className="w-4 h-4" />
            Nuevo Competidor
          </button>
        </div>
      </div>
      
      {/* Error */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700 flex items-center gap-2">
          <AlertCircle className="w-5 h-5" />
          {error}
        </div>
      )}
      
      {/* Lista */}
      {loading ? (
        <div className="flex justify-center py-12">
          <RefreshCw className="w-8 h-8 animate-spin text-blue-500" />
        </div>
      ) : competidoresFiltrados.length === 0 ? (
        <div className="text-center py-12 text-gray-500">
          <Store className="w-12 h-12 mx-auto mb-4 opacity-50" />
          <p>No hay competidores registrados</p>
          <p className="text-sm">Agregue competidores para iniciar el benchmark</p>
        </div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {competidoresFiltrados.map((comp) => (
            <div 
              key={comp.competidor_id} 
              className="bg-white border rounded-lg p-4 hover:shadow-md transition-shadow"
              data-testid={`competidor-${comp.competidor_id}`}
            >
              <div className="flex justify-between items-start mb-3">
                <div>
                  <h4 className="font-semibold text-gray-800">{comp.nombre_competidor}</h4>
                  <p className="text-sm text-gray-500">{comp.tipo_restaurante || 'Sin tipo'}</p>
                </div>
                <div className="flex gap-1">
                  <button
                    onClick={() => { setSelectedCompetidor(comp); setModalOpen(true); }}
                    className="p-1.5 hover:bg-gray-100 rounded"
                    title="Editar"
                  >
                    <Edit2 className="w-4 h-4 text-gray-500" />
                  </button>
                  <button
                    onClick={() => handleDeleteCompetidor(comp.competidor_id)}
                    className="p-1.5 hover:bg-red-50 rounded"
                    title="Eliminar"
                  >
                    <Trash2 className="w-4 h-4 text-red-500" />
                  </button>
                </div>
              </div>
              
              <div className="flex flex-wrap gap-2 mb-3">
                {comp.es_competencia_directa && (
                  <span className="px-2 py-0.5 text-xs rounded bg-blue-100 text-blue-700">
                    Competencia Directa
                  </span>
                )}
                {comp.es_benchmark_aspiracional && (
                  <span className="px-2 py-0.5 text-xs rounded bg-purple-100 text-purple-700">
                    Aspiracional
                  </span>
                )}
                <span className={`px-2 py-0.5 text-xs rounded ${
                  comp.segmento_precio === 'ECONOMICO' ? 'bg-green-100 text-green-700' :
                  comp.segmento_precio === 'MEDIO' ? 'bg-yellow-100 text-yellow-700' :
                  comp.segmento_precio === 'MEDIO_ALTO' ? 'bg-amber-100 text-amber-700' :
                  comp.segmento_precio === 'PREMIUM' ? 'bg-orange-100 text-orange-700' :
                  'bg-red-100 text-red-700'
                }`}>
                  {comp.segmento_precio || 'Sin definir'}
                </span>
              </div>
              
              {comp.zona_comercial && (
                <p className="text-xs text-gray-400 truncate">{comp.zona_comercial}</p>
              )}
              
              <div className="mt-3 pt-3 border-t text-xs text-gray-400">
                Items capturados: {comp.total_items || 0}
              </div>
            </div>
          ))}
        </div>
      )}
      
      {/* Modal */}
      <CompetidorModal
        isOpen={modalOpen}
        onClose={() => { setModalOpen(false); setSelectedCompetidor(null); }}
        competidor={selectedCompetidor}
        onSave={handleSaveCompetidor}
        loading={saving}
      />
    </div>
  );
};

// ==================== TAB PRECIOS COMPETENCIA ====================

const TabPreciosCompetencia = ({ empresaId, unidadId }) => {
  const [competidores, setCompetidores] = useState([]);
  const [selectedCompetidor, setSelectedCompetidor] = useState(null);
  const [menuItems, setMenuItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [loadingItems, setLoadingItems] = useState(false);
  const [error, setError] = useState(null);
  const [modalOpen, setModalOpen] = useState(false);
  const [selectedItem, setSelectedItem] = useState(null);
  const [saving, setSaving] = useState(false);
  const [busqueda, setBusqueda] = useState('');
  
  // Cargar competidores
  useEffect(() => {
    const cargar = async () => {
      setLoading(true);
      try {
        const params = new URLSearchParams();
        if (empresaId) params.append('empresa_id', empresaId);
        params.append('page_size', '100');
        
        const res = await api.get(`/comercial/competidores?${params}`);
        const comps = res.data.competidores || [];
        setCompetidores(comps);
        if (comps.length > 0 && !selectedCompetidor) {
          setSelectedCompetidor(comps[0]);
        }
      } catch (err) {
        setError(err.response?.data?.detail || err.message);
      } finally {
        setLoading(false);
      }
    };
    cargar();
  }, [empresaId, unidadId]);
  
  // Cargar items del competidor seleccionado
  useEffect(() => {
    if (!selectedCompetidor) {
      setMenuItems([]);
      return;
    }
    
    const cargarItems = async () => {
      setLoadingItems(true);
      try {
        const res = await api.get(`/comercial/competidores/${selectedCompetidor.competidor_id}/menu-items?page_size=200`);
        setMenuItems(res.data.menu_items || []);
      } catch (err) {
        console.error('Error cargando items:', err);
        setMenuItems([]);
      } finally {
        setLoadingItems(false);
      }
    };
    cargarItems();
  }, [selectedCompetidor]);
  
  const handleSaveItem = async (form) => {
    setSaving(true);
    try {
      if (selectedItem) {
        await api.put(`/comercial/competidores/menu-items/${selectedItem.menu_item_id}`, form);
      } else {
        await api.post(`/comercial/competidores/${selectedCompetidor.competidor_id}/menu-items`, form);
      }
      
      setModalOpen(false);
      setSelectedItem(null);
      
      // Recargar items
      const res = await api.get(`/comercial/competidores/${selectedCompetidor.competidor_id}/menu-items?page_size=200`);
      setMenuItems(res.data.menu_items || []);
    } catch (err) {
      alert('Error: ' + (err.response?.data?.detail || err.message));
    } finally {
      setSaving(false);
    }
  };
  
  const handleDeleteItem = async (id) => {
    if (!window.confirm('Esta seguro de eliminar este precio?')) return;
    
    try {
      await api.delete(`/comercial/competidores/menu-items/${id}`);
      setMenuItems(prev => prev.filter(i => i.menu_item_id !== id));
    } catch (err) {
      alert('Error: ' + (err.response?.data?.detail || err.message));
    }
  };
  
  const itemsFiltrados = busqueda
    ? menuItems.filter(i => 
        i.nombre_producto_competidor?.toLowerCase().includes(busqueda.toLowerCase()) ||
        i.categoria_competidor?.toLowerCase().includes(busqueda.toLowerCase())
      )
    : menuItems;
  
  if (loading) {
    return (
      <div className="flex justify-center py-12">
        <RefreshCw className="w-8 h-8 animate-spin text-blue-500" />
      </div>
    );
  }
  
  if (competidores.length === 0) {
    return (
      <div className="text-center py-12 text-gray-500">
        <Store className="w-12 h-12 mx-auto mb-4 opacity-50" />
        <p>No hay competidores registrados</p>
        <p className="text-sm">Primero agregue competidores en la pestana anterior</p>
      </div>
    );
  }
  
  return (
    <div className="space-y-4">
      {/* Selector de competidor */}
      <div className="flex flex-col sm:flex-row gap-4">
        <div className="sm:w-64">
          <label className="block text-sm font-medium text-gray-700 mb-1">Competidor</label>
          <select
            value={selectedCompetidor?.competidor_id || ''}
            onChange={(e) => {
              const comp = competidores.find(c => c.competidor_id === e.target.value);
              setSelectedCompetidor(comp);
            }}
            className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            data-testid="select-competidor"
          >
            {competidores.map(c => (
              <option key={c.competidor_id} value={c.competidor_id}>
                {c.nombre_competidor}
              </option>
            ))}
          </select>
        </div>
        
        <div className="relative flex-1">
          <label className="block text-sm font-medium text-gray-700 mb-1">Buscar</label>
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              value={busqueda}
              onChange={(e) => setBusqueda(e.target.value)}
              placeholder="Buscar producto..."
              className="w-full pl-10 pr-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>
        
        <div className="flex items-end">
          <button
            onClick={() => { setSelectedItem(null); setModalOpen(true); }}
            disabled={!selectedCompetidor}
            className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 transition-colors"
            data-testid="btn-capturar-precio"
          >
            <Plus className="w-4 h-4" />
            Capturar Precio
          </button>
        </div>
      </div>
      
      {/* Info del competidor */}
      {selectedCompetidor && (
        <div className="bg-blue-50 rounded-lg p-4 flex items-center justify-between">
          <div>
            <h4 className="font-semibold text-blue-800">{selectedCompetidor.nombre_competidor}</h4>
            <p className="text-sm text-blue-600">
              {selectedCompetidor.tipo_restaurante || 'Sin tipo'} | {selectedCompetidor.segmento_precio || 'Sin precio'}
            </p>
          </div>
          <div className="text-right">
            <div className="text-2xl font-bold text-blue-700">{menuItems.length}</div>
            <div className="text-xs text-blue-600">precios capturados</div>
          </div>
        </div>
      )}
      
      {/* Lista de items */}
      {loadingItems ? (
        <div className="flex justify-center py-8">
          <RefreshCw className="w-6 h-6 animate-spin text-gray-400" />
        </div>
      ) : itemsFiltrados.length === 0 ? (
        <div className="text-center py-8 text-gray-500">
          <DollarSign className="w-10 h-10 mx-auto mb-3 opacity-50" />
          <p>No hay precios capturados para este competidor</p>
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-gray-100">
              <tr>
                <th className="p-3 text-left">Producto</th>
                <th className="p-3 text-left">Categoria</th>
                <th className="p-3 text-right">Precio</th>
                <th className="p-3 text-center">Unidad</th>
                <th className="p-3 text-center">Premium</th>
                <th className="p-3 text-left">Fecha</th>
                <th className="p-3 text-center">Acciones</th>
              </tr>
            </thead>
            <tbody>
              {itemsFiltrados.map((item) => (
                <tr key={item.menu_item_id} className="border-b hover:bg-gray-50">
                  <td className="p-3">
                    <div className="font-medium text-gray-800">{item.nombre_producto_competidor}</div>
                    {item.descripcion_producto && (
                      <div className="text-xs text-gray-500 truncate max-w-xs">{item.descripcion_producto}</div>
                    )}
                  </td>
                  <td className="p-3 text-gray-600">{item.categoria_competidor || '-'}</td>
                  <td className="p-3 text-right font-semibold text-green-600">{formatCurrency(item.precio)}</td>
                  <td className="p-3 text-center text-gray-500">{item.unidad_medida}</td>
                  <td className="p-3 text-center">
                    {item.es_producto_premium && (
                      <span className="px-2 py-0.5 text-xs rounded bg-purple-100 text-purple-700">Premium</span>
                    )}
                  </td>
                  <td className="p-3 text-gray-500 text-xs">{formatDate(item.fecha_captura)}</td>
                  <td className="p-3 text-center">
                    <div className="flex justify-center gap-1">
                      <button
                        onClick={() => { setSelectedItem(item); setModalOpen(true); }}
                        className="p-1.5 hover:bg-gray-100 rounded"
                        title="Editar"
                      >
                        <Edit2 className="w-4 h-4 text-gray-500" />
                      </button>
                      <button
                        onClick={() => handleDeleteItem(item.menu_item_id)}
                        className="p-1.5 hover:bg-red-50 rounded"
                        title="Eliminar"
                      >
                        <Trash2 className="w-4 h-4 text-red-500" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      
      {/* Modal */}
      <MenuItemModal
        isOpen={modalOpen}
        onClose={() => { setModalOpen(false); setSelectedItem(null); }}
        menuItem={selectedItem}
        competidorId={selectedCompetidor?.competidor_id}
        onSave={handleSaveItem}
        loading={saving}
      />
    </div>
  );
};

// ==================== TAB ANALISIS IA ====================

const TabAnalisisIA = ({ empresaId, unidadId }) => {
  const [modalProductoOpen, setModalProductoOpen] = useState(false);
  const [modalBenchmarkOpen, setModalBenchmarkOpen] = useState(false);
  const [analizando, setAnalizando] = useState(false);
  const [analizandoBenchmark, setAnalizandoBenchmark] = useState(false);
  const [resultado, setResultado] = useState(null);
  const [resultadoModalOpen, setResultadoModalOpen] = useState(false);
  const [historial, setHistorial] = useState([]);
  const [loadingHistorial, setLoadingHistorial] = useState(false);
  
  const handleAnalizarProducto = async (form) => {
    setAnalizando(true);
    try {
      const res = await api.post('/comercial/pricing-ai/analizar-producto', {
        ...form,
        empresa_id: empresaId || form.empresa_id || 1,
        unidad_negocio_id: unidadId || form.unidad_negocio_id || 1
      });
      
      setResultado(res.data);
      setModalProductoOpen(false);
      setResultadoModalOpen(true);
    } catch (err) {
      alert('Error en analisis: ' + (err.response?.data?.detail || err.message));
    } finally {
      setAnalizando(false);
    }
  };
  
  const handleAnalizarBenchmark = async (listaId = null) => {
    if (!empresaId || !unidadId) {
      alert('Seleccione una unidad de negocio primero');
      return;
    }
    
    setAnalizandoBenchmark(true);
    setModalBenchmarkOpen(false);
    try {
      const payload = {
        empresa_id: empresaId,
        unidad_negocio_id: unidadId
      };
      // Incluir lista_id solo si se selecciono
      if (listaId) {
        payload.lista_id = listaId;
      }
      
      const res = await api.post('/comercial/pricing-ai/analizar-benchmark', payload);
      
      setResultado(res.data);
      setResultadoModalOpen(true);
    } catch (err) {
      alert('Error en analisis benchmark: ' + (err.response?.data?.detail || err.message));
    } finally {
      setAnalizandoBenchmark(false);
    }
  };
  
  return (
    <div className="space-y-6">
      {/* Header con acciones */}
      <div className="bg-gradient-to-r from-purple-600 to-indigo-600 rounded-lg p-6 text-white">
        <div className="flex items-start justify-between">
          <div>
            <h3 className="text-xl font-bold flex items-center gap-2">
              <Brain className="w-6 h-6" />
              Motor de Precios con IA
            </h3>
            <p className="mt-2 text-purple-100 text-sm">
              Analiza productos y benchmark competitivo usando GPT-5.2. 
              Las sugerencias son <strong>recomendaciones</strong>, no precios oficiales.
            </p>
          </div>
          <div className="flex flex-col gap-2">
            <button
              onClick={() => setModalProductoOpen(true)}
              disabled={analizando}
              className="flex items-center gap-2 px-4 py-2 bg-white text-purple-700 rounded-lg hover:bg-purple-50 font-medium transition-colors"
              data-testid="btn-analizar-producto"
            >
              {analizando ? <Loader2 className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />}
              Analizar Producto
            </button>
            <button
              onClick={() => setModalBenchmarkOpen(true)}
              disabled={analizandoBenchmark}
              className="flex items-center gap-2 px-4 py-2 bg-purple-800 text-white rounded-lg hover:bg-purple-900 font-medium transition-colors"
              data-testid="btn-analizar-benchmark"
            >
              {analizandoBenchmark ? <Loader2 className="w-4 h-4 animate-spin" /> : <BarChart2 className="w-4 h-4" />}
              Analizar Benchmark
            </button>
          </div>
        </div>
      </div>
      
      {/* Info de reglas */}
      <div className="grid sm:grid-cols-3 gap-4">
        <div className="bg-green-50 border border-green-200 rounded-lg p-4">
          <div className="flex items-center gap-2 text-green-700 font-medium mb-2">
            <CheckCircle className="w-4 h-4" />
            IA Sugiere
          </div>
          <p className="text-sm text-green-600">
            La IA genera recomendaciones de precios basadas en datos reales de EDARSAHUB
          </p>
        </div>
        
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-center gap-2 text-red-700 font-medium mb-2">
            <AlertCircle className="w-4 h-4" />
            IA NO Modifica
          </div>
          <p className="text-sm text-red-600">
            La IA no tiene permiso para modificar precios oficiales ni crear solicitudes automaticas
          </p>
        </div>
        
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div className="flex items-center gap-2 text-blue-700 font-medium mb-2">
            <ShieldAlert className="w-4 h-4" />
            Revision Humana
          </div>
          <p className="text-sm text-blue-600">
            Las sugerencias con confianza MEDIA o BAJA requieren revision humana obligatoria
          </p>
        </div>
      </div>
      
      {/* Guia de uso */}
      <div className="bg-gray-50 rounded-lg p-6">
        <h4 className="font-semibold text-gray-800 mb-4">Como usar el Motor de Precios IA</h4>
        <div className="grid sm:grid-cols-2 gap-6">
          <div>
            <h5 className="font-medium text-gray-700 mb-2 flex items-center gap-2">
              <span className="w-6 h-6 rounded-full bg-purple-600 text-white text-sm flex items-center justify-center">1</span>
              Analisis de Producto Individual
            </h5>
            <p className="text-sm text-gray-600 ml-8">
              Seleccione un producto por codigo y la IA analizara su costo, precio actual, 
              margen y comparara con la competencia para sugerir un precio optimo.
            </p>
          </div>
          
          <div>
            <h5 className="font-medium text-gray-700 mb-2 flex items-center gap-2">
              <span className="w-6 h-6 rounded-full bg-indigo-600 text-white text-sm flex items-center justify-center">2</span>
              Analisis de Benchmark General
            </h5>
            <p className="text-sm text-gray-600 ml-8">
              La IA evaluara el posicionamiento general de la unidad vs sus competidores, 
              identificando oportunidades y riesgos en la estrategia de precios.
            </p>
          </div>
        </div>
      </div>
      
      {/* Levels de confianza */}
      <div className="bg-white border rounded-lg p-6">
        <h4 className="font-semibold text-gray-800 mb-4">Niveles de Confianza IA</h4>
        <div className="grid sm:grid-cols-3 gap-4">
          <div className="flex items-start gap-3">
            <ConfianzaBadge confianza="ALTA" />
            <div className="text-sm text-gray-600">
              Datos completos, benchmark robusto, margen consistente
            </div>
          </div>
          <div className="flex items-start gap-3">
            <ConfianzaBadge confianza="MEDIA" />
            <div className="text-sm text-gray-600">
              Datos parciales o variabilidad moderada. Requiere revision
            </div>
          </div>
          <div className="flex items-start gap-3">
            <ConfianzaBadge confianza="BAJA" />
            <div className="text-sm text-gray-600">
              Datos insuficientes o inconsistentes. Revision obligatoria
            </div>
          </div>
        </div>
      </div>
      
      {/* Modales */}
      <AnalisisIAProductoModal
        isOpen={modalProductoOpen}
        onClose={() => setModalProductoOpen(false)}
        onAnalizar={handleAnalizarProducto}
        loading={analizando}
      />
      
      <AnalisisBenchmarkModal
        isOpen={modalBenchmarkOpen}
        onClose={() => setModalBenchmarkOpen(false)}
        onAnalizar={handleAnalizarBenchmark}
        loading={analizandoBenchmark}
      />
      
      <ResultadoAnalisisModal
        isOpen={resultadoModalOpen}
        onClose={() => setResultadoModalOpen(false)}
        resultado={resultado}
      />
    </div>
  );
};

// ==================== TAB HISTORIAL ====================

const TabHistorial = ({ empresaId, unidadId }) => {
  const [analisis, setAnalisis] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedId, setSelectedId] = useState(null);
  const [detalle, setDetalle] = useState(null);
  const [loadingDetalle, setLoadingDetalle] = useState(false);
  
  // Por ahora mostramos mensaje informativo ya que el endpoint de listar historial 
  // no esta implementado en esta fase
  
  useEffect(() => {
    // Simular carga - en produccion se conectaria al endpoint de historial
    setLoading(false);
    setAnalisis([]);
  }, []);
  
  const cargarDetalle = async (id) => {
    setLoadingDetalle(true);
    setSelectedId(id);
    try {
      const res = await api.get(`/comercial/pricing-ai/analisis/${id}`);
      setDetalle(res.data.analisis);
    } catch (err) {
      setError('Error cargando detalle: ' + (err.response?.data?.detail || err.message));
    } finally {
      setLoadingDetalle(false);
    }
  };
  
  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h3 className="text-lg font-semibold text-gray-800 flex items-center gap-2">
          <History className="w-5 h-5" />
          Historial de Analisis IA
        </h3>
      </div>
      
      {loading ? (
        <div className="flex justify-center py-12">
          <RefreshCw className="w-8 h-8 animate-spin text-blue-500" />
        </div>
      ) : analisis.length === 0 ? (
        <div className="text-center py-12 bg-gray-50 rounded-lg">
          <History className="w-12 h-12 mx-auto mb-4 text-gray-400" />
          <p className="text-gray-600">No hay analisis en el historial</p>
          <p className="text-sm text-gray-500 mt-2">
            Los analisis realizados con IA se guardaran automaticamente en la tabla 
            <code className="bg-gray-200 px-1 rounded mx-1">Comercial_PricingAnalisisIA</code>
            de EDARSAHUB SQL
          </p>
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-gray-100">
              <tr>
                <th className="p-3 text-left">Fecha</th>
                <th className="p-3 text-left">Tipo</th>
                <th className="p-3 text-left">Producto</th>
                <th className="p-3 text-center">Confianza</th>
                <th className="p-3 text-center">Revision</th>
                <th className="p-3 text-center">Acciones</th>
              </tr>
            </thead>
            <tbody>
              {analisis.map((a) => (
                <tr key={a.analisis_id} className="border-b hover:bg-gray-50">
                  <td className="p-3 text-gray-600">{formatDate(a.fecha_creacion)}</td>
                  <td className="p-3">{a.tipo_analisis}</td>
                  <td className="p-3 font-medium">{a.producto_nombre || a.codigo_producto}</td>
                  <td className="p-3 text-center">
                    <ConfianzaBadge confianza={a.confianza_ia} />
                  </td>
                  <td className="p-3 text-center">
                    {a.requiere_revision_humana && <RevisionHumanaBadge requiere={true} />}
                  </td>
                  <td className="p-3 text-center">
                    <button
                      onClick={() => cargarDetalle(a.analisis_id)}
                      className="p-1.5 hover:bg-blue-50 rounded text-blue-600"
                      title="Ver detalle"
                    >
                      <Eye className="w-4 h-4" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      
      {/* Info sobre persistencia */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 text-sm">
        <div className="flex items-start gap-2">
          <Info className="w-4 h-4 mt-0.5 text-blue-600 flex-shrink-0" />
          <div className="text-blue-700">
            <strong>Auditoria SQL:</strong> Todos los analisis IA se guardan en la tabla 
            <code className="bg-blue-100 px-1 rounded mx-1">Comercial_PricingAnalisisIA</code>
            de EDARSAHUB SQL Server, incluyendo el prompt, respuesta completa, nivel de confianza 
            y si requirio revision humana. No se usa MongoDB.
          </div>
        </div>
      </div>
    </div>
  );
};

// ==================== TAB DASHBOARD IA (FASE 1C-3I-E) ====================

const TabDashboardIA = ({ empresaId, unidadId }) => {
  const [metricas, setMetricas] = useState(null);
  const [statsCompetidores, setStatsCompetidores] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  const cargarMetricas = useCallback(async () => {
    setLoading(true);
    setError(null);
    
    try {
      const params = new URLSearchParams();
      if (empresaId) params.append('empresa_id', empresaId);
      if (unidadId) params.append('unidad_negocio_id', unidadId);
      params.append('dias_historial', '30');
      
      const [metricasRes, statsRes] = await Promise.all([
        api.get(`/comercial/pricing-ai/dashboard/metricas?${params}`),
        api.get(`/comercial/pricing-ai/dashboard/estadisticas-competidores?${params}`)
      ]);
      
      setMetricas(metricasRes.data.metricas);
      setStatsCompetidores(statsRes.data.estadisticas);
    } catch (err) {
      setError(err.response?.data?.detail || err.message);
    } finally {
      setLoading(false);
    }
  }, [empresaId, unidadId]);
  
  useEffect(() => {
    cargarMetricas();
  }, [cargarMetricas]);
  
  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-16">
        <RefreshCw className="w-10 h-10 animate-spin text-purple-500 mb-4" />
        <p className="text-gray-500">Cargando metricas del dashboard...</p>
      </div>
    );
  }
  
  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
        <AlertCircle className="w-10 h-10 text-red-500 mx-auto mb-4" />
        <p className="text-red-700 font-medium">Error cargando metricas</p>
        <p className="text-red-600 text-sm mt-1">{error}</p>
        <button
          onClick={cargarMetricas}
          className="mt-4 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700"
        >
          Reintentar
        </button>
      </div>
    );
  }
  
  if (!metricas || metricas.total_analisis === 0) {
    return (
      <div className="text-center py-16 bg-gray-50 rounded-lg">
        <BarChart2 className="w-16 h-16 mx-auto mb-4 text-gray-300" />
        <h3 className="text-lg font-medium text-gray-600 mb-2">Sin datos de metricas</h3>
        <p className="text-gray-500 text-sm max-w-md mx-auto">
          Aun no se han realizado analisis IA. Las metricas se generaran automaticamente 
          cuando ejecutes analisis de producto o benchmark desde la pestana "Analisis IA".
        </p>
        <div className="mt-6 p-4 bg-purple-50 rounded-lg inline-block">
          <p className="text-purple-700 text-sm">
            <Sparkles className="w-4 h-4 inline mr-1" />
            Datos desde: <code className="bg-purple-100 px-1 rounded">Comercial_PricingAnalisisIA</code> (EDARSAHUB SQL)
          </p>
        </div>
      </div>
    );
  }
  
  // Preparar datos para graficas simples
  const distribucion = metricas.distribucion_confianza || {};
  const totalDistribucion = (distribucion.ALTA || 0) + (distribucion.MEDIA || 0) + (distribucion.BAJA || 0);
  
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h3 className="text-lg font-semibold text-gray-800 flex items-center gap-2">
            <BarChart2 className="w-5 h-5 text-purple-600" />
            Dashboard de Metricas IA
          </h3>
          <p className="text-sm text-gray-500">
            Estadisticas de uso y calidad de los analisis realizados con GPT-5.2
          </p>
        </div>
        <div className="flex items-center gap-3">
          <ExportButton metricas={metricas} statsCompetidores={statsCompetidores} />
          <span className="text-xs text-gray-400">
            Actualizado: {formatDate(metricas.fecha_actualizacion)}
          </span>
          <button
            onClick={cargarMetricas}
            className="p-2 border rounded-lg hover:bg-gray-50"
            title="Actualizar metricas"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>
      </div>
      
      {/* KPIs Principales */}
      <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-5 gap-4">
        <div className="bg-gradient-to-br from-purple-500 to-purple-700 rounded-lg p-4 text-white">
          <div className="flex items-center justify-between mb-2">
            <Brain className="w-6 h-6 opacity-80" />
            <span className="text-xs opacity-75">Total</span>
          </div>
          <div className="text-3xl font-bold">{metricas.total_analisis}</div>
          <div className="text-xs opacity-80 mt-1">Analisis IA realizados</div>
        </div>
        
        <div className="bg-gradient-to-br from-green-500 to-green-700 rounded-lg p-4 text-white">
          <div className="flex items-center justify-between mb-2">
            <CheckCircle className="w-6 h-6 opacity-80" />
            <span className="text-xs opacity-75">Confianza Alta</span>
          </div>
          <div className="text-3xl font-bold">{metricas.porcentaje_confianza_alta || 0}%</div>
          <div className="text-xs opacity-80 mt-1">{distribucion.ALTA || 0} analisis</div>
        </div>
        
        <div className="bg-gradient-to-br from-orange-500 to-orange-700 rounded-lg p-4 text-white">
          <div className="flex items-center justify-between mb-2">
            <ShieldAlert className="w-6 h-6 opacity-80" />
            <span className="text-xs opacity-75">Revision</span>
          </div>
          <div className="text-3xl font-bold">{metricas.total_revision_humana || 0}</div>
          <div className="text-xs opacity-80 mt-1">{metricas.porcentaje_revision_humana || 0}% requieren revision</div>
        </div>
        
        <div className="bg-gradient-to-br from-blue-500 to-blue-700 rounded-lg p-4 text-white">
          <div className="flex items-center justify-between mb-2">
            <Clock className="w-6 h-6 opacity-80" />
            <span className="text-xs opacity-75">Hoy</span>
          </div>
          <div className="text-3xl font-bold">{metricas.analisis_hoy || 0}</div>
          <div className="text-xs opacity-80 mt-1">Analisis del dia</div>
        </div>
        
        <div className="bg-gradient-to-br from-indigo-500 to-indigo-700 rounded-lg p-4 text-white">
          <div className="flex items-center justify-between mb-2">
            <TrendingUp className="w-6 h-6 opacity-80" />
            <span className="text-xs opacity-75">Mes</span>
          </div>
          <div className="text-3xl font-bold">{metricas.analisis_mes || 0}</div>
          <div className="text-xs opacity-80 mt-1">Ultimos 30 dias</div>
        </div>
      </div>
      
      {/* Gráficas con Recharts (FASE 1C-3I-F) */}
      <div className="grid sm:grid-cols-2 gap-6">
        {/* Gráfica Análisis por Día */}
        <div className="bg-white border rounded-lg p-6">
          <h4 className="font-semibold text-gray-800 mb-4 flex items-center gap-2">
            <TrendingUp className="w-4 h-4 text-purple-600" />
            Análisis por Día (Últimos 30 días)
          </h4>
          <ChartAnalisisPorDia data={metricas.analisis_por_dia} />
        </div>
        
        {/* Gráfica Distribución de Confianza */}
        <div className="bg-white border rounded-lg p-6">
          <h4 className="font-semibold text-gray-800 mb-4 flex items-center gap-2">
            <Target className="w-4 h-4 text-purple-600" />
            Distribución de Confianza IA
          </h4>
          <ChartDistribucionConfianza data={metricas.distribucion_confianza} />
        </div>
      </div>
      
      {/* Gráfica Productos Más Analizados */}
      {metricas.productos_mas_analizados && metricas.productos_mas_analizados.length > 0 && (
        <div className="bg-white border rounded-lg p-6">
          <h4 className="font-semibold text-gray-800 mb-4 flex items-center gap-2">
            <Tag className="w-4 h-4 text-indigo-600" />
            Top Productos Analizados
          </h4>
          <ChartProductosMasAnalizados data={metricas.productos_mas_analizados} />
        </div>
      )}
      
      {/* Distribucion de Confianza (Barras originales) */}
      <div className="grid sm:grid-cols-2 gap-6">
        <div className="bg-white border rounded-lg p-6">
          <h4 className="font-semibold text-gray-800 mb-4 flex items-center gap-2">
            <Target className="w-4 h-4 text-purple-600" />
            Detalle Distribución de Confianza
          </h4>
          
          {totalDistribucion > 0 ? (
            <div className="space-y-4">
              {/* Barra ALTA */}
              <div>
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-green-700 font-medium">ALTA</span>
                  <span className="text-gray-600">{distribucion.ALTA || 0} ({totalDistribucion > 0 ? ((distribucion.ALTA / totalDistribucion) * 100).toFixed(1) : 0}%)</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-3">
                  <div 
                    className="bg-green-500 h-3 rounded-full transition-all duration-500"
                    style={{ width: `${totalDistribucion > 0 ? (distribucion.ALTA / totalDistribucion) * 100 : 0}%` }}
                  />
                </div>
              </div>
              
              {/* Barra MEDIA */}
              <div>
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-yellow-700 font-medium">MEDIA</span>
                  <span className="text-gray-600">{distribucion.MEDIA || 0} ({totalDistribucion > 0 ? ((distribucion.MEDIA / totalDistribucion) * 100).toFixed(1) : 0}%)</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-3">
                  <div 
                    className="bg-yellow-500 h-3 rounded-full transition-all duration-500"
                    style={{ width: `${totalDistribucion > 0 ? (distribucion.MEDIA / totalDistribucion) * 100 : 0}%` }}
                  />
                </div>
              </div>
              
              {/* Barra BAJA */}
              <div>
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-red-700 font-medium">BAJA</span>
                  <span className="text-gray-600">{distribucion.BAJA || 0} ({totalDistribucion > 0 ? ((distribucion.BAJA / totalDistribucion) * 100).toFixed(1) : 0}%)</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-3">
                  <div 
                    className="bg-red-500 h-3 rounded-full transition-all duration-500"
                    style={{ width: `${totalDistribucion > 0 ? (distribucion.BAJA / totalDistribucion) * 100 : 0}%` }}
                  />
                </div>
              </div>
            </div>
          ) : (
            <p className="text-gray-500 text-center py-4">Sin datos de distribucion</p>
          )}
        </div>
        
        {/* Comparacion de Precios */}
        <div className="bg-white border rounded-lg p-6">
          <h4 className="font-semibold text-gray-800 mb-4 flex items-center gap-2">
            <DollarSign className="w-4 h-4 text-green-600" />
            Promedio Precio Sugerido vs Actual
          </h4>
          
          {metricas.promedio_precio_actual ? (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="bg-gray-50 rounded-lg p-4 text-center">
                  <div className="text-xs text-gray-500 mb-1">Precio Actual Prom.</div>
                  <div className="text-xl font-bold text-gray-800">
                    {formatCurrency(metricas.promedio_precio_actual)}
                  </div>
                </div>
                <div className="bg-purple-50 rounded-lg p-4 text-center">
                  <div className="text-xs text-purple-600 mb-1">Precio Sugerido Prom.</div>
                  <div className="text-xl font-bold text-purple-700">
                    {formatCurrency(metricas.promedio_precio_sugerido)}
                  </div>
                </div>
              </div>
              
              <div className={`text-center p-3 rounded-lg ${
                metricas.variacion_promedio_porcentaje > 0 
                  ? 'bg-green-50 text-green-700'
                  : metricas.variacion_promedio_porcentaje < 0
                  ? 'bg-red-50 text-red-700'
                  : 'bg-gray-50 text-gray-700'
              }`}>
                <div className="flex items-center justify-center gap-2">
                  {metricas.variacion_promedio_porcentaje > 0 ? (
                    <TrendingUp className="w-5 h-5" />
                  ) : metricas.variacion_promedio_porcentaje < 0 ? (
                    <TrendingDown className="w-5 h-5" />
                  ) : null}
                  <span className="font-semibold">
                    {metricas.variacion_promedio_porcentaje > 0 ? '+' : ''}{metricas.variacion_promedio_porcentaje}%
                  </span>
                  <span className="text-sm opacity-80">variacion promedio</span>
                </div>
              </div>
            </div>
          ) : (
            <p className="text-gray-500 text-center py-4">
              Sin datos de precios suficientes para calcular promedios
            </p>
          )}
        </div>
      </div>
      
      {/* Estadisticas de Competidores */}
      {statsCompetidores && (
        <div className="bg-white border rounded-lg p-6">
          <h4 className="font-semibold text-gray-800 mb-4 flex items-center gap-2">
            <Store className="w-4 h-4 text-blue-600" />
            Estadisticas de Benchmark
          </h4>
          
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <div className="text-center p-3 bg-blue-50 rounded-lg">
              <div className="text-2xl font-bold text-blue-700">{statsCompetidores.total_competidores || 0}</div>
              <div className="text-xs text-blue-600">Competidores</div>
            </div>
            <div className="text-center p-3 bg-green-50 rounded-lg">
              <div className="text-2xl font-bold text-green-700">{statsCompetidores.total_items_capturados || 0}</div>
              <div className="text-xs text-green-600">Items Capturados</div>
            </div>
            <div className="text-center p-3 bg-purple-50 rounded-lg">
              <div className="text-2xl font-bold text-purple-700">{statsCompetidores.categorias_cubiertas || 0}</div>
              <div className="text-xs text-purple-600">Categorias</div>
            </div>
            <div className="text-center p-3 bg-amber-50 rounded-lg">
              <div className="text-2xl font-bold text-amber-700">
                {statsCompetidores.promedio_precio_competencia 
                  ? formatCurrency(statsCompetidores.promedio_precio_competencia)
                  : 'N/A'}
              </div>
              <div className="text-xs text-amber-600">Precio Prom. Comp.</div>
            </div>
          </div>
        </div>
      )}
      
      {/* Productos Mas Analizados */}
      {metricas.productos_mas_analizados && metricas.productos_mas_analizados.length > 0 && (
        <div className="bg-white border rounded-lg p-6">
          <h4 className="font-semibold text-gray-800 mb-4 flex items-center gap-2">
            <Tag className="w-4 h-4 text-indigo-600" />
            Productos Mas Analizados
          </h4>
          
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-50">
                <tr>
                  <th className="p-3 text-left">#</th>
                  <th className="p-3 text-left">Codigo Producto</th>
                  <th className="p-3 text-center">Analisis</th>
                  <th className="p-3 text-center">Ult. Confianza</th>
                  <th className="p-3 text-left">Ultimo Analisis</th>
                </tr>
              </thead>
              <tbody>
                {metricas.productos_mas_analizados.slice(0, 5).map((p, idx) => (
                  <tr key={p.codigo_producto} className="border-b">
                    <td className="p-3 text-gray-400">{idx + 1}</td>
                    <td className="p-3 font-medium text-gray-800">{p.codigo_producto}</td>
                    <td className="p-3 text-center">
                      <span className="px-2 py-1 bg-purple-100 text-purple-700 rounded-full text-xs font-medium">
                        {p.cantidad_analisis}x
                      </span>
                    </td>
                    <td className="p-3 text-center">
                      <ConfianzaBadge confianza={p.ultima_confianza} />
                    </td>
                    <td className="p-3 text-gray-500 text-xs">{formatDate(p.ultimo_analisis)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
      
      {/* Competidores Mas Usados */}
      {metricas.competidores_mas_usados && metricas.competidores_mas_usados.length > 0 && (
        <div className="bg-white border rounded-lg p-6">
          <h4 className="font-semibold text-gray-800 mb-4 flex items-center gap-2">
            <Users className="w-4 h-4 text-blue-600" />
            Competidores Mas Usados en Benchmark
          </h4>
          
          <div className="flex flex-wrap gap-2">
            {metricas.competidores_mas_usados.map((c) => (
              <span 
                key={c.nombre}
                className="px-3 py-1.5 bg-blue-50 text-blue-700 rounded-full text-sm flex items-center gap-2"
              >
                <Store className="w-3 h-3" />
                {c.nombre}
                <span className="bg-blue-200 px-1.5 rounded text-xs">{c.veces_usado}x</span>
              </span>
            ))}
          </div>
        </div>
      )}
      
      {/* Ultimos Analisis */}
      {metricas.ultimos_analisis && metricas.ultimos_analisis.length > 0 && (
        <div className="bg-white border rounded-lg p-6">
          <h4 className="font-semibold text-gray-800 mb-4 flex items-center gap-2">
            <History className="w-4 h-4 text-gray-600" />
            Ultimos Analisis Realizados
          </h4>
          
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-50">
                <tr>
                  <th className="p-3 text-left">Fecha</th>
                  <th className="p-3 text-left">Producto</th>
                  <th className="p-3 text-left">Tipo</th>
                  <th className="p-3 text-center">Confianza</th>
                  <th className="p-3 text-center">Revision</th>
                  <th className="p-3 text-right">P. Actual</th>
                  <th className="p-3 text-right">P. Sugerido</th>
                </tr>
              </thead>
              <tbody>
                {metricas.ultimos_analisis.slice(0, 10).map((a) => (
                  <tr key={a.analisis_id} className="border-b hover:bg-gray-50">
                    <td className="p-3 text-gray-500 text-xs">{formatDate(a.fecha)}</td>
                    <td className="p-3 font-medium text-gray-800">{a.codigo_producto}</td>
                    <td className="p-3 text-gray-600 text-xs">{a.tipo_analisis}</td>
                    <td className="p-3 text-center">
                      <ConfianzaBadge confianza={a.confianza} />
                    </td>
                    <td className="p-3 text-center">
                      {a.requiere_revision && <RevisionHumanaBadge requiere={true} />}
                    </td>
                    <td className="p-3 text-right text-gray-600">
                      {a.precio_actual ? formatCurrency(a.precio_actual) : '-'}
                    </td>
                    <td className="p-3 text-right font-medium text-purple-600">
                      {a.precio_sugerido ? formatCurrency(a.precio_sugerido) : '-'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
      
      {/* Tipos de Analisis */}
      {metricas.tipos_analisis && Object.keys(metricas.tipos_analisis).length > 0 && (
        <div className="bg-white border rounded-lg p-6">
          <h4 className="font-semibold text-gray-800 mb-4 flex items-center gap-2">
            <FileText className="w-4 h-4 text-gray-600" />
            Distribucion por Tipo de Analisis
          </h4>
          
          <div className="flex flex-wrap gap-3">
            {Object.entries(metricas.tipos_analisis).map(([tipo, cantidad]) => (
              <div key={tipo} className="flex items-center gap-2 px-3 py-2 bg-gray-50 rounded-lg">
                <span className="text-gray-600 text-sm">{tipo.replace(/_/g, ' ')}</span>
                <span className="px-2 py-0.5 bg-gray-200 rounded text-xs font-medium">{cantidad}</span>
              </div>
            ))}
          </div>
        </div>
      )}
      
      {/* Footer info */}
      <div className="bg-purple-50 border border-purple-200 rounded-lg p-4 text-sm">
        <div className="flex items-start gap-2">
          <Info className="w-4 h-4 mt-0.5 text-purple-600 flex-shrink-0" />
          <div className="text-purple-700">
            <strong>Fuente de datos:</strong> Tabla <code className="bg-purple-100 px-1 rounded">Comercial_PricingAnalisisIA</code> 
            de EDARSAHUB SQL Server. No se usa MongoDB. Las metricas se calculan en tiempo real desde la base de datos.
          </div>
        </div>
      </div>
    </div>
  );
};

// ==================== COMPONENTE PRINCIPAL ====================

const PricingIA = () => {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [empresaId, setEmpresaId] = useState(1);
  const [unidadId, setUnidadId] = useState(1);
  const [resumen, setResumen] = useState(null);
  const [loadingResumen, setLoadingResumen] = useState(true);
  
  // Cargar resumen de benchmark
  useEffect(() => {
    const cargarResumen = async () => {
      if (!unidadId || !empresaId) return;
      
      setLoadingResumen(true);
      try {
        const res = await api.get(`/comercial/benchmark/resumen/${unidadId}?empresa_id=${empresaId}`);
        setResumen(res.data);
      } catch (err) {
        console.error('Error cargando resumen:', err);
        setResumen(null);
      } finally {
        setLoadingResumen(false);
      }
    };
    cargarResumen();
  }, [empresaId, unidadId]);
  
  return (
    <div className="space-y-6" data-testid="pricing-ia-page">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-800 flex items-center gap-2">
            <Brain className="w-7 h-7 text-purple-600" />
            Motor de Precios Sugeridos IA
          </h1>
          <p className="text-gray-500 mt-1">
            Gestion de competidores, benchmark y analisis de precios con GPT-5.2
          </p>
        </div>
        
        <div className="flex items-center gap-2 text-sm">
          <span className="px-3 py-1 bg-purple-100 text-purple-700 rounded-full flex items-center gap-1">
            <Sparkles className="w-3 h-3" />
            Modelo: GPT-5.2
          </span>
          <span className="px-3 py-1 bg-blue-100 text-blue-700 rounded-full">
            FASE 1C-3I-D
          </span>
        </div>
      </div>
      
      {/* Cards de resumen */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <SummaryCard
          title="Competidores"
          value={loadingResumen ? '...' : (resumen?.total_competidores || 0)}
          icon={Store}
          color="blue"
          subtitle="Registrados"
        />
        <SummaryCard
          title="Precios Capturados"
          value={loadingResumen ? '...' : (resumen?.total_items_competencia || 0)}
          icon={DollarSign}
          color="green"
          subtitle="Items de competencia"
        />
        <SummaryCard
          title="Productos Mapeados"
          value={loadingResumen ? '...' : (resumen?.total_productos_mapeados || 0)}
          icon={Target}
          color="purple"
          subtitle="Con benchmark"
        />
        <SummaryCard
          title="Cobertura"
          value={loadingResumen ? '...' : `${(resumen?.cobertura_benchmark || 0).toFixed(0)}%`}
          icon={BarChart2}
          color="amber"
          subtitle="Productos cubiertos"
        />
      </div>
      
      {/* Alerta importante */}
      <div className="bg-amber-50 border border-amber-200 rounded-lg p-4">
        <div className="flex items-start gap-3">
          <AlertTriangle className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
          <div>
            <h4 className="font-medium text-amber-800">Importante: Recomendaciones IA</h4>
            <p className="text-sm text-amber-700 mt-1">
              Los precios sugeridos por la IA son <strong>RECOMENDACIONES</strong>, no precios oficiales. 
              La IA no modifica precios, no crea solicitudes automaticas y no sustituye la regla de VINOS_RANGOS.
              Toda sugerencia debe ser validada por un usuario autorizado antes de cualquier accion.
            </p>
          </div>
        </div>
      </div>
      
      {/* Tabs */}
      <div className="border-b border-gray-200">
        <div className="flex flex-wrap gap-1">
          <TabButton
            active={activeTab === 'dashboard'}
            onClick={() => setActiveTab('dashboard')}
            icon={BarChart2}
            label="Dashboard IA"
          />
          <TabButton
            active={activeTab === 'competidores'}
            onClick={() => setActiveTab('competidores')}
            icon={Store}
            label="Competidores"
            badge={resumen?.total_competidores}
          />
          <TabButton
            active={activeTab === 'precios'}
            onClick={() => setActiveTab('precios')}
            icon={DollarSign}
            label="Precios Competencia"
            badge={resumen?.total_items_competencia}
          />
          <TabButton
            active={activeTab === 'analisis'}
            onClick={() => setActiveTab('analisis')}
            icon={Brain}
            label="Analisis IA"
          />
          <TabButton
            active={activeTab === 'historial'}
            onClick={() => setActiveTab('historial')}
            icon={History}
            label="Historial"
          />
          <TabButton
            active={activeTab === 'sectorial'}
            onClick={() => setActiveTab('sectorial')}
            icon={Layers}
            label="Benchmark Sectorial"
          />
          <TabButton
            active={activeTab === 'listas'}
            onClick={() => setActiveTab('listas')}
            icon={Folder}
            label="Listas"
          />
        </div>
      </div>
      
      {/* Contenido de tabs */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        {activeTab === 'dashboard' && (
          <TabDashboardIA empresaId={empresaId} unidadId={unidadId} />
        )}
        {activeTab === 'competidores' && (
          <TabCompetidores empresaId={empresaId} unidadId={unidadId} />
        )}
        {activeTab === 'precios' && (
          <TabPreciosCompetencia empresaId={empresaId} unidadId={unidadId} />
        )}
        {activeTab === 'analisis' && (
          <TabAnalisisIA empresaId={empresaId} unidadId={unidadId} />
        )}
        {activeTab === 'historial' && (
          <TabHistorial empresaId={empresaId} unidadId={unidadId} />
        )}
        {activeTab === 'sectorial' && (
          <TabBenchmarkSectorial empresaId={empresaId} unidadId={unidadId} onNavigateTab={setActiveTab} />
        )}
        {activeTab === 'listas' && (
          <TabListasCompetidores empresaId={empresaId} unidadId={unidadId} />
        )}
      </div>
      
      {/* Footer info */}
      <div className="text-xs text-gray-400 flex items-center justify-between">
        <span>Datos de EDARSAHUB SQL Server | CERO MongoDB</span>
        <span>FASE 1C-3I-F/G: Visualización y Listas de Competidores</span>
      </div>
    </div>
  );
};

export default PricingIA;
