import React, { useEffect, useState, useCallback } from "react";
import { getToken } from "../lib/api";
import {
  LayoutDashboard,
  Database,
  AlertOctagon,
  BookOpen,
  GitBranch,
  FileSearch,
  ScrollText,
  ClipboardCheck,
  RefreshCw,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  HelpCircle,
  ShieldCheck,
  Clock,
  ChevronLeft,
  ChevronRight,
  Search,
  Lock,
} from "lucide-react";

const API = process.env.REACT_APP_BACKEND_URL || "";
const QUEUE_STATES = ["requests", "pending", "processing", "results", "done", "published", "rejected"];
const LIFECYCLE_FILTER_OPTIONS = [
  "",
  "ACTIVE_IN_PREVIEW",
  "CERTIFIED",
  "INTEGRATED",
  "SUBMITTED",
  "BLOCKED",
  "FAILED",
  "REJECTED",
  "INVALID",
];

async function apiGet(path) {
  const token = getToken();
  const res = await fetch(`${API}/api/worker/console${path}`, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
    credentials: "include",
  });
  if (!res.ok) {
    let detailMsg = "";
    try {
      const errJson = await res.json();
      if (typeof errJson?.detail === "string") {
        detailMsg = errJson.detail;
      } else if (errJson?.detail?.mensaje) {
        detailMsg = errJson.detail.mensaje;
      }
    } catch (_) {
      // ignore non-json error body
    }
    const err = new Error(detailMsg || `HTTP ${res.status}`);
    err.status = res.status;
    throw err;
  }
  return res.json();
}

function ErrorBanner({ error }) {
  if (!error) return null;
  const status = error.status;
  let title = "Error al consultar la consola";
  let hint = error.message || "Error inesperado";
  if (status === 401) {
    title = "Sesión expirada o revocada (HTTP 401)";
    hint = error.message || "Tu sesión ya no es válida. Inicia sesión nuevamente para continuar.";
  } else if (status === 403) {
    title = "Acceso restringido por RBAC (HTTP 403)";
    hint = error.message || "Esta consola requiere rol SUPERADMIN o permiso SQL explícito RBAC_ADMIN.";
  } else if (status === 503) {
    title = "SQL Canónico temporalmente no disponible (HTTP 503)";
    hint = error.message || "La consola opera fail-closed cuando EDARSAHUB SQL no responde.";
  }
  return (
    <div
      className="bg-red-950/50 border border-red-800/80 rounded-xl p-4 flex items-start gap-3 text-sm"
      data-testid="wc-error-banner"
    >
      <Lock size={18} className="text-red-400 mt-0.5 shrink-0" />
      <div>
        <div className="font-semibold text-red-300">{title}</div>
        <p className="text-red-200/80 mt-0.5">{hint}</p>
      </div>
    </div>
  );
}

