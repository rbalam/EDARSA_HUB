/**
 * FASE 1C-3F: Pantalla de Costos y Márgenes + Simulación y Solicitudes de Precio
 * ==============================================================================
 * Consume endpoints NO-LIVE de EDARSAHUB SQL
 * 
 * Endpoints utilizados:
 * - GET /api/costos-margenes/resumen
 * - GET /api/costos-margenes/productos
 * - GET /api/costos-margenes/productos/{id}/receta
 * - GET /api/costos-margenes/productos/{id}/insumos
 * - GET /api/costos-margenes/sync-status
 * - POST /api/costos-margenes/simulacion (NUEVO FASE 1C-3F)
 * - GET/POST /api/costos-margenes/solicitudes-precio (NUEVO FASE 1C-3F)
 * - POST /api/costos-margenes/solicitudes-precio/{id}/enviar|aprobar|rechazar|aplicar
 */

import React, { useState, useEffect, useCallback, useMemo } from 'react';
import {
  Package, DollarSign, BarChart2, RefreshCw, Search, Filter,
  ChevronLeft, ChevronRight, Eye, List, AlertCircle, CheckCircle,
  Clock, Database, Percent, TrendingUp, TrendingDown, X, Calculator,
  FileText, Send, Check, XCircle, Play, AlertTriangle, History, Info,
  ChevronDown, ChevronUp, Building2, Layers
} from 'lucide-react';
import api from '@/lib/api';

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
  return `${value.toFixed(1)}%`;
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

// ==================== COMPONENTES AUXILIARES ====================

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

const EstatusBadge = ({ estatus }) => {
  const estatusConfig = {
    'BORRADOR': { bg: 'bg-gray-100', text: 'text-gray-700', label: 'Borrador' },
    'SOLICITADA': { bg: 'bg-blue-100', text: 'text-blue-700', label: 'Solicitada' },
    'EN_REVISION': { bg: 'bg-yellow-100', text: 'text-yellow-700', label: 'En Revisión' },
    'APROBADA': { bg: 'bg-green-100', text: 'text-green-700', label: 'Aprobada' },
    'RECHAZADA': { bg: 'bg-red-100', text: 'text-red-700', label: 'Rechazada' },
    'CANCELADA': { bg: 'bg-gray-200', text: 'text-gray-600', label: 'Cancelada' },
    'APLICADA': { bg: 'bg-emerald-100', text: 'text-emerald-700', label: 'Aplicada' },
    'ERROR_APLICACION': { bg: 'bg-orange-100', text: 'text-orange-700', label: 'Error' },
  };
  
  const config = estatusConfig[estatus] || estatusConfig['BORRADOR'];
  
  return (
    <span className={`px-2 py-1 rounded text-xs font-medium ${config.bg} ${config.text}`}>
      {config.label}
    </span>
  );
};

// ==================== MODAL RECETA ====================

