import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { 
  Users, CheckCircle2, XCircle, RefreshCw, Filter, 
  AlertTriangle, FileText, Building2, Search, 
  ChevronRight, Eye, Check, X, Clock, Ban,
  ArrowRight, Download, Upload
} from 'lucide-react';
import { toast } from 'sonner';

const API_URL = process.env.REACT_APP_BACKEND_URL || '';

export default function ImportadorRH() {
  const [activeTab, setActiveTab] = useState('pendientes');
  const [loading, setLoading] = useState(false);
  
  // Data states
  const [estadisticas, setEstadisticas] = useState(null);
  const [pendientes, setPendientes] = useState([]);
  const [incompletos, setIncompletos] = useState([]);
  const [excluidos, setExcluidos] = useState([]);
  
  // Filters
  const [filtroEmpresa, setFiltroEmpresa] = useState('');
  const [filtroBuscar, setFiltroBuscar] = useState('');
  
  // Modal states
  const [selectedRegistro, setSelectedRegistro] = useState(null);
  const [showDetalleModal, setShowDetalleModal] = useState(false);
  const [motivoRechazo, setMotivoRechazo] = useState('');
  const [observacion, setObservacion] = useState('');
  
  // Aprobación en lote
  const [aprobandoLote, setAprobandoLote] = useState(false);
  const [resultadoLote, setResultadoLote] = useState(null);

  const getToken = () => localStorage.getItem('token');

  const fetchEstadisticas = useCallback(async () => {
    try {
      const resp = await fetch(`${API_URL}/api/rrhh/importar/staging/estadisticas`, {
        headers: { 'Authorization': `Bearer ${getToken()}` }
      });
      if (resp.ok) {
        const data = await resp.json();
        setEstadisticas(data.data);
      }
    } catch (error) {
      console.error('Error cargando estadísticas:', error);
    }
  }, []);

  const fetchPendientes = useCallback(async () => {
    setLoading(true);
    try {
      const empresaParam = filtroEmpresa ? `&empresa=${encodeURIComponent(filtroEmpresa)}` : '';
      const resp = await fetch(`${API_URL}/api/rrhh/importar/staging/pendientes?limite=200${empresaParam}`, {
        headers: { 'Authorization': `Bearer ${getToken()}` }
      });
      if (resp.ok) {
        const data = await resp.json();
        setPendientes(data.data || []);
      }
    } catch (error) {
      console.error('Error cargando pendientes:', error);
      toast.error('Error al cargar pendientes');
    } finally {
      setLoading(false);
    }
  }, [filtroEmpresa]);

  const fetchIncompletos = useCallback(async () => {
    setLoading(true);
    try {
      const resp = await fetch(`${API_URL}/api/rrhh/importar/staging/incompletos?limite=200`, {
        headers: { 'Authorization': `Bearer ${getToken()}` }
      });
      if (resp.ok) {
        const data = await resp.json();
        setIncompletos(data.data || []);
      }
    } catch (error) {
      console.error('Error cargando incompletos:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchExcluidos = useCallback(async () => {
    setLoading(true);
    try {
      const resp = await fetch(`${API_URL}/api/rrhh/importar/staging/excluidos?limite=200`, {
        headers: { 'Authorization': `Bearer ${getToken()}` }
      });
      if (resp.ok) {
        const data = await resp.json();
        setExcluidos(data.data || []);
      }
    } catch (error) {
      console.error('Error cargando excluidos:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchEstadisticas();
  }, [fetchEstadisticas]);

  useEffect(() => {
    if (activeTab === 'pendientes') fetchPendientes();
    else if (activeTab === 'incompletos') fetchIncompletos();
    else if (activeTab === 'excluidos') fetchExcluidos();
  }, [activeTab, fetchPendientes, fetchIncompletos, fetchExcluidos]);

  // =============== ACCIONES ===============

  const aprobarRegistro = async (stagingId) => {
    try {
      const resp = await fetch(`${API_URL}/api/rrhh/importar/staging/aprobar/${stagingId}`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${getToken()}` }
      });
      const data = await resp.json();
      
      if (data.success && data.data.exito) {
        toast.success(`Aprobado: ${data.data.mensaje}`);
        fetchPendientes();
        fetchEstadisticas();
      } else {
        toast.error(`Error: ${data.data?.mensaje || 'Error desconocido'}`);
      }
    } catch (error) {
      toast.error('Error al aprobar registro');
    }
  };

  const rechazarRegistro = async (stagingId) => {
    if (!motivoRechazo || motivoRechazo.length < 5) {
      toast.error('El motivo debe tener al menos 5 caracteres');
      return;
    }
    
    try {
      const resp = await fetch(
        `${API_URL}/api/rrhh/importar/staging/rechazar/${stagingId}?motivo=${encodeURIComponent(motivoRechazo)}`,
        {
          method: 'POST',
          headers: { 'Authorization': `Bearer ${getToken()}` }
        }
      );
      const data = await resp.json();
      
      if (data.success) {
        toast.success('Registro rechazado');
        setMotivoRechazo('');
        setShowDetalleModal(false);
        fetchPendientes();
        fetchEstadisticas();
      } else {
        toast.error(data.data?.mensaje || 'Error al rechazar');
      }
    } catch (error) {
      toast.error('Error al rechazar registro');
    }
  };

  const observarRegistro = async (stagingId) => {
    if (!observacion || observacion.length < 5) {
      toast.error('La observación debe tener al menos 5 caracteres');
      return;
    }
    
    try {
      const resp = await fetch(
        `${API_URL}/api/rrhh/importar/staging/observar/${stagingId}?observacion=${encodeURIComponent(observacion)}`,
        {
          method: 'POST',
          headers: { 'Authorization': `Bearer ${getToken()}` }
        }
      );
      const data = await resp.json();
      
      if (data.success) {
        toast.success('Registro marcado para revisión');
        setObservacion('');
        setShowDetalleModal(false);
        fetchPendientes();
        fetchEstadisticas();
      } else {
        toast.error(data.data?.mensaje || 'Error al observar');
      }
    } catch (error) {
      toast.error('Error al observar registro');
    }
  };

  const aprobarLote = async () => {
    setAprobandoLote(true);
    setResultadoLote(null);
    
    try {
      const empresaParam = filtroEmpresa ? `empresa=${encodeURIComponent(filtroEmpresa)}&` : '';
      const resp = await fetch(
        `${API_URL}/api/rrhh/importar/staging/aprobar-lote?${empresaParam}limite=100`,
        {
          method: 'POST',
          headers: { 'Authorization': `Bearer ${getToken()}` }
        }
      );
      const data = await resp.json();
      
      if (data.success) {
        setResultadoLote(data.data);
        toast.success(`Lote procesado: ${data.data.exitosos} exitosos, ${data.data.fallidos} fallidos`);
        fetchPendientes();
        fetchEstadisticas();
      } else {
        toast.error('Error en aprobación en lote');
      }
    } catch (error) {
      toast.error('Error al procesar lote');
    } finally {
      setAprobandoLote(false);
    }
  };

  // =============== FILTRADO ===============

  const pendientesFiltrados = pendientes.filter(p => {
    if (!filtroBuscar) return true;
    const busq = filtroBuscar.toLowerCase();
    return (
      (p.Nombre_Completo || '').toLowerCase().includes(busq) ||
      (p.CURP || '').toLowerCase().includes(busq) ||
      (p.RFC || '').toLowerCase().includes(busq)
    );
  });

  // =============== RENDER ===============

  const TabButton = ({ id, label, icon: Icon, count }) => (
    <button
      onClick={() => setActiveTab(id)}
      className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-all ${
        activeTab === id 
          ? 'bg-blue-600 text-white' 
          : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
      }`}
    >
      <Icon className="w-4 h-4" />
      <span>{label}</span>
      {count !== undefined && (
        <span className={`px-2 py-0.5 rounded-full text-xs ${
          activeTab === id ? 'bg-white/20' : 'bg-gray-300'
        }`}>
          {count}
        </span>
      )}
    </button>
  );

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-800">Importador RH - Aprobación</h1>
          <p className="text-gray-500">Gestión de registros en staging para el catálogo maestro</p>
        </div>
        <Button onClick={fetchEstadisticas} variant="outline" className="gap-2">
          <RefreshCw className="w-4 h-4" />
          Actualizar
        </Button>
      </div>

      {/* Estadísticas */}
      {estadisticas && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card className="bg-blue-50 border-blue-200">
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-blue-100 rounded-lg">
                  <Users className="w-5 h-5 text-blue-600" />
                </div>
                <div>
                  <p className="text-sm text-blue-600">Total en Staging</p>
                  <p className="text-2xl font-bold text-blue-800">
                    {estadisticas.resumen?.total_valido || 0}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
          
          <Card className="bg-green-50 border-green-200">
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-green-100 rounded-lg">
                  <CheckCircle2 className="w-5 h-5 text-green-600" />
                </div>
                <div>
                  <p className="text-sm text-green-600">Candidatos a Aprobar</p>
                  <p className="text-2xl font-bold text-green-800">
                    {estadisticas.resumen?.candidatos_aprobacion || 0}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
          
          <Card className="bg-purple-50 border-purple-200">
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-purple-100 rounded-lg">
                  <CheckCircle2 className="w-5 h-5 text-purple-600" />
                </div>
                <div>
                  <p className="text-sm text-purple-600">Ya Procesados</p>
                  <p className="text-2xl font-bold text-purple-800">
                    {estadisticas.resumen?.ya_procesados || 0}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
          
          <Card className="bg-gray-50 border-gray-200">
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-gray-100 rounded-lg">
                  <Ban className="w-5 h-5 text-gray-600" />
                </div>
                <div>
                  <p className="text-sm text-gray-600">Excluidos</p>
                  <p className="text-2xl font-bold text-gray-800">
                    {estadisticas.resumen?.excluidos || 0}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Distribución por Empresa */}
      {estadisticas?.por_empresa && (
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-lg flex items-center gap-2">
              <Building2 className="w-5 h-5" />
              Distribución por Empresa
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              {estadisticas.por_empresa.map((e, idx) => (
                <div 
                  key={idx} 
                  className={`p-3 rounded-lg border cursor-pointer transition-all ${
                    filtroEmpresa === e.empresa 
                      ? 'border-blue-500 bg-blue-50' 
                      : 'border-gray-200 hover:border-blue-300'
                  }`}
                  onClick={() => {
                    setFiltroEmpresa(filtroEmpresa === e.empresa ? '' : e.empresa);
                    setActiveTab('pendientes');
                  }}
                >
                  <p className="font-medium text-sm truncate" title={e.empresa}>
                    {e.empresa}
                  </p>
                  <div className="flex justify-between mt-1">
                    <span className="text-xs text-gray-500">{e.total} total</span>
                    <span className="text-xs text-green-600 font-medium">{e.candidatos} listos</span>
                  </div>
                  {e.procesados > 0 && (
                    <span className="text-xs text-purple-600">{e.procesados} procesados</span>
                  )}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Tabs */}
      <div className="flex gap-2 flex-wrap">
        <TabButton 
          id="pendientes" 
          label="Pendientes" 
          icon={Clock}
          count={estadisticas?.resumen?.candidatos_aprobacion}
        />
        <TabButton 
          id="incompletos" 
          label="Incompletos" 
          icon={AlertTriangle}
          count={estadisticas?.por_estado?.Incompleto || incompletos.length}
        />
        <TabButton 
          id="excluidos" 
          label="Excluidos (Auditoría)" 
          icon={Ban}
          count={estadisticas?.por_estado?.Excluido || excluidos.length}
        />
      </div>

      {/* Contenido Principal */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between pb-2">
          <CardTitle className="text-lg">
            {activeTab === 'pendientes' && 'Registros Pendientes de Aprobación'}
            {activeTab === 'incompletos' && 'Registros Incompletos'}
            {activeTab === 'excluidos' && 'Registros Excluidos (Solo Auditoría)'}
          </CardTitle>
          
          {activeTab === 'pendientes' && pendientesFiltrados.length > 0 && (
            <Button 
              onClick={aprobarLote}
              disabled={aprobandoLote}
              className="bg-green-600 hover:bg-green-700 gap-2"
            >
              {aprobandoLote ? (
                <RefreshCw className="w-4 h-4 animate-spin" />
              ) : (
                <Check className="w-4 h-4" />
              )}
              Aprobar Lote ({filtroEmpresa || 'Todos'})
            </Button>
          )}
        </CardHeader>
        
        <CardContent>
          {/* Barra de búsqueda */}
          {activeTab === 'pendientes' && (
            <div className="mb-4 flex gap-2">
              <div className="relative flex-1">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                <Input
                  placeholder="Buscar por nombre, CURP o RFC..."
                  value={filtroBuscar}
                  onChange={(e) => setFiltroBuscar(e.target.value)}
                  className="pl-10"
                />
              </div>
              {filtroEmpresa && (
                <Button 
                  variant="outline" 
                  onClick={() => setFiltroEmpresa('')}
                  className="gap-1"
                >
                  <X className="w-4 h-4" />
                  {filtroEmpresa}
                </Button>
              )}
            </div>
          )}

          {/* Resultado de aprobación en lote */}
          {resultadoLote && (
            <div className="mb-4 p-4 bg-blue-50 rounded-lg border border-blue-200">
              <p className="font-medium text-blue-800">
                Resultado del lote: {resultadoLote.exitosos} exitosos, {resultadoLote.fallidos} fallidos
              </p>
              <button 
                className="text-sm text-blue-600 underline mt-1"
                onClick={() => setResultadoLote(null)}
              >
                Cerrar
              </button>
            </div>
          )}

          {/* Loading */}
          {loading ? (
            <div className="flex justify-center py-8">
              <RefreshCw className="w-8 h-8 animate-spin text-blue-600" />
            </div>
          ) : (
            /* Tabla de registros */
            <div className="overflow-x-auto">
              <table className="w-full text-sm" data-testid="staging-table">
                <thead>
                  <tr className="border-b bg-gray-50">
                    <th className="text-left p-2">Nombre</th>
                    <th className="text-left p-2">CURP</th>
                    <th className="text-left p-2">RFC</th>
                    <th className="text-left p-2">Empresa</th>
                    <th className="text-left p-2">Estado</th>
                    <th className="text-right p-2">Acciones</th>
                  </tr>
                </thead>
                <tbody>
                  {activeTab === 'pendientes' && pendientesFiltrados.map((r) => (
                    <tr key={r.StagingID} className="border-b hover:bg-gray-50">
                      <td className="p-2 font-medium">{r.Nombre_Completo}</td>
                      <td className="p-2 font-mono text-xs">{r.CURP || '-'}</td>
                      <td className="p-2 font-mono text-xs">{r.RFC || '-'}</td>
                      <td className="p-2 text-sm">{r.Sucursal_Nombre}</td>
                      <td className="p-2">
                        <span className="px-2 py-1 rounded-full text-xs bg-yellow-100 text-yellow-800">
                          {r.Estado}
                        </span>
                      </td>
                      <td className="p-2 text-right space-x-1">
                        <Button
                          size="sm"
                          variant="ghost"
                          className="text-green-600 hover:bg-green-50"
                          onClick={() => aprobarRegistro(r.StagingID)}
                          data-testid={`aprobar-${r.StagingID}`}
                        >
                          <Check className="w-4 h-4" />
                        </Button>
                        <Button
                          size="sm"
                          variant="ghost"
                          className="text-blue-600 hover:bg-blue-50"
                          onClick={() => {
                            setSelectedRegistro(r);
                            setShowDetalleModal(true);
                          }}
                          data-testid={`ver-${r.StagingID}`}
                        >
                          <Eye className="w-4 h-4" />
                        </Button>
                      </td>
                    </tr>
                  ))}
                  
                  {activeTab === 'incompletos' && incompletos.map((r) => (
                    <tr key={r.StagingID} className="border-b hover:bg-gray-50">
                      <td className="p-2 font-medium">{r.Nombre_Completo}</td>
                      <td className="p-2 font-mono text-xs text-red-500">{r.CURP || 'SIN CURP'}</td>
                      <td className="p-2 font-mono text-xs text-red-500">{r.RFC || 'SIN RFC'}</td>
                      <td className="p-2 text-sm">{r.Sucursal_Nombre}</td>
                      <td className="p-2">
                        <span className="px-2 py-1 rounded-full text-xs bg-red-100 text-red-800">
                          {r.Clasificacion}
                        </span>
                      </td>
                      <td className="p-2 text-right">
                        <span className="text-xs text-gray-400">No aprobable</span>
                      </td>
                    </tr>
                  ))}
                  
                  {activeTab === 'excluidos' && excluidos.map((r) => (
                    <tr key={r.StagingID} className="border-b hover:bg-gray-50 bg-gray-50">
                      <td className="p-2 font-medium text-gray-500">{r.Nombre_Completo}</td>
                      <td className="p-2 font-mono text-xs text-gray-400">{r.CURP || '-'}</td>
                      <td className="p-2 font-mono text-xs text-gray-400">{r.RFC || '-'}</td>
                      <td className="p-2 text-sm text-gray-500">{r.Sucursal_Nombre}</td>
                      <td className="p-2">
                        <span className="px-2 py-1 rounded-full text-xs bg-gray-200 text-gray-600">
                          {r.Fuente}
                        </span>
                      </td>
                      <td className="p-2 text-right">
                        <span className="text-xs text-gray-400">Excluido</span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              
              {/* Empty states */}
              {activeTab === 'pendientes' && pendientesFiltrados.length === 0 && (
                <div className="text-center py-8 text-gray-500">
                  <CheckCircle2 className="w-12 h-12 mx-auto mb-2 text-green-300" />
                  <p>No hay registros pendientes{filtroEmpresa && ` en ${filtroEmpresa}`}</p>
                </div>
              )}
              
              {activeTab === 'incompletos' && incompletos.length === 0 && (
                <div className="text-center py-8 text-gray-500">
                  <CheckCircle2 className="w-12 h-12 mx-auto mb-2 text-green-300" />
                  <p>No hay registros incompletos</p>
                </div>
              )}
              
              {activeTab === 'excluidos' && excluidos.length === 0 && (
                <div className="text-center py-8 text-gray-500">
                  <Ban className="w-12 h-12 mx-auto mb-2 text-gray-300" />
                  <p>No hay registros excluidos</p>
                </div>
              )}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Modal de Detalle */}
      {showDetalleModal && selectedRegistro && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-lg w-full mx-4 max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-start mb-4">
              <h2 className="text-xl font-bold">Detalle del Registro</h2>
              <button onClick={() => setShowDetalleModal(false)}>
                <X className="w-5 h-5" />
              </button>
            </div>
            
            <div className="space-y-3">
              <div>
                <label className="text-xs text-gray-500">Nombre</label>
                <p className="font-medium">{selectedRegistro.Nombre_Completo}</p>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-xs text-gray-500">CURP</label>
                  <p className="font-mono text-sm">{selectedRegistro.CURP || '-'}</p>
                </div>
                <div>
                  <label className="text-xs text-gray-500">RFC</label>
                  <p className="font-mono text-sm">{selectedRegistro.RFC || '-'}</p>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-xs text-gray-500">Empresa</label>
                  <p className="text-sm">{selectedRegistro.Sucursal_Nombre}</p>
                </div>
                <div>
                  <label className="text-xs text-gray-500">No. Empleado</label>
                  <p className="text-sm">{selectedRegistro.Numero_Empleado_Externo || '-'}</p>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-xs text-gray-500">Puesto</label>
                  <p className="text-sm">{selectedRegistro.Puesto_Nombre || '-'}</p>
                </div>
                <div>
                  <label className="text-xs text-gray-500">Departamento</label>
                  <p className="text-sm">{selectedRegistro.Area_Departamento || '-'}</p>
                </div>
              </div>
              
              {/* Acciones */}
              <div className="border-t pt-4 mt-4 space-y-3">
                <Button 
                  className="w-full bg-green-600 hover:bg-green-700"
                  onClick={() => {
                    aprobarRegistro(selectedRegistro.StagingID);
                    setShowDetalleModal(false);
                  }}
                >
                  <Check className="w-4 h-4 mr-2" />
                  Aprobar
                </Button>
                
                <div>
                  <label className="text-xs text-gray-500 mb-1 block">Observar (requiere revisión)</label>
                  <div className="flex gap-2">
                    <Input
                      placeholder="Motivo de la observación..."
                      value={observacion}
                      onChange={(e) => setObservacion(e.target.value)}
                    />
                    <Button 
                      variant="outline"
                      onClick={() => observarRegistro(selectedRegistro.StagingID)}
                    >
                      <Eye className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
                
                <div>
                  <label className="text-xs text-gray-500 mb-1 block">Rechazar</label>
                  <div className="flex gap-2">
                    <Input
                      placeholder="Motivo del rechazo..."
                      value={motivoRechazo}
                      onChange={(e) => setMotivoRechazo(e.target.value)}
                    />
                    <Button 
                      variant="destructive"
                      onClick={() => rechazarRegistro(selectedRegistro.StagingID)}
                    >
                      <X className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
