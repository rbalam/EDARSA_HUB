import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { 
  Users, Wallet, Calendar, UserCheck, FileText, AlertTriangle,
  Search, Plus, ChevronRight, Building2, Briefcase, Clock,
  CheckCircle2, XCircle, RefreshCw, Filter, ArrowUpDown
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
        <Button size="sm" className="bg-zinc-900 text-white">
          <Plus className="h-4 w-4 mr-1" />
          Nuevo
        </Button>
      </div>

      {/* Tabla */}
      <Card>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-zinc-50 border-b">
                <tr>
                  <th className="text-left p-3 font-medium">Nombre</th>
                  <th className="text-left p-3 font-medium">RFC</th>
                  <th className="text-left p-3 font-medium">Sucursal</th>
                  <th className="text-left p-3 font-medium">Puesto</th>
                  <th className="text-left p-3 font-medium">Estatus</th>
                  <th className="text-left p-3 font-medium">Acciones</th>
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
                      <td className="p-3 text-zinc-600">{col.RFC || '-'}</td>
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
                        <Button variant="ghost" size="sm">
                          <ChevronRight className="h-4 w-4" />
                        </Button>
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
          Nueva Incidencia
        </Button>
      </div>

      <Card>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-zinc-50 border-b">
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
    </div>
  );
}
