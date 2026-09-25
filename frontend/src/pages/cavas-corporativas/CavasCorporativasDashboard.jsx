import React, { useMemo, useState } from 'react';
import api from '@/lib/api';
import { useAccessContext } from '@/hooks/useAccessContext';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { AlertCircle, Building2, CheckCircle2, Loader2, ShieldCheck, Users2 } from 'lucide-react';

const REASON_LABELS = {
  APPLICABLE: 'Aplicable',
  BENEFIT_INACTIVE: 'Beneficio inactivo',
  USER_NOT_AUTHORIZED: 'Usuario no autorizado',
  UNIT_NOT_INCLUDED: 'Unidad no incluida',
  SCOPE_NOT_INCLUDED: 'Alcance no incluido',
  NOT_YET_VALID: 'Aun no vigente',
  EXPIRED: 'Vigencia terminada',
  WEEKDAY_NOT_ALLOWED: 'Dia no permitido',
  TIME_NOT_ALLOWED: 'Horario no permitido',
  RESERVATION_REQUIRED: 'Reserva requerida',
  GUEST_COUNT_REQUIRED: 'Falta numero de invitados',
  GUEST_LIMIT_EXCEEDED: 'Limite de invitados excedido',
};

function errorMessage(error, fallback) {
  const status = error?.response?.status;
  const detail = error?.response?.data?.detail;
  if (status === 401) return 'Tu sesion no es valida o expiro.';
  if (status === 403) return typeof detail === 'string' ? detail : 'No tienes permiso para esta operacion.';
  if (status === 409) return typeof detail === 'string' ? detail : 'La operacion no puede aplicarse.';
  return fallback;
}

