import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { 
  DollarSign, TrendingUp, TrendingDown, Building2, 
  Plus, RefreshCw, Filter, X, Save, Edit, Trash2,
  ChevronUp, ChevronDown, AlertCircle, FileText, Copy,
  PieChart, BarChart3, Calendar
} from 'lucide-react';
import { toast } from 'sonner';

const API_URL = process.env.REACT_APP_BACKEND_URL || '';

export default function Finanzas() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [loading, setLoading] = useState(false);
  const [dashboard, setDashboard] = useState(null);
  const [presupuestos, setPresupuestos] = useState([]);
  const [sucursales, setSucursales] = useState([]);
  const [categorias, setCategorias] = useState([]);
  
  // Filtros
  const [filtroAnio, setFiltroAnio] = useState(new Date().getFullYear());
  const [filtroMes, setFiltroMes] = useState(new Date().getMonth() + 1);
  const [filtroSucursal, setFiltroSucursal] = useState('');
  
  // Modal states
  const [modalPresupuesto, setModalPresupuesto] = useState(false);
  const [modalScript, setModalScript] = useState(false);
  const [editingPresupuesto, setEditingPresupuesto] = useState(null);
  const [savingForm, setSavingForm] = useState(false);
  const [scriptData, setScriptData] = useState(null);
  
  // Form
  const [formPresupuesto, setFormPresupuesto] = useState({
    sucursal_id: '',
    categoria: '',
    subcategoria: '',
    tipo: 'Egreso',
    monto: 0,
    anio: new Date().getFullYear(),
    mes: new Date().getMonth() + 1,
    notas: ''
  });
  
  const token = localStorage.getItem('token');
  
  const meses = [
    'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
    'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'
  ];
  
  // Fetch helpers
  const fetchWithAuth = useCallback(async (endpoint) => {
    const response = await fetch(`${API_URL}${endpoint}`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    if (!response.ok) throw new Error('Error en la petición');
    return response.json();
  }, [token]);
  
  // Load dashboard
  const loadDashboard = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({
        anio: filtroAnio,
        mes: filtroMes,
        ...(filtroSucursal && { sucursal_id: filtroSucursal })
      });
      const data = await fetchWithAuth(`/api/finanzas/dashboard?${params}`);
      setDashboard(data);
    } catch (error) {
      console.error('Error:', error);
    } finally {
      setLoading(false);
    }
  }, [fetchWithAuth, filtroAnio, filtroMes, filtroSucursal]);
  
  // Load presupuestos
  const loadPresupuestos = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({
        anio: filtroAnio,
        ...(filtroMes && { mes: filtroMes }),
        ...(filtroSucursal && { sucursal_id: filtroSucursal })
      });
      const data = await fetchWithAuth(`/api/finanzas/presupuestos?${params}`);
      setPresupuestos(data.presupuestos || []);
    } catch (error) {
      console.error('Error:', error);
    } finally {
      setLoading(false);
    }
  }, [fetchWithAuth, filtroAnio, filtroMes, filtroSucursal]);
  
  // Load sucursales
  const loadSucursales = useCallback(async () => {
    try {
      const data = await fetchWithAuth('/api/rrhh/catalogos/sucursales');
      setSucursales(data.sucursales || []);
    } catch (error) {
      console.error('Error:', error);
    }
  }, [fetchWithAuth]);
  
  // Load categorias
  const loadCategorias = useCallback(async () => {
    try {
      const data = await fetchWithAuth('/api/finanzas/categorias');
      setCategorias(data.categorias || []);
    } catch (error) {
      console.error('Error:', error);
    }
  }, [fetchWithAuth]);
  
  // Initial load
  useEffect(() => {
    loadSucursales();
    loadCategorias();
  }, [loadSucursales, loadCategorias]);
  
  // Load data on tab change or filter change
  useEffect(() => {
    if (activeTab === 'dashboard') {
      loadDashboard();
    } else if (activeTab === 'presupuestos') {
      loadPresupuestos();
    }
  }, [activeTab, loadDashboard, loadPresupuestos]);
  
  // CRUD handlers
  const handleNuevoPresupuesto = () => {
    setEditingPresupuesto(null);
    setFormPresupuesto({
      sucursal_id: '',
      categoria: '',
      subcategoria: '',
      tipo: 'Egreso',
      monto: 0,
      anio: filtroAnio,
      mes: filtroMes,
      notas: ''
    });
    setModalPresupuesto(true);
  };
  
  const handleEditarPresupuesto = (pres) => {
    setEditingPresupuesto(pres);
    setFormPresupuesto({
      sucursal_id: pres.SucursalID?.toString() || '',
      categoria: pres.Categoria || '',
      subcategoria: pres.SubCategoria || '',
      tipo: pres.Tipo || 'Egreso',
      monto: pres.Monto_Presupuestado || 0,
      anio: pres.Anio,
      mes: pres.Mes,
      notas: pres.Notas || ''
    });
    setModalPresupuesto(true);
  };
  
  const handleGuardarPresupuesto = async () => {
    if (!formPresupuesto.sucursal_id || !formPresupuesto.categoria) {
      toast.error('Sucursal y categoría son requeridos');
      return;
    }
    
    setSavingForm(true);
    try {
      const url = editingPresupuesto 
        ? `${API_URL}/api/finanzas/presupuestos/${editingPresupuesto.PresupuestoID}`
        : `${API_URL}/api/finanzas/presupuestos`;
      
      const method = editingPresupuesto ? 'PUT' : 'POST';
      const body = editingPresupuesto 
        ? {
            monto_presupuestado: formPresupuesto.monto,
            categoria: formPresupuesto.categoria,
            subcategoria: formPresupuesto.subcategoria,
            notas: formPresupuesto.notas
          }
        : formPresupuesto;
      
      const response = await fetch(url, {
        method,
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(body)
      });
      
      if (!response.ok) throw new Error('Error al guardar');
      
      toast.success(editingPresupuesto ? 'Presupuesto actualizado' : 'Presupuesto creado');
      setModalPresupuesto(false);
      loadPresupuestos();
      loadDashboard();
    } catch (error) {
      console.error('Error:', error);
      toast.error('Error al guardar presupuesto');
    } finally {
      setSavingForm(false);
    }
  };
  
  const handleEliminarPresupuesto = async (pres) => {
    if (!window.confirm(`¿Eliminar presupuesto de ${pres.Categoria}?`)) return;
    
    try {
      const response = await fetch(`${API_URL}/api/finanzas/presupuestos/${pres.PresupuestoID}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (!response.ok) throw new Error('Error');
      
      toast.success('Presupuesto eliminado');
      loadPresupuestos();
      loadDashboard();
    } catch (error) {
      toast.error('Error al eliminar');
    }
  };
  
  const handleVerScript = async () => {
    try {
      const data = await fetchWithAuth('/api/finanzas/script-inicializacion');
      setScriptData(data);
      setModalScript(true);
    } catch (error) {
      toast.error('Error al obtener script');
    }
  };
  
  const handleCopyScript = () => {
    if (scriptData?.script) {
      navigator.clipboard.writeText(scriptData.script);
      toast.success('Script copiado al portapapeles');
    }
  };
  
  // Tabs
  const tabs = [
    { id: 'dashboard', label: 'Dashboard', icon: PieChart },
    { id: 'presupuestos', label: 'Presupuestos', icon: DollarSign },
  ];
  
  // Format currency
  const formatCurrency = (value) => {
    return new Intl.NumberFormat('es-MX', {
      style: 'currency',
      currency: 'MXN',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(value || 0);
  };
  
  // Render Dashboard
  const renderDashboard = () => {
    const kpis = dashboard?.kpis || {};
    const porSucursal = dashboard?.por_sucursal || [];
    
    // Check if tables don't exist
    if (dashboard?.nota) {
      return (
        <div className="space-y-6">
          <Card className="border-2 border-dashed border-amber-300 bg-amber-50">
            <CardContent className="py-8 text-center">
              <AlertCircle className="h-16 w-16 text-amber-500 mx-auto mb-4" />
              <h2 className="text-xl font-semibold text-amber-700 mb-2">Tablas no configuradas</h2>
              <p className="text-amber-600 mb-4">
                Las tablas de finanzas aún no han sido creadas en la base de datos EDARSA HUB.
              </p>
              <Button onClick={handleVerScript} className="bg-amber-600 hover:bg-amber-700 text-white">
                <FileText className="h-4 w-4 mr-2" />
                Ver Script de Inicialización
              </Button>
            </CardContent>
          </Card>
        </div>
      );
    }
    
    return (
      <div className="space-y-6">
        {/* Filtros */}
        <div className="flex flex-wrap gap-3 items-center">
          <div className="flex items-center gap-2">
            <Calendar className="h-4 w-4 text-zinc-400" />
            <select
              value={filtroMes}
              onChange={(e) => setFiltroMes(parseInt(e.target.value))}
              className="px-3 py-2 border rounded-lg text-sm"
            >
              {meses.map((m, i) => (
                <option key={i} value={i + 1}>{m}</option>
              ))}
            </select>
            <select
              value={filtroAnio}
              onChange={(e) => setFiltroAnio(parseInt(e.target.value))}
              className="px-3 py-2 border rounded-lg text-sm"
            >
              {[2024, 2025, 2026, 2027].map(a => (
                <option key={a} value={a}>{a}</option>
              ))}
            </select>
          </div>
          <select
            value={filtroSucursal}
            onChange={(e) => setFiltroSucursal(e.target.value)}
            className="px-3 py-2 border rounded-lg text-sm"
          >
            <option value="">Todas las sucursales</option>
            {sucursales.map(s => (
              <option key={s.SucursalID} value={s.SucursalID}>{s.Nombre_Sucursal}</option>
            ))}
          </select>
          <Button variant="outline" size="sm" onClick={loadDashboard} disabled={loading}>
            <RefreshCw className={`h-4 w-4 mr-1 ${loading ? 'animate-spin' : ''}`} />
            Actualizar
          </Button>
        </div>
        
        {/* KPIs */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* Ingresos */}
          <Card className="border-l-4 border-l-green-500">
            <CardContent className="pt-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs text-zinc-500 uppercase tracking-wide">Ingresos</p>
                  <p className="text-2xl font-bold text-green-600">{formatCurrency(kpis.ingresos_ejecutados)}</p>
                  <p className="text-xs text-zinc-400">de {formatCurrency(kpis.ingresos_presupuestados)}</p>
                </div>
                <div className={`flex items-center gap-1 text-sm ${kpis.ingresos_var_mes_ant >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                  {kpis.ingresos_var_mes_ant >= 0 ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                  {Math.abs(kpis.ingresos_var_mes_ant || 0)}%
                </div>
              </div>
            </CardContent>
          </Card>
          
          {/* Egresos */}
          <Card className="border-l-4 border-l-red-500">
            <CardContent className="pt-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs text-zinc-500 uppercase tracking-wide">Egresos</p>
                  <p className="text-2xl font-bold text-red-600">{formatCurrency(kpis.egresos_ejecutados)}</p>
                  <p className="text-xs text-zinc-400">de {formatCurrency(kpis.egresos_presupuestados)}</p>
                </div>
                <div className={`flex items-center gap-1 text-sm ${kpis.egresos_var_mes_ant <= 0 ? 'text-green-600' : 'text-red-600'}`}>
                  {kpis.egresos_var_mes_ant >= 0 ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                  {Math.abs(kpis.egresos_var_mes_ant || 0)}%
                </div>
              </div>
            </CardContent>
          </Card>
          
          {/* Utilidad */}
          <Card className="border-l-4 border-l-blue-500">
            <CardContent className="pt-4">
              <div>
                <p className="text-xs text-zinc-500 uppercase tracking-wide">Utilidad</p>
                <p className={`text-2xl font-bold ${kpis.utilidad_real >= 0 ? 'text-blue-600' : 'text-red-600'}`}>
                  {formatCurrency(kpis.utilidad_real)}
                </p>
                <p className="text-xs text-zinc-400">Presupuestada: {formatCurrency(kpis.utilidad_presupuestada)}</p>
              </div>
            </CardContent>
          </Card>
          
          {/* Margen */}
          <Card className="border-l-4 border-l-purple-500">
            <CardContent className="pt-4">
              <div>
                <p className="text-xs text-zinc-500 uppercase tracking-wide">Margen de Utilidad</p>
                <p className={`text-2xl font-bold ${kpis.margen_utilidad >= 0 ? 'text-purple-600' : 'text-red-600'}`}>
                  {kpis.margen_utilidad || 0}%
                </p>
                <p className="text-xs text-zinc-400">{meses[filtroMes - 1]} {filtroAnio}</p>
              </div>
            </CardContent>
          </Card>
        </div>
        
        {/* Por Sucursal */}
        <Card>
          <CardHeader className="py-3 bg-zinc-800 text-white rounded-t-lg">
            <CardTitle className="text-base flex items-center gap-2">
              <BarChart3 className="h-5 w-5" />
              Comparativo por Sucursal
            </CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-zinc-100">
                  <tr>
                    <th className="text-left p-3 font-medium">Sucursal</th>
                    <th className="text-right p-3 font-medium">Ingresos Pres.</th>
                    <th className="text-right p-3 font-medium">Ingresos Real</th>
                    <th className="text-right p-3 font-medium">Egresos Pres.</th>
                    <th className="text-right p-3 font-medium">Egresos Real</th>
                    <th className="text-right p-3 font-medium">Utilidad</th>
                    <th className="text-center p-3 font-medium">Cumplimiento</th>
                  </tr>
                </thead>
                <tbody>
                  {porSucursal.length === 0 ? (
                    <tr>
                      <td colSpan={7} className="text-center py-8 text-zinc-400">
                        No hay datos para el periodo seleccionado
                      </td>
                    </tr>
                  ) : (
                    porSucursal.map((suc, i) => {
                      const utilidad = (suc.Ingresos || 0) - (suc.Egresos || 0);
                      const cumplimiento = suc.Ingresos_Pres > 0 
                        ? Math.round((suc.Ingresos / suc.Ingresos_Pres) * 100) 
                        : 0;
                      
                      return (
                        <tr key={suc.SucursalID || i} className="border-b hover:bg-zinc-50">
                          <td className="p-3 font-medium">{suc.Nombre_Sucursal}</td>
                          <td className="p-3 text-right text-zinc-500">{formatCurrency(suc.Ingresos_Pres)}</td>
                          <td className="p-3 text-right text-green-600 font-medium">{formatCurrency(suc.Ingresos)}</td>
                          <td className="p-3 text-right text-zinc-500">{formatCurrency(suc.Egresos_Pres)}</td>
                          <td className="p-3 text-right text-red-600 font-medium">{formatCurrency(suc.Egresos)}</td>
                          <td className={`p-3 text-right font-bold ${utilidad >= 0 ? 'text-blue-600' : 'text-red-600'}`}>
                            {formatCurrency(utilidad)}
                          </td>
                          <td className="p-3 text-center">
                            <span className={`px-2 py-1 rounded text-xs font-medium ${
                              cumplimiento >= 100 ? 'bg-green-100 text-green-700' :
                              cumplimiento >= 80 ? 'bg-amber-100 text-amber-700' :
                              'bg-red-100 text-red-700'
                            }`}>
                              {cumplimiento}%
                            </span>
                          </td>
                        </tr>
                      );
                    })
                  )}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  };
  
  // Render Presupuestos
  const renderPresupuestos = () => (
    <div className="space-y-4">
      {/* Filtros y acciones */}
      <div className="flex flex-wrap gap-3 justify-between">
        <div className="flex flex-wrap gap-2 items-center">
          <select
            value={filtroAnio}
            onChange={(e) => setFiltroAnio(parseInt(e.target.value))}
            className="px-3 py-2 border rounded-lg text-sm"
          >
            {[2024, 2025, 2026, 2027].map(a => (
              <option key={a} value={a}>{a}</option>
            ))}
          </select>
          <select
            value={filtroMes}
            onChange={(e) => setFiltroMes(parseInt(e.target.value))}
            className="px-3 py-2 border rounded-lg text-sm"
          >
            <option value="">Todos los meses</option>
            {meses.map((m, i) => (
              <option key={i} value={i + 1}>{m}</option>
            ))}
          </select>
          <select
            value={filtroSucursal}
            onChange={(e) => setFiltroSucursal(e.target.value)}
            className="px-3 py-2 border rounded-lg text-sm"
          >
            <option value="">Todas las sucursales</option>
            {sucursales.map(s => (
              <option key={s.SucursalID} value={s.SucursalID}>{s.Nombre_Sucursal}</option>
            ))}
          </select>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={handleVerScript}>
            <FileText className="h-4 w-4 mr-1" />
            Ver Script SQL
          </Button>
          <Button size="sm" className="bg-zinc-900 text-white" onClick={handleNuevoPresupuesto}>
            <Plus className="h-4 w-4 mr-1" />
            Nuevo Presupuesto
          </Button>
        </div>
      </div>
      
      {/* Tabla */}
      <Card>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-zinc-800 text-white">
                <tr>
                  <th className="text-left p-3 font-medium">Sucursal</th>
                  <th className="text-left p-3 font-medium">Categoría</th>
                  <th className="text-center p-3 font-medium">Tipo</th>
                  <th className="text-center p-3 font-medium">Periodo</th>
                  <th className="text-right p-3 font-medium">Presupuestado</th>
                  <th className="text-right p-3 font-medium">Ejecutado</th>
                  <th className="text-center p-3 font-medium">%</th>
                  <th className="text-center p-3 font-medium">Acciones</th>
                </tr>
              </thead>
              <tbody>
                {presupuestos.length === 0 ? (
                  <tr>
                    <td colSpan={8} className="text-center py-8 text-zinc-400">
                      No hay presupuestos registrados para este periodo
                    </td>
                  </tr>
                ) : (
                  presupuestos.map((pres, i) => {
                    const porcentaje = pres.Monto_Presupuestado > 0 
                      ? Math.round((pres.Monto_Ejecutado / pres.Monto_Presupuestado) * 100) 
                      : 0;
                    
                    return (
                      <tr key={pres.PresupuestoID || i} className="border-b hover:bg-zinc-50">
                        <td className="p-3 font-medium">{pres.Nombre_Sucursal}</td>
                        <td className="p-3">
                          <div>
                            <span>{pres.Categoria}</span>
                            {pres.SubCategoria && (
                              <span className="text-xs text-zinc-400 block">{pres.SubCategoria}</span>
                            )}
                          </div>
                        </td>
                        <td className="p-3 text-center">
                          <span className={`px-2 py-1 rounded text-xs font-medium ${
                            pres.Tipo === 'Ingreso' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
                          }`}>
                            {pres.Tipo}
                          </span>
                        </td>
                        <td className="p-3 text-center text-zinc-500">
                          {meses[pres.Mes - 1]?.substring(0, 3)} {pres.Anio}
                        </td>
                        <td className="p-3 text-right font-mono">{formatCurrency(pres.Monto_Presupuestado)}</td>
                        <td className="p-3 text-right font-mono font-medium">{formatCurrency(pres.Monto_Ejecutado)}</td>
                        <td className="p-3 text-center">
                          <span className={`px-2 py-1 rounded text-xs font-medium ${
                            porcentaje >= 100 ? 'bg-green-100 text-green-700' :
                            porcentaje >= 80 ? 'bg-amber-100 text-amber-700' :
                            'bg-zinc-100 text-zinc-600'
                          }`}>
                            {porcentaje}%
                          </span>
                        </td>
                        <td className="p-3">
                          <div className="flex items-center justify-center gap-1">
                            <Button variant="ghost" size="sm" onClick={() => handleEditarPresupuesto(pres)} title="Editar">
                              <Edit className="h-4 w-4 text-amber-600" />
                            </Button>
                            <Button variant="ghost" size="sm" onClick={() => handleEliminarPresupuesto(pres)} title="Eliminar">
                              <Trash2 className="h-4 w-4 text-red-600" />
                            </Button>
                          </div>
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
  
  return (
    <div className="p-6" data-testid="finanzas-page">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-zinc-800">Finanzas y Control Presupuestal</h1>
        <p className="text-zinc-500">Gestión de presupuestos e indicadores financieros - Conectado a EDARSA HUB</p>
      </div>
      
      {/* Tabs */}
      <div className="flex gap-2 mb-6 border-b pb-2">
        {tabs.map(tab => {
          const Icon = tab.icon;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                activeTab === tab.id 
                  ? 'bg-zinc-900 text-white' 
                  : 'text-zinc-600 hover:bg-zinc-100'
              }`}
            >
              <Icon className="h-4 w-4" />
              {tab.label}
            </button>
          );
        })}
      </div>
      
      {/* Loading */}
      {loading && (
        <div className="flex justify-center py-12">
          <RefreshCw className="h-8 w-8 animate-spin text-zinc-400" />
        </div>
      )}
      
      {/* Content */}
      {!loading && (
        <>
          {activeTab === 'dashboard' && renderDashboard()}
          {activeTab === 'presupuestos' && renderPresupuestos()}
        </>
      )}
      
      {/* Modal Presupuesto */}
      {modalPresupuesto && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-2xl w-full max-w-md">
            <div className="bg-zinc-800 text-white px-6 py-4 flex items-center justify-between rounded-t-xl">
              <h2 className="text-lg font-semibold flex items-center gap-2">
                <DollarSign className="h-5 w-5" />
                {editingPresupuesto ? 'Editar Presupuesto' : 'Nuevo Presupuesto'}
              </h2>
              <button onClick={() => setModalPresupuesto(false)} className="p-1 hover:bg-white/20 rounded">
                <X className="h-5 w-5" />
              </button>
            </div>
            
            <div className="p-6 space-y-4">
              <div>
                <Label className="text-sm font-medium">Sucursal *</Label>
                <select
                  value={formPresupuesto.sucursal_id}
                  onChange={(e) => setFormPresupuesto({...formPresupuesto, sucursal_id: e.target.value})}
                  className="mt-1 w-full px-3 py-2 border rounded-lg text-sm"
                  disabled={editingPresupuesto}
                >
                  <option value="">Seleccionar...</option>
                  {sucursales.map(s => (
                    <option key={s.SucursalID} value={s.SucursalID}>{s.Nombre_Sucursal}</option>
                  ))}
                </select>
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label className="text-sm font-medium">Tipo *</Label>
                  <select
                    value={formPresupuesto.tipo}
                    onChange={(e) => setFormPresupuesto({...formPresupuesto, tipo: e.target.value})}
                    className="mt-1 w-full px-3 py-2 border rounded-lg text-sm"
                    disabled={editingPresupuesto}
                  >
                    <option value="Ingreso">Ingreso</option>
                    <option value="Egreso">Egreso</option>
                  </select>
                </div>
                <div>
                  <Label className="text-sm font-medium">Categoría *</Label>
                  <select
                    value={formPresupuesto.categoria}
                    onChange={(e) => setFormPresupuesto({...formPresupuesto, categoria: e.target.value})}
                    className="mt-1 w-full px-3 py-2 border rounded-lg text-sm"
                  >
                    <option value="">Seleccionar...</option>
                    {categorias
                      .filter(c => c.Tipo === formPresupuesto.tipo)
                      .map((c, i) => (
                        <option key={i} value={c.Categoria}>{c.Categoria}</option>
                      ))}
                  </select>
                </div>
              </div>
              
              <div>
                <Label className="text-sm font-medium">Subcategoría</Label>
                <Input
                  value={formPresupuesto.subcategoria}
                  onChange={(e) => setFormPresupuesto({...formPresupuesto, subcategoria: e.target.value})}
                  placeholder="Opcional"
                  className="mt-1"
                />
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label className="text-sm font-medium">Mes</Label>
                  <select
                    value={formPresupuesto.mes}
                    onChange={(e) => setFormPresupuesto({...formPresupuesto, mes: parseInt(e.target.value)})}
                    className="mt-1 w-full px-3 py-2 border rounded-lg text-sm"
                    disabled={editingPresupuesto}
                  >
                    {meses.map((m, i) => (
                      <option key={i} value={i + 1}>{m}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <Label className="text-sm font-medium">Año</Label>
                  <select
                    value={formPresupuesto.anio}
                    onChange={(e) => setFormPresupuesto({...formPresupuesto, anio: parseInt(e.target.value)})}
                    className="mt-1 w-full px-3 py-2 border rounded-lg text-sm"
                    disabled={editingPresupuesto}
                  >
                    {[2024, 2025, 2026, 2027].map(a => (
                      <option key={a} value={a}>{a}</option>
                    ))}
                  </select>
                </div>
              </div>
              
              <div>
                <Label className="text-sm font-medium">Monto Presupuestado</Label>
                <Input
                  type="number"
                  value={formPresupuesto.monto}
                  onChange={(e) => setFormPresupuesto({...formPresupuesto, monto: parseFloat(e.target.value) || 0})}
                  className="mt-1 font-mono"
                  min="0"
                  step="100"
                />
              </div>
              
              <div>
                <Label className="text-sm font-medium">Notas</Label>
                <textarea
                  value={formPresupuesto.notas}
                  onChange={(e) => setFormPresupuesto({...formPresupuesto, notas: e.target.value})}
                  className="mt-1 w-full px-3 py-2 border rounded-lg text-sm resize-none"
                  rows={2}
                  placeholder="Notas opcionales..."
                />
              </div>
            </div>
            
            <div className="border-t px-6 py-4 flex justify-end gap-3 bg-zinc-50 rounded-b-xl">
              <Button variant="outline" onClick={() => setModalPresupuesto(false)}>
                Cancelar
              </Button>
              <Button onClick={handleGuardarPresupuesto} disabled={savingForm} className="bg-zinc-900 text-white">
                {savingForm ? <RefreshCw className="h-4 w-4 animate-spin mr-2" /> : <Save className="h-4 w-4 mr-2" />}
                {editingPresupuesto ? 'Actualizar' : 'Guardar'}
              </Button>
            </div>
          </div>
        </div>
      )}
      
      {/* Modal Script SQL */}
      {modalScript && scriptData && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-2xl w-full max-w-3xl max-h-[90vh] overflow-hidden flex flex-col">
            <div className="bg-zinc-800 text-white px-6 py-4 flex items-center justify-between">
              <h2 className="text-lg font-semibold flex items-center gap-2">
                <FileText className="h-5 w-5" />
                Script de Inicialización - Finanzas
              </h2>
              <button onClick={() => setModalScript(false)} className="p-1 hover:bg-white/20 rounded">
                <X className="h-5 w-5" />
              </button>
            </div>
            
            <div className="p-6 space-y-4 overflow-y-auto flex-1">
              {/* Instrucciones */}
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <p className="font-medium text-blue-800 mb-2">Instrucciones:</p>
                <ol className="list-decimal list-inside text-sm text-blue-700 space-y-1">
                  {scriptData.instrucciones?.map((inst, i) => (
                    <li key={i}>{inst}</li>
                  ))}
                </ol>
              </div>
              
              {/* Script */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <Label className="font-medium">Script SQL:</Label>
                  <Button variant="outline" size="sm" onClick={handleCopyScript}>
                    <Copy className="h-4 w-4 mr-1" />
                    Copiar
                  </Button>
                </div>
                <pre className="bg-zinc-900 text-green-400 p-4 rounded-lg text-xs overflow-x-auto max-h-[400px] overflow-y-auto font-mono">
                  {scriptData.script}
                </pre>
              </div>
            </div>
            
            <div className="border-t px-6 py-4 flex justify-end bg-zinc-50">
              <Button variant="outline" onClick={() => setModalScript(false)}>
                Cerrar
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