const RecetaModal = ({ isOpen, onClose, productoId, serverId, onVerSubReceta }) => {
  const [receta, setReceta] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [historialProductos, setHistorialProductos] = useState([]);
  const [productoActual, setProductoActual] = useState({ id: productoId, serverId });
  
  // Estado para drag del modal
  const [isDragging, setIsDragging] = useState(false);
  const [position, setPosition] = useState({ x: 0, y: 0 });
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });
  
  const cargarReceta = useCallback(async (id, srvId, esElaborado = false) => {
    if (!id) return;
    
    setLoading(true);
    setError(null);
    
    try {
      let url = `/costos-margenes/productos/${encodeURIComponent(id)}/receta`;
      const params = new URLSearchParams();
      if (srvId) params.append('server_id', srvId);
      if (esElaborado) params.append('es_elaborado', 'true');
      if (params.toString()) url += `?${params.toString()}`;
      
      const res = await api.get(url);
      setReceta(res.data);
    } catch (err) {
      setError(err.response?.data?.detail || err.message);
    } finally {
      setLoading(false);
    }
  }, []);
  
  useEffect(() => {
    if (isOpen && productoId) {
      setProductoActual({ id: productoId, serverId });
      setHistorialProductos([]);
      setPosition({ x: 0, y: 0 }); // Reset position on new open
      cargarReceta(productoId, serverId);
    }
  }, [isOpen, productoId, serverId, cargarReceta]);
  
  // Manejar doble click en elaborado para ver su sub-receta
  const handleVerSubReceta = (componente) => {
    if (componente.es_elaborado && componente.codigo_fuente) {
      // Guardar producto actual en historial para poder volver
      setHistorialProductos(prev => [...prev, { 
        id: productoActual.id, 
        serverId: productoActual.serverId,
        nombre: receta?.producto_nombre 
      }]);
      const nuevoId = componente.codigo_fuente;
      const nuevoServerId = receta?.server_id || productoActual.serverId;
      setProductoActual({ id: nuevoId, serverId: nuevoServerId });
      cargarReceta(nuevoId, nuevoServerId, true);
    }
  };
  
  // Volver al producto anterior
  const handleVolver = () => {
    if (historialProductos.length > 0) {
      const anterior = historialProductos[historialProductos.length - 1];
      setHistorialProductos(prev => prev.slice(0, -1));
      setProductoActual({ id: anterior.id, serverId: anterior.serverId });
      cargarReceta(anterior.id, anterior.serverId);
    }
  };
  
  // Handlers para drag
  const handleMouseDown = (e) => {
    if (e.target.closest('button')) return; // No drag si es un botón
    setIsDragging(true);
    setDragStart({ x: e.clientX - position.x, y: e.clientY - position.y });
  };
  
  const handleMouseMove = useCallback((e) => {
    if (!isDragging) return;
    setPosition({
      x: e.clientX - dragStart.x,
      y: e.clientY - dragStart.y
    });
  }, [isDragging, dragStart]);
  
  const handleMouseUp = useCallback(() => {
    setIsDragging(false);
  }, []);
  
  useEffect(() => {
    if (isDragging) {
      window.addEventListener('mousemove', handleMouseMove);
      window.addEventListener('mouseup', handleMouseUp);
      return () => {
        window.removeEventListener('mousemove', handleMouseMove);
        window.removeEventListener('mouseup', handleMouseUp);
      };
    }
  }, [isDragging, handleMouseMove, handleMouseUp]);
  
  if (!isOpen) return null;
  
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div 
        className="bg-white rounded-lg shadow-xl w-full max-w-4xl max-h-[80vh] overflow-hidden"
        style={{ 
          transform: `translate(${position.x}px, ${position.y}px)`,
          cursor: isDragging ? 'grabbing' : 'default'
        }}
      >
        <div 
          className="p-4 border-b flex justify-between items-center bg-gray-50 cursor-grab select-none"
          onMouseDown={handleMouseDown}
          style={{ cursor: isDragging ? 'grabbing' : 'grab' }}
        >
          <div className="flex items-center gap-2">
            {historialProductos.length > 0 && (
              <button 
                onClick={handleVolver}
                className="p-1 hover:bg-gray-200 rounded text-blue-600"
                title="Volver a receta anterior"
              >
                <ChevronLeft className="w-5 h-5" />
              </button>
            )}
            <h3 className="text-lg font-semibold text-gray-800">
              Receta Expandida
              {historialProductos.length > 0 && (
                <span className="ml-2 text-sm font-normal text-gray-500">
                  (Sub-receta nivel {historialProductos.length + 1})
                </span>
              )}
            </h3>
            <span className="text-xs text-gray-400 ml-2">(Arrastre para mover)</span>
          </div>
          <button onClick={onClose} className="p-1 hover:bg-gray-200 rounded">
            <X className="w-5 h-5" />
          </button>
        </div>
        
        {/* Breadcrumb de navegación */}
        {historialProductos.length > 0 && (
          <div className="px-4 py-2 bg-blue-50 border-b flex items-center gap-1 text-sm text-blue-600 overflow-x-auto">
            {historialProductos.map((p, idx) => (
              <span key={idx} className="flex items-center">
                <button 
                  onClick={() => {
                    const nuevosHistorial = historialProductos.slice(0, idx);
                    setHistorialProductos(nuevosHistorial);
                    setProductoActual({ id: p.id, serverId: p.serverId });
                    cargarReceta(p.id, p.serverId);
                  }}
                  className="hover:underline truncate max-w-[150px]"
                  title={p.nombre}
                >
                  {p.nombre}
                </button>
                <ChevronRight className="w-4 h-4 mx-1 flex-shrink-0" />
              </span>
            ))}
            <span className="font-medium truncate">{receta?.producto_nombre}</span>
          </div>
        )}
        
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
              
              <div className="text-xs text-gray-500 bg-yellow-50 p-2 rounded flex items-center gap-1">
                <Info className="w-4 h-4" />
                Haga doble click en los insumos <span className="bg-purple-100 text-purple-700 px-1 rounded">Elaborado</span> para ver su receta
              </div>
              
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
                      <tr 
                        key={idx} 
                        className={`border-b hover:bg-gray-50 ${comp.es_elaborado ? 'cursor-pointer hover:bg-purple-50' : ''}`}
                        onDoubleClick={() => comp.es_elaborado && handleVerSubReceta(comp)}
                        title={comp.es_elaborado ? 'Doble click para ver receta' : ''}
                      >
                        <td className="p-2">
                          <span className={comp.es_elaborado ? 'text-purple-600 font-medium' : ''}>
                            {comp.nombre}
                          </span>
                          {comp.es_elaborado && (
                            <span className="ml-2 text-xs bg-purple-100 text-purple-700 px-1 rounded cursor-pointer">
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

// ==================== MODAL INSUMOS ====================

const InsumosModal = ({ isOpen, onClose, productoId }) => {
  const [insumos, setInsumos] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  
  useEffect(() => {
    if (isOpen && productoId) {
      setLoading(true);
      setError(null);
      
      api.get(`/costos-margenes/productos/${productoId}/insumos`)
        .then(res => {
          setInsumos(res.data);
        })
        .catch(err => setError(err.response?.data?.detail || err.message))
        .finally(() => setLoading(false));
    }
  }, [isOpen, productoId]);
  
  if (!isOpen) return null;
  
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-3xl max-h-[80vh] overflow-hidden">
        <div className="p-4 border-b flex justify-between items-center bg-gray-50">
          <h3 className="text-lg font-semibold text-gray-800">Insumos Consolidados</h3>
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

// ==================== MODAL SIMULACIÓN DE PRECIO (FASE 1C-3F) ====================

const SimulacionPrecioModal = ({ isOpen, onClose, producto, onCrearSolicitud }) => {
  const [precioNuevo, setPrecioNuevo] = useState('');
  const [simulacion, setSimulacion] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [motivo, setMotivo] = useState('');
  const [justificacion, setJustificacion] = useState('');
  const [creandoSolicitud, setCreandoSolicitud] = useState(false);
  
  // Reset state when modal opens with new product
  useEffect(() => {
    if (isOpen && producto) {
      setPrecioNuevo('');
      setSimulacion(null);
      setError(null);
      setMotivo('');
      setJustificacion('');
    }
  }, [isOpen, producto?.producto_id]);
  
  // Calcular simulación en tiempo real
  useEffect(() => {
    if (!precioNuevo || !producto || isNaN(parseFloat(precioNuevo))) {
      setSimulacion(null);
      return;
    }
    
    const precio = parseFloat(precioNuevo);
    if (precio <= 0) {
      setSimulacion(null);
      return;
    }
    
    const costo = producto.costo_receta || 0;
    const precioActual = producto.precio_venta || 0;
    
    // Margen actual
    const margenActualPesos = precioActual - costo;
    const margenActualPct = precioActual > 0 ? (margenActualPesos / precioActual) * 100 : 0;
    
    // Margen simulado
    const margenSimuladoPesos = precio - costo;
    const margenSimuladoPct = precio > 0 ? (margenSimuladoPesos / precio) * 100 : 0;
    
    // Variación
    const variacionPesos = precio - precioActual;
    const variacionPct = precioActual > 0 ? (variacionPesos / precioActual) * 100 : 0;
    
    // Advertencias
    const advertencias = [];
    if (margenSimuladoPesos < 0) {
      advertencias.push({ tipo: 'error', mensaje: 'MARGEN NEGATIVO: El precio está por debajo del costo' });
    } else if (margenSimuladoPct < 20) {
      advertencias.push({ tipo: 'warning', mensaje: 'Margen bajo: Menor al 20% recomendado' });
    }
    if (Math.abs(variacionPct) > 15) {
      advertencias.push({ tipo: 'info', mensaje: `Variación significativa: ${variacionPct.toFixed(1)}%` });
    }
    
    setSimulacion({
      precio_actual: precioActual,
      costo_actual: costo,
      margen_actual_pesos: margenActualPesos,
      margen_actual_porcentaje: margenActualPct,
      precio_simulado: precio,
      margen_simulado_pesos: margenSimuladoPesos,
      margen_simulado_porcentaje: margenSimuladoPct,
      variacion_pesos: variacionPesos,
      variacion_porcentaje: variacionPct,
      advertencias
    });
    
  }, [precioNuevo, producto]);
  
  const handleCrearSolicitud = async () => {
    if (!motivo || motivo.length < 5) {
      setError('El motivo es obligatorio (mínimo 5 caracteres)');
      return;
    }
    
    if (!precioNuevo || parseFloat(precioNuevo) <= 0) {
      setError('El precio debe ser mayor a cero');
      return;
    }
    
    setCreandoSolicitud(true);
    setError(null);
    
    try {
      const response = await api.post('/costos-margenes/solicitudes-precio', {
        producto_id: producto.producto_id,
        server_id: producto.server_id,
        precio_solicitado: parseFloat(precioNuevo),
        motivo: motivo,
        justificacion: justificacion || null
      });
      
      onCrearSolicitud && onCrearSolicitud(response.data);
      onClose();
      
    } catch (err) {
      setError(err.response?.data?.detail?.mensaje || err.response?.data?.detail || err.message);
    } finally {
      setCreandoSolicitud(false);
    }
  };
  
  if (!isOpen || !producto) return null;
  
  const tieneReceta = producto.tiene_receta;
  const costoNull = producto.costo_receta === null || producto.costo_receta === undefined;
  const precioNull = producto.precio_venta === null || producto.precio_venta === undefined;
  
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-2xl max-h-[90vh] overflow-hidden">
        <div className="p-4 border-b flex justify-between items-center bg-gradient-to-r from-blue-600 to-blue-700">
          <div className="flex items-center gap-2 text-white">
            <Calculator className="w-5 h-5" />
            <h3 className="text-lg font-semibold">Simular Precio</h3>
          </div>
          <button onClick={onClose} className="p-1 hover:bg-blue-800 rounded text-white">
            <X className="w-5 h-5" />
          </button>
        </div>
        
        <div className="p-6 overflow-y-auto max-h-[calc(90vh-180px)]">
          {/* Información del producto */}
          <div className="bg-gray-50 rounded-lg p-4 mb-6">
            <h4 className="font-bold text-gray-800">{producto.nombre}</h4>
            <div className="flex gap-4 mt-2 text-sm text-gray-600">
              <span>Código: {producto.id_producto_origen}</span>
              <span className={`px-2 py-0.5 rounded text-xs ${
                producto.sistema_origen === 'SOFTRESTAURANT_PRO'
                  ? 'bg-blue-100 text-blue-700'
                  : 'bg-purple-100 text-purple-700'
              }`}>
                {producto.sistema_origen === 'SOFTRESTAURANT_PRO' ? 'SoftRestaurant' : 'MPRO'}
              </span>
            </div>
            {producto.familia && (
              <div className="text-xs text-gray-500 mt-1">Familia: {producto.familia}</div>
            )}
          </div>
          
          {/* Datos actuales */}
          <div className="grid grid-cols-2 gap-4 mb-6">
            <div className="bg-white border rounded-lg p-4">
              <div className="text-sm text-gray-500 mb-1">Precio Actual</div>
              <div className="text-2xl font-bold text-gray-800">
                {precioNull ? 'Sin precio' : formatCurrency(producto.precio_venta)}
              </div>
            </div>
            <div className="bg-white border rounded-lg p-4">
              <div className="text-sm text-gray-500 mb-1">Costo Actual</div>
              <div className="text-2xl font-bold text-gray-800">
                {costoNull ? 'Sin costo' : formatCurrency(producto.costo_receta)}
              </div>
              {!tieneReceta && (
                <div className="text-xs text-orange-600 mt-1 flex items-center gap-1">
                  <AlertTriangle className="w-3 h-3" />
                  Sin receta registrada
                </div>
              )}
            </div>
            <div className="bg-white border rounded-lg p-4">
              <div className="text-sm text-gray-500 mb-1">Margen Actual ($)</div>
              <div className={`text-xl font-bold ${
                producto.margen_pesos < 0 ? 'text-red-600' : 'text-green-600'
              }`}>
                {producto.margen_pesos !== null ? formatCurrency(producto.margen_pesos) : 'Sin dato'}
              </div>
            </div>
            <div className="bg-white border rounded-lg p-4">
              <div className="text-sm text-gray-500 mb-1">Margen Actual (%)</div>
              <div className={`text-xl font-bold ${
                producto.margen_porcentaje < 20 ? 'text-orange-600' : 'text-green-600'
              }`}>
                {producto.margen_porcentaje !== null ? formatPercent(producto.margen_porcentaje) : 'Sin dato'}
              </div>
            </div>
          </div>
          
          {/* Input de nuevo precio */}
          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Nuevo Precio Propuesto
            </label>
            <div className="relative">
              <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500">$</span>
              <input
                type="number"
                value={precioNuevo}
                onChange={(e) => setPrecioNuevo(e.target.value)}
                placeholder="0.00"
                min="0"
                step="0.01"
                className="w-full pl-8 pr-4 py-3 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-lg"
                data-testid="input-precio-nuevo"
              />
            </div>
          </div>
          
          {/* Resultados de simulación */}
          {simulacion && (
            <div className="bg-blue-50 rounded-lg p-4 mb-6">
              <h5 className="font-semibold text-blue-800 mb-3 flex items-center gap-2">
                <BarChart2 className="w-4 h-4" />
                Resultado de Simulación
              </h5>
              
              <div className="grid grid-cols-2 gap-4 mb-4">
                <div>
                  <div className="text-xs text-gray-500">Nuevo Margen ($)</div>
                  <div className={`text-lg font-bold ${
                    simulacion.margen_simulado_pesos < 0 ? 'text-red-600' : 'text-green-600'
                  }`}>
                    {formatCurrency(simulacion.margen_simulado_pesos)}
                  </div>
                </div>
                <div>
                  <div className="text-xs text-gray-500">Nuevo Margen (%)</div>
                  <div className={`text-lg font-bold ${
                    simulacion.margen_simulado_porcentaje < 20 ? 'text-orange-600' : 'text-green-600'
                  }`}>
                    {formatPercent(simulacion.margen_simulado_porcentaje)}
                  </div>
                </div>
                <div>
                  <div className="text-xs text-gray-500">Variación ($)</div>
                  <div className={`text-lg font-bold ${
                    simulacion.variacion_pesos < 0 ? 'text-red-600' : simulacion.variacion_pesos > 0 ? 'text-green-600' : ''
                  }`}>
                    {simulacion.variacion_pesos > 0 ? '+' : ''}{formatCurrency(simulacion.variacion_pesos)}
                  </div>
                </div>
                <div>
                  <div className="text-xs text-gray-500">Variación (%)</div>
                  <div className={`text-lg font-bold ${
                    simulacion.variacion_porcentaje < 0 ? 'text-red-600' : simulacion.variacion_porcentaje > 0 ? 'text-green-600' : ''
                  }`}>
                    {simulacion.variacion_porcentaje > 0 ? '+' : ''}{formatPercent(simulacion.variacion_porcentaje)}
                  </div>
                </div>
              </div>
              
              {/* Advertencias */}
              {simulacion.advertencias?.length > 0 && (
                <div className="space-y-2">
                  {simulacion.advertencias.map((adv, idx) => (
                    <div key={idx} className={`flex items-center gap-2 text-sm p-2 rounded ${
                      adv.tipo === 'error' ? 'bg-red-100 text-red-700' :
                      adv.tipo === 'warning' ? 'bg-yellow-100 text-yellow-700' :
                      'bg-blue-100 text-blue-700'
                    }`}>
                      <AlertTriangle className="w-4 h-4 flex-shrink-0" />
                      {adv.mensaje}
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
          
          {/* Campos para solicitud */}
          <div className="border-t pt-4 space-y-4">
            <h5 className="font-semibold text-gray-800">Crear Solicitud de Cambio</h5>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Motivo <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                value={motivo}
                onChange={(e) => setMotivo(e.target.value)}
                placeholder="Ej: Ajuste por competencia, promoción, revisión de costos..."
                maxLength={200}
                className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                data-testid="input-motivo"
              />
              <div className="text-xs text-gray-400 mt-1">{motivo.length}/200 caracteres</div>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Justificación Detallada (Opcional)
              </label>
              <textarea
                value={justificacion}
                onChange={(e) => setJustificacion(e.target.value)}
                placeholder="Proporcione información adicional que respalde esta solicitud..."
                rows={3}
                maxLength={2000}
                className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
                data-testid="input-justificacion"
              />
            </div>
          </div>
          
          {/* Error */}
          {error && (
            <div className="mt-4 bg-red-50 border border-red-200 rounded p-3 text-red-700 text-sm flex items-center gap-2">
              <AlertCircle className="w-4 h-4 flex-shrink-0" />
              {error}
            </div>
          )}
        </div>
        
        {/* Footer */}
        <div className="p-4 border-t bg-gray-50 flex justify-end gap-3">
          <button
            onClick={onClose}
            className="px-4 py-2 border rounded-lg hover:bg-gray-100 transition-colors"
          >
            Cancelar
          </button>
          <button
            onClick={handleCrearSolicitud}
            disabled={creandoSolicitud || !simulacion || !motivo || motivo.length < 5}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 transition-colors"
            data-testid="btn-crear-solicitud"
          >
            {creandoSolicitud ? (
              <RefreshCw className="w-4 h-4 animate-spin" />
            ) : (
              <FileText className="w-4 h-4" />
            )}
            Crear Solicitud
          </button>
        </div>
      </div>
    </div>
  );
};

// ==================== MODAL DETALLE SOLICITUD (FASE 1C-3F) ====================

const DetalleSolicitudModal = ({ isOpen, onClose, solicitudId, onAccionRealizada }) => {
  const [solicitud, setSolicitud] = useState(null);
  const [historial, setHistorial] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [ejecutandoAccion, setEjecutandoAccion] = useState(null);
  const [comentarioAccion, setComentarioAccion] = useState('');
  
  const cargarDatos = useCallback(async () => {
    if (!solicitudId) return;
    
    setLoading(true);
    setError(null);
    
    try {
      const [resSol, resHist] = await Promise.all([
        api.get(`/costos-margenes/solicitudes-precio/${solicitudId}`),
        api.get(`/costos-margenes/solicitudes-precio/${solicitudId}/historial`)
      ]);
      
      setSolicitud(resSol.data);
      setHistorial(resHist.data.historial || []);
      
    } catch (err) {
      setError(err.response?.data?.detail?.mensaje || err.response?.data?.detail || err.message);
    } finally {
      setLoading(false);
    }
  }, [solicitudId]);
  
  useEffect(() => {
    if (isOpen && solicitudId) {
      cargarDatos();
    }
  }, [isOpen, solicitudId, cargarDatos]);
  
  const ejecutarAccion = async (accion) => {
    if (accion === 'rechazar' && !comentarioAccion) {
      setError('El motivo de rechazo es obligatorio');
      return;
    }
    
    setEjecutandoAccion(accion);
    setError(null);
    
    try {
      const response = await api.post(
        `/costos-margenes/solicitudes-precio/${solicitudId}/${accion}`,
        comentarioAccion ? { comentario: comentarioAccion } : {}
      );
      
      setComentarioAccion('');
      await cargarDatos();
      onAccionRealizada && onAccionRealizada(response.data);
      
    } catch (err) {
      setError(err.response?.data?.detail?.mensaje || err.response?.data?.detail || `Error al ${accion}`);
    } finally {
      setEjecutandoAccion(null);
    }
  };
  
  if (!isOpen) return null;
  
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-3xl max-h-[90vh] overflow-hidden">
        <div className="p-4 border-b flex justify-between items-center bg-gradient-to-r from-indigo-600 to-indigo-700">
          <div className="flex items-center gap-2 text-white">
            <FileText className="w-5 h-5" />
            <h3 className="text-lg font-semibold">Detalle de Solicitud</h3>
          </div>
          <button onClick={onClose} className="p-1 hover:bg-indigo-800 rounded text-white">
            <X className="w-5 h-5" />
          </button>
        </div>
        
        <div className="p-6 overflow-y-auto max-h-[calc(90vh-180px)]">
          {loading && (
            <div className="flex justify-center py-8">
              <RefreshCw className="w-8 h-8 animate-spin text-blue-500" />
            </div>
          )}
          
          {error && (
            <div className="bg-red-50 border border-red-200 rounded p-3 text-red-700 text-sm mb-4 flex items-center gap-2">
              <AlertCircle className="w-4 h-4 flex-shrink-0" />
              {error}
            </div>
          )}
          
          {solicitud && !loading && (
            <div className="space-y-6">
              {/* Header solicitud */}
              <div className="flex justify-between items-start">
                <div>
                  <div className="text-sm text-gray-500">Folio</div>
                  <div className="text-lg font-bold text-gray-800">{solicitud.folio_solicitud}</div>
                </div>
                <EstatusBadge estatus={solicitud.estatus} />
              </div>
              
              {/* Producto */}
              <div className="bg-gray-50 rounded-lg p-4">
                <h5 className="font-semibold text-gray-800 mb-2">{solicitud.nombre_producto}</h5>
                <div className="flex flex-wrap gap-3 text-sm text-gray-600">
                  <span>Código: {solicitud.codigo_producto}</span>
                  <span className={`px-2 py-0.5 rounded text-xs ${
                    solicitud.system_type === 'SOFTRESTAURANT_PRO'
                      ? 'bg-blue-100 text-blue-700'
                      : 'bg-purple-100 text-purple-700'
                  }`}>
                    {solicitud.system_type === 'SOFTRESTAURANT_PRO' ? 'SoftRestaurant' : 'MPRO'}
                  </span>
                  {solicitud.familia_nombre && <span>Familia: {solicitud.familia_nombre}</span>}
                </div>
              </div>
              
              {/* Comparación de precios */}
              <div className="grid grid-cols-3 gap-4">
                <div className="bg-white border rounded-lg p-4 text-center">
                  <div className="text-xs text-gray-500 mb-1">Precio Actual</div>
                  <div className="text-xl font-bold text-gray-800">{formatCurrency(solicitud.precio_actual)}</div>
                </div>
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 text-center">
                  <div className="text-xs text-blue-600 mb-1">Precio Solicitado</div>
                  <div className="text-xl font-bold text-blue-700">{formatCurrency(solicitud.precio_solicitado)}</div>
                </div>
                <div className={`rounded-lg p-4 text-center ${
                  solicitud.variacion_pesos >= 0 ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'
                }`}>
                  <div className="text-xs text-gray-500 mb-1">Variación</div>
                  <div className={`text-xl font-bold ${
                    solicitud.variacion_pesos >= 0 ? 'text-green-700' : 'text-red-700'
                  }`}>
                    {solicitud.variacion_pesos >= 0 ? '+' : ''}{formatPercent(solicitud.variacion_porcentaje)}
                  </div>
                </div>
              </div>
              
              {/* Márgenes */}
              <div className="grid grid-cols-2 gap-4">
                <div className="bg-white border rounded-lg p-4">
                  <div className="text-xs text-gray-500 mb-1">Margen Actual</div>
                  <div className="text-lg font-semibold">
                    {formatCurrency(solicitud.margen_actual_pesos)} ({formatPercent(solicitud.margen_actual_porcentaje)})
                  </div>
                </div>
                <div className="bg-white border rounded-lg p-4">
                  <div className="text-xs text-gray-500 mb-1">Margen Solicitado</div>
                  <div className={`text-lg font-semibold ${
                    solicitud.margen_solicitado_pesos < 0 ? 'text-red-600' : 
                    solicitud.margen_solicitado_porcentaje < 20 ? 'text-orange-600' : 'text-green-600'
                  }`}>
                    {formatCurrency(solicitud.margen_solicitado_pesos)} ({formatPercent(solicitud.margen_solicitado_porcentaje)})
                  </div>
                </div>
              </div>
              
              {/* Motivo y justificación */}
              <div className="space-y-3">
                <div>
                  <div className="text-sm font-medium text-gray-700">Motivo</div>
                  <div className="text-gray-600 mt-1">{solicitud.motivo}</div>
                </div>
                {solicitud.justificacion && (
                  <div>
                    <div className="text-sm font-medium text-gray-700">Justificación</div>
                    <div className="text-gray-600 mt-1 whitespace-pre-wrap">{solicitud.justificacion}</div>
                  </div>
                )}
              </div>
              
              {/* Usuarios involucrados */}
              <div className="grid grid-cols-3 gap-4 text-sm">
                <div>
                  <div className="text-gray-500">Solicitante</div>
                  <div className="font-medium">{solicitud.solicitante_nombre || solicitud.solicitante_email}</div>
                  {solicitud.fecha_solicitud && (
                    <div className="text-xs text-gray-400">{formatDate(solicitud.fecha_solicitud)}</div>
                  )}
                </div>
                {solicitud.autorizador_email && (
                  <div>
                    <div className="text-gray-500">Autorizador</div>
                    <div className="font-medium">{solicitud.autorizador_nombre || solicitud.autorizador_email}</div>
                    {solicitud.fecha_autorizacion && (
                      <div className="text-xs text-gray-400">{formatDate(solicitud.fecha_autorizacion)}</div>
                    )}
                  </div>
                )}
                {solicitud.modificador_email && (
                  <div>
                    <div className="text-gray-500">Modificador</div>
                    <div className="font-medium">{solicitud.modificador_nombre || solicitud.modificador_email}</div>
                    {solicitud.fecha_aplicacion && (
                      <div className="text-xs text-gray-400">{formatDate(solicitud.fecha_aplicacion)}</div>
                    )}
                  </div>
                )}
              </div>
              
              {/* Comentario autorización/aplicación */}
              {solicitud.comentario_autorizacion && (
                <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3">
                  <div className="text-sm font-medium text-yellow-800">Comentario de Autorización</div>
                  <div className="text-yellow-700 mt-1">{solicitud.comentario_autorizacion}</div>
                </div>
              )}
              
              {/* Historial */}
              {historial.length > 0 && (
                <div>
                  <h5 className="font-semibold text-gray-800 mb-3 flex items-center gap-2">
                    <History className="w-4 h-4" />
                    Historial de Acciones
                  </h5>
                  <div className="space-y-2">
                    {historial.map((h, idx) => (
                      <div key={idx} className="flex items-start gap-3 text-sm border-l-2 border-gray-200 pl-3 py-1">
                        <div className="flex-1">
                          <div className="font-medium text-gray-700">
                            {h.accion} → {h.estatus_nuevo}
                          </div>
                          <div className="text-gray-500">
                            {h.usuario_nombre || h.usuario_email}
                          </div>
                          {h.comentario && (
                            <div className="text-gray-600 mt-1 italic">"{h.comentario}"</div>
                          )}
                        </div>
                        <div className="text-xs text-gray-400 whitespace-nowrap">
                          {formatDate(h.fecha_accion)}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
              
              {/* Campo de comentario para acciones */}
              {solicitud.acciones_disponibles?.length > 0 && 
               (solicitud.acciones_disponibles.includes('aprobar') || 
                solicitud.acciones_disponibles.includes('rechazar') ||
                solicitud.acciones_disponibles.includes('aplicar')) && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Comentario {solicitud.acciones_disponibles.includes('rechazar') ? '(Obligatorio para rechazar)' : '(Opcional)'}
                  </label>
                  <textarea
                    value={comentarioAccion}
                    onChange={(e) => setComentarioAccion(e.target.value)}
                    placeholder="Agregue un comentario..."
                    rows={2}
                    className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
                  />
                </div>
              )}
              
              {/* Acciones */}
              {solicitud.acciones_disponibles?.length > 0 && (
                <div className="flex flex-wrap gap-2 pt-4 border-t">
                  {solicitud.acciones_disponibles.includes('enviar') && (
                    <button
                      onClick={() => ejecutarAccion('enviar')}
                      disabled={ejecutandoAccion !== null}
                      className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 flex items-center gap-2"
                    >
                      {ejecutandoAccion === 'enviar' ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
                      Enviar a Revisión
                    </button>
                  )}
                  
                  {solicitud.acciones_disponibles.includes('aprobar') && (
                    <button
                      onClick={() => ejecutarAccion('aprobar')}
                      disabled={ejecutandoAccion !== null}
                      className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 flex items-center gap-2"
                    >
                      {ejecutandoAccion === 'aprobar' ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Check className="w-4 h-4" />}
                      Aprobar
                    </button>
                  )}
                  
                  {solicitud.acciones_disponibles.includes('rechazar') && (
                    <button
                      onClick={() => ejecutarAccion('rechazar')}
                      disabled={ejecutandoAccion !== null || !comentarioAccion}
                      className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50 flex items-center gap-2"
                    >
                      {ejecutandoAccion === 'rechazar' ? <RefreshCw className="w-4 h-4 animate-spin" /> : <XCircle className="w-4 h-4" />}
                      Rechazar
                    </button>
                  )}
                  
                  {solicitud.acciones_disponibles.includes('aplicar') && (
                    <button
                      onClick={() => ejecutarAccion('aplicar')}
                      disabled={ejecutandoAccion !== null}
                      className="px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 disabled:opacity-50 flex items-center gap-2"
                    >
                      {ejecutandoAccion === 'aplicar' ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
                      Aplicar Cambio
                    </button>
                  )}
                  
                  {solicitud.acciones_disponibles.includes('cancelar') && (
                    <button
                      onClick={() => ejecutarAccion('cancelar')}
                      disabled={ejecutandoAccion !== null}
                      className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 disabled:opacity-50 flex items-center gap-2"
                    >
                      {ejecutandoAccion === 'cancelar' ? <RefreshCw className="w-4 h-4 animate-spin" /> : <X className="w-4 h-4" />}
                      Cancelar
                    </button>
                  )}
                </div>
              )}
            </div>
          )}
        </div>
        
        <div className="p-4 border-t bg-gray-50 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 border rounded-lg hover:bg-gray-100 transition-colors"
          >
            Cerrar
          </button>
        </div>
      </div>
    </div>
  );
};

// ==================== TAB PRODUCTOS (MEJORADO) ====================

const TabProductos = ({ onSimularPrecio }) => {
  const [resumen, setResumen] = useState(null);
  const [productos, setProductos] = useState([]);
  const [syncStatus, setSyncStatus] = useState(null);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(20);
  const [pageSizeAgrupado] = useState(200); // Más productos para vista agrupada
  const [totalPages, setTotalPages] = useState(1);
  const [totalProductos, setTotalProductos] = useState(0);
  const [busqueda, setBusqueda] = useState('');
  const [unidadNegocio, setUnidadNegocio] = useState('');
  const [familia, setFamilia] = useState('');
  const [subfamilia, setSubfamilia] = useState('');
  const [soloConReceta, setSoloConReceta] = useState(false);
  const [margenBajo, setMargenBajo] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [recetaModal, setRecetaModal] = useState({ open: false, productoId: null, serverId: null });
  const [insumosModal, setInsumosModal] = useState({ open: false, productoId: null, serverId: null });
  
  // Datos para filtros
  const [unidades, setUnidades] = useState([]);
  const [familias, setFamilias] = useState([]);
  const [subfamilias, setSubfamilias] = useState([]);
  const [loadingFamilias, setLoadingFamilias] = useState(false);
  
  // Vista agrupada
  const [vistaAgrupada, setVistaAgrupada] = useState(false);
  const [familiasExpandidas, setFamiliasExpandidas] = useState(new Set());
  
  // Cargar unidades de negocio (solo una vez)
  useEffect(() => {
    api.get('/costos-margenes/unidades-negocio')
      .then(res => setUnidades(res.data.unidades || []))
      .catch(err => console.error('Error cargando unidades:', err));
  }, []);
  
  // Cargar familias cuando cambie la unidad de negocio
  useEffect(() => {
    const cargarFamilias = async () => {
      setLoadingFamilias(true);
      try {
        const params = unidadNegocio ? `?servidor_id=${encodeURIComponent(unidadNegocio)}` : '';
        const res = await api.get(`/costos-margenes/familias${params}`);
        setFamilias(res.data.familias || []);
        // Limpiar familia y subfamilia si la seleccionada ya no existe
        setFamilia('');
        setSubfamilia('');
      } catch (err) {
        console.error('Error cargando familias:', err);
      } finally {
        setLoadingFamilias(false);
      }
    };
    cargarFamilias();
  }, [unidadNegocio]);
  
  // Cargar subfamilias cuando cambie la familia
  useEffect(() => {
    if (familia) {
      const params = new URLSearchParams({ familia });
      if (unidadNegocio) params.append('servidor_id', unidadNegocio);
      
      api.get(`/costos-margenes/subfamilias?${params}`)
        .then(res => setSubfamilias(res.data.subfamilias || []))
        .catch(err => console.error('Error cargando subfamilias:', err));
    } else {
      setSubfamilias([]);
      setSubfamilia('');
    }
  }, [familia, unidadNegocio]);
  
  const loadResumen = useCallback(async () => {
    try {
      const res = await api.get('/costos-margenes/resumen');
      setResumen(res.data);
    } catch (err) {
      console.error('Error cargando resumen:', err);
    }
  }, []);
  
  const loadSyncStatus = useCallback(async () => {
    try {
      const res = await api.get('/costos-margenes/sync-status');
      setSyncStatus(res.data);
    } catch (err) {
      console.error('Error cargando sync status:', err);
    }
  }, []);
  
  const loadProductos = useCallback(async () => {
    setLoading(true);
    setError(null);
    
    try {
      // Usar más productos cuando está en vista agrupada
      const currentPageSize = vistaAgrupada ? pageSizeAgrupado : pageSize;
      
      const params = new URLSearchParams({
        page: vistaAgrupada ? '1' : page.toString(),
        page_size: currentPageSize.toString()
      });
      
      if (busqueda) params.append('busqueda', busqueda);
      if (unidadNegocio) params.append('servidor_id', unidadNegocio);
      if (familia) params.append('familia', familia);
      if (subfamilia) params.append('subfamilia', subfamilia);
      if (soloConReceta) params.append('solo_con_receta', 'true');
      if (margenBajo) params.append('margen_bajo', 'true');
      
      const res = await api.get(`/costos-margenes/productos?${params}`);
      
      setProductos(res.data.productos || []);
      setTotalProductos(res.data.total || 0);
      setTotalPages(vistaAgrupada ? 1 : (res.data.total_pages || 1));
    } catch (err) {
      setError(err.response?.data?.detail || err.message);
    } finally {
      setLoading(false);
    }
  }, [page, pageSize, pageSizeAgrupado, vistaAgrupada, busqueda, unidadNegocio, familia, subfamilia, soloConReceta, margenBajo]);
  
  useEffect(() => {
    loadResumen();
    loadSyncStatus();
  }, [loadResumen, loadSyncStatus]);
  
  useEffect(() => {
    loadProductos();
  }, [loadProductos]);
  
  // Recargar cuando cambie vista agrupada
  useEffect(() => {
    loadProductos();
  }, [vistaAgrupada]); // eslint-disable-line react-hooks/exhaustive-deps
  
  const handleSearch = (e) => {
    setBusqueda(e.target.value);
    setPage(1);
  };
  
  // Agrupar productos por familia
  const productosAgrupados = useMemo(() => {
    if (!vistaAgrupada) return null;
    
    const grupos = {};
    productos.forEach(p => {
      const fam = p.familia || 'Sin clasificar';
      if (!grupos[fam]) {
        grupos[fam] = [];
      }
      grupos[fam].push(p);
    });
    
    return Object.entries(grupos).sort((a, b) => a[0].localeCompare(b[0]));
  }, [productos, vistaAgrupada]);
  
  const toggleFamilia = (fam) => {
    setFamiliasExpandidas(prev => {
      const next = new Set(prev);
      if (next.has(fam)) {
        next.delete(fam);
      } else {
        next.add(fam);
      }
      return next;
    });
  };
  
  return (
    <div className="space-y-6">
      {/* Tarjetas de Resumen */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
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
      
      {/* Sync Status */}
      <div className="flex justify-end">
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
      
      {/* Filtros */}
      <div className="bg-white rounded-lg shadow-sm border p-4">
        <div className="flex flex-wrap gap-4 items-center">
          <div className="relative flex-1 min-w-[200px]">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              placeholder="Buscar producto..."
              value={busqueda}
              onChange={handleSearch}
              className="w-full pl-10 pr-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              data-testid="search-productos"
            />
          </div>
          
          {/* Filtro por Unidad de Negocio */}
          <select
            value={unidadNegocio}
            onChange={(e) => { setUnidadNegocio(e.target.value); setPage(1); }}
            className="border rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 min-w-[180px]"
            data-testid="filtro-unidad"
          >
            <option value="">Todas las unidades</option>
            {unidades.map(u => (
              <option key={u.server_id} value={u.server_id}>{u.nombre}</option>
            ))}
          </select>
          
          {/* Filtro por Familia */}
          <select
            value={familia}
            onChange={(e) => { setFamilia(e.target.value); setSubfamilia(''); setPage(1); }}
            className="border rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 min-w-[180px]"
            data-testid="filtro-familia"
          >
            <option value="">Todas las familias</option>
            {familias.map(f => (
              <option key={f.familia} value={f.familia}>{f.familia} ({f.total_productos})</option>
            ))}
          </select>
          
          {/* Filtro por Subfamilia (solo si hay familia seleccionada) */}
          {subfamilias.length > 0 && (
            <select
              value={subfamilia}
              onChange={(e) => { setSubfamilia(e.target.value); setPage(1); }}
              className="border rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 min-w-[180px]"
              data-testid="filtro-subfamilia"
            >
              <option value="">Todas las subfamilias</option>
              {subfamilias.map(sf => (
                <option key={sf.subfamilia} value={sf.subfamilia}>{sf.subfamilia} ({sf.total_productos})</option>
              ))}
            </select>
          )}
          
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
          
          {/* Toggle vista agrupada */}
          <button
            onClick={() => setVistaAgrupada(!vistaAgrupada)}
            className={`px-3 py-2 border rounded-lg flex items-center gap-2 transition-colors ${
              vistaAgrupada ? 'bg-blue-100 border-blue-300 text-blue-700' : 'hover:bg-gray-100'
            }`}
            title={vistaAgrupada ? 'Vista lista' : 'Vista agrupada por familia'}
          >
            <Layers className="w-4 h-4" />
            <span className="text-sm hidden sm:inline">
              {vistaAgrupada ? 'Vista lista' : 'Agrupar'}
            </span>
          </button>
          
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
        ) : vistaAgrupada && productosAgrupados ? (
          /* Vista agrupada por familia */
          <div className="divide-y">
            {productosAgrupados.map(([fam, prods]) => (
              <div key={fam}>
                <button
                  onClick={() => toggleFamilia(fam)}
                  className="w-full px-4 py-3 flex items-center justify-between bg-gray-50 hover:bg-gray-100 transition-colors"
                >
                  <div className="flex items-center gap-2">
                    {familiasExpandidas.has(fam) ? (
                      <ChevronUp className="w-5 h-5 text-gray-500" />
                    ) : (
                      <ChevronDown className="w-5 h-5 text-gray-500" />
                    )}
                    <span className="font-semibold text-gray-800">{fam}</span>
                    <span className="text-sm text-gray-500">({prods.length} productos)</span>
                  </div>
                </button>
                
                {familiasExpandidas.has(fam) && (
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead className="bg-gray-100 text-gray-700">
                        <tr>
                          <th className="p-3 text-left">Producto</th>
                          <th className="p-3 text-left">Unidad</th>
                          <th className="p-3 text-right">Precio Venta</th>
                          <th className="p-3 text-right">Costo Receta</th>
                          <th className="p-3 text-right">Margen $</th>
                          <th className="p-3 text-right">Margen %</th>
                          <th className="p-3 text-center">Receta</th>
                          <th className="p-3 text-center">Acciones</th>
                        </tr>
                      </thead>
                      <tbody>
                        {prods.map((prod) => (
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
                            <td className="p-3 text-right font-mono">{formatCurrency(prod.precio_venta)}</td>
                            <td className="p-3 text-right font-mono">{formatCurrency(prod.costo_receta)}</td>
                            <td className="p-3 text-right font-mono">
                              {prod.margen_pesos != null ? (
                                <span className={prod.margen_pesos < 0 ? 'text-red-600' : 'text-green-600'}>
                                  {formatCurrency(prod.margen_pesos)}
                                </span>
                              ) : <span className="text-gray-400">Sin dato</span>}
                            </td>
                            <td className="p-3 text-right">
                              {prod.margen_porcentaje != null ? (
                                <span className={prod.margen_porcentaje < 20 ? 'text-red-600 font-medium' : 'text-green-600'}>
                                  {formatPercent(prod.margen_porcentaje)}
                                </span>
                              ) : <span className="text-gray-400">Sin dato</span>}
                            </td>
                            <td className="p-3 text-center">
                              {prod.tiene_receta ? (
                                <span className="text-green-600">
                                  <CheckCircle className="w-4 h-4 inline" />
                                  <span className="ml-1 text-xs">{prod.numero_insumos}</span>
                                </span>
                              ) : <span className="text-gray-400">-</span>}
                            </td>
                            <td className="p-3">
                              <div className="flex justify-center gap-1">
                                <button
                                  onClick={() => setRecetaModal({ open: true, productoId: prod.producto_id, serverId: prod.server_id })}
                                  disabled={!prod.tiene_receta}
                                  className={`p-1 rounded ${prod.tiene_receta ? 'hover:bg-blue-100 text-blue-600' : 'text-gray-300 cursor-not-allowed'}`}
                                  title="Ver receta"
                                >
                                  <Eye className="w-4 h-4" />
                                </button>
                                <button
                                  onClick={() => onSimularPrecio(prod)}
                                  className="p-1 rounded hover:bg-yellow-100 text-yellow-600"
                                  title="Simular precio"
                                >
                                  <Calculator className="w-4 h-4" />
                                </button>
                              </div>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            ))}
          </div>
        ) : (
          /* Vista lista (original) */
          <>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-gray-100 text-gray-700">
                  <tr>
                    <th className="p-3 text-left">Producto</th>
                    <th className="p-3 text-left">Unidad</th>
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
                      <tr key={prod.producto_id} className="border-b hover:bg-gray-50" data-testid={`producto-row-${prod.producto_id}`}>
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
                              onClick={() => setRecetaModal({ open: true, productoId: prod.producto_id, serverId: prod.server_id })}
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
                              onClick={() => setInsumosModal({ open: true, productoId: prod.producto_id, serverId: prod.server_id })}
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
                            <button
                              onClick={() => onSimularPrecio(prod)}
                              className="p-1 rounded hover:bg-yellow-100 text-yellow-600"
                              title="Simular precio"
                              data-testid={`btn-simular-${prod.producto_id}`}
                            >
                              <Calculator className="w-4 h-4" />
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
      <div className="text-xs text-gray-400 text-right">
        Fuente: {resumen?.source_type || 'EDARSAHUB_SQL'} | 
        Sync ID: {resumen?.sync_run_id?.substring(0, 30) || '-'}...
      </div>
      
      {/* Modales */}
      <RecetaModal
        isOpen={recetaModal.open}
        onClose={() => setRecetaModal({ open: false, productoId: null, serverId: null })}
        productoId={recetaModal.productoId}
        serverId={recetaModal.serverId}
      />
      
      <InsumosModal
        isOpen={insumosModal.open}
        onClose={() => setInsumosModal({ open: false, productoId: null, serverId: null })}
        productoId={insumosModal.productoId}
      />
    </div>
  );
};

// ==================== TAB SOLICITUDES DE PRECIO (FASE 1C-3F) ====================

const TabSolicitudesPrecio = () => {
  const [solicitudes, setSolicitudes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(20);
  const [totalPages, setTotalPages] = useState(1);
  const [total, setTotal] = useState(0);
  const [filtroEstatus, setFiltroEstatus] = useState('');
  const [misSolicitudes, setMisSolicitudes] = useState(false);
  const [detalleModal, setDetalleModal] = useState({ open: false, solicitudId: null });
  
  const loadSolicitudes = useCallback(async () => {
    setLoading(true);
    setError(null);
    
    try {
      const params = new URLSearchParams({
        page: page.toString(),
        page_size: pageSize.toString()
      });
      
      if (filtroEstatus) params.append('estatus', filtroEstatus);
      if (misSolicitudes) params.append('mis_solicitudes', 'true');
      
      const res = await api.get(`/costos-margenes/solicitudes-precio?${params}`);
      
      setSolicitudes(res.data.solicitudes || []);
      setTotal(res.data.total || 0);
      setTotalPages(res.data.total_pages || 1);
      
    } catch (err) {
      setError(err.response?.data?.detail?.mensaje || err.response?.data?.detail || err.message);
    } finally {
      setLoading(false);
    }
  }, [page, pageSize, filtroEstatus, misSolicitudes]);
  
  useEffect(() => {
    loadSolicitudes();
  }, [loadSolicitudes]);
  
  return (
    <div className="space-y-6">
      {/* Filtros */}
      <div className="bg-white rounded-lg shadow-sm border p-4">
        <div className="flex flex-wrap gap-4 items-center">
          <select
            value={filtroEstatus}
            onChange={(e) => { setFiltroEstatus(e.target.value); setPage(1); }}
            className="border rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            data-testid="filtro-estatus"
          >
            <option value="">Todos los estados</option>
            <option value="BORRADOR">Borrador</option>
            <option value="SOLICITADA">Solicitada</option>
            <option value="EN_REVISION">En Revisión</option>
            <option value="APROBADA">Aprobada</option>
            <option value="RECHAZADA">Rechazada</option>
            <option value="APLICADA">Aplicada</option>
            <option value="CANCELADA">Cancelada</option>
          </select>
          
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={misSolicitudes}
              onChange={(e) => { setMisSolicitudes(e.target.checked); setPage(1); }}
              className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
            />
            <span className="text-sm text-gray-600">Solo mis solicitudes</span>
          </label>
          
          <button
            onClick={loadSolicitudes}
            className="p-2 border rounded-lg hover:bg-gray-100"
            title="Actualizar"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
          
          <div className="flex-1" />
          
          <div className="text-sm text-gray-500">
            {total} solicitud{total !== 1 ? 'es' : ''}
          </div>
        </div>
      </div>
      
      {/* Tabla de Solicitudes */}
      <div className="bg-white rounded-lg shadow-sm border overflow-hidden">
        {loading ? (
          <div className="flex justify-center items-center py-12">
            <RefreshCw className="w-8 h-8 animate-spin text-blue-500" />
            <span className="ml-2 text-gray-500">Cargando solicitudes...</span>
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
                    <th className="p-3 text-left">Folio</th>
                    <th className="p-3 text-left">Producto</th>
                    <th className="p-3 text-left">Sistema</th>
                    <th className="p-3 text-right">Precio Actual</th>
                    <th className="p-3 text-right">Precio Solicitado</th>
                    <th className="p-3 text-right">Variación</th>
                    <th className="p-3 text-center">Estado</th>
                    <th className="p-3 text-left">Solicitante</th>
                    <th className="p-3 text-left">Fecha</th>
                    <th className="p-3 text-center">Acciones</th>
                  </tr>
                </thead>
                <tbody>
                  {solicitudes.length === 0 ? (
                    <tr>
                      <td colSpan="10" className="p-8 text-center text-gray-500">
                        <FileText className="w-12 h-12 mx-auto mb-2 text-gray-300" />
                        No hay solicitudes de cambio de precio
                      </td>
                    </tr>
                  ) : (
                    solicitudes.map((sol) => (
                      <tr key={sol.solicitud_id} className="border-b hover:bg-gray-50" data-testid={`solicitud-row-${sol.solicitud_id}`}>
                        <td className="p-3 font-mono text-xs">{sol.folio_solicitud}</td>
                        <td className="p-3">
                          <div className="font-medium text-gray-800 truncate max-w-[200px]" title={sol.nombre_producto}>
                            {sol.nombre_producto}
                          </div>
                          <div className="text-xs text-gray-400">{sol.codigo_producto}</div>
                        </td>
                        <td className="p-3">
                          <span className={`text-xs px-2 py-1 rounded ${
                            sol.system_type === 'SOFTRESTAURANT_PRO'
                              ? 'bg-blue-100 text-blue-700'
                              : 'bg-purple-100 text-purple-700'
                          }`}>
                            {sol.system_type === 'SOFTRESTAURANT_PRO' ? 'SR' : 'MPRO'}
                          </span>
                        </td>
                        <td className="p-3 text-right font-mono">{formatCurrency(sol.precio_actual)}</td>
                        <td className="p-3 text-right font-mono font-medium">{formatCurrency(sol.precio_solicitado)}</td>
                        <td className="p-3 text-right">
                          <span className={`font-medium ${
                            sol.variacion_porcentaje < 0 ? 'text-red-600' : 
                            sol.variacion_porcentaje > 0 ? 'text-green-600' : ''
                          }`}>
                            {sol.variacion_porcentaje > 0 ? '+' : ''}{formatPercent(sol.variacion_porcentaje)}
                          </span>
                        </td>
                        <td className="p-3 text-center">
                          <EstatusBadge estatus={sol.estatus} />
                        </td>
                        <td className="p-3 text-xs text-gray-600">{sol.solicitante_email}</td>
                        <td className="p-3 text-xs text-gray-500">{formatDate(sol.fecha_solicitud)}</td>
                        <td className="p-3 text-center">
                          <button
                            onClick={() => setDetalleModal({ open: true, solicitudId: sol.solicitud_id })}
                            className="p-1 rounded hover:bg-blue-100 text-blue-600"
                            title="Ver detalle"
                            data-testid={`btn-detalle-${sol.solicitud_id}`}
                          >
                            <Eye className="w-4 h-4" />
                          </button>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
            
            {/* Paginación */}
            {totalPages > 1 && (
              <div className="p-4 border-t bg-gray-50 flex justify-between items-center">
                <div className="text-sm text-gray-500">
                  Mostrando {solicitudes.length} de {total} solicitudes
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
            )}
          </>
        )}
      </div>
      
      {/* Modal de detalle */}
      <DetalleSolicitudModal
        isOpen={detalleModal.open}
        onClose={() => setDetalleModal({ open: false, solicitudId: null })}
        solicitudId={detalleModal.solicitudId}
        onAccionRealizada={loadSolicitudes}
      />
    </div>
  );
};

// ==================== COMPONENTE PRINCIPAL ====================

const CostosMargenes = () => {
  const [activeTab, setActiveTab] = useState('productos');
  const [simulacionModal, setSimulacionModal] = useState({ open: false, producto: null });
  
  const handleSimularPrecio = (producto) => {
    setSimulacionModal({ open: true, producto });
  };
  
  const handleSolicitudCreada = (solicitud) => {
    // Cambiar a tab de solicitudes
    setActiveTab('solicitudes');
  };
  
  return (
    <div className="p-6 bg-gray-50 min-h-screen">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-800">Costos y Márgenes</h1>
        <p className="text-gray-500 text-sm mt-1">
          Análisis de recetas, insumos, márgenes y gestión de precios
        </p>
      </div>
      
      {/* Tabs */}
      <div className="mb-6">
        <div className="border-b border-gray-200">
          <nav className="flex gap-4">
            <button
              onClick={() => setActiveTab('productos')}
              className={`py-3 px-1 border-b-2 font-medium text-sm transition-colors ${
                activeTab === 'productos'
                  ? 'border-blue-600 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
              data-testid="tab-productos"
            >
              <div className="flex items-center gap-2">
                <Package className="w-4 h-4" />
                Resumen / Productos
              </div>
            </button>
            <button
              onClick={() => setActiveTab('solicitudes')}
              className={`py-3 px-1 border-b-2 font-medium text-sm transition-colors ${
                activeTab === 'solicitudes'
                  ? 'border-blue-600 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
              data-testid="tab-solicitudes"
            >
              <div className="flex items-center gap-2">
                <FileText className="w-4 h-4" />
                Solicitudes de Precio
              </div>
            </button>
          </nav>
        </div>
      </div>
      
      {/* Contenido del Tab */}
      {activeTab === 'productos' && (
        <TabProductos onSimularPrecio={handleSimularPrecio} />
      )}
      
      {activeTab === 'solicitudes' && (
        <TabSolicitudesPrecio />
      )}
      
      {/* Modal de simulación */}
      <SimulacionPrecioModal
        isOpen={simulacionModal.open}
        onClose={() => setSimulacionModal({ open: false, producto: null })}
        producto={simulacionModal.producto}
        onCrearSolicitud={handleSolicitudCreada}
      />
    </div>
  );
};

export default CostosMargenes;
