import React, {
  useEffect,
  useMemo,
  useRef,
  useState,
} from 'react';

import { DayPicker } from 'react-day-picker';
import { es } from 'date-fns/locale';
import {
  CalendarDays,
  Check,
  ChevronDown,
  Filter,
  Loader2,
  Plus,
  Trash2,
  X,
} from 'lucide-react';

import { Button } from '../../ui/button';
import { Label } from '../../ui/label';

import {
  COMMERCIAL_BASIC_MODES,
  COMMERCIAL_TEMPORAL_MODES,
  MONTH_OCCURRENCES,
  WEEKDAYS,
  createCalendarWeekDates,
  createInclusiveDateSequence,
  createMonthDateRange,
  createMonthWeekdayColumnDates,
  isBackendResolvableTemporalSelection,
  mergeSpecificDateBlocks,
  normalizeIsoDate,
  normalizeTemporalSelection,
  normalizeUnitIds,
  validateTemporalSelection,
} from './commercialTemporalContract';

function isoToDate(value) {
  const normalized = normalizeIsoDate(value);
  if (!normalized) return undefined;

  const [year, month, day] = normalized.split('-').map(Number);
  return new Date(year, month - 1, day, 12, 0, 0);
}

function dateToIso(value) {
  if (!(value instanceof Date)) return null;

  return [
    value.getFullYear(),
    String(value.getMonth() + 1).padStart(2, '0'),
    String(value.getDate()).padStart(2, '0'),
  ].join('-');
}

function selectionLabel(value) {
  const selection = normalizeTemporalSelection(value?.selection);

  if (
    selection.mode
    === COMMERCIAL_TEMPORAL_MODES.CURRENT_OPERATIONAL_DAY
  ) {
    return 'Ventas del día';
  }

  if (
    selection.mode
    === COMMERCIAL_TEMPORAL_MODES.SPECIFIC_DATES
  ) {
    return selection.dates.length === 1
      ? selection.dates[0]
      : `${selection.dates.length} fechas seleccionadas`;
  }

  if (
    selection.mode
    === COMMERCIAL_TEMPORAL_MODES.DATE_RANGES
  ) {
    return selection.ranges.length === 1
      ? `${selection.ranges[0].start_date} a ${selection.ranges[0].end_date}`
      : `${selection.ranges.length} rangos seleccionados`;
  }

  if (
    selection.mode
    === COMMERCIAL_TEMPORAL_MODES.DATE_RULES
  ) {
    return 'Regla temporal avanzada';
  }

  return 'Seleccionar periodo';
}

function UnitSelector({
  units,
  selectedIds,
  onChange,
  disabled,
}) {
  const normalizedSelected = normalizeUnitIds(selectedIds);

  if (!Array.isArray(units) || units.length === 0) {
    return null;
  }

  const toggleUnit = (id) => {
    const next = normalizedSelected.includes(id)
      ? normalizedSelected.filter((value) => value !== id)
      : [...normalizedSelected, id];

    onChange(normalizeUnitIds(next));
  };

  return (
    <div>
      <Label className="mb-2 block text-xs">
        Unidades de negocio
      </Label>

      <div className="flex flex-wrap gap-2">
        {units.map((unit) => {
          const id = String(
            unit?.id
            || unit?.codigo
            || unit?.unidad_negocio_id
            || ''
          ).trim();

          if (!id) return null;

          const selected = normalizedSelected.includes(id);

          return (
            <button
              key={id}
              type="button"
              disabled={disabled}
              onClick={() => toggleUnit(id)}
              className={`rounded-md border px-3 py-2 text-sm transition ${
                selected
                  ? 'border-blue-500 bg-blue-50 text-blue-700'
                  : 'border-zinc-200 bg-white text-zinc-700'
              }`}
            >
              {selected && (
                <Check className="mr-1 inline h-3.5 w-3.5" />
              )}
              {unit?.nombre || unit?.label || id}
            </button>
          );
        })}
      </div>
    </div>
  );
}