const StageBadge = ({ stage }) => {
  const s = String(stage || "UNKNOWN").toUpperCase();
  const styles = {
    ACTIVE_IN_PREVIEW: ["bg-emerald-600/25 text-emerald-300 border-emerald-600/60", CheckCircle2, "ACTIVO EN PREVIEW"],
    CERTIFIED: ["bg-sky-600/25 text-sky-300 border-sky-600/60", ShieldCheck, "CERTIFICADO (CÓDIGO)"],
    INTEGRATED: ["bg-indigo-600/25 text-indigo-300 border-indigo-600/60", GitBranch, "INTEGRADO"],
    SUBMITTED: ["bg-amber-600/20 text-amber-300 border-amber-600/50", Clock, "ENVIADO"],
    BLOCKED: ["bg-red-600/25 text-red-300 border-red-600/60", XCircle, "BLOQUEADO"],
    FAILED: ["bg-red-600/25 text-red-300 border-red-600/60", XCircle, "FALLIDO"],
    REJECTED: ["bg-rose-600/25 text-rose-300 border-rose-600/60", XCircle, "RECHAZADO"],
    INVALID: ["bg-orange-600/25 text-orange-300 border-orange-600/60", AlertTriangle, "INVÁLIDO"],
  };
  const [cls, Icon, label] = styles[s] || ["bg-zinc-800 text-zinc-400 border-zinc-700", HelpCircle, s];
  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium border ${cls}`}
      data-testid={`stage-badge-${s}`}
    >
      <Icon size={12} /> {label}
    </span>
  );
};

const Verdict = ({ v }) => {
  const map = {
    PASS: ["text-emerald-400", CheckCircle2],
    FAIL: ["text-red-400", XCircle],
    PENDING: ["text-amber-400", Clock],
    NOT_FOUND: ["text-zinc-500", HelpCircle],
    UNKNOWN: ["text-amber-400", AlertTriangle],
  };
  const [cls, Icon] = map[v] || map.UNKNOWN;
  return (
    <span className={`inline-flex items-center gap-1 font-semibold ${cls}`} data-testid={`verdict-${v}`}>
      <Icon size={16} /> {v}
    </span>
  );
};

const TABS = [
  ["dashboard", "Resumen SQL", LayoutDashboard],
  ["jobs", "Trabajos", Database],
  ["incidents", "Incidentes", AlertOctagon],
  ["capabilities", "Capacidades y Lecciones", BookOpen],
  ["lifecycle", "Lifecycle", GitBranch],
  ["result", "Intérprete", FileSearch],
  ["audit", "Auditoría", ScrollText],
  ["tablajerias", "Tablajerías", ClipboardCheck],
];

export default function WorkerConsole() {
  const [tab, setTab] = useState("dashboard");
  const [selectedJobId, setSelectedJobId] = useState("");

  const openLifecycle = (jobId) => {
    setSelectedJobId(jobId);
    setTab("lifecycle");
  };

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100 p-6" data-testid="worker-console-page">
      <header className="mb-6 flex flex-col md:flex-row md:items-center md:justify-between gap-2">
        <div>
          <h1 className="text-2xl font-bold tracking-tight" data-testid="wc-title">
            EDARSAHUB · Universal Worker Console
          </h1>
          <p className="text-sm text-zinc-400">
            SQL Canónico EDARSAHUB (solo lectura · RBAC fail-closed). Separa certificación de código vs validación operativa en Preview · Producción protegida.
          </p>
        </div>
        <div className="inline-flex items-center gap-2 text-xs px-3 py-1.5 rounded-lg bg-zinc-900 border border-zinc-800 text-zinc-300">
          <ShieldCheck size={14} className="text-emerald-400" />
          RBAC Activo · HRLectura Read-Only
        </div>
      </header>

      <nav className="flex flex-wrap gap-2 mb-6 border-b border-zinc-800 pb-3">
        {TABS.map(([id, label, Icon]) => (
          <button
            key={id}
            onClick={() => setTab(id)}
            data-testid={`wc-tab-${id}`}
            className={`inline-flex items-center gap-2 px-3.5 py-2 rounded-lg text-sm transition-colors ${
              tab === id ? "bg-emerald-600 text-white" : "bg-zinc-900 text-zinc-300 hover:bg-zinc-800"
            }`}
          >
            <Icon size={15} /> {label}
          </button>
        ))}
      </nav>

      {tab === "dashboard" && <DashboardTab onSelectStage={() => setTab("jobs")} />}
      {tab === "jobs" && <JobsSqlTab onOpenLifecycle={openLifecycle} />}
      {tab === "incidents" && <IncidentsTab onOpenLifecycle={openLifecycle} />}
      {tab === "capabilities" && <CapabilitiesTab />}
      {tab === "lifecycle" && <LifecycleTab initialJobId={selectedJobId} />}
      {tab === "result" && <ResultTab />}
      {tab === "audit" && <AuditTab />}
      {tab === "tablajerias" && <TablajeriasTab />}
    </div>
  );
}

function Panel({ children, testid }) {
  return (
    <div className="bg-zinc-900/60 border border-zinc-800 rounded-xl p-5" data-testid={testid}>
      {children}
    </div>
  );
}

const Row = ({ k, v, warn }) => (
  <div className="flex justify-between gap-4 border-b border-zinc-800/60 py-1.5 text-sm" data-testid={`wc-row-${k}`}>
    <span className="text-zinc-500 shrink-0">{k}</span>
    <span className={`text-right break-all ${warn ? "text-amber-400 font-semibold" : "text-zinc-200"}`}>
      {v !== undefined && v !== null && v !== "" ? String(v) : "—"}
    </span>
  </div>
);

function KpiCard({ label, value, sub, accent = "text-zinc-100", testid }) {
  return (
    <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-4" data-testid={testid}>
      <div className={`text-3xl font-bold ${accent}`}>{value}</div>
      <div className="text-xs uppercase tracking-wide text-zinc-400 mt-1">{label}</div>
      {sub && <div className="text-xs text-zinc-500 mt-1">{sub}</div>}
    </div>
  );
}

function DashboardTab({ onSelectStage }) {
  const [data, setData] = useState(null);
  const [err, setErr] = useState(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(() => {
    setLoading(true);
    setErr(null);
    apiGet("/dashboard")
      .then((res) => {
        setData(res);
        setLoading(false);
      })
      .catch((e) => {
        setErr(e);
        setLoading(false);
      });
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  if (err) return <ErrorBanner error={err} />;
  if (loading && !data) {
    return (
      <Panel testid="wc-dashboard">
        <p className="text-zinc-400">Cargando estado canónico desde SQL Server EDARSAHUB…</p>
      </Panel>
    );
  }

  const sql = data?.sql_summary || {};
  const jobs = sql.jobs || {};
  const incidents = sql.incidents || {};
  const caps = sql.capabilities || {};
  const rt = data?.runtime || {};

  return (
    <div className="space-y-5" data-testid="wc-dashboard">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="text-xs text-zinc-400">
          Fuente: <span className="text-emerald-400 font-mono">{data?.source || "SQL_CANONICAL"}</span> · Actualizado:{" "}
          <span>{data?.generated_at_utc || "—"}</span>
        </div>
        <button
          onClick={load}
          data-testid="wc-dashboard-refresh"
          className="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg bg-zinc-900 border border-zinc-700 text-xs text-zinc-200 hover:bg-zinc-800"
        >
          <RefreshCw size={13} /> Actualizar
        </button>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3" data-testid="wc-sql-kpis">
        <KpiCard label="Total Trabajos SQL" value={jobs.total ?? 0} sub="dbo.Sys_Worker_Jobs" testid="wc-kpi-total-jobs" />
        <KpiCard
          label="Código Certificado"
          value={jobs.certified ?? 0}
          sub="CERTIFIED (pendiente Preview si aplica)"
          accent="text-sky-400"
          testid="wc-kpi-certified"
        />
        <KpiCard
          label="Activo en Preview"
          value={jobs.active_in_preview ?? 0}
          sub="Validado operativamente en Preview"
          accent="text-emerald-400"
          testid="wc-kpi-active-preview"
        />
        <KpiCard
          label="Incidentes / Capacidades"
          value={`${incidents.total ?? 0} / ${caps.total ?? 0}`}
          sub={`Abiertos: ${incidents.open ?? 0} · Lecciones: ${caps.knowledge_lesson ?? 0}`}
          accent="text-amber-300"
          testid="wc-kpi-incidents-caps"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <Panel testid="wc-stage-breakdown">
          <div className="flex items-center justify-between mb-3">
            <h3 className="font-semibold text-zinc-200">Distribución por Etapa (LifecycleStage)</h3>
            <button onClick={onSelectStage} className="text-xs text-emerald-400 hover:underline">
              Explorar trabajos →
            </button>
          </div>
          <div className="flex flex-wrap gap-2">
            {Object.entries(jobs.by_lifecycle_stage || {}).map(([stage, count]) => (
              <div
                key={stage}
                className="flex items-center gap-2 bg-zinc-950/70 border border-zinc-800 rounded-lg px-3 py-2"
              >
                <StageBadge stage={stage} />
                <span className="font-mono font-bold text-zinc-100">{count}</span>
              </div>
            ))}
          </div>
          <p className="text-xs text-zinc-500 mt-3">
            Regla canónica: <b>CERTIFIED</b> indica código certificado en Desarrollo; <b>ACTIVE_IN_PREVIEW</b> requiere
            evidencia operativa verificada en Preview. Producción tocada:{" "}
            <b className={jobs.production_touched ? "text-red-400" : "text-emerald-400"}>
              {jobs.production_touched ?? 0}
            </b>
            .
          </p>
        </Panel>

        <Panel testid="wc-runtime">
          <h3 className="font-semibold mb-3 text-zinc-200">Runtime del Universal Worker V4</h3>
          <dl className="space-y-0.5">
            <Row k="current_job_id" v={rt.current_job_id} />
            <Row k="generation" v={rt.generation} />
            <Row k="last_cycle_utc" v={rt.last_cycle_utc} />
            <Row k="last_terminal_utc" v={rt.last_terminal_utc} />
            <Row k="preferred_job_orphaned" v={String(Boolean(rt.preferred_job_orphaned))} warn={Boolean(rt.preferred_job_orphaned)} />
          </dl>
        </Panel>
      </div>

      <Panel testid="wc-state-cards">
        <h3 className="font-semibold mb-3 text-zinc-200 text-sm">Artefactos en Cola Local (.git/universal-worker-queue)</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-3">
          {QUEUE_STATES.map((s) => (
            <div key={s} className="bg-zinc-950 border border-zinc-800 rounded-lg p-3" data-testid={`wc-state-${s}`}>
              <div className="text-2xl font-bold">{(data?.states || {})[s] ?? 0}</div>
              <div className="text-xs uppercase tracking-wide text-zinc-500 mt-1">{s}</div>
            </div>
          ))}
        </div>
      </Panel>
    </div>
  );
}

function JobsSqlTab({ onOpenLifecycle }) {
  const [filters, setFilters] = useState({
    q: "",
    source_job_id: "",
    project_id: "",
    bounded_context: "",
    lifecycle_stage: "",
    certification_status: "",
    operational_validation_status: "",
    date_from: "",
    date_to: "",
    has_blockers: "",
  });
  const [offset, setOffset] = useState(0);
  const limit = 25;
  const [data, setData] = useState(null);
  const [err, setErr] = useState(null);
  const [loading, setLoading] = useState(false);
  const [detail, setDetail] = useState(null);
  const [detailErr, setDetailErr] = useState(null);

  const loadJobs = useCallback(
    (nextOffset = offset) => {
      setLoading(true);
      setErr(null);
      const params = new URLSearchParams();
      params.set("limit", String(limit));
      params.set("offset", String(nextOffset));
      Object.entries(filters).forEach(([k, v]) => {
        if (v !== "" && v !== null && v !== undefined) {
          params.set(k, String(v));
        }
      });
      apiGet(`/jobs?${params.toString()}`)
        .then((res) => {
          setData(res);
          setLoading(false);
        })
        .catch((e) => {
          setErr(e);
          setLoading(false);
        });
    },
    [filters, offset]
  );

  useEffect(() => {
    loadJobs(offset);
  }, [offset]); // eslint-disable-line react-hooks/exhaustive-deps

  const applySearch = (e) => {
    e.preventDefault();
    setOffset(0);
    loadJobs(0);
  };

  const inspectJob = (jobId) => {
    setDetailErr(null);
    setDetail({ loading: true, job_id: jobId });
    apiGet(`/job/${encodeURIComponent(jobId)}`)
      .then((res) => setDetail(res))
      .catch((e) => {
        setDetail(null);
        setDetailErr(e);
      });
  };

  const items = data?.items || [];
  const total = data?.total ?? 0;

  return (
    <div className="space-y-4" data-testid="wc-jobs-sql">
      <Panel testid="wc-jobs-filters">
        <form onSubmit={applySearch} className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-3 text-sm">
          <input
            value={filters.q}
            onChange={(e) => setFilters({ ...filters, q: e.target.value })}
            placeholder="Buscar JobID / objetivo / capacidad"
            data-testid="wc-filter-q"
            className="bg-zinc-950 border border-zinc-700 rounded-lg px-3 py-2 outline-none focus:border-emerald-500"
          />
          <input
            value={filters.source_job_id}
            onChange={(e) => setFilters({ ...filters, source_job_id: e.target.value })}
            placeholder="source_job_id"
            data-testid="wc-filter-source-job"
            className="bg-zinc-950 border border-zinc-700 rounded-lg px-3 py-2 outline-none focus:border-emerald-500"
          />
          <input
            value={filters.bounded_context}
            onChange={(e) => setFilters({ ...filters, bounded_context: e.target.value })}
            placeholder="Dominio (BoundedContext)"
            data-testid="wc-filter-domain"
            className="bg-zinc-950 border border-zinc-700 rounded-lg px-3 py-2 outline-none focus:border-emerald-500"
          />
          <select
            value={filters.lifecycle_stage}
            onChange={(e) => setFilters({ ...filters, lifecycle_stage: e.target.value })}
            data-testid="wc-filter-stage"
            className="bg-zinc-950 border border-zinc-700 rounded-lg px-3 py-2 outline-none focus:border-emerald-500"
          >
            {LIFECYCLE_FILTER_OPTIONS.map((opt) => (
              <option key={opt || "ALL"} value={opt}>
                {opt ? `Etapa: ${opt}` : "Todas las etapas"}
              </option>
            ))}
          </select>
          <select
            value={filters.operational_validation_status}
            onChange={(e) => setFilters({ ...filters, operational_validation_status: e.target.value })}
            data-testid="wc-filter-preview"
            className="bg-zinc-950 border border-zinc-700 rounded-lg px-3 py-2 outline-none focus:border-emerald-500"
          >
            <option value="">Preview: Todos</option>
            <option value="VALIDATED_IN_PREVIEW">VALIDATED_IN_PREVIEW</option>
            <option value="PENDING_PREVIEW_VALIDATION">PENDING_PREVIEW_VALIDATION</option>
            <option value="NOT_APPLICABLE">NOT_APPLICABLE</option>
          </select>

          <input
            value={filters.project_id}
            onChange={(e) => setFilters({ ...filters, project_id: e.target.value })}
            placeholder="Proyecto (ProjectID)"
            data-testid="wc-filter-project"
            className="bg-zinc-950 border border-zinc-700 rounded-lg px-3 py-2 outline-none focus:border-emerald-500"
          />
          <input
            type="date"
            value={filters.date_from}
            onChange={(e) => setFilters({ ...filters, date_from: e.target.value })}
            data-testid="wc-filter-date-from"
            className="bg-zinc-950 border border-zinc-700 rounded-lg px-3 py-2 outline-none focus:border-emerald-500"
          />
          <input
            type="date"
            value={filters.date_to}
            onChange={(e) => setFilters({ ...filters, date_to: e.target.value })}
            data-testid="wc-filter-date-to"
            className="bg-zinc-950 border border-zinc-700 rounded-lg px-3 py-2 outline-none focus:border-emerald-500"
          />
          <select
            value={filters.has_blockers}
            onChange={(e) => setFilters({ ...filters, has_blockers: e.target.value })}
            data-testid="wc-filter-blockers"
            className="bg-zinc-950 border border-zinc-700 rounded-lg px-3 py-2 outline-none focus:border-emerald-500"
          >
            <option value="">Bloqueos: Todos</option>
            <option value="true">Solo con bloqueos</option>
            <option value="false">Sin bloqueos</option>
          </select>
          <button
            type="submit"
            data-testid="wc-filter-submit"
            className="inline-flex items-center justify-center gap-2 px-4 py-2 bg-emerald-600 hover:bg-emerald-500 rounded-lg font-medium text-white"
          >
            <Search size={15} /> Filtrar SQL
          </button>
        </form>
      </Panel>

      {err && <ErrorBanner error={err} />}

      <Panel testid="wc-jobs-table-panel">
        <div className="flex flex-wrap items-center justify-between gap-2 mb-3 text-xs text-zinc-400">
          <span>
            Mostrando <b>{items.length}</b> de <b>{total}</b> trabajos en <span className="font-mono">dbo.Sys_Worker_Jobs</span>
          </span>
          <div className="flex items-center gap-2">
            <button
              disabled={offset === 0 || loading}
              onClick={() => setOffset(Math.max(0, offset - limit))}
              data-testid="wc-jobs-prev"
              className="inline-flex items-center gap-1 px-2.5 py-1 rounded bg-zinc-800 disabled:opacity-40"
            >
              <ChevronLeft size={14} /> Anterior
            </button>
            <span>
              Página {Math.floor(offset / limit) + 1} / {Math.max(1, Math.ceil(total / limit))}
            </span>
            <button
              disabled={offset + limit >= total || loading}
              onClick={() => setOffset(offset + limit)}
              data-testid="wc-jobs-next"
              className="inline-flex items-center gap-1 px-2.5 py-1 rounded bg-zinc-800 disabled:opacity-40"
            >
              Siguiente <ChevronRight size={14} />
            </button>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-xs md:text-sm" data-testid="wc-jobs-table">
            <thead>
              <tr className="text-zinc-500 text-left border-b border-zinc-800">
                <th className="py-2 pr-3">Job ID</th>
                <th className="py-2 pr-3">Dominio / Proyecto</th>
                <th className="py-2 pr-3">Etapa</th>
                <th className="py-2 pr-3">Certificación</th>
                <th className="py-2 pr-3">Preview</th>
                <th className="py-2 pr-3">Bloqueos</th>
                <th className="py-2 pr-3">SHA</th>
                <th className="py-2">Acción</th>
              </tr>
            </thead>
            <tbody>
              {items.map((job) => (
                <tr
                  key={job.job_id}
                  className="border-b border-zinc-800/60 hover:bg-zinc-800/40"
                  data-testid={`wc-job-row-${job.job_id}`}
                >
                  <td className="py-2 pr-3 font-mono text-xs text-zinc-200 max-w-xs truncate" title={job.job_id}>
                    {job.job_id}
                  </td>
                  <td className="py-2 pr-3 text-zinc-400">
                    <div>{job.bounded_context || "UNSPECIFIED"}</div>
                    <div className="text-xs text-zinc-500">{job.project_id || "—"}</div>
                  </td>
                  <td className="py-2 pr-3">
                    <StageBadge stage={job.lifecycle_stage} />
                  </td>
                  <td className="py-2 pr-3 text-xs text-zinc-300">{job.certification_status || "—"}</td>
                  <td className="py-2 pr-3 text-xs">
                    {job.operational_validated ? (
                      <span className="text-emerald-400 font-medium">VALIDADO</span>
                    ) : (
                      <span className="text-zinc-400">{job.operational_validation_status || "PENDIENTE"}</span>
                    )}
                  </td>
                  <td className="py-2 pr-3">
                    {job.blocker_count > 0 ? (
                      <span className="text-red-400 font-semibold">{job.blocker_count}</span>
                    ) : (
                      <span className="text-zinc-500">0</span>
                    )}
                  </td>
                  <td className="py-2 pr-3 font-mono text-xs text-zinc-400">
                    {job.development_commit_sha ? job.development_commit_sha.slice(0, 10) : "—"}
                  </td>
                  <td className="py-2 flex gap-2">
                    <button
                      onClick={() => inspectJob(job.job_id)}
                      className="px-2 py-1 rounded bg-zinc-800 hover:bg-zinc-700 text-xs text-zinc-200"
                    >
                      Detalle
                    </button>
                    <button
                      onClick={() => onOpenLifecycle(job.job_id)}
                      className="px-2 py-1 rounded bg-emerald-700/40 hover:bg-emerald-700/60 text-xs text-emerald-300"
                    >
                      Traza
                    </button>
                  </td>
                </tr>
              ))}
              {!loading && items.length === 0 && (
                <tr>
                  <td colSpan={8} className="py-6 text-center text-zinc-500">
                    No se encontraron trabajos con los filtros seleccionados.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </Panel>

      {detailErr && <ErrorBanner error={detailErr} />}
      {detail && (
        <Panel testid="wc-job-detail-panel">
          {detail.loading ? (
            <p className="text-zinc-400 text-sm">Cargando evidencia del trabajo {detail.job_id}…</p>
          ) : (
            <div className="space-y-4">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <div>
                  <h3 className="font-mono font-semibold text-emerald-400 text-sm">{detail.job_id}</h3>
                  <p className="text-xs text-zinc-400 mt-0.5">{detail.sql_job?.objective || "Sin objetivo registrado"}</p>
                </div>
                {detail.sql_job && <StageBadge stage={detail.sql_job.lifecycle_stage} />}
              </div>

              {detail.sql_job && (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-x-8">
                  <Row k="certification_status" v={detail.sql_job.certification_status} />
                  <Row k="operational_validation_status" v={detail.sql_job.operational_validation_status} />
                  <Row k="quality_gate / tests" v={`${detail.sql_job.quality_gate} / ${detail.sql_job.tests_status}`} />
                  <Row k="reconciliation_status" v={detail.sql_job.reconciliation_status} />
                  <Row k="development_commit_sha" v={detail.sql_job.development_commit_sha} />
                  <Row k="published_result_commit_sha" v={detail.sql_job.published_result_commit_sha} />
                  <Row k="result_sha256" v={detail.sql_job.result_sha256} />
                  <Row k="production_touched" v={String(detail.sql_job.production_touched)} warn={detail.sql_job.production_touched} />
                </div>
              )}

              {detail.sql_job?.blockers?.length > 0 && (
                <div className="bg-red-950/40 border border-red-800/60 rounded-lg p-3">
                  <div className="text-xs font-semibold text-red-300 mb-1">Bloqueos concretos</div>
                  <ul className="list-disc list-inside text-xs text-red-200 space-y-1">
                    {detail.sql_job.blockers.map((b, idx) => (
                      <li key={idx}>{b}</li>
                    ))}
                  </ul>
                </div>
              )}

              {detail.sql_job?.evidence_breakdown && (
                <div>
                  <div className="text-xs font-semibold text-zinc-400 mb-2">Desglose de Evidencia (7 ejes canónicos)</div>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-xs">
                    {Object.entries(detail.sql_job.evidence_breakdown).map(([axis, val]) => (
                      <div key={axis} className="bg-zinc-950 border border-zinc-800 rounded p-2">
                        <div className="text-zinc-500">{axis}</div>
                        <div className="font-mono text-zinc-200 mt-0.5">{String(val)}</div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </Panel>
      )}
    </div>
  );
}

function IncidentsTab({ onOpenLifecycle }) {
  const [severity, setSeverity] = useState("");
  const [stateFilter, setStateFilter] = useState("");
  const [q, setQ] = useState("");
  const [data, setData] = useState(null);
  const [err, setErr] = useState(null);

  const load = useCallback(() => {
    setErr(null);
    const params = new URLSearchParams({ limit: "50", offset: "0" });
    if (severity) params.set("severity", severity);
    if (stateFilter) params.set("incident_state", stateFilter);
    if (q.trim()) params.set("q", q.trim());
    apiGet(`/incidents?${params.toString()}`)
      .then(setData)
      .catch(setErr);
  }, [severity, stateFilter, q]);

  useEffect(() => {
    load();
  }, [load]);

  return (
    <div className="space-y-4" data-testid="wc-incidents">
      <Panel testid="wc-incidents-filters">
        <div className="flex flex-wrap gap-3 text-sm">
          <input
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="Buscar incidente, firma o job_id"
            className="flex-1 min-w-[200px] bg-zinc-950 border border-zinc-700 rounded-lg px-3 py-2 outline-none focus:border-emerald-500"
          />
          <select
            value={severity}
            onChange={(e) => setSeverity(e.target.value)}
            className="bg-zinc-950 border border-zinc-700 rounded-lg px-3 py-2"
          >
            <option value="">Todas las severidades</option>
            <option value="CRITICAL">CRITICAL</option>
            <option value="HIGH">HIGH</option>
            <option value="MEDIUM">MEDIUM</option>
            <option value="LOW">LOW</option>
          </select>
          <select
            value={stateFilter}
            onChange={(e) => setStateFilter(e.target.value)}
            className="bg-zinc-950 border border-zinc-700 rounded-lg px-3 py-2"
          >
            <option value="">Todos los estados</option>
            <option value="OPEN">OPEN</option>
            <option value="MITIGATED">MITIGATED</option>
            <option value="RESOLVED">RESOLVED</option>
            <option value="ESCALATED">ESCALATED</option>
          </select>
          <button onClick={load} className="px-4 py-2 bg-emerald-600 rounded-lg font-medium">
            Buscar
          </button>
        </div>
      </Panel>

      {err && <ErrorBanner error={err} />}

      <Panel testid="wc-incidents-list">
        <div className="text-xs text-zinc-400 mb-3">
          Total incidentes en <span className="font-mono">dbo.Sys_Worker_Incidents</span>: <b>{data?.total ?? 0}</b>
        </div>
        <div className="space-y-3">
          {(data?.items || []).map((inc) => (
            <div key={inc.incident_id} className="bg-zinc-950 border border-zinc-800 rounded-lg p-3.5 text-xs space-y-1.5">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <span className="font-mono font-semibold text-amber-300">{inc.incident_id}</span>
                <div className="flex items-center gap-2">
                  <span className="px-2 py-0.5 rounded bg-zinc-800 text-zinc-300">{inc.severity || "—"}</span>
                  <span className="px-2 py-0.5 rounded bg-zinc-800 text-emerald-300">{inc.incident_state || "—"}</span>
                </div>
              </div>
              <div className="text-zinc-300">
                <b>Causa raíz:</b> {inc.root_cause || inc.problem_signature || "—"}
              </div>
              <div className="text-zinc-400">
                <b>Acción recomendada:</b> {inc.recommended_action || "—"}
              </div>
              <div className="flex flex-wrap gap-3 text-zinc-500 pt-1">
                {inc.source_job_id && (
                  <button
                    onClick={() => onOpenLifecycle(inc.source_job_id)}
                    className="text-emerald-400 hover:underline font-mono"
                  >
                    Origen: {inc.source_job_id}
                  </button>
                )}
                {inc.repair_job_id && (
                  <button
                    onClick={() => onOpenLifecycle(inc.repair_job_id)}
                    className="text-sky-400 hover:underline font-mono"
                  >
                    Reparación: {inc.repair_job_id}
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      </Panel>
    </div>
  );
}

function CapabilitiesTab() {
  const [kind, setKind] = useState("");
  const [q, setQ] = useState("");
  const [data, setData] = useState(null);
  const [err, setErr] = useState(null);

  const load = useCallback(() => {
    setErr(null);
    const params = new URLSearchParams({ limit: "100", offset: "0" });
    if (kind) params.set("capability_kind", kind);
    if (q.trim()) params.set("q", q.trim());
    apiGet(`/capabilities?${params.toString()}`)
      .then(setData)
      .catch(setErr);
  }, [kind, q]);

  useEffect(() => {
    load();
  }, [load]);

  return (
    <div className="space-y-4" data-testid="wc-capabilities">
      <Panel testid="wc-capabilities-filters">
        <div className="flex flex-wrap gap-3 text-sm">
          <input
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="Buscar capacidad, causa o regla de prevención"
            className="flex-1 min-w-[200px] bg-zinc-950 border border-zinc-700 rounded-lg px-3 py-2 outline-none focus:border-emerald-500"
          />
          <select
            value={kind}
            onChange={(e) => setKind(e.target.value)}
            className="bg-zinc-950 border border-zinc-700 rounded-lg px-3 py-2"
          >
            <option value="">Todos los tipos</option>
            <option value="LEARNED_REPAIR">LEARNED_REPAIR</option>
            <option value="KNOWLEDGE_LESSON">KNOWLEDGE_LESSON</option>
          </select>
          <button onClick={load} className="px-4 py-2 bg-emerald-600 rounded-lg font-medium">
            Filtrar
          </button>
        </div>
      </Panel>

      {err && <ErrorBanner error={err} />}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {(data?.items || []).map((cap) => (
          <Panel key={cap.capability_code} testid={`wc-cap-${cap.capability_code}`}>
            <div className="flex items-start justify-between gap-2 mb-2">
              <div className="font-mono text-sm font-semibold text-emerald-400 break-all">{cap.capability_code}</div>
              <span className="px-2 py-0.5 rounded bg-zinc-800 text-xs text-sky-300 shrink-0">{cap.capability_kind}</span>
            </div>
            <Row k="certification" v={cap.certification_status} />
            <Row k="preview_status" v={cap.operational_validation_status} />
            <Row k="problem_signature" v={cap.problem_signature} />
            <Row k="root_cause" v={cap.root_cause} />
            <Row k="prevention_rule" v={cap.prevention_rule} />
            <Row k="certified_commit_sha" v={cap.certified_commit_sha} />
          </Panel>
        ))}
      </div>
    </div>
  );
}

function LifecycleTab({ initialJobId = "" }) {
  const [jid, setJid] = useState(initialJobId);
  const [data, setData] = useState(null);
  const [err, setErr] = useState(null);

  const search = useCallback(
    (targetId) => {
      const value = String(targetId !== undefined ? targetId : jid).trim();
      if (!value) return;
      setErr(null);
      setData(null);
      apiGet(`/lifecycle/${encodeURIComponent(value)}`)
        .then(setData)
        .catch(setErr);
    },
    [jid]
  );

  useEffect(() => {
    if (initialJobId) {
      setJid(initialJobId);
      search(initialJobId);
    }
  }, [initialJobId]); // eslint-disable-line react-hooks/exhaustive-deps

  const presenceEntries = Array.isArray(data?.presence_list)
    ? data.presence_list
    : Object.entries(data?.presence || {}).map(([state, present]) => ({ state, present: Boolean(present) }));

  const interp = data?.interpretation || data?.result || null;

  return (
    <div className="space-y-4">
      <div className="flex gap-2">
        <input
          value={jid}
          onChange={(e) => setJid(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && search()}
          placeholder="job_id (ej. EDARSAHUB-BOS-...)"
          data-testid="wc-lifecycle-input"
          className="flex-1 bg-zinc-900 border border-zinc-700 rounded-lg px-4 py-2 text-sm outline-none focus:border-emerald-500"
        />
        <button onClick={() => search()} data-testid="wc-lifecycle-search" className="px-5 py-2 bg-emerald-600 rounded-lg text-sm font-medium">
          Buscar
        </button>
      </div>
      {err && <ErrorBanner error={err} />}
      {data && (
        <Panel testid="wc-lifecycle-result">
          <div className="flex flex-wrap gap-2 mb-4">
            {presenceEntries.map((p) => (
              <span
                key={p.state}
                data-testid={`wc-presence-${p.state}`}
                className={`px-3 py-1 rounded-full text-xs ${
                  p.present
                    ? "bg-emerald-600/30 text-emerald-300 border border-emerald-700"
                    : "bg-zinc-800 text-zinc-500"
                }`}
              >
                {p.state}
                {p.present ? " ✓" : ""}
              </span>
            ))}
          </div>
          {data.sql_job && (
            <div className="mb-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-semibold text-zinc-400">Estado Canónico SQL</span>
                <StageBadge stage={data.sql_job.lifecycle_stage} />
              </div>
              <Row k="certification_status" v={data.sql_job.certification_status} />
              <Row k="operational_validation_status" v={data.sql_job.operational_validation_status} />
              <Row k="reconciliation_status" v={data.sql_job.reconciliation_status} />
              <Row k="development_commit_sha" v={data.sql_job.development_commit_sha} />
            </div>
          )}
          {interp && (
            <div className="mb-4 text-sm space-y-1">
              <div className="flex items-center gap-3">
                <span>Veredicto:</span> <Verdict v={interp.verdict} />
                {interp.lifecycle_stage && <StageBadge stage={interp.lifecycle_stage} />}
              </div>
              <Row k="certification" v={interp.certification} />
              <Row k="quality_gate" v={interp.quality_gate} />
              <Row k="production_touched" v={String(interp.production_touched)} warn={Boolean(interp.production_touched)} />
              <Row k="blockers" v={(interp.blockers || []).join(", ") || "—"} />
            </div>
          )}
          <pre className="bg-zinc-950 rounded-lg p-3 text-xs overflow-auto max-h-80 text-zinc-400" data-testid="wc-lifecycle-json">
            {JSON.stringify(data.job || data.sql_job || {}, null, 2)}
          </pre>
        </Panel>
      )}
    </div>
  );
}

function ResultTab() {
  const [jid, setJid] = useState("");
  const [data, setData] = useState(null);
  const [err, setErr] = useState(null);
  const search = () => {
    if (!jid.trim()) return;
    setErr(null);
    setData(null);
    apiGet(`/result/${encodeURIComponent(jid.trim())}`)
      .then(setData)
      .catch(setErr);
  };
  return (
    <div className="space-y-4">
      <div className="flex gap-2">
        <input
          value={jid}
          onChange={(e) => setJid(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && search()}
          placeholder="job_id para interpretar su resultado canónico"
          data-testid="wc-result-input"
          className="flex-1 bg-zinc-900 border border-zinc-700 rounded-lg px-4 py-2 text-sm outline-none focus:border-emerald-500"
        />
        <button onClick={search} data-testid="wc-result-search" className="px-5 py-2 bg-emerald-600 rounded-lg text-sm font-medium">
          Interpretar
        </button>
      </div>
      {err && <ErrorBanner error={err} />}
      {data && (
        <Panel testid="wc-result-panel">
          <div className="text-sm mb-3">
            Encontrado en: <span className="text-emerald-400 font-mono">{data.found_in || "—"}</span>
          </div>
          {data.interpretation ? (
            <div className="text-sm space-y-1">
              <div className="flex items-center gap-3 mb-2">
                <span>Veredicto:</span> <Verdict v={data.interpretation.verdict} />
                {data.interpretation.lifecycle_stage && <StageBadge stage={data.interpretation.lifecycle_stage} />}
              </div>
              <Row k="certification" v={data.interpretation.certification} />
              <Row k="quality_gate" v={data.interpretation.quality_gate} />
              <Row k="operational_validation_status" v={data.interpretation.operational_validation_status} />
              <Row k="production_touched" v={String(data.interpretation.production_touched)} warn={Boolean(data.interpretation.production_touched)} />
              <Row k="files_changed_count" v={data.interpretation.files_changed_count} />
              <Row k="blockers" v={(data.interpretation.blockers || []).join(", ") || "—"} />
            </div>
          ) : (
            <p className="text-zinc-500 text-sm">Sin resultado interpretable.</p>
          )}
        </Panel>
      )}
    </div>
  );
}

function TablajeriasTab() {
  const [data, setData] = useState(null);
  const [err, setErr] = useState(null);
  useEffect(() => {
    apiGet("/tablajerias/checklist").then(setData).catch(setErr);
  }, []);
  if (err) return <ErrorBanner error={err} />;
  if (!data) {
    return (
      <Panel testid="wc-tablajerias">
        <p className="text-zinc-400">Cargando…</p>
      </Panel>
    );
  }
  const go = data.technical_status === "GO técnico READ_ONLY";
  return (
    <div className="space-y-4">
      <Panel testid="wc-tablajerias-status">
        <div className={`text-lg font-bold ${go ? "text-emerald-400" : "text-amber-400"}`} data-testid="wc-tablajerias-verdict">
          {data.technical_status}
        </div>
        <p className="text-sm text-zinc-400 mt-1">
          production_touched: <b className="text-zinc-200">{String(data.production_touched)}</b>
        </p>
        <p className="text-sm text-amber-300 mt-2" data-testid="wc-tablajerias-next">
          ⚠ Siguiente decisión: {data.next_decision}
        </p>
        <p className="text-xs text-zinc-500 mt-1">{data.note}</p>
      </Panel>
      <Panel testid="wc-tablajerias-checklist">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-zinc-500 text-left">
              <th className="pb-2">Check</th>
              <th>Veredicto</th>
              <th>prod_touched</th>
              <th>job_id</th>
            </tr>
          </thead>
          <tbody>
            {(data.items || []).map((it, i) => (
              <tr key={i} className="border-t border-zinc-800/60" data-testid={`wc-check-row-${i}`}>
                <td className="py-2">{it.check}</td>
                <td>
                  <Verdict v={it.verdict} />
                </td>
                <td className="text-zinc-400">{String(it.production_touched)}</td>
                <td className="text-zinc-500 text-xs font-mono truncate max-w-xs">{it.job_id || "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </Panel>
    </div>
  );
}

function AuditTab() {
  const [data, setData] = useState(null);
  const [err, setErr] = useState(null);
  const load = useCallback(() => {
    setErr(null);
    apiGet("/audit?tail=120").then(setData).catch(setErr);
  }, []);
  useEffect(() => {
    load();
  }, [load]);

  if (err) return <ErrorBanner error={err} />;
  if (!data) {
    return (
      <Panel testid="wc-audit">
        <p className="text-zinc-400">Cargando evidencia de auditoría…</p>
      </Panel>
    );
  }
  const logs = data.logs || {
    "universal-worker-cert.log": data.cert_log || [],
    "universal-worker-launch.log": data.launch_log || [],
    "control_plane_status.json": data.control_plane_status,
    "reconciler.json": data.reconciler,
  };
  return (
    <div className="space-y-4" data-testid="wc-audit">
      <div className="flex items-center justify-between">
        <p className="text-xs text-zinc-500">Evidencia de runtime y proyección SQL (solo lectura, RBAC activo).</p>
        <button
          onClick={load}
          className="inline-flex items-center gap-1.5 px-3 py-1 rounded bg-zinc-900 border border-zinc-700 text-xs text-zinc-200"
        >
          <RefreshCw size={12} /> Refrescar
        </button>
      </div>
      {Object.keys(logs).map((name) => (
        <Panel key={name} testid={`wc-audit-${name}`}>
          <h3 className="font-mono text-xs text-emerald-400 mb-2">{name}</h3>
          <pre className="bg-zinc-950 rounded-lg p-3 text-xs overflow-auto max-h-64 text-zinc-400">
            {Array.isArray(logs[name]) ? (logs[name] || []).join("\n") || "(vacío)" : JSON.stringify(logs[name], null, 2)}
          </pre>
        </Panel>
      ))}
    </div>
  );
}
