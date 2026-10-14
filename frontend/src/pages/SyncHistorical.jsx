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
  BarChart3,
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
  'PENDING',
  'QUEUED',
  'PROCESSING',
  'RUNNING',
  'RETRYING',
  'WAITING_RETRY',
  'FAILED_RETRYABLE',
  'PAUSE_REQUESTED',
  'CANCEL_REQUESTED',
]);

const TERMINAL_OK = new Set(['SUCCESS', 'DONE', 'CANCELLED_SAFE']);
const TERMINAL_ERROR = new Set(['PARTIAL_FAILED', 'PERMANENT_FAILURE', 'FAILED', 'ENQUEUE_FAILED']);
const TERMINAL_PROGRESS = new Set(['SUCCESS', 'DONE', 'PERMANENT_FAILURE', 'FAILED', 'CANCELLED_SAFE']);

const CATEGORY_PALETTES = [
  {
    shell: 'border-blue-200 bg-blue-50/40',
    header: 'border-blue-200 bg-blue-50/80',
    accent: 'text-blue-700',
    bar: 'bg-blue-600',
  },
  {
    shell: 'border-emerald-200 bg-emerald-50/40',
    header: 'border-emerald-200 bg-emerald-50/80',
    accent: 'text-emerald-700',
    bar: 'bg-emerald-500',
  },
  {
    shell: 'border-amber-200 bg-amber-50/40',
    header: 'border-amber-200 bg-amber-50/80',
    accent: 'text-amber-700',
    bar: 'bg-amber-500',
  },
  {
    shell: 'border-violet-200 bg-violet-50/40',
    header: 'border-violet-200 bg-violet-50/80',
    accent: 'text-violet-700',
    bar: 'bg-violet-500',
  },
  {
    shell: 'border-cyan-200 bg-cyan-50/40',
    header: 'border-cyan-200 bg-cyan-50/80',
    accent: 'text-cyan-700',
    bar: 'bg-cyan-500',
  },
];

const CATEGORY_ICONS = [Database, Layers3, TableProperties, Server, Activity];

const formatDateTime = (value) => {
  if (!value) return '-';
  try {
    return new Date(value).toLocaleString('es-MX');
  } catch {
    return '-';
  }
};

const formatTime = (value) => {
  if (!value) return '-';
  try {
    return new Date(value).toLocaleTimeString('es-MX', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    });
  } catch {
    return '-';
  }
};

const statusTone = (status) => {
  const normalized = String(status || '').toUpperCase();
  if (TERMINAL_OK.has(normalized)) return 'border-emerald-200 bg-emerald-100 text-emerald-800';
  if (TERMINAL_ERROR.has(normalized)) return 'border-red-200 bg-red-100 text-red-800';
  if (normalized === 'PAUSED' || normalized === 'PAUSE_REQUESTED') return 'border-amber-200 bg-amber-100 text-amber-800';
  if (ACTIVE_STATUSES.has(normalized)) return 'border-blue-200 bg-blue-100 text-blue-800';
  return 'border-zinc-200 bg-zinc-100 text-zinc-700';
};

const eventTone = (type) => {
  const normalized = String(type || '').toUpperCase();
  if (normalized.includes('ERROR') || normalized.includes('FAIL')) return 'border-red-200 bg-red-50 text-red-700';
  if (normalized.includes('WARN')) return 'border-amber-200 bg-amber-50 text-amber-700';
  if (normalized.includes('SUCCESS') || normalized.includes('OK')) return 'border-emerald-200 bg-emerald-50 text-emerald-700';
  return 'border-blue-200 bg-blue-50 text-blue-700';
};

const ProgressBar = ({ value, barClass = 'bg-blue-600', heightClass = 'h-2.5' }) => {
  const safe = Math.max(0, Math.min(100, Number(value) || 0));
  return (
    <div className={heightClass + ' overflow-hidden rounded-full bg-zinc-200'}>
      <div
        className={'h-full rounded-full transition-all duration-300 ' + barClass}
        style={{ width: safe + '%' }}
      />
    </div>
  );
};

