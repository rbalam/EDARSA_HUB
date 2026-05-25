/**
 * FASE 1C-3I-F: Componentes de Visualización Avanzada para Dashboard IA
 * FASE 1C-3I-G: Gestión de Listas de Competidores
 * ==================================================================
 * 
 * Gráficas con Recharts y Exportación Excel/PDF
 * UI para crear y gestionar listas manuales de competidores
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  BarChart, Bar, PieChart, Pie, Cell
} from 'recharts';
import {
  Download, FileSpreadsheet, FileText, List, Plus, Edit2, Trash2, X,
  CheckCircle, AlertCircle, RefreshCw, Search, Users, Store, Tag,
  ChevronRight, ChevronDown, Folder, FolderPlus
} from 'lucide-react';
import * as XLSX from 'xlsx';
import api from '@/lib/api';

// ==================== COLORES ====================

const COLORS_CONFIANZA = {
  ALTA: '#22c55e',
  MEDIA: '#eab308',
  BAJA: '#ef4444'
};

const COLORS_CHART = ['#8b5cf6', '#3b82f6', '#22c55e', '#eab308', '#ef4444', '#f97316', '#06b6d4'];

// ==================== UTILIDADES ====================

const formatDate = (dateStr) => {
  if (!dateStr) return '';
  try {
    return new Date(dateStr).toLocaleDateString('es-MX', { month: 'short', day: 'numeric' });
  } catch {
    return dateStr;
  }
};

const formatCurrency = (value) => {
  if (value === null || value === undefined) return 'N/A';
  return new Intl.NumberFormat('es-MX', {
    style: 'currency',
    currency: 'MXN',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0
  }).format(value);
};

// ==================== GRÁFICA: ANÁLISIS POR DÍA ====================

export const ChartAnalisisPorDia = ({ data = [] }) => {
  if (!data || data.length === 0) {
    return (
      <div className="h-64 flex items-center justify-center text-gray-400">
        Sin datos de análisis por día
      </div>
    );
  }

  // Ordenar por fecha y formatear
  const chartData = [...data]
    .sort((a, b) => new Date(a.fecha) - new Date(b.fecha))
    .map(item => ({
      ...item,
      fechaCorta: formatDate(item.fecha)
    }));

  return (
    <div className="h-64">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={chartData} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis 
            dataKey="fechaCorta" 
            tick={{ fontSize: 11 }}
            stroke="#9ca3af"
          />
          <YAxis 
            tick={{ fontSize: 11 }}
            stroke="#9ca3af"
            allowDecimals={false}
          />
          <Tooltip 
            contentStyle={{ 
              backgroundColor: '#fff', 
              border: '1px solid #e5e7eb',
              borderRadius: '8px',
              fontSize: '12px'
            }}
            formatter={(value) => [value, 'Análisis']}
            labelFormatter={(label) => `Fecha: ${label}`}
          />
          <Line 
            type="monotone" 
            dataKey="cantidad" 
            stroke="#8b5cf6" 
            strokeWidth={2}
            dot={{ fill: '#8b5cf6', strokeWidth: 2, r: 4 }}
            activeDot={{ r: 6, fill: '#7c3aed' }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};

// ==================== GRÁFICA: DISTRIBUCIÓN DE CONFIANZA ====================

export const ChartDistribucionConfianza = ({ data = {} }) => {
  const chartData = [
    { name: 'ALTA', value: data.ALTA || 0, color: COLORS_CONFIANZA.ALTA },
    { name: 'MEDIA', value: data.MEDIA || 0, color: COLORS_CONFIANZA.MEDIA },
    { name: 'BAJA', value: data.BAJA || 0, color: COLORS_CONFIANZA.BAJA }
  ].filter(item => item.value > 0);

  if (chartData.length === 0) {
    return (
      <div className="h-48 flex items-center justify-center text-gray-400">
        Sin datos de distribución
      </div>
    );
  }

  const total = chartData.reduce((sum, item) => sum + item.value, 0);

  return (
    <div className="h-48 flex items-center">
      <div className="w-1/2">
        <ResponsiveContainer width="100%" height={180}>
          <PieChart>
            <Pie
              data={chartData}
              cx="50%"
              cy="50%"
              innerRadius={40}
              outerRadius={70}
              paddingAngle={2}
              dataKey="value"
            >
              {chartData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.color} />
              ))}
            </Pie>
            <Tooltip 
              formatter={(value, name) => [`${value} (${((value/total)*100).toFixed(1)}%)`, name]}
            />
          </PieChart>
        </ResponsiveContainer>
      </div>
      <div className="w-1/2 space-y-2">
        {chartData.map((item) => (
          <div key={item.name} className="flex items-center gap-2">
            <div 
              className="w-3 h-3 rounded-full" 
              style={{ backgroundColor: item.color }}
            />
            <span className="text-sm text-gray-600">{item.name}</span>
            <span className="text-sm font-semibold">{item.value}</span>
            <span className="text-xs text-gray-400">({((item.value/total)*100).toFixed(0)}%)</span>
          </div>
        ))}
      </div>
    </div>
  );
};

// ==================== GRÁFICA: PRODUCTOS MÁS ANALIZADOS ====================

export const ChartProductosMasAnalizados = ({ data = [] }) => {
  if (!data || data.length === 0) {
    return (
      <div className="h-48 flex items-center justify-center text-gray-400">
        Sin datos de productos
      </div>
    );
  }

  const chartData = data.slice(0, 7).map(item => ({
    codigo: item.codigo_producto?.substring(0, 10) || 'N/A',
    cantidad: item.cantidad_analisis || 0
  }));

  return (
    <div className="h-48">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={chartData} layout="vertical" margin={{ top: 5, right: 20, left: 60, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" horizontal={false} />
          <XAxis type="number" tick={{ fontSize: 11 }} stroke="#9ca3af" allowDecimals={false} />
          <YAxis 
            type="category" 
            dataKey="codigo" 
            tick={{ fontSize: 10 }}
            stroke="#9ca3af"
            width={55}
          />
          <Tooltip 
            contentStyle={{ 
              backgroundColor: '#fff', 
              border: '1px solid #e5e7eb',
              borderRadius: '8px',
              fontSize: '12px'
            }}
            formatter={(value) => [value, 'Análisis']}
          />
          <Bar dataKey="cantidad" fill="#8b5cf6" radius={[0, 4, 4, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
};

// ==================== EXPORTACIÓN A EXCEL ====================

export const exportarMetricasExcel = (metricas, statsCompetidores) => {
  if (!metricas) return;

  const wb = XLSX.utils.book_new();

  // Hoja 1: Resumen KPIs
  const kpis = [
    ['DASHBOARD MÉTRICAS IA PRICING', ''],
    ['Fecha de exportación', new Date().toLocaleString('es-MX')],
    ['', ''],
    ['MÉTRICAS PRINCIPALES', ''],
    ['Total Análisis IA', metricas.total_analisis || 0],
    ['Análisis Hoy', metricas.analisis_hoy || 0],
    ['Análisis Semana', metricas.analisis_semana || 0],
    ['Análisis Mes', metricas.analisis_mes || 0],
    ['', ''],
    ['DISTRIBUCIÓN DE CONFIANZA', ''],
    ['Confianza ALTA', metricas.distribucion_confianza?.ALTA || 0],
    ['Confianza MEDIA', metricas.distribucion_confianza?.MEDIA || 0],
    ['Confianza BAJA', metricas.distribucion_confianza?.BAJA || 0],
    ['% Confianza Alta', `${metricas.porcentaje_confianza_alta || 0}%`],
    ['', ''],
    ['REVISIÓN HUMANA', ''],
    ['Requieren Revisión', metricas.total_revision_humana || 0],
    ['% Revisión Humana', `${metricas.porcentaje_revision_humana || 0}%`],
    ['', ''],
    ['PROMEDIOS DE PRECIOS', ''],
    ['Precio Actual Promedio', metricas.promedio_precio_actual || 'N/A'],
    ['Precio Sugerido Promedio', metricas.promedio_precio_sugerido || 'N/A'],
    ['Variación Promedio %', `${metricas.variacion_promedio_porcentaje || 0}%`]
  ];
  const wsKpis = XLSX.utils.aoa_to_sheet(kpis);
  XLSX.utils.book_append_sheet(wb, wsKpis, 'Resumen KPIs');

  // Hoja 2: Análisis por Día
  if (metricas.analisis_por_dia && metricas.analisis_por_dia.length > 0) {
    const analisisDia = [
      ['Fecha', 'Cantidad de Análisis'],
      ...metricas.analisis_por_dia.map(a => [a.fecha, a.cantidad])
    ];
    const wsAnalisis = XLSX.utils.aoa_to_sheet(analisisDia);
    XLSX.utils.book_append_sheet(wb, wsAnalisis, 'Análisis por Día');
  }

  // Hoja 3: Productos Más Analizados
  if (metricas.productos_mas_analizados && metricas.productos_mas_analizados.length > 0) {
    const productos = [
      ['Código Producto', 'Cantidad Análisis', 'Última Confianza', 'Último Análisis'],
      ...metricas.productos_mas_analizados.map(p => [
        p.codigo_producto,
        p.cantidad_analisis,
        p.ultima_confianza,
        p.ultimo_analisis
      ])
    ];
    const wsProductos = XLSX.utils.aoa_to_sheet(productos);
    XLSX.utils.book_append_sheet(wb, wsProductos, 'Productos Analizados');
  }

  // Hoja 4: Últimos Análisis
  if (metricas.ultimos_analisis && metricas.ultimos_analisis.length > 0) {
    const ultimos = [
      ['Fecha', 'Producto', 'Tipo', 'Confianza', 'Revisión', 'Precio Actual', 'Precio Sugerido', 'Usuario'],
      ...metricas.ultimos_analisis.map(a => [
        a.fecha,
        a.codigo_producto,
        a.tipo_analisis,
        a.confianza,
        a.requiere_revision ? 'SÍ' : 'NO',
        a.precio_actual || '',
        a.precio_sugerido || '',
        a.usuario
      ])
    ];
    const wsUltimos = XLSX.utils.aoa_to_sheet(ultimos);
    XLSX.utils.book_append_sheet(wb, wsUltimos, 'Últimos Análisis');
  }

  // Hoja 5: Estadísticas Competidores
  if (statsCompetidores) {
    const stats = [
      ['ESTADÍSTICAS DE BENCHMARK', ''],
      ['Total Competidores', statsCompetidores.total_competidores || 0],
      ['Competidores Directos', statsCompetidores.competidores_directos || 0],
      ['Competidores Aspiracionales', statsCompetidores.competidores_aspiracionales || 0],
      ['Items Capturados', statsCompetidores.total_items_capturados || 0],
      ['Categorías Cubiertas', statsCompetidores.categorias_cubiertas || 0],
      ['Precio Promedio Competencia', statsCompetidores.promedio_precio_competencia || 'N/A']
    ];
    const wsStats = XLSX.utils.aoa_to_sheet(stats);
    XLSX.utils.book_append_sheet(wb, wsStats, 'Stats Competidores');
  }

  // Descargar
  const fileName = `Metricas_IA_Pricing_${new Date().toISOString().split('T')[0]}.xlsx`;
  XLSX.writeFile(wb, fileName);
};

// ==================== BOTÓN DE EXPORTACIÓN ====================

export const ExportButton = ({ metricas, statsCompetidores, disabled = false }) => {
  const [exporting, setExporting] = useState(false);

  const handleExport = () => {
    setExporting(true);
    try {
      exportarMetricasExcel(metricas, statsCompetidores);
    } finally {
      setTimeout(() => setExporting(false), 500);
    }
  };

  return (
    <button
      onClick={handleExport}
      disabled={disabled || exporting || !metricas}
      className="flex items-center gap-2 px-3 py-1.5 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed text-sm transition-colors"
      data-testid="btn-export-excel"
    >
      {exporting ? (
        <RefreshCw className="w-4 h-4 animate-spin" />
      ) : (
        <FileSpreadsheet className="w-4 h-4" />
      )}
      Exportar Excel
    </button>
  );
};

// ==================== MODAL CREAR/EDITAR LISTA ====================

export const ListaCompetidoresModal = ({ isOpen, onClose, lista, onSave, loading }) => {
  const [form, setForm] = useState({
    nombre_lista: '',
    descripcion: '',
    segmento: '',
    categoria: '',
    color: '#8b5cf6'
  });

  useEffect(() => {
    if (lista) {
      setForm({
        nombre_lista: lista.nombre_lista || '',
        descripcion: lista.descripcion || '',
        segmento: lista.segmento || '',
        categoria: lista.categoria || '',
        color: lista.color || '#8b5cf6'
      });
    } else {
      setForm({
        nombre_lista: '',
        descripcion: '',
        segmento: '',
        categoria: '',
        color: '#8b5cf6'
      });
    }
  }, [lista, isOpen]);

  if (!isOpen) return null;

  const handleSubmit = (e) => {
    e.preventDefault();
    onSave(form);
  };

  const colores = [
    '#8b5cf6', '#3b82f6', '#22c55e', '#eab308', '#ef4444', 
    '#f97316', '#06b6d4', '#ec4899', '#6366f1', '#84cc16'
  ];

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-md">
        <div className="p-4 border-b flex justify-between items-center bg-gradient-to-r from-indigo-600 to-purple-600">
          <h3 className="text-lg font-semibold text-white flex items-center gap-2">
            <Folder className="w-5 h-5" />
            {lista ? 'Editar Lista' : 'Nueva Lista de Competidores'}
          </h3>
          <button onClick={onClose} className="p-1 hover:bg-indigo-800 rounded text-white">
            <X className="w-5 h-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Nombre de la Lista *
            </label>
            <input
              type="text"
              value={form.nombre_lista}
              onChange={(e) => setForm({ ...form, nombre_lista: e.target.value })}
              placeholder="Ej: Competidores Mérida Premium"
              required
              maxLength={200}
              className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
              data-testid="input-nombre-lista"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Descripción
            </label>
            <textarea
              value={form.descripcion}
              onChange={(e) => setForm({ ...form, descripcion: e.target.value })}
              placeholder="Descripción opcional..."
              rows={2}
              maxLength={500}
              className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 resize-none"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Segmento
              </label>
              <input
                type="text"
                value={form.segmento}
                onChange={(e) => setForm({ ...form, segmento: e.target.value })}
                placeholder="Ej: Premium"
                maxLength={100}
                className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Categoría
              </label>
              <input
                type="text"
                value={form.categoria}
                onChange={(e) => setForm({ ...form, categoria: e.target.value })}
                placeholder="Ej: Restaurantes"
                maxLength={100}
                className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Color Identificador
            </label>
            <div className="flex flex-wrap gap-2">
              {colores.map((c) => (
                <button
                  key={c}
                  type="button"
                  onClick={() => setForm({ ...form, color: c })}
                  className={`w-8 h-8 rounded-full border-2 transition-transform ${
                    form.color === c ? 'border-gray-800 scale-110' : 'border-transparent'
                  }`}
                  style={{ backgroundColor: c }}
                />
              ))}
            </div>
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
            disabled={loading || !form.nombre_lista}
            className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            data-testid="btn-guardar-lista"
          >
            {loading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <CheckCircle className="w-4 h-4" />}
            Guardar
          </button>
        </div>
      </div>
    </div>
  );
};

// ==================== MODAL AGREGAR COMPETIDORES A LISTA ====================

export const AgregarCompetidoresModal = ({ isOpen, onClose, lista, competidoresDisponibles, competidoresEnLista, onAgregar, onQuitar, loading }) => {
  const [busqueda, setBusqueda] = useState('');

  if (!isOpen || !lista) return null;

  const idsEnLista = new Set(competidoresEnLista.map(c => c.competidor_id));
  
  const competidoresFiltrados = competidoresDisponibles.filter(c => 
    !idsEnLista.has(c.competidor_id) &&
    (c.nombre_competidor?.toLowerCase().includes(busqueda.toLowerCase()) ||
     c.tipo_negocio?.toLowerCase().includes(busqueda.toLowerCase()))
  );

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-2xl max-h-[80vh] overflow-hidden">
        <div className="p-4 border-b flex justify-between items-center" style={{ backgroundColor: lista.color || '#8b5cf6' }}>
          <h3 className="text-lg font-semibold text-white flex items-center gap-2">
            <Users className="w-5 h-5" />
            {lista.nombre_lista} ({competidoresEnLista.length} competidores)
          </h3>
          <button onClick={onClose} className="p-1 hover:bg-black/20 rounded text-white">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="p-4 border-b bg-gray-50">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              value={busqueda}
              onChange={(e) => setBusqueda(e.target.value)}
              placeholder="Buscar competidores para agregar..."
              className="w-full pl-10 pr-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>
        </div>

        <div className="grid grid-cols-2 divide-x max-h-[50vh] overflow-hidden">
          {/* Competidores en la lista */}
          <div className="p-4 overflow-y-auto">
            <h4 className="text-sm font-medium text-gray-700 mb-3 flex items-center gap-2">
              <CheckCircle className="w-4 h-4 text-green-500" />
              En esta lista ({competidoresEnLista.length})
            </h4>
            {competidoresEnLista.length === 0 ? (
              <p className="text-sm text-gray-400 text-center py-4">Sin competidores</p>
            ) : (
              <div className="space-y-2">
                {competidoresEnLista.map((c) => (
                  <div 
                    key={c.competidor_id} 
                    className="flex items-center justify-between p-2 bg-green-50 rounded-lg"
                  >
                    <div>
                      <div className="font-medium text-sm text-gray-800">{c.nombre_competidor}</div>
                      <div className="text-xs text-gray-500">{c.tipo_negocio}</div>
                    </div>
                    <button
                      onClick={() => onQuitar(c.competidor_id)}
                      disabled={loading}
                      className="p-1 hover:bg-red-100 rounded text-red-500"
                      title="Quitar de la lista"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Competidores disponibles */}
          <div className="p-4 overflow-y-auto bg-gray-50">
            <h4 className="text-sm font-medium text-gray-700 mb-3 flex items-center gap-2">
              <Store className="w-4 h-4 text-blue-500" />
              Disponibles ({competidoresFiltrados.length})
            </h4>
            {competidoresFiltrados.length === 0 ? (
              <p className="text-sm text-gray-400 text-center py-4">
                {busqueda ? 'Sin resultados' : 'Todos los competidores están en la lista'}
              </p>
            ) : (
              <div className="space-y-2">
                {competidoresFiltrados.slice(0, 20).map((c) => (
                  <div 
                    key={c.competidor_id} 
                    className="flex items-center justify-between p-2 bg-white rounded-lg border hover:border-indigo-300"
                  >
                    <div>
                      <div className="font-medium text-sm text-gray-800">{c.nombre_competidor}</div>
                      <div className="text-xs text-gray-500">{c.tipo_negocio} | {c.nivel_precio_percibido}</div>
                    </div>
                    <button
                      onClick={() => onAgregar(c.competidor_id)}
                      disabled={loading}
                      className="p-1 hover:bg-indigo-100 rounded text-indigo-600"
                      title="Agregar a la lista"
                    >
                      <Plus className="w-4 h-4" />
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
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

// ==================== TAB LISTAS DE COMPETIDORES ====================

export const TabListasCompetidores = ({ empresaId, unidadId }) => {
  const [listas, setListas] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [modalOpen, setModalOpen] = useState(false);
  const [selectedLista, setSelectedLista] = useState(null);
  const [saving, setSaving] = useState(false);
  const [busqueda, setBusqueda] = useState('');
  
  // Modal de agregar competidores
  const [modalCompetidoresOpen, setModalCompetidoresOpen] = useState(false);
  const [listaParaCompetidores, setListaParaCompetidores] = useState(null);
  const [competidoresDisponibles, setCompetidoresDisponibles] = useState([]);
  const [competidoresEnLista, setCompetidoresEnLista] = useState([]);

  const cargarListas = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams();
      if (empresaId) params.append('empresa_id', empresaId);
      if (unidadId) params.append('unidad_negocio_id', unidadId);
      params.append('page_size', '100');

      const res = await api.get(`/comercial/pricing/listas-competidores?${params}`);
      setListas(res.data.listas || []);
    } catch (err) {
      setError(err.response?.data?.detail || err.message);
    } finally {
      setLoading(false);
    }
  }, [empresaId, unidadId]);

  useEffect(() => {
    cargarListas();
  }, [cargarListas]);

  const handleSaveLista = async (form) => {
    setSaving(true);
    try {
      const payload = {
        ...form,
        empresa_id: empresaId || 1,
        unidad_negocio_id: unidadId || 1
      };

      if (selectedLista) {
        await api.put(`/comercial/pricing/listas-competidores/${selectedLista.lista_id}`, payload);
      } else {
        await api.post('/comercial/pricing/listas-competidores', payload);
      }

      setModalOpen(false);
      setSelectedLista(null);
      cargarListas();
    } catch (err) {
      alert('Error: ' + (err.response?.data?.detail || err.message));
    } finally {
      setSaving(false);
    }
  };

  const handleDeleteLista = async (id) => {
    if (!window.confirm('¿Está seguro de desactivar esta lista?')) return;

    try {
      await api.delete(`/comercial/pricing/listas-competidores/${id}`);
      cargarListas();
    } catch (err) {
      alert('Error: ' + (err.response?.data?.detail || err.message));
    }
  };

  const abrirModalCompetidores = async (lista) => {
    setListaParaCompetidores(lista);
    setModalCompetidoresOpen(true);

    try {
      // Cargar competidores disponibles y los de la lista
      const [dispRes, listaRes] = await Promise.all([
        api.get(`/comercial/competidores?page_size=200&empresa_id=${empresaId || 1}`),
        api.get(`/comercial/pricing/listas-competidores/${lista.lista_id}/competidores`)
      ]);

      setCompetidoresDisponibles(dispRes.data.competidores || []);
      setCompetidoresEnLista(listaRes.data.competidores || []);
    } catch (err) {
      console.error('Error cargando competidores:', err);
    }
  };

  const handleAgregarCompetidor = async (competidorId) => {
    if (!listaParaCompetidores) return;

    try {
      await api.post(`/comercial/pricing/listas-competidores/${listaParaCompetidores.lista_id}/competidores`, {
        competidor_id: competidorId,
        orden: competidoresEnLista.length + 1
      });

      // Actualizar lista local
      const comp = competidoresDisponibles.find(c => c.competidor_id === competidorId);
      if (comp) {
        setCompetidoresEnLista(prev => [...prev, comp]);
      }
      
      // Actualizar conteo en la lista principal
      setListas(prev => prev.map(l => 
        l.lista_id === listaParaCompetidores.lista_id 
          ? { ...l, total_competidores: (l.total_competidores || 0) + 1 }
          : l
      ));
    } catch (err) {
      alert('Error: ' + (err.response?.data?.detail || err.message));
    }
  };

  const handleQuitarCompetidor = async (competidorId) => {
    if (!listaParaCompetidores) return;

    try {
      await api.delete(`/comercial/pricing/listas-competidores/${listaParaCompetidores.lista_id}/competidores/${competidorId}`);

      setCompetidoresEnLista(prev => prev.filter(c => c.competidor_id !== competidorId));
      
      // Actualizar conteo en la lista principal
      setListas(prev => prev.map(l => 
        l.lista_id === listaParaCompetidores.lista_id 
          ? { ...l, total_competidores: Math.max((l.total_competidores || 0) - 1, 0) }
          : l
      ));
    } catch (err) {
      alert('Error: ' + (err.response?.data?.detail || err.message));
    }
  };

  const listasFiltradas = busqueda
    ? listas.filter(l =>
        l.nombre_lista?.toLowerCase().includes(busqueda.toLowerCase()) ||
        l.segmento?.toLowerCase().includes(busqueda.toLowerCase()) ||
        l.categoria?.toLowerCase().includes(busqueda.toLowerCase())
      )
    : listas;

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
            placeholder="Buscar lista..."
            className="w-full pl-10 pr-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
            data-testid="search-listas"
          />
        </div>

        <div className="flex gap-2">
          <button
            onClick={cargarListas}
            disabled={loading}
            className="p-2 border rounded-lg hover:bg-gray-50 transition-colors"
            title="Recargar"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
          <button
            onClick={() => { setSelectedLista(null); setModalOpen(true); }}
            className="flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors"
            data-testid="btn-nueva-lista"
          >
            <FolderPlus className="w-4 h-4" />
            Nueva Lista
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
          <RefreshCw className="w-8 h-8 animate-spin text-indigo-500" />
        </div>
      ) : listasFiltradas.length === 0 ? (
        <div className="text-center py-12 text-gray-500">
          <Folder className="w-12 h-12 mx-auto mb-4 opacity-50" />
          <p>No hay listas de competidores</p>
          <p className="text-sm">Cree listas para agrupar competidores por ciudad, segmento o estrategia</p>
        </div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {listasFiltradas.map((lista) => (
            <div
              key={lista.lista_id}
              className="bg-white border rounded-lg overflow-hidden hover:shadow-md transition-shadow"
              data-testid={`lista-${lista.lista_id}`}
            >
              <div 
                className="h-2" 
                style={{ backgroundColor: lista.color || '#8b5cf6' }}
              />
              <div className="p-4">
                <div className="flex justify-between items-start mb-3">
                  <div>
                    <h4 className="font-semibold text-gray-800">{lista.nombre_lista}</h4>
                    {lista.descripcion && (
                      <p className="text-xs text-gray-500 mt-1 line-clamp-2">{lista.descripcion}</p>
                    )}
                  </div>
                  <div className="flex gap-1">
                    <button
                      onClick={() => { setSelectedLista(lista); setModalOpen(true); }}
                      className="p-1.5 hover:bg-gray-100 rounded"
                      title="Editar"
                    >
                      <Edit2 className="w-4 h-4 text-gray-500" />
                    </button>
                    <button
                      onClick={() => handleDeleteLista(lista.lista_id)}
                      className="p-1.5 hover:bg-red-50 rounded"
                      title="Desactivar"
                    >
                      <Trash2 className="w-4 h-4 text-red-500" />
                    </button>
                  </div>
                </div>

                <div className="flex flex-wrap gap-2 mb-3">
                  {lista.segmento && (
                    <span className="px-2 py-0.5 text-xs rounded bg-purple-100 text-purple-700">
                      {lista.segmento}
                    </span>
                  )}
                  {lista.categoria && (
                    <span className="px-2 py-0.5 text-xs rounded bg-blue-100 text-blue-700">
                      {lista.categoria}
                    </span>
                  )}
                </div>

                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2 text-sm text-gray-600">
                    <Users className="w-4 h-4" />
                    <span className="font-medium">{lista.total_competidores || 0}</span>
                    <span>competidores</span>
                  </div>
                  <button
                    onClick={() => abrirModalCompetidores(lista)}
                    className="text-sm text-indigo-600 hover:text-indigo-800 flex items-center gap-1"
                  >
                    Gestionar
                    <ChevronRight className="w-4 h-4" />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Modales */}
      <ListaCompetidoresModal
        isOpen={modalOpen}
        onClose={() => { setModalOpen(false); setSelectedLista(null); }}
        lista={selectedLista}
        onSave={handleSaveLista}
        loading={saving}
      />

      <AgregarCompetidoresModal
        isOpen={modalCompetidoresOpen}
        onClose={() => { setModalCompetidoresOpen(false); setListaParaCompetidores(null); }}
        lista={listaParaCompetidores}
        competidoresDisponibles={competidoresDisponibles}
        competidoresEnLista={competidoresEnLista}
        onAgregar={handleAgregarCompetidor}
        onQuitar={handleQuitarCompetidor}
        loading={saving}
      />
    </div>
  );
};

export default {
  ChartAnalisisPorDia,
  ChartDistribucionConfianza,
  ChartProductosMasAnalizados,
  ExportButton,
  exportarMetricasExcel,
  ListaCompetidoresModal,
  AgregarCompetidoresModal,
  TabListasCompetidores
};
