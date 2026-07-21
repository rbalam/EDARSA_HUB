import logger from '../services/logger';
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

import { useState, useEffect, useCallback, useMemo } from 'react';
import api from '../lib/api';
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
import TabOperativasCompras from '@/components/TabOperativasCompras';
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
  Zap,
  ListChecks,
} from 'lucide-react';
import { getUser } from '@/lib/auth';
import { fetchUnidadesNegocio } from '@/services/unidadesNegocioService';
import { toast } from 'sonner';
import { useAuditoriasData } from '@/components/auditorias';

const READ_PERMISSIONS = ['AUDITORIA_VER', 'AUTOMATIZACIONES_VER'];
const PROGRAMAR_PERMISSIONS = ['AUDITORIAS_PROGRAMAR'];
const GESTIONAR_PERMISSIONS = ['AUDITORIAS_GESTIONAR'];

const normalizePermissionCode = (value) => String(value || '').trim().toUpperCase();

const getUnidadId = (unidad) => String(unidad?.id || unidad?.unidad_negocio_pk || '');

const getUnidadNombre = (unidad) => (
  unidad?.nombre
  || unidad?.unidad_negocio_nombre
  || unidad?.codigo
  || getUnidadId(unidad)
);

const buildInitialFormData = (unidadNegocioPk = '') => ({
  nombre: '',
  descripcion: '',
  unidad_negocio_pk: unidadNegocioPk,
  sucursal_id: '',
  sucursal_nombre: '',
  tipo_auditoria: 'INVENTARIO_COMPLETO',
  frecuencia: 'SEMANAL',
  dia_semana: 0,
  dia_mes: 1,
  hora_ejecucion: '08:00',
  observaciones: '',
});

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
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [unidadesNegocio, setUnidadesNegocio] = useState([]);
  const [selectedUnidad, setSelectedUnidad] = useState('all');
  const [loadingUnidades, setLoadingUnidades] = useState(true);
  const [permissionsLoading, setPermissionsLoading] = useState(true);
  const [functionalPermissions, setFunctionalPermissions] = useState([]);
  const [globalAccess, setGlobalAccess] = useState(false);

  const permissionSet = useMemo(
    () => new Set(functionalPermissions.map(normalizePermissionCode)),
    [functionalPermissions]
  );

  const hasAnyPermission = useCallback((codes) => {
    if (globalAccess) return true;
    return codes.some((code) => permissionSet.has(normalizePermissionCode(code)));
  }, [globalAccess, permissionSet]);

  const permisos = useMemo(() => ({
    ver: hasAnyPermission(READ_PERMISSIONS),
    programar: hasAnyPermission(PROGRAMAR_PERMISSIONS),
    gestionar: hasAnyPermission(GESTIONAR_PERMISSIONS),
  }), [hasAnyPermission]);

  const selectedUnidadFiltro = selectedUnidad === 'all' ? '' : selectedUnidad;
  const dataEnabled = !permissionsLoading && permisos.ver;

  // Hook para datos (extraído)
  const {
    loading,
    refreshing,
    auditorias,
    kpis,
    historial,
    calendario,
    historialDias,
    setHistorialDias,
    handleRefresh,
    loadAllData,
    cambiarMesCalendario
  } = useAuditoriasData(selectedUnidadFiltro, dataEnabled);
  
  // Filters
  const [filterStatus, setFilterStatus] = useState('all');
  const [searchText, setSearchText] = useState('');
  
  // Form
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [formData, setFormData] = useState(() => buildInitialFormData());
  const [formLoading, setFormLoading] = useState(false);
  
  // Confirm dialog
  const [confirmDialog, setConfirmDialog] = useState({ open: false, type: null, id: null, nombre: null });
  const [actionLoading, setActionLoading] = useState(false);

  useEffect(() => {
    let mounted = true;

    const loadPermissions = async () => {
      setPermissionsLoading(true);
      try {
        const response = await api.get('/auth/me/menu-permissions');
        if (!mounted) return;
        setFunctionalPermissions(response.data?.permisos_funcionales || []);
        setGlobalAccess(Boolean(response.data?.tiene_acceso_global));
      } catch (error) {
        logger.error('[Automatizaciones] Error cargando permisos:', error);
        if (mounted) {
          setFunctionalPermissions([]);
          setGlobalAccess(false);
        }
      } finally {
        if (mounted) setPermissionsLoading(false);
      }
    };

    loadPermissions();
    return () => { mounted = false; };
  }, []);

  useEffect(() => {
    let mounted = true;

    const loadUnidades = async () => {
      setLoadingUnidades(true);
      try {
        const unidades = await fetchUnidadesNegocio();
        if (!mounted) return;
        const disponibles = unidades || [];
        const ids = disponibles.map(getUnidadId).filter(Boolean);
        setUnidadesNegocio(disponibles);
        setSelectedUnidad((prev) => {
          if (ids.length === 1) return ids[0];
          if (prev && prev !== 'all' && !ids.includes(prev)) return 'all';
          return prev || 'all';
        });
      } catch (error) {
        logger.error('[Automatizaciones] Error cargando unidades:', error);
        if (mounted) setUnidadesNegocio([]);
      } finally {
        if (mounted) setLoadingUnidades(false);
      }
    };

    loadUnidades();
    return () => { mounted = false; };
  }, []);

  // Auto-refresh
  useEffect(() => {
    if (!autoRefresh) return;
    const interval = setInterval(() => loadAllData(), 60000);
    return () => clearInterval(interval);
  }, [autoRefresh, loadAllData]);

  const findUnidadById = useCallback((unidadId) => {
    const target = String(unidadId || '');
    return unidadesNegocio.find((unidad) => getUnidadId(unidad) === target);
  }, [unidadesNegocio]);

  const getDefaultUnidadPk = useCallback(() => {
    if (selectedUnidad !== 'all') return selectedUnidad;
    if (unidadesNegocio.length === 1) return getUnidadId(unidadesNegocio[0]);
    return '';
  }, [selectedUnidad, unidadesNegocio]);

  const findUnidadForAuditoria = useCallback((auditoria) => {
    const direct = auditoria?.unidad_negocio_pk;
    if (direct && findUnidadById(direct)) return String(direct);

    const serverId = String(auditoria?.server_id || '');
    const sucursalId = String(auditoria?.sucursal_id || '');
    const matched = unidadesNegocio.find((unidad) => (
      String(unidad.server_id || '') === serverId
      && [unidad.sucursal_origen_id, unidad.codigo, getUnidadId(unidad)]
        .some((value) => String(value || '') === sucursalId)
    ));

    return matched ? getUnidadId(matched) : (direct || getDefaultUnidadPk());
  }, [findUnidadById, getDefaultUnidadPk, unidadesNegocio]);

  const openNewForm = useCallback(() => {
    setEditingId(null);
    setFormData(buildInitialFormData(getDefaultUnidadPk()));
    setShowForm(true);
  }, [getDefaultUnidadPk]);

  // Actions
  const handleAction = async (action, id) => {
    setActionLoading(true);
    try {
      await api.post(`/v2/auditorias-programadas/${id}/${action}`);
      await handleRefresh();
    } catch (error) {
      alert(`Error: ${error.response?.data?.detail || 'Error de conexión'}`);
    } finally {
      setActionLoading(false);
      setConfirmDialog({ open: false, type: null, id: null, nombre: null });
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setFormLoading(true);
    
    try {
      const unidad = findUnidadById(formData.unidad_negocio_pk);
      if (!unidad) {
        toast.error('Selecciona una unidad de negocio válida');
        setFormLoading(false);
        return;
      }

      const unidadPk = getUnidadId(unidad);
      const payload = {
        ...formData,
        unidad_negocio_pk: unidadPk,
        server_id: unidad.server_id || '',
        sucursal_id: unidad.sucursal_origen_id || unidad.codigo || unidadPk,
        sucursal_nombre: getUnidadNombre(unidad),
        created_by: user?.email || 'unknown',
      };
      
      if (editingId) {
        await api.put(`/v2/auditorias-programadas/${editingId}`, payload);
      } else {
        await api.post('/v2/auditorias-programadas', payload);
      }
      
      setShowForm(false);
      setEditingId(null);
      setFormData(buildInitialFormData(getDefaultUnidadPk()));
      await handleRefresh();
    } catch (error) {
      toast.error(`Error: ${error.response?.data?.detail || 'Error de conexión'}`);
    } finally {
      setFormLoading(false);
    }
  };

  const handleEdit = (auditoria) => {
    setFormData({
      nombre: auditoria.nombre || '',
      descripcion: auditoria.descripcion || '',
      unidad_negocio_pk: findUnidadForAuditoria(auditoria),
      sucursal_id: auditoria.sucursal_id || '',
      sucursal_nombre: auditoria.sucursal_nombre || auditoria.unidad_negocio_nombre || '',
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
      const target = [
        a.nombre,
        a.sucursal_nombre,
        a.unidad_negocio_nombre,
        a.unidad_negocio_codigo,
      ].filter(Boolean).join(' ').toLowerCase();
      return target.includes(search);
    }
    return true;
  });

  if (permissionsLoading || loadingUnidades || (permisos.ver && loading)) {
    return (
      <div className="flex items-center justify-center h-96" data-testid="auditorias-loading">
        <Loader2 className="w-8 h-8 animate-spin text-zinc-400" />
        <span className="ml-2 text-zinc-500">Cargando módulo...</span>
      </div>
    );
  }

  if (!permisos.ver) {
    return (
      <div className="flex items-center justify-center h-96" data-testid="auditorias-denied">
        <div className="text-center text-zinc-500">
          <AlertCircle className="w-8 h-8 mx-auto mb-2 text-amber-500" />
          <p>Sin permiso para ver Automatizaciones</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="automatizaciones-page">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-zinc-900">Automatizaciones</h1>
          <p className="text-zinc-500 text-sm mt-1">Gestión de procesos automáticos del sistema</p>
        </div>
        
        <div className="flex flex-wrap items-center gap-3">
          <Select value={selectedUnidad} onValueChange={setSelectedUnidad} disabled={loadingUnidades || unidadesNegocio.length === 0}>
            <SelectTrigger className="w-[220px]">
              <SelectValue placeholder="Unidad de negocio" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Todas las unidades</SelectItem>
              {unidadesNegocio.map((unidad) => {
                const unidadId = getUnidadId(unidad);
                return unidadId ? (
                  <SelectItem key={unidadId} value={unidadId}>{getUnidadNombre(unidad)}</SelectItem>
                ) : null;
              })}
            </SelectContent>
          </Select>

          <div className="flex items-center gap-2 text-sm">
            <Switch id="auto-refresh" checked={autoRefresh} onCheckedChange={setAutoRefresh} />
            <Label htmlFor="auto-refresh" className="text-zinc-600">Auto-refresh</Label>
          </div>
          
          <Button variant="outline" size="sm" onClick={() => handleRefresh()} disabled={refreshing}>
            <RefreshCw className={`w-4 h-4 mr-1 ${refreshing ? 'animate-spin' : ''}`} />
            Actualizar
          </Button>
        </div>
      </div>

      {/* Tabs Nivel Superior */}
      <Tabs defaultValue="programadas" className="space-y-4">
        <TabsList className="grid w-full grid-cols-3 lg:w-auto lg:inline-flex">
          <TabsTrigger value="programadas" className="flex items-center gap-2">
            <Clock className="w-4 h-4" />
            Programadas
          </TabsTrigger>
          <TabsTrigger value="operativas" className="flex items-center gap-2">
            <Zap className="w-4 h-4" />
            Operativas
          </TabsTrigger>
          <TabsTrigger value="historial-global" className="flex items-center gap-2">
            <ListChecks className="w-4 h-4" />
            Historial
          </TabsTrigger>
        </TabsList>

        {/* ========== TAB: PROGRAMADAS ========== */}
        <TabsContent value="programadas" className="space-y-4">
          {/* Botón Nueva Programación */}
          <div className="flex justify-end">
            {permisos.programar && (
              <Button size="sm" onClick={openNewForm} disabled={loadingUnidades || unidadesNegocio.length === 0} data-testid="new-auditoria-btn">
                <Plus className="w-4 h-4 mr-1" />
                Nueva Programación
              </Button>
            )}
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
                <CardTitle className="text-lg">Automatizaciones Programadas</CardTitle>
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
                            {auditoria.unidad_negocio_nombre || auditoria.sucursal_nombre || auditoria.unidad_negocio_pk || '-'}
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
                      <Button variant="link" onClick={openNewForm} disabled={loadingUnidades || unidadesNegocio.length === 0}>
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
                    onClick={() => cambiarMesCalendario(-1)}
                  >
                    Anterior
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => cambiarMesCalendario(1)}
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
                          <div key={a.id || `aud-${evento.fecha}-${idx}`} className="flex items-center gap-2 text-sm text-zinc-600">
                            <Clock className="w-4 h-4 text-blue-500" />
                            <span>{a.hora_ejecucion}</span>
                            <span className="font-medium">{a.nombre}</span>
                            <Badge variant="outline" className="text-xs">{a.unidad_negocio_nombre || a.sucursal_nombre}</Badge>
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
        </TabsContent>

        {/* ========== TAB: OPERATIVAS ========== */}
        <TabsContent value="operativas" className="space-y-4">
          <TabOperativasCompras />
        </TabsContent>

        {/* ========== TAB: HISTORIAL GLOBAL ========== */}
        <TabsContent value="historial-global" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-2">
                <ListChecks className="w-5 h-5 text-blue-500" />
                Historial de Automatizaciones
              </CardTitle>
              <CardDescription>
                Registro unificado de todas las ejecuciones automáticas del sistema
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Fecha</TableHead>
                    <TableHead>Tipo</TableHead>
                    <TableHead>Origen</TableHead>
                    <TableHead>Estado</TableHead>
                    <TableHead>Resultado</TableHead>
                    <TableHead>Usuario</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {historial.map((log) => (
                    <TableRow key={log.id}>
                      <TableCell className="text-sm">{formatDateTime(log.fecha_ejecucion)}</TableCell>
                      <TableCell>
                        <Badge variant="outline" className="text-xs">
                          <Clock className="w-3 h-3 mr-1" />
                          Programada
                        </Badge>
                      </TableCell>
                      <TableCell className="font-mono text-xs">{log.auditoria_programada_id?.substring(0, 8)}...</TableCell>
                      <TableCell><ExecutionBadge estado={log.estado} /></TableCell>
                      <TableCell className="max-w-xs truncate text-sm text-zinc-500">{log.mensaje || '-'}</TableCell>
                      <TableCell className="text-sm">{log.disparado_por === 'SCHEDULER' ? 'Sistema' : log.disparado_por}</TableCell>
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
              <div className="col-span-2">
                <Label>Unidad de negocio</Label>
                <Select
                  value={formData.unidad_negocio_pk || ''}
                  onValueChange={(v) => setFormData({ ...formData, unidad_negocio_pk: v })}
                  disabled={loadingUnidades || unidadesNegocio.length === 0}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Selecciona unidad" />
                  </SelectTrigger>
                  <SelectContent>
                    {unidadesNegocio.map((unidad) => {
                      const unidadId = getUnidadId(unidad);
                      return unidadId ? (
                        <SelectItem key={unidadId} value={unidadId}>{getUnidadNombre(unidad)}</SelectItem>
                      ) : null;
                    })}
                  </SelectContent>
                </Select>
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
                        <SelectItem key={`dia-${dia}`} value={String(idx)}>{dia}</SelectItem>
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
              <Button type="submit" disabled={formLoading || !formData.unidad_negocio_pk}>
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
