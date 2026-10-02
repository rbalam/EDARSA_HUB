import React, { useEffect, useState, useCallback } from "react";
import { getToken } from "../lib/api";
import {
  LayoutDashboard, GitBranch, FileSearch, ScrollText, ClipboardCheck,
  RefreshCw, CheckCircle2, XCircle, AlertTriangle, HelpCircle,
} from "lucide-react";

const API = process.env.REACT_APP_BACKEND_URL || "";
const STATES = ["requests", "pending", "processing", "results", "done", "published", "rejected"];

async function apiGet(path) {
  const token = getToken();
  const res = await fetch(`${API}/api/worker/console${path}`, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
    credentials: "include",
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

const Verdict = ({ v }) => {
  const map = {
    PASS: ["text-emerald-400", CheckCircle2],
    FAIL: ["text-red-400", XCircle],
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
  ["dashboard", "Dashboard", LayoutDashboard],
  ["lifecycle", "Lifecycle", GitBranch],
  ["result", "Intérprete", FileSearch],
  ["tablajerias", "Tablajerías", ClipboardCheck],
  ["audit", "Auditoría", ScrollText],
];

export default function WorkerConsole() {
  const [tab, setTab] = useState("dashboard");
  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100 p-6" data-testid="worker-console-page">
      <header className="mb-6">
        <h1 className="text-2xl font-bold tracking-tight" data-testid="wc-title">
          EDARSAHUB · Universal Worker Console
        </h1>
        <p className="text-sm text-zinc-400">Consola de operación — Fase 1 (solo lectura). No toca Producción · No ejecuta SQL · No muta.</p>
      </header>

      <nav className="flex flex-wrap gap-2 mb-6 border-b border-zinc-800 pb-3">
        {TABS.map(([id, label, Icon]) => (
          <button
            key={id}
            onClick={() => setTab(id)}
            data-testid={`wc-tab-${id}`}
            className={`inline-flex items-center gap-2 px-4 py-2 rounded-lg text-sm transition-colors ${
              tab === id ? "bg-emerald-600 text-white" : "bg-zinc-900 text-zinc-300 hover:bg-zinc-800"
            }`}
          >
            <Icon size={16} /> {label}
          </button>
        ))}
      </nav>

      {tab === "dashboard" && <DashboardTab />}
      {tab === "lifecycle" && <LifecycleTab />}
      {tab === "result" && <ResultTab />}
      {tab === "tablajerias" && <TablajeriasTab />}
      {tab === "audit" && <AuditTab />}
    </div>
  );
}

function Panel({ children, testid }) {
  return <div className="bg-zinc-900/60 border border-zinc-800 rounded-xl p-5" data-testid={testid}>{children}</div>;
}

function DashboardTab() {
  const [data, setData] = useState(null);
  const [err, setErr] = useState(null);
  const load = useCallback(() => {
    apiGet("/dashboard").then(setData).catch((e) => setErr(e.message));
  }, []);
  useEffect(() => { load(); }, [load]);
  if (err) return <Panel testid="wc-dashboard"><p className="text-red-400">Error: {err}</p></Panel>;
  if (!data) return <Panel testid="wc-dashboard"><p className="text-zinc-400">Cargando…</p></Panel>;
  const rt = data.runtime || {};
  return (
    <div className="space-y-5">
      <div className="flex justify-end">
        <button onClick={load} data-testid="wc-dashboard-refresh" className="inline-flex items-center gap-2 text-sm text-zinc-300 hover:text-white">
          <RefreshCw size={14} /> Actualizar
        </button>
      </div>
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-3" data-testid="wc-state-cards">
        {STATES.map((s) => (
          <div key={s} className="bg-zinc-900 border border-zinc-800 rounded-lg p-4" data-testid={`wc-state-${s}`}>
            <div className="text-3xl font-bold">{(data.states || {})[s] ?? 0}</div>
            <div className="text-xs uppercase tracking-wide text-zinc-500 mt-1">{s}</div>
          </div>
        ))}
      </div>
      <Panel testid="wc-runtime">
        <h3 className="font-semibold mb-3 text-zinc-200">Runtime del Worker</h3>
        <dl className="grid grid-cols-1 md:grid-cols-2 gap-x-8 gap-y-2 text-sm">
          <Row k="current_job_id" v={rt.current_job_id} />
          <Row k="generation" v={rt.generation} />
          <Row k="last_cycle_utc" v={rt.last_cycle_utc} />
          <Row k="preferred_job_orphaned" v={String(rt.preferred_job_orphaned)} warn={rt.preferred_job_orphaned} />
        </dl>
      </Panel>
    </div>
  );
}

const Row = ({ k, v, warn }) => (
  <div className="flex justify-between border-b border-zinc-800/60 py-1" data-testid={`wc-row-${k}`}>
    <span className="text-zinc-500">{k}</span>
    <span className={warn ? "text-amber-400 font-semibold" : "text-zinc-200"}>{v ?? "—"}</span>
  </div>
);

function LifecycleTab() {
  const [jid, setJid] = useState("");
  const [data, setData] = useState(null);
  const [err, setErr] = useState(null);
  const search = () => {
    if (!jid.trim()) return;
    setErr(null); setData(null);
    apiGet(`/lifecycle/${encodeURIComponent(jid.trim())}`).then(setData).catch((e) => setErr(e.message));
  };
  return (
    <div className="space-y-4">
      <div className="flex gap-2">
        <input
          value={jid} onChange={(e) => setJid(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && search()}
          placeholder="job_id (ej. EDARSAHUB-...-R1B-...)"
          data-testid="wc-lifecycle-input"
          className="flex-1 bg-zinc-900 border border-zinc-700 rounded-lg px-4 py-2 text-sm outline-none focus:border-emerald-500"
        />
        <button onClick={search} data-testid="wc-lifecycle-search" className="px-5 py-2 bg-emerald-600 rounded-lg text-sm font-medium">Buscar</button>
      </div>
      {err && <p className="text-red-400 text-sm">Error: {err}</p>}
      {data && (
        <Panel testid="wc-lifecycle-result">
          <div className="flex flex-wrap gap-2 mb-4">
            {(data.presence || []).map((p) => (
              <span key={p.state} data-testid={`wc-presence-${p.state}`}
                className={`px-3 py-1 rounded-full text-xs ${p.present ? "bg-emerald-600/30 text-emerald-300 border border-emerald-700" : "bg-zinc-800 text-zinc-500"}`}>
                {p.state}{p.present ? " ✓" : ""}
              </span>
            ))}
          </div>
          {data.interpretation && (
            <div className="mb-4 text-sm space-y-1">
              <div>Veredicto: <Verdict v={data.interpretation.verdict} /></div>
              <Row k="certification" v={data.interpretation.certification} />
              <Row k="quality_gate" v={data.interpretation.quality_gate} />
              <Row k="production_touched" v={String(data.interpretation.production_touched)} warn={data.interpretation.production_touched} />
              <Row k="blockers" v={(data.interpretation.blockers || []).join(", ") || "—"} />
            </div>
          )}
          <pre className="bg-zinc-950 rounded-lg p-3 text-xs overflow-auto max-h-80 text-zinc-400" data-testid="wc-lifecycle-json">
            {JSON.stringify(data.job || {}, null, 2)}
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
    setErr(null); setData(null);
    apiGet(`/result/${encodeURIComponent(jid.trim())}`).then(setData).catch((e) => setErr(e.message));
  };
  return (
    <div className="space-y-4">
      <div className="flex gap-2">
        <input value={jid} onChange={(e) => setJid(e.target.value)} onKeyDown={(e) => e.key === "Enter" && search()}
          placeholder="job_id para interpretar su result" data-testid="wc-result-input"
          className="flex-1 bg-zinc-900 border border-zinc-700 rounded-lg px-4 py-2 text-sm outline-none focus:border-emerald-500" />
        <button onClick={search} data-testid="wc-result-search" className="px-5 py-2 bg-emerald-600 rounded-lg text-sm font-medium">Interpretar</button>
      </div>
      {err && <p className="text-red-400 text-sm">Error: {err}</p>}
      {data && (
        <Panel testid="wc-result-panel">
          <div className="text-sm mb-2">Encontrado en: <span className="text-emerald-400">{data.found_in || "—"}</span></div>
          {data.interpretation ? (
            <div className="text-sm space-y-1">
              <div>Veredicto: <Verdict v={data.interpretation.verdict} /></div>
              <Row k="certification" v={data.interpretation.certification} />
              <Row k="quality_gate" v={data.interpretation.quality_gate} />
              <Row k="production_touched" v={String(data.interpretation.production_touched)} warn={data.interpretation.production_touched} />
              <Row k="files_changed" v={data.interpretation.files_changed} />
              <Row k="blockers" v={(data.interpretation.blockers || []).join(", ") || "—"} />
            </div>
          ) : <p className="text-zinc-500 text-sm">Sin result interpretable.</p>}
        </Panel>
      )}
    </div>
  );
}

function TablajeriasTab() {
  const [data, setData] = useState(null);
  const [err, setErr] = useState(null);
  useEffect(() => { apiGet("/tablajerias/checklist").then(setData).catch((e) => setErr(e.message)); }, []);
  if (err) return <Panel testid="wc-tablajerias"><p className="text-red-400">Error: {err}</p></Panel>;
  if (!data) return <Panel testid="wc-tablajerias"><p className="text-zinc-400">Cargando…</p></Panel>;
  const go = data.technical_status === "GO técnico READ_ONLY";
  return (
    <div className="space-y-4">
      <Panel testid="wc-tablajerias-status">
        <div className={`text-lg font-bold ${go ? "text-emerald-400" : "text-amber-400"}`} data-testid="wc-tablajerias-verdict">
          {data.technical_status}
        </div>
        <p className="text-sm text-zinc-400 mt-1">production_touched: <b className="text-zinc-200">{String(data.production_touched)}</b></p>
        <p className="text-sm text-amber-300 mt-2" data-testid="wc-tablajerias-next">⚠ Siguiente decisión: {data.next_decision}</p>
        <p className="text-xs text-zinc-500 mt-1">{data.note}</p>
      </Panel>
      <Panel testid="wc-tablajerias-checklist">
        <table className="w-full text-sm">
          <thead><tr className="text-zinc-500 text-left"><th className="pb-2">Check</th><th>Veredicto</th><th>prod_touched</th><th>job_id</th></tr></thead>
          <tbody>
            {(data.items || []).map((it, i) => (
              <tr key={i} className="border-t border-zinc-800/60" data-testid={`wc-check-row-${i}`}>
                <td className="py-2">{it.check}</td>
                <td><Verdict v={it.verdict} /></td>
                <td className="text-zinc-400">{String(it.production_touched)}</td>
                <td className="text-zinc-600 text-xs truncate max-w-xs">{it.job_id || "—"}</td>
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
  useEffect(() => { apiGet("/audit?tail=120").then(setData).catch((e) => setErr(e.message)); }, []);
  if (err) return <Panel testid="wc-audit"><p className="text-red-400">Error: {err}</p></Panel>;
  if (!data) return <Panel testid="wc-audit"><p className="text-zinc-400">Cargando…</p></Panel>;
  const logs = data.logs || {};
  return (
    <div className="space-y-4" data-testid="wc-audit">
      <p className="text-xs text-zinc-500">Evidencia de runtime (solo lectura). No se escribe ni borra evidencia en Fase 1.</p>
      {Object.keys(logs).map((name) => (
        <Panel key={name} testid={`wc-audit-${name}`}>
          <h3 className="font-mono text-xs text-emerald-400 mb-2">{name}</h3>
          <pre className="bg-zinc-950 rounded-lg p-3 text-xs overflow-auto max-h-64 text-zinc-400">
            {Array.isArray(logs[name]) ? (logs[name] || []).join("\n") : JSON.stringify(logs[name], null, 2)}
          </pre>
        </Panel>
      ))}
    </div>
  );
}
