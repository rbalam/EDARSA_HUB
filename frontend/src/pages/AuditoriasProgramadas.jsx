/**
 * EDARSA HUB - Módulo de Auditorías Programadas
 * 
 * Features:
 * - KPIs: Total, activas, inactivas, pendientes hoy, completadas/fallidas mes
 * - Calendario visual de auditorías programadas
 * - Lista con estado activo/inactivo
 * - Historial de ejecuciones
 * - Formulario crear/editar
 * - Acciones: Ejecutar, Activar, Desactivar (con confirmación)
 * - RBAC integrado
 * - Auto-refresh
 */

import { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Switch } from '@/components/ui/switch';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Calendar,
  ClipboardList,
  Play,
  Pause,
  RefreshCw,
  CheckCircle2,
  XCircle,
  AlertCircle,
  Clock,
  Activity,
  Plus,
  Search,
  TrendingUp,
  Loader2,
  Building2,
  CalendarDays,
  History,
  Settings,
  Power,
  PowerOff,
} from 'lucide-react';
import { getUser, getToken } from '@/lib/auth';

const API_URL = process.env.REACT_APP_BACKEND_URL;

const formatDateTime = (isoString) => {
  if (!isoString) return '-';
  const date = new Date(isoString);
  return date.toLocaleString('es-MX', {
    day: '2-digit', month: '2-digit', year: 'numeric',
    hour: '2-digit', minute: '2-digit',
  });
};

const formatDate = (isoString) => {
  if (!isoString) return '-';
  const date = new Date(isoString);
  return date.toLocaleDateString('es-MX', {
    day: '2-digit', month: 'short', year: 'numeric',
  });
};

const FRECUENCIAS = {
  DIARIA: 'Diaria',
  SEMANAL: 'Semanal',
  QUINCENAL: 'Quincenal',
  MENSUAL: 'Mensual',
  MANUAL: 'Manual',
};

const TIPOS_AUDITORIA = {
  INVENTARIO_COMPLETO: 'Inventario Completo',
  INVENTARIO_SELECTIVO: 'Inventario Selectivo',
  CONTEO_CICLICO: 'Conteo Cíclico',
  AUDITORIA_SORPRESA: 'Auditoría Sorpresa',
};

const DIAS_SEMANA = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo'];

const StatusBadge = ({ activo, ultimoStatus }) => {
  if (!activo) {
    return (
      <Badge variant="outline" className="bg-zinc-100 text-zinc-600">
        <PowerOff className="w-3 h-3 mr-1" />
        Inactiva
      </Badge>
    );
  }
  if (ultimoStatus === 'FALLIDA') {
    return (
      <Badge variant="outline" className="bg-red-50 text-red-700 border-red-200">
        <XCircle className="w-3 h-3 mr-1" />
        Error
      </Badge>
    );
  }
  return (
    <Badge variant="outline" className="bg-emerald-50 text-emerald-700 border-emerald-200">
      <Power className="w-3 h-3 mr-1" />
      Activa
    </Badge>
  );
};

const ExecutionBadge = ({ estado }) => {
  const badges = {
    COMPLETADA: { class: 'bg-emerald-100 text-emerald-800', icon: CheckCircle2, text: 'Completada' },
    FALLIDA: { class: 'bg-red-100 text-red-800', icon: XCircle, text: 'Fallida' },
    EN_PROGRESO: { class: 'bg-blue-100 text-blue-800', icon: Loader2, text: 'En Progreso' },
    OMITIDA: { class: 'bg-amber-100 text-amber-800', icon: AlertCircle, text: 'Omitida' },
    PENDIENTE: { class: 'bg-zinc-100 text-zinc-800', icon: Clock, text: 'Pendiente' },
  };
  const badge = badges[estado] || badges.PENDIENTE;
  const Icon = badge.icon;
  return (
    <Badge className={`${badge.class} hover:${badge.class}`}>
      <Icon className={`w-3 h-3 mr-1 ${estado === 'EN_PROGRESO' ? 'animate-spin' : ''}`} />
      {badge.text}
    </Badge>
  );
};

