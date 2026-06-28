/**
 * Utilidades CANÓNICAS para el selector de Inventario Inicial / Final.
 * ====================================================================
 * Regla de centralización: esta lógica se usa en Análisis (Reportes.js) y
 * Auditoría (Compras.js). Fuente única de verdad para:
 *   - obtener la fecha base de un inventario,
 *   - calcular la fecha mínima de los inventarios iniciales,
 *   - filtrar los inventarios finales.
 *
 * Sin estado, sin side-effects: funciones puras reutilizables.
 */

/** Normaliza la fecha de un inventario a 'YYYY-MM-DD' (soporta ISO y con espacio). */
export function getFechaBase(inv) {
  if (!inv || !inv.fecha) return null;
  return inv.fecha.split('T')[0] || inv.fecha.split(' ')[0] || null;
}

export function getInventarioKey(inv) {
  const key = inv?.folio ?? inv?.id;
  return key == null ? '' : String(key).trim();
}

export function getInventarioTimestamp(inv) {
  if (!inv?.fecha) return null;
  const normalized = String(inv.fecha)
    .trim()
    .replace(' ', 'T')
    .replace(/(\.\d{3})\d+/, '$1');
  const timestamp = new Date(normalized).getTime();
  return Number.isFinite(timestamp) ? timestamp : null;
}

/**
 * Fecha más antigua entre los inventarios iniciales seleccionados.
 * @returns {string|null} 'YYYY-MM-DD' o null si no hay fechas.
 */
export function fechaMinimaInventarios(inventariosIniciales) {
  if (!Array.isArray(inventariosIniciales) || inventariosIniciales.length === 0) {
    return null;
  }
  const fechas = inventariosIniciales
    .map(getFechaBase)
    .filter((f) => f);
  if (fechas.length === 0) return null;
  return fechas.sort()[0];
}

/**
 * Filtra los inventarios finales.
 * Si no hay fechaMinima, devuelve todos. Inventarios sin fecha se conservan.
 * Cuando strictAfterInitial=true, el final debe ser posterior al inicial y no
 * puede ser el mismo folio.
 */
export function filtrarInventariosFinales(inventarios, fechaMinima, options = {}) {
  const { inventariosIniciales = [], strictAfterInitial = false } = options;
  const inicialKeys = new Set((inventariosIniciales || []).map(getInventarioKey).filter(Boolean));
  const inicialTimestamps = (inventariosIniciales || [])
    .map(getInventarioTimestamp)
    .filter((timestamp) => timestamp != null);
  const latestInitialTimestamp = inicialTimestamps.length > 0 ? Math.max(...inicialTimestamps) : null;

  if (!fechaMinima && !strictAfterInitial) return inventarios;
  return (inventarios || []).filter((inv) => {
    const key = getInventarioKey(inv);
    if (strictAfterInitial && key && inicialKeys.has(key)) return false;

    if (strictAfterInitial && latestInitialTimestamp != null) {
      const timestamp = getInventarioTimestamp(inv);
      if (timestamp != null) return timestamp > latestInitialTimestamp;
    }

    if (!fechaMinima) return true;
    const fechaInv = getFechaBase(inv);
    if (!fechaInv) return true; // sin fecha -> mostrar
    if (strictAfterInitial) return fechaInv > fechaMinima;
    return fechaInv >= fechaMinima;
  });
}
