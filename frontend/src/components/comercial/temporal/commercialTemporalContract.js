export const COMMERCIAL_TEMPORAL_MODES = Object.freeze({
  CURRENT_OPERATIONAL_DAY: 'current_operational_day',
  SPECIFIC_DATES: 'specific_dates',
  DATE_RANGES: 'date_ranges',
  DATE_RULES: 'date_rules',
  KEY_DATES: 'key_dates',
});

export const COMMERCIAL_BASIC_MODES = Object.freeze({
  TODAY: 'today',
  SINGLE_OR_RANGE: 'single_or_range',
  HISTORICAL: 'historical',
  ADVANCED: 'advanced',
});

export function isBackendResolvableTemporalSelection(selection) {
  const mode = selection?.mode;

  return (
    mode === COMMERCIAL_TEMPORAL_MODES.SPECIFIC_DATES
    || mode === COMMERCIAL_TEMPORAL_MODES.DATE_RANGES
    || mode === COMMERCIAL_TEMPORAL_MODES.DATE_RULES
  );
}

export const WEEKDAYS = Object.freeze([
  { value: 0, label: 'Lunes' },
  { value: 1, label: 'Martes' },
  { value: 2, label: 'Miércoles' },
  { value: 3, label: 'Jueves' },
  { value: 4, label: 'Viernes' },
  { value: 5, label: 'Sábado' },
  { value: 6, label: 'Domingo' },
]);

export const MONTH_OCCURRENCES = Object.freeze([
  { value: 1, label: 'Primer' },
  { value: 2, label: 'Segundo' },
  { value: 3, label: 'Tercer' },
  { value: 4, label: 'Cuarto' },
  { value: -1, label: 'Último' },
]);

const ISO_DATE_RE = /^\d{4}-\d{2}-\d{2}$/;

export function normalizeIsoDate(value) {
  const normalized = String(value || '').trim().slice(0, 10);
  return ISO_DATE_RE.test(normalized) ? normalized : null;
}

export function normalizeUnitIds(values) {
  if (!Array.isArray(values)) return [];

  return [...new Set(
    values
      .map((value) => String(value || '').trim())
      .filter(Boolean)
  )].sort();
}

export function normalizeSpecificDates(values) {
  if (!Array.isArray(values)) return [];

  return [...new Set(
    values
      .map(normalizeIsoDate)
      .filter(Boolean)
  )].sort();
}

function isoDateToUtc(value) {
  const normalized = normalizeIsoDate(value);
  if (!normalized) return null;

  const [year, month, day] = normalized.split('-').map(Number);
  return new Date(Date.UTC(year, month - 1, day));
}

function utcDateToIso(value) {
  if (!(value instanceof Date)) return null;

  return [
    value.getUTCFullYear(),
    String(value.getUTCMonth() + 1).padStart(2, '0'),
    String(value.getUTCDate()).padStart(2, '0'),
  ].join('-');
}

export function createInclusiveDateSequence(
  startValue,
  endValue
) {
  const start = isoDateToUtc(startValue);
  const end = isoDateToUtc(endValue);

  if (!start || !end) return [];

  const lower = start <= end ? start : end;
  const upper = start <= end ? end : start;
  const result = [];

  for (
    let cursor = new Date(lower);
    cursor <= upper;
    cursor.setUTCDate(cursor.getUTCDate() + 1)
  ) {
    result.push(utcDateToIso(cursor));
  }

  return result;
}

export function createCalendarWeekDates(value) {
  const date = isoDateToUtc(value);
  if (!date) return [];

  const nativeWeekday = date.getUTCDay();
  const mondayOffset = nativeWeekday === 0
    ? -6
    : 1 - nativeWeekday;

  const monday = new Date(date);
  monday.setUTCDate(date.getUTCDate() + mondayOffset);

  const sunday = new Date(monday);
  sunday.setUTCDate(monday.getUTCDate() + 6);

  return createInclusiveDateSequence(
    utcDateToIso(monday),
    utcDateToIso(sunday)
  );
}

export function createMonthWeekdayColumnDates(value) {
  const selected = isoDateToUtc(value);
  if (!selected) return [];

  const targetWeekday = selected.getUTCDay();
  const year = selected.getUTCFullYear();
  const month = selected.getUTCMonth();
  const result = [];

  const cursor = new Date(Date.UTC(year, month, 1));

  while (cursor.getUTCMonth() === month) {
    if (cursor.getUTCDay() === targetWeekday) {
      result.push(utcDateToIso(cursor));
    }

    cursor.setUTCDate(cursor.getUTCDate() + 1);
  }

  return result;
}

export function createMonthDateRange(yearValue, monthValue) {
  const year = Number(yearValue);
  const month = Number(monthValue);

  if (
    !Number.isInteger(year)
    || !Number.isInteger(month)
    || month < 1
    || month > 12
  ) {
    return null;
  }

  const start = new Date(Date.UTC(year, month - 1, 1));
  const end = new Date(Date.UTC(year, month, 0));

  return {
    start_date: utcDateToIso(start),
    end_date: utcDateToIso(end),
  };
}

export function mergeSpecificDateBlocks(
  currentValues,
  blockValues,
  preserveExisting = true
) {
  return normalizeSpecificDates(
    preserveExisting
      ? [...(currentValues || []), ...(blockValues || [])]
      : blockValues
  );
}

