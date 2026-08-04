import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from 'react';

import {
  createInitialCommercialTemporalValue,
  isBackendResolvableTemporalSelection,
  normalizeTemporalSelection,
  normalizeUnitIds,
  validateTemporalSelection,
} from './commercialTemporalContract';

import {
  resolveCommercialTemporalSelection,
} from './commercialTemporalApi';

export function useCommercialTemporalSelection({
  initialValue,
  autoResolve = false,
  onResolved,
} = {}) {
  const initial = useMemo(
    () => initialValue || createInitialCommercialTemporalValue(),
    [initialValue]
  );

  const [value, setValue] = useState(() => ({
    ...initial,
    unidad_negocio_ids: normalizeUnitIds(
      initial?.unidad_negocio_ids
    ),
    selection: normalizeTemporalSelection(
      initial?.selection
    ),
  }));

  const [resolved, setResolved] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const abortRef = useRef(null);

  const validation = useMemo(
    () => validateTemporalSelection(value.selection),
    [value.selection]
  );

  const updateValue = useCallback((nextValue) => {
    setValue((previous) => {
      const candidate = typeof nextValue === 'function'
        ? nextValue(previous)
        : nextValue;

      return {
        ...candidate,
        unidad_negocio_ids: normalizeUnitIds(
          candidate?.unidad_negocio_ids
        ),
        selection: normalizeTemporalSelection(
          candidate?.selection
        ),
      };
    });
  }, []);

  const resolve = useCallback(async (candidateValue = value) => {
    const candidateSelection = normalizeTemporalSelection(
      candidateValue?.selection
    );
    const candidateValidation = validateTemporalSelection(
      candidateSelection
    );

    if (!candidateValidation.valid) {
      setError(
        candidateValidation.errors[0]
        || 'Selección temporal inválida.'
      );
      return null;
    }

    if (!isBackendResolvableTemporalSelection(candidateSelection)) {
      setResolved(null);
      setError('');
      return {
        local_only: true,
        selection: candidateSelection,
      };
    }

    abortRef.current?.abort();

    const controller = new AbortController();
    abortRef.current = controller;

    setLoading(true);
    setError('');

    try {
      const result = await resolveCommercialTemporalSelection({
        selection: candidateValidation.selection,
        unidadNegocioIds: candidateValue?.unidad_negocio_ids,
        signal: controller.signal,
      });

      setResolved(result);
      onResolved?.(result, candidateValue);

      return result;
    } catch (requestError) {
      if (requestError?.name === 'AbortError') {
        return null;
      }

      setResolved(null);
      setError(
        requestError?.message
        || 'No fue posible resolver la selección.'
      );

      return null;
    } finally {
      if (abortRef.current === controller) {
        setLoading(false);
      }
    }
  }, [
    onResolved,
    value,
  ]);

  useEffect(() => () => {
    abortRef.current?.abort();
  }, []);

  useEffect(() => {
    if (
      !autoResolve
      || !validation.valid
      || !isBackendResolvableTemporalSelection(
        validation.selection
      )
    ) {
      return undefined;
    }

    const timeout = window.setTimeout(() => {
      resolve(value);
    }, 250);

    return () => window.clearTimeout(timeout);
  }, [
    autoResolve,
    resolve,
    validation.selection,
    validation.valid,
    value,
  ]);

  return {
    value,
    setValue: updateValue,
    selection: validation.selection,
    validation,
    resolved,
    loading,
    error,
    resolve,
    clearError: () => setError(''),
  };
}
