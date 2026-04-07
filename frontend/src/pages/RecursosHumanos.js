import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { 
  Users, Wallet, Calendar, UserCheck, FileText, AlertTriangle,
  Search, Plus, ChevronRight, Building2, Briefcase, Clock,
  CheckCircle2, XCircle, RefreshCw, Filter, ArrowUpDown,
  X, Save, Upload, Trash2, Eye, Edit, UserPlus, FileSpreadsheet
} from 'lucide-react';
import { toast } from 'sonner';

const API_URL = process.env.REACT_APP_BACKEND_URL || '';

export default function RecursosHumanos() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [loading, setLoading] = useState(false);
  
  // Data states
  const [dashboard, setDashboard] = useState(null);
  const [colaboradores, setColaboradores] = useState([]);
  const [incidencias, setIncidencias] = useState([]);
  const [flujos, setFlujos] = useState([]);
  const [sucursales, setSucursales] = useState([]);
  const [puestos, setPuestos] = useState([]);
  
  // Filters
  const [filtroSucursal, setFiltroSucursal] = useState('');
  const [filtroBuscar, setFiltroBuscar] = useState('');
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  
  // Modal states - FASE 2
  const [modalColaborador, setModalColaborador] = useState(false);
  const [modalIncidencia, setModalIncidencia] = useState(false);
  const [modalDetalle, setModalDetalle] = useState(false);
  const [modalImportExcel, setModalImportExcel] = useState(false);
  const [editingColaborador, setEditingColaborador] = useState(null);
  const [detalleColaborador, setDetalleColaborador] = useState(null);
  const [loadingDetalle, setLoadingDetalle] = useState(false);
  const [savingForm, setSavingForm] = useState(false);
  
  // Estados para importar Excel
  const [importFile, setImportFile] = useState(null);
  const [importLoading, setImportLoading] = useState(false);
  const [importResult, setImportResult] = useState(null);
  
  // Form states
  const [formColaborador, setFormColaborador] = useState({
    nombre_completo: '',
    curp: '',
    rfc: '',
    clabe_bancaria: '',
    sucursal_id: '',
    puesto_id: '',
    estatus_laboral: 'Activo'
  });
  
  const [formIncidencia, setFormIncidencia] = useState({
    colaborador_id: '',
    tipo_incidencia: '',
    monto: 0,
    unidades: 0,
    fecha_incidencia: new Date().toISOString().split('T')[0]
  });

  const token = localStorage.getItem('token');

  const fetchWithAuth = useCallback(async (url) => {
    const response = await fetch(`${API_URL}${url}`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    if (!response.ok) throw new Error('Error en la petición');
    return response.json();
  }, [token]);

  // Cargar dashboard
  const loadDashboard = useCallback(async () => {
    try {
      setLoading(true);
      const data = await fetchWithAuth('/api/rrhh/dashboard');
      setDashboard(data);
    } catch (error) {
      console.error('Error cargando dashboard:', error);
    } finally {
      setLoading(false);
    }
  }, [fetchWithAuth]);

  // Cargar catálogos
  const loadCatalogos = useCallback(async () => {
    try {
      const [sucData, puestosData] = await Promise.all([
        fetchWithAuth('/api/rrhh/catalogos/sucursales'),
        fetchWithAuth('/api/rrhh/catalogos/puestos')
      ]);
      setSucursales(sucData.sucursales || []);
      setPuestos(puestosData.puestos || []);
    } catch (error) {
      console.error('Error cargando catálogos:', error);
    }
  }, [fetchWithAuth]);

  // Cargar colaboradores
  const loadColaboradores = useCallback(async () => {
    try {
      setLoading(true);
      let url = `/api/rrhh/colaboradores?page=${page}&limit=50`;
      if (filtroSucursal) url += `&sucursal_id=${filtroSucursal}`;
      if (filtroBuscar) url += `&buscar=${encodeURIComponent(filtroBuscar)}`;
      
      const data = await fetchWithAuth(url);
      setColaboradores(data.colaboradores || []);
      setTotalPages(data.pages || 1);
    } catch (error) {
      console.error('Error cargando colaboradores:', error);
    } finally {
      setLoading(false);
    }
  }, [fetchWithAuth, page, filtroSucursal, filtroBuscar]);

  // Cargar incidencias
  const loadIncidencias = useCallback(async () => {
    try {
      setLoading(true);
      let url = `/api/rrhh/incidencias?page=1&limit=100`;
      if (filtroSucursal) url += `&sucursal_id=${filtroSucursal}`;
      
      const data = await fetchWithAuth(url);
      setIncidencias(data.incidencias || []);
    } catch (error) {
      console.error('Error cargando incidencias:', error);
    } finally {
      setLoading(false);
    }
  }, [fetchWithAuth, filtroSucursal]);

  // Cargar flujos de nómina
  const loadFlujos = useCallback(async () => {
    try {
      setLoading(true);
      let url = `/api/rrhh/nominas/flujo`;
      if (filtroSucursal) url += `?sucursal_id=${filtroSucursal}`;
      
      const data = await fetchWithAuth(url);
      setFlujos(data.flujos || []);
    } catch (error) {
      console.error('Error cargando flujos:', error);
    } finally {
      setLoading(false);
    }
  }, [fetchWithAuth, filtroSucursal]);

  // Initial load
  useEffect(() => {
    loadDashboard();
    loadCatalogos();
  }, [loadDashboard, loadCatalogos]);

  // Load data based on tab
  useEffect(() => {
    if (activeTab === 'colaboradores') loadColaboradores();
    if (activeTab === 'incidencias') loadIncidencias();
    if (activeTab === 'nomina') loadFlujos();
  }, [activeTab, loadColaboradores, loadIncidencias, loadFlujos]);

  // ===================== FUNCIONES CRUD - FASE 2 =====================
  
  // Abrir modal para nuevo colaborador
  const handleNuevoColaborador = () => {
    setEditingColaborador(null);
    setFormColaborador({
      nombre_completo: '',
      curp: '',
      rfc: '',
      clabe_bancaria: '',
      sucursal_id: '',
      puesto_id: '',
      estatus_laboral: 'Activo'
    });
    setModalColaborador(true);
  };
  
  // Abrir modal para editar colaborador
  const handleEditarColaborador = (col) => {
    setEditingColaborador(col);
    setFormColaborador({
      nombre_completo: col.Nombre_Completo || '',
      curp: col.CURP || '',
      rfc: col.RFC || '',
      clabe_bancaria: col.CLABE_Bancaria || '',
      sucursal_id: col.SucursalID?.toString() || '',
      puesto_id: col.PuestoID?.toString() || '',
      estatus_laboral: col.Estatus_Laboral || 'Activo'
    });
    setModalColaborador(true);
  };
  
  // Guardar colaborador (crear o actualizar)
  const handleGuardarColaborador = async () => {
    if (!formColaborador.nombre_completo || !formColaborador.sucursal_id || !formColaborador.puesto_id) {
      toast.error('Nombre, sucursal y puesto son requeridos');
      return;
    }
    
    setSavingForm(true);
    try {
      const url = editingColaborador 
        ? `${API_URL}/api/rrhh/colaboradores/${editingColaborador.ColaboradorID}`
        : `${API_URL}/api/rrhh/colaboradores`;
      
      const method = editingColaborador ? 'PUT' : 'POST';
      
      const response = await fetch(url, {
        method,
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(formColaborador)
      });
      
      if (!response.ok) throw new Error('Error al guardar');
      
      toast.success(editingColaborador ? 'Colaborador actualizado' : 'Colaborador creado');
      setModalColaborador(false);
      loadColaboradores();
    } catch (error) {
      console.error('Error:', error);
      toast.error('Error al guardar colaborador');
    } finally {
      setSavingForm(false);
    }
  };
  
  // Ver detalle de colaborador
  const handleVerDetalle = async (col) => {
    setLoadingDetalle(true);
    setModalDetalle(true);
    try {
      const data = await fetchWithAuth(`/api/rrhh/colaboradores/${col.ColaboradorID}`);
      setDetalleColaborador(data);
    } catch (error) {
      console.error('Error:', error);
      toast.error('Error al cargar detalle');
    } finally {
      setLoadingDetalle(false);
    }
  };
  
  // Dar de baja colaborador
  const handleDarBaja = async (col) => {
    if (!window.confirm(`¿Seguro que deseas dar de baja a ${col.Nombre_Completo}?`)) return;
    
    try {
      const response = await fetch(`${API_URL}/api/rrhh/colaboradores/${col.ColaboradorID}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (!response.ok) throw new Error('Error al dar de baja');
      
      toast.success('Colaborador dado de baja');
      loadColaboradores();
    } catch (error) {
      console.error('Error:', error);
      toast.error('Error al dar de baja');
    }
  };
  
  // Abrir modal nueva incidencia
  const handleNuevaIncidencia = (colaboradorId = '') => {
    setFormIncidencia({
      colaborador_id: colaboradorId?.toString() || '',
      tipo_incidencia: '',
      monto: 0,
      unidades: 0,
      fecha_incidencia: new Date().toISOString().split('T')[0]
    });
    setModalIncidencia(true);
  };
  
  // Guardar incidencia
  const handleGuardarIncidencia = async () => {
    if (!formIncidencia.colaborador_id || !formIncidencia.tipo_incidencia || !formIncidencia.fecha_incidencia) {
      toast.error('Colaborador, tipo y fecha son requeridos');
      return;
    }
    
    setSavingForm(true);
    try {
      const response = await fetch(`${API_URL}/api/rrhh/incidencias`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(formIncidencia)
      });
      
      if (!response.ok) throw new Error('Error al guardar');
      
      toast.success('Incidencia registrada');
      setModalIncidencia(false);
      loadIncidencias();
    } catch (error) {
      console.error('Error:', error);
      toast.error('Error al guardar incidencia');
    } finally {
      setSavingForm(false);
    }
  };

  // Tipos de incidencia
  const tiposIncidencia = [
    'Falta', 'Retardo', 'Bono', 'Descuento', 'Horas Extra', 
    'Vacaciones', 'Incapacidad', 'Permiso', 'Comision', 'Otro'
  ];

  // ===================== FUNCIONES IMPORTAR EXCEL =====================
  
  // Abrir modal importar Excel
  const handleAbrirImportExcel = () => {
    setImportFile(null);
    setImportResult(null);
    setModalImportExcel(true);
  };
  
  // Descargar plantilla Excel
  const handleDescargarPlantilla = async () => {
    try {
      const response = await fetch(`${API_URL}/api/rrhh/incidencias/plantilla-excel`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (!response.ok) throw new Error('Error al descargar');
      
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'plantilla_incidencias.xlsx';
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
      
      toast.success('Plantilla descargada');
    } catch (error) {
      console.error('Error:', error);
      toast.error('Error al descargar plantilla');
    }
  };
  
  // Importar archivo Excel
  const handleImportarExcel = async () => {
    if (!importFile) {
      toast.error('Selecciona un archivo Excel');
      return;
    }
    
    setImportLoading(true);
    setImportResult(null);
    
    try {
      const formData = new FormData();
      formData.append('file', importFile);
      
      const response = await fetch(`${API_URL}/api/rrhh/incidencias/importar-excel`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
        body: formData
      });
      
      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.detail || 'Error al importar');
      }
      
      setImportResult(data);
      
      if (data.registros_importados > 0) {
        toast.success(`${data.registros_importados} incidencias importadas`);
        loadIncidencias();
      }
      
      if (data.total_errores > 0) {
        toast.warning(`${data.total_errores} errores encontrados`);
      }
      
    } catch (error) {
      console.error('Error:', error);
      toast.error(error.message || 'Error al importar archivo');
    } finally {
      setImportLoading(false);
    }
  };

  // ===================== FIN FUNCIONES CRUD =====================

  // Tabs config
  const tabs = [
    { id: 'dashboard', label: 'Dashboard', icon: Building2 },
    { id: 'colaboradores', label: 'Colaboradores', icon: Users },
    { id: 'incidencias', label: 'Incidencias', icon: AlertTriangle },
    { id: 'nomina', label: 'Flujo Nómina', icon: Wallet },
    { id: 'asistencia', label: 'Asistencia', icon: Clock },
  ];

  // Render Dashboard
  const renderDashboard = () => {
    const resumen = dashboard?.resumen || {};
    const porDepto = dashboard?.por_departamento || [];
    const incMes = dashboard?.incidencias_mes || [];
    const flujosPend = dashboard?.flujos_pendientes || [];
    const alertas = dashboard?.alertas_fraude || 0;

    return (
      <div className="space-y-6">
        {/* KPIs */}
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          <Card className="bg-gradient-to-br from-blue-500 to-blue-600 text-white">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-blue-100 text-xs">Total</p>
                  <p className="text-2xl font-bold">{resumen.total || 0}</p>
                </div>
                <Users className="h-8 w-8 text-blue-200" />
              </div>
            </CardContent>
          </Card>
          
          <Card className="bg-gradient-to-br from-green-500 to-green-600 text-white">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-green-100 text-xs">Activos</p>
                  <p className="text-2xl font-bold">{resumen.activos || 0}</p>
                </div>
                <CheckCircle2 className="h-8 w-8 text-green-200" />
              </div>
            </CardContent>
          </Card>
          
          <Card className="bg-gradient-to-br from-amber-500 to-amber-600 text-white">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-amber-100 text-xs">Vacaciones</p>
                  <p className="text-2xl font-bold">{resumen.vacaciones || 0}</p>
                </div>
                <Calendar className="h-8 w-8 text-amber-200" />
              </div>
            </CardContent>
          </Card>
          
          <Card className="bg-gradient-to-br from-purple-500 to-purple-600 text-white">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-purple-100 text-xs">Incapacidad</p>
                  <p className="text-2xl font-bold">{resumen.incapacidad || 0}</p>
                </div>
                <FileText className="h-8 w-8 text-purple-200" />
              </div>
            </CardContent>
          </Card>
          
          <Card className={`${alertas > 0 ? 'bg-gradient-to-br from-red-500 to-red-600' : 'bg-gradient-to-br from-zinc-500 to-zinc-600'} text-white`}>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-red-100 text-xs">Alertas Fraude</p>
                  <p className="text-2xl font-bold">{alertas}</p>
                </div>
                <AlertTriangle className="h-8 w-8 text-red-200" />
              </div>
            </CardContent>
          </Card>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Por departamento */}
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium flex items-center gap-2">
                <Briefcase className="h-4 w-4" />
                Por Departamento
              </CardTitle>
            </CardHeader>
            <CardContent>
              {porDepto.length === 0 ? (
                <p className="text-sm text-zinc-400 text-center py-4">Sin datos</p>
              ) : (
                <div className="space-y-2">
                  {porDepto.map((d, i) => (
                    <div key={i} className="flex items-center justify-between py-2 border-b last:border-0">
                      <span className="text-sm">{d.Departamento}</span>
                      <span className="font-medium">{d.total}</span>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Incidencias del mes */}
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium flex items-center gap-2">
                <AlertTriangle className="h-4 w-4" />
                Incidencias del Mes
              </CardTitle>
            </CardHeader>
            <CardContent>
              {incMes.length === 0 ? (
                <p className="text-sm text-zinc-400 text-center py-4">Sin incidencias este mes</p>
              ) : (
                <div className="space-y-2">
                  {incMes.map((inc, i) => (
                    <div key={i} className="flex items-center justify-between py-2 border-b last:border-0">
                      <span className="text-sm">{inc.Tipo_Incidencia}</span>
                      <div className="text-right">
                        <span className="font-medium">{inc.cantidad}</span>
                        {inc.monto_total > 0 && (
                          <span className="text-xs text-zinc-500 ml-2">
                            ${(inc.monto_total || 0).toLocaleString()}
                          </span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Flujos pendientes */}
          <Card className="md:col-span-2">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium flex items-center gap-2">
                <Wallet className="h-4 w-4" />
                Flujos de Nómina Pendientes
              </CardTitle>
            </CardHeader>
            <CardContent>
              {flujosPend.length === 0 ? (
                <p className="text-sm text-zinc-400 text-center py-4">Todos los flujos han sido procesados</p>
              ) : (
                <div className="flex flex-wrap gap-3">
                  {flujosPend.map((f, i) => (
                    <div key={i} className="px-3 py-2 bg-amber-50 border border-amber-200 rounded-lg">
                      <span className="text-sm font-medium text-amber-700">{f.Estatus_Flujo}</span>
                      <span className="ml-2 text-amber-600">({f.cantidad})</span>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    );
  };

  // Render Colaboradores
  const renderColaboradores = () => (
    <div className="space-y-4">
      {/* Filtros */}
      <div className="flex flex-wrap gap-3">
        <div className="relative flex-1 min-w-[200px]">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-zinc-400" />
          <Input
            placeholder="Buscar por nombre, RFC o CURP..."
            value={filtroBuscar}
            onChange={(e) => setFiltroBuscar(e.target.value)}
            className="pl-10"
          />
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
        <Button variant="outline" size="sm" onClick={loadColaboradores}>
          <RefreshCw className="h-4 w-4 mr-1" />
          Actualizar
        </Button>
        <Button size="sm" className="bg-zinc-900 text-white" onClick={handleNuevoColaborador}>
          <UserPlus className="h-4 w-4 mr-1" />
          Nuevo Colaborador
        </Button>
      </div>

      {/* Tabla */}
      <Card>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-zinc-800 text-white">
                <tr>
                  <th className="text-left p-3 font-medium">Nombre</th>
                  <th className="text-left p-3 font-medium">RFC</th>
                  <th className="text-left p-3 font-medium">Sucursal</th>
                  <th className="text-left p-3 font-medium">Puesto</th>
                  <th className="text-left p-3 font-medium">Estatus</th>
                  <th className="text-center p-3 font-medium">Acciones</th>
                </tr>
              </thead>
              <tbody>
                {colaboradores.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="text-center py-8 text-zinc-400">
                      No hay colaboradores registrados
                    </td>
                  </tr>
                ) : (
                  colaboradores.map((col, i) => (
                    <tr key={col.ColaboradorID || i} className="border-b hover:bg-zinc-50">
                      <td className="p-3 font-medium">{col.Nombre_Completo}</td>
                      <td className="p-3 text-zinc-600 font-mono text-xs">{col.RFC || '-'}</td>
                      <td className="p-3">{col.Nombre_Sucursal || '-'}</td>
                      <td className="p-3">{col.Puesto || '-'}</td>
                      <td className="p-3">
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                          col.Estatus_Laboral === 'Activo' ? 'bg-green-100 text-green-700' :
                          col.Estatus_Laboral === 'Baja' ? 'bg-red-100 text-red-700' :
                          'bg-amber-100 text-amber-700'
                        }`}>
                          {col.Estatus_Laboral || 'Sin estatus'}
                        </span>
                      </td>
                      <td className="p-3">
                        <div className="flex items-center justify-center gap-1">
                          <Button variant="ghost" size="sm" onClick={() => handleVerDetalle(col)} title="Ver detalle">
                            <Eye className="h-4 w-4 text-blue-600" />
                          </Button>
                          <Button variant="ghost" size="sm" onClick={() => handleEditarColaborador(col)} title="Editar">
                            <Edit className="h-4 w-4 text-amber-600" />
                          </Button>
                          <Button variant="ghost" size="sm" onClick={() => handleNuevaIncidencia(col.ColaboradorID)} title="Nueva incidencia">
                            <AlertTriangle className="h-4 w-4 text-purple-600" />
                          </Button>
                          {col.Estatus_Laboral === 'Activo' && (
                            <Button variant="ghost" size="sm" onClick={() => handleDarBaja(col)} title="Dar de baja">
                              <Trash2 className="h-4 w-4 text-red-600" />
                            </Button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* Paginación */}
      {totalPages > 1 && (
        <div className="flex justify-center gap-2">
          <Button 
            variant="outline" 
            size="sm" 
            disabled={page === 1}
            onClick={() => setPage(p => p - 1)}
          >
            Anterior
          </Button>
          <span className="px-3 py-2 text-sm">
            Página {page} de {totalPages}
          </span>
          <Button 
            variant="outline" 
            size="sm" 
            disabled={page === totalPages}
            onClick={() => setPage(p => p + 1)}
          >
            Siguiente
          </Button>
        </div>
      )}
    </div>
  );

  // Render Incidencias
  const renderIncidencias = () => (
    <div className="space-y-4">
      <div className="flex flex-wrap gap-3 justify-between">
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
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={handleAbrirImportExcel}>
            <FileSpreadsheet className="h-4 w-4 mr-1" />
            Importar Excel
          </Button>
          <Button size="sm" className="bg-zinc-900 text-white" onClick={() => handleNuevaIncidencia()}>
            <Plus className="h-4 w-4 mr-1" />
            Nueva Incidencia
          </Button>
        </div>
      </div>

      <Card>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-zinc-800 text-white">
                <tr>
                  <th className="text-left p-3 font-medium">Colaborador</th>
                  <th className="text-left p-3 font-medium">Sucursal</th>
                  <th className="text-left p-3 font-medium">Tipo</th>
                  <th className="text-left p-3 font-medium">Fecha</th>
                  <th className="text-right p-3 font-medium">Monto</th>
                  <th className="text-right p-3 font-medium">Unidades</th>
                </tr>
              </thead>
              <tbody>
                {incidencias.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="text-center py-8 text-zinc-400">
                      No hay incidencias registradas
                    </td>
                  </tr>
                ) : (
                  incidencias.map((inc, i) => (
                    <tr key={inc.IncidenciaID || i} className="border-b hover:bg-zinc-50">
                      <td className="p-3 font-medium">{inc.Nombre_Completo}</td>
                      <td className="p-3">{inc.Nombre_Sucursal || '-'}</td>
                      <td className="p-3">
                        <span className={`px-2 py-1 rounded text-xs font-medium ${
                          inc.Tipo_Incidencia === 'Falta' ? 'bg-red-100 text-red-700' :
                          inc.Tipo_Incidencia === 'Bono' ? 'bg-green-100 text-green-700' :
                          'bg-zinc-100 text-zinc-700'
                        }`}>
                          {inc.Tipo_Incidencia}
                        </span>
                      </td>
                      <td className="p-3 text-zinc-600">
                        {inc.Fecha_Incidencia ? new Date(inc.Fecha_Incidencia).toLocaleDateString('es-MX') : '-'}
                      </td>
                      <td className="p-3 text-right">${(inc.Monto || 0).toLocaleString()}</td>
                      <td className="p-3 text-right">{inc.Unidades || 0}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );

  // Render Flujo Nómina
  const renderFlujoNomina = () => {
    const estatusConfig = {
      'Captura': { color: 'bg-zinc-100 text-zinc-700', icon: FileText },
      'Enviado_RH': { color: 'bg-blue-100 text-blue-700', icon: Clock },
      'Validacion_Gerente': { color: 'bg-amber-100 text-amber-700', icon: UserCheck },
      'Rechazado_Gerente': { color: 'bg-red-100 text-red-700', icon: XCircle },
      'Autorizacion_DG': { color: 'bg-purple-100 text-purple-700', icon: CheckCircle2 },
      'Enviado_Tesoreria': { color: 'bg-indigo-100 text-indigo-700', icon: Wallet },
      'Pagado': { color: 'bg-green-100 text-green-700', icon: CheckCircle2 },
    };

    return (
      <div className="space-y-4">
        <div className="flex justify-between">
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
          <Button size="sm" className="bg-zinc-900 text-white">
            <Plus className="h-4 w-4 mr-1" />
            Nuevo Periodo
          </Button>
        </div>

        <Card>
          <CardContent className="p-0">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-zinc-50 border-b">
                  <tr>
                    <th className="text-left p-3 font-medium">Sucursal</th>
                    <th className="text-left p-3 font-medium">Semana/Año</th>
                    <th className="text-left p-3 font-medium">Estatus</th>
                    <th className="text-left p-3 font-medium">Entrega RH</th>
                    <th className="text-left p-3 font-medium">Validación</th>
                    <th className="text-left p-3 font-medium">Autorización</th>
                    <th className="text-left p-3 font-medium">Pago</th>
                    <th className="text-left p-3 font-medium">Acciones</th>
                  </tr>
                </thead>
                <tbody>
                  {flujos.length === 0 ? (
                    <tr>
                      <td colSpan={8} className="text-center py-8 text-zinc-400">
                        No hay flujos de nómina registrados
                      </td>
                    </tr>
                  ) : (
                    flujos.map((f, i) => {
                      const config = estatusConfig[f.Estatus_Flujo] || estatusConfig['Captura'];
                      return (
                        <tr key={f.FlujoID || i} className="border-b hover:bg-zinc-50">
                          <td className="p-3 font-medium">{f.Nombre_Sucursal}</td>
                          <td className="p-3">{f.Semana_Anio}</td>
                          <td className="p-3">
                            <span className={`px-2 py-1 rounded text-xs font-medium ${config.color}`}>
                              {f.Estatus_Flujo?.replace('_', ' ')}
                            </span>
                          </td>
                          <td className="p-3 text-xs text-zinc-500">
                            {f.Hora_Entrega_RH ? new Date(f.Hora_Entrega_RH).toLocaleString('es-MX') : '-'}
                          </td>
                          <td className="p-3 text-xs text-zinc-500">
                            {f.Hora_Validacion_Gerente ? new Date(f.Hora_Validacion_Gerente).toLocaleString('es-MX') : '-'}
                          </td>
                          <td className="p-3 text-xs text-zinc-500">
                            {f.Hora_Autorizacion_DG ? new Date(f.Hora_Autorizacion_DG).toLocaleString('es-MX') : '-'}
                          </td>
                          <td className="p-3 text-xs text-zinc-500">
                            {f.Hora_Pago_Ejecutado ? new Date(f.Hora_Pago_Ejecutado).toLocaleString('es-MX') : '-'}
                          </td>
                          <td className="p-3">
                            <Button variant="ghost" size="sm">
                              <ChevronRight className="h-4 w-4" />
                            </Button>
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

  // Render Asistencia (placeholder)
  const renderAsistencia = () => (
    <Card className="border-2 border-dashed border-zinc-300">
      <CardContent className="py-12 text-center">
        <Clock className="h-12 w-12 text-zinc-300 mx-auto mb-4" />
        <h3 className="text-lg font-medium text-zinc-600 mb-2">Control de Asistencia</h3>
        <p className="text-zinc-400 text-sm">
          Módulo de reloj checador en desarrollo.<br />
          Conectará con RH_Reloj_Checador de EDARSA HUB.
        </p>
      </CardContent>
    </Card>
  );

  return (
    <div className="p-6" data-testid="rrhh-page">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-zinc-800">Recursos Humanos</h1>
        <p className="text-zinc-500">Gestión del capital humano - Conectado a EDARSA HUB</p>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 mb-6 overflow-x-auto pb-2">
        {tabs.map(tab => {
          const Icon = tab.icon;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium whitespace-nowrap transition-all ${
                activeTab === tab.id 
                  ? 'bg-zinc-900 text-white' 
                  : 'bg-zinc-100 text-zinc-600 hover:bg-zinc-200'
              }`}
            >
              <Icon className="h-4 w-4" />
              {tab.label}
            </button>
          );
        })}
      </div>

      {/* Content */}
      {loading && (
        <div className="flex justify-center py-8">
          <RefreshCw className="h-6 w-6 animate-spin text-zinc-400" />
        </div>
      )}

      {!loading && (
        <>
          {activeTab === 'dashboard' && renderDashboard()}
          {activeTab === 'colaboradores' && renderColaboradores()}
          {activeTab === 'incidencias' && renderIncidencias()}
          {activeTab === 'nomina' && renderFlujoNomina()}
          {activeTab === 'asistencia' && renderAsistencia()}
        </>
      )}

      {/* ==================== MODALES FASE 2 ==================== */}
      
      {/* Modal Nuevo/Editar Colaborador */}
      {modalColaborador && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-2xl w-full max-w-lg max-h-[90vh] overflow-hidden flex flex-col">
            <div className="bg-zinc-800 text-white px-6 py-4 flex items-center justify-between">
              <h2 className="text-lg font-semibold flex items-center gap-2">
                <UserPlus className="h-5 w-5" />
                {editingColaborador ? 'Editar Colaborador' : 'Nuevo Colaborador'}
              </h2>
              <button onClick={() => setModalColaborador(false)} className="p-1 hover:bg-white/20 rounded">
                <X className="h-5 w-5" />
              </button>
            </div>
            
            <div className="p-6 space-y-4 overflow-y-auto">
              <div>
                <Label className="text-sm font-medium">Nombre Completo *</Label>
                <Input
                  value={formColaborador.nombre_completo}
                  onChange={(e) => setFormColaborador({...formColaborador, nombre_completo: e.target.value})}
                  placeholder="Nombre completo del colaborador"
                  className="mt-1"
                />
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label className="text-sm font-medium">CURP</Label>
                  <Input
                    value={formColaborador.curp}
                    onChange={(e) => setFormColaborador({...formColaborador, curp: e.target.value.toUpperCase()})}
                    placeholder="CURP"
                    maxLength={18}
                    className="mt-1 font-mono"
                  />
                </div>
                <div>
                  <Label className="text-sm font-medium">RFC</Label>
                  <Input
                    value={formColaborador.rfc}
                    onChange={(e) => setFormColaborador({...formColaborador, rfc: e.target.value.toUpperCase()})}
                    placeholder="RFC"
                    maxLength={13}
                    className="mt-1 font-mono"
                  />
                </div>
              </div>
              
              <div>
                <Label className="text-sm font-medium">CLABE Bancaria</Label>
                <Input
                  value={formColaborador.clabe_bancaria}
                  onChange={(e) => setFormColaborador({...formColaborador, clabe_bancaria: e.target.value.replace(/\D/g, '')})}
                  placeholder="18 dígitos"
                  maxLength={18}
                  className="mt-1 font-mono"
                />
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label className="text-sm font-medium">Sucursal *</Label>
                  <select
                    value={formColaborador.sucursal_id}
                    onChange={(e) => setFormColaborador({...formColaborador, sucursal_id: e.target.value})}
                    className="mt-1 w-full px-3 py-2 border rounded-lg text-sm"
                  >
                    <option value="">Seleccionar...</option>
                    {sucursales.map(s => (
                      <option key={s.SucursalID} value={s.SucursalID}>{s.Nombre_Sucursal}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <Label className="text-sm font-medium">Puesto *</Label>
                  <select
                    value={formColaborador.puesto_id}
                    onChange={(e) => setFormColaborador({...formColaborador, puesto_id: e.target.value})}
                    className="mt-1 w-full px-3 py-2 border rounded-lg text-sm"
                  >
                    <option value="">Seleccionar...</option>
                    {puestos.map(p => (
                      <option key={p.PuestoID} value={p.PuestoID}>{p.Nombre_Puesto}</option>
                    ))}
                  </select>
                </div>
              </div>
              
              <div>
                <Label className="text-sm font-medium">Estatus Laboral</Label>
                <select
                  value={formColaborador.estatus_laboral}
                  onChange={(e) => setFormColaborador({...formColaborador, estatus_laboral: e.target.value})}
                  className="mt-1 w-full px-3 py-2 border rounded-lg text-sm"
                >
                  <option value="Activo">Activo</option>
                  <option value="Vacaciones">Vacaciones</option>
                  <option value="Incapacidad">Incapacidad</option>
                  <option value="Permiso">Permiso</option>
                  <option value="Baja">Baja</option>
                </select>
              </div>
            </div>
            
            <div className="border-t px-6 py-4 flex justify-end gap-3 bg-zinc-50">
              <Button variant="outline" onClick={() => setModalColaborador(false)}>
                Cancelar
              </Button>
              <Button onClick={handleGuardarColaborador} disabled={savingForm} className="bg-zinc-900 text-white">
                {savingForm ? <RefreshCw className="h-4 w-4 animate-spin mr-2" /> : <Save className="h-4 w-4 mr-2" />}
                {editingColaborador ? 'Actualizar' : 'Guardar'}
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Modal Nueva Incidencia */}
      {modalIncidencia && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-2xl w-full max-w-md">
            <div className="bg-zinc-800 text-white px-6 py-4 flex items-center justify-between rounded-t-xl">
              <h2 className="text-lg font-semibold flex items-center gap-2">
                <AlertTriangle className="h-5 w-5" />
                Nueva Incidencia
              </h2>
              <button onClick={() => setModalIncidencia(false)} className="p-1 hover:bg-white/20 rounded">
                <X className="h-5 w-5" />
              </button>
            </div>
            
            <div className="p-6 space-y-4">
              <div>
                <Label className="text-sm font-medium">Colaborador *</Label>
                <select
                  value={formIncidencia.colaborador_id}
                  onChange={(e) => setFormIncidencia({...formIncidencia, colaborador_id: e.target.value})}
                  className="mt-1 w-full px-3 py-2 border rounded-lg text-sm"
                >
                  <option value="">Seleccionar colaborador...</option>
                  {colaboradores.map(c => (
                    <option key={c.ColaboradorID} value={c.ColaboradorID}>{c.Nombre_Completo}</option>
                  ))}
                </select>
              </div>
              
              <div>
                <Label className="text-sm font-medium">Tipo de Incidencia *</Label>
                <select
                  value={formIncidencia.tipo_incidencia}
                  onChange={(e) => setFormIncidencia({...formIncidencia, tipo_incidencia: e.target.value})}
                  className="mt-1 w-full px-3 py-2 border rounded-lg text-sm"
                >
                  <option value="">Seleccionar tipo...</option>
                  {tiposIncidencia.map(t => (
                    <option key={t} value={t}>{t}</option>
                  ))}
                </select>
              </div>
              
              <div>
                <Label className="text-sm font-medium">Fecha *</Label>
                <Input
                  type="date"
                  value={formIncidencia.fecha_incidencia}
                  onChange={(e) => setFormIncidencia({...formIncidencia, fecha_incidencia: e.target.value})}
                  className="mt-1"
                />
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label className="text-sm font-medium">Monto ($)</Label>
                  <Input
                    type="number"
                    value={formIncidencia.monto}
                    onChange={(e) => setFormIncidencia({...formIncidencia, monto: parseFloat(e.target.value) || 0})}
                    className="mt-1"
                    min="0"
                    step="0.01"
                  />
                </div>
                <div>
                  <Label className="text-sm font-medium">Unidades</Label>
                  <Input
                    type="number"
                    value={formIncidencia.unidades}
                    onChange={(e) => setFormIncidencia({...formIncidencia, unidades: parseFloat(e.target.value) || 0})}
                    className="mt-1"
                    min="0"
                    step="0.5"
                  />
                </div>
              </div>
            </div>
            
            <div className="border-t px-6 py-4 flex justify-end gap-3 bg-zinc-50 rounded-b-xl">
              <Button variant="outline" onClick={() => setModalIncidencia(false)}>
                Cancelar
              </Button>
              <Button onClick={handleGuardarIncidencia} disabled={savingForm} className="bg-zinc-900 text-white">
                {savingForm ? <RefreshCw className="h-4 w-4 animate-spin mr-2" /> : <Save className="h-4 w-4 mr-2" />}
                Registrar
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Modal Detalle Colaborador */}
      {modalDetalle && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-2xl w-full max-w-2xl max-h-[90vh] overflow-hidden flex flex-col">
            <div className="bg-zinc-800 text-white px-6 py-4 flex items-center justify-between">
              <h2 className="text-lg font-semibold flex items-center gap-2">
                <Users className="h-5 w-5" />
                Detalle del Colaborador
              </h2>
              <button onClick={() => setModalDetalle(false)} className="p-1 hover:bg-white/20 rounded">
                <X className="h-5 w-5" />
              </button>
            </div>
            
            <div className="p-6 overflow-y-auto flex-1">
              {loadingDetalle ? (
                <div className="flex justify-center py-8">
                  <RefreshCw className="h-8 w-8 animate-spin text-zinc-400" />
                </div>
              ) : detalleColaborador ? (
                <div className="space-y-6">
                  {/* Datos básicos */}
                  <div>
                    <h3 className="text-lg font-semibold mb-3">{detalleColaborador.colaborador?.Nombre_Completo}</h3>
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div>
                        <span className="text-zinc-500">RFC:</span>
                        <span className="ml-2 font-mono">{detalleColaborador.colaborador?.RFC || '-'}</span>
                      </div>
                      <div>
                        <span className="text-zinc-500">CURP:</span>
                        <span className="ml-2 font-mono">{detalleColaborador.colaborador?.CURP || '-'}</span>
                      </div>
                      <div>
                        <span className="text-zinc-500">Sucursal:</span>
                        <span className="ml-2">{detalleColaborador.colaborador?.Nombre_Sucursal || '-'}</span>
                      </div>
                      <div>
                        <span className="text-zinc-500">Puesto:</span>
                        <span className="ml-2">{detalleColaborador.colaborador?.Puesto || '-'}</span>
                      </div>
                      <div>
                        <span className="text-zinc-500">Estatus:</span>
                        <span className={`ml-2 px-2 py-0.5 rounded text-xs font-medium ${
                          detalleColaborador.colaborador?.Estatus_Laboral === 'Activo' ? 'bg-green-100 text-green-700' : 'bg-amber-100 text-amber-700'
                        }`}>
                          {detalleColaborador.colaborador?.Estatus_Laboral}
                        </span>
                      </div>
                      <div>
                        <span className="text-zinc-500">CLABE:</span>
                        <span className="ml-2 font-mono text-xs">{detalleColaborador.colaborador?.CLABE_Bancaria || '-'}</span>
                      </div>
                    </div>
                  </div>
                  
                  {/* Incidencias recientes */}
                  <div>
                    <h4 className="font-medium mb-2 flex items-center gap-2">
                      <AlertTriangle className="h-4 w-4" />
                      Últimas Incidencias
                    </h4>
                    {detalleColaborador.incidencias?.length === 0 ? (
                      <p className="text-sm text-zinc-400">Sin incidencias registradas</p>
                    ) : (
                      <div className="border rounded-lg overflow-hidden">
                        <table className="w-full text-sm">
                          <thead className="bg-zinc-50">
                            <tr>
                              <th className="text-left p-2">Tipo</th>
                              <th className="text-left p-2">Fecha</th>
                              <th className="text-right p-2">Monto</th>
                            </tr>
                          </thead>
                          <tbody>
                            {detalleColaborador.incidencias?.slice(0, 5).map((inc, i) => (
                              <tr key={i} className="border-t">
                                <td className="p-2">{inc.Tipo_Incidencia}</td>
                                <td className="p-2 text-zinc-500">{inc.Fecha_Incidencia ? new Date(inc.Fecha_Incidencia).toLocaleDateString('es-MX') : '-'}</td>
                                <td className="p-2 text-right">${(inc.Monto || 0).toLocaleString()}</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    )}
                  </div>
                  
                  {/* Asistencias recientes */}
                  <div>
                    <h4 className="font-medium mb-2 flex items-center gap-2">
                      <Clock className="h-4 w-4" />
                      Últimas Asistencias
                    </h4>
                    {detalleColaborador.asistencias?.length === 0 ? (
                      <p className="text-sm text-zinc-400">Sin registros de asistencia</p>
                    ) : (
                      <div className="border rounded-lg overflow-hidden">
                        <table className="w-full text-sm">
                          <thead className="bg-zinc-50">
                            <tr>
                              <th className="text-left p-2">Fecha/Hora</th>
                              <th className="text-left p-2">Tipo</th>
                            </tr>
                          </thead>
                          <tbody>
                            {detalleColaborador.asistencias?.slice(0, 5).map((a, i) => (
                              <tr key={i} className="border-t">
                                <td className="p-2 font-mono text-xs">{a.FechaHora ? new Date(a.FechaHora).toLocaleString('es-MX') : '-'}</td>
                                <td className="p-2">
                                  <span className={`px-2 py-0.5 rounded text-xs ${a.Tipo_Registro === 'Entrada' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
                                    {a.Tipo_Registro}
                                  </span>
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    )}
                  </div>
                </div>
              ) : (
                <p className="text-center text-zinc-400">No se encontró información</p>
              )}
            </div>
            
            <div className="border-t px-6 py-4 flex justify-end bg-zinc-50">
              <Button variant="outline" onClick={() => setModalDetalle(false)}>
                Cerrar
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Modal Importar Excel */}
      {modalImportExcel && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-2xl w-full max-w-lg">
            <div className="bg-zinc-800 text-white px-6 py-4 flex items-center justify-between rounded-t-xl">
              <h2 className="text-lg font-semibold flex items-center gap-2">
                <FileSpreadsheet className="h-5 w-5" />
                Importar Incidencias desde Excel
              </h2>
              <button onClick={() => setModalImportExcel(false)} className="p-1 hover:bg-white/20 rounded">
                <X className="h-5 w-5" />
              </button>
            </div>
            
            <div className="p-6 space-y-4">
              {/* Instrucciones */}
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 text-sm">
                <p className="font-medium text-blue-800 mb-2">Formato del archivo Excel:</p>
                <ul className="list-disc list-inside text-blue-700 space-y-1">
                  <li><strong>Columna A:</strong> RFC o ID del Colaborador</li>
                  <li><strong>Columna B:</strong> Tipo de Incidencia</li>
                  <li><strong>Columna C:</strong> Fecha (DD/MM/YYYY)</li>
                  <li><strong>Columna D:</strong> Monto (opcional)</li>
                  <li><strong>Columna E:</strong> Unidades (opcional)</li>
                </ul>
              </div>
              
              {/* Descargar plantilla */}
              <div className="flex items-center justify-between py-3 border-b">
                <span className="text-sm text-zinc-600">¿No tienes el formato?</span>
                <Button variant="outline" size="sm" onClick={handleDescargarPlantilla}>
                  <FileText className="h-4 w-4 mr-1" />
                  Descargar Plantilla
                </Button>
              </div>
              
              {/* Selección de archivo */}
              <div>
                <Label className="text-sm font-medium">Seleccionar archivo Excel</Label>
                <div className="mt-2">
                  <input
                    type="file"
                    accept=".xlsx,.xls"
                    onChange={(e) => setImportFile(e.target.files?.[0] || null)}
                    className="block w-full text-sm text-zinc-500
                      file:mr-4 file:py-2 file:px-4
                      file:rounded-lg file:border-0
                      file:text-sm file:font-medium
                      file:bg-zinc-100 file:text-zinc-700
                      hover:file:bg-zinc-200
                      cursor-pointer"
                  />
                </div>
                {importFile && (
                  <p className="mt-2 text-sm text-green-600 flex items-center gap-1">
                    <CheckCircle2 className="h-4 w-4" />
                    {importFile.name}
                  </p>
                )}
              </div>
              
              {/* Resultado de importación */}
              {importResult && (
                <div className={`rounded-lg p-4 ${importResult.total_errores > 0 ? 'bg-amber-50 border border-amber-200' : 'bg-green-50 border border-green-200'}`}>
                  <p className="font-medium text-green-700 mb-2">
                    ✓ {importResult.registros_importados} incidencias importadas
                  </p>
                  
                  {importResult.total_errores > 0 && (
                    <div className="mt-2">
                      <p className="text-amber-700 font-medium text-sm mb-1">
                        ⚠ {importResult.total_errores} errores encontrados:
                      </p>
                      <ul className="text-xs text-amber-600 space-y-1 max-h-32 overflow-y-auto">
                        {importResult.errores.map((err, i) => (
                          <li key={i}>{err}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              )}
            </div>
            
            <div className="border-t px-6 py-4 flex justify-end gap-3 bg-zinc-50 rounded-b-xl">
              <Button variant="outline" onClick={() => setModalImportExcel(false)}>
                {importResult ? 'Cerrar' : 'Cancelar'}
              </Button>
              {!importResult && (
                <Button 
                  onClick={handleImportarExcel} 
                  disabled={!importFile || importLoading}
                  className="bg-zinc-900 text-white"
                >
                  {importLoading ? (
                    <>
                      <RefreshCw className="h-4 w-4 animate-spin mr-2" />
                      Procesando...
                    </>
                  ) : (
                    <>
                      <Upload className="h-4 w-4 mr-2" />
                      Importar
                    </>
                  )}
                </Button>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
