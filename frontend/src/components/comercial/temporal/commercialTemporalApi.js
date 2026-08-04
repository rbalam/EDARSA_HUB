import { getToken } from '../../../lib/api';
import {
  isBackendResolvableTemporalSelection,
  normalizeTemporalSelection,
  normalizeUnitIds,
} from './commercialTemporalContract';

const backendBase = String(
  process.env.REACT_APP_BACKEND_URL || ''
).replace(/\/+$/, '');

export class CommercialTemporalApiError extends Error {
  constructor(message, options = {}) {
    super(message);
    this.name = 'CommercialTemporalApiError';
    this.status = options.status || 0;
    this.details = options.details || null;
  }
}

export async function resolveCommercialTemporalSelection({
  selection,
  unidadNegocioIds = [],
  signal,
}) {
  const token = getToken();
  const normalizedSelection = normalizeTemporalSelection(selection);
  const normalizedUnitIds = normalizeUnitIds(unidadNegocioIds);

  if (!isBackendResolvableTemporalSelection(normalizedSelection)) {
    throw new CommercialTemporalApiError(
      'Este modo temporal no requiere resolución por este endpoint.',
      {
        status: 0,
        details: {
          mode: normalizedSelection.mode,
          local_only: true,
        },
      }
    );
  }

  const payload = {
    selection: normalizedSelection,
    ...(normalizedUnitIds.length > 0
      ? { unidad_negocio_ids: normalizedUnitIds }
      : {}),
  };

  const response = await fetch(
    `${backendBase}/api/comercial/analytics/temporal/resolve`,
    {
      method: 'POST',
      signal,
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
        ...(token
          ? { Authorization: `Bearer ${token}` }
          : {}),
      },
      body: JSON.stringify(payload),
    }
  );

  let body = null;

  try {
    body = await response.json();
  } catch {
    body = null;
  }

  if (!response.ok) {
    const detail = body?.detail;

    throw new CommercialTemporalApiError(
      typeof detail === 'string'
        ? detail
        : 'No fue posible resolver la selección temporal.',
      {
        status: response.status,
        details: detail || body,
      }
    );
  }

  return body;
}
