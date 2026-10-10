import { useCallback, useEffect, useMemo, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import api from '@/lib/api';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Checkbox } from '@/components/ui/checkbox';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import {
  Activity,
  AlertTriangle,
  ArrowLeft,
  CalendarRange,
  CheckCircle2,
  ChevronRight,
  CircleStop,
  Clock3,
  Database,
  History,
  Layers3,
  Loader2,
  Pause,
  Play,
  RefreshCw,
  RotateCcw,
  Server,
  ShieldCheck,
  TableProperties,
  XCircle,
  Zap,
} from 'lucide-react';

const ACTIVE_STATUSES = new Set([
  'QUEUED',
  'RUNNING',
  'WAITING_RETRY',
  'FAILED_RETRYABLE',
  'PAUSE_REQUESTED',
  'CANCEL_REQUESTED',
]);

const TERMINAL_OK = new Set(['SUCCESS', 'CANCELLED_SAFE']);
const TERMINAL_ERROR = new Set(['PARTIAL_FAILED', 'PERMANENT_FAILURE', 'ENQUEUE_FAILED']);

const formatDateTime = (value) => {
  if (!value) return '-';
  try {
    return new Date(value).toLocaleString('es-MX');
  } catch {
    return '-';
  }
};

const statusTone = (status) => {
  if (TERMINAL_OK.has(status)) return 'bg-emerald-100 text-emerald-800 border-emerald-200';
  if (TERMINAL_ERROR.has(status)) return 'bg-red-100 text-red-800 border-red-200';
  if (status === 'PAUSED' || status === 'PAUSE_REQUESTED') return 'bg-amber-100 text-amber-800 border-amber-200';
  if (ACTIVE_STATUSES.has(status)) return 'bg-blue-100 text-blue-800 border-blue-200';
  return 'bg-zinc-100 text-zinc-700 border-zinc-200';
};

