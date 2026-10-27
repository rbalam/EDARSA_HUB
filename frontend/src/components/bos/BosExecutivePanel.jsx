import React from 'react';

const valueOrDash = (value) => (
  value === null || value === undefined || value === '' ? '—' : String(value)
);

const BosExecutivePanel = ({ bos }) => {
  if (!bos || typeof bos !== 'object') return null;

  const finding = bos.finding || null;
  const priorities = Array.isArray(bos.priorities)
    ? bos.priorities
    : Array.isArray(bos.priority_items)
      ? bos.priority_items
      : [];
  const recommendation = bos.recommendation || null;
  const actionDecisions = Array.isArray(bos.action_decisions)
    ? bos.action_decisions
    : [];
  const eligibleActions = Array.isArray(recommendation?.eligible_actions)
    ? recommendation.eligible_actions
    : [];

  if (!finding && priorities.length === 0 && !recommendation && actionDecisions.length === 0) {
    return null;
  }

  return (
    <section
      className="rounded-lg border border-slate-200 bg-slate-50 p-4 space-y-4"
      data-testid="bos-executive-panel"
      aria-label="Inteligencia ejecutiva BOS"
    >
      <div>
        <h2 className="text-base font-semibold text-slate-900">Inteligencia BOS</h2>
        <p className="text-xs text-slate-500">
          Evidencia, prioridades y recomendaciones. Las acciones mostradas no se ejecutan automáticamente.
        </p>
      </div>

      {finding && (
        <div data-testid="bos-why">
          <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Por qué ocurre</p>
          <p className="text-sm text-slate-800 mt-1">{valueOrDash(finding.claim)}</p>
          {(finding.stale || bos.stale) && (
            <p className="text-xs text-amber-700 mt-1">Evidencia marcada como desactualizada.</p>
          )}
        </div>
      )}

      {priorities.length > 0 && (
        <div data-testid="bos-priorities">
          <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Qué debe atenderse</p>
          <div className="mt-2 space-y-2">
            {priorities.map((item, index) => (
              <div key={item.source_object_ref || item.priority_item_id || index} className="rounded border bg-white p-2">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <span className="text-sm font-medium text-slate-800">
                    {valueOrDash(item.title || item.source_object_ref)}
                  </span>
                  <span className="text-xs font-semibold text-slate-600">
                    {valueOrDash(item.priority_band)}
                  </span>
                </div>
                {(item.sla_state || item.due_at || item.impact) && (
                  <p className="text-xs text-slate-500 mt-1">
                    {[item.sla_state, item.due_at, item.impact].filter(Boolean).join(' • ')}
                  </p>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {recommendation && (
        <div data-testid="bos-recommendation">
          <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Qué recomienda BOS</p>
          <p className="text-sm font-medium text-slate-900 mt-1">{valueOrDash(recommendation.title)}</p>
          <p className="text-sm text-slate-700 mt-1">{valueOrDash(recommendation.rationale)}</p>
          {recommendation.expected_impact && (
            <p className="text-xs text-slate-500 mt-1">
              Impacto esperado: {recommendation.expected_impact}
            </p>
          )}
        </div>
      )}

      {eligibleActions.length > 0 && (
        <div data-testid="bos-eligible-actions">
          <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Acciones elegibles</p>
          <div className="mt-2 flex flex-wrap gap-2">
            {eligibleActions.map((action) => (
              <span key={action} className="rounded border border-slate-300 bg-white px-2 py-1 text-xs text-slate-700">
                {action}
              </span>
            ))}
          </div>
          <p className="text-xs text-slate-500 mt-2">
            Requieren autorización y confirmación según policy; este panel no ejecuta acciones.
          </p>
        </div>
      )}
    </section>
  );
};

export default BosExecutivePanel;