const SelectionList = ({
  title,
  subtitle,
  items,
  selected,
  getKey,
  getLabel,
  getMeta,
  onToggle,
  onToggleAll,
}) => {
  const all = items.length > 0 && items.every((item) => selected.includes(getKey(item)));
  const some = items.some((item) => selected.includes(getKey(item)));

  return (
    <Card className="h-full">
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between gap-3">
          <div>
            <CardTitle className="text-base">{title}</CardTitle>
            <CardDescription>{subtitle}</CardDescription>
          </div>
          <Badge variant="outline" className="whitespace-nowrap">
            {selected.length}/{items.length}
          </Badge>
        </div>
      </CardHeader>
      <CardContent>
        <button
          type="button"
          onClick={() => onToggleAll(!all)}
          disabled={items.length === 0}
          className="mb-3 text-xs font-semibold text-blue-600 hover:underline disabled:text-zinc-400"
        >
          {all ? 'Quitar todo' : some ? 'Completar selección' : 'Seleccionar todo'}
        </button>
        <div className="max-h-56 space-y-2 overflow-y-auto pr-1">
          {items.length === 0 && (
            <p className="rounded-md border border-dashed p-4 text-sm text-zinc-500">
              Sin opciones canónicas disponibles.
            </p>
          )}
          {items.map((item) => {
            const key = getKey(item);
            const checked = selected.includes(key);
            return (
              <label
                key={key}
                className={
                  'flex cursor-pointer items-start gap-3 rounded-lg border p-3 transition ' +
                  (checked ? 'border-blue-300 bg-blue-50' : 'border-zinc-200 bg-white hover:bg-zinc-50')
                }
              >
                <Checkbox checked={checked} onCheckedChange={() => onToggle(key)} />
                <span className="min-w-0 flex-1">
                  <span className="block text-sm font-semibold text-zinc-900">{getLabel(item)}</span>
                  {getMeta && <span className="mt-0.5 block text-xs text-zinc-500">{getMeta(item)}</span>}
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
      const response = await api.get('/sync-historical/jobs/' + parentId);
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
  const activeJob = Boolean(job?.parent && ACTIVE_STATUSES.has(String(parentStatus || '').toUpperCase()));

  useEffect(() => {
    if (!jobFromUrl || !activeJob) return undefined;
    const timer = setInterval(() => {
      loadJob(jobFromUrl);
      loadHistory();
    }, 4000);
    return () => clearInterval(timer);
  }, [jobFromUrl, activeJob, loadJob, loadHistory]);

  useEffect(() => {
    if (preflightSignature && preflightSignature !== selectionSignature) {
      setPreflight(null);
      setPreflightSignature('');
    }
  }, [selectionSignature, preflightSignature]);

  const systemItems = catalog?.systems || [];
  const allUnits = catalog?.units || [];
  const categories = catalog?.categories || [];

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

  const capabilityIndex = useMemo(() => {
    const index = new Map();
    categories.forEach((category) => {
      (category.capabilities || []).forEach((capability) => {
        index.set(capability.key, { ...capability, category });
      });
    });
    return index;
  }, [categories]);

  const isCapabilitySelectable = useCallback((capability) => {
    const eligibleSystems = capability?.eligible_systems || capability?.systems || [];
    const executionEnabled = capability?.execution_enabled !== undefined
      ? Boolean(capability.execution_enabled)
      : eligibleSystems.length > 0;
    return executionEnabled
      && effectiveSystems.length > 0
      && effectiveSystems.some((system) => eligibleSystems.includes(system));
  }, [effectiveSystems]);

  const selectableCapabilityKeys = useMemo(
    () => categories.flatMap((category) =>
      (category.capabilities || [])
        .filter((capability) => isCapabilitySelectable(capability))
        .map((capability) => capability.key)
    ),
    [categories, isCapabilitySelectable]
  );

  useEffect(() => {
    setCapabilities((current) => current.filter((key) => selectableCapabilityKeys.includes(key)));
  }, [selectableCapabilityKeys]);

  const toggleSystems = (key) => {
    const next = systems.includes(key)
      ? systems.filter((value) => value !== key)
      : [...systems, key];
    setSystems(next);
    setUnits((current) => current.filter((unitCode) => {
      const unit = allUnits.find((item) => item.unit_code === unitCode);
      return unit && next.includes(unit.system_code);
    }));
  };

  const toggleUnit = (key) => {
    const item = allUnits.find((unit) => unit.unit_code === key);
    const selecting = !units.includes(key);
    if (selecting && item?.system_code && !systems.includes(item.system_code)) {
      setSystems((current) => [...new Set([...current, item.system_code])]);
    }
    setUnits((current) => selecting ? [...current, key] : current.filter((value) => value !== key));
  };

  const selectAllSystems = (checked) => {
    setSystems(checked ? systemItems.map((item) => item.code) : []);
    if (!checked) setUnits([]);
  };

  const selectAllUnits = (checked) => {
    if (checked) {
      setUnits(unitItems.map((item) => item.unit_code));
      setSystems((current) => [...new Set([
        ...current,
        ...unitItems.map((item) => item.system_code).filter(Boolean),
      ])]);
    } else {
      setUnits([]);
    }
  };

  const toggleCapability = (key) => {
    const item = capabilityIndex.get(key);
    if (!item || !isCapabilitySelectable(item)) return;
    setCapabilities((current) => current.includes(key)
      ? current.filter((value) => value !== key)
      : [...current, key]);
  };

  const toggleCategory = (category) => {
    const keys = (category.capabilities || [])
      .filter((capability) => isCapabilitySelectable(capability))
      .map((capability) => capability.key);
    const allSelected = keys.length > 0 && keys.every((key) => capabilities.includes(key));
    setCapabilities((current) => allSelected
      ? current.filter((key) => !keys.includes(key))
      : [...new Set([...current, ...keys])]);
  };

  const selectAllCapabilities = (checked) => {
    setCapabilities(checked ? selectableCapabilityKeys : []);
  };

  const requestPayload = useMemo(() => ({
    systems,
    units,
    capabilities,
    date_start: dateStart,
    date_end: dateEnd,
  }), [systems, units, capabilities, dateStart, dateEnd]);

  const selectionValid = systems.length > 0
    && units.length > 0
    && capabilities.length > 0
    && Boolean(dateStart)
    && Boolean(dateEnd);

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
      await api.post('/sync-historical/jobs/' + parentId + '/' + action, body || {});
      await loadJob(parentId);
      await loadHistory();
    } catch (err) {
      setError(err.response?.data?.detail || ('No se pudo ejecutar ' + action + '.'));
    } finally {
      setActionLoading(false);
    }
  };

  const categoryProgress = useMemo(() => {
    const rows = new Map();
    (job?.children || []).forEach((child) => {
      const key = child.CategoriaCodigo || 'OTROS';
      const current = rows.get(key) || {
        key,
        total: 0,
        terminal: 0,
        success: 0,
        failed: 0,
      };
      current.total += 1;
      const state = String(child.Status || '').toUpperCase();
      if (TERMINAL_PROGRESS.has(state)) current.terminal += 1;
      if (TERMINAL_OK.has(state)) current.success += 1;
      if (TERMINAL_ERROR.has(state)) current.failed += 1;
      rows.set(key, current);
    });

    return [...rows.values()].map((row) => {
      const catalogCategory = categories.find((category) => category.key === row.key);
      return {
        ...row,
        name: catalogCategory?.name || row.key,
        percent: row.total ? Math.round((row.terminal * 100) / row.total) : 0,
      };
    });
  }, [job, categories]);

  const selectionProgressRows = useMemo(() => {
    if (categoryProgress.length > 0) return categoryProgress;
    return categories
      .map((category) => {
        const keys = (category.capabilities || []).map((capability) => capability.key);
        const selectedCount = keys.filter((key) => capabilities.includes(key)).length;
        return {
          key: category.key,
          name: category.name || category.key,
          total: selectedCount,
          terminal: 0,
          success: 0,
          failed: 0,
          percent: 0,
        };
      })
      .filter((row) => row.total > 0);
  }, [categoryProgress, categories, capabilities]);

  const unitById = useMemo(() => {
    const map = new Map();
    allUnits.forEach((unit) => {
      if (unit.unit_id) map.set(String(unit.unit_id).toLowerCase(), unit);
    });
    return map;
  }, [allUnits]);

  const childById = useMemo(() => {
    const map = new Map();
    (job?.children || []).forEach((child) => map.set(String(child.SyncControlID), child));
    return map;
  }, [job]);

  const recentEvents = useMemo(
    () => (job?.logs || []).slice(0, 12).map((entry) => {
      const child = childById.get(String(entry.SyncControlID));
      const unit = child?.UnidadNegocioID
        ? unitById.get(String(child.UnidadNegocioID).toLowerCase())
        : null;
      const capability = child?.CodigoSync ? capabilityIndex.get(child.CodigoSync) : null;
      return {
        ...entry,
        child,
        unit,
        capability,
        displayType: String(entry.type || entry.EventCode || 'INFO').toUpperCase(),
      };
    }),
    [job, childById, unitById, capabilityIndex]
  );

  const overallPercent = Number(job?.progress?.percent || 0);
  const catalogCounts = catalog?.counts || {};

  if (catalogLoading) {
    return (
      <div className="flex h-96 items-center justify-center">
        <Loader2 className="mr-2 h-7 w-7 animate-spin text-blue-600" />
        <span className="text-zinc-600">Cargando catálogo canónico...</span>
      </div>
    );
  }

  return (
    <div className="space-y-5 p-4 lg:p-6" data-testid="sync-historical-page">
      <div className="flex flex-col justify-between gap-4 xl:flex-row xl:items-start">
        <div>
          <Button
            variant="ghost"
            size="sm"
            className="mb-2 -ml-2"
            onClick={() => navigate('/admin/sync-monitor')}
          >
            <ArrowLeft className="mr-2 h-4 w-4" /> Volver a Sincronización
          </Button>
          <h1 className="flex items-center gap-3 text-3xl font-bold text-zinc-950">
            <Database className="h-8 w-8 text-blue-600" />
            Sincronización Histórica de Tablas
          </h1>
          <p className="mt-1 text-sm text-zinc-500">
            Panel transversal para selección, preflight, ejecución atómica, avance y auditoría.
          </p>
        </div>

        <div className="flex flex-wrap gap-2">
          <Badge variant="outline" className={activeJob ? 'border-emerald-200 bg-emerald-50 text-emerald-700' : ''}>
            <Activity className="mr-1 h-3 w-3" />
            {activeJob ? 'Sincronización en curso' : 'Sin trabajo activo'}
          </Badge>
          <Badge variant="outline"><ShieldCheck className="mr-1 h-3 w-3" /> Catálogo canónico</Badge>
          <Badge variant="outline"><Layers3 className="mr-1 h-3 w-3" /> Unidades atómicas</Badge>
          <Badge variant="outline"><TableProperties className="mr-1 h-3 w-3" /> Módulo transversal</Badge>
        </div>
      </div>

      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        <div className="rounded-xl border bg-white px-4 py-3">
          <p className="text-xs font-medium uppercase tracking-wide text-zinc-500">Sistemas canónicos</p>
          <p className="mt-1 text-2xl font-bold text-zinc-950">{catalogCounts.systems ?? systemItems.length}</p>
        </div>
        <div className="rounded-xl border bg-white px-4 py-3">
          <p className="text-xs font-medium uppercase tracking-wide text-zinc-500">Sucursales resolubles</p>
          <p className="mt-1 text-2xl font-bold text-zinc-950">{catalogCounts.units ?? allUnits.length}</p>
        </div>
        <div className="rounded-xl border bg-white px-4 py-3">
          <p className="text-xs font-medium uppercase tracking-wide text-zinc-500">Tablas / capabilities declaradas</p>
          <p className="mt-1 text-2xl font-bold text-zinc-950">{catalogCounts.declared_capabilities ?? capabilityIndex.size}</p>
        </div>
        <div className="rounded-xl border bg-white px-4 py-3">
          <p className="text-xs font-medium uppercase tracking-wide text-zinc-500">Ejecutables históricamente</p>
          <p className="mt-1 text-2xl font-bold text-blue-700">
            {catalogCounts.executable_capabilities ?? selectableCapabilityKeys.length}
          </p>
        </div>
      </div>

      {error && (
        <div className="flex items-start gap-3 rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-800">
          <AlertTriangle className="mt-0.5 h-4 w-4 flex-none" />
          <span>{String(error)}</span>
        </div>
      )}

      <div className="grid gap-4 xl:grid-cols-3">
        <SelectionList
          title="Sistemas"
          subtitle="Selecciona uno o más sistemas dados de alta."
          items={systemItems}
          selected={systems}
          getKey={(item) => item.code}
          getLabel={(item) => item.name || item.code}
          getMeta={(item) => item.code}
          onToggle={toggleSystems}
          onToggleAll={selectAllSystems}
        />

        <SelectionList
          title="Sucursales a sincronizar"
          subtitle="Filtradas por los sistemas seleccionados."
          items={unitItems}
          selected={units}
          getKey={(item) => item.unit_code}
          getLabel={(item) => item.unit_name || item.unit_code}
          getMeta={(item) =>
            (item.system_name || item.system_code)
            + ' · '
            + (item.branch_name || item.connection_name || 'Servidor canónico')
          }
          onToggle={toggleUnit}
          onToggleAll={selectAllUnits}
        />

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <CalendarRange className="h-4 w-4 text-blue-600" /> Rango de fechas
            </CardTitle>
            <CardDescription>
              El planner divide el rango según la metadata atómica de cada capability.
            </CardDescription>
          </CardHeader>
          <CardContent className="grid gap-4">
            <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-1 2xl:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="historical-date-start">Fecha inicial</Label>
                <Input
                  id="historical-date-start"
                  type="date"
                  value={dateStart}
                  onChange={(event) => setDateStart(event.target.value)}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="historical-date-end">Fecha final</Label>
                <Input
                  id="historical-date-end"
                  type="date"
                  value={dateEnd}
                  onChange={(event) => setDateEnd(event.target.value)}
                />
              </div>
            </div>
            <div className="rounded-lg border border-blue-100 bg-blue-50 p-3 text-xs text-blue-800">
              El frontend no decide bloques ni compatibilidades: el preflight canónico los revalida antes de encolar.
            </div>
          </CardContent>
        </Card>
      </div>

      <Card data-testid="historical-table-catalog">
        <CardHeader className="pb-3">
          <div className="flex flex-col justify-between gap-3 sm:flex-row sm:items-center">
            <div>
              <CardTitle className="flex items-center gap-2">
                <TableProperties className="h-5 w-5 text-blue-600" /> Tablas del sistema
              </CardTitle>
              <CardDescription>
                Organizadas por módulo desde metadata canónica. Las no certificadas se muestran, pero no se pueden ejecutar.
              </CardDescription>
            </div>
            <div className="flex items-center gap-2">
              <Badge variant="outline">{capabilities.length} seleccionadas</Badge>
              <Button
                variant="outline"
                size="sm"
                onClick={() => selectAllCapabilities(capabilities.length !== selectableCapabilityKeys.length)}
                disabled={selectableCapabilityKeys.length === 0}
              >
                {capabilities.length === selectableCapabilityKeys.length && selectableCapabilityKeys.length > 0
                  ? 'Quitar ejecutables'
                  : 'Seleccionar ejecutables'}
              </Button>
            </div>
          </div>
        </CardHeader>

        <CardContent>
          {categories.length === 0 ? (
            <div className="rounded-lg border border-dashed p-8 text-center">
              <TableProperties className="mx-auto h-8 w-8 text-zinc-400" />
              <p className="mt-2 text-sm font-medium text-zinc-700">No existen capabilities declaradas.</p>
              <p className="mt-1 text-xs text-zinc-500">El frontend no inventa tablas fuera del catálogo canónico.</p>
            </div>
          ) : (
            <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-5">
              {categories.map((category, index) => {
                const palette = CATEGORY_PALETTES[index % CATEGORY_PALETTES.length];
                const CategoryIcon = CATEGORY_ICONS[index % CATEGORY_ICONS.length];
                const categoryCapabilities = category.capabilities || [];
                const selectable = categoryCapabilities.filter((capability) => isCapabilitySelectable(capability));
                const selectedCount = categoryCapabilities.filter((capability) => capabilities.includes(capability.key)).length;
                const allSelectableSelected = selectable.length > 0
                  && selectable.every((capability) => capabilities.includes(capability.key));

                return (
                  <div key={category.key} className={'overflow-hidden rounded-xl border ' + palette.shell}>
                    <div className={'flex items-center justify-between gap-2 border-b px-4 py-3 ' + palette.header}>
                      <div className="flex min-w-0 items-center gap-2">
                        <CategoryIcon className={'h-5 w-5 flex-none ' + palette.accent} />
                        <div className="min-w-0">
                          <p className={'truncate font-bold ' + palette.accent}>{category.name || category.key}</p>
                          <p className="text-[11px] text-zinc-500">
                            {selectedCount}/{categoryCapabilities.length} seleccionadas
                          </p>
                        </div>
                      </div>
                      <Checkbox
                        checked={allSelectableSelected}
                        disabled={selectable.length === 0}
                        onCheckedChange={() => toggleCategory(category)}
                      />
                    </div>

                    <div className="space-y-2 p-3">
                      {categoryCapabilities.map((capability) => {
                        const selectableNow = isCapabilitySelectable(capability);
                        const checked = capabilities.includes(capability.key);
                        const eligibleSystems = capability.eligible_systems || capability.systems || [];
                        const compatibleSelectedSystems = effectiveSystems.filter(
                          (system) => eligibleSystems.includes(system)
                        );
                        const partiallyCompatible = selectableNow
                          && compatibleSelectedSystems.length > 0
                          && compatibleSelectedSystems.length < effectiveSystems.length;
                        const noCompatibleSelectedSystem = effectiveSystems.length > 0
                          && compatibleSelectedSystems.length === 0;

                        return (
                          <label
                            key={capability.key}
                            className={
                              'flex gap-2 rounded-lg border p-2.5 transition ' +
                              (selectableNow
                                ? (checked ? 'cursor-pointer border-blue-300 bg-white shadow-sm' : 'cursor-pointer border-white bg-white/90 hover:border-zinc-300')
                                : 'cursor-not-allowed border-zinc-200 bg-zinc-100/80 opacity-75')
                            }
                          >
                            <Checkbox
                              checked={checked}
                              disabled={!selectableNow}
                              onCheckedChange={() => toggleCapability(capability.key)}
                            />
                            <span className="min-w-0 flex-1">
                              <span className="block text-sm font-semibold text-zinc-900">
                                {capability.display_name || capability.key}
                              </span>
                              <span className="mt-0.5 block break-words text-[11px] text-zinc-500">
                                {capability.table_name
                                  ? ('Tabla: ' + capability.table_name)
                                  : (capability.entity_key || capability.key)}
                              </span>
                              <span className="mt-1 flex flex-wrap gap-1">
                                {capability.supports_resume && (
                                  <span className="rounded bg-zinc-200 px-1.5 py-0.5 text-[10px] text-zinc-600">reanudable</span>
                                )}
                                {capability.supports_safe_stop && (
                                  <span className="rounded bg-zinc-200 px-1.5 py-0.5 text-[10px] text-zinc-600">safe stop</span>
                                )}
                                {capability.chunk_unit && (
                                  <span className="rounded bg-zinc-200 px-1.5 py-0.5 text-[10px] text-zinc-600">
                                    bloque {capability.chunk_unit}
                                  </span>
                                )}
                              </span>
                              {partiallyCompatible && (
                                <span className="mt-1 block text-[10px] font-medium text-blue-700">
                                  Compatible con {compatibleSelectedSystems.length} de {effectiveSystems.length} sistema(s);
                                  el planner ejecutará solo las sucursales válidas.
                                </span>
                              )}
                              {!selectableNow && (
                                <span className="mt-1 block text-[10px] font-medium text-amber-700">
                                  {noCompatibleSelectedSystem && eligibleSystems.length > 0
                                    ? 'No compatible con los sistemas seleccionados'
                                    : 'Pendiente de certificación histórica'}
                                </span>
                              )}
                            </span>
                          </label>
                        );
                      })}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </CardContent>
      </Card>

      <div className="grid gap-4 xl:grid-cols-12">
        <Card className="xl:col-span-4" data-testid="historical-progress-dashboard">
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2">
              <BarChart3 className="h-5 w-5 text-blue-600" /> Estado de sincronización
            </CardTitle>
            <CardDescription>Progreso general y por módulo/categoría.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <div className="mb-2 flex items-end justify-between">
                <span className="text-sm font-semibold text-zinc-700">Progreso general</span>
                <span className="text-2xl font-bold text-zinc-950">{overallPercent}%</span>
              </div>
              <ProgressBar value={overallPercent} barClass="bg-blue-600" heightClass="h-3" />
              <p className="mt-2 text-xs text-zinc-500">
                {job?.progress?.terminal || 0} de {job?.progress?.total || 0} unidades atómicas terminales
              </p>
            </div>

            <div className="space-y-3 border-t pt-4">
              {selectionProgressRows.length === 0 && (
                <p className="text-sm text-zinc-500">
                  Selecciona tablas para preparar el tablero de avance.
                </p>
              )}
              {selectionProgressRows.map((row, index) => {
                const palette = CATEGORY_PALETTES[index % CATEGORY_PALETTES.length];
                return (
                  <div key={row.key}>
                    <div className="mb-1 flex items-center justify-between gap-3 text-xs">
                      <span className="truncate font-medium text-zinc-700">{row.name}</span>
                      <span className="font-semibold text-zinc-900">{row.percent}%</span>
                    </div>
                    <ProgressBar value={row.percent} barClass={palette.bar} />
                    {job?.parent && (
                      <div className="mt-1 flex justify-between text-[10px] text-zinc-500">
                        <span>{row.success} OK</span>
                        <span>{row.failed} error</span>
                        <span>{row.terminal}/{row.total}</span>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>

            {job?.parent && (
              <div className="flex flex-wrap gap-1 border-t pt-3">
                {Object.entries(job.progress?.by_status || {}).map(([key, count]) => (
                  <Badge key={key} variant="outline" className={statusTone(key)}>
                    {key}: {count}
                  </Badge>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        <Card className="xl:col-span-5" data-testid="historical-error-log">
          <CardHeader className="pb-3">
            <div className="flex items-start justify-between gap-3">
              <div>
                <CardTitle className="flex items-center gap-2">
                  <History className="h-5 w-5 text-blue-600" /> Log de errores del sincronizador
                </CardTitle>
                <CardDescription>Bitácora persistente y auditable en tiempo real.</CardDescription>
              </div>
              {job?.parent && (
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => loadJob(job.parent.SyncControlID)}
                  disabled={actionLoading}
                >
                  <RefreshCw className="mr-1 h-3.5 w-3.5" /> Actualizar
                </Button>
              )}
            </div>
          </CardHeader>
          <CardContent>
            {recentEvents.length === 0 ? (
              <div className="rounded-lg border border-dashed p-6 text-center text-sm text-zinc-500">
                Sin eventos registrados para el trabajo seleccionado.
              </div>
            ) : (
              <div className="overflow-x-auto rounded-lg border">
                <table className="w-full min-w-[720px] text-left text-xs">
                  <thead className="bg-zinc-50 text-zinc-600">
                    <tr>
                      <th className="px-3 py-2 font-semibold">Hora</th>
                      <th className="px-3 py-2 font-semibold">Sucursal</th>
                      <th className="px-3 py-2 font-semibold">Tabla</th>
                      <th className="px-3 py-2 font-semibold">Mensaje</th>
                      <th className="px-3 py-2 font-semibold">Tipo</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y">
                    {recentEvents.map((entry) => (
                      <tr key={entry.id} className="align-top">
                        <td className="whitespace-nowrap px-3 py-2 text-zinc-500">{formatTime(entry.timestamp)}</td>
                        <td className="px-3 py-2 font-medium text-zinc-700">
                          {entry.unit?.unit_name || entry.unit?.branch_name || '-'}
                        </td>
                        <td className="px-3 py-2 text-zinc-600">
                          {entry.capability?.table_name
                            || entry.child?.EntidadCodigo
                            || entry.child?.CodigoSync
                            || '-'}
                        </td>
                        <td className="max-w-[280px] px-3 py-2 text-zinc-700">{entry.message || entry.EventCode}</td>
                        <td className="px-3 py-2">
                          <Badge variant="outline" className={eventTone(entry.displayType)}>
                            {entry.displayType}
                          </Badge>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </CardContent>
        </Card>

        <Card className="xl:col-span-3" data-testid="historical-actions">
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2"><Zap className="h-5 w-5 text-blue-600" /> Acciones</CardTitle>
            <CardDescription>Preflight, ejecución y controles cooperativos.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <Button
              variant="outline"
              className="w-full"
              onClick={handlePreflight}
              disabled={!selectionValid || actionLoading}
            >
              {actionLoading
                ? <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                : <ShieldCheck className="mr-2 h-4 w-4" />}
              Ejecutar preflight
            </Button>

            {preflight && (
              <div className={
                'rounded-lg border p-3 text-xs ' +
                (preflight.ready
                  ? 'border-emerald-200 bg-emerald-50 text-emerald-800'
                  : 'border-red-200 bg-red-50 text-red-800')
              }>
                <div className="flex items-center gap-2 font-semibold">
                  {preflight.ready
                    ? <CheckCircle2 className="h-4 w-4" />
                    : <XCircle className="h-4 w-4" />}
                  {preflight.ready ? 'Plan atómico listo' : 'Plan bloqueado'}
                </div>
                <p className="mt-1">
                  {preflight.total_atomic_units} unidad(es) atómica(s) · límite {preflight.max_atomic_units}
                </p>
              </div>
            )}

            <div className="space-y-2">
              <Label htmlFor="historical-reason">Motivo auditable</Label>
              <Textarea
                id="historical-reason"
                value={reason}
                onChange={(event) => setReason(event.target.value)}
                rows={3}
                placeholder="Motivo de la sincronización histórica..."
              />
              <p className="text-[11px] text-zinc-500">{reason.trim().length}/10 caracteres mínimos</p>
            </div>

            <label className="flex items-center gap-2 text-sm text-zinc-700">
              <Checkbox checked={dryRun} onCheckedChange={(value) => setDryRun(Boolean(value))} />
              Ejecutar como DRY RUN
            </label>

            <Button
              className="w-full"
              onClick={handleCreate}
              disabled={
                !preflight?.ready
                || preflightSignature !== selectionSignature
                || reason.trim().length < 10
                || actionLoading
              }
            >
              <Play className="mr-2 h-4 w-4" /> Iniciar sincronización
            </Button>

            {job?.parent && (
              <>
                <div className="border-t pt-3">
                  <div className="mb-2 flex items-center justify-between gap-2">
                    <span className="text-xs font-medium text-zinc-500">Job #{job.parent.SyncControlID}</span>
                    <Badge variant="outline" className={statusTone(parentStatus)}>{parentStatus || '-'}</Badge>
                  </div>

                  <div className="grid grid-cols-2 gap-2">
                    {ACTIVE_STATUSES.has(String(parentStatus || '').toUpperCase()) && parentStatus !== 'PAUSE_REQUESTED' && (
                      <Button variant="outline" onClick={() => runControl('pause')} disabled={actionLoading}>
                        <Pause className="mr-1 h-4 w-4" /> Pausar
                      </Button>
                    )}
                    {ACTIVE_STATUSES.has(String(parentStatus || '').toUpperCase()) && parentStatus !== 'CANCEL_REQUESTED' && (
                      <Button variant="destructive" onClick={() => runControl('cancel')} disabled={actionLoading}>
                        <CircleStop className="mr-1 h-4 w-4" /> Safe stop
                      </Button>
                    )}
                  </div>

                  {['PAUSED', 'PAUSE_REQUESTED', 'CANCELLED_SAFE', 'ENQUEUE_FAILED'].includes(parentStatus) && (
                    <Button
                      className="mt-2 w-full"
                      onClick={() => runControl('resume', { retry_failed: false })}
                      disabled={actionLoading}
                    >
                      <RotateCcw className="mr-2 h-4 w-4" /> Reanudar
                    </Button>
                  )}

                  {parentStatus === 'PARTIAL_FAILED' && (
                    <Button
                      className="mt-2 w-full"
                      onClick={() => runControl('resume', { retry_failed: true })}
                      disabled={actionLoading}
                    >
                      <RotateCcw className="mr-2 h-4 w-4" /> Reintentar solo fallidos
                    </Button>
                  )}
                </div>
              </>
            )}
          </CardContent>
        </Card>
      </div>

      {job?.parent && (
        <Card data-testid="historical-atomic-detail">
          <CardHeader>
            <div className="flex flex-col justify-between gap-3 md:flex-row md:items-start">
              <div>
                <CardTitle className="flex items-center gap-2">
                  <Layers3 className="h-5 w-5 text-blue-600" /> Detalle de unidades atómicas
                </CardTitle>
                <CardDescription>
                  Job #{job.parent.SyncControlID} · {job.parent.SyncRunID} · {job.parent.Reason}
                </CardDescription>
              </div>
              <div className="flex gap-2">
                <Badge variant="outline">{job.progress?.total || 0} unidades</Badge>
                <Badge variant="outline" className={statusTone(parentStatus)}>{parentStatus || '-'}</Badge>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <div className="max-h-[420px] overflow-auto rounded-lg border">
              <table className="w-full min-w-[980px] text-left text-xs">
                <thead className="sticky top-0 bg-zinc-50 text-zinc-600">
                  <tr>
                    <th className="px-3 py-2 font-semibold">Capability</th>
                    <th className="px-3 py-2 font-semibold">Sucursal</th>
                    <th className="px-3 py-2 font-semibold">Bloque</th>
                    <th className="px-3 py-2 font-semibold">Intento</th>
                    <th className="px-3 py-2 font-semibold">Procesados</th>
                    <th className="px-3 py-2 font-semibold">Insertados</th>
                    <th className="px-3 py-2 font-semibold">Actualizados</th>
                    <th className="px-3 py-2 font-semibold">Errores</th>
                    <th className="px-3 py-2 font-semibold">Estado</th>
                  </tr>
                </thead>
                <tbody className="divide-y">
                  {(job.children || []).map((child) => {
                    const unit = child.UnidadNegocioID
                      ? unitById.get(String(child.UnidadNegocioID).toLowerCase())
                      : null;
                    const capability = capabilityIndex.get(child.CodigoSync);
                    return (
                      <tr key={child.SyncControlID}>
                        <td className="px-3 py-2">
                          <p className="font-semibold text-zinc-800">{capability?.display_name || child.CodigoSync}</p>
                          <p className="text-[10px] text-zinc-500">{capability?.table_name || child.EntidadCodigo || '-'}</p>
                        </td>
                        <td className="px-3 py-2 text-zinc-700">{unit?.unit_name || unit?.unit_code || '-'}</td>
                        <td className="whitespace-nowrap px-3 py-2 text-zinc-600">
                          {String(child.FechaInicio || '').slice(0, 10)} → {String(child.FechaFin || '').slice(0, 10)}
                        </td>
                        <td className="px-3 py-2">{child.AttemptCount || 0}/{child.MaxAttempts || 0}</td>
                        <td className="px-3 py-2">{child.RegistrosProcesados || 0}</td>
                        <td className="px-3 py-2">{child.RegistrosInsertados || 0}</td>
                        <td className="px-3 py-2">{child.RegistrosActualizados || 0}</td>
                        <td className="px-3 py-2">{child.RegistrosError || 0}</td>
                        <td className="px-3 py-2">
                          <Badge variant="outline" className={statusTone(child.Status)}>{child.Status}</Badge>
                          {child.ErrorMessage && (
                            <p className="mt-1 max-w-[240px] text-[10px] text-red-600">{child.ErrorMessage}</p>
                          )}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader>
          <div className="flex items-start justify-between gap-3">
            <div>
              <CardTitle className="flex items-center gap-2"><History className="h-5 w-5" /> Historial de ejecuciones</CardTitle>
              <CardDescription>Persistente, auditable y reconstruible después de recargar la pantalla.</CardDescription>
            </div>
            <Button variant="outline" size="sm" onClick={loadHistory} disabled={historyLoading}>
              <RefreshCw className="mr-1 h-3.5 w-3.5" /> Actualizar
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {historyLoading ? (
            <div className="flex items-center py-6 text-sm text-zinc-500">
              <Loader2 className="mr-2 h-4 w-4 animate-spin" /> Cargando historial...
            </div>
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

      <div className="flex flex-wrap items-center gap-x-4 gap-y-2 text-xs text-zinc-500">
        <span className="flex items-center gap-1">
          <Server className="h-3.5 w-3.5" />
          Sistemas, sucursales y tablas provienen de fuentes canónicas; el frontend no contiene listas funcionales fijas.
        </span>
        <span className="flex items-center gap-1">
          <Clock3 className="h-3.5 w-3.5" />
          Polling controlado solo mientras existe un trabajo activo.
        </span>
      </div>
    </div>
  );
}