const CheckList = ({ title, items, selected, getKey, getLabel, getMeta, onToggle, onToggleAll }) => {
  const all = items.length > 0 && items.every((item) => selected.includes(getKey(item)));
  const some = items.some((item) => selected.includes(getKey(item)));

  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between gap-3">
          <CardTitle className="text-base">{title}</CardTitle>
          <button
            type="button"
            onClick={() => onToggleAll(!all)}
            className="text-xs font-medium text-blue-600 hover:underline disabled:text-zinc-400"
            disabled={items.length === 0}
          >
            {all ? 'Quitar todo' : some ? 'Completar selección' : 'Seleccionar todo'}
          </button>
        </div>
      </CardHeader>
      <CardContent>
        <div className="max-h-64 space-y-2 overflow-y-auto pr-1">
          {items.length === 0 && <p className="text-sm text-zinc-500">Sin opciones compatibles.</p>}
          {items.map((item) => {
            const key = getKey(item);
            const checked = selected.includes(key);
            return (
              <label
                key={key}
                className="flex cursor-pointer items-start gap-3 rounded-md border border-zinc-200 p-3 hover:bg-zinc-50"
              >
                <Checkbox checked={checked} onCheckedChange={() => onToggle(key)} />
                <span className="min-w-0 flex-1">
                  <span className="block text-sm font-medium text-zinc-900">{getLabel(item)}</span>
                  {getMeta && <span className="block text-xs text-zinc-500">{getMeta(item)}</span>}
                </span>
              </label>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
};

export default function SyncHistorical() {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const jobFromUrl = Number(searchParams.get('job') || 0);

  const [catalog, setCatalog] = useState(null);
  const [history, setHistory] = useState([]);
  const [catalogLoading, setCatalogLoading] = useState(true);
  const [historyLoading, setHistoryLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [error, setError] = useState('');

  const [systems, setSystems] = useState([]);
  const [units, setUnits] = useState([]);
  const [capabilities, setCapabilities] = useState([]);
  const [dateStart, setDateStart] = useState('');
  const [dateEnd, setDateEnd] = useState('');
  const [reason, setReason] = useState('');
  const [dryRun, setDryRun] = useState(false);

  const [preflight, setPreflight] = useState(null);
  const [preflightSignature, setPreflightSignature] = useState('');
  const [job, setJob] = useState(null);

  const selectionSignature = useMemo(
    () => JSON.stringify({
      systems: [...systems].sort(),
      units: [...units].sort(),
      capabilities: [...capabilities].sort(),
      date_start: dateStart,
      date_end: dateEnd,
    }),
    [systems, units, capabilities, dateStart, dateEnd]
  );

  const loadCatalog = useCallback(async () => {
    setCatalogLoading(true);
    try {
      const response = await api.get('/sync-historical/catalog');
      setCatalog(response.data);
      setError('');
    } catch (err) {
      setError(err.response?.data?.detail || 'No se pudo cargar el catálogo histórico.');
    } finally {
      setCatalogLoading(false);
    }
  }, []);

  const loadHistory = useCallback(async () => {
    setHistoryLoading(true);
    try {
      const response = await api.get('/sync-historical/jobs?limit=30');
      setHistory(response.data?.items || []);
    } catch {
      setHistory([]);
    } finally {
      setHistoryLoading(false);
    }
  }, []);

  const loadJob = useCallback(async (parentId) => {
    if (!parentId) return;
    try {
      const response = await api.get(`/sync-historical/jobs/${parentId}`);
      setJob(response.data);
      setError('');
    } catch (err) {
      setError(err.response?.data?.detail || 'No se pudo reconstruir el trabajo histórico.');
    }
  }, []);

  useEffect(() => {
    loadCatalog();
    loadHistory();
  }, [loadCatalog, loadHistory]);

  useEffect(() => {
    if (jobFromUrl) loadJob(jobFromUrl);
  }, [jobFromUrl, loadJob]);

  const parentStatus = job?.parent?.Status || job?.parent?.status;
  useEffect(() => {
    if (!jobFromUrl || !ACTIVE_STATUSES.has(parentStatus)) return undefined;
    const timer = setInterval(() => {
      loadJob(jobFromUrl);
      loadHistory();
    }, 4000);
    return () => clearInterval(timer);
  }, [jobFromUrl, parentStatus, loadJob, loadHistory]);

  useEffect(() => {
    if (preflightSignature && preflightSignature !== selectionSignature) {
      setPreflight(null);
      setPreflightSignature('');
    }
  }, [selectionSignature, preflightSignature]);

  const systemItems = catalog?.systems || [];
  const allUnits = catalog?.units || [];
  const unitItems = useMemo(
    () => allUnits.filter((unit) => systems.length === 0 || systems.includes(unit.system_code)),
    [allUnits, systems]
  );

  const selectedUnitObjects = useMemo(
    () => allUnits.filter((unit) => units.includes(unit.unit_code)),
    [allUnits, units]
  );
  const effectiveSystems = useMemo(() => {
    const fromUnits = [...new Set(selectedUnitObjects.map((unit) => unit.system_code).filter(Boolean))];
    return fromUnits.length > 0 ? fromUnits : systems;
  }, [selectedUnitObjects, systems]);

  const categories = catalog?.categories || [];
  const compatibleCategories = useMemo(
    () => categories.map((category) => ({
      ...category,
      capabilities: (category.capabilities || []).filter((capability) =>
        effectiveSystems.length === 0 ||
        effectiveSystems.every((system) => (capability.systems || []).includes(system))
      ),
    })).filter((category) => category.capabilities.length > 0),
    [categories, effectiveSystems]
  );

  const toggle = (setter, values, key) => {
    setter(values.includes(key) ? values.filter((value) => value !== key) : [...values, key]);
  };

  const toggleSystems = (key) => {
    const next = systems.includes(key) ? systems.filter((value) => value !== key) : [...systems, key];
    setSystems(next);
    setUnits((current) => current.filter((unitCode) => {
      const unit = allUnits.find((item) => item.unit_code === unitCode);
      return unit && next.includes(unit.system_code);
    }));
    setCapabilities([]);
  };

  const selectAllSystems = (checked) => {
    setSystems(checked ? systemItems.map((item) => item.code) : []);
    setUnits([]);
    setCapabilities([]);
  };

  const selectAllUnits = (checked) => {
    setUnits(checked ? unitItems.map((item) => item.unit_code) : []);
    setCapabilities([]);
  };

  const allCompatibleCapabilities = useMemo(
    () => compatibleCategories.flatMap((category) => category.capabilities.map((capability) => capability.key)),
    [compatibleCategories]
  );

  const selectAllCapabilities = (checked) => {
    setCapabilities(checked ? allCompatibleCapabilities : []);
  };

  const requestPayload = useMemo(() => ({
    systems,
    units,
    capabilities,
    date_start: dateStart,
    date_end: dateEnd,
  }), [systems, units, capabilities, dateStart, dateEnd]);

  const selectionValid = systems.length > 0 && units.length > 0 && capabilities.length > 0 && dateStart && dateEnd;

  const handlePreflight = async () => {
    if (!selectionValid) return;
    setActionLoading(true);
    setError('');
    try {
      const response = await api.post('/sync-historical/preflight', requestPayload);
      setPreflight(response.data);
      setPreflightSignature(selectionSignature);
    } catch (err) {
      setPreflight(null);
      setPreflightSignature('');
      setError(err.response?.data?.detail || 'El preflight no pudo certificar la selección.');
    } finally {
      setActionLoading(false);
    }
  };

  const handleCreate = async () => {
    if (!preflight?.ready || preflightSignature !== selectionSignature || reason.trim().length < 10) return;
    setActionLoading(true);
    setError('');
    try {
      const response = await api.post('/sync-historical/jobs', {
        ...requestPayload,
        reason: reason.trim(),
        dry_run: dryRun,
      });
      const parentId = response.data?.parent_sync_control_id;
      if (parentId) {
        setSearchParams({ job: String(parentId) });
        await loadJob(parentId);
        await loadHistory();
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'No se pudo crear y encolar el trabajo.');
    } finally {
      setActionLoading(false);
    }
  };

  const runControl = async (action, body = undefined) => {
    const parentId = job?.parent?.SyncControlID;
    if (!parentId) return;
    setActionLoading(true);
    setError('');
    try {
      await api.post(`/sync-historical/jobs/${parentId}/${action}`, body || {});
      await loadJob(parentId);
      await loadHistory();
    } catch (err) {
      setError(err.response?.data?.detail || `No se pudo ejecutar ${action}.`);
    } finally {
      setActionLoading(false);
    }
  };

  if (catalogLoading) {
    return (
      <div className="flex h-96 items-center justify-center">
        <Loader2 className="mr-2 h-7 w-7 animate-spin text-blue-600" />
        <span className="text-zinc-600">Cargando catálogo canónico...</span>
      </div>
    );
  }

  return (
    <div className="space-y-6 p-6" data-testid="sync-historical-page">
      <div className="flex flex-col justify-between gap-4 lg:flex-row lg:items-start">
        <div>
          <Button variant="ghost" size="sm" className="mb-2 -ml-2" onClick={() => navigate('/admin/sync-monitor')}>
            <ArrowLeft className="mr-2 h-4 w-4" /> Volver a Sincronización
          </Button>
          <h1 className="flex items-center gap-3 text-3xl font-bold text-zinc-950">
            <Database className="h-8 w-8 text-blue-600" />
            Sincronización Histórica de Tablas
          </h1>
          <p className="mt-1 text-sm text-zinc-500">Panel de control de sincronización EDARSAHUB</p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Badge variant="outline"><Activity className="mr-1 h-3 w-3" /> Sincronización en curso</Badge>
          <Badge variant="outline"><Layers3 className="mr-1 h-3 w-3" /> Módulo escalable</Badge>
          <Badge variant="outline"><CheckCircle2 className="mr-1 h-3 w-3" /> Multiselección activa</Badge>
          <Badge variant="outline"><History className="mr-1 h-3 w-3" /> Histórico</Badge>
        </div>
      </div>

      {error && (
        <div className="flex items-start gap-3 rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-800">
          <AlertTriangle className="mt-0.5 h-4 w-4 flex-none" />
          <span>{String(error)}</span>
        </div>
      )}

      <div className="grid gap-4 xl:grid-cols-3">
        <CheckList
          title="Sistemas"
          items={systemItems}
          selected={systems}
          getKey={(item) => item.code}
          getLabel={(item) => item.name || item.code}
          getMeta={(item) => item.code}
          onToggle={(key) => toggleSystems(key)}
          onToggleAll={selectAllSystems}
        />
        <CheckList
          title="Sucursales a sincronizar"
          items={unitItems}
          selected={units}
          getKey={(item) => item.unit_code}
          getLabel={(item) => item.unit_name || item.unit_code}
          getMeta={(item) => `${item.system_name || item.system_code} · ${item.connection_name || 'Servidor canónico'}`}
          onToggle={(key) => {
            toggle(setUnits, units, key);
            setCapabilities([]);
          }}
          onToggleAll={selectAllUnits}
        />
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <CalendarRange className="h-4 w-4" /> Rango de fechas
            </CardTitle>
            <CardDescription>El planner divide el rango según metadata de cada capability.</CardDescription>
          </CardHeader>
          <CardContent className="grid gap-4">
            <div className="space-y-2">
              <Label htmlFor="historical-date-start">Fecha inicio</Label>
              <Input id="historical-date-start" type="date" value={dateStart} onChange={(e) => setDateStart(e.target.value)} />
            </div>
            <div className="space-y-2">
              <Label htmlFor="historical-date-end">Fecha fin</Label>
              <Input id="historical-date-end" type="date" value={dateEnd} onChange={(e) => setDateEnd(e.target.value)} />
            </div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <div className="flex flex-col justify-between gap-3 sm:flex-row sm:items-center">
            <div>
              <CardTitle className="flex items-center gap-2">
                <TableProperties className="h-5 w-5" /> Capacidades / tablas
              </CardTitle>
              <CardDescription>
                Generadas desde el registry canónico y filtradas por compatibilidad real de los sistemas seleccionados.
              </CardDescription>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={() => selectAllCapabilities(capabilities.length !== allCompatibleCapabilities.length)}
              disabled={allCompatibleCapabilities.length === 0}
            >
              {capabilities.length === allCompatibleCapabilities.length && allCompatibleCapabilities.length > 0
                ? 'Quitar todas'
                : 'Seleccionar todas'}
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
            {compatibleCategories.map((category) => {
              const keys = category.capabilities.map((capability) => capability.key);
              const selectedCount = keys.filter((key) => capabilities.includes(key)).length;
              return (
                <div key={category.key} className="rounded-lg border border-zinc-200 bg-zinc-50/60 p-4">
                  <div className="mb-3 flex items-center justify-between border-b pb-2">
                    <div>
                      <p className="font-semibold text-zinc-900">{category.name || category.key}</p>
                      <p className="text-xs text-zinc-500">{selectedCount}/{keys.length} seleccionadas</p>
                    </div>
                    <button
                      type="button"
                      className="text-xs text-blue-600 hover:underline"
                      onClick={() => {
                        const allSelected = keys.every((key) => capabilities.includes(key));
                        setCapabilities((current) => allSelected
                          ? current.filter((key) => !keys.includes(key))
                          : [...new Set([...current, ...keys])]);
                      }}
                    >
                      {keys.every((key) => capabilities.includes(key)) ? 'Quitar grupo' : 'Seleccionar grupo'}
                    </button>
                  </div>
                  <div className="space-y-2">
                    {category.capabilities.map((capability) => (
                      <label key={capability.key} className="flex cursor-pointer items-start gap-3 rounded-md bg-white p-2">
                        <Checkbox
                          checked={capabilities.includes(capability.key)}
                          onCheckedChange={() => toggle(setCapabilities, capabilities, capability.key)}
                        />
                        <span className="flex-1">
                          <span className="block text-sm font-medium">{capability.display_name || capability.key}</span>
                          <span className="block text-xs text-zinc-500">
                            {capability.entity_key}
                            {capability.supports_resume ? ' · reanudable' : ''}
                            {capability.supports_safe_stop ? ' · detención segura' : ''}
                          </span>
                        </span>
                      </label>
                    ))}
                  </div>
                </div>
              );
            })}
          </div>
          {compatibleCategories.length === 0 && (
            <p className="py-8 text-center text-sm text-zinc-500">
              Selecciona sistemas y sucursales con capabilities históricas certificadas.
            </p>
          )}
        </CardContent>
      </Card>

      <div className="grid gap-4 lg:grid-cols-[1.4fr_1fr]">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2"><ShieldCheck className="h-5 w-5" /> Preflight obligatorio</CardTitle>
            <CardDescription>
              Revalida sistemas, sucursales, capabilities, dependencias y número de unidades atómicas antes de encolar.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <Button onClick={handlePreflight} disabled={!selectionValid || actionLoading}>
              {actionLoading ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <ShieldCheck className="mr-2 h-4 w-4" />}
              Ejecutar preflight
            </Button>
            {preflight && (
              <div className={`rounded-lg border p-4 ${preflight.ready ? 'border-emerald-200 bg-emerald-50' : 'border-red-200 bg-red-50'}`}>
                <div className="flex items-center gap-2">
                  {preflight.ready ? <CheckCircle2 className="h-5 w-5 text-emerald-600" /> : <XCircle className="h-5 w-5 text-red-600" />}
                  <strong>{preflight.ready ? 'Plan listo para ejecución' : 'Plan bloqueado'}</strong>
                </div>
                <p className="mt-2 text-sm">
                  {preflight.total_atomic_units} unidad(es) atómica(s) · límite {preflight.max_atomic_units}.
                </p>
                {preflight.preview_truncated && <p className="mt-1 text-xs">La vista previa se limita a 200 unidades.</p>}
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2"><Zap className="h-5 w-5" /> Crear trabajo</CardTitle>
            <CardDescription>La API solo persiste y encola. La ejecución real pertenece al Worker Universal V1.2.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label>Motivo auditable</Label>
              <Textarea value={reason} onChange={(e) => setReason(e.target.value)} rows={3} placeholder="Motivo de la sincronización histórica..." />
              <p className="text-xs text-zinc-500">{reason.trim().length}/10 caracteres mínimos</p>
            </div>
            <label className="flex items-center gap-2 text-sm text-zinc-700">
              <Checkbox checked={dryRun} onCheckedChange={(value) => setDryRun(Boolean(value))} />
              Ejecutar como DRY RUN
            </label>
            <Button
              className="w-full"
              onClick={handleCreate}
              disabled={!preflight?.ready || preflightSignature !== selectionSignature || reason.trim().length < 10 || actionLoading}
            >
              <Play className="mr-2 h-4 w-4" /> Iniciar sincronización histórica
            </Button>
          </CardContent>
        </Card>
      </div>

      {job?.parent && (
        <Card className="border-blue-200" data-testid="historical-active-job">
          <CardHeader>
            <div className="flex flex-col justify-between gap-3 md:flex-row md:items-start">
              <div>
                <CardTitle className="flex items-center gap-2">
                  <Activity className="h-5 w-5 text-blue-600" /> Estado de sincronización
                </CardTitle>
                <CardDescription>
                  Job #{job.parent.SyncControlID} · {job.parent.SyncRunID} · {job.parent.Reason}
                </CardDescription>
              </div>
              <Badge className={statusTone(parentStatus)} variant="outline">{parentStatus || '-'}</Badge>
            </div>
          </CardHeader>
          <CardContent className="space-y-5">
            <div>
              <div className="mb-2 flex justify-between text-sm">
                <span>{job.progress?.terminal || 0} de {job.progress?.total || 0} unidades terminales</span>
                <strong>{job.progress?.percent || 0}%</strong>
              </div>
              <div className="h-3 overflow-hidden rounded-full bg-zinc-200">
                <div className="h-full bg-blue-600 transition-all" style={{ width: `${Math.min(100, job.progress?.percent || 0)}%` }} />
              </div>
              <div className="mt-2 flex flex-wrap gap-2">
                {Object.entries(job.progress?.by_status || {}).map(([statusKey, count]) => (
                  <Badge key={statusKey} variant="outline" className={statusTone(statusKey)}>{statusKey}: {count}</Badge>
                ))}
              </div>
            </div>

            <div className="flex flex-wrap gap-2">
              <Button variant="outline" onClick={() => loadJob(job.parent.SyncControlID)} disabled={actionLoading}>
                <RefreshCw className="mr-2 h-4 w-4" /> Actualizar
              </Button>
              {ACTIVE_STATUSES.has(parentStatus) && parentStatus !== 'PAUSE_REQUESTED' && (
                <Button variant="outline" onClick={() => runControl('pause')} disabled={actionLoading}>
                  <Pause className="mr-2 h-4 w-4" /> Pausar
                </Button>
              )}
              {ACTIVE_STATUSES.has(parentStatus) && parentStatus !== 'CANCEL_REQUESTED' && (
                <Button variant="destructive" onClick={() => runControl('cancel')} disabled={actionLoading}>
                  <CircleStop className="mr-2 h-4 w-4" /> Detener de manera segura
                </Button>
              )}
              {['PAUSED', 'PAUSE_REQUESTED', 'CANCELLED_SAFE', 'ENQUEUE_FAILED'].includes(parentStatus) && (
                <Button onClick={() => runControl('resume', { retry_failed: false })} disabled={actionLoading}>
                  <RotateCcw className="mr-2 h-4 w-4" /> Reanudar
                </Button>
              )}
              {parentStatus === 'PARTIAL_FAILED' && (
                <Button onClick={() => runControl('resume', { retry_failed: true })} disabled={actionLoading}>
                  <RotateCcw className="mr-2 h-4 w-4" /> Reintentar solo fallidos
                </Button>
              )}
            </div>

            <div className="grid gap-4 xl:grid-cols-2">
              <div className="rounded-lg border">
                <div className="border-b px-4 py-3 font-semibold">Unidades atómicas</div>
                <div className="max-h-80 overflow-auto divide-y">
                  {(job.children || []).map((child) => (
                    <div key={child.SyncControlID} className="grid grid-cols-[1fr_auto] gap-3 p-3 text-sm">
                      <div>
                        <p className="font-medium">{child.CodigoSync}</p>
                        <p className="text-xs text-zinc-500">
                          {String(child.FechaInicio || '').slice(0, 10)} → {String(child.FechaFin || '').slice(0, 10)}
                          {' · '}intento {child.AttemptCount || 0}/{child.MaxAttempts || 0}
                        </p>
                        {child.ErrorMessage && <p className="mt-1 text-xs text-red-600">{child.ErrorMessage}</p>}
                      </div>
                      <Badge variant="outline" className={statusTone(child.Status)}>{child.Status}</Badge>
                    </div>
                  ))}
                </div>
              </div>
              <div className="rounded-lg border">
                <div className="border-b px-4 py-3 font-semibold">Bitácora persistente</div>
                <div className="max-h-80 overflow-auto divide-y">
                  {(job.logs || []).length === 0 && <p className="p-4 text-sm text-zinc-500">Sin eventos registrados todavía.</p>}
                  {(job.logs || []).map((entry) => (
                    <div key={entry.id} className="p-3 text-sm">
                      <div className="flex items-center justify-between gap-2">
                        <strong>{entry.EventCode || entry.type}</strong>
                        <span className="text-xs text-zinc-500">{formatDateTime(entry.timestamp)}</span>
                      </div>
                      <p className="mt-1 text-zinc-600">{entry.message}</p>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2"><History className="h-5 w-5" /> Historial de ejecuciones</CardTitle>
          <CardDescription>Persistente y reconstruible después de recargar la pantalla.</CardDescription>
        </CardHeader>
        <CardContent>
          {historyLoading ? (
            <div className="flex items-center py-6 text-sm text-zinc-500"><Loader2 className="mr-2 h-4 w-4 animate-spin" /> Cargando historial...</div>
          ) : history.length === 0 ? (
            <p className="py-6 text-sm text-zinc-500">No hay trabajos históricos registrados.</p>
          ) : (
            <div className="divide-y rounded-lg border">
              {history.map((item) => (
                <button
                  type="button"
                  key={item.SyncControlID}
                  onClick={() => setSearchParams({ job: String(item.SyncControlID) })}
                  className="grid w-full gap-3 p-4 text-left hover:bg-zinc-50 md:grid-cols-[1fr_auto_auto]"
                >
                  <span>
                    <span className="block font-medium">Job #{item.SyncControlID} · {item.Reason || 'Sin motivo'}</span>
                    <span className="block text-xs text-zinc-500">
                      {formatDateTime(item.StartedAtUTC)} · {item.TotalAtomicUnits || 0} unidades · {item.RequestedBy || '-'}
                    </span>
                  </span>
                  <span className="text-sm text-zinc-600">
                    {item.SuccessCount || 0} OK · {item.FailureCount || 0} error
                  </span>
                  <span className="flex items-center gap-2">
                    <Badge variant="outline" className={statusTone(item.Status)}>{item.Status}</Badge>
                    <ChevronRight className="h-4 w-4 text-zinc-400" />
                  </span>
                </button>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      <div className="flex items-center gap-2 text-xs text-zinc-500">
        <Server className="h-3.5 w-3.5" />
        Catálogo, sucursales, servidores y capabilities provienen de metadata canónica. El frontend no contiene listas fijas.
        <Clock3 className="ml-2 h-3.5 w-3.5" />
        Polling controlado solo mientras existe un trabajo activo.
      </div>
    </div>
  );
}