export default function CommercialTemporalSelector({
  value,
  onChange,
  availableUnits = [],
  disabled = false,
  loading = false,
  resolved = null,
  error = '',
  onResolve,
  availability = null,
  allowedBasicModes = null,
  className = '',
}) {
  const [open, setOpen] = useState(false);
  const [draft, setDraft] = useState(value);
  const [draftRange, setDraftRange] = useState({
    start_date: '',
    end_date: '',
  });
  const [calendarBlockMode, setCalendarBlockMode] =
    useState('single');
  const [selectionAnchor, setSelectionAnchor] =
    useState(null);

  const triggerRef = useRef(null);
  const dialogRef = useRef(null);

  useEffect(() => {
    if (!open) setDraft(value);
  }, [open, value]);

  useEffect(() => {
    if (!open) return undefined;

    const dialog = dialogRef.current;
    const focusableSelector = [
      'button:not([disabled])',
      'input:not([disabled])',
      'select:not([disabled])',
      '[tabindex]:not([tabindex="-1"])',
    ].join(',');

    const focusables = () => (
      dialog
        ? Array.from(dialog.querySelectorAll(focusableSelector))
        : []
    );

    const handleKeyDown = (event) => {
      if (event.key === 'Escape') {
        event.preventDefault();
        setOpen(false);
        return;
      }

      if (event.key !== 'Tab') return;

      const items = focusables();
      if (items.length === 0) return;

      const first = items[0];
      const last = items[items.length - 1];

      if (
        event.shiftKey
        && document.activeElement === first
      ) {
        event.preventDefault();
        last.focus();
      } else if (
        !event.shiftKey
        && document.activeElement === last
      ) {
        event.preventDefault();
        first.focus();
      }
    };

    const handlePointerDown = (event) => {
      if (
        dialogRef.current?.contains(event.target)
        || triggerRef.current?.contains(event.target)
      ) {
        return;
      }

      setOpen(false);
    };

    document.addEventListener('keydown', handleKeyDown);
    document.addEventListener('mousedown', handlePointerDown);

    const items = focusables();
    items[0]?.focus();

    return () => {
      document.removeEventListener('keydown', handleKeyDown);
      document.removeEventListener(
        'mousedown',
        handlePointerDown
      );
    };
  }, [open]);

  useEffect(() => {
    if (!open) {
      triggerRef.current?.focus();
    }
  }, [open]);

  const normalizedSelection = useMemo(
    () => normalizeTemporalSelection(draft?.selection),
    [draft]
  );

  const validation = useMemo(
    () => validateTemporalSelection(normalizedSelection),
    [normalizedSelection]
  );

  const historicalAvailability = useMemo(() => {
    const years = Array.isArray(availability?.anios)
      ? availability.anios
      : [];

    return years
      .map((yearEntry) => ({
        year: Number(yearEntry?.anio),
        months: Array.isArray(yearEntry?.meses)
          ? yearEntry.meses
            .map((monthEntry) => Number(monthEntry?.mes))
            .filter((month) => (
              Number.isInteger(month)
              && month >= 1
              && month <= 12
            ))
          : [],
      }))
      .filter((yearEntry) => (
        Number.isInteger(yearEntry.year)
        && yearEntry.months.length > 0
      ))
      .sort((left, right) => right.year - left.year);
  }, [availability]);

  const visibleBasicOptions = useMemo(() => {
    const options = [
      {
        id: COMMERCIAL_BASIC_MODES.TODAY,
        label: 'Ventas del día',
      },
      {
        id: COMMERCIAL_BASIC_MODES.SINGLE_OR_RANGE,
        label: 'Día o rango',
      },
      {
        id: COMMERCIAL_BASIC_MODES.HISTORICAL,
        label: 'Históricos',
      },
      {
        id: COMMERCIAL_BASIC_MODES.ADVANCED,
        label: 'Filtros avanzados',
      },
    ];

    if (
      !Array.isArray(allowedBasicModes)
      || allowedBasicModes.length === 0
    ) {
      return options;
    }

    const allowed = new Set(allowedBasicModes);

    return options.filter((option) => allowed.has(option.id));
  }, [allowedBasicModes]);

  const updateSelection = (selection) => {
    setDraft((previous) => ({
      ...previous,
      selection: normalizeTemporalSelection(selection),
    }));
  };

  const applyCalendarBlock = (
    clickedDate,
    nativeEvent = null
  ) => {
    const clickedIso = dateToIso(clickedDate);
    if (!clickedIso) return;

    const preserveExisting = Boolean(nativeEvent?.shiftKey);
    const currentDates = normalizedSelection.dates || [];

    let blockDates = [clickedIso];

    if (
      nativeEvent?.shiftKey
      && selectionAnchor
      && calendarBlockMode === 'single'
    ) {
      blockDates = createInclusiveDateSequence(
        selectionAnchor,
        clickedIso
      );
    } else if (calendarBlockMode === 'horizontal') {
      blockDates = createCalendarWeekDates(clickedIso);
    } else if (calendarBlockMode === 'vertical') {
      blockDates = createMonthWeekdayColumnDates(clickedIso);
    }

    updateSelection({
      mode: COMMERCIAL_TEMPORAL_MODES.SPECIFIC_DATES,
      dates: mergeSpecificDateBlocks(
        currentDates,
        blockDates,
        preserveExisting
      ),
    });

    setSelectionAnchor(clickedIso);
  };

  const toggleHistoricalMonth = (
    year,
    month,
    preserveExisting = true
  ) => {
    const range = createMonthDateRange(year, month);
    if (!range) return;

    const currentRanges = normalizedSelection.ranges || [];

    const exists = currentRanges.some((candidate) => (
      candidate.start_date === range.start_date
      && candidate.end_date === range.end_date
    ));

    const nextRanges = exists
      ? currentRanges.filter((candidate) => !(
        candidate.start_date === range.start_date
        && candidate.end_date === range.end_date
      ))
      : (
        preserveExisting
          ? [...currentRanges, range]
          : [range]
      );

    updateSelection({
      mode: COMMERCIAL_TEMPORAL_MODES.DATE_RANGES,
      ranges: nextRanges,
    });
  };

  const selectBasicMode = (basicMode) => {
    if (basicMode === COMMERCIAL_BASIC_MODES.TODAY) {
      setDraft((previous) => ({
        ...previous,
        basic_mode: basicMode,
        selection: {
          mode:
            COMMERCIAL_TEMPORAL_MODES.CURRENT_OPERATIONAL_DAY,
        },
      }));
      return;
    }

    if (
      basicMode
      === COMMERCIAL_BASIC_MODES.SINGLE_OR_RANGE
    ) {
      setDraft((previous) => ({
        ...previous,
        basic_mode: basicMode,
        selection: {
          mode: COMMERCIAL_TEMPORAL_MODES.DATE_RANGES,
          ranges: [],
        },
      }));
      return;
    }

    if (basicMode === COMMERCIAL_BASIC_MODES.HISTORICAL) {
      setDraft((previous) => ({
        ...previous,
        basic_mode: basicMode,
        selection: {
          mode: COMMERCIAL_TEMPORAL_MODES.DATE_RANGES,
          ranges: [],
        },
      }));
      return;
    }

    setDraft((previous) => ({
      ...previous,
      basic_mode: COMMERCIAL_BASIC_MODES.ADVANCED,
      selection: {
        mode: COMMERCIAL_TEMPORAL_MODES.SPECIFIC_DATES,
        dates: [],
      },
    }));
  };

  const addRange = () => {
    const startDate = normalizeIsoDate(draftRange.start_date);
    const endDate = normalizeIsoDate(
      draftRange.end_date || draftRange.start_date
    );

    if (!startDate || !endDate) return;

    updateSelection({
      mode: COMMERCIAL_TEMPORAL_MODES.DATE_RANGES,
      ranges: [
        ...(normalizedSelection.ranges || []),
        {
          start_date: startDate,
          end_date: endDate,
        },
      ],
    });

    setDraftRange({
      start_date: '',
      end_date: '',
    });
  };

  const apply = async () => {
    if (!validation.valid) return;

    const normalizedDraft = {
      ...draft,
      unidad_negocio_ids: normalizeUnitIds(
        draft?.unidad_negocio_ids
      ),
      selection: validation.selection,
    };

    const requiresBackendResolution =
      isBackendResolvableTemporalSelection(
        normalizedDraft.selection
      );

    if (requiresBackendResolution && onResolve) {
      const result = await onResolve(normalizedDraft);

      if (!result) {
        return;
      }
    }

    onChange?.(normalizedDraft);
    setOpen(false);
  };

  const isAdvanced = (
    draft?.basic_mode === COMMERCIAL_BASIC_MODES.ADVANCED
  );

  return (
    <div className={`relative ${className}`}>
      <Label className="mb-1 block text-xs">
        Periodo comercial
      </Label>

      <button
        ref={triggerRef}
        type="button"
        disabled={disabled || loading}
        onClick={() => setOpen((previous) => !previous)}
        className="flex h-10 min-w-[250px] w-full items-center justify-between rounded-md border border-input bg-background px-3 py-2 text-sm disabled:opacity-50"
        aria-expanded={open}
        aria-haspopup="dialog"
      >
        <span className="flex min-w-0 items-center gap-2">
          <CalendarDays className="h-4 w-4 shrink-0" />
          <span className="truncate">
            {loading
              ? 'Resolviendo selección…'
              : selectionLabel(value)}
          </span>
        </span>

        {loading
          ? <Loader2 className="h-4 w-4 animate-spin" />
          : <ChevronDown className="h-4 w-4" />}
      </button>

      {open && (
        <div
          ref={dialogRef}
          role="dialog"
          aria-modal="true"
          aria-label="Selector temporal comercial"
          className="absolute left-0 z-50 mt-1 w-[min(94vw,920px)] rounded-lg border bg-white shadow-xl"
        >
          <div className="flex items-center justify-between border-b p-4">
            <div>
              <h3 className="font-semibold">
                Filtros comerciales
              </h3>
              <p className="text-sm text-zinc-500">
                La resolución final y el alcance se validan en backend.
              </p>
            </div>

            <button
              type="button"
              onClick={() => setOpen(false)}
              aria-label="Cerrar"
            >
              <X className="h-5 w-5" />
            </button>
          </div>

          <div className="grid lg:grid-cols-[230px_1fr]">
            <aside className="space-y-2 border-b p-3 lg:border-b-0 lg:border-r">
              {visibleBasicOptions.map((option) => (
                <button
                  key={option.id}
                  type="button"
                  onClick={() => selectBasicMode(option.id)}
                  className={`w-full rounded-md border px-3 py-3 text-left text-sm ${
                    draft?.basic_mode === option.id
                      ? 'border-blue-500 bg-blue-50 text-blue-700'
                      : 'border-zinc-200'
                  }`}
                >
                  {option.id === COMMERCIAL_BASIC_MODES.ADVANCED
                    && <Filter className="mr-2 inline h-4 w-4" />}
                  {option.label}
                </button>
              ))}
            </aside>

            <main className="min-h-[420px] space-y-5 p-4">
              <UnitSelector
                units={availableUnits}
                selectedIds={draft?.unidad_negocio_ids}
                disabled={disabled}
                onChange={(unidadNegocioIds) => {
                  setDraft((previous) => ({
                    ...previous,
                    unidad_negocio_ids: unidadNegocioIds,
                  }));
                }}
              />

              {(
                normalizedSelection.mode
                === COMMERCIAL_TEMPORAL_MODES.CURRENT_OPERATIONAL_DAY
              ) && (
                <div className="rounded-md border bg-zinc-50 p-6 text-center">
                  <CalendarDays className="mx-auto h-8 w-8 text-blue-500" />
                  <p className="mt-3 font-medium">
                    Ventas del día operativo
                  </p>
                  <p className="mt-1 text-sm text-zinc-500">
                    El backend resolverá la fecha operativa vigente
                    de cada unidad.
                  </p>
                </div>
              )}

              {(
                normalizedSelection.mode
                === COMMERCIAL_TEMPORAL_MODES.DATE_RANGES
              ) && (
                <div className="space-y-4">
                  <div className="grid gap-3 sm:grid-cols-[1fr_1fr_auto]">
                    <div>
                      <Label className="mb-1 block text-xs">
                        Inicio
                      </Label>
                      <input
                        type="date"
                        value={draftRange.start_date}
                        onChange={(event) => {
                          setDraftRange((previous) => ({
                            ...previous,
                            start_date: event.target.value,
                          }));
                        }}
                        className="h-10 w-full rounded-md border px-3"
                      />
                    </div>

                    <div>
                      <Label className="mb-1 block text-xs">
                        Fin
                      </Label>
                      <input
                        type="date"
                        value={draftRange.end_date}
                        min={draftRange.start_date || undefined}
                        onChange={(event) => {
                          setDraftRange((previous) => ({
                            ...previous,
                            end_date: event.target.value,
                          }));
                        }}
                        className="h-10 w-full rounded-md border px-3"
                      />
                    </div>

                    <Button
                      type="button"
                      onClick={addRange}
                      className="self-end"
                    >
                      <Plus className="mr-1 h-4 w-4" />
                      Agregar
                    </Button>
                  </div>

                  {(normalizedSelection.ranges || []).map(
                    (range, index) => (
                      <div
                        key={`${range.start_date}-${range.end_date}`}
                        className="flex items-center justify-between rounded-md border px-3 py-2"
                      >
                        <span className="text-sm">
                          {range.start_date} a {range.end_date}
                        </span>

                        <button
                          type="button"
                          onClick={() => {
                            updateSelection({
                              ...normalizedSelection,
                              ranges:
                                normalizedSelection.ranges.filter(
                                  (_, candidateIndex) => (
                                    candidateIndex !== index
                                  )
                                ),
                            });
                          }}
                          aria-label="Eliminar rango"
                        >
                          <Trash2 className="h-4 w-4 text-red-500" />
                        </button>
                      </div>
                    )
                  )}
                </div>
              )}

              {(
                draft?.basic_mode
                === COMMERCIAL_BASIC_MODES.HISTORICAL
              ) && (
                <div className="space-y-4">
                  <div>
                    <h4 className="font-medium">
                      Meses y años históricos
                    </h4>
                    <p className="text-sm text-zinc-500">
                      Selecciona meses de uno o varios años.
                      Mantén Shift para conservar bloques anteriores.
                    </p>
                  </div>

                  {historicalAvailability.length === 0 ? (
                    <p className="rounded-md border bg-zinc-50 p-4 text-sm text-zinc-500">
                      La cobertura histórica deberá ser proporcionada
                      por el módulo consumidor.
                    </p>
                  ) : (
                    <div className="max-h-[320px] space-y-4 overflow-y-auto">
                      {historicalAvailability.map((yearEntry) => (
                        <section
                          key={yearEntry.year}
                          className="rounded-md border p-3"
                        >
                          <div className="mb-2 flex items-center justify-between">
                            <strong>{yearEntry.year}</strong>

                            <button
                              type="button"
                              onClick={(event) => {
                                yearEntry.months.forEach(
                                  (month, index) => {
                                    toggleHistoricalMonth(
                                      yearEntry.year,
                                      month,
                                      event.shiftKey || index > 0
                                    );
                                  }
                                );
                              }}
                              className="text-sm text-blue-600"
                            >
                              Año completo
                            </button>
                          </div>

                          <div className="grid grid-cols-3 gap-2 sm:grid-cols-4">
                            {yearEntry.months.map((month) => {
                              const range = createMonthDateRange(
                                yearEntry.year,
                                month
                              );

                              const selected = (
                                normalizedSelection.ranges || []
                              ).some((candidate) => (
                                candidate.start_date
                                  === range?.start_date
                                && candidate.end_date
                                  === range?.end_date
                              ));

                              return (
                                <button
                                  key={month}
                                  type="button"
                                  onClick={(event) => {
                                    toggleHistoricalMonth(
                                      yearEntry.year,
                                      month,
                                      event.shiftKey
                                    );
                                  }}
                                  className={`rounded-md border px-3 py-2 text-sm ${
                                    selected
                                      ? 'border-blue-500 bg-blue-50'
                                      : ''
                                  }`}
                                >
                                  {new Intl.DateTimeFormat(
                                    'es-MX',
                                    { month: 'short' }
                                  ).format(
                                    new Date(
                                      yearEntry.year,
                                      month - 1,
                                      1
                                    )
                                  )}
                                </button>
                              );
                            })}
                          </div>
                        </section>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {isAdvanced && (
                <div className="space-y-4">
                  <div className="flex flex-wrap gap-2">
                    {[
                      {
                        mode:
                          COMMERCIAL_TEMPORAL_MODES.SPECIFIC_DATES,
                        label: 'Fechas específicas',
                      },
                      {
                        mode:
                          COMMERCIAL_TEMPORAL_MODES.DATE_RANGES,
                        label: 'Varios rangos',
                      },
                      {
                        mode:
                          COMMERCIAL_TEMPORAL_MODES.DATE_RULES,
                        label: 'Reglas',
                      },
                    ].map((option) => (
                      <button
                        key={option.mode}
                        type="button"
                        onClick={() => {
                          if (
                            option.mode
                            === COMMERCIAL_TEMPORAL_MODES.SPECIFIC_DATES
                          ) {
                            updateSelection({
                              mode: option.mode,
                              dates: [],
                            });
                          } else if (
                            option.mode
                            === COMMERCIAL_TEMPORAL_MODES.DATE_RANGES
                          ) {
                            updateSelection({
                              mode: option.mode,
                              ranges: [],
                            });
                          } else {
                            updateSelection({
                              mode: option.mode,
                              rule_type: 'weekdays',
                              start_date: '',
                              end_date: '',
                              weekdays: [],
                            });
                          }
                        }}
                        className={`rounded-md border px-3 py-2 text-sm ${
                          normalizedSelection.mode === option.mode
                            ? 'border-blue-500 bg-blue-50 text-blue-700'
                            : ''
                        }`}
                      >
                        {option.label}
                      </button>
                    ))}
                  </div>

                  {(
                    normalizedSelection.mode
                    === COMMERCIAL_TEMPORAL_MODES.SPECIFIC_DATES
                  ) && (
                    <div className="space-y-3">
                      <div className="flex flex-wrap gap-2">
                        {[
                          {
                            id: 'single',
                            label: 'Día o bloque con Shift',
                          },
                          {
                            id: 'horizontal',
                            label: 'Semana horizontal',
                          },
                          {
                            id: 'vertical',
                            label: 'Columna vertical',
                          },
                        ].map((option) => (
                          <button
                            key={option.id}
                            type="button"
                            onClick={() => {
                              setCalendarBlockMode(option.id);
                              setSelectionAnchor(null);
                            }}
                            className={`rounded-md border px-3 py-2 text-sm ${
                              calendarBlockMode === option.id
                                ? 'border-blue-500 bg-blue-50'
                                : ''
                            }`}
                          >
                            {option.label}
                          </button>
                        ))}
                      </div>

                      <p className="text-xs text-zinc-500">
                        Mantén Shift al seleccionar para conservar
                        bloques anteriores. En modo Día, Shift crea
                        un bloque desde la última fecha seleccionada.
                      </p>

                      <div className="w-full max-w-[420px] overflow-x-auto">
                        <DayPicker
                          mode="multiple"
                          locale={es}
                          className="w-full p-2"
                          classNames={{
                            months: 'w-full',
                            month: 'w-full space-y-4',
                            caption:
                              'relative flex items-center justify-center pt-1',
                            caption_label:
                              'text-base font-semibold capitalize',
                            nav:
                              'absolute inset-x-0 top-0 flex items-center justify-between',
                            nav_button:
                              'inline-flex h-8 w-8 items-center justify-center rounded-md border bg-white',
                            table:
                              'w-full table-fixed border-collapse',
                            head_row:
                              'grid w-full grid-cols-7',
                            head_cell:
                              'min-w-0 py-2 text-center text-xs font-semibold text-zinc-600',
                            row:
                              'mt-1 grid w-full grid-cols-7',
                            cell:
                              'relative min-w-0 p-0 text-center',
                            day:
                              'mx-auto inline-flex h-10 w-10 max-w-full items-center justify-center rounded-md text-sm font-normal hover:bg-zinc-100 aria-selected:bg-blue-600 aria-selected:text-white',
                            day_selected:
                              'bg-blue-600 text-white hover:bg-blue-700',
                            day_today:
                              'border border-blue-500 font-semibold',
                            day_outside:
                              'text-zinc-300 opacity-50',
                            day_disabled:
                              'text-zinc-300 opacity-40',
                            day_range_start:
                              'rounded-l-full bg-blue-600 text-white',
                            day_range_middle:
                              'rounded-none bg-blue-600 text-white',
                            day_range_end:
                              'rounded-r-full bg-blue-600 text-white',
                          }}
                          selected={
                            normalizedSelection.dates.map(isoToDate)
                          }
                          onDayClick={(day, modifiers, event) => {
                            applyCalendarBlock(day, event);
                          }}
                          showOutsideDays={false}
                        />
                      </div>
                    </div>
                  )}

                  {(
                    normalizedSelection.mode
                    === COMMERCIAL_TEMPORAL_MODES.DATE_RULES
                  ) && (
                    <div className="space-y-4">
                      <div className="grid gap-3 sm:grid-cols-2">
                        <div>
                          <Label className="mb-1 block text-xs">
                            Inicio
                          </Label>
                          <input
                            type="date"
                            value={
                              normalizedSelection.start_date || ''
                            }
                            onChange={(event) => {
                              updateSelection({
                                ...normalizedSelection,
                                start_date: event.target.value,
                              });
                            }}
                            className="h-10 w-full rounded-md border px-3"
                          />
                        </div>

                        <div>
                          <Label className="mb-1 block text-xs">
                            Fin
                          </Label>
                          <input
                            type="date"
                            value={
                              normalizedSelection.end_date || ''
                            }
                            min={
                              normalizedSelection.start_date
                              || undefined
                            }
                            onChange={(event) => {
                              updateSelection({
                                ...normalizedSelection,
                                end_date: event.target.value,
                              });
                            }}
                            className="h-10 w-full rounded-md border px-3"
                          />
                        </div>
                      </div>

                      <div>
                        <Label className="mb-2 block text-xs">
                          Tipo de regla
                        </Label>

                        <select
                          value={normalizedSelection.rule_type}
                          onChange={(event) => {
                            updateSelection({
                              ...normalizedSelection,
                              rule_type: event.target.value,
                            });
                          }}
                          className="h-10 rounded-md border px-3"
                        >
                          <option value="weekdays">
                            Días de la semana
                          </option>
                          <option value="weekdays_in_month_weeks">
                            Semanas específicas del mes
                          </option>
                          <option value="nth_weekday_of_month">
                            Primer, segundo o último día del mes
                          </option>
                        </select>
                      </div>

                      <div>
                        <Label className="mb-2 block text-xs">
                          Días
                        </Label>

                        <div className="flex flex-wrap gap-2">
                          {WEEKDAYS.map((weekday) => {
                            const selected =
                              normalizedSelection.weekdays.includes(
                                weekday.value
                              );

                            return (
                              <button
                                key={weekday.value}
                                type="button"
                                onClick={() => {
                                  updateSelection({
                                    ...normalizedSelection,
                                    weekdays: selected
                                      ? normalizedSelection.weekdays.filter(
                                        (value) => (
                                          value !== weekday.value
                                        )
                                      )
                                      : [
                                        ...normalizedSelection.weekdays,
                                        weekday.value,
                                      ],
                                  });
                                }}
                                className={`rounded-md border px-3 py-2 text-sm ${
                                  selected
                                    ? 'border-blue-500 bg-blue-50'
                                    : ''
                                }`}
                              >
                                {weekday.label}
                              </button>
                            );
                          })}
                        </div>
                      </div>

                      {(
                        normalizedSelection.rule_type
                        === 'weekdays_in_month_weeks'
                      ) && (
                        <div>
                          <Label className="mb-2 block text-xs">
                            Semanas del mes
                          </Label>

                          <div className="flex gap-2">
                            {[1, 2, 3, 4, 5].map((week) => {
                              const selected = (
                                normalizedSelection.month_weeks || []
                              ).includes(week);

                              return (
                                <button
                                  key={week}
                                  type="button"
                                  onClick={() => {
                                    const values = (
                                      normalizedSelection.month_weeks
                                      || []
                                    );

                                    updateSelection({
                                      ...normalizedSelection,
                                      month_weeks: selected
                                        ? values.filter(
                                          (value) => value !== week
                                        )
                                        : [...values, week],
                                    });
                                  }}
                                  className={`rounded-md border px-3 py-2 ${
                                    selected
                                      ? 'border-blue-500 bg-blue-50'
                                      : ''
                                  }`}
                                >
                                  {week}
                                </button>
                              );
                            })}
                          </div>
                        </div>
                      )}

                      {(
                        normalizedSelection.rule_type
                        === 'nth_weekday_of_month'
                      ) && (
                        <div>
                          <Label className="mb-2 block text-xs">
                            Ocurrencia
                          </Label>

                          <div className="flex flex-wrap gap-2">
                            {MONTH_OCCURRENCES.map((occurrence) => {
                              const selected = (
                                normalizedSelection.occurrences || []
                              ).includes(occurrence.value);

                              return (
                                <button
                                  key={occurrence.value}
                                  type="button"
                                  onClick={() => {
                                    const values = (
                                      normalizedSelection.occurrences
                                      || []
                                    );

                                    updateSelection({
                                      ...normalizedSelection,
                                      occurrences: selected
                                        ? values.filter(
                                          (value) => (
                                            value !== occurrence.value
                                          )
                                        )
                                        : [
                                          ...values,
                                          occurrence.value,
                                        ],
                                    });
                                  }}
                                  className={`rounded-md border px-3 py-2 text-sm ${
                                    selected
                                      ? 'border-blue-500 bg-blue-50'
                                      : ''
                                  }`}
                                >
                                  {occurrence.label}
                                </button>
                              );
                            })}
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )}

              {error && (
                <p className="rounded-md bg-red-50 p-3 text-sm text-red-700">
                  {error}
                </p>
              )}

              {!validation.valid && (
                <ul className="text-sm text-amber-700">
                  {validation.errors.map((message) => (
                    <li key={message}>{message}</li>
                  ))}
                </ul>
              )}

              {resolved?.resolved_dates?.length > 0 && (
                <p className="text-sm text-zinc-600">
                  Fechas resueltas: {resolved.resolved_dates.length}
                </p>
              )}
            </main>
          </div>

          <div className="flex justify-end gap-2 border-t p-4">
            <Button
              type="button"
              variant="outline"
              onClick={() => setOpen(false)}
            >
              Cancelar
            </Button>

            <Button
              type="button"
              disabled={!validation.valid || loading}
              onClick={apply}
            >
              {loading && (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              )}
              Aplicar
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