export default function AuditoriasProgramadas() {
  const user = getUser();
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [autoRefresh, setAutoRefresh] = useState(true);
  
  const [auditorias, setAuditorias] = useState([]);
  const [kpis, setKpis] = useState(null);
  const [historial, setHistorial] = useState([]);
  const [calendario, setCalendario] = useState({ eventos: [], mes: new Date().getMonth() + 1, anio: new Date().getFullYear() });
  
  // Filters
  const [filterStatus, setFilterStatus] = useState('all');
  const [searchText, setSearchText] = useState('');
  const [historialDias, setHistorialDias] = useState('30');
  
  // Form
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [formData, setFormData] = useState({
    nombre: '',
    descripcion: '',
    sucursal_id: '',
    sucursal_nombre: '',
    tipo_auditoria: 'INVENTARIO_COMPLETO',
    frecuencia: 'SEMANAL',
    dia_semana: 0,
    dia_mes: 1,
    hora_ejecucion: '08:00',
    observaciones: '',
  });
  const [formLoading, setFormLoading] = useState(false);
  
  // Confirm dialog
  const [confirmDialog, setConfirmDialog] = useState({ open: false, type: null, id: null, nombre: null });
  const [actionLoading, setActionLoading] = useState(false);
  
  // Permissions
  const permisos = {
    ver: ['Administrador', 'Supervisor', 'Gerente', 'Director', 'Auditor'].includes(user?.role),
    programar: ['Administrador', 'Gerente', 'Director'].includes(user?.role),
    gestionar: ['Administrador', 'Director'].includes(user?.role),
  };

  const fetchAuditorias = useCallback(async () => {
    try {
      const response = await fetch(`${API_URL}/api/v2/auditorias-programadas`, {
        headers: { Authorization: `Bearer ${getToken()}` },
      });
      if (response.ok) {
        const data = await response.json();
        setAuditorias(data.items || []);
      }
    } catch (error) {
      console.error('Error fetching auditorias:', error);
    }
  }, []);

  const fetchKpis = useCallback(async () => {
    try {
      const response = await fetch(`${API_URL}/api/v2/auditorias-programadas/kpis`, {
        headers: { Authorization: `Bearer ${getToken()}` },
      });
      if (response.ok) {
        setKpis(await response.json());
      }
    } catch (error) {
      console.error('Error fetching KPIs:', error);
    }
  }, []);

  const fetchHistorial = useCallback(async () => {
    try {
      const response = await fetch(`${API_URL}/api/v2/auditorias-programadas/historial?dias=${historialDias}&limit=100`, {
        headers: { Authorization: `Bearer ${getToken()}` },
      });
      if (response.ok) {
        const data = await response.json();
        setHistorial(data.items || []);
      }
    } catch (error) {
      console.error('Error fetching historial:', error);
    }
  }, [historialDias]);

  const fetchCalendario = useCallback(async () => {
    try {
      const response = await fetch(
        `${API_URL}/api/v2/auditorias-programadas/calendario?anio=${calendario.anio}&mes=${calendario.mes}`,
        { headers: { Authorization: `Bearer ${getToken()}` } }
      );
      if (response.ok) {
        const data = await response.json();
        setCalendario(prev => ({ ...prev, eventos: data.eventos || [] }));
      }
    } catch (error) {
      console.error('Error fetching calendario:', error);
    }
  }, [calendario.anio, calendario.mes]);

  const fetchAll = useCallback(async (showRefreshing = false) => {
    if (showRefreshing) setRefreshing(true);
    await Promise.all([fetchAuditorias(), fetchKpis(), fetchHistorial(), fetchCalendario()]);
    setLoading(false);
    if (showRefreshing) setRefreshing(false);
  }, [fetchAuditorias, fetchKpis, fetchHistorial, fetchCalendario]);

  useEffect(() => { fetchAll(); }, [fetchAll]);

  useEffect(() => {
    if (!autoRefresh) return;
    const interval = setInterval(() => fetchAll(false), 60000);
    return () => clearInterval(interval);
  }, [autoRefresh, fetchAll]);

  // Actions
  const handleAction = async (action, id) => {
    setActionLoading(true);
    try {
      const response = await fetch(`${API_URL}/api/v2/auditorias-programadas/${id}/${action}`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${getToken()}` },
      });
      if (response.ok) {
        await fetchAll(true);
      } else {
        const error = await response.json();
        alert(`Error: ${error.detail || 'No se pudo ejecutar la acción'}`);
      }
    } catch (error) {
      alert('Error de conexión');
    } finally {
      setActionLoading(false);
      setConfirmDialog({ open: false, type: null, id: null, nombre: null });
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setFormLoading(true);
    
    try {
      const payload = {
        ...formData,
        created_by: user?.email || 'unknown',
      };
      
      const url = editingId 
        ? `${API_URL}/api/v2/auditorias-programadas/${editingId}`
        : `${API_URL}/api/v2/auditorias-programadas`;
      
      const response = await fetch(url, {
        method: editingId ? 'PUT' : 'POST',
        headers: {
          Authorization: `Bearer ${getToken()}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      });
      
      if (response.ok) {
        setShowForm(false);
        setEditingId(null);
        setFormData({
          nombre: '', descripcion: '', sucursal_id: '', sucursal_nombre: '',
          tipo_auditoria: 'INVENTARIO_COMPLETO', frecuencia: 'SEMANAL',
          dia_semana: 0, dia_mes: 1, hora_ejecucion: '08:00', observaciones: '',
        });
        await fetchAll(true);
      } else {
        const error = await response.json();
        alert(`Error: ${error.detail || 'No se pudo guardar'}`);
      }
    } catch (error) {
      alert('Error de conexión');
    } finally {
      setFormLoading(false);
    }
  };

  const handleEdit = (auditoria) => {
    setFormData({
      nombre: auditoria.nombre || '',
      descripcion: auditoria.descripcion || '',
      sucursal_id: auditoria.sucursal_id || '',
      sucursal_nombre: auditoria.sucursal_nombre || '',
      tipo_auditoria: auditoria.tipo_auditoria || 'INVENTARIO_COMPLETO',
      frecuencia: auditoria.frecuencia || 'SEMANAL',
      dia_semana: auditoria.dia_semana || 0,
      dia_mes: auditoria.dia_mes || 1,
      hora_ejecucion: auditoria.hora_ejecucion || '08:00',
      observaciones: auditoria.observaciones || '',
    });
    setEditingId(auditoria.id);
    setShowForm(true);
  };

  // Filtered auditorias
  const filteredAuditorias = auditorias.filter(a => {
    if (filterStatus === 'activas' && !a.activo) return false;
    if (filterStatus === 'inactivas' && a.activo) return false;
    if (searchText) {
      const search = searchText.toLowerCase();
      return a.nombre?.toLowerCase().includes(search) || a.sucursal_nombre?.toLowerCase().includes(search);
    }
    return true;
  });

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96" data-testid="auditorias-loading">
        <Loader2 className="w-8 h-8 animate-spin text-zinc-400" />
        <span className="ml-2 text-zinc-500">Cargando módulo...</span>
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="auditorias-page">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-zinc-900">Auditorías Programadas</h1>
          <p className="text-zinc-500 text-sm mt-1">Gestión de auditorías de inventario automatizadas</p>
        </div>
        
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 text-sm">
            <Switch id="auto-refresh" checked={autoRefresh} onCheckedChange={setAutoRefresh} />
            <Label htmlFor="auto-refresh" className="text-zinc-600">Auto-refresh</Label>
          </div>
          
          <Button variant="outline" size="sm" onClick={() => fetchAll(true)} disabled={refreshing}>
            <RefreshCw className={`w-4 h-4 mr-1 ${refreshing ? 'animate-spin' : ''}`} />
            Actualizar
          </Button>
          
          {permisos.programar && (
            <Button size="sm" onClick={() => { setEditingId(null); setShowForm(true); }} data-testid="new-auditoria-btn">
              <Plus className="w-4 h-4 mr-1" />
              Nueva Programación
            </Button>
          )}
        </div>
      </div>

      {/* KPIs */}
      {kpis && (
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-8 gap-3" data-testid="auditorias-kpis">
          <Card>
            <CardContent className="p-3">
              <div className="flex items-center gap-2">
                <ClipboardList className="w-4 h-4 text-blue-600" />
                <span className="text-xs text-zinc-500">Total</span>
              </div>
              <p className="text-lg font-bold">{kpis.total_programadas}</p>
            </CardContent>
          </Card>
          <Card className="bg-emerald-50 border-emerald-200">
            <CardContent className="p-3">
              <div className="flex items-center gap-2">
                <Power className="w-4 h-4 text-emerald-600" />
                <span className="text-xs text-zinc-500">Activas</span>
              </div>
              <p className="text-lg font-bold text-emerald-700">{kpis.activas}</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-3">
              <div className="flex items-center gap-2">
                <PowerOff className="w-4 h-4 text-zinc-400" />
                <span className="text-xs text-zinc-500">Inactivas</span>
              </div>
              <p className="text-lg font-bold">{kpis.inactivas}</p>
            </CardContent>
          </Card>
          <Card className={kpis.pendientes_hoy > 0 ? 'bg-amber-50 border-amber-200' : ''}>
            <CardContent className="p-3">
              <div className="flex items-center gap-2">
                <Clock className="w-4 h-4 text-amber-600" />
                <span className="text-xs text-zinc-500">Hoy</span>
              </div>
              <p className="text-lg font-bold">{kpis.pendientes_hoy}</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-3">
              <div className="flex items-center gap-2">
                <Activity className="w-4 h-4 text-blue-500" />
                <span className="text-xs text-zinc-500">En Curso</span>
              </div>
              <p className="text-lg font-bold">{kpis.en_curso}</p>
            </CardContent>
          </Card>
          <Card className="bg-emerald-50 border-emerald-200">
            <CardContent className="p-3">
              <div className="flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                <span className="text-xs text-zinc-500">Mes</span>
              </div>
              <p className="text-lg font-bold text-emerald-700">{kpis.completadas_mes}</p>
            </CardContent>
          </Card>
          <Card className={kpis.fallidas_mes > 0 ? 'bg-red-50 border-red-200' : ''}>
            <CardContent className="p-3">
              <div className="flex items-center gap-2">
                <XCircle className="w-4 h-4 text-red-500" />
                <span className="text-xs text-zinc-500">Fallidas</span>
              </div>
              <p className={`text-lg font-bold ${kpis.fallidas_mes > 0 ? 'text-red-700' : ''}`}>{kpis.fallidas_mes}</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-3">
              <div className="flex items-center gap-2">
                <TrendingUp className="w-4 h-4 text-violet-600" />
                <span className="text-xs text-zinc-500">Cumplimiento</span>
              </div>
              <p className="text-lg font-bold">{kpis.tasa_cumplimiento}%</p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Tabs */}
      <Tabs defaultValue="lista" className="space-y-4">
        <TabsList>
          <TabsTrigger value="lista" className="flex items-center gap-1">
            <ClipboardList className="w-4 h-4" />
            Programaciones
          </TabsTrigger>
          <TabsTrigger value="calendario" className="flex items-center gap-1">
            <CalendarDays className="w-4 h-4" />
            Calendario
          </TabsTrigger>
          <TabsTrigger value="historial" className="flex items-center gap-1">
            <History className="w-4 h-4" />
            Historial
          </TabsTrigger>
        </TabsList>

        {/* Lista */}
        <TabsContent value="lista">
          <Card>
            <CardHeader className="pb-3">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <CardTitle className="text-lg">Auditorías Programadas</CardTitle>
                <div className="flex items-center gap-2">
                  <Select value={filterStatus} onValueChange={setFilterStatus}>
                    <SelectTrigger className="w-[140px]">
                      <SelectValue placeholder="Estado" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">Todas</SelectItem>
                      <SelectItem value="activas">Activas</SelectItem>
                      <SelectItem value="inactivas">Inactivas</SelectItem>
                    </SelectContent>
                  </Select>
                  <div className="relative">
                    <Search className="absolute left-2.5 top-1/2 transform -translate-y-1/2 w-4 h-4 text-zinc-400" />
                    <Input
                      placeholder="Buscar..."
                      value={searchText}
                      onChange={(e) => setSearchText(e.target.value)}
                      className="pl-8 w-[180px]"
                    />
                  </div>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {filteredAuditorias.map((auditoria) => (
                  <div key={auditoria.id} className="border rounded-lg p-4 bg-white hover:bg-zinc-50 transition-colors" data-testid={`auditoria-card-${auditoria.id}`}>
                    <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-3">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 flex-wrap">
                          <h3 className="font-semibold text-zinc-900">{auditoria.nombre}</h3>
                          <StatusBadge activo={auditoria.activo} ultimoStatus={auditoria.ultima_ejecucion_status} />
                          <Badge variant="outline">{TIPOS_AUDITORIA[auditoria.tipo_auditoria] || auditoria.tipo_auditoria}</Badge>
                        </div>
                        
                        <div className="flex flex-wrap items-center gap-4 mt-2 text-sm text-zinc-600">
                          <span className="flex items-center gap-1">
                            <Building2 className="w-4 h-4 text-zinc-400" />
                            {auditoria.sucursal_nombre}
                          </span>
                          <span className="flex items-center gap-1">
                            <Calendar className="w-4 h-4 text-zinc-400" />
                            {FRECUENCIAS[auditoria.frecuencia]} • {auditoria.hora_ejecucion}
                          </span>
                          {auditoria.proxima_ejecucion && (
                            <span className="flex items-center gap-1 text-blue-600">
                              <Clock className="w-4 h-4" />
                              Próxima: {formatDateTime(auditoria.proxima_ejecucion)}
                            </span>
                          )}
                          {auditoria.ultima_ejecucion && (
                            <span className="flex items-center gap-1">
                              <History className="w-4 h-4 text-zinc-400" />
                              Última: {formatDateTime(auditoria.ultima_ejecucion)}
                            </span>
                          )}
                        </div>
                      </div>
                      
                      <div className="flex items-center gap-2">
                        {permisos.gestionar && (
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => setConfirmDialog({ open: true, type: 'ejecutar', id: auditoria.id, nombre: auditoria.nombre })}
                            disabled={!auditoria.activo}
                            title="Ejecutar ahora"
                          >
                            <Play className="w-4 h-4" />
                          </Button>
                        )}
                        
                        {permisos.programar && (
                          <>
                            {auditoria.activo ? (
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={() => setConfirmDialog({ open: true, type: 'desactivar', id: auditoria.id, nombre: auditoria.nombre })}
                                title="Desactivar"
                              >
                                <Pause className="w-4 h-4 text-amber-600" />
                              </Button>
                            ) : (
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={() => setConfirmDialog({ open: true, type: 'activar', id: auditoria.id, nombre: auditoria.nombre })}
                                title="Activar"
                              >
                                <Power className="w-4 h-4 text-emerald-600" />
                              </Button>
                            )}
                            <Button variant="outline" size="sm" onClick={() => handleEdit(auditoria)} title="Editar">
                              <Settings className="w-4 h-4" />
                            </Button>
                          </>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
                
                {filteredAuditorias.length === 0 && (
                  <div className="text-center py-12 text-zinc-500">
                    <ClipboardList className="w-12 h-12 mx-auto mb-3 text-zinc-300" />
                    <p>No hay auditorías programadas</p>
                    {permisos.programar && (
                      <Button variant="link" onClick={() => setShowForm(true)}>
                        Crear primera programación
                      </Button>
                    )}
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Calendario */}
        <TabsContent value="calendario">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle>Calendario de Auditorías - {calendario.mes}/{calendario.anio}</CardTitle>
                <div className="flex items-center gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => {
                      const newDate = new Date(calendario.anio, calendario.mes - 2, 1);
                      setCalendario(prev => ({ ...prev, mes: newDate.getMonth() + 1, anio: newDate.getFullYear() }));
                    }}
                  >
                    Anterior
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => {
                      const newDate = new Date(calendario.anio, calendario.mes, 1);
                      setCalendario(prev => ({ ...prev, mes: newDate.getMonth() + 1, anio: newDate.getFullYear() }));
                    }}
                  >
                    Siguiente
                  </Button>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              {calendario.eventos.length > 0 ? (
                <div className="space-y-3">
                  {calendario.eventos.map((evento) => (
                    <div key={evento.fecha} className="border rounded-lg p-3">
                      <h4 className="font-medium text-zinc-900 mb-2">{formatDate(evento.fecha)}</h4>
                      <div className="space-y-2">
                        {evento.auditorias.map((a, idx) => (
                          <div key={idx} className="flex items-center gap-2 text-sm text-zinc-600">
                            <Clock className="w-4 h-4 text-blue-500" />
                            <span>{a.hora_ejecucion}</span>
                            <span className="font-medium">{a.nombre}</span>
                            <Badge variant="outline" className="text-xs">{a.sucursal_nombre}</Badge>
                          </div>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-12 text-zinc-500">
                  <CalendarDays className="w-12 h-12 mx-auto mb-3 text-zinc-300" />
                  <p>No hay auditorías programadas para este mes</p>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Historial */}
        <TabsContent value="historial">
          <Card>
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <CardTitle>Historial de Ejecuciones</CardTitle>
                <Select value={historialDias} onValueChange={(v) => { setHistorialDias(v); }}>
                  <SelectTrigger className="w-[150px]">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="7">Últimos 7 días</SelectItem>
                    <SelectItem value="30">Últimos 30 días</SelectItem>
                    <SelectItem value="90">Últimos 90 días</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Auditoría</TableHead>
                    <TableHead>Estado</TableHead>
                    <TableHead>Disparado por</TableHead>
                    <TableHead>Workflow</TableHead>
                    <TableHead>Fecha</TableHead>
                    <TableHead>Mensaje</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {historial.map((log) => (
                    <TableRow key={log.id}>
                      <TableCell className="font-medium">{log.auditoria_programada_id?.substring(0, 8)}...</TableCell>
                      <TableCell><ExecutionBadge estado={log.estado} /></TableCell>
                      <TableCell>{log.disparado_por === 'SCHEDULER' ? 'Automático' : log.disparado_por}</TableCell>
                      <TableCell className="font-mono text-xs">{log.workflow_id?.substring(0, 8) || '-'}</TableCell>
                      <TableCell className="text-sm">{formatDateTime(log.fecha_ejecucion)}</TableCell>
                      <TableCell className="max-w-xs truncate text-sm text-zinc-500">{log.mensaje || log.error_detalle || '-'}</TableCell>
                    </TableRow>
                  ))}
                  {historial.length === 0 && (
                    <TableRow>
                      <TableCell colSpan={6} className="text-center py-8 text-zinc-500">
                        No hay registros de ejecución
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Form Dialog */}
      <Dialog open={showForm} onOpenChange={setShowForm}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>{editingId ? 'Editar' : 'Nueva'} Auditoría Programada</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="col-span-2">
                <Label>Nombre</Label>
                <Input
                  value={formData.nombre}
                  onChange={(e) => setFormData({ ...formData, nombre: e.target.value })}
                  required
                  minLength={3}
                />
              </div>
              <div>
                <Label>Sucursal ID</Label>
                <Input
                  value={formData.sucursal_id}
                  onChange={(e) => setFormData({ ...formData, sucursal_id: e.target.value })}
                  required
                />
              </div>
              <div>
                <Label>Nombre Sucursal</Label>
                <Input
                  value={formData.sucursal_nombre}
                  onChange={(e) => setFormData({ ...formData, sucursal_nombre: e.target.value })}
                  required
                />
              </div>
              <div>
                <Label>Tipo de Auditoría</Label>
                <Select value={formData.tipo_auditoria} onValueChange={(v) => setFormData({ ...formData, tipo_auditoria: v })}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    {Object.entries(TIPOS_AUDITORIA).map(([k, v]) => (
                      <SelectItem key={k} value={k}>{v}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label>Frecuencia</Label>
                <Select value={formData.frecuencia} onValueChange={(v) => setFormData({ ...formData, frecuencia: v })}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    {Object.entries(FRECUENCIAS).map(([k, v]) => (
                      <SelectItem key={k} value={k}>{v}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              {formData.frecuencia === 'SEMANAL' && (
                <div>
                  <Label>Día de la Semana</Label>
                  <Select value={String(formData.dia_semana)} onValueChange={(v) => setFormData({ ...formData, dia_semana: parseInt(v) })}>
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>
                      {DIAS_SEMANA.map((dia, idx) => (
                        <SelectItem key={idx} value={String(idx)}>{dia}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              )}
              {formData.frecuencia === 'MENSUAL' && (
                <div>
                  <Label>Día del Mes</Label>
                  <Input
                    type="number"
                    min={1}
                    max={31}
                    value={formData.dia_mes}
                    onChange={(e) => setFormData({ ...formData, dia_mes: parseInt(e.target.value) })}
                  />
                </div>
              )}
              <div>
                <Label>Hora de Ejecución</Label>
                <Input
                  type="time"
                  value={formData.hora_ejecucion}
                  onChange={(e) => setFormData({ ...formData, hora_ejecucion: e.target.value })}
                  required
                />
              </div>
              <div className="col-span-2">
                <Label>Observaciones</Label>
                <Input
                  value={formData.observaciones}
                  onChange={(e) => setFormData({ ...formData, observaciones: e.target.value })}
                />
              </div>
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setShowForm(false)}>Cancelar</Button>
              <Button type="submit" disabled={formLoading}>
                {formLoading ? <Loader2 className="w-4 h-4 mr-1 animate-spin" /> : null}
                {editingId ? 'Guardar Cambios' : 'Crear Programación'}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Confirm Dialog */}
      <Dialog open={confirmDialog.open} onOpenChange={(open) => !actionLoading && setConfirmDialog({ ...confirmDialog, open })}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>
              {confirmDialog.type === 'ejecutar' && 'Ejecutar Auditoría'}
              {confirmDialog.type === 'activar' && 'Activar Auditoría'}
              {confirmDialog.type === 'desactivar' && 'Desactivar Auditoría'}
            </DialogTitle>
            <DialogDescription>
              {confirmDialog.type === 'ejecutar' && `¿Ejecutar "${confirmDialog.nombre}" manualmente? Se creará un workflow de inventario.`}
              {confirmDialog.type === 'activar' && `¿Activar "${confirmDialog.nombre}"? Se calculará la próxima ejecución.`}
              {confirmDialog.type === 'desactivar' && `¿Desactivar "${confirmDialog.nombre}"? No se ejecutará hasta que se reactive.`}
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setConfirmDialog({ open: false, type: null, id: null, nombre: null })} disabled={actionLoading}>
              Cancelar
            </Button>
            <Button
              onClick={() => handleAction(confirmDialog.type, confirmDialog.id)}
              disabled={actionLoading}
              className={
                confirmDialog.type === 'desactivar' ? 'bg-amber-600 hover:bg-amber-700' :
                confirmDialog.type === 'ejecutar' ? 'bg-blue-600 hover:bg-blue-700' :
                'bg-emerald-600 hover:bg-emerald-700'
              }
            >
              {actionLoading ? <Loader2 className="w-4 h-4 mr-1 animate-spin" /> : null}
              Confirmar
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
