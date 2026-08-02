import React, { useMemo, useState } from 'react';
import { DayPicker } from 'react-day-picker';
import { es } from 'date-fns/locale';
import {
  CalendarDays,
  ChevronDown,
  ChevronRight,
  Clock3,
} from 'lucide-react';

import { Button } from '../ui/button';
import { Checkbox } from '../ui/checkbox';
import { Label } from '../ui/label';

import 'react-day-picker/dist/style.css';

/**
 * Modos temporales canónicos.
 *
 * CURRENT_OPERATIONAL_DAY:
 *   Día operativo vigente resuelto por backend.
 *
 * DATE_RANGE:
 *   Uno o varios días seleccionados mediante calendario.
 *
 * HISTORICAL_PERIODS:
 *   Uno o varios meses agrupados por año.
 */
export const TEMPORAL_MODES = Object.freeze({
  CURRENT_OPERATIONAL_DAY: 'current_operational_day',
  DATE_RANGE: 'date_range',
  HISTORICAL_PERIODS: 'historical_periods',
});

const MONTH_FORMATTER = new Intl.DateTimeFormat('es-MX', {
  month: 'long',
});

const DATE_FORMATTER = new Intl.DateTimeFormat('es-MX', {
  day: 'numeric',
  month: 'short',
  year: 'numeric',
});

const normalizeIsoDate = (value) => {
  if (!value) return null;

  const date = value instanceof Date
    ? value
    : new Date(`${String(value).slice(0, 10)}T12:00:00`);

  if (Number.isNaN(date.getTime())) return null;

  return [
    date.getFullYear(),
    String(date.getMonth() + 1).padStart(2, '0'),
    String(date.getDate()).padStart(2, '0'),
  ].join('-');
};

const isoToDate = (value) => {
  if (!value) return undefined;

  const normalized = String(value).slice(0, 10);
  const [year, month, day] = normalized.split('-').map(Number);

  if (!year || !month || !day) return undefined;

  return new Date(year, month - 1, day, 12, 0, 0);
};

const monthLabel = (month) => {
  const date = new Date(2000, Number(month) - 1, 1);
  const label = MONTH_FORMATTER.format(date);

  return label.charAt(0).toUpperCase() + label.slice(1);
};

const normalizeAvailability = (availability) => {
  const years = Array.isArray(availability?.anios)
    ? availability.anios
    : [];

  return years
    .map((yearEntry) => ({
      year: Number(yearEntry?.anio),
      startDate: yearEntry?.fecha_inicio || null,
      endDate: yearEntry?.fecha_fin || null,
      months: Array.isArray(yearEntry?.meses)
        ? yearEntry.meses
          .map((monthEntry) => ({
            month: Number(monthEntry?.mes),
            startDate: monthEntry?.fecha_inicio || null,
            endDate: monthEntry?.fecha_fin || null,
            availableDays: Number(
              monthEntry?.dias_disponibles || 0
            ),
          }))
          .filter((monthEntry) => (
            monthEntry.month >= 1
            && monthEntry.month <= 12
          ))
          .sort((a, b) => a.month - b.month)
        : [],
    }))
    .filter((yearEntry) => (
      Number.isInteger(yearEntry.year)
      && yearEntry.months.length > 0
    ))
    .sort((a, b) => b.year - a.year);
};

const periodKey = (year, month) => (
  `${year}-${String(month).padStart(2, '0')}`
);

const normalizePeriods = (periods) => {
  const normalized = [];

  (Array.isArray(periods) ? periods : []).forEach((entry) => {
    const year = Number(entry?.year ?? entry?.anio);
    const months = Array.isArray(entry?.months)
      ? entry.months
      : entry?.meses;

    if (!Number.isInteger(year) || !Array.isArray(months)) {
      return;
    }

    const validMonths = [...new Set(
      months
        .map(Number)
        .filter((month) => month >= 1 && month <= 12)
    )].sort((a, b) => a - b);

    if (validMonths.length > 0) {
      normalized.push({
        year,
        months: validMonths,
      });
    }
  });

  return normalized.sort((a, b) => b.year - a.year);
};

const periodsToSet = (periods) => {
  const selected = new Set();

  normalizePeriods(periods).forEach(({ year, months }) => {
    months.forEach((month) => {
      selected.add(periodKey(year, month));
    });
  });

  return selected;
};

const setToPeriods = (selectedSet) => {
  const grouped = new Map();

  [...selectedSet].forEach((key) => {
    const [yearRaw, monthRaw] = key.split('-');
    const year = Number(yearRaw);
    const month = Number(monthRaw);

    if (!grouped.has(year)) {
      grouped.set(year, []);
    }

    grouped.get(year).push(month);
  });

  return [...grouped.entries()]
    .map(([year, months]) => ({
      year,
      months: [...new Set(months)].sort((a, b) => a - b),
    }))
    .sort((a, b) => b.year - a.year);
};