export function normalizeDateRanges(values) {
  if (!Array.isArray(values)) return [];

  return values
    .map((range) => {
      const startDate = normalizeIsoDate(
        range?.start_date || range?.startDate
      );
      const endDate = normalizeIsoDate(
        range?.end_date || range?.endDate || startDate
      );

      if (!startDate || !endDate) return null;

      return startDate <= endDate
        ? {
          start_date: startDate,
          end_date: endDate,
        }
        : {
          start_date: endDate,
          end_date: startDate,
        };
    })
    .filter(Boolean)
    .filter((range, index, all) => (
      all.findIndex((candidate) => (
        candidate.start_date === range.start_date
        && candidate.end_date === range.end_date
      )) === index
    ))
    .sort((left, right) => (
      left.start_date.localeCompare(right.start_date)
      || left.end_date.localeCompare(right.end_date)
    ));
}

function normalizeIntegerList(values, allowedValues) {
  if (!Array.isArray(values)) return [];

  const allowed = new Set(allowedValues);

  return [...new Set(
    values
      .map(Number)
      .filter((value) => allowed.has(value))
  )].sort((left, right) => left - right);
}

export function normalizeTemporalSelection(selection) {
  const mode = selection?.mode;

  if (
    mode === COMMERCIAL_TEMPORAL_MODES.CURRENT_OPERATIONAL_DAY
  ) {
    return { mode };
  }

  if (mode === COMMERCIAL_TEMPORAL_MODES.SPECIFIC_DATES) {
    return {
      mode,
      dates: normalizeSpecificDates(selection?.dates),
      exclude_dates: normalizeSpecificDates(
        selection?.exclude_dates
      ),
    };
  }

  if (mode === COMMERCIAL_TEMPORAL_MODES.DATE_RANGES) {
    return {
      mode,
      ranges: normalizeDateRanges(selection?.ranges),
      exclude_dates: normalizeSpecificDates(
        selection?.exclude_dates
      ),
    };
  }

  if (mode === COMMERCIAL_TEMPORAL_MODES.DATE_RULES) {
    const ruleType = selection?.rule_type || 'weekdays';

    const normalized = {
      mode,
      rule_type: ruleType,
      start_date: normalizeIsoDate(selection?.start_date),
      end_date: normalizeIsoDate(selection?.end_date),
      weekdays: normalizeIntegerList(
        selection?.weekdays,
        [0, 1, 2, 3, 4, 5, 6]
      ),
      exclude_dates: normalizeSpecificDates(
        selection?.exclude_dates
      ),
    };

    if (ruleType === 'weekdays_in_month_weeks') {
      normalized.month_weeks = normalizeIntegerList(
        selection?.month_weeks,
        [1, 2, 3, 4, 5]
      );
    }

    if (ruleType === 'nth_weekday_of_month') {
      normalized.occurrences = normalizeIntegerList(
        selection?.occurrences,
        [-1, 1, 2, 3, 4, 5]
      );
    }

    return normalized;
  }

  if (mode === COMMERCIAL_TEMPORAL_MODES.KEY_DATES) {
    return {
      mode,
      key_date_code: String(
        selection?.key_date_code || ''
      ).trim(),
      years: normalizeIntegerList(
        selection?.years,
        Array.from({ length: 30 }, (_, index) => 2000 + index)
      ),
    };
  }

  return {
    mode: COMMERCIAL_TEMPORAL_MODES.CURRENT_OPERATIONAL_DAY,
  };
}

export function validateTemporalSelection(selection) {
  const normalized = normalizeTemporalSelection(selection);
  const errors = [];

  if (
    normalized.mode
    === COMMERCIAL_TEMPORAL_MODES.SPECIFIC_DATES
    && normalized.dates.length === 0
  ) {
    errors.push('Selecciona al menos una fecha.');
  }

  if (
    normalized.mode
    === COMMERCIAL_TEMPORAL_MODES.DATE_RANGES
    && normalized.ranges.length === 0
  ) {
    errors.push('Agrega al menos un rango.');
  }

  if (
    normalized.mode
    === COMMERCIAL_TEMPORAL_MODES.DATE_RULES
  ) {
    if (!normalized.start_date || !normalized.end_date) {
      errors.push('Define el inicio y fin de la regla.');
    }

    if (
      normalized.start_date
      && normalized.end_date
      && normalized.start_date > normalized.end_date
    ) {
      errors.push('La fecha inicial no puede ser posterior a la final.');
    }

    if (normalized.weekdays.length === 0) {
      errors.push('Selecciona al menos un día de la semana.');
    }

    if (
      normalized.rule_type === 'weekdays_in_month_weeks'
      && normalized.month_weeks.length === 0
    ) {
      errors.push('Selecciona al menos una semana del mes.');
    }

    if (
      normalized.rule_type === 'nth_weekday_of_month'
      && normalized.occurrences.length === 0
    ) {
      errors.push('Selecciona al menos una ocurrencia mensual.');
    }
  }

  if (
    normalized.mode
    === COMMERCIAL_TEMPORAL_MODES.KEY_DATES
  ) {
    errors.push(
      'Los días especiales comerciales todavía no están habilitados.'
    );
  }

  return {
    valid: errors.length === 0,
    errors,
    selection: normalized,
  };
}

export function createInitialCommercialTemporalValue() {
  return {
    basic_mode: COMMERCIAL_BASIC_MODES.TODAY,
    unidad_negocio_ids: [],
    selection: {
      mode: COMMERCIAL_TEMPORAL_MODES.CURRENT_OPERATIONAL_DAY,
    },
  };
}
