/**
 * FASE 1C-3D: Pantalla de Costos y Márgenes
 * ==========================================
 * Consume endpoints NO-LIVE de EDARSAHUB SQL
 * 
 * Endpoints utilizados:
 * - GET /api/costos-margenes/resumen
 * - GET /api/costos-margenes/productos
 * - GET /api/costos-margenes/productos/{id}/receta
 * - GET /api/costos-margenes/productos/{id}/insumos
 * - GET /api/costos-margenes/sync-status
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
  Package, DollarSign, BarChart2, RefreshCw, Search, Filter,
  ChevronLeft, ChevronRight, Eye, List, AlertCircle, CheckCircle,
  Clock, Database, Percent, TrendingUp, TrendingDown, X
} from 'lucide-react';

const API_URL = process.env.REACT_APP_BACKEND_URL || '';

// Función para formatear moneda
const formatCurrency = (value) => {
  if (value === null || value === undefined) return 'Sin dato';
  if (value === 0) return '$0.00';
  return new Intl.NumberFormat('es-MX', {
    style: 'currency',
    currency: 'MXN',
    minimumFractionDigits: 2
  }).format(value);
};

// Función para formatear porcentaje
const formatPercent = (value) => {
  if (value === null || value === undefined) return 'Sin dato';
  return `${value.toFixed(1)}%`;
};

// Componente de tarjeta de resumen
const SummaryCard = ({ title, value, icon: Icon, color = 'blue', subtitle }) => (
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

// Componente de indicador de sync status
const SyncStatusBadge = ({ status, lastSync, syncRunId }) => {
  const statusConfig = {
    'EDARSAHUB_SQL': { color: 'green', text: 'Sincronizado', icon: CheckCircle },
    'STALE_EDARSAHUB_SQL': { color: 'yellow', text: 'Datos antiguos', icon: Clock },
    'SIN_DATOS_EDARSAHUB': { color: 'red', text: 'Sin datos', icon: AlertCircle }
  };
  
  const config = statusConfig[status] || statusConfig['SIN_DATOS_EDARSAHUB'];
  const StatusIcon = config.icon;
  
  return (
    <div className="flex items-center gap-2 text-sm">
      <StatusIcon className={`w-4 h-4 text-${config.color}-500`} />
      <span className={`text-${config.color}-600 font-medium`}>{config.text}</span>
      {lastSync && (
        <span className="text-gray-400 text-xs">
          | {new Date(lastSync).toLocaleString('es-MX')}
        </span>
      )}
    </div>
  );
};

// Modal de receta expandida
const RecetaModal = ({ isOpen, onClose, productoId, token }) => {
  const [receta, setReceta] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  
  useEffect(() => {
    if (isOpen && productoId) {
      setLoading(true);
      setError(null);
      
      fetch(`${API_URL}/api/costos-margenes/productos/${productoId}/receta`, {
        headers: { 'Authorization': `Bearer ${token}` }
      })
        .then(res => res.json())
        .then(data => {
          if (data.detail) throw new Error(data.detail);
          setReceta(data);
        })
        .catch(err => setError(err.message))
        .finally(() => setLoading(false));
    }
  }, [isOpen, productoId, token]);
  
  if (!isOpen) return null;
  
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-4xl max-h-[80vh] overflow-hidden">
        <div className="p-4 border-b flex justify-between items-center bg-gray-50">
          <h3 className="text-lg font-semibold text-gray-800">
            Receta Expandida
          </h3>
          <button onClick={onClose} className="p-1 hover:bg-gray-200 rounded">
            <X className="w-5 h-5" />
          </button>
        </div>
        
        <div className="p-4 overflow-y-auto max-h-[calc(80vh-120px)]">
          {loading && (
            <div className="flex justify-center py-8">
              <RefreshCw className="w-8 h-8 animate-spin text-blue-500" />
            </div>
          )}
          
          {error && (
            <div className="bg-red-50 border border-red-200 rounded p-4 text-red-700">
              Error: {error}
            </div>
          )}
          
          {receta && !loading && (
            <div className="space-y-4">
              {/* Header del producto */}
              <div className="bg-blue-50 rounded-lg p-4">
                <h4 className="font-bold text-lg text-blue-800">{receta.producto_nombre}</h4>
                <div className="flex gap-4 mt-2 text-sm text-gray-600">
                  <span>Código: {receta.producto_codigo}</span>
                  <span>Sistema: {receta.sistema_origen}</span>
                  <span>Componentes: {receta.total_componentes}</span>
                </div>
                <div className="mt-2 text-lg font-semibold text-green-700">
                  Costo Total: {formatCurrency(receta.costo_total_receta)}
                </div>
              </div>
              
              {/* Tabla de componentes */}
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead className="bg-gray-100">
                    <tr>
                      <th className="p-2 text-left">Componente</th>
                      <th className="p-2 text-left">Tipo</th>
                      <th className="p-2 text-right">Cantidad</th>
                      <th className="p-2 text-left">Unidad</th>
                      <th className="p-2 text-right">Costo Unit.</th>
                      <th className="p-2 text-right">Costo Total</th>
                      <th className="p-2 text-right">% del Total</th>
                    </tr>
                  </thead>
                  <tbody>
                    {receta.componentes?.map((comp, idx) => (
                      <tr key={idx} className="border-b hover:bg-gray-50">
                        <td className="p-2">
                          <span className={comp.es_elaborado ? 'text-purple-600 font-medium' : ''}>
                            {comp.nombre}
                          </span>
                          {comp.es_elaborado && (
                            <span className="ml-2 text-xs bg-purple-100 text-purple-700 px-1 rounded">
                              Elaborado
                            </span>
                          )}
                        </td>
                        <td className="p-2 text-gray-500 text-xs">{comp.tipo_componente}</td>
                        <td className="p-2 text-right font-mono">{comp.cantidad?.toFixed(3)}</td>
                        <td className="p-2">{comp.unidad_medida}</td>
                        <td className="p-2 text-right">{formatCurrency(comp.costo_unitario)}</td>
                        <td className="p-2 text-right font-medium">{formatCurrency(comp.costo_total)}</td>
                        <td className="p-2 text-right">
                          {comp.porcentaje_costo_total != null ? (
                            <div className="flex items-center justify-end gap-1">
                              <div 
                                className="h-2 bg-blue-500 rounded" 
                                style={{ width: `${Math.min(comp.porcentaje_costo_total, 100)}px` }}
                              />
                              <span>{comp.porcentaje_costo_total?.toFixed(1)}%</span>
                            </div>
                          ) : '-'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              
              {/* Footer */}
              <div className="text-xs text-gray-400 flex justify-between">
                <span>source_type: {receta.source_type}</span>
                <span>sync_run_id: {receta.sync_run_id?.substring(0, 30)}...</span>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

// Modal de insumos consolidados
const InsumosModal = ({ isOpen, onClose, productoId, token }) => {
  const [insumos, setInsumos] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  
  useEffect(() => {
    if (isOpen && productoId) {
      setLoading(true);
      setError(null);
      
      fetch(`${API_URL}/api/costos-margenes/productos/${productoId}/insumos`, {
        headers: { 'Authorization': `Bearer ${token}` }
      })
        .then(res => res.json())
        .then(data => {
          if (data.detail) throw new Error(data.detail);
          setInsumos(data);
        })
        .catch(err => setError(err.message))
        .finally(() => setLoading(false));
    }
  }, [isOpen, productoId, token]);
  
  if (!isOpen) return null;
  
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-3xl max-h-[80vh] overflow-hidden">
        <div className="p-4 border-b flex justify-between items-center bg-gray-50">
          <h3 className="text-lg font-semibold text-gray-800">
            Insumos Consolidados
          </h3>
          <button onClick={onClose} className="p-1 hover:bg-gray-200 rounded">
            <X className="w-5 h-5" />
          </button>
        </div>
        
        <div className="p-4 overflow-y-auto max-h-[calc(80vh-120px)]">
          {loading && (
            <div className="flex justify-center py-8">
              <RefreshCw className="w-8 h-8 animate-spin text-blue-500" />
            </div>
          )}
          
          {error && (
            <div className="bg-red-50 border border-red-200 rounded p-4 text-red-700">
              Error: {error}
            </div>
          )}
          
          {insumos && !loading && (
            <div className="space-y-4">
              <div className="bg-green-50 rounded-lg p-4">
                <h4 className="font-bold text-lg text-green-800">{insumos.producto_nombre}</h4>
                <div className="flex gap-4 mt-2 text-sm">
                  <span>Total Insumos: {insumos.total_insumos}</span>
                  <span className="font-semibold">
                    Costo Total: {formatCurrency(insumos.costo_total_insumos)}
                  </span>
                </div>
              </div>
              
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead className="bg-gray-100">
                    <tr>
                      <th className="p-2 text-left">Insumo</th>
                      <th className="p-2 text-right">Cantidad</th>
                      <th className="p-2 text-left">Unidad</th>
                      <th className="p-2 text-right">Costo Unit.</th>
                      <th className="p-2 text-right">Costo Total</th>
                      <th className="p-2 text-right">% Costo</th>
                      <th className="p-2 text-center">Origen</th>
                    </tr>
                  </thead>
                  <tbody>
                    {insumos.insumos?.map((ins, idx) => (
                      <tr key={idx} className="border-b hover:bg-gray-50">
                        <td className="p-2">{ins.nombre}</td>
                        <td className="p-2 text-right font-mono">{ins.cantidad_total?.toFixed(3)}</td>
                        <td className="p-2">{ins.unidad_medida}</td>
                        <td className="p-2 text-right">{formatCurrency(ins.costo_unitario)}</td>
                        <td className="p-2 text-right font-medium">{formatCurrency(ins.costo_total)}</td>
                        <td className="p-2 text-right">
                          {ins.porcentaje_costo_total != null ? (
                            <span className={ins.porcentaje_costo_total > 20 ? 'text-red-600 font-medium' : ''}>
                              {ins.porcentaje_costo_total?.toFixed(1)}%
                            </span>
                          ) : '-'}
                        </td>
                        <td className="p-2 text-center">
                          <span className={`text-xs px-2 py-1 rounded ${
                            ins.origen === 'INSUMO_DIRECTO' 
                              ? 'bg-blue-100 text-blue-700' 
                              : 'bg-purple-100 text-purple-700'
                          }`}>
                            {ins.origen === 'INSUMO_DIRECTO' ? 'Directo' : 'SubReceta'}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              
              <div className="text-xs text-gray-400">
                source_type: {insumos.source_type}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

// Componente principal
const CostosMargenes = () => {
  const [token, setToken] = useState(localStorage.getItem('token') || '');
  
  // Estados de datos
  const [resumen, setResumen] = useState(null);
  const [productos, setProductos] = useState([]);
  const [syncStatus, setSyncStatus] = useState(null);
  
  // Estados de paginación y filtros
  const [page, setPage] = useState(1);
  const [pageSize] = useState(20);
  const [totalPages, setTotalPages] = useState(1);
  const [totalProductos, setTotalProductos] = useState(0);
  
  // Filtros
  const [busqueda, setBusqueda] = useState('');
  const [sistemaOrigen, setSistemaOrigen] = useState('');
  const [soloConReceta, setSoloConReceta] = useState(false);
  const [margenBajo, setMargenBajo] = useState(false);
  
  // Estados de UI
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  // Modales
  const [recetaModal, setRecetaModal] = useState({ open: false, productoId: null });
  const [insumosModal, setInsumosModal] = useState({ open: false, productoId: null });
  
  // Cargar resumen
  const loadResumen = useCallback(async () => {
    if (!token) return;
    try {
      const res = await fetch(`${API_URL}/api/costos-margenes/resumen`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      if (data.detail) throw new Error(data.detail);
      setResumen(data);
    } catch (err) {
      console.error('Error cargando resumen:', err);
    }
  }, [token]);
  
  // Cargar sync status
  const loadSyncStatus = useCallback(async () => {
    if (!token) return;
    try {
      const res = await fetch(`${API_URL}/api/costos-margenes/sync-status`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      if (data.detail) throw new Error(data.detail);
      setSyncStatus(data);
    } catch (err) {
      console.error('Error cargando sync status:', err);
    }
  }, [token]);
  
  // Cargar productos
  const loadProductos = useCallback(async () => {
    if (!token) return;
    setLoading(true);
    setError(null);
    
    try {
      const params = new URLSearchParams({
        page: page.toString(),
        page_size: pageSize.toString()
      });
      
      if (busqueda) params.append('busqueda', busqueda);
      if (sistemaOrigen) params.append('sistema_origen', sistemaOrigen);
      if (soloConReceta) params.append('solo_con_receta', 'true');
      if (margenBajo) params.append('margen_bajo', 'true');
      
      const res = await fetch(`${API_URL}/api/costos-margenes/productos?${params}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      
      if (data.detail) throw new Error(data.detail);
      
      setProductos(data.productos || []);
      setTotalProductos(data.total || 0);
      setTotalPages(data.total_pages || 1);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [token, page, pageSize, busqueda, sistemaOrigen, soloConReceta, margenBajo]);
  
  // Efecto inicial
  useEffect(() => {
    loadResumen();
    loadSyncStatus();
  }, [loadResumen, loadSyncStatus]);
  
  // Efecto para cargar productos cuando cambian filtros
  useEffect(() => {
    loadProductos();
  }, [loadProductos]);
  
  // Manejar búsqueda con debounce
  const handleSearch = (e) => {
    setBusqueda(e.target.value);
    setPage(1);
  };
  
  return (
    <div className="p-6 bg-gray-50 min-h-screen">
      {/* Header */}
      <div className="flex justify-between items-start mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-800">Costos y Márgenes</h1>
          <p className="text-gray-500 text-sm mt-1">
            Análisis de recetas, insumos y márgenes de productos
          </p>
        </div>
        
        {/* Sync Status */}
        <div className="bg-white rounded-lg shadow-sm border p-3">
          <div className="text-xs text-gray-500 mb-1">Estado de Sincronización</div>
          {syncStatus ? (
            <SyncStatusBadge 
              status={syncStatus.estado} 
              lastSync={syncStatus.fecha_ultima_sincronizacion}
              syncRunId={syncStatus.ultimo_sync_run_id}
            />
          ) : (
            <span className="text-gray-400">Cargando...</span>
          )}
        </div>
      </div>
      
      {/* Tarjetas de Resumen */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <SummaryCard
          title="Total Productos"
          value={resumen?.total_productos?.toLocaleString() || '-'}
          icon={Package}
          color="blue"
        />
        <SummaryCard
          title="Con Receta"
          value={resumen?.productos_con_receta?.toLocaleString() || '-'}
          icon={List}
          color="green"
          subtitle={resumen ? `${((resumen.productos_con_receta / resumen.total_productos) * 100).toFixed(1)}% del total` : ''}
        />
        <SummaryCard
          title="Total Recetas"
          value={resumen?.total_recetas?.toLocaleString() || '-'}
          icon={BarChart2}
          color="purple"
        />
        <SummaryCard
          title="Total Insumos"
          value={resumen?.total_insumos?.toLocaleString() || '-'}
          icon={Database}
          color="orange"
        />
      </div>
      
      {/* Filtros */}
      <div className="bg-white rounded-lg shadow-sm border p-4 mb-6">
        <div className="flex flex-wrap gap-4 items-center">
          {/* Búsqueda */}
          <div className="relative flex-1 min-w-[200px]">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              placeholder="Buscar producto..."
              value={busqueda}
              onChange={handleSearch}
              className="w-full pl-10 pr-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          
          {/* Sistema Origen */}
          <select
            value={sistemaOrigen}
            onChange={(e) => { setSistemaOrigen(e.target.value); setPage(1); }}
            className="border rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">Todos los sistemas</option>
            <option value="SOFTRESTAURANT_PRO">SoftRestaurant</option>
            <option value="MPRO">MPRO</option>
          </select>
          
          {/* Checkboxes */}
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={soloConReceta}
              onChange={(e) => { setSoloConReceta(e.target.checked); setPage(1); }}
              className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
            />
            <span className="text-sm text-gray-600">Solo con receta</span>
          </label>
          
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={margenBajo}
              onChange={(e) => { setMargenBajo(e.target.checked); setPage(1); }}
              className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
            />
            <span className="text-sm text-gray-600">Margen bajo (&lt;20%)</span>
          </label>
          
          {/* Botón refresh */}
          <button
            onClick={() => { loadResumen(); loadSyncStatus(); loadProductos(); }}
            className="p-2 border rounded-lg hover:bg-gray-100"
            title="Actualizar"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>
      </div>
      
      {/* Tabla de Productos */}
      <div className="bg-white rounded-lg shadow-sm border overflow-hidden">
        {loading ? (
          <div className="flex justify-center items-center py-12">
            <RefreshCw className="w-8 h-8 animate-spin text-blue-500" />
            <span className="ml-2 text-gray-500">Cargando productos...</span>
          </div>
        ) : error ? (
          <div className="p-4 bg-red-50 text-red-700">
            <AlertCircle className="w-5 h-5 inline mr-2" />
            Error: {error}
          </div>
        ) : (
          <>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-gray-100 text-gray-700">
                  <tr>
                    <th className="p-3 text-left">Producto</th>
                    <th className="p-3 text-left">Sistema</th>
                    <th className="p-3 text-left">Familia</th>
                    <th className="p-3 text-right">Precio Venta</th>
                    <th className="p-3 text-right">Costo Receta</th>
                    <th className="p-3 text-right">Margen $</th>
                    <th className="p-3 text-right">Margen %</th>
                    <th className="p-3 text-center">Receta</th>
                    <th className="p-3 text-center">Acciones</th>
                  </tr>
                </thead>
                <tbody>
                  {productos.length === 0 ? (
                    <tr>
                      <td colSpan="9" className="p-8 text-center text-gray-500">
                        No se encontraron productos con los filtros actuales
                      </td>
                    </tr>
                  ) : (
                    productos.map((prod) => (
                      <tr key={prod.producto_id} className="border-b hover:bg-gray-50">
                        <td className="p-3">
                          <div className="font-medium text-gray-800">{prod.nombre}</div>
                          <div className="text-xs text-gray-400">{prod.id_producto_origen}</div>
                        </td>
                        <td className="p-3">
                          <span className={`text-xs px-2 py-1 rounded ${
                            prod.sistema_origen === 'SOFTRESTAURANT_PRO'
                              ? 'bg-blue-100 text-blue-700'
                              : 'bg-purple-100 text-purple-700'
                          }`}>
                            {prod.sistema_origen === 'SOFTRESTAURANT_PRO' ? 'SR' : 'MPRO'}
                          </span>
                        </td>
                        <td className="p-3 text-gray-600 text-xs">
                          {prod.familia || 'Sin clasificar'}
                        </td>
                        <td className="p-3 text-right font-mono">
                          {formatCurrency(prod.precio_venta)}
                        </td>
                        <td className="p-3 text-right font-mono">
                          {formatCurrency(prod.costo_receta)}
                        </td>
                        <td className="p-3 text-right font-mono">
                          {prod.margen_pesos != null ? (
                            <span className={prod.margen_pesos < 0 ? 'text-red-600' : 'text-green-600'}>
                              {formatCurrency(prod.margen_pesos)}
                            </span>
                          ) : (
                            <span className="text-gray-400">Sin dato</span>
                          )}
                        </td>
                        <td className="p-3 text-right">
                          {prod.margen_porcentaje != null ? (
                            <div className="flex items-center justify-end gap-1">
                              {prod.margen_porcentaje < 20 ? (
                                <TrendingDown className="w-4 h-4 text-red-500" />
                              ) : (
                                <TrendingUp className="w-4 h-4 text-green-500" />
                              )}
                              <span className={prod.margen_porcentaje < 20 ? 'text-red-600 font-medium' : 'text-green-600'}>
                                {formatPercent(prod.margen_porcentaje)}
                              </span>
                            </div>
                          ) : (
                            <span className="text-gray-400">Sin dato</span>
                          )}
                        </td>
                        <td className="p-3 text-center">
                          {prod.tiene_receta ? (
                            <span className="text-green-600">
                              <CheckCircle className="w-4 h-4 inline" />
                              <span className="ml-1 text-xs">{prod.numero_insumos}</span>
                            </span>
                          ) : (
                            <span className="text-gray-400">-</span>
                          )}
                        </td>
                        <td className="p-3">
                          <div className="flex justify-center gap-1">
                            <button
                              onClick={() => setRecetaModal({ open: true, productoId: prod.producto_id })}
                              disabled={!prod.tiene_receta}
                              className={`p-1 rounded ${
                                prod.tiene_receta 
                                  ? 'hover:bg-blue-100 text-blue-600' 
                                  : 'text-gray-300 cursor-not-allowed'
                              }`}
                              title="Ver receta"
                            >
                              <Eye className="w-4 h-4" />
                            </button>
                            <button
                              onClick={() => setInsumosModal({ open: true, productoId: prod.producto_id })}
                              disabled={!prod.tiene_receta}
                              className={`p-1 rounded ${
                                prod.tiene_receta 
                                  ? 'hover:bg-green-100 text-green-600' 
                                  : 'text-gray-300 cursor-not-allowed'
                              }`}
                              title="Ver insumos"
                            >
                              <List className="w-4 h-4" />
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
            
            {/* Paginación */}
            <div className="p-4 border-t bg-gray-50 flex justify-between items-center">
              <div className="text-sm text-gray-500">
                Mostrando {productos.length} de {totalProductos.toLocaleString()} productos
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setPage(p => Math.max(1, p - 1))}
                  disabled={page === 1}
                  className="p-2 border rounded hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <ChevronLeft className="w-4 h-4" />
                </button>
                <span className="text-sm text-gray-600">
                  Página {page} de {totalPages}
                </span>
                <button
                  onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                  disabled={page === totalPages}
                  className="p-2 border rounded hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <ChevronRight className="w-4 h-4" />
                </button>
              </div>
            </div>
          </>
        )}
      </div>
      
      {/* Source Type Footer */}
      <div className="mt-4 text-xs text-gray-400 text-right">
        Fuente: {resumen?.source_type || 'EDARSAHUB_SQL'} | 
        Sync ID: {resumen?.sync_run_id?.substring(0, 30) || '-'}...
      </div>
      
      {/* Modales */}
      <RecetaModal
        isOpen={recetaModal.open}
        onClose={() => setRecetaModal({ open: false, productoId: null })}
        productoId={recetaModal.productoId}
        token={token}
      />
      
      <InsumosModal
        isOpen={insumosModal.open}
        onClose={() => setInsumosModal({ open: false, productoId: null })}
        productoId={insumosModal.productoId}
        token={token}
      />
    </div>
  );
};

export default CostosMargenes;