const buildSelectionLabel = (value) => {
  const mode = value?.mode;

  if (mode === TEMPORAL_MODES.CURRENT_OPERATIONAL_DAY) {
    return 'Ventas del Día';
  }

  if (mode === TEMPORAL_MODES.DATE_RANGE) {
    const start = isoToDate(value?.startDate);
    const end = isoToDate(value?.endDate);

    if (!start) return 'Seleccionar fechas';
    if (!end || start.getTime() === end.getTime()) {
      return DATE_FORMATTER.format(start);
    }

    return `${DATE_FORMATTER.format(start)} – ${DATE_FORMATTER.format(end)}`;
  }

  const periods = normalizePeriods(value?.periods);
  const totalMonths = periods.reduce(
    (total, entry) => total + entry.months.length,
    0
  );

  if (totalMonths === 0) return 'Seleccionar histórico';

  if (periods.length === 1) {
    const [{ year, months }] = periods;

    if (months.length === 1) {
      return `${monthLabel(months[0])} ${year}`;
    }

    if (months.length === 12) {
      return String(year);
    }
  }

  return `${totalMonths} meses seleccionados`;
};

export default function CanonicalPeriodSelector({
  value,
  availability,
  onChange,
  disabled = false,
  loading = false,
  className = '',
}) {
  const normalizedAvailability = useMemo(
    () => normalizeAvailability(availability),
    [availability]
  );

  const currentValue = value || {
    mode: TEMPORAL_MODES.CURRENT_OPERATIONAL_DAY,
  };

  const [open, setOpen] = useState(false);
  const [expandedYears, setExpandedYears] = useState(() => new Set());
  const [draftMode, setDraftMode] = useState(currentValue.mode);
  const [draftRange, setDraftRange] = useState(() => ({
    from: isoToDate(currentValue.startDate),
    to: isoToDate(currentValue.endDate),
  }));
  const [draftPeriods, setDraftPeriods] = useState(
    () => periodsToSet(currentValue.periods)
  );

  const openSelector = () => {
    setDraftMode(currentValue.mode);
    setDraftRange({
      from: isoToDate(currentValue.startDate),
      to: isoToDate(currentValue.endDate),
    });
    setDraftPeriods(periodsToSet(currentValue.periods));

    setExpandedYears((previous) => {
      if (previous.size > 0) return previous;

      const firstYear = normalizedAvailability[0]?.year;
      return firstYear ? new Set([firstYear]) : previous;
    });

    setOpen(true);
  };

  const selectCurrentOperationalDay = () => {
    onChange?.({
      mode: TEMPORAL_MODES.CURRENT_OPERATIONAL_DAY,
    });
    setOpen(false);
  };

  const toggleYear = (year) => {
    setExpandedYears((previous) => {
      const next = new Set(previous);

      if (next.has(year)) {
        next.delete(year);
      } else {
        next.add(year);
      }

      return next;
    });
  };

  const toggleMonth = (year, month) => {
    const key = periodKey(year, month);

    setDraftPeriods((previous) => {
      const next = new Set(previous);

      if (next.has(key)) {
        next.delete(key);
      } else {
        next.add(key);
      }

      return next;
    });
  };

  const toggleCompleteYear = (yearEntry) => {
    const keys = yearEntry.months.map((monthEntry) => (
      periodKey(yearEntry.year, monthEntry.month)
    ));

    setDraftPeriods((previous) => {
      const next = new Set(previous);
      const complete = keys.every((key) => next.has(key));

      keys.forEach((key) => {
        if (complete) {
          next.delete(key);
        } else {
          next.add(key);
        }
      });

      return next;
    });
  };

  const applyDraft = () => {
    if (draftMode === TEMPORAL_MODES.DATE_RANGE) {
      if (!draftRange?.from) return;

      const startDate = normalizeIsoDate(draftRange.from);
      const endDate = normalizeIsoDate(
        draftRange.to || draftRange.from
      );

      onChange?.({
        mode: TEMPORAL_MODES.DATE_RANGE,
        startDate,
        endDate,
      });

      setOpen(false);
      return;
    }

    if (draftMode === TEMPORAL_MODES.HISTORICAL_PERIODS) {
      const periods = setToPeriods(draftPeriods);

      if (periods.length === 0) return;

      onChange?.({
        mode: TEMPORAL_MODES.HISTORICAL_PERIODS,
        periods,
      });

      setOpen(false);
    }
  };

  const minDate = isoToDate(availability?.fecha_minima);
  const maxDate = isoToDate(availability?.fecha_maxima);

  const hasDateAvailability = Boolean(minDate && maxDate);

  const calendarMonthCount = (
    hasDateAvailability
    && minDate.getFullYear() === maxDate.getFullYear()
    && minDate.getMonth() === maxDate.getMonth()
  )
    ? 1
    : 2;

  const calendarDefaultMonth = (() => {
    if (!hasDateAvailability) return undefined;

    if (calendarMonthCount === 1) {
      return new Date(
        maxDate.getFullYear(),
        maxDate.getMonth(),
        1
      );
    }

    return new Date(
      maxDate.getFullYear(),
      maxDate.getMonth() - 1,
      1
    );
  })();

  return (
    <div className={`relative ${className}`}>
      <Label className="text-xs mb-1 block">
        Periodo
      </Label>

      <button
        type="button"
        disabled={disabled || loading}
        onClick={() => {
          if (open) {
            setOpen(false);
          } else {
            openSelector();
          }
        }}
        className="flex h-10 min-w-[230px] w-full items-center justify-between rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background disabled:cursor-not-allowed disabled:opacity-50 focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
        aria-expanded={open}
        aria-haspopup="dialog"
      >
        <span className="truncate">
          {loading ? 'Cargando periodos…' : buildSelectionLabel(currentValue)}
        </span>
        <ChevronDown className="h-4 w-4 opacity-50" />
      </button>

      {open && (
        <div
          role="dialog"
          aria-label="Seleccionar periodo"
          className="absolute left-0 z-50 mt-1 w-[min(92vw,760px)] rounded-md border bg-white shadow-xl"
        >
          <div className="grid md:grid-cols-[220px_1fr]">
            <div className="border-b md:border-b-0 md:border-r p-3 space-y-2">
              <button
                type="button"
                onClick={selectCurrentOperationalDay}
                className={`w-full rounded-md border px-3 py-3 text-left transition ${
                  draftMode === TEMPORAL_MODES.CURRENT_OPERATIONAL_DAY
                    ? 'border-amber-400 bg-amber-50'
                    : 'hover:bg-zinc-50'
                }`}
              >
                <div className="flex items-center gap-2 font-medium">
                  <Clock3 className="h-4 w-4 text-amber-600" />
                  Ventas del Día
                </div>
                <p className="mt-1 text-xs text-zinc-500">
                  Día operativo vigente
                </p>
              </button>

              <button
                type="button"
                disabled={!hasDateAvailability}
                onClick={() => {
                  if (!hasDateAvailability) return;
                  setDraftMode(TEMPORAL_MODES.DATE_RANGE);
                }}
                className={`w-full rounded-md border px-3 py-3 text-left transition disabled:cursor-not-allowed disabled:opacity-50 ${
                  draftMode === TEMPORAL_MODES.DATE_RANGE
                    ? 'border-blue-400 bg-blue-50'
                    : 'hover:bg-zinc-50'
                }`}
              >
                <div className="flex items-center gap-2 font-medium">
                  <CalendarDays className="h-4 w-4 text-blue-600" />
                  Día o rango
                </div>
                <p className="mt-1 text-xs text-zinc-500">
                  Fechas operativas específicas
                </p>
              </button>

              <button
                type="button"
                disabled={normalizedAvailability.length === 0}
                onClick={() => {
                  if (normalizedAvailability.length === 0) return;
                  setDraftMode(TEMPORAL_MODES.HISTORICAL_PERIODS);
                }}
                className={`w-full rounded-md border px-3 py-3 text-left transition disabled:cursor-not-allowed disabled:opacity-50 ${
                  draftMode === TEMPORAL_MODES.HISTORICAL_PERIODS
                    ? 'border-zinc-500 bg-zinc-50'
                    : 'hover:bg-zinc-50'
                }`}
              >
                <div className="font-medium">
                  Histórico
                </div>
                <p className="mt-1 text-xs text-zinc-500">
                  Meses agrupados por año
                </p>
              </button>
            </div>

            <div className="p-3 min-h-[340px]">
              {draftMode === TEMPORAL_MODES.CURRENT_OPERATIONAL_DAY && (
                <div className="flex h-full min-h-[300px] items-center justify-center text-center">
                  <div>
                    <Clock3 className="mx-auto h-8 w-8 text-amber-600" />
                    <p className="mt-3 font-medium">
                      Ventas del Día
                    </p>
                    <p className="mt-1 max-w-sm text-sm text-zinc-500">
                      La fecha operativa vigente será resuelta por el backend
                      para cada unidad de negocio.
                    </p>
                  </div>
                </div>
              )}

              {draftMode === TEMPORAL_MODES.DATE_RANGE && (
                <div>
                  {!hasDateAvailability ? (
                    <div className="flex min-h-[300px] items-center justify-center text-center">
                      <div>
                        <CalendarDays className="mx-auto h-8 w-8 text-zinc-400" />
                        <p className="mt-3 font-medium text-zinc-700">
                          Cobertura temporal no disponible
                        </p>
                        <p className="mt-1 max-w-sm text-sm text-zinc-500">
                          No es posible seleccionar fechas hasta recuperar
                          los límites canónicos del histórico.
                        </p>
                      </div>
                    </div>
                  ) : (
                    <DayPicker
                      mode="range"
                      locale={es}
                      selected={draftRange}
                      onSelect={(range) => setDraftRange(
                        range || {
                          from: undefined,
                          to: undefined,
                        }
                      )}
                      defaultMonth={
                        draftRange?.from
                        || calendarDefaultMonth
                      }
                      fromDate={minDate}
                      toDate={maxDate}
                      fromMonth={new Date(
                        minDate.getFullYear(),
                        minDate.getMonth(),
                        1
                      )}
                      toMonth={new Date(
                        maxDate.getFullYear(),
                        maxDate.getMonth(),
                        1
                      )}
                      numberOfMonths={calendarMonthCount}
                      showOutsideDays={false}
                    />
                  )}
                </div>
              )}

              {draftMode === TEMPORAL_MODES.HISTORICAL_PERIODS && (
                <div className="max-h-[390px] overflow-y-auto">
                  {normalizedAvailability.length === 0 ? (
                    <p className="py-12 text-center text-sm text-zinc-500">
                      No existen periodos históricos disponibles.
                    </p>
                  ) : (
                    normalizedAvailability.map((yearEntry) => {
                      const expanded = expandedYears.has(yearEntry.year);
                      const monthKeys = yearEntry.months.map(
                        (monthEntry) => periodKey(
                          yearEntry.year,
                          monthEntry.month
                        )
                      );
                      const complete = monthKeys.every(
                        (key) => draftPeriods.has(key)
                      );
                      const partial = (
                        !complete
                        && monthKeys.some((key) => draftPeriods.has(key))
                      );

                      return (
                        <div
                          key={yearEntry.year}
                          className="border-b last:border-b-0"
                        >
                          <div className="flex items-center gap-2 px-2 py-2">
                            <button
                              type="button"
                              onClick={() => toggleYear(yearEntry.year)}
                              className="flex flex-1 items-center gap-2 text-left font-semibold"
                            >
                              {expanded ? (
                                <ChevronDown className="h-4 w-4" />
                              ) : (
                                <ChevronRight className="h-4 w-4" />
                              )}
                              {yearEntry.year}
                            </button>

                            <Checkbox
                              checked={complete ? true : partial ? 'indeterminate' : false}
                              onCheckedChange={() => toggleCompleteYear(yearEntry)}
                              aria-label={`Seleccionar año ${yearEntry.year}`}
                            />
                          </div>

                          {expanded && (
                            <div className="grid grid-cols-2 gap-1 pb-3 pl-8 pr-2 md:grid-cols-3">
                              {yearEntry.months.map((monthEntry) => {
                                const key = periodKey(
                                  yearEntry.year,
                                  monthEntry.month
                                );

                                return (
                                  <label
                                    key={key}
                                    className="flex cursor-pointer items-center gap-2 rounded px-2 py-2 hover:bg-zinc-50"
                                  >
                                    <Checkbox
                                      checked={draftPeriods.has(key)}
                                      onCheckedChange={() => toggleMonth(
                                        yearEntry.year,
                                        monthEntry.month
                                      )}
                                    />
                                    <span className="text-sm">
                                      {monthLabel(monthEntry.month)}
                                    </span>
                                  </label>
                                );
                              })}
                            </div>
                          )}
                        </div>
                      );
                    })
                  )}
                </div>
              )}
            </div>
          </div>

          {draftMode !== TEMPORAL_MODES.CURRENT_OPERATIONAL_DAY && (
            <div className="flex justify-end gap-2 border-t p-3">
              <Button
                type="button"
                variant="outline"
                onClick={() => setOpen(false)}
              >
                Cancelar
              </Button>

              <Button
                type="button"
                onClick={applyDraft}
                disabled={
                  (
                    draftMode === TEMPORAL_MODES.DATE_RANGE
                    && !draftRange?.from
                  )
                  || (
                    draftMode === TEMPORAL_MODES.HISTORICAL_PERIODS
                    && draftPeriods.size === 0
                  )
                }
              >
                Aplicar
              </Button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