export default function CavasCorporativasDashboard() {
  const { context, loading: contextLoading } = useAccessContext();
  const unidadActiva = context?.unidad_activa || '';
  const nowLocal = useMemo(() => {
    const d = new Date();
    const pad = value => String(value).padStart(2, '0');
    return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
  }, []);

  const [form, setForm] = useState({
    identidad_fuente: '',
    identidad_referencia: '',
    occurred_at: nowLocal,
    unit_reference: unidadActiva,
    sales_line_reference: '',
    category_reference: '',
    family_reference: '',
    sku_reference: '',
    has_reservation: false,
    guest_count: '',
  });
  const [evaluation, setEvaluation] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [applyState, setApplyState] = useState({});

  React.useEffect(() => {
    if (unidadActiva) {
      setForm(current => ({ ...current, unit_reference: current.unit_reference || unidadActiva }));
    }
  }, [unidadActiva]);

  const payload = () => ({
    identidad_fuente: form.identidad_fuente.trim(),
    identidad_referencia: form.identidad_referencia.trim(),
    occurred_at: new Date(form.occurred_at).toISOString(),
    unit_reference: form.unit_reference.trim(),
    sales_line_reference: form.sales_line_reference.trim() || null,
    category_reference: form.category_reference.trim() || null,
    family_reference: form.family_reference.trim() || null,
    sku_reference: form.sku_reference.trim() || null,
    has_reservation: Boolean(form.has_reservation),
    guest_count: form.guest_count === '' ? null : Number(form.guest_count),
  });

  const evaluate = async event => {
    event.preventDefault();
    setLoading(true);
    setError('');
    setApplyState({});
    try {
      const response = await api.post('/cavas/corporativas/evaluar', payload());
      setEvaluation(response.data);
    } catch (err) {
      setEvaluation(null);
      setError(errorMessage(err, 'No se pudo evaluar el beneficio corporativo.'));
    } finally {
      setLoading(false);
    }
  };

  const applyBenefit = async benefitId => {
    const operacionTipo = window.prompt('Tipo de operacion (ej. TICKET):', 'TICKET');
    if (!operacionTipo) return;
    const operacionReferencia = window.prompt('Referencia de la operacion:');
    if (!operacionReferencia) return;
    setApplyState(current => ({ ...current, [benefitId]: { loading: true } }));
    try {
      const response = await api.post('/cavas/corporativas/aplicar', {
        ...payload(),
        benefit_id: benefitId,
        operacion_tipo: operacionTipo.trim(),
        operacion_referencia: operacionReferencia.trim(),
      });
      setApplyState(current => ({ ...current, [benefitId]: { loading: false, data: response.data } }));
    } catch (err) {
      setApplyState(current => ({ ...current, [benefitId]: { loading: false, error: errorMessage(err, 'No se pudo registrar la aplicacion.') } }));
    }
  };

  const field = (name, value) => setForm(current => ({ ...current, [name]: value }));
  const decisions = evaluation?.decisions || [];

  return (
    <div className="p-6 space-y-6" data-testid="cavas-corporativas-dashboard">
      <div className="flex items-center gap-3">
        <div className="rounded-xl bg-slate-900 p-2 text-white"><Building2 className="h-6 w-6" /></div>
        <div><h1 className="text-2xl font-semibold">Cavas Corporativas</h1><p className="text-sm text-muted-foreground">Evaluacion y aplicacion de beneficios B2B con reglas resueltas por el backend.</p></div>
      </div>
      <Card>
        <CardHeader><CardTitle className="flex items-center gap-2"><ShieldCheck className="h-5 w-5" /> Evaluar beneficio</CardTitle><CardDescription>React solo envia contexto operativo. Autorizacion, vigencia, alcance, horario y politicas se calculan en EDARSAHUB.</CardDescription></CardHeader>
        <CardContent>
          <form onSubmit={evaluate} className="space-y-5">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              <div><Label>Fuente de identidad</Label><Input value={form.identidad_fuente} onChange={e => field('identidad_fuente', e.target.value)} placeholder="CRM_CANONICO" required /></div>
              <div><Label>Referencia de identidad</Label><Input value={form.identidad_referencia} onChange={e => field('identidad_referencia', e.target.value)} placeholder="Identificador canonico" required /></div>
              <div><Label>Unidad</Label><Input value={form.unit_reference} onChange={e => field('unit_reference', e.target.value)} placeholder={contextLoading ? 'Resolviendo...' : 'Unidad canonica'} required /></div>
              <div><Label>Fecha y hora</Label><Input type="datetime-local" value={form.occurred_at} onChange={e => field('occurred_at', e.target.value)} required /></div>
              <div><Label>Linea de venta</Label><Input value={form.sales_line_reference} onChange={e => field('sales_line_reference', e.target.value)} placeholder="Opcional" /></div>
              <div><Label>Categoria</Label><Input value={form.category_reference} onChange={e => field('category_reference', e.target.value)} placeholder="Opcional" /></div>
              <div><Label>Familia</Label><Input value={form.family_reference} onChange={e => field('family_reference', e.target.value)} placeholder="Opcional" /></div>
              <div><Label>SKU</Label><Input value={form.sku_reference} onChange={e => field('sku_reference', e.target.value)} placeholder="Opcional" /></div>
              <div><Label>Invitados</Label><Input type="number" min="0" value={form.guest_count} onChange={e => field('guest_count', e.target.value)} placeholder="Opcional" /></div>
            </div>
            <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={form.has_reservation} onChange={e => field('has_reservation', e.target.checked)} />Existe reserva asociada</label>
            <Button type="submit" disabled={loading}>{loading ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <ShieldCheck className="h-4 w-4 mr-2" />}Evaluar</Button>
          </form>
        </CardContent>
      </Card>
      {error && <div className="rounded-lg bg-red-50 text-red-700 p-4 flex gap-2"><AlertCircle className="h-5 w-5 shrink-0" />{error}</div>}
      {evaluation && (
        <Card>
          <CardHeader><CardTitle className="flex items-center gap-2"><Users2 className="h-5 w-5" /> Resultado</CardTitle><CardDescription>Convenio: {evaluation.convenio_id || 'Sin convenio autorizado'}</CardDescription></CardHeader>
          <CardContent className="space-y-3">
            {decisions.length === 0 ? <div className="rounded-lg border p-4 text-sm text-muted-foreground">No hay beneficios evaluables para esta identidad y contexto.</div> : decisions.map(decision => {
              const state = applyState[decision.benefit_id] || {};
              return <div key={decision.benefit_id} className="rounded-lg border p-4 flex flex-col md:flex-row md:items-center md:justify-between gap-3"><div><div className="font-medium">{decision.benefit_id}</div><div className={decision.applicable ? 'text-sm text-emerald-700' : 'text-sm text-muted-foreground'}>{REASON_LABELS[decision.reason] || decision.reason}</div>{state.data && <div className="text-xs text-emerald-700 mt-1">{state.data.idempotent_replay ? 'Operacion ya registrada; no se duplico.' : 'Beneficio registrado.'}</div>}{state.error && <div className="text-xs text-red-700 mt-1">{state.error}</div>}</div>{decision.applicable && <Button variant="outline" onClick={() => applyBenefit(decision.benefit_id)} disabled={state.loading}>{state.loading ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <CheckCircle2 className="h-4 w-4 mr-2" />}Aplicar</Button>}</div>;
            })}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
